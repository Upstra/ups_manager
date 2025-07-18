from dataclasses import dataclass
from json import dumps as json_dumps, loads as json_loads
from pyVmomi import vim

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


def serialize_vm(vm: vim.VirtualMachine) -> str:
    """
    Serialize a `VirtualMachine` object into a JSON string
    Args:
        vm (vim.VirtualMachine): The VM to serialize
    Returns:
        str: Json formatted string representation of a VM
    """
    return json_dumps({
        "type": "VM",
        "moid": vm._moId,
    })

def serialize_server(vm: vim.HostSystem) -> str:
    """
    Serialize a `Server` object into a JSON string
    Args:
        vm (vim.HostSystem): The VM to serialize
    Returns:
        str: Json formatted string representation of a Server
    """
    return json_dumps({
        "type": "Server",
        "moid": vm._moId,
    })

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
        ip = obj["ip"] if "ip" in obj else None
        password = decrypt(obj["password"]) if "password" in obj else None
        user = obj["user"] if "user" in obj else None
        if not ip or not password or not user:
            raise ValueError(f"Ip, password or user is None: {vcenter_json}")
        return VCenterElement(ip, user, password, port)
    except DecryptionException as e:
        raise e
    except Exception as e:
        raise ValueError(f"Invalid JSON format: {e}") from e
