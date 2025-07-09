from argparse import ArgumentParser
from pyVmomi import vim

from vm_ware_connection import VMwareConnection, error_message

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
            hardware = host.hardware
            summary = host.summary
            stats = host.summary.quickStats

            print([attr for attr in dir(host) if attr[0] != '_' and attr[0].islower()])
            print([attr for attr in dir(hardware) if attr[0] != '_' and attr[0].islower()])
            print([attr for attr in dir(summary) if attr[0] != '_' and attr[0].islower()])
            print([attr for attr in dir(stats) if attr[0] != '_' and attr[0].islower()])

            print(f"Nom: {host.name}")
            print(f"CPU cores: {hardware.cpuInfo.numCpuCores}")
            print(f"RAM totale: {hardware.memorySize / (1024 ** 3):.2f} GB")
            print(f"CPU usage: {stats.overallCpuUsage} MHz")
            print(f"RAM usage: {stats.overallMemoryUsage} MB")
            print(f"Etat général: {summary.overallStatus}")
        else:
            print(error_message("Server not found", 404))
    except vim.fault.InvalidLogin as _:
        print(error_message("Invalid credentials", 401))
    except Exception as err:
        print(error_message(str(err)))
    finally:
        conn.disconnect()
