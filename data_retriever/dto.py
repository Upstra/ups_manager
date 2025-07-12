from json import dumps as json_dumps
from pyVmomi import vim


def result_message(message: str, http_code) -> str:
    """
    Dump a json formatted result message
    Args:
        message (str): The message explaining the result of the command
        http_code (int): The HTTP response code corresponding to the result
    Returns:
        str: A string formatted json dump of the result message
    """
    return json_dumps({
        "result": {
            "message": message,
            "httpCode": http_code
        }
    }, indent=2)


def vms_list_info(vms: list[vim.VirtualMachine]) -> str:
    """
    Format VMs data to a json dictionary
    Args:
        vms (list[vim.VirtualMachine]): A list of VM object
    Returns:
        str: A string formatted json dump of the vms data
    """
    vm_list = [None] * len(vms)

    for i, vm in enumerate(vms):
        json_object = {
            "name": vm.name,
            "moid": vm._moId,
            "ip": vm.summary.guest.ipAddress if vm.summary.guest and vm.summary.guest.ipAddress else "",
            "guestOs": vm.config.guestFullName,
            "guestFamily": vm.guest.guestFamily if vm.guest else "",
            "version": vm.config.version,
            "createDate": vm.config.createDate.isoformat() if vm.config.createDate else "",
            "numCoresPerSocket": vm.config.hardware.numCoresPerSocket,
            "numCPU": vm.config.hardware.numCPU
        }
        if vm.runtime.host:
            json_object["esxiHostName"] = vm.runtime.host.name
            json_object["esxiHostMoid"] = vm.runtime.host._moId
        else:
            json_object["esxiHostName"] = ""
            json_object["esxiHostMoid"] = ""
        vm_list[i] = json_object
    return json_dumps({"vms": vm_list}, indent=2)


def vm_metrics_info(vm: vim.VirtualMachine) -> str:
    """
    Format VM metrics data to a json dictionary
    Args:
        vm (vim.VirtualMachine): The VM object where metrics are retrieved
    Returns:
        str: A string formatted json dump of the metrics data
    """
    json_object = {
        "powerState": vm.runtime.powerState,
        "guestState": vm.guest.guestState if vm.guest else "",
        "connectionState": vm.runtime.connectionState,
        "guestHeartbeatStatus": vm.guestHeartbeatStatus,
        "overallStatus": vm.overallStatus,
        "maxCpuUsage": vm.runtime.maxCpuUsage,
        "maxMemoryUsage": vm.runtime.maxMemoryUsage,
        "bootTime": vm.runtime.bootTime.isoformat() if vm.runtime.bootTime else "",
        "isMigrating": vm.runtime.vmFailoverInProgress
    }
    if vm.summary.quickStats:
        json_object["overallCpuUsage"] = vm.summary.quickStats.overallCpuUsage
        json_object["guestMemoryUsage"] = vm.summary.quickStats.guestMemoryUsage
        json_object["uptimeSeconds"] = vm.summary.quickStats.uptimeSeconds
        json_object["swappedMemory"] = vm.summary.quickStats.swappedMemory
    else:
        json_object["overallCpuUsage"] = 0
        json_object["guestMemoryUsage"] = 0
        json_object["uptimeSeconds"] = 0
        json_object["swappedMemory"] = 0
    if vm.summary.storage:
        json_object["usedStorage"] = vm.summary.storage.committed
        json_object["totalStorage"] = vm.summary.storage.committed + vm.summary.storage.uncommitted
    else:
        json_object["usedStorage"] = 0
        json_object["totalStorage"] = 0
    return json_dumps(json_object, indent=2)


def server_info(host: vim.HostSystem) -> str:
    """
    Format Server data to a json dictionary
    Args:
        host (vim.HostSystem): The Host object where server data are retrieved
    Returns:
        str: A string formatted json dump of the server data
    """
    json_object = {
        "name": host.name,
        "vCenterIp": host.summary.managementServerIp,
        "cluster": host.parent.name if host.parent else "",
        "vendor": host.hardware.systemInfo.vendor,
        "model": host.hardware.systemInfo.model,
        "ip": host.config.network.vnic[0].spec.ip.ipAddress if host.config and host.config.network.vnic else "",
        "cpuCores": host.hardware.cpuInfo.numCpuCores,
        "cpuThreads": host.hardware.cpuInfo.numCpuThreads,
        "cpuMHz": host.hardware.cpuInfo.hz / 1000000,
        "ramTotal": int(host.hardware.memorySize / (1024 ** 3)),
    }
    return json_dumps(json_object, indent=2)


def server_metrics_info(host: vim.HostSystem) -> str:
    """
    Format Server metrics data to a json dictionary
    Args:
       host (vim.HostSystem): The Host object where metrics are retrieved
    Returns:
       str: A string formatted json dump of the metrics data
    """
    cpu_usage = (host.summary.quickStats.overallCpuUsage / ((host.hardware.cpuInfo.hz / 1000000) * host.hardware.cpuInfo.numCpuCores)) * 100
    json_object = {
        "powerState": host.runtime.powerState,
        "overallStatus": host.overallStatus,
        "rebootRequired": host.summary.rebootRequired,
        "cpuUsagePercent": cpu_usage,
        "ramUsageMB": host.summary.quickStats.overallMemoryUsage,
        "uptime": host.summary.quickStats.uptime,
        "boottime": host.runtime.bootTime.isoformat() if host.runtime.bootTime else "",
    }
    return json_dumps(json_object, indent=2)
