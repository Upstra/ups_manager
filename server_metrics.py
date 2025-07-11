from argparse import ArgumentParser
from pyVmomi import vim

from vm_ware_connection import VMwareConnection, error_message, json_server_info

if __name__ == "__main__":
    parser = ArgumentParser(description="Récupérer les métriques d'un serveur")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID du serveur'")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur ESXi ou du vCenter")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du serveur ESXi ou du vCenter")
    parser.add_argument("--password", required=True, help="Mot de passe du serveur ESXi ou du vCenter")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur ESXi ou du vCenter")

    args = parser.parse_args()

    conn = VMwareConnection()
    try:
        conn.connect(args.ip, args.user, args.password, port=args.port)
        host = conn.get_host_system(args.moid)
        if host:
            print(json_server_info(host))
        else:
            print(error_message("Server not found", 404))
    except vim.fault.InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
    except Exception as err:
        print(error_message(str(err)))
    finally:
        conn.disconnect()
