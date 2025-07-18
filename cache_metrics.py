from time import sleep
from pyVmomi import vim
from json import dumps as json_dumps
import logging

from data_retriever.cache import Cache, CacheException
from data_retriever.cache_element import serialize_element
from data_retriever.dto import vm_metrics_info, server_metrics_info
from data_retriever.vm_ware_connection import VMwareConnection


RELOAD_DELAY = 60

if __name__ == "__main__":
    logging.basicConfig(
        filename='cache_metrics.log',
        level=logging.ERROR,
        format='%(asctime)s %(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )

    conn = VMwareConnection()
    metrics = None

    while True:
        try:
            cache = Cache()
            vcenter = cache.get_vcenter()
            while not vcenter:
                sleep(RELOAD_DELAY)
                vcenter = cache.get_vcenter()
            conn.connect(vcenter.ip, vcenter.user, vcenter.password, vcenter.port)
            while True:
                elements = cache.get_elements()
                for element in elements:
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
        except CacheException as e:
            sleep(RELOAD_DELAY)
            logging.error(e)
        except vim.fault.InvalidLogin as _:
            sleep(RELOAD_DELAY)
            logging.error("Invalid credentials")
        except Exception as e:
            sleep(RELOAD_DELAY)
            logging.error(e)
