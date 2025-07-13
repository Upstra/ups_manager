from yaml import safe_load as yaml_load
from time import sleep
from argparse import ArgumentParser
from dataclasses import dataclass
from os.path import join as path_join
from pyVmomi import vim
from redis import Redis
from json import dumps as json_dumps, loads as json_loads

from data_retriever.vm_ware_connection import VMwareConnection
from server_start import server_start
from server_stop import server_stop
from vm_migration import vm_migration
from vm_start import vm_start
from vm_stop import vm_stop


@dataclass
class Shutdown:
    vmOrder: list[str]
    delay: int

@dataclass
class Restart:
    delay: int

@dataclass
class IloYaml:
    ip: str
    user: str
    password: str

@dataclass
class Host:
    name: str
    moid: str
    ilo: IloYaml

@dataclass
class Server:
    host: Host
    destination: Host
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
            host=Host(
                name=server['server']['host']['name'],
                moid=server['server']['host']['moid'],
                ilo=IloYaml(
                    ip=server['server']['host']['ilo']['ip'],
                    user=server['server']['host']['ilo']['user'],
                    password=server['server']['host']['ilo']['password'],
                )
            ),
            destination=Host(
                name=server['server']['destination']['name'],
                moid=server['server']['destination']['moid'],
                ilo=IloYaml(
                    ip=server['server']['destination']['ilo']['ip'],
                    user=server['server']['destination']['ilo']['user'],
                    password=server['server']['destination']['ilo']['password'],
                )
            ) if 'destination' in server['server'] else None,
            shutdown=Shutdown(
                vmOrder=[vm['vmMoId'] for vm in server['server']['shutdown']['vmOrder']],
                delay=server['server']['shutdown']['delay'],
            ),
            restart=Restart(
                delay=server['server']['restart']['delay'],
            )
        )
    return v_center, servers


def restart(start_delay: int):
    """ Launch the restart plan of all servers specified in `servers` to go back to the initial state """
    conn = VMwareConnection()
    try:
        conn.connect(v_center.ip, v_center.user, v_center.password, v_center.port)
        redis = Redis()
        redis.set("migration:state", "restarting")
        events = redis.lrange("migration:events", 0, -1)

        for json_event in events:
            event = json_loads(json_event)
            if event['type'] == "VM":
                vm = conn.get_vm(event['moid'])
                if event['action'] == "MIGRATION":
                    target_host = conn.get_host_system(event['host_moid'])
                    start_result = vm_migration(vm, event['moid'], target_host, event['host_moid'])
                else:
                    start_result = vm_start(vm, event['moid'])
            else:
                start_result = server_start(event['ilo_ip'], event['ilo_user'], event['ilo_password'])
            print(start_result['result']['message'])
            sleep(start_delay)

        redis.set("migration:state", "rolled_back")
        print("Rollback complete")
    except vim.fault.InvalidLogin as _:
        return print("Invalid credentials")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()
        redis.set("migration:state", "ok")
        print("Rollback complete")


def get_distant_host(conn: VMwareConnection, server: Server) -> vim.HostSystem:
    """
    Get the distant server if set and on
    Args:
        conn (VMwareConnection): The connection to the vCenter that orchestrates the migration plan
        server (Server): The `Server` object that represents the migration plan for one server
    Returns:
        vim.HostSystem: The `HostSystem` object representing the distant server, or None if the server is unavailable
    """
    if not server.destination:
        print(f"Distant server not set")
        return None

    dist_host = conn.get_host_system(server.destination.moid)
    if not dist_host:
        print(f"Distant server '{server.destination.name}' ({server.destination.moid}) not found")
        return None

    if dist_host.runtime.powerState == vim.HostSystem.PowerState.poweredOff:
        start_result = server_start(dist_host.ip, dist_host.user, dist_host.password)
        if start_result['result']['httpCode'] != 200:
            print(f"Distant server '{server.destination.name}' ({server.destination.moid}) is off and won't turn on : {start_result['result']['message']}")
            return None

    return dist_host


def push_vm_migration(redis: Redis, vm_moid: str, server_moid: str):
    event = json_dumps({
        "type": "VM",
        "moid": vm_moid,
        "action": "MIGRATION",
        "host_moid": server_moid
    })
    redis.lpush("migration:events", event)

def push_vm_shutdown(redis: Redis, vm_moid: str):
    event = json_dumps({
        "type": "VM",
        "moid": vm_moid,
        "action": "SHUTDOWN",
    })
    redis.lpush("migration:events", event)

def push_server(redis: Redis, server_moid: str, ilo_ip: str, ilo_user: str, ilo_password: str):
    event = json_dumps({
        "type": "SERVER",
        "moid": server_moid,
        "ilo_ip": ilo_ip,
        "ilo_user": ilo_user,
        "ilo_password": ilo_password
    })
    redis.lpush("migration:events", event)


def shutdown(v_center: VCenter, servers: Servers):
    """
    Launch the shutdown plan of all servers specified in `servers
    Args:
        v_center (VCenter): The vCenter that orchestrates the migration plan
        servers (Servers): The migration plan for each server
    """
    redis = Redis()
    redis.set("migration:state", "shutting down")
    conn = VMwareConnection()
    try:
        conn.connect(v_center.ip, v_center.user, v_center.password, v_center.port)
        for server in servers.servers:
            vms = server.shutdown.vmOrder
            stop_delay = server.shutdown.delay
            current_host = conn.get_host_system(server.host.moid)
            if not current_host:
                print(f"Server '{server.host.name}' ({server.host.moid}) not found")
                continue
            if current_host.runtime.powerState == vim.HostSystem.PowerState.poweredOff:
                print(f"Server '{server.host.name}' ({server.host.moid}) is already off")
                continue

            dist_host = get_distant_host(conn, server)
            if dist_host:
                print(f"Launching migration plan for server '{server.host.name}' ({server.host.moid})...")
            else:
                print(f"Launching shutdown plan for server '{server.host.name}' ({server.host.moid})...")

            for vm_moid in vms:
                vm = conn.get_vm(vm_moid)
                if dist_host:
                    migration_result = vm_migration(vm, vm_moid, dist_host, server.destination.moid)
                    print(migration_result['result']['message'])
                    push_migration(redis, vm_moid, server.host.ilo.ip, server.host.ilo.user, server.host.ilo.password)
                else:
                    stop_result = vm_stop(vm, vm_moid)
                    print(stop_result['result']['message'])
                    push_shutdown(redis, moid=vm_moid, is_vm=True)
                sleep(stop_delay)

            stop_result = server_stop(server.host.ilo.ip, server.host.ilo.user, server.host.ilo.password)
            if stop_result['result']['httpCode'] == 200:
                print(f"Server '{server.host.name}' ({server.host.moid}) is fully migrated")
                push_shutdown(redis, moid=server.host.moid, is_vm=False)
            else:
                print(f"Couldn't stop server '{server.host.name}' ({server.host.moid})")
    except vim.fault.InvalidLogin as _:
        return print("Invalid credentials")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()
        redis.set("migration:state", "shutted down")
        print("Finished migration plan")


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
        shutdown(v_center, servers)
    elif args.restart:
        print("Lancement du plan de redémarrage...")
        restart()
    else:
        print("ERREUR: Utilisez --shutdown ou --restart")
