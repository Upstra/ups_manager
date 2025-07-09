from argparse import ArgumentParser
from pyVmomi import vim

from vm_ware_connection import error_message, VMwareConnection, json_metrics_info


if __name__ == "__main__":
    parser = ArgumentParser(description="Récupérer les métriques d'une VM")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID de la VM'")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    conn = VMwareConnection()
    try:
        conn.connect(args.ip, args.user, args.password, port=args.port)
        vm = conn.get_vm(args.moid)
        if vm:
            print(json_metrics_info(vm))
        else:
            print(error_message("VM not found", 404))
    except vim.fault.InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
    except Exception as err:
        print(error_message(str(err)))
    finally:
        conn.disconnect()
