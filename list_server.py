from argparse import ArgumentParser
from pyVmomi import vim

from data_retriever.dto import result_message, output, servers_list_info
from data_retriever.vm_ware_connection import VMwareConnection


def list_server(ip: str, user: str, password: str, port: int) -> dict:
    """
    List all servers on an architecture
    Args:
        ip (str): The ip of the VCenter to retrieve data from
        user (str): The username of the VCenter to retrieve data from
        password (str): The password of the VCenter to retrieve data from
        port (int): The port to use to connect to the VCenter
    Returns:
        dict: A dictionary formatted for json dump containing the Servers data (servers_list_info()), or an error message (result_message())
    """
    conn = VMwareConnection()
    try:
        conn.connect(ip, user, password, port=port)
        hosts = conn.get_all_hosts()
        return servers_list_info(hosts)

    except vim.fault.InvalidLogin as _:
        return result_message("Invalid credentials", 401)
    except Exception as err:
        return result_message(str(err), 400)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(description="Lister les VM d'un serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP du vCenter")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur du vCenter")
    parser.add_argument("--password", required=True, help="Mot de passe de l'utilisateur du vCenter")
    parser.add_argument("--port", type=int, default=443, help="Port du vCenter")

    args = parser.parse_args()

    output(list_server(args.ip, args.user, args.password, args.port))
