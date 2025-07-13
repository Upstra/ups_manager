from time import sleep
from pyVmomi import vim
from redis import Redis

from data_retriever.migration_event import deserialize_event, VMMigrationEvent, VMShutdownEvent, ServerShutdownEvent
from data_retriever.vm_ware_connection import VMwareConnection
from data_retriever.yaml_parser import VCenter, load_plan_from_yaml
from server_start import server_start
from vm_migration import vm_migration
from vm_start import vm_start


def restart(v_center: VCenter):
    """
    Launch the restart plan of all servers specified in `servers` to go back to the initial state
    Args:
        v_center (VCenter): The VCenter informations to connect to
    """
    conn = VMwareConnection()
    redis = Redis()
    try:
        conn.connect(v_center.ip, v_center.user, v_center.password, v_center.port)
        redis.set("migration:state", "restarting")
        events = redis.lrange("migration:events", 0, -1)
        start_delay = 60

        for json_event in events:
            event = deserialize_event(json_event)
            if isinstance(event, VMMigrationEvent):
                vm = conn.get_vm(event.vm_moid)
                target_host = conn.get_host_system(event.server_moid)
                start_result = vm_migration(vm, event.vm_moid, target_host, event.server_moid)
            elif isinstance(event, VMShutdownEvent):
                vm = conn.get_vm(event.vm_moid)
                start_result = vm_start(vm, event.vm_moid)
            elif isinstance(event, ServerShutdownEvent):
                start_result = server_start(event.ilo_ip, event.ilo_user, event.ilo_password)
                start_delay = event.start_delay
            else:
                print(f"Unknown event type: {event}")
                continue
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


if __name__ == "__main__":
    v_center, _ = load_plan_from_yaml("plans/migration.yml")
    restart(v_center)
