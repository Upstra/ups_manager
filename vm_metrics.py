from argparse import ArgumentParser
from pyVmomi import vim

from dto import vm_metrics_info, result_message
from vm_ware_connection import VMwareConnection


def vm_metrics(moid: str, ip: str, user: str, password: str, port: int) -> str:
    """
    Retrieve metrics of a VM from a VCenter or an ESXi server
    Args:
        moid (str): The Managed Object ID of the VM to get metrics from
        ip (str): The ip of the VCenter or the ESXI server to connect to
        user (str): The username of the VCenter or the ESXI server to connect to
        password (str): The password of the VCenter or the ESXI server to connect to
        port (int): The port to use to connect to the VCenter or the ESXI server
    Returns:
        str: A string formatted json dump with VM metrics (vm_metrics_info()), or an error message (result_message())
    """
    conn = VMwareConnection()
    try:
        conn.connect(ip, user, password, port=port)
        vm = conn.get_vm(moid)
        if not vm:
            return result_message("VM not found", 404)

        return vm_metrics_info(vm)

    except vim.fault.InvalidLogin as _:
        return result_message("Invalid credentials", 401)
    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Récupérer les métriques d'une VM")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID de la VM'")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    print(vm_metrics(args.moid, args.ip, args.user, args.password, args.port))
