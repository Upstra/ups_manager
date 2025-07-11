from yaml import safe_load as yaml_load
from time import sleep
from argparse import ArgumentParser
from dataclasses import dataclass
from os.path import join as path_join
from pyVim.task import WaitForTask
from pyVmomi import vim

from vm_ware_connection import VMwareConnection


@dataclass
class Shutdown:
    vmOrder: list[str]
    delay: int

@dataclass
class Restart:
    delay: int

@dataclass
class Server:
    name: str
    moid: str
    destination: str
    shutdown: Shutdown
    restart: Restart

@dataclass
class Servers:
    servers: list[Server]

@dataclass
class VCenter:
    ip: str
    user: str
    password: str
    port: int


def load_plan_from_yaml(file_path: str) -> tuple[VCenter, Servers]:
    """
    Load a migration plan stored in a YAML file
    Args:
        file_path (str): The path to the migration plan
    Returns:
        tuple[VCenter, Servers]: A `VCenter` object and a list of `Server` objects representing the migration plan
    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
        KeyError: If required keys are missing from the YAML structure
     """
    try:
        with open(file_path, 'r') as f:
            data = yaml_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Migration plan file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error parsing YAML file: {e}")

    v_center = VCenter(
        ip=data['vCenter']['ip'],
        user=data['vCenter']['user'],
        password=data['vCenter']['password'],
        port=data['vCenter']['port'] if 'port' in data['vCenter'] else 443,
    )

    servers = Servers(servers=[None] * len(data['servers']))
    for i, server in enumerate(data['servers']):
        servers.servers[i] = Server(
            name=server['server']['name'],
            moid=server['server']['moid'],
            destination=server['server']['destination'] if 'destination' in server['server'] else None,
            shutdown=Shutdown(
                vmOrder=[vm['vmMoId'] for vm in server['server']['shutdown']['vmOrder']],
                delay=server['server']['shutdown']['delay'],
            ),
            restart=Restart(
                delay=server['server']['restart']['delay'],
            )
        )
    return v_center, servers


def turn_on_vms(v_center: VCenter, servers: Servers):
    """
    Launch the restart plan of all servers specified in `servers` to go back to the initial state
    Args:
        v_center (VCenter): The vCenter that orchestrates the migration plan
        servers (Servers): The migration plan for each server
    """
    conn = VMwareConnection()
    try:
        conn.connect(v_center.ip, v_center.user, v_center.password, v_center.port)
        for server in servers.servers:
            print(f"Allumage du serveur {server.name} ({server.moid})")
            vms = server.vms.restart.order
            start_delay = server.vms.restart.delay
            for vm_moid in vms:
                vm = conn.get_vm(vm_moid)
                if not vm:
                    print(f"{vm_moid} not found")
                    continue
                print(f"Powering On {vm.name} ({vm_moid})...")
                task = vm.PowerOn()
                WaitForTask(task)
                sleep(start_delay)
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()


def turn_off_vms(v_center: VCenter, servers: Servers):
    """
    Launch the shutdown plan of all servers specified in `servers
    Args:
        v_center (VCenter): The vCenter that orchestrates the migration plan
        servers (Servers): The migration plan for each server
    """
    conn = VMwareConnection()
    try:
        conn.connect(v_center.ip, v_center.user, v_center.password, v_center.port)
        for server in servers.servers:
            print(f"Extinction du serveur {server.name} ({server.moid})")
            vms = server.vms.shutdown.order
            stop_delay = server.vms.shutdown.delay
            for vm_moid in vms:
                vm = conn.get_vm(vm_moid)
                if not vm:
                    print(f"{vm_moid} not found")
                    continue
                print(f"Powering Off {vm.name}...")
                task = vm.PowerOff()
                WaitForTask(task)
                sleep(stop_delay)
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()


def migrate_vms(v_center: VCenter, servers: Servers):
    """
    Launch the migration plan of all servers specified in `servers` to migrate each vm to a distant server
    Args:
        v_center (VCenter): The vCenter that orchestrates the migration plan
        servers (Servers): The migration plan for each server
    """
    conn = VMwareConnection()
    try:
        conn.connect(v_center.ip, v_center.user, v_center.password, v_center.port)
        for server in servers.servers:
            print(f"Migration du serveur {server.name} ({server.moid})")
            vms = server.vms.shutdown.order
            stop_delay = server.vms.shutdown.delay
            for vm_moid in vms:
                vm = conn.get_vm(vm_moid)
                if not vm:
                    print(f"{vm_moid} not found")
                    continue
                print(f"Powering Off {vm.name}...")
                task = vm.PowerOff()
                WaitForTask(task)
                target_host = conn.get_host_system(server.destination)
                target_resource_pool = target_host.parent.resourcePool
                task = vm.Migrate(
                    pool=target_resource_pool,
                    host=target_host,
                    priority=vim.VirtualMachine.MovePriority.defaultPriority
                )
                WaitForTask(task)
                sleep(stop_delay)
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

    v_center, servers = load_plan_from_yaml(path_join("plans", args.plan))

    if args.shutdown:
        print("Lancement du plan de migration...")
        turn_off_vms(v_center, servers)
    elif args.restart:
        print("Lancement du plan de redémarrage...")
        turn_on_vms(v_center, servers)
    else:
        print("ERREUR: Utilisez --shutdown ou --restart")
