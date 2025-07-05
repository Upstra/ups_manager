from json import dumps as json_dumps
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from argparse import ArgumentParser
import ssl


VERIFIED_SSL = False


def error_message(message: str, http_code = 400) -> str:
    """
    Dump a json formatted error message
    Args:
        message (str): The message explaining the error
        http_code (int): The HTTP response code corresponding to the error (defaults to 400)
    Returns:
        str: A json dump of the error message
    """
    return json_dumps({
        "error": {
            "message": message,
            "httpCode": http_code
        }
    })


def to_json(vm: vim.VirtualMachine, datacenter_name: str) -> dict[str, str | int | None]:
    """
    Format VM data as json dictionary
    Args:
        vm (vim.VirtualMachine): The VM object where data is retrieved
        datacenter_name (str): The name of the datacenter where the VM is stored for search function
    Returns:
        dict[str, str | int | None]: A dictionary formatted for json dumps
    """
    return {
        "name": vm.name,
        "datacenter": datacenter_name,
        "hostName": vm.guest.hostName if vm.guest.hostName else "",
        "ip": vm.summary.guest.ipAddress if vm.summary.guest.ipAddress else "",
        "guestOs": vm.config.guestFullName,
        "guestFamily": vm.guest.guestFamily,
        "version": vm.config.version,
        "createDate": vm.config.createDate.isoformat() if vm.config.createDate else "",
        "numCoresPerSocket": vm.config.hardware.numCoresPerSocket,
        "numCPU": vm.config.hardware.numCPU,
        "vmPathName": vm.summary.config.vmPathName
    }


def get_vms(host: str, user: str, password: str, port=443) -> None:
    """
    Print a list of virtual machines from a server host
    Args:
        host (str): The IP address or hostname of the server
        user (str): The username for authentication
        password (str): The password of the user
        port (int): The port to use for the connection (default is 443)
    """
    # context = ssl._create_unverified_context()
    context = ssl.create_default_context()
    # Only disable verification if explicitly configured
    if not VERIFIED_SSL:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    try:
        si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
    except vim.fault.InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
        return
    except Exception as err:
        print(error_message(str(err)))
        return
    content = si.RetrieveContent()

    vms = {"vms": []}
    for datacenter in content.rootFolder.childEntity:
        datacenter_name = datacenter.name
        vm_folder = datacenter.vmFolder
        vm_list = vm_folder.childEntity
        for vm in vm_list:
            if isinstance(vm, vim.VirtualMachine):
                vms["vms"].append(to_json(vm, datacenter_name))
    print(json_dumps(vms))
    Disconnect(si)


if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    get_vms(args.ip, args.user, args.password, args.port)
