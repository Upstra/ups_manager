#!/usr/bin/env python

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
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
    context = ssl._create_unverified_context() #

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
