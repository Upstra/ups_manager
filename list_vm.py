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

    def to_json(self):
        return {
            "name": self.name,
            "power_state": self.power_state,
            "guest_os": self.guest_os,
            "ip": self.ip
        }


def get_vms(host: str, user: str, password: str, port=443) -> list[Vm]:
    # Ignorer les vérifications SSL (attention en production)
    context = ssl._create_unverified_context()

    si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
    content = si.RetrieveContent()

    vms = []
    for datacenter in content.rootFolder.childEntity:
        vm_folder = datacenter.vmFolder
        vm_list = vm_folder.childEntity
        for vm in vm_list:
            if isinstance(vm, vim.VirtualMachine):
                vms.append(Vm(vm.name, vm.runtime.powerState, vm.config.guestFullName, vm.summary.guest.ipAddress))

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
    for vm in vms:
        print(vm.to_json())
