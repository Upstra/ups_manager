from argparse import ArgumentParser
from pyVim.task import WaitForTask

from vm_ware_connection import VMwareConnection, json_metrics_info


if __name__ == "__main__":
    parser = ArgumentParser(description="Allume une VM sur un serveur ESXi")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID de la VM")
    parser.add_argument("--ip", required=True, help="Adresse IP du vCenter ou du serveur ESXi")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du vCenter ou du serveur ESXi")
    parser.add_argument("--password", required=True, help="Mot de passe du vCenter ou du serveur ESXi")
    parser.add_argument("--port", type=int, default=443, help="Port du vCenter ou serveur ESXi (optionnel, 443 par défaut)")

    args = parser.parse_args()

    conn = VMwareConnection()
    try:
        conn.connect(args.ip, args.user, args.password, port=args.port)
        vm = conn.get_vm(args.moid)
        if vm:
            print(json_metrics_info(vm))
            if vm.runtime.powerState == "poweredOff":
                print("Power On...")
                task = vm.PowerOn()
                WaitForTask(task)
            else:
                print("VM is already on")
            print(json_metrics_info(vm))
        else:
            print("VM not found")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()
