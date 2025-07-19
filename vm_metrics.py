from argparse import ArgumentParser
from pyVmomi import vim, vmodl

from data_retriever.dto import vm_metrics_info, result_message, output
from data_retriever.vm_ware_connection import VMwareConnection


def vm_metrics(moid: str, ip: str, user: str, password: str, port: int) -> dict:
    """
    Retrieve metrics of a VM from a VCenter
    Args:
        moid (str): The Managed Object ID of the VM to get metrics from
        ip (str): The ip of the VCenter to connect to
        user (str): The username of the VCenter to connect to
        password (str): The password of the VCenter to connect to
        port (int): The port to use to connect to the VCenter
    Returns:
        dict: A dictionary formatted for json dump containing the VM metrics (vm_metrics_info()), or an error message (result_message())
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
    except (vim.fault.NoCompatibleHost, vim.fault.InvalidHostState, vim.fault.HostNotConnected, vmodl.fault.HostCommunication):
        return result_message("Host is unreachable", 404)
    except (vim.fault.VimFault, vmodl.MethodFault):
        return result_message(f"Can't get metrics from VM '{moid}'", 403)
    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Récupérer les métriques d'une VM")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID de la VM")
    parser.add_argument("--ip", required=True, help="Adresse IP du vCenter")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du vCenter")
    parser.add_argument("--password", required=True, help="Mot de passe de l'utilisateur du vCenter")
    parser.add_argument("--port", type=int, default=443, help="Port du vCenter (optionnel, 443 par défaut)")

    args = parser.parse_args()

    output(vm_metrics(args.moid, args.ip, args.user, args.password, args.port))
