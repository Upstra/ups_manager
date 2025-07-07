from yaml import safe_load as yaml_load
from time import sleep
from argparse import ArgumentParser
from dataclasses import dataclass

from vm_ware_connection import VMwareConnection


@dataclass
class VM:
    name: str
    datacenter: str

@dataclass
class VMAction:
    order: list[VM]
    delay: int

@dataclass
class VMs:
    shutdown: VMAction
    restart: VMAction

@dataclass
class Server:
    name: str
    ip: str
    host: str
    password: str
    destination: str
    vms: VMs


def load_plan_from_yaml(file_path: str) -> list[Server]:
    """
    Load a migration plan stored in a YAML file
    Args:
        file_path (str): The path to the migration plan
    Returns:
        list[Server]: A list of `Server` objects representing the migration plan for each server
    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
        KeyError: If required keys are missing from the YAML structure
     """
    try:
        with open(file_path, 'r') as f:
            yaml_data = yaml_load(f)
            if not yaml_data or 'servers' not in yaml_data:
                raise KeyError("YAML file must contain 'servers' key")
            data = yaml_data['servers']
    except FileNotFoundError:
        raise FileNotFoundError(f"Migration plan file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error parsing YAML file: {e}")

    servers = []
    for server in data:
        servers.append(
            Server(
                name=server['name'],
                ip=server['ip'],
                host=server['host'],
                password=server['password'],
                destination=server['destination'],
                vms=VMs(
                    shutdown=VMAction(
                        order=[VM(name=vm['vm']['name'], datacenter=vm['vm']['datacenter']) for vm in server['vms']['shutdown']['order']],
                        delay=server['vms']['shutdown']['delay']
                    ),
                    restart=VMAction(
                        order=[VM(name=vm['vm']['name'], datacenter=vm['vm']['datacenter']) for vm in server['vms']['restart']['order']],
                        delay=server['vms']['restart']['delay']
                    ),
                )
            )
        )
    return servers


def turn_on_vms(servers: list[Server]):
    """
    Launch the restart plan of all servers specified in `servers` to go back to the initial state
    Args:
        servers (list[Server]): The migration plan for each server
    """
    conn = VMwareConnection()

    for server in servers:
        print(f"Allumage du serveur {server.name}")
        ip = server.ip
        user = server.host
        password = server.password
        vms = server.vms.restart.order
        start_delay = server.vms.restart.delay
        try:
            conn.connect(ip, user, password)
            vms_found = conn.get_all_vms()
            for vm_info in vms:
                for vm, datacenter in vms_found:
                    if vm.name == vm_info.name and datacenter == vm_info.datacenter:
                        vm.PowerOn()
                        sleep(start_delay)
                        break
        except Exception as err:
            print(err)
        finally:
            conn.disconnect()


def turn_off_vms(servers: list[Server]):
    """
    Launch the shutdown plan of all servers specified in `servers` to migrate each vm to a distant server
    Args:
        servers (list[Server]): The migration plan for each server
    """
    conn = VMwareConnection()

    for server in servers:
        print(f"Extinction du serveur {server.name}")
        ip = server.ip
        user = server.host
        password = server.password
        vms = server.vms.shutdown.order
        stop_delay = server.vms.shutdown.delay
        try:
            conn.connect(ip, user, password)
            vms_found = conn.get_all_vms()
            for vm_info in vms:
                for vm, datacenter in vms_found:
                    if vm.name == vm_info.name and datacenter == vm_info.datacenter:
                        vm.PowerOff()
                        sleep(stop_delay)
                        break
        except Exception as err:
            print(err)
        finally:
            conn.disconnect()


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
        turn_off_vms(servers)
    elif args.restart:
        print("Lancement du plan de redémarrage...")
        turn_on_vms(servers)
    else:
        print("ERREUR: Utilisez --shutdown ou --restart")
