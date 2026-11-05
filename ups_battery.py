import sys
from argparse import ArgumentParser
from json import dumps as json_dumps
from shutil import which
from subprocess import run, TimeoutExpired

import os

import requests

from data_retriever.cli_security import SNMP_COMMUNITY_ENV
from data_retriever.ups_telemetry import (
    SNMP_OIDS,
    parse_snmpget_output,
    parse_upsc_output,
    runtime_minutes,
    telemetry_from_contract,
    telemetry_from_nut,
    telemetry_from_snmp,
)


class TelemetryError(Exception):
    pass


def http_base_url(address: str) -> str:
    base = address.rstrip("/")
    for suffix in ("/battery", "/telemetry"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    return base


def collect_http(address: str, timeout: int) -> dict:
    response = requests.get(f"{http_base_url(address)}/telemetry", timeout=timeout)
    response.raise_for_status()
    return telemetry_from_contract(response.json())


def collect_nut(address: str, ups_name: str, timeout: int) -> dict:
    binary = which("upsc")
    if binary is None:
        raise TelemetryError("upsc binary not found")
    result = run(
        [binary, f"{ups_name}@{address}"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise TelemetryError(result.stderr.strip() or "upsc failed")
    return telemetry_from_nut(parse_upsc_output(result.stdout))


def snmpget(binary: str, address: str, community: str, oid: str, timeout: int) -> str:
    result = run(
        [binary, "-v1", "-c", community, "-On", "-Oe", "-t", str(timeout), "-r", "1", address, oid],
        capture_output=True,
        text=True,
        timeout=timeout * 3,
    )
    if result.returncode != 0:
        return f".{oid} = No Such Object"
    return result.stdout


def collect_snmp(address: str, community: str, timeout: int) -> dict:
    binary = which("snmpget") or "/bin/snmpget"
    lines = [snmpget(binary, address, community, oid, timeout) for oid in SNMP_OIDS.values()]
    values = parse_snmpget_output("\n".join(lines))
    if all(value is None for value in values.values()):
        raise TelemetryError(f"No SNMP answer from {address}")
    return telemetry_from_snmp(values)


def collect(address: str, source: str, ups_name: str, community: str, timeout: int) -> dict:
    if source == "auto":
        source = "http" if address.startswith(("http://", "https://")) else "snmp"
    if source == "http":
        return collect_http(address, timeout)
    if source == "nut":
        return collect_nut(address, ups_name, timeout)
    return collect_snmp(address, community, timeout)


def main() -> int:
    parser = ArgumentParser(description="Read UPS telemetry")
    parser.add_argument("--ip", required=True, help="UPS address, NUT host or mock HTTP URL")
    parser.add_argument("--format", choices=["minutes", "json"], default="minutes")
    parser.add_argument("--source", choices=["auto", "snmp", "nut", "http"], default="auto")
    parser.add_argument("--ups-name", default="ups", help="NUT UPS name")
    parser.add_argument("--community", default=os.environ.get(SNMP_COMMUNITY_ENV, "public"), help=f"SNMP community (or {SNMP_COMMUNITY_ENV})")
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    try:
        telemetry = collect(args.ip, args.source, args.ups_name, args.community, args.timeout)
    except (TelemetryError, requests.RequestException, TimeoutExpired, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.format == "json":
        print(json_dumps(telemetry))
        return 0

    minutes = runtime_minutes(telemetry)
    if minutes is None:
        print("Runtime not available", file=sys.stderr)
        return 1
    print(minutes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
