from time import sleep
from pyVmomi import vim

from data_retriever.migration_event_queue import EventQueue, EventQueueException
from data_retriever.migration_event import VMMigrationEvent, VMShutdownEvent, ServerShutdownEvent, VMStartedEvent, \
    MigrationErrorEvent
from data_retriever.vm_ware_connection import VMwareConnection
from data_retriever.yaml_parser import Server, VCenter, Servers, load_plan_from_yaml, UpsGrace
from server_start import server_start
from server_stop import server_stop
from vm_migration import vm_migration
from vm_start import vm_start
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
        # print(f"Distant server not set")
        return None

    dist_host = conn.get_host_system(server.destination.moid)
    if not dist_host:
        # print(f"Distant server '{server.destination.name}' ({server.destination.moid}) not found")
        return None

    if dist_host.runtime.powerState == vim.HostSystem.PowerState.poweredOff:
        start_result = server_start(server.destination.ilo.ip, server.destination.ilo.user, server.destination.ilo.password)
        if start_result['result']['httpCode'] != 200:
            # print(f"Distant server '{server.destination.name}' ({server.destination.moid}) is off and won't turn on : {start_result['result']['message']}")
            return None

    return dist_host


def shutdown(vcenter: VCenter, ups_grace: UpsGrace, servers: Servers):
    """
    Launch the shutdown plan of all servers specified in `servers
    Args:
        vcenter (VCenter): The vCenter that orchestrates the migration plan
        ups_grace (UpsGrace): The `UpsGrace` object containing graces periods to wait before shutdown and restart
        servers (Servers): The migration plan for each server
    """
    stop_delay = ups_grace.shutdown_grace
    conn = VMwareConnection()
    event_queue = EventQueue()
    try:
        event_queue.connect()
        event_queue.grace_shutdown()
        sleep(stop_delay)

        event_queue.start_shutdown()
        conn.connect(vcenter.ip, vcenter.user, vcenter.password, vcenter.port)
        for server in servers.servers:
            vms = server.vm_order
            current_host = conn.get_host_system(server.host.moid)
            if not current_host:
                event = MigrationErrorEvent("Server not found", f"Server '{server.host.name}' with moId {server.host.moid} not found")
                event_queue.push(event)
                continue
            if current_host.runtime.powerState == vim.HostSystem.PowerState.poweredOff:
                event = MigrationErrorEvent("Server off", f"Server '{server.host.name}' with moId {server.host.moid} is already off")
                event_queue.push(event)
                continue

            dist_host = get_distant_host(conn, server)
            for vm_moid in vms:
                vm = conn.get_vm(vm_moid)
                stop_result = vm_stop(vm, vm_moid)
                if stop_result['result']['httpCode'] == 200:
                    event = VMShutdownEvent(vm_moid, server.host.moid)
                else:
                    event = MigrationErrorEvent("VM won't stop", stop_result['result']['message'])
                event_queue.push(event)
                if not dist_host:
                    continue

                stop_result = vm_migration(vm, vm_moid, dist_host, server.destination.moid)
                if stop_result['result']['httpCode'] == 200:
                    event = VMMigrationEvent(vm_moid, server.host.moid)
                    event_queue.push(event)
                    stop_result = vm_start(vm, vm_moid)
                    if stop_result['result']['httpCode'] == 200:
                        event = VMStartedEvent(vm_moid, server.host.moid)
                    else:
                        event = MigrationErrorEvent("VM won't start", stop_result['result']['message'])
                    event_queue.push(event)
                else:
                    event = MigrationErrorEvent("VM won't migrate", stop_result['result']['message'])
                    event_queue.push(event)

            stop_result = server_stop(server.host.ilo.ip, server.host.ilo.user, server.host.ilo.password)
            if stop_result['result']['httpCode'] == 200:
                event = ServerShutdownEvent(server.host.moid, server.host.ilo.ip, server.host.ilo.user, server.host.ilo.password)
            else:
                event = MigrationErrorEvent("Server won't stop", stop_result['result']['message'])
            event_queue.push(event)

    except EventQueueException as e:
        event = MigrationErrorEvent("Database error", str(e))
        event_queue.push(event)
    except vim.fault.InvalidLogin as _:
        event = MigrationErrorEvent("Invalid credentials", "Username or password is incorrect")
        event_queue.push(event)
    except Exception as e:
        event = MigrationErrorEvent("Unknown error", str(e))
        event_queue.push(event)
    finally:
        event_queue.finish_shutdown()
        event_queue.disconnect()
        conn.disconnect()


if __name__ == "__main__":
    try:
        vcenter, ups_grace, servers = load_plan_from_yaml("plans/migration.yml")
        shutdown(vcenter, ups_grace, servers)
    except Exception as e:
        print(f"Error parsing YAML file: {e}")
