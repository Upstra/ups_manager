# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**UPS Manager** — Python CLI toolset for orchestrating VMware ESXi hosts and VMs during UPS power events. On power loss: migrates VMs to a destination host, then shuts down source hosts via HP iLO. On power restore: reverses the sequence using Redis-cached migration events.

## Setup

```bash
./init.sh           # creates venv + installs requirements.txt
# OR
docker compose up -d --build   # isolated Docker environment
```

Python ≥ 3.9 required.

## Commands

Each `.sh` script activates the venv and delegates to the matching `.py` file.

```bash
# Server power (via HP iLO)
./server_start.sh --ip <ilo_ip> --user <u> --password <p>
./server_stop.sh  --ip <ilo_ip> --user <u> --password <p>

# VM lifecycle (via vCenter)
./vm_start.sh     --moid <vm_moid> --ip <vcenter_ip> --user <u> --password <p>
./vm_stop.sh      --moid <vm_moid> --ip <vcenter_ip> --user <u> --password <p>
./vm_migration.sh --vm_moid <vm> --dist_moid <host> --ip <vcenter_ip> --user <u> --password <p>

# Orchestration plans
./migration_plan.sh   # execute full shutdown/migration plan from plans/migration.yml
./restart_plan.sh     # replay recorded events from Redis to reverse the migration

# Metrics / info
./server_info.sh    --ip <vcenter_ip> --user <u> --password <p>
./server_metrics.sh --ip <vcenter_ip> --user <u> --password <p>
./vm_metrics.sh     --moid <vm_moid> --ip <vcenter_ip> --user <u> --password <p>
./list_vm.sh        --ip <vcenter_ip> --user <u> --password <p>
./list_server.sh    --ip <vcenter_ip> --user <u> --password <p>

# UPS
./ups_battery.sh    # SNMP query for remaining battery time

# Cache
./cache_metrics.sh         # start metric caching daemon
./cache_metrics_kill.sh    # stop it
```

All commands accept `--help`. All print JSON to stdout.

## Architecture

### `data_retriever/` — Shared Library

| File | Purpose |
|---|---|
| `vm_ware_connection.py` | VMware vCenter connection wrapper (pyVmomi) |
| `ilo.py` | HP iLO REST API client (server power via `requests`) |
| `yaml_parser.py` | Loads and validates `plans/migration.yml` into typed dataclasses (`VCenter`, `Server`, `UpsGrace`, etc.) |
| `cache.py` / `cache_element.py` | Redis cache helpers for metric caching |
| `migration_event.py` | Event types: `VMMigrationEvent`, `VMShutdownEvent`, `ServerShutdownEvent`, `VMStartedEvent`, `MigrationErrorEvent` |
| `migration_event_queue.py` | Redis-backed event queue (`EventQueue`) — persists migration operations so `restart_plan.sh` can replay them |
| `dto.py` | Shared data transfer objects |
| `decrypt_password.py` | AES decryption for passwords stored encrypted in the YAML plan |

### Migration Plan Flow

`migration_plan.py` → `shutdown()`:
1. Connects to vCenter via `VMwareConnection`
2. For each server in the plan: migrates VMs in `vmOrder` sequence to `destination` host
3. Each operation is pushed to `EventQueue` (Redis) as a typed event
4. Source host is powered off via iLO after VMs are migrated
5. `restart_plan.sh` reads the queue in reverse to power hosts back on and migrate VMs home

### Plan Configuration

Plans live in `plans/`. The active plan is `plans/migration.yml` (gitignored — copy from `plans/migration-example.yml`).

Passwords in the plan are AES-encrypted. Use `data_retriever/decrypt_password.py` logic for encryption. The encryption key comes from the `.env` file.

### Environment

`.env` is required for Redis connection and encryption key. See `.env.example` if present, or check `data_retriever/` imports for the expected variable names.

### Integration with infra-control

The NestJS backend (`infra-control`) calls these scripts via its `PythonExecutorService` to perform VMware operations from the web UI. The scripts are designed to be composable — they print structured JSON and exit, making them easy to integrate into any automation layer.
