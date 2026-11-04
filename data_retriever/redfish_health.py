from datetime import datetime, timezone
from typing import Optional


ABSENT = "Absent"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def number(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def status_of(item: dict) -> dict:
    status = item.get("Status") or {}
    return status if isinstance(status, dict) else {}


def is_absent(item: dict) -> bool:
    return status_of(item).get("State") == ABSENT


def sensor_record(item: dict) -> dict:
    absent = is_absent(item)
    return {
        "name": item.get("Name"),
        "readingC": None if absent else number(item.get("ReadingCelsius")),
        "warnC": None if absent else number(item.get("UpperThresholdNonCritical")),
        "critC": None if absent else number(item.get("UpperThresholdCritical")),
        "state": status_of(item).get("State"),
        "health": None if absent else status_of(item).get("Health"),
    }


def fan_record(item: dict) -> dict:
    absent = is_absent(item)
    return {
        "name": item.get("Name") or item.get("FanName"),
        "percent": None if absent else number(item.get("Reading", item.get("CurrentReading"))),
        "state": status_of(item).get("State"),
        "health": None if absent else status_of(item).get("Health"),
    }


def supply_record(item: dict) -> dict:
    absent = is_absent(item)
    return {
        "name": item.get("Name"),
        "state": status_of(item).get("State"),
        "health": None if absent else status_of(item).get("Health"),
        "capacityW": None if absent else number(item.get("PowerCapacityWatts")),
        "outputW": None if absent else number(item.get("LastPowerOutputWatts")),
    }


def find_inlet(sensors: list[dict]) -> Optional[dict]:
    for sensor in sensors:
        if sensor["readingC"] is not None and "inlet" in str(sensor["name"] or "").lower():
            return sensor
    return None


def max_cpu(sensors: list[dict]) -> Optional[float]:
    readings = [
        sensor["readingC"]
        for sensor in sensors
        if sensor["readingC"] is not None and "cpu" in str(sensor["name"] or "").lower()
    ]
    return max(readings) if readings else None


def parse_health(thermal: dict, power: dict, system: dict, generation: Optional[str]) -> dict:
    thermal = thermal or {}
    power = power or {}
    system = system or {}
    sensors = [sensor_record(item) for item in thermal.get("Temperatures") or []]
    fans = [fan_record(item) for item in thermal.get("Fans") or []]
    inlet = find_inlet(sensors)
    control = (power.get("PowerControl") or [{}])[0] or {}
    system_status = status_of(system)
    return {
        "collectedAt": now_iso(),
        "generation": generation,
        "system": {
            "model": system.get("Model"),
            "serial": system.get("SerialNumber"),
            "powerState": system.get("PowerState"),
            "health": system_status.get("HealthRollup") or system_status.get("Health"),
        },
        "thermal": {
            "inletC": inlet["readingC"] if inlet else None,
            "inletWarnC": inlet["warnC"] if inlet else None,
            "inletCritC": inlet["critC"] if inlet else None,
            "maxCpuC": max_cpu(sensors),
            "sensors": sensors,
            "fans": fans,
        },
        "power": {
            "consumedW": number(control.get("PowerConsumedWatts")),
            "capacityW": number(control.get("PowerCapacityWatts")),
            "supplies": [supply_record(item) for item in power.get("PowerSupplies") or []],
        },
    }
