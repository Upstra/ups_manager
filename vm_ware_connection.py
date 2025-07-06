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
        str: A json dump of the error message
    """
    return json_dumps({
        "error": {
            "message": message,
            "httpCode": http_code
        }
    })

def json_vm_info(vm: vim.VirtualMachine, datacenter_name: str) -> dict:
    """
    Format VM data to a json dictionary
    Args:
        vm (vim.VirtualMachine): The VM object where data is retrieved
        datacenter_name (str): The name of the datacenter where the VM is stored for search function
    Returns:
        dict: A dictionary formatted for json dumps
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

def json_metrics_info(vm: vim.VirtualMachine) -> dict:
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


class VMwareConnection:
    def __init__(self, host: str, user: str, password: str, port=443, verified_ssl=False):
        """
        Create an object to connect to a distant server containing a VMware architecture and to help manipulate VMs
        stored on this server
        Args:
            host (str): The IP address or hostname of the server
            user (str): The username for authentication
            password (str): The password of the user
            port (int): The port to use for the connection (default to 443)
            verified_ssl (bool): Whether or not to verify the SSL certificate (default to False)
        """
        self._content = None
        self._si = None
        self._connect(host, user, password, port, verified_ssl)

    def _connect(self, host: str, user: str, password: str, port: int, verified_ssl: bool):
        """
        Connect to the server where VMs are located
        Args:
            host (str): The IP address or hostname of the server
            user (str): The username for authentication
            password (str): The password of the user
            port (int): The port to use for the connection
            verified_ssl (bool): Whether or not to verify the SSL certificate
        """
        context = ssl.create_default_context()
        if not verified_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        try:
            self._si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
        except vim.fault.InvalidLogin as _:
            print(error_message("Invalid credentials", 401))
            return
        except Exception as err:
            print(error_message(str(err)))
            return
        self._content = self._si.RetrieveContent()

    def disconnect(self):
        """ Close the connection with the server where VMs are located """
        if self._si:
            Disconnect(self._si)
        self._content = None
        self._si = None

    def list_vm(self):
        """ Print a list of virtual machines from a server host """
        if not self._si:
            return
        vms = {"vms": []}
        for datacenter in self._content.rootFolder.childEntity:
            datacenter_name = datacenter.name
            vm_folder = datacenter.vmFolder
            vm_list = vm_folder.childEntity
            for vm in vm_list:
                if isinstance(vm, vim.VirtualMachine):
                    vms["vms"].append(json_vm_info(vm, datacenter_name))
        print(json_dumps(vms))

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
