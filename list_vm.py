from argparse import ArgumentParser
from pyVmomi.vim.fault import InvalidLogin

from vm_ware_connection import VMwareConnection, error_message


if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur")

    args = parser.parse_args()

    conn = VMwareConnection()
    try:
        conn.connect(args.ip, args.user, args.password, port=args.port)
        conn.list_vm()
    except InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
    except Exception as err:
        print(error_message(str(err)))
    finally:
        conn.disconnect()
