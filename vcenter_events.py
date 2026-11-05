import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from json import dumps as json_dumps

from pyVmomi import vim

from data_retriever.inventory import event_record, iso
from data_retriever.vm_ware_connection import VMwareConnection
from data_retriever.cli_security import add_password_argument

EVENT_TYPES = [
    vim.event.VmPoweredOffEvent,
    vim.event.VmPoweredOnEvent,
    vim.event.VmGuestShutdownEvent,
    vim.event.VmFailoverFailed,
    vim.event.HostConnectionLostEvent,
    vim.event.HostDisconnectedEvent,
    vim.event.HostReconnectionFailedEvent,
    vim.event.HostConnectedEvent,
    vim.event.VmMigratedEvent,
    vim.event.DrsVmMigratedEvent,
    vim.event.EventEx,
]

HA_EVENT_PREFIX = "com.vmware.vc.ha."
PAGE_SIZE = 100
DEFAULT_LOOKBACK = timedelta(minutes=10)


def parse_since(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc) - DEFAULT_LOOKBACK
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


TYPED_EVENTS = tuple(event_type for event_type in EVENT_TYPES if event_type is not vim.event.EventEx)


def keep(event) -> bool:
    if isinstance(event, vim.event.EventEx):
        return str(getattr(event, "eventTypeId", "")).startswith(HA_EVENT_PREFIX)
    return isinstance(event, TYPED_EVENTS)


def vcenter_events(ip: str, user: str, password: str, port: int, since: datetime, maximum: int) -> dict:
    connection = VMwareConnection()
    connection.connect(ip, user, password, port=port)
    until = datetime.now(timezone.utc)
    try:
        content = connection._si.RetrieveContent()
        time_filter = vim.event.EventFilterSpec.ByTime(beginTime=since, endTime=until)
        spec = vim.event.EventFilterSpec(time=time_filter, type=EVENT_TYPES)
        collector = content.eventManager.CreateCollectorForEvents(spec)
        events = []
        try:
            collector.SetCollectorPageSize(PAGE_SIZE)
            collector.RewindCollector()
            while len(events) < maximum:
                page = collector.ReadNextEvents(PAGE_SIZE)
                if not page:
                    break
                events.extend(event for event in page if keep(event))
        finally:
            collector.DestroyCollector()

        records = sorted((event_record(event) for event in events[:maximum]), key=lambda item: (item["createdAt"] or "", item["key"] or 0))
        return {"until": iso(until), "events": records}
    finally:
        connection.disconnect()


def main() -> int:
    parser = ArgumentParser(description="Read vCenter events since a cursor")
    parser.add_argument("--ip", required=True, help="vCenter address")
    parser.add_argument("--user", required=True, help="vCenter user")
    add_password_argument(parser, help="vCenter password")
    parser.add_argument("--port", type=int, default=443, help="vCenter port")
    parser.add_argument("--since", help="ISO date of the oldest event to read")
    parser.add_argument("--max", type=int, default=500, help="Maximum number of events")
    args = parser.parse_args()

    try:
        result = vcenter_events(args.ip, args.user, args.password, args.port, parse_since(args.since), args.max)
        print(json_dumps(result))
        return 0
    except vim.fault.InvalidLogin:
        print("Invalid credentials", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"vCenter events failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
