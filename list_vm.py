from argparse import ArgumentParser
from pyVmomi import vim
import socket

from data_retriever.dto import result_message, vms_list_info, output
from data_retriever.vm_ware_connection import VMwareConnection


def list_vm(ip: str, user: str, password: str, port: int) -> dict:
    """
    List all VMs on a server
    Args:
        ip (str): The ip of the VCenter to connect to
        user (str): The username of the VCenter to connect to
        password (str): The password of the VCenter to connect to
        port (int): The port to use to connect to the VCenter
    Returns:
        dict: A dictionary formatted for json dump containing the VMs data (vms_list_info()), or an error message (result_message())
    """
    conn = VMwareConnection()
    try:
        conn.connect(ip, user, password, port=port)
        vms = conn.get_all_vms()
        return vms_list_info(vms)

    except vim.fault.InvalidLogin:
        return result_message("Invalid credentials", 401)
    except (vim.fault.NoCompatibleHost, vim.fault.InvalidHostState, OSError, socket.error):
        return result_message("Host is unreachable", 404)
    except vim.fault.VimFault:
        return result_message("Can't list VMs", 403)
    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP du vCenter")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du vCenter")
    parser.add_argument("--password", required=True, help="Mot de passe de l'utilisateur du vCenter")
    parser.add_argument("--port", type=int, default=443, help="Port du vCenter (optionnel, 443 par défaut)")

    args = parser.parse_args()

    output(list_vm(args.ip, args.user, args.password, args.port))
