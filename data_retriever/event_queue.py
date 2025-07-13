from redis import Redis

from data_retriever.migration_event import serialize_event, deserialize_event


STATE = "migration:state"
EVENTS = "migration:events"

class EventQueue:
    def __init__(self):
        try:
            self._redis = Redis()
            self._redis.ping()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}") from e

    def push(self, event):
        """
        Push an event to the queue
        Args:
            event (VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent): The event to push to the queue
        """
        try:
            self._redis.lpush(EVENTS, serialize_event(event))
        except Exception as e:
            print(f"Failed to push event to Redis: {e}")

    def get_event_list(self):
        """
        Get all events from the queue
        Returns:
            (list[VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent]): All events pushed to the queue
        """
        try:
            return [deserialize_event(event) for event in self._redis.lrange(EVENTS, 0, -1)]
        except Exception as e:
            print(f"Failed to get events from Redis: {e}")
            return []

    def start_shutdown(self):
        """ Notify redis listener of the start of the migration """
        try:
            self._redis.set(STATE, "in migration")
        except Exception as e:
            print(f"Failed to push status to Redis: {e}")

    def finish_shutdown(self):
        """ Notify redis listener of the end of the migration """
        try:
            self._redis.set(STATE, "migrated")
        except Exception as e:
            print(f"Failed to push status to Redis: {e}")

    def start_restart(self):
        """ Notify redis listener of the start of the rollback """
        try:
            self._redis.set(STATE, "restarting")
        except Exception as e:
            print(f"Failed to push status to Redis: {e}")

    def finish_restart(self):
        """ Notify redis listener that everything is back to normal """
        try:
            self._redis.delete(STATE)
            self._redis.delete(EVENTS)
        except Exception as e:
            print(f"Failed to delete status and events in Redis: {e}")
