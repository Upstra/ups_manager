from argparse import ArgumentParser
from pyVmomi import vim
from pyVim.task import WaitForTask
import socket

from data_retriever.dto import result_message, output
from data_retriever.vm_ware_connection import VMwareConnection


def vm_stop(vm: vim.VirtualMachine, name: str) -> dict:
    """
    Stop a VM
    Args:
        vm (vim.VirtualMachine): The `VirtualMachine` object representing the VM to stop
        name (str): The name of the VM to stop for logging
    Returns:
        dict: A dictionary formatted for json dump containing the result message. See result_message() function in dto.py
    """
    try:
        if not vm:
            return result_message(f"VM '{name}' not found", 404)
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
            return result_message(f"VM '{name}' is already off", 403)

        task = vm.PowerOff()
        WaitForTask(task)
        return result_message(f"VM '{name}' has been successfully stopped", 200)

    except (vim.fault.NoCompatibleHost, vim.fault.InvalidHostState, OSError, socket.error):
        return result_message("Host is unreachable", 404)
    except vim.fault.TaskInProgress:
        return result_message(f"VM '{name}' is busy", 403)
    except (vim.fault.InvalidPowerState, vim.fault.VimFault):
        return result_message(f"VM '{name}' can't be stopped", 403)
    except Exception as err:
        return result_message(str(err), 400)


def complete_vm_stop(moid: str, ip: str, user: str, password: str, port: int) -> dict:
    """
    Stop a VM by creating a connection to the VCenter
    Args:
        moid (str): The Managed Object ID of the VM to stop
        ip (str): The ip of the VCenter to connect to
        user (str): The username of the VCenter to connect to
        password (str): The password of the VCenter to connect to
        port (int): The port to use to connect to the VCenter
    Returns:
        dict: A dictionary formatted for json dump containing the result message. See result_message() function in dto.py
    """
    conn = VMwareConnection()
    try:
        conn.connect(ip, user, password, port=port)
        vm = conn.get_vm(moid)

        return vm_stop(vm, moid)

    except vim.fault.InvalidLogin:
        return result_message("Invalid credentials", 401)
    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Éteins une VM sur un serveur ESXi")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID de la VM")
    parser.add_argument("--ip", required=True, help="Adresse IP du vCenter")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du vCenter")
    parser.add_argument("--password", required=True, help="Mot de passe de l'utilisateur du vCenter")
    parser.add_argument("--port", type=int, default=443, help="Port du vCenter (optionnel, 443 par défaut)")

    args = parser.parse_args()

    output(complete_vm_stop(args.moid, args.ip, args.user, args.password, args.port))
