from yaml import safe_load as yaml_load
from time import sleep
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import List


@dataclass
class VMAction:
    order: List[str]
    delay: int

@dataclass
class VMs:
    shutdown: VMAction
    restart: VMAction

@dataclass
class Server:
    name: str
    ip: str
    destination: str
    vms: VMs


def load_plan_from_yaml(file_path: str) -> list[Server]:
    """
    Load a migration plan stored in a YAML file
    Args:
        file_path (str): The path to the migration plan
    Returns:
        list[Server]: A list of `Server` objects representing the migration plan for each server
    """
    with open(file_path, 'r') as f:
        data = yaml_load(f)['servers']

    servers = []
    for server in data:
        servers.append(
            Server(
                name=server['name'],
                ip=server['ip'],
                destination=server['destination'],
                vms=VMs(
                    shutdown=VMAction(**server['vms']['shutdown']),
                    restart=VMAction(**server['vms']['restart'])
                )
            )
        )
    return servers


def restart_plan(servers: list[Server]) -> None:
    """
    Launch the restart plan of all servers specified in `servers` to go back to the initial state
    Args:
        servers (list[Server]): The migration plan for each server
    """
    for server in servers:
        print(f"Migration du serveur {server.name}")
        ip = server.ip
        destination = server.destination
        vms = server.vms.restart.order
        start_delay = server.vms.restart.delay
        for vm in vms:
            print(f"Power ON: {vm}")
            sleep(start_delay)


def shutdown_plan(servers: list[Server]) -> None:
    """
    Launch the shutdown plan of all servers specified in `servers` to migrate each vm to a distant server
    Args:
        servers (list[Server]): The migration plan for each server
    """
    for server in servers:
        print(f"Migration du serveur {server.name}")
        ip = server.ip
        destination = server.destination
        vms = server.vms.shutdown.order
        stop_delay = server.vms.shutdown.delay
        for vm in vms:
            print(f"Power OFF: {vm}")
            sleep(stop_delay)

if __name__ == "__main__":
    parser = ArgumentParser(description="Migration des vms")
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument("--plan", required=True, help="Fichier contenant le plan de migration")
    group.add_argument("--shutdown", action="store_true", help="Éteindre les VM et migrer sur le serveur distant")
    group.add_argument("--restart", action="store_true", help="Migrer les VM depuis le serveur distant et les redémarrer")

    args = parser.parse_args()

    servers = load_plan_from_yaml(args.plan)

    if args.shutdown:
        print("Lancement du plan de migration...")
        shutdown_plan(servers)
    elif args.restart:
        print("Lancement du plan de redémarrage...")
        restart_plan(servers)
    else:
        print("ERREUR: Utilisez --shutdown ou --restart")
