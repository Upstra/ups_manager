from datetime import datetime, timezone
from typing import Optional


UPS_MIB_BASE = "1.3.6.1.2.1.33.1"

SNMP_OIDS = {
    "manufacturer": f"{UPS_MIB_BASE}.1.1.0",
    "model": f"{UPS_MIB_BASE}.1.2.0",
    "battery_status": f"{UPS_MIB_BASE}.2.1.0",
    "minutes_remaining": f"{UPS_MIB_BASE}.2.3.0",
    "charge_remaining": f"{UPS_MIB_BASE}.2.4.0",
    "battery_temperature": f"{UPS_MIB_BASE}.2.7.0",
    "input_voltage": f"{UPS_MIB_BASE}.3.3.1.3.1",
    "output_source": f"{UPS_MIB_BASE}.4.1.0",
    "output_voltage": f"{UPS_MIB_BASE}.4.4.1.2.1",
    "output_power": f"{UPS_MIB_BASE}.4.4.1.4.1",
    "output_load": f"{UPS_MIB_BASE}.4.4.1.5.1",
}

SNMP_OUTPUT_SOURCE_BATTERY = 5
SNMP_OUTPUT_SOURCE_BYPASS = 4
SNMP_OUTPUT_SOURCE_NORMAL = 3
SNMP_BATTERY_LOW = 3
SNMP_BATTERY_DEPLETED = 4


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def to_number(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        text = str(value).strip().strip('"')
        if text == "":
            return None
        number = float(text)
        return int(number) if number.is_integer() else number
    except ValueError:
        return None


def to_text(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip().strip('"')
    return text or None


def status_flags(raw: Optional[str]) -> dict:
    if raw is None:
        return {
            "raw": None,
            "onBattery": None,
            "lowBattery": None,
            "charging": None,
            "onBypass": None,
            "overload": None,
            "replaceBattery": None,
        }
    tokens = raw.upper().split()
    on_battery = None
    if "OB" in tokens:
        on_battery = True
    elif "OL" in tokens:
        on_battery = False
    return {
        "raw": raw,
        "onBattery": on_battery,
        "lowBattery": "LB" in tokens,
        "charging": "CHRG" in tokens,
        "onBypass": "BYPASS" in tokens,
        "overload": "OVER" in tokens,
        "replaceBattery": "RB" in tokens,
    }


def real_power(real_power_w, load_percent, nominal_w) -> Optional[float]:
    if real_power_w is not None:
        return real_power_w
    if load_percent is not None and nominal_w is not None:
        return round(load_percent * nominal_w / 100)
    return None


def build_telemetry(
    source: str,
    device: dict,
    raw_status: Optional[str],
    battery: dict,
    input_values: dict,
    output_values: dict,
    load: dict,
    temperature_c,
) -> dict:
    load_percent = to_number(load.get("percent"))
    nominal_w = to_number(load.get("nominalRealPowerW"))
    return {
        "source": source,
        "collectedAt": now_iso(),
        "device": {
            "manufacturer": to_text(device.get("manufacturer")),
            "model": to_text(device.get("model")),
            "serial": to_text(device.get("serial")),
            "firmware": to_text(device.get("firmware")),
        },
        "status": status_flags(to_text(raw_status)),
        "battery": {
            "chargePercent": to_number(battery.get("chargePercent")),
            "runtimeSeconds": to_number(battery.get("runtimeSeconds")),
            "voltage": to_number(battery.get("voltage")),
            "temperatureC": to_number(battery.get("temperatureC")),
            "lastTestResult": to_text(battery.get("lastTestResult")),
            "lastTestAt": to_text(battery.get("lastTestAt")),
        },
        "input": {
            "voltage": to_number(input_values.get("voltage")),
            "frequencyHz": to_number(input_values.get("frequencyHz")),
        },
        "output": {
            "voltage": to_number(output_values.get("voltage")),
            "frequencyHz": to_number(output_values.get("frequencyHz")),
        },
        "load": {
            "percent": load_percent,
            "realPowerW": real_power(
                to_number(load.get("realPowerW")), load_percent, nominal_w
            ),
            "nominalRealPowerW": nominal_w,
        },
        "temperatureC": to_number(temperature_c),
    }


def parse_upsc_output(text: str) -> dict:
    variables = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        variables[key.strip()] = value.strip()
    return variables


def telemetry_from_nut(variables: dict) -> dict:
    ups_temperature = to_number(variables.get("ups.temperature"))
    battery_temperature = to_number(variables.get("battery.temperature"))
    return build_telemetry(
        source="nut",
        device={
            "manufacturer": variables.get("ups.mfr") or variables.get("device.mfr"),
            "model": variables.get("ups.model") or variables.get("device.model"),
            "serial": variables.get("ups.serial") or variables.get("device.serial"),
            "firmware": variables.get("ups.firmware"),
        },
        raw_status=variables.get("ups.status"),
        battery={
            "chargePercent": variables.get("battery.charge"),
            "runtimeSeconds": variables.get("battery.runtime"),
            "voltage": variables.get("battery.voltage"),
            "temperatureC": battery_temperature,
            "lastTestResult": variables.get("ups.test.result"),
            "lastTestAt": variables.get("battery.date"),
        },
        input_values={
            "voltage": variables.get("input.voltage"),
            "frequencyHz": variables.get("input.frequency"),
        },
        output_values={
            "voltage": variables.get("output.voltage"),
            "frequencyHz": variables.get("output.frequency"),
        },
        load={
            "percent": variables.get("ups.load"),
            "realPowerW": variables.get("ups.realpower"),
            "nominalRealPowerW": variables.get("ups.realpower.nominal"),
        },
        temperature_c=ups_temperature if ups_temperature is not None else battery_temperature,
    )


def snmp_raw_status(output_source, battery_status) -> Optional[str]:
    source = to_number(output_source)
    battery = to_number(battery_status)
    if source is None and battery is None:
        return None
    tokens = []
    if source == SNMP_OUTPUT_SOURCE_BATTERY:
        tokens.extend(["OB", "DISCHRG"])
    elif source == SNMP_OUTPUT_SOURCE_BYPASS:
        tokens.extend(["OL", "BYPASS"])
    elif source == SNMP_OUTPUT_SOURCE_NORMAL:
        tokens.append("OL")
    if battery in (SNMP_BATTERY_LOW, SNMP_BATTERY_DEPLETED):
        tokens.append("LB")
    return " ".join(tokens) or None


def telemetry_from_snmp(values: dict) -> dict:
    minutes = to_number(values.get("minutes_remaining"))
    battery_temperature = to_number(values.get("battery_temperature"))
    return build_telemetry(
        source="snmp",
        device={
            "manufacturer": values.get("manufacturer"),
            "model": values.get("model"),
        },
        raw_status=snmp_raw_status(values.get("output_source"), values.get("battery_status")),
        battery={
            "chargePercent": values.get("charge_remaining"),
            "runtimeSeconds": minutes * 60 if minutes is not None else None,
            "temperatureC": battery_temperature,
        },
        input_values={"voltage": values.get("input_voltage")},
        output_values={"voltage": values.get("output_voltage")},
        load={
            "percent": values.get("output_load"),
            "realPowerW": values.get("output_power"),
        },
        temperature_c=battery_temperature,
    )


def parse_snmpget_output(text: str) -> dict:
    by_oid = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        oid, value = line.split("=", 1)
        oid = oid.strip().lstrip(".")
        value = value.strip()
        if "No Such" in value or value == "":
            by_oid[oid] = None
            continue
        if ":" in value:
            value = value.split(":", 1)[1].strip()
        by_oid[oid] = value.split(" ")[0] if value and not value.startswith('"') else value
    return {name: by_oid.get(oid) for name, oid in SNMP_OIDS.items()}


def runtime_minutes(telemetry: dict) -> Optional[int]:
    seconds = telemetry["battery"]["runtimeSeconds"]
    if seconds is None:
        return None
    return int(seconds // 60)


def telemetry_from_contract(payload: dict) -> dict:
    device = payload.get("device") or {}
    status = payload.get("status") or {}
    battery = payload.get("battery") or {}
    load = payload.get("load") or {}
    return build_telemetry(
        source=payload.get("source") or "http",
        device=device,
        raw_status=status.get("raw"),
        battery=battery,
        input_values=payload.get("input") or {},
        output_values=payload.get("output") or {},
        load=load,
        temperature_c=payload.get("temperatureC"),
    )
