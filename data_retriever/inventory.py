from datetime import datetime, timezone
from typing import Optional


VM_PROPERTIES = [
    "name",
    "runtime.powerState",
    "runtime.host",
    "runtime.connectionState",
    "runtime.bootTime",
    "summary.quickStats.overallCpuUsage",
    "summary.runtime.maxCpuUsage",
    "summary.quickStats.guestMemoryUsage",
    "summary.config.memorySizeMB",
    "summary.config.numCpu",
    "summary.quickStats.uptimeSeconds",
    "guest.guestState",
    "guest.ipAddress",
    "guestHeartbeatStatus",
    "overallStatus",
]

HOST_PROPERTIES = [
    "name",
    "runtime.connectionState",
    "runtime.powerState",
    "runtime.inMaintenanceMode",
    "overallStatus",
    "summary.quickStats.overallCpuUsage",
    "summary.hardware.cpuMhz",
    "summary.hardware.numCpuCores",
    "summary.quickStats.overallMemoryUsage",
    "summary.hardware.memorySize",
    "summary.quickStats.uptime",
]

BYTES_PER_MB = 1024 * 1024


def iso(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return str(value)


def now_iso() -> str:
    return iso(datetime.now(timezone.utc))


def text(value) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def moid_of(value) -> Optional[str]:
    if value is None:
        return None
    return getattr(value, "_moId", None) or text(value)


def number(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def percent(used, total) -> Optional[float]:
    used = number(used)
    total = number(total)
    if used is None or total is None or total <= 0:
        return None
    return round(used / total * 100, 1)


def vm_record(moid: str, props: dict) -> dict:
    power_state = text(props.get("runtime.powerState"))
    powered_on = power_state == "poweredOn"
    cpu_usage = number(props.get("summary.quickStats.overallCpuUsage")) if powered_on else None
    cpu_max = number(props.get("summary.runtime.maxCpuUsage"))
    memory_usage = number(props.get("summary.quickStats.guestMemoryUsage")) if powered_on else None
    uptime = number(props.get("summary.quickStats.uptimeSeconds")) if powered_on else None
    return {
        "moid": moid,
        "name": text(props.get("name")),
        "hostMoid": moid_of(props.get("runtime.host")),
        "powerState": power_state,
        "connectionState": text(props.get("runtime.connectionState")),
        "guestState": text(props.get("guest.guestState")),
        "heartbeat": text(props.get("guestHeartbeatStatus")),
        "overallStatus": text(props.get("overallStatus")),
        "cpuUsageMhz": cpu_usage,
        "cpuMaxMhz": cpu_max,
        "cpuPercent": percent(cpu_usage, cpu_max),
        "memoryUsageMb": memory_usage,
        "memoryMb": number(props.get("summary.config.memorySizeMB")),
        "numCpu": number(props.get("summary.config.numCpu")),
        "uptimeSeconds": uptime,
        "bootTime": iso(props.get("runtime.bootTime")) if powered_on else None,
        "ip": text(props.get("guest.ipAddress")),
    }


def host_record(moid: str, props: dict) -> dict:
    cpu_mhz = number(props.get("summary.hardware.cpuMhz"))
    cores = number(props.get("summary.hardware.numCpuCores"))
    cpu_capacity = cpu_mhz * cores if cpu_mhz is not None and cores is not None else None
    memory_bytes = number(props.get("summary.hardware.memorySize"))
    memory_mb = memory_bytes / BYTES_PER_MB if memory_bytes is not None else None
    maintenance = props.get("runtime.inMaintenanceMode")
    return {
        "moid": moid,
        "name": text(props.get("name")),
        "connectionState": text(props.get("runtime.connectionState")),
        "powerState": text(props.get("runtime.powerState")),
        "maintenance": maintenance if isinstance(maintenance, bool) else None,
        "overallStatus": text(props.get("overallStatus")),
        "cpuPercent": percent(props.get("summary.quickStats.overallCpuUsage"), cpu_capacity),
        "memoryPercent": percent(props.get("summary.quickStats.overallMemoryUsage"), memory_mb),
        "uptimeSeconds": number(props.get("summary.quickStats.uptime")),
    }


def event_type_name(event) -> str:
    event_type_id = getattr(event, "eventTypeId", None)
    if event_type_id:
        return str(event_type_id)
    name = type(event).__name__
    return name.split(".")[-1]


def event_record(event) -> dict:
    vm = getattr(event, "vm", None)
    host = getattr(event, "host", None)
    return {
        "key": getattr(event, "key", None),
        "type": event_type_name(event),
        "createdAt": iso(getattr(event, "createdTime", None)),
        "userName": text(getattr(event, "userName", None)) or None,
        "vmMoid": moid_of(getattr(vm, "vm", None)) if vm else None,
        "vmName": text(getattr(vm, "name", None)) if vm else None,
        "hostMoid": moid_of(getattr(host, "host", None)) if host else None,
        "hostName": text(getattr(host, "name", None)) if host else None,
        "message": text(getattr(event, "fullFormattedMessage", None)),
    }
