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
            print("\tBiosInfo")
            biosInfo = host.hardware.biosInfo
            [print(f"{attr}: {type(getattr(biosInfo, attr))}") for attr in dir(biosInfo) if attr[0] != '_' and attr[0].islower()]

            print("\tCpuFeature")
            cpuFeature = host.hardware.cpuFeature
            [print(f"{attr}: {type(getattr(cpuFeature, attr))}") for attr in dir(cpuFeature) if attr[0] != '_' and attr[0].islower()]

            print("\tCpuInfo")
            cpuInfo = host.hardware.cpuInfo
            [print(f"{attr}: {type(getattr(cpuInfo, attr))}") for attr in dir(cpuInfo) if attr[0] != '_' and attr[0].islower()]

            print("\tMemoryTierInfo")
            memoryTierInfo = host.hardware.memoryTierInfo
            [print(f"{attr}: {type(getattr(memoryTierInfo, attr))}") for attr in dir(memoryTierInfo) if attr[0] != '_' and attr[0].islower()]

            print("\tSystemInfo")
            systemInfo = host.hardware.systemInfo
            [print(f"{attr}: {type(getattr(systemInfo, attr))}") for attr in dir(systemInfo) if attr[0] != '_' and attr[0].islower()]

            print(json_server_info(host))
        else:
            print(error_message("Server not found", 404))
    except vim.fault.InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
    except Exception as err:
        print(error_message(str(err)))
    finally:
        conn.disconnect()
