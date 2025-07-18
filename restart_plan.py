from time import sleep
from pyVmomi import vim

from data_retriever.migration_event_queue import EventQueue, EventQueueException
from data_retriever.migration_event import VMMigrationEvent, VMShutdownEvent, ServerShutdownEvent, VMStartedEvent, \
    MigrationErrorEvent, ServerStartedEvent
from data_retriever.vm_ware_connection import VMwareConnection
from data_retriever.yaml_parser import VCenter, load_plan_from_yaml, UpsGrace
from server_start import server_start
from vm_migration import vm_migration
from vm_start import vm_start
from vm_stop import vm_stop


def restart(vcenter: VCenter, ups_grace: UpsGrace):
    """
    Launch the restart plan of all servers specified in `servers` to go back to the initial state
    Args:
        vcenter (VCenter): The VCenter informations to connect to
        ups_grace (UpsGrace): The `UpsGrace` object containing graces periods to wait before shutdown and restart
    """
    start_delay = ups_grace.restart_grace
    conn = VMwareConnection()
    try:
        event_queue = EventQueue()
        conn.connect(vcenter.ip, vcenter.user, vcenter.password, vcenter.port)
        event_queue.start_restart()
        events = event_queue.get_event_list()

        for event in events:
            if isinstance(event, VMShutdownEvent):
                vm = conn.get_vm(event.vm_moid)
                target_host = conn.get_host_system(event.server_moid)
                while target_host.runtime.connectionState != 'connected':
                    sleep(start_delay)
                start_result = vm_start(vm, event.vm_moid)
                if start_result['result']['httpCode'] == 200:
                    event = VMStartedEvent(event.vm_moid, event.server_moid)
                else:
                    event = MigrationErrorEvent("VM won't start", start_result['result']['message'])
                event_queue.push(event, True)
            elif isinstance(event, VMMigrationEvent):
                vm = conn.get_vm(event.vm_moid)
                target_host = conn.get_host_system(event.server_moid)
                while target_host.runtime.connectionState != 'connected':
                    sleep(start_delay)
                start_result = vm_migration(vm, event.vm_moid, target_host, event.server_moid)
                if start_result['result']['httpCode'] == 200:
                    event = VMMigrationEvent(event.vm_moid, event.server_moid)
                else:
                    event = MigrationErrorEvent("VM won't migrate", start_result['result']['message'])
                event_queue.push(event, True)
            elif isinstance(event, VMStartedEvent):
                vm = conn.get_vm(event.vm_moid)
                target_host = conn.get_host_system(event.server_moid)
                while target_host.runtime.connectionState != 'connected':
                    sleep(start_delay)
                start_result = vm_stop(vm, event.vm_moid)
                if start_result['result']['httpCode'] == 200:
                    event = VMShutdownEvent(event.vm_moid, event.server_moid)
                else:
                    event = MigrationErrorEvent("VM won't stop", start_result['result']['message'])
                event_queue.push(event, True)
            elif isinstance(event, ServerShutdownEvent):
                start_result = server_start(event.ilo_ip, event.ilo_user, event.ilo_password)
                if start_result['result']['httpCode'] == 200:
                    event = ServerStartedEvent(event.server_moid)
                else:
                    event = MigrationErrorEvent("Server won't start", start_result['result']['message'])
                event_queue.push(event, True)
            else:
                event = MigrationErrorEvent("Unsupported event", f"Unknown event type: {event}")
                event_queue.push(event, True)
                continue
        event_queue.finish_restart()
        event_queue.disconnect()
    except EventQueueException as e:
        event = MigrationErrorEvent("Database error", str(e))
        event_queue.push(event)
        event_queue.finish_restart()
        event_queue.disconnect()
    except vim.fault.InvalidLogin as _:
        event = MigrationErrorEvent("Invalid credentials", "Username or password is incorrect")
        event_queue.push(event)
        event_queue.finish_restart()
        event_queue.disconnect()
    except Exception as e:
        event = MigrationErrorEvent("Unknown error", str(e))
        event_queue.push(event)
        event_queue.finish_restart()
        event_queue.disconnect()
    finally:
        conn.disconnect()


if __name__ == "__main__":
    try:
        vcenter, ups_grace, _ = load_plan_from_yaml("plans/migration.yml")
        restart(vcenter, ups_grace)
    except Exception as e:
        print(f"Error parsing YAML file: {e}")
