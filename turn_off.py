from argparse import ArgumentParser
from pyVmomi import vim
from pyVim.task import WaitForTask

from vm_ware_connection import VMwareConnection


if __name__ == "__main__":
    parser = ArgumentParser(description="Éteins une VM sur un serveur ESXi")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID de la VM")
    parser.add_argument("--ip", required=True, help="Adresse IP du vCenter ou du serveur ESXi")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du vCenter ou du serveur ESXi")
    parser.add_argument("--password", required=True, help="Mot de passe du vCenter ou du serveur ESXi")
    parser.add_argument("--port", type=int, default=443, help="Port du vCenter ou du serveur ESXi")

    args = parser.parse_args()

    conn = VMwareConnection()
    try:
        conn.connect(args.ip, args.user, args.password, port=args.port)
        vm = conn.get_vm(args.moid)
        if vm:
            print(f"Power state : {vm.runtime.powerState}")
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                print("Power Off...")
                task = vm.PowerOff()
                WaitForTask(task)
            else:
                print("VM is already off")
            print(f"Power state : {vm.runtime.powerState}")
        else:
            print("VM not found")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()
