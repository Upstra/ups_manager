from dataclasses import dataclass
from json import dumps as json_dumps, loads as json_loads


@dataclass
class VMMigrationEvent:
    vm_moid: str
    server_moid: str

@dataclass
class VMShutdownEvent:
    vm_moid: str
    server_moid: str

@dataclass
class ServerShutdownEvent:
    server_moid: str
    ilo_ip: str
    ilo_user: str
    ilo_password: str
    start_delay: int

EVENT_CLASSES = {
    "VMMigrationEvent": VMMigrationEvent,
    "VMShutdownEvent": VMShutdownEvent,
    "ServerShutdownEvent": ServerShutdownEvent,
}

def serialize_event(event) -> str:
    """
    Serialize an Event object into a JSON string
    Args:
        event (VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent): The event to serialize
    Returns:
        str: Json formatted string representation of an Event
    """
    return json_dumps({
        "event_type": type(event).__name__,
        "data": event.__dict__,
    })

def deserialize_event(event_json: str):
    """
    Deserialize a JSON string into an Event object
    Args:
        event_json: (str): Json formatted string representation of an Event
    Returns:
        VMMigrationEvent | VMShutdownEvent | ServerShutdownEvent: The deserialized event
    Raises:
        ValueError: If JSON is malformed or event type is unknown
    """
    try:
        obj = json_loads(event_json)
    except Exception as e:
        raise ValueError(f"Invalid JSON format: {e}") from e

    event_type = obj.get("event_type")
    if event_type not in EVENT_CLASSES:
        raise ValueError(f"Unknown event type: {event_type}")

    cls = EVENT_CLASSES[event_type]
    try:
        return cls(**obj["data"])
    except TypeError as e:
        raise ValueError(f"Invalid event data for {event_type}: {e}") from e
