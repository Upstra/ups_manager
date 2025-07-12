from argparse import ArgumentParser
from pyVmomi import vim
from pyVim.task import WaitForTask

from data_retriever.dto import result_message, output
from data_retriever.vm_ware_connection import VMwareConnection


def vm_migration(vm_moid: str, dist_moid: str,  ip: str, user: str, password: str, port: int) -> dict:
    """
    Migrate a VM to a different host
    Args:
        vm_moid (str): The Managed Object ID of the VM to migrate
        dist_moid (str): The Managed Object ID of the server where to migrate the VM
        ip (str): The ip of the VCenter or the ESXI server to connect to
        user (str): The username of the VCenter or the ESXI server to connect to
        password (str): The password of the VCenter or the ESXI server to connect to
        port (int): The port to use to connect to the VCenter or the ESXI server
    Returns:
        dict: A dictionary formatted for json dump containing the result message. See result_message() function in dto.py
    """
    conn = VMwareConnection()
    try:
        conn.connect(ip, user, password, port=port)
        vm = conn.get_vm(vm_moid)
        if not vm:
            return result_message("VM not found", 404)
        if vm.runtime.host._moId == dist_moid:
            return result_message("VM is already on this server", 403)
        target_host = conn.get_host_system(dist_moid)
        if not target_host:
            return result_message("Target server not found", 404)
        if target_host.runtime.powerState == vim.HostSystem.PowerState.poweredOff:
            return result_message("Target server is off", 403)

        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            task = vm.PowerOff()
            WaitForTask(task)

        target_resource_pool = target_host.parent.resourcePool
        task = vm.Migrate(
            pool=target_resource_pool,
            host=target_host,
            priority=vim.VirtualMachine.MovePriority.defaultPriority
        )
        WaitForTask(task)
        task = vm.PowerOn()
        WaitForTask(task)
        return result_message("VM migrated successfully", 200)

    except vim.fault.InvalidLogin as _:
        return result_message("Invalid credentials", 401)
    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Migrer une VM")
    parser.add_argument("--vm_moid", required=True, help="Le Managed Object ID de la VM")
    parser.add_argument("--dist_moid", required=True, help="Le Managed Object ID du serveur ESXi destination")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    output(vm_migration(args.vm_moid, args.dist_moid, args.ip, args.user, args.password, args.port))
