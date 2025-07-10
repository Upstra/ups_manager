from json import dumps as json_dumps
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl


def error_message(message: str, http_code = 400) -> str:
    """
    Dump a json formatted error message
    Args:
        message (str): The message explaining the error
        http_code (int): The HTTP response code corresponding to the error (defaults to 400)
    Returns:
        str: A string formatted json dump of the error message
    """
    return json_dumps({
        "error": {
            "message": message,
            "httpCode": http_code
        }
    }, indent=2)

def json_vms_info(vms: list[vim.VirtualMachine]) -> str:
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

def json_metrics_info(vm: vim.VirtualMachine) -> str:
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


def json_server_info(host: vim.HostSystem) -> str:
    """
    Format Server data data to a json dictionary
    Args:
        host (vim.HostSystem): The Host object where server data are retrieved
    Returns:
        str: A string formatted json dump of the server data
    """
    json_object = {
        "name": host.name,
        "overallStatus": host.overallStatus,
        "cpuCores": host.hardware.cpuInfo.numCpuCores,
        "ramTotal": int(host.hardware.memorySize / (1024 ** 3)),
        "rebootRequired": host.summary.rebootRequired,
        "managementServerIp": host.summary.managementServerIp,
        "maxEVCModeKey": host.summary.maxEVCModeKey,
        "cpuUsageMHz": host.summary.quickStats.overallCpuUsage,
        "ramUsageMB": host.summary.quickStats.overallMemoryUsage,
        "availablePMemCapacity": host.summary.quickStats.availablePMemCapacity,
        "distributedCpuFairness": host.summary.quickStats.distributedCpuFairness,
        "distributedMemoryFairness": host.summary.quickStats.distributedMemoryFairness,
        "uptime": host.summary.quickStats.uptime,
        "cluster": host.parent.name
    }
    return json_dumps(json_object, indent=2)


class VMwareConnection:
    def __init__(self):
        self._content = None
        self._si = None

    def connect(self, host: str, user: str, password: str, port=443, verified_ssl=False):
        """
        Connect to the server where VMs are located
        Args:
            host (str): The IP address or hostname of the server
            user (str): The username for authentication
            password (str): The password of the user
            port (int): The port to use for the connection (default to 443)
            verified_ssl (bool): Whether or not to verify the SSL certificate (default to False)
        Raises:
            vim.fault.InvalidLogin: If credentials are invalid
            Exception: If connection fails for any reason
        """
        context = ssl.create_default_context()
        if not verified_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        self._si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
        self._content = self._si.RetrieveContent()

    def disconnect(self):
        """ Close the connection with the server where VMs are located """
        if self._si:
            Disconnect(self._si)
        self._content = None
        self._si = None

    def get_all_vms(self) -> list[vim.VirtualMachine]:
        """
        Get a list of VMs stored in the server
        Returns:
            list[vim.VirtualMachine]: The list of VM object
        """
        def collect_vms_from_folder(folder, vms):
            for entity in folder.childEntity:
                if isinstance(entity, vim.VirtualMachine):
                    vms.append(entity)
                elif isinstance(entity, vim.Folder):
                    collect_vms_from_folder(entity, vms)

        vms = []
        if not self._si:
            return vms
        for datacenter in self._content.rootFolder.childEntity:
            vm_folder = datacenter.vmFolder
            vm_list = vm_folder.childEntity
            for entity in vm_list:
                if isinstance(entity, vim.VirtualMachine):
                    vms.append(entity)
                elif isinstance(entity, vim.Folder):
                    collect_vms_from_folder(entity, vms)
        return vms

    def get_vm(self, moid: str) -> vim.VirtualMachine:
        """
        Get a VM by its MoId
        Args:
            moid (str): The Managed Object ID of the VM
        Returns:
            vim.VirtualMachine: The VM object, or None if not found
        """
        def search_moid_in_folder(folder, moid):
            for entity in folder.childEntity:
                if isinstance(entity, vim.VirtualMachine):
                    if entity._moId == moid:
                        return entity
                elif isinstance(entity, vim.Folder):
                    vm = search_moid_in_folder(entity, moid)
                    if vm:
                        return vm
            return None

        if not self._si:
            return None

        for datacenter in self._content.rootFolder.childEntity:
            vm_folder = datacenter.vmFolder
            vm = search_moid_in_folder(vm_folder, moid)
            if vm:
                return vm
        return None

    def get_host_system(self, esxi_moid: str) -> vim.HostSystem:
        """
        Find a HostSystem object by its MoRef ID (moid)
        Args:
            esxi_moid (str): The Managed Object ID of the host
        Returns:
            vim.HostSystem: The HostSystem object, or None if not found
        """
        if not self._content:
            return None

        for datacenter in self._content.rootFolder.childEntity:
            host_folder = datacenter.hostFolder
            for compute_resource in host_folder.childEntity:
                if hasattr(compute_resource, 'host'):
                    hosts = compute_resource.host
                else:
                    hosts = [compute_resource]

                for host in hosts:
                    if host._moId == esxi_moid:
                        return host
        return None

