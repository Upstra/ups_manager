from json import dumps as json_dumps
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from argparse import ArgumentParser
import ssl


def to_json(vm: vim.VirtualMachine):
    def disk_to_dict(disk):
        return {
            "diskPath": getattr(disk, "diskPath", None),
            "capacity": getattr(disk, "capacity", None),
            "freeSpace": getattr(disk, "freeSpace", None),
            "diskType": getattr(disk, "diskType", None)
        }

    def disk_layout_to_dict(dl):
        return {
            "key": getattr(dl, "key", None),
            "chain": [c for c in getattr(dl, "chain", [])]
        }

    return {
        "name": vm.name,
        "hostName": vm.guest.hostName,
        "isMigrating": vm.runtime.vmFailoverInProgress,
        "ip": vm.summary.guest.ipAddress,
        "guestOs": vm.config.guestFullName,
        "guestFamily": vm.guest.guestFamily,
        "version": vm.config.version,
        "createDate": vm.config.createDate.isoformat(),
        "bootTime": vm.runtime.bootTime.isoformat(),
        "uptimeSeconds": vm.summary.quickStats.uptimeSeconds,
        "powerState": vm.runtime.powerState,
        "guestState": vm.guest.guestState,
        "connectionState": vm.runtime.connectionState,
        "guestHeartbeatStatus": vm.guestHeartbeatStatus,
        "overallStatus": vm.overallStatus,
        "maxCpuUsage": vm.runtime.maxCpuUsage,
        "overallCpuUsage": vm.summary.quickStats.overallCpuUsage,
        "numCoresPerSocket": vm.config.hardware.numCoresPerSocket,
        "numCPU": vm.config.hardware.numCPU,
        "maxMemoryUsage": vm.runtime.maxMemoryUsage,
        "memoryMB": vm.config.hardware.memoryMB,
        "memorySizeMB": vm.summary.config.memorySizeMB,
        "hostMemoryUsage": vm.summary.quickStats.hostMemoryUsage,
        "swappedMemory": vm.summary.quickStats.swappedMemory,
        "usedStorage": vm.summary.storage.committed,
        "totalStorage": vm.summary.storage.committed + vm.summary.storage.uncommitted,

        "vmPathName": vm.summary.config.vmPathName,
        "disks": [disk_to_dict(d) for d in vm.guest.disk],
        "diskLayout": disk_layout_to_dict(vm.layout),
        "datastore": vm.config.datastoreUrl
    }


def get_vms(host: str, user: str, password: str, port=443) -> None:
    """
    Print a list of virtual machines from a server host
    Args:
        host (str): The IP address or hostname of the server
        user (str): The username for authentication
        password (str): The password of the user
        port (int, optional): The port to use for the connection (default is 443)
    """
    context = ssl._create_unverified_context()
    try:
        si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
    except vim.fault.InvalidLogin as _:
        print("Mot de passe incorrect")
        return
    except Exception as err:
        print(err)
        return
    content = si.RetrieveContent()

    for datacenter in content.rootFolder.childEntity:
        vm_folder = datacenter.vmFolder
        vm_list = vm_folder.childEntity
        for vm in vm_list:
            if isinstance(vm, vim.VirtualMachine):
                print(json_dumps(to_json(vm)))
            else:
                print(f"Element is not a VirtualMachine : {vm}")
    Disconnect(si)


if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    get_vms(args.ip, args.user, args.password, args.port)
