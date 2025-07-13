from redis import Redis

from data_retriever.migration_event import serialize_event, deserialize_event


STATE = "migration:state"
EVENTS = "migration:events"

class EventQueue:
    def __init__(self):
        self._redis = Redis()

    def push(self, event):
        """
        Push an event to the queue
        Args:
            event (VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent): The event to push to the queue
        """
        self._redis.lpush(EVENTS, serialize_event(event))

    def get_event_list(self):
        """
        Pop all events pushed to the queue
        Returns:
            (list[VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent]): The events pushed to the queue
        """
        return [deserialize_event(event) for event in self._redis.lrange(EVENTS, 0, -1)]

    def start_shutdown(self):
        """ Notify redis listener of the start of the migration """
        self._redis.set(STATE, "in migration")

    def finish_shutdown(self):
        """ Notify redis listener of the end of the migration """
        self._redis.set(STATE, "migrated")

    def start_restart(self):
        """ Notify redis listener of the start of the rollback """
        self._redis.set(STATE, "restarting")

    def finish_restart(self):
        """ Notify redis listener that everything is back to normal """
        self._redis.delete(STATE)
        self._redis.delete(EVENTS)
