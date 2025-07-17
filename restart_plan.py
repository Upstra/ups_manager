from time import sleep
from pyVmomi import vim

from data_retriever.migration_event_queue import EventQueue
from data_retriever.migration_event import VMMigrationEvent, VMShutdownEvent, ServerShutdownEvent, VMStartedEvent
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
                    print(f"Waiting {start_delay} seconds for server to completely turn on...")
                    sleep(start_delay)
                start_result = vm_start(vm, event.vm_moid)
            elif isinstance(event, VMMigrationEvent):
                vm = conn.get_vm(event.vm_moid)
                target_host = conn.get_host_system(event.server_moid)
                while target_host.runtime.connectionState != 'connected':
                    print(f"Waiting {start_delay} seconds for server to completely turn on...")
                    sleep(start_delay)
                start_result = vm_migration(vm, event.vm_moid, target_host, event.server_moid)
            elif isinstance(event, VMStartedEvent):
                vm = conn.get_vm(event.vm_moid)
                target_host = conn.get_host_system(event.server_moid)
                while target_host.runtime.connectionState != 'connected':
                    print(f"Waiting {start_delay} seconds for server to completely turn on...")
                    sleep(start_delay)
                start_result = vm_stop(vm, event.vm_moid)
            elif isinstance(event, ServerShutdownEvent):
                start_result = server_start(event.ilo_ip, event.ilo_user, event.ilo_password)
            else:
                print(f"Unknown event type: {event}")
                continue
            print(start_result['result']['message'])
        event_queue.finish_restart()
        print("Rollback complete")

    except ConnectionError as err:
        print(err)
    except vim.fault.InvalidLogin as _:
        print("Invalid credentials")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()


if __name__ == "__main__":
    try:
        vcenter, ups_grace, _ = load_plan_from_yaml("plans/migration.yml")
        restart(vcenter, ups_grace)
    except Exception as err:
        print(err)
