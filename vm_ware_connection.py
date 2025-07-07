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

def json_vms_info(vms: list[tuple[vim.VirtualMachine, str]]) -> str:
    """
    Format VMs data to a json dictionary
    Args:
        vms (list[tuple[vim.VirtualMachine, str]]): A list of VM object and name of the datacenter
    Returns:
        str: A string formatted json dump of the vms data
    """
    json_vms = {"vms": []}
    for vm, datacenter_name in vms:
        json_vms["vms"].append({
            "name": vm.name,
            "datacenter": datacenter_name,
            "hostName": vm.guest.hostName if vm.guest and vm.guest.hostName else "",
            "ip": vm.summary.guest.ipAddress if vm.summary.guest and vm.summary.guest.ipAddress else "",
            "guestOs": vm.config.guestFullName,
            "guestFamily": vm.guest.guestFamily if vm.guest else "",
            "version": vm.config.version,
            "createDate": vm.config.createDate.isoformat() if vm.config.createDate else "",
            "numCoresPerSocket": vm.config.hardware.numCoresPerSocket,
            "numCPU": vm.config.hardware.numCPU,
            "vmPathName": vm.summary.config.vmPathName
        })
    return json_dumps(json_vms, indent=2)

def json_metrics_info(vm: vim.VirtualMachine) -> str:
    """
    Format VM metrics data to a json dictionary
    Args:
        vm (vim.VirtualMachine): The VM object where metrics are retrieved
    Returns:
        str: A string formatted json dump of the metrics data
    """
    return json_dumps({
        "powerState": vm.runtime.powerState,
        "guestState": vm.guest.guestState if vm.guest else "",
        "connectionState": vm.runtime.connectionState,
        "guestHeartbeatStatus": vm.guestHeartbeatStatus,
        "overallStatus": vm.overallStatus,
        "overallCpuUsage": vm.summary.quickStats.overallCpuUsage if vm.summary.quickStats else 0,
        "maxCpuUsage": vm.runtime.maxCpuUsage,
        "guestMemoryUsage": vm.summary.quickStats.guestMemoryUsage if vm.summary.quickStats else 0,
        "maxMemoryUsage": vm.runtime.maxMemoryUsage,
        "uptimeSeconds": vm.summary.quickStats.uptimeSeconds if vm.summary.quickStats else 0,
        "usedStorage": vm.summary.storage.committed if vm.summary.storage else 0,
        "totalStorage": (vm.summary.storage.committed + vm.summary.storage.uncommitted) if vm.summary.storage else 0,
        "bootTime": vm.runtime.bootTime.isoformat() if vm.runtime.bootTime else "",
        "isMigrating": vm.runtime.vmFailoverInProgress,
        "swappedMemory": vm.summary.quickStats.swappedMemory if vm.summary.quickStats else 0
    }, indent=2)


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

    def get_all_vms(self) -> list[tuple[vim.VirtualMachine, str]]:
        """
        Get a list of VMs stored in the server
        Returns:
            list[tuple[vim.VirtualMachine, str]]: The list of VM object with corresponding datacenter name
        """
        vms = []
        if not self._si:
            return vms
        for datacenter in self._content.rootFolder.childEntity:
            datacenter_name = datacenter.name
            vm_folder = datacenter.vmFolder
            vm_list = vm_folder.childEntity
            for vm in vm_list:
                if isinstance(vm, vim.VirtualMachine):
                    vms.append((vm, datacenter_name))
        return vms

    def get_vm(self, vm_name: str, datacenter_name: str) -> vim.VirtualMachine:
        """
        Get a VM by name and datacenter location
        Args:
            vm_name (str): The name of the VM
            datacenter_name (str): The name of the datacenter where the VM is located
        Returns:
            vim.VirtualMachine: The VM object, or None if not found
        """
        if not self._si:
            return None
        search_index = self._content.searchIndex
        vm = search_index.FindByInventoryPath(f"{datacenter_name}/vm/{vm_name}")
        return vm

    def get_host_system(self, datacenter_name: str) -> vim.HostSystem:
        if not self._si:
            return None
        for datacenter in self._content.rootFolder.childEntity:
            if datacenter.name == datacenter_name:
                target_host = datacenter.hostFolder.childEntity[0].host[0]
                return target_host
        return None
