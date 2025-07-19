from uuid import uuid4
from enum import Enum
from psycopg2 import connect as postgres
from dotenv import load_dotenv
from os import environ as env, remove as remove_file
from os.path import exists as path_exists
from datetime import datetime

from data_retriever.migration_event import deserialize_event, serialize_event, VMShutdownEvent, serialize_event_type, \
    MigrationErrorEvent

load_dotenv()

SAVED_MIGRATION_ID = "plans/migration_id"

class EventQueueException(Exception):
    def __init__(self, message):
        self.message = message

class MigrationStatus(str, Enum):
    POWER_FAILURE = "POWER_FAILURE"     # A power failure occured, start of the grace period
    START_MIGRATION = "START_MIGRATION" # Grace period ended, start of the execution of the migration plan
    END_MIGRATION = "END_MIGRATION"     # The execution of the migration plan ended
    START_ROLLBACK = "START_ROLLBACK"   # Power came back, start of the rollback of the migration plan
    END_ROLLBACK = "END_ROLLBACK"       # The rollback of the migration plan ended

class EventQueue:
    def __init__(self):
        self._conn = None
        self._cursor = None
        self._migration_id = ""

    def connect(self):
        """
        Connect to Postgres
        Raises:
            EventQueueException: If connection could not be performed
        """
        try:
            db_host = env.get('DB_HOST')
            db_port = env.get('DB_PORT')
            db_name = env.get('DB_NAME')
            db_username = env.get('DB_USERNAME')
            db_password = env.get('DB_PASSWORD')
            self._conn = postgres(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_username,
                password=db_password
            )
            self._cursor = self._conn.cursor()
            self._migration_id = ""
        except Exception as e:
            raise EventQueueException(f"Failed to connect to Postgres: {e}") from e

    def disconnect(self):
        """
        Disconnect from Postgres
        Raises:
            EventQueueException: If deconnection could not be performed
        """
        if not self._conn or not self._cursor:
            raise EventQueueException(f"Postgres connection not established")
        try:
            self._cursor.close()
            self._conn.close()
        except Exception as e:
            raise EventQueueException(f"Failed to close Postgres connection: {e}") from e

    def push(self, event, is_rollback=False):
        """
        Push an event to the queue
        Args:
            event (VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent): The event to push to the queue
            is_rollback (bool): Whether the event occured during migration or rollback. Default to False for migration
        Raises:
            EventQueueException: If push could not be performed
        """
        if not self._conn or not self._cursor:
            raise EventQueueException(f"Postgres connection not established")
        if self._migration_id == "":
            self._generate_migration_id()
            if self._migration_id != "":
                EventQueueException("No migration has been started")
        if isinstance(event, MigrationErrorEvent):
            migration_id = f"error_{self._migration_id}"
        elif is_rollback:
            migration_id = f"rollback_{self._migration_id}"
        else:
            migration_id = f"migration_{self._migration_id}"
        try:
            self._cursor.execute("""
                INSERT INTO "history_event" (
                    "entity", "entityId", "action", "metadata", "userAgent", "createdAt"
                ) VALUES (
                    'migration', %s, %s, %s, 'UPSTRA', %s
                );
                """, (migration_id, serialize_event_type(event), serialize_event(event), datetime.now())
            )
        except Exception as e:
            EventQueueException(f"Failed to push event to Redis: {e}")

    def get_event_list(self):
        """
        Get all events from the queue
        Returns:
            (list[VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent]): All events pushed to the queue
        Raises:
            EventQueueException: If no events could be pulled
        """
        if not self._conn or not self._cursor:
            raise EventQueueException(f"Postgres connection not established")
        if self._migration_id == "":
            self._generate_migration_id()
            if self._migration_id == "":
                raise EventQueueException("No migration has been started")
        migration_id = "migration_" + self._migration_id
        try:
            self._cursor.execute("""
                SELECT "action", "metadata" FROM "history_event" WHERE "entityId"=%s ORDER BY "createdAt" DESC
            """, (migration_id,))
            rows = self._cursor.fetchall()
            return [deserialize_event(row[0], row[1]) for row in rows]
        except Exception as e:
            raise EventQueueException(f"Failed to get events from Redis: {e}")

    def _generate_migration_id(self):
        """ Generate migration id to save current migration events """
        if path_exists(SAVED_MIGRATION_ID):
            with open(SAVED_MIGRATION_ID, "r") as f:
                self._migration_id = f.read().strip()
        else:
            self._migration_id = str(uuid4())
            with open(SAVED_MIGRATION_ID, "w") as f:
                f.write(self._migration_id)

    def _delete_migration_id(self):
        """ Delete migration id """
        if path_exists(SAVED_MIGRATION_ID):
            remove_file(SAVED_MIGRATION_ID)
        self._migration_id = ""

    def _send_status(self, status):
        """
        Send a migration status in log to notify of the current status of the migration
        Args:
            status (str): The migration status
        Raises:
            EventQueueException: If status could not be sent
        """
        if not self._conn or not self._cursor:
            raise EventQueueException(f"Postgres connection not established")
        try:
            self._cursor.execute("""
                INSERT INTO "history_event" ("entity", "entityId", "action", "userAgent", "createdAt")
                VALUES ('migration', 'migration_status', %s, 'UPSTRA', NOW());
            """, (status,))
            self._conn.commit()
        except Exception as e:
            EventQueueException(f"Failed to push {status} status to Postgres: {e}")

    def grace_shutdown(self):
        """
        Send a POWER_FAILURE status in log to notify of a power failure, and of the start of the grace period
        Raises:
            EventQueueException: If status POWER_FAILURE could not be sent
        """
        self._send_status(MigrationStatus.POWER_FAILURE)

    def start_shutdown(self):
        """
        Send a START_MIGRATION status in log to notify of the start of the execution of the migration plan
        Raises:
            EventQueueException: If status START_MIGRATION could not be sent
        """
        self._send_status(MigrationStatus.START_MIGRATION)
        self._generate_migration_id()

    def finish_shutdown(self):
        """
        Send a END_MIGRATION status in log to notify of the end of the execution of the migration plan
        Raises:
            EventQueueException: If status END_MIGRATION could not be sent
        """
        self._send_status(MigrationStatus.END_MIGRATION)

    def start_restart(self):
        """
        Send a START_ROLLBACK status in log to notify of the start of the rollback of the migration plan
        Raises:
            EventQueueException: If status START_ROLLBACK could not be sent
        """
        self._send_status(MigrationStatus.START_ROLLBACK)

    def finish_restart(self):
        """
        Send a END_ROLLBACK status in log to notify of the end of the rollback of the migration plan
        Raises:
            EventQueueException: If status END_ROLLBACK could not be sent
        """
        self._send_status(MigrationStatus.START_ROLLBACK)
        self._delete_migration_id()
