from time import sleep
from pyVmomi import vim
from json import dumps as json_dumps
import logging
import socket

from data_retriever.cache import Cache, CacheException
from data_retriever.cache_element import serialize_server, serialize_vm
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
                vms = conn.get_all_vms()
                for vm in vms:
                    metrics = vm_metrics_info(vm)
                    cache.set_metrics(serialize_vm(vm), json_dumps(metrics))

                servers = conn.get_all_hosts()
                for server in servers:
                    metrics = server_metrics_info(server)
                    cache.set_metrics(serialize_server(server), json_dumps(metrics))

                sleep(RELOAD_DELAY)
                new_vcenter = cache.get_vcenter()
                if not new_vcenter or vcenter != new_vcenter:
                    conn.disconnect()
                    break

        except CacheException as e:
            sleep(RELOAD_DELAY)
            logging.error(e)
        except vim.fault.InvalidLogin:
            sleep(RELOAD_DELAY)
            logging.error("Invalid credentials")
        except (vim.fault.NoCompatibleHost, vim.fault.InvalidHostState, OSError, socket.error):
            sleep(RELOAD_DELAY)
            logging.error("Host is unreachable")
        except vim.fault.VimFault:
            sleep(RELOAD_DELAY)
            logging.error("Can't retrieve metrics")
        except Exception as e:
            sleep(RELOAD_DELAY)
            logging.error(e)
