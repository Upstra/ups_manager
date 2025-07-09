from argparse import ArgumentParser
from pyVmomi import vim
from pyVim.task import WaitForTask

from vm_ware_connection import VMwareConnection, json_metrics_info


if __name__ == "__main__":
    parser = ArgumentParser(description="Migrer une VM")
    parser.add_argument("--vmMoId", required=True, help="Le Managed Object ID de la VM")
    parser.add_argument("--distMoId", required=True, help="Le Managed Object ID du serveur ESXi destination")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    conn = VMwareConnection()
    try:
        conn.connect(args.ip, args.user, args.password, port=args.port)
        vm = conn.get_vm(args.vmMoId)
        if vm:
            print(json_metrics_info(vm))
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                print("Power Off...")
                task = vm.PowerOff()
                WaitForTask(task)
            else:
                print("VM is off")
            print("Migration to distant server...")
            target_host = conn.get_host_system(args.distMoId)
            target_resource_pool = target_host.parent.resourcePool
            task = vm.Migrate(
                pool=target_resource_pool,
                host=target_host,
                priority=vim.VirtualMachine.MovePriority.defaultPriority
            )
            WaitForTask(task)
            print("Power On...")
            task = vm.PowerOn()
            WaitForTask(task)
            print(json_metrics_info(vm))
            print(f"esxiHostName: {vm.runtime.host.name}")
            print(f"esxiHostMoid: {vm.runtime.host.moref.value}")
        else:
            print("VM not found")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()
