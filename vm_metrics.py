import ssl
from argparse import ArgumentParser
from json import dumps as json_dumps
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from list_vm import error_message


def to_json(vm: vim.VirtualMachine) -> dict[str, str | int | None]:
    """
    Format VM metrics data to a json dictionary
    Args:
        vm (vim.VirtualMachine): The VM object where metrics are retrieved
    Returns:
        dict[str, str | int | None]: A dictionary formatted for json dumps
    """
    return {
        "powerState": vm.runtime.powerState,
        "guestState": vm.guest.guestState,
        "connectionState": vm.runtime.connectionState,
        "guestHeartbeatStatus": vm.guestHeartbeatStatus,
        "overallStatus": vm.overallStatus,
        "overallCpuUsage": vm.summary.quick_stats.overallCpuUsage,
        "maxCpuUsage": vm.runtime.maxCpuUsage,
        "guestMemoryUsage": vm.summary.quick_stats.guestMemoryUsage,
        "maxMemoryUsage": vm.runtime.maxMemoryUsage,
        "uptimeSeconds": vm.summary.quick_stats.uptimeSeconds,
        "usedStorage": vm.summary.storage.committed,
        "totalStorage": vm.summary.storage.committed + vm.summary.storage.uncommitted,
        "bootTime": vm.runtime.bootTime.isoformat() if vm.runtime.bootTime else "",
        "isMigrating": vm.runtime.vmFailoverInProgress,
        "swappedMemory": vm.summary.quickStats.swappedMemory
    }


def get_vm_metrics(vm_name: str, datacenter_name: str, host: str, user: str, password: str, port=443):
    context = ssl._create_unverified_context()

    try:
        si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
    except vim.fault.InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
        return
    except Exception as err:
        print(error_message(str(err)))
        return

    content = si.RetrieveContent()
    search_index = content.searchIndex
    vm = search_index.FindByInventoryPath(f"{datacenter_name}/vm/{vm_name}")
    if not vm:
        print(error_message("VM not found", 404))
        Disconnect(si)
        return

    print(json_dumps(to_json(vm)))
    Disconnect(si)


if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--vm", required=True, help="Le nom de la VM")
    parser.add_argument("--datacenter", required=True, help="Le nom du datacenter où est stocké la VM")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    get_vm_metrics(args.vm, args.datacenter, args.ip, args.user, args.password, args.port)
