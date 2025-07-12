from argparse import ArgumentParser
from pyVmomi import vim
from pyVim.task import WaitForTask

from data_retriever.dto import result_message, output
from data_retriever.vm_ware_connection import VMwareConnection


def vm_migration(vm: vim.VirtualMachine, vm_name: str, target_host: vim.HostSystem, target_moid: str) -> dict:
    """
    Migrate a VM to a different host
    Args:
        vm (vim.VirtualMachine): The `VirtualMachine` object representing the VM to migrate
        vm_name (str): The name of the VM to migrate for logging
        target_host (vim.HostSystem): The `HostSystem` object representing the server to migrate to
        target_moid (str): The Managed Object ID of the server to migrate to
    Returns:
        dict: A dictionary formatted for json dump containing the result message. See result_message() function in dto.py
    """
    try:
        if not vm:
            return result_message(f"VM '{vm_name}' not found", 404)
        if vm.runtime.host._moId == target_moid:
            return result_message(f"VM '{vm_name}' is already on this server", 403)
        if not target_host:
            return result_message(f"Target server '{target_moid}' not found", 404)
        if target_host.runtime.powerState == vim.HostSystem.PowerState.poweredOff:
            return result_message(f"Target server '{target_moid}' is off. Turn it on before launching a migration", 403)

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
        return result_message(f"VM '{vm_name}' migrated successfully", 200)

    except Exception as err:
        return result_message(str(err), 400)


def complete_vm_migration(vm_moid: str, dist_moid: str,  ip: str, user: str, password: str, port: int) -> dict:
    """
    Migrate a VM to a different host by creating a connection to the VCenter or the ESXI server
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
        target_host = conn.get_host_system(dist_moid)

        return vm_migration(vm, target_host, dist_moid)

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

    output(complete_vm_migration(args.vm_moid, args.dist_moid, args.ip, args.user, args.password, args.port))
