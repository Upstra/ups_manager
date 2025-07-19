from dataclasses import dataclass
from enum import Enum
from json import dumps as json_dumps, loads as json_loads

from data_retriever.decrypt_password import encrypt, decrypt


@dataclass
class VMMigrationEvent:
    vm_moid: str
    server_moid: str

@dataclass
class VMShutdownEvent:
    vm_moid: str
    server_moid: str

@dataclass
class VMStartedEvent:
    vm_moid: str
    server_moid: str

@dataclass
class ServerStartedEvent:
    server_moid: str

@dataclass
class ServerShutdownEvent:
    server_moid: str
    ilo_ip: str
    ilo_user: str
    ilo_password: str

@dataclass
class MigrationErrorEvent:
    title: str
    message: str


class ActionType(str, Enum):
    VM_STARTED = "VM_STARTED"
    VM_MIGRATED = "VM_MIGRATED"
    VM_STOPPED = "VM_STOPPED"
    SERVER_STARTED = "SERVER_STARTED"
    SERVER_STOPPED = "SERVER_STOPPED"
    MIGRATION_ERROR = "MIGRATION_ERROR"

EVENT_CLASSES = {
    ActionType.VM_STARTED.value: VMStartedEvent,
    ActionType.VM_MIGRATED.value: VMMigrationEvent,
    ActionType.VM_STOPPED.value: VMShutdownEvent,
    ActionType.SERVER_STARTED.value: ServerStartedEvent,
    ActionType.SERVER_STOPPED.value: ServerShutdownEvent,
    ActionType.MIGRATION_ERROR.value: MigrationErrorEvent,
}

def serialize_event_type(event) -> str:
    """
    Serialize an Event type from its object into a status string
    Args:
        event (VMStartedEvent | VMMigrationEvent | VMShutdownEvent | ServerStartedEvent | ServerShutdownEvent | MigrationErrorEvent): The event to get type from and to serialize
    Returns:
        str: A string representing the event type in Postgres log
    Raises: TypeError if the event type is not supported
    """
    if isinstance(event, VMStartedEvent):
        return ActionType.VM_STARTED
    elif isinstance(event, VMMigrationEvent):
        return ActionType.VM_MIGRATED
    elif isinstance(event, VMShutdownEvent):
        return ActionType.VM_STOPPED
    elif isinstance(event, ServerStartedEvent):
        return ActionType.SERVER_STARTED
    elif isinstance(event, ServerShutdownEvent):
        return ActionType.SERVER_STOPPED
    elif isinstance(event, MigrationErrorEvent):
        return ActionType.MIGRATION_ERROR
    else:
        raise TypeError("Unknown event type")

def serialize_event(event) -> str:
    """
    Serialize an Event object into a JSON string
    Args:
        event (VMStartedEvent | VMMigrationEvent | VMShutdownEvent | ServerStartedEvent | ServerShutdownEvent | MigrationErrorEvent): The event to serialize
    Returns:
        str: Json formatted string representation of an Event
    """
    if isinstance(event, ServerShutdownEvent):
        event.ilo_password = encrypt(event.ilo_password)
    return json_dumps(event.__dict__)

def deserialize_event(event_type: str, event_json: dict):
    """
    Deserialize a JSON string into an Event object
    Args:
        event_type (str): The type of event to deserialize
        event_json: (dict): Json formatted dictionary representation of an Event
    Returns:
        VMStartedEvent | VMMigrationEvent | VMShutdownEvent | ServerStartedEvent | ServerShutdownEvent | MigrationErrorEvent: The deserialized event
    Raises:
        ValueError: If JSON is malformed or event type is unknown
    """
    if event_type not in EVENT_CLASSES:
        raise ValueError(f"Unknown event type: {event_type}")

    cls = EVENT_CLASSES[event_type]
    try:
        event = cls(**event_json)
        if event_type == ActionType.SERVER_STOPPED.value:
            event.ilo_password = decrypt(event.ilo_password)
        return event
    except TypeError as e:
        raise ValueError(f"Invalid event data for {event_type}: {e}") from e
