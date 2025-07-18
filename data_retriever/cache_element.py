from dataclasses import dataclass
from json import dumps as json_dumps, loads as json_loads

from data_retriever.decrypt_password import decrypt, DecryptionException


@dataclass
class VMwareElement:
    type: str
    moid: str

@dataclass
class VCenterElement:
    ip: str
    user: str
    password: str
    port: int


def serialize_element(element: VMwareElement) -> str:
    """
    Serialize a `VMwareElement` object into a JSON string
    Args:
        element (VMwareElement): The element to serialize
    Returns:
        str: Json formatted string representation of a VMwareElement
    """
    return json_dumps({
        "type": element.type,
        "moid": element.moid,
    })

def deserialize_element(element_json: str) -> VMwareElement:
    """
    Deserialize a JSON string into an `Element` object
    Args:
        element_json: (str): Json formatted string representation of an `Element`
    Returns:
        VMwareElement: The deserialized element
    """
    try:
        obj = json_loads(element_json)
        return VMwareElement(obj["type"], obj["moid"])
    except Exception as e:
        raise ValueError(f"Invalid JSON format: {e}") from e

def deserialize_vcenter(vcenter_json: str) -> VCenterElement:
    """
    Deserialize a JSON string into a `VCenterElement` object
    Args:
        vcenter_json: (str): JSON formatted string representation of a `VCenterElement`
    Returns:
        VCenterElement: The deserialized element
    """
    try:
        obj = json_loads(vcenter_json)
        if "port" in obj:
            port = obj["port"]
        else:
            port = None
        decrypted_password = decrypt(obj["password"])
        return VCenterElement(obj["ip"], obj["user"], decrypted_password, port)
    except DecryptionException as e:
        raise e
    except Exception as e:
        raise ValueError(f"Invalid JSON format: {e}") from e
