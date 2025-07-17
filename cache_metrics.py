from time import sleep
from pyVmomi import vim
from json import dumps as json_dumps

from data_retriever.cache import Cache
from data_retriever.cache_element import serialize_element
from data_retriever.dto import vm_metrics_info, server_metrics_info
from data_retriever.vm_ware_connection import VMwareConnection


RELOAD_DELAY = 60

if __name__ == "__main__":
    cache = Cache()
    vcenter = cache.get_vcenter()
    if vcenter is None:
        print("No vcenter found")
    conn = VMwareConnection()
    metrics = None

    try:
        conn.connect(vcenter.ip, vcenter.user, vcenter.password, vcenter.port)
        while True:
            elements = cache.get_elements()
            for element in elements:
                print(element)
                if element.type == "VM":
                    vm = conn.get_vm(element.moid)
                    if not vm:
                        continue
                    metrics = vm_metrics_info(vm)
                elif element.type == "Server":
                    server = conn.get_host_system(element.moid)
                    if not server:
                        continue
                    metrics = server_metrics_info(server)
                else:
                    continue
                if metrics:
                    cache.set_metrics(serialize_element(element), json_dumps(metrics))
            sleep(RELOAD_DELAY)
    except ConnectionError as err:
        print(err)
    except vim.fault.InvalidLogin as _:
       print("Invalid credentials")
    except Exception as err:
        print(err)
    finally:
        conn.disconnect()
