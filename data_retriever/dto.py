from pyVmomi import vim
from json import dumps as json_dumps


def output(json_dict: dict):
    """
    Send dictionary to output
    Args:
        json_dict (dict): Json formatted dictionary to send
    """
    print(json_dumps(json_dict, indent=2))


def result_message(message: str, http_code) -> dict:
    """
    Dump a json formatted result message
    Args:
        message (str): The message explaining the result of the command
        http_code (int): The HTTP response code corresponding to the result
    Returns:
        dict: A dictionary formatted for json dump containing the result message
    """
    return {
        "result": {
            "message": message,
            "httpCode": http_code
        }
    }


def vms_list_info(vms: list[vim.VirtualMachine]) -> dict:
    """
    Format VMs data to a json dictionary
    Args:
        vms (list[vim.VirtualMachine]): A list of VM object
    Returns:
        dict: A dictionary formatted for json dump containing the vms data
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
    return {"vms": vm_list}


def vm_metrics_info(vm: vim.VirtualMachine) -> dict:
    """
    Format VM metrics data to a json dictionary
    Args:
        vm (vim.VirtualMachine): The VM object where metrics are retrieved
    Returns:
        dict: A dictionary formatted for json dump containing the metrics data
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
    return json_object


def servers_list_info(hosts: list[vim.HostSystem]) -> dict:
    """
    Format Server data to a json dictionary
    Args:
        hosts (list[vim.HostSystem]): The list of `HostSystem` object where server data are retrieved
    Returns:
        dict: A dictionary formatted for json dump containing the servers data
    """
    host_json = [None] * len(hosts)
    for i, host in enumerate(hosts):
        host_json[i] = server_info(host)
    return {"servers": host_json}


def server_info(host: vim.HostSystem) -> dict:
    """
    Format Server data to a json dictionary
    Args:
        host (vim.HostSystem): The `HostSystem` object where server data are retrieved
    Returns:
        dict: A dictionary formatted for json dump containing the server data
    """
    return {
        "name": host.name,
        "moid": host._moId,
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


def server_metrics_info(host: vim.HostSystem) -> dict:
    """
    Format Server metrics data to a json dictionary
    Args:
       host (vim.HostSystem): The Host object where metrics are retrieved
    Returns:
       dict: A dictionary formatted for json dump containing the metrics data
    """
    if host.summary.quickStats.overallCpuUsage and host.hardware:
        cpu_usage = (host.summary.quickStats.overallCpuUsage / ((host.hardware.cpuInfo.hz / 1000000) * host.hardware.cpuInfo.numCpuCores)) * 100
    else:
        cpu_usage = 0
    return {
        "powerState": host.runtime.powerState,
        "overallStatus": host.overallStatus,
        "rebootRequired": host.summary.rebootRequired,
        "cpuUsagePercent": cpu_usage,
        "ramUsageMB": host.summary.quickStats.overallMemoryUsage,
        "uptime": host.summary.quickStats.uptime,
        "boottime": host.runtime.bootTime.isoformat() if host.runtime.bootTime else "",
    }
