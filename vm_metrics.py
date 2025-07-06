import ssl
from argparse import ArgumentParser
from datetime import datetime
from json import dumps as json_dumps
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from time import sleep

from list_vm import error_message


def to_json(vm: vim.VirtualMachine) -> dict:
    """
    Format VM metrics data to a json dictionary
    Args:
        vm (vim.VirtualMachine): The VM object where metrics are retrieved
    Returns:
        dict: A dictionary formatted for json dumps
    """
    return {
        "powerState": vm.runtime.powerState,
        "guestState": vm.guest.guestState,
        "connectionState": vm.runtime.connectionState,
        "guestHeartbeatStatus": vm.guestHeartbeatStatus,
        "overallStatus": vm.overallStatus,
        "overallCpuUsage": vm.summary.quickStats.overallCpuUsage,
        "maxCpuUsage": vm.runtime.maxCpuUsage,
        "guestMemoryUsage": vm.summary.quickStats.guestMemoryUsage,
        "maxMemoryUsage": vm.runtime.maxMemoryUsage,
        "uptimeSeconds": vm.summary.quickStats.uptimeSeconds,
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
    perf_manager = content.perfManager

    counters = {f"{c.groupInfo.key}.{c.nameInfo.key}.{c.rollupType}": c.key for c in perf_manager.perfCounter}

    wanted = [
        'cpu.usage.average',
        'cpu.usagemhz.average',
        'mem.usage.average',
        'mem.consumed.average',
        'disk.usage.average',
        'net.usage.average'
    ]
    metric_ids = [
        vim.PerformanceManager.MetricId(counterId=counters[name], instance="")
        for name in wanted if name in counters
    ]
    if not metric_ids:
        print(error_message("No metrics where found", 400))
        Disconnect(si)
        return

    try:
        while True:
            vm = search_index.FindByInventoryPath(f"{datacenter_name}/vm/{vm_name}")
            if not vm:
                print(error_message("VM not found", 404))
                break

            query = vim.PerformanceManager.QuerySpec(
                entity=vm,
                metricId=metric_ids,
                intervalId=20,
                maxSample=1
            )
            stats = perf_manager.QueryStats([query])

            result = {
                "timestamp": datetime.now().isoformat(),
                "vmName": vm.name,
                "powerState": vm.runtime.powerState,
                "guestState": vm.guest.guestState,
                "uptime": vm.summary.quickStats.uptimeSeconds,
            }

            if stats and stats[0].value:
                for metric in stats[0].value:
                    counter_info = next(c for c in perf_manager.perfCounter if c.key == metric.id.counterId)
                    name = f"{counter_info.groupInfo.key}.{counter_info.nameInfo.key}.{counter_info.rollupType}"
                    result[name] = metric.value[-1] if metric.value else 0

            print(json_dumps(result, indent=2))
            sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
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
