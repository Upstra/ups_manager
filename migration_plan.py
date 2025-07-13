from time import sleep
from pyVmomi import vim

from data_retriever.event_queue import EventQueue
from data_retriever.migration_event import VMMigrationEvent, VMShutdownEvent, ServerShutdownEvent
from data_retriever.vm_ware_connection import VMwareConnection
from data_retriever.yaml_parser import Server, VCenter, Servers, load_plan_from_yaml
from server_start import server_start
from server_stop import server_stop
from vm_migration import vm_migration
from vm_stop import vm_stop


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
        start_result = server_start(server.destination.ilo.ip, server.destination.ilo.user, server.destination.ilo.password)
        if start_result['result']['httpCode'] != 200:
            print(f"Distant server '{server.destination.name}' ({server.destination.moid}) is off and won't turn on : {start_result['result']['message']}")
            return None

    return dist_host


def shutdown(v_center: VCenter, servers: Servers):
    """
    Launch the shutdown plan of all servers specified in `servers
    Args:
        v_center (VCenter): The vCenter that orchestrates the migration plan
        servers (Servers): The migration plan for each server
    """
    conn = VMwareConnection()
    try:
        event_queue = EventQueue()
        event_queue.start_shutdown()
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
                    stop_result = vm_migration(vm, vm_moid, dist_host, server.destination.moid)
                    event = VMMigrationEvent(vm_moid, server.host.moid)
                else:
                    stop_result = vm_stop(vm, vm_moid)
                    event = VMShutdownEvent(vm_moid, server.host.moid)
                print(stop_result['result']['message'])
                if stop_result['result']['httpCode'] == 200:
                    event_queue.push(event)
                sleep(stop_delay)

            stop_result = server_stop(server.host.ilo.ip, server.host.ilo.user, server.host.ilo.password)
            if stop_result['result']['httpCode'] == 200:
                print(f"Server '{server.host.name}' ({server.host.moid}) is fully migrated")
                event = ServerShutdownEvent(server.host.moid, server.host.ilo.ip, server.host.ilo.user, server.host.ilo.password, server.restart.delay)
                event_queue.push(event)
            else:
                print(f"Couldn't stop server '{server.host.name}' ({server.host.moid})")
    except ConnectionError as err:
        print(err)
    except vim.fault.InvalidLogin as _:
        print("Invalid credentials")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()
        event_queue.finish_shutdown()
        print("Finished migration plan")


if __name__ == "__main__":
    v_center, servers = load_plan_from_yaml("plans/migration.yml")
    shutdown(v_center, servers)
