import sys
from argparse import ArgumentParser
from json import dumps as json_dumps

from pyVmomi import vim, vmodl

from data_retriever.inventory import (
    HOST_PROPERTIES,
    VM_PROPERTIES,
    host_record,
    now_iso,
    vm_record,
)
from data_retriever.vm_ware_connection import VMwareConnection

PAGE_SIZE = 500


def retrieve(content, managed_type, properties: list[str]) -> list[tuple[str, dict]]:
    view = content.viewManager.CreateContainerView(content.rootFolder, [managed_type], True)
    try:
        traversal = vmodl.query.PropertyCollector.TraversalSpec(
            name="traverseView", path="view", skip=False, type=vim.view.ContainerView
        )
        object_spec = vmodl.query.PropertyCollector.ObjectSpec(obj=view, skip=True, selectSet=[traversal])
        property_spec = vmodl.query.PropertyCollector.PropertySpec(
            type=managed_type, pathSet=properties, all=False
        )
        filter_spec = vmodl.query.PropertyCollector.FilterSpec(
            objectSet=[object_spec], propSet=[property_spec]
        )
        options = vmodl.query.PropertyCollector.RetrieveOptions(maxObjects=PAGE_SIZE)
        collector = content.propertyCollector

        records = []
        result = collector.RetrievePropertiesEx([filter_spec], options)
        while result:
            for item in result.objects:
                props = {prop.name: prop.val for prop in (item.propSet or [])}
                records.append((item.obj._moId, props))
            if not result.token:
                break
            result = collector.ContinueRetrievePropertiesEx(result.token)
        return records
    finally:
        view.DestroyView()


def inventory_metrics(ip: str, user: str, password: str, port: int) -> dict:
    connection = VMwareConnection()
    connection.connect(ip, user, password, port=port)
    try:
        content = connection._si.RetrieveContent()
        vms = [vm_record(moid, props) for moid, props in retrieve(content, vim.VirtualMachine, VM_PROPERTIES)]
        hosts = [host_record(moid, props) for moid, props in retrieve(content, vim.HostSystem, HOST_PROPERTIES)]
        return {"collectedAt": now_iso(), "vms": vms, "hosts": hosts}
    finally:
        connection.disconnect()


def main() -> int:
    parser = ArgumentParser(description="Collect metrics of every VM and ESXi host in one vCenter session")
    parser.add_argument("--ip", required=True, help="vCenter address")
    parser.add_argument("--user", required=True, help="vCenter user")
    parser.add_argument("--password", required=True, help="vCenter password")
    parser.add_argument("--port", type=int, default=443, help="vCenter port")
    args = parser.parse_args()

    try:
        print(json_dumps(inventory_metrics(args.ip, args.user, args.password, args.port)))
        return 0
    except vim.fault.InvalidLogin:
        print("Invalid credentials", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"Inventory metrics failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
