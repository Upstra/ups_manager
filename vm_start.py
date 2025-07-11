from argparse import ArgumentParser
from pyVmomi import vim
from pyVim.task import WaitForTask

from dto import result_message
from vm_ware_connection import VMwareConnection


def vm_start(moid: str, ip: str, user: str, password: str, port: int) -> str:
    """
    Start a VM
    Args:
        moid (str): The Managed Object ID of the VM to start
        ip (str): The ip of the VCenter or the ESXI server to connect to
        user (str): The username of the VCenter or the ESXI server to connect to
        password (str): The password of the VCenter or the ESXI server to connect to
        port (int): The port to use to connect to the VCenter or the ESXI server
    Returns:
        str: A string formatted json dump of the result message
    """
    conn = VMwareConnection()
    try:
        conn.connect(ip, user, password, port=port)
        vm = conn.get_vm(moid)
        if not vm:
            return result_message("VM not found", 404)
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            return result_message("VM is already on", 403)

        task = vm.PowerOn()
        WaitForTask(task)
        return result_message("VM has been successfully started")

    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Allume une VM sur un serveur ESXi")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID de la VM")
    parser.add_argument("--ip", required=True, help="Adresse IP du vCenter ou du serveur ESXi")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du vCenter ou du serveur ESXi")
    parser.add_argument("--password", required=True, help="Mot de passe du vCenter ou du serveur ESXi")
    parser.add_argument("--port", type=int, default=443, help="Port du vCenter ou serveur ESXi (optionnel, 443 par défaut)")

    args = parser.parse_args()

    print(vm_start(args.moid, args.ip, args.user, args.password, args.port))
