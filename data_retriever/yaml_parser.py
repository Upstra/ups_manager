from dataclasses import dataclass
from yaml import safe_load as yaml_load


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
        tuple[VCenter, Servers]: A `VCenter` object and a list of `Server` objects representing the migration plan, or `None` if an error occurs
     """
    try:
        with open(file_path, 'r') as f:
            data = yaml_load(f)
    except FileNotFoundError:
        print(f"Migration plan file not found: {file_path}")
        return None, None
    except Exception as e:
        print(f"Error parsing YAML file: {e}")
        return None, None

    try:
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

    except KeyError as e:
        print(f"Key not found in YAML file: {e}")
        return None, None
