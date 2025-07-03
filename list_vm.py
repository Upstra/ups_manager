from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from argparse import ArgumentParser
import ssl


class Vm:
    def __init__(self, name: str, power_state: str, guest_os: str, ip: str):
        self.name = name
        self.power_state = power_state
        self.guest_os = guest_os
        self.ip = ip

    def to_json(self) -> dict[str, str]:
        """
        Convert the actual vm object to a json object
        Returns:
            dict[str, str]: A json dictionary with the keys name, power_state, guest_os and ip
        """
        return {
            "name": self.name,
            "power_state": self.power_state,
            "guest_os": self.guest_os,
            "ip": self.ip
        }


def to_json(vm: vim.VirtualMachine):
    return {
        "name": vm.name,
        "config": vm.config,
        "summary": vm.summary,
        "availableField": vm.availableField,
        "alarmActionsEnabled": vm.alarmActionsEnabled,
        "capability": vm.capability,
        "configIssue": vm.configIssue,
        "configStatus": vm.configStatus,
        "customValue": vm.customValue,
        "datastore": vm.datastore,
        "declaredAlarmState": vm.declaredAlarmState,
        "disabledMethod": vm.disabledMethod,
        "effectiveRole": vm.effectiveRole,
        "environmentBrowser": vm.environmentBrowser,
        "guest": vm.guest,
        "guestHeartbeatStatus": vm.guestHeartbeatStatus,
        "guest_os": vm.guest_os,
        "layout": vm.layout,
        "layoutEx": vm.layoutEx,
        "network": vm.network,
        "overallStatus": vm.overallStatus,
        "parent": vm.parent,
        "parentVApp": vm.parentVApp,
        "permission": vm.permission,
        "recentTask": vm.recentTask,
        "resourceConfig": vm.resourceConfig,
        "resourcePool": vm.resourcePool,
        "runtime": vm.runtime,
        "rootSnapshot": vm.rootSnapshot,
        "snapshot": vm.snapshot,
        "storage": vm.storage,
        "tag": vm.tag,
        "triggeredAlarmState": vm.triggeredAlarmState,
        "power_state": vm.power_state,
        "ip": vm.ip,
        "value": vm.value
    }


def get_vms(host: str, user: str, password: str, port=443) -> list[vim.VirtualMachine] | None:
    """
    Retrieves a list of virtual machines from a server host
    Args:
        host (str): The IP address or hostname of the server
        user (str): The username for authentication
        password (str): The password of the user
        port (int, optional): The port to use for the connection (default is 443)
    Returns:
        list[vim.VirtualMachine] | None: A list of `VirtualMachine` objects representing the discovered virtual machines,
        or `None` in case there is an error
    """
    context = ssl._create_unverified_context()
    try:
        si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
    except vim.fault.InvalidLogin as _:
        print("Mot de passe incorrect")
        return None
    except Exception as err:
        print(err)
        return None
    content = si.RetrieveContent()

    vms = []
    for datacenter in content.rootFolder.childEntity:
        vm_folder = datacenter.vmFolder
        vm_list = vm_folder.childEntity
        for vm in vm_list:
            if isinstance(vm, vim.VirtualMachine):
                print(to_json(vm))
                # vms.append(vm)
            else:
                print(f"Element is not a VirtualMachine : {vm}")

    Disconnect(si)
    return vms


if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    vms = get_vms(args.ip, args.user, args.password, args.port)
    # if vms is not None:
    #     for vm in vms:
    #         print(to_json(vm))
