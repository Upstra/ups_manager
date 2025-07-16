from dataclasses import dataclass
from yaml import safe_load as yaml_load


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
    vm_order: list[str]

@dataclass
class Servers:
    servers: list[Server]

@dataclass
class VCenter:
    ip: str
    user: str
    password: str
    port: int

@dataclass
class UpsGrace:
    shutdown_grace: int
    restart_grace: int


def load_plan_from_yaml(file_path: str) -> tuple[VCenter, UpsGrace, Servers]:
    """
    Load a migration plan stored in a YAML file
    Args:
        file_path (str): The path to the migration plan
    Returns:
        tuple[VCenter, UpsGrace, Servers]: A `VCenter` object, an `UpsGrace` object and a list of `Server` objects representing the migration plan
    Raises:
        FileNotFoundError: If `file_path` is not a valid YAML file
        KeyError: If YAML file has not a correct format
        Exception: For any other error
     """
    with open(file_path, 'r') as f:
        data = yaml_load(f)

    v_center = VCenter(
        ip=data['vCenter']['ip'],
        user=data['vCenter']['user'],
        password=data['vCenter']['password'],
        port=data['vCenter']['port'] if 'port' in data['vCenter'] else 443,
    )

    ups_grace = UpsGrace(
        shutdown_grace=data['ups']['shutdownGrace'],
        restart_grace=data['ups']['restartGrace'],
    )

    servers = Servers(servers=[None] * len(data['servers']))
    for i, server in enumerate(data['servers']):
        host = server['server']['host']
        destination = server['server']['destination'] if 'destination' in server['server'] else None
        servers.servers[i] = Server(
            host=Host(
                name=host['name'],
                moid=host['moid'],
                ilo=IloYaml(
                    ip=host['ilo']['ip'],
                    user=host['ilo']['user'],
                    password=host['ilo']['password'],
                )
            ),
            destination=Host(
                name=destination['name'],
                moid=destination['moid'],
                ilo=IloYaml(
                    ip=destination['ilo']['ip'],
                    user=destination['ilo']['user'],
                    password=destination['ilo']['password'],
                )
            ) if destination else None,
            vm_order=[vm['vmMoId'] for vm in server['server']['vmOrder']],
        )
    return v_center, ups_grace, servers
