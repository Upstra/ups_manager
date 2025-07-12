from argparse import ArgumentParser
from pyVmomi import vim

from data_retriever.dto import result_message, server_info
from data_retriever.vm_ware_connection import VMwareConnection


def server_data(moid: str, ip: str, user: str, password: str, port: int) -> str:
    """
    Retrieve data of a server from the ESXi server host or the VCenter
    Args:
        moid (str): The Managed Object ID of the server to get data from
        ip (str): The ip of the VCenter or the ESXI server to connect to
        user (str): The username of the VCenter or the ESXI server to connect to
        password (str): The password of the VCenter or the ESXI server to connect to
        port (int): The port to use to connect to the VCenter or the ESXI server
    Returns:
        str: A string formatted json dump with server data (server_info()), or an error message (result_message())
    """
    conn = VMwareConnection()
    try:
        conn.connect(ip, user, password, port=port)
        host = conn.get_host_system(moid)
        if not host:
            return result_message("Server not found", 404)

        return server_info(host)

    except vim.fault.InvalidLogin as _:
        return result_message("Invalid credentials", 401)
    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Récupérer les informations d'un serveur")
    parser.add_argument("--moid", required=True, help="Le Managed Object ID du serveur'")
    parser.add_argument("--ip", required=True, help="Adresse IP du serveur ESXi ou du vCenter")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du serveur ESXi ou du vCenter")
    parser.add_argument("--password", required=True, help="Mot de passe du serveur ESXi ou du vCenter")
    parser.add_argument("--port", type=int, default=443, help="Port du serveur ESXi ou du vCenter")

    args = parser.parse_args()

    print(server_data(args.moid, args.ip, args.user, args.password, args.port))
