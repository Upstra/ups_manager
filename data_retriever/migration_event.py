from dataclasses import dataclass
from json import dumps as json_dumps, loads as json_loads


@dataclass
class VMMigrationEvent:
    vm_moid: str
    server_moid: str

@dataclass
class VMShutdownEvent:
    vm_moid: str

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
    """
    obj = json_loads(event_json)
    cls = EVENT_CLASSES[obj["event_type"]]
    return cls(**obj["data"])
