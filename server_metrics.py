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
            capability = host.capability
            print("\tcapability")
            [print(f"{attr}: {type(getattr(capability, attr))}") for attr in dir(capability) if attr[0] != '_' and attr[0].islower()]

            config = host.config
            print("\tconfig")
            [print(f"{attr}: {type(getattr(config, attr))}") for attr in dir(config) if attr[0] != '_' and attr[0].islower()]

            configManager = host.configManager
            [print(f"{attr}: {type(getattr(configManager, attr))}") for attr in dir(configManager) if attr[0] != '_' and attr[0].islower()]

            configStatus = host.configStatus
            [print(f"{attr}: {type(getattr(configStatus, attr))}") for attr in dir(configStatus) if attr[0] != '_' and attr[0].islower()]

            network = host.network[0]
            [print(f"{attr}: {type(getattr(network, attr))}") for attr in dir(network) if attr[0] != '_' and attr[0].islower()]

            parent = host.parent
            [print(f"{attr}: {type(getattr(parent, attr))}") for attr in dir(parent) if attr[0] != '_' and attr[0].islower()]

            runtime = host.runtime
            [print(f"{attr}: {type(getattr(runtime, attr))}") for attr in dir(runtime) if attr[0] != '_' and attr[0].islower()]

            systemResources = host.systemResources
            [print(f"{attr}: {type(getattr(systemResources, attr))}") for attr in dir(systemResources) if attr[0] != '_' and attr[0].islower()]

            print(json_server_info(host))
        else:
            print(error_message("Server not found", 404))
    except vim.fault.InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
    except Exception as err:
        print(error_message(str(err)))
    finally:
        conn.disconnect()
