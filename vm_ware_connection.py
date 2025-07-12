from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl


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
