from json import dumps as json_dumps
from argparse import ArgumentParser

from vm_ware_connection import error_message, VMwareConnection, json_metrics_info

if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--vm", required=True, help="Le nom de la VM")
    parser.add_argument("--datacenter", required=True, help="Le nom du datacenter où est stocké la VM")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    conn = VMwareConnection(args.ip, args.user, args.password, port=args.port)
    vm = conn.get_vm(args.vm, args.datacenter)
    if vm:
        print(json_dumps(json_metrics_info(vm), indent=2))
    else:
        print(error_message("VM not found", 404))
    conn.disconnect()
