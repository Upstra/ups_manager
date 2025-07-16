# Ups Manager

This project contains a collection of Python scripts used to orchestrate VMware hosts and virtual machines when dealing
with power events. It was initially designed to prepare for UPS outages by safely migrating or shutting down VMs and
powering hosts back on when power is restored.

## Features

- Start and stop ESXi servers through their HP iLO interfaces.
- Start, stop and migrate individual virtual machines.
- Retrieve detailed information and metrics for hosts and VMs.
- Execute a complete migration/shutdown plan defined in YAML.
- Store migration events in Redis in order to roll back the operations afterwards.
- Convenience shell scripts that wrap the Python commands and activate the project virtual environment.

## Project layout

```
.
├── data_retriever/       # Connection helpers and data transfer objects
├── plans/                # Example migration plan in YAML
├── *.py                  # Command line utilities (server_start.py, vm_migration.py, ...)
├── *.sh                  # Shell wrappers for the Python tools
└── requirements.txt      # Python dependencies
```

## Installation

A recent Python (>3.9) interpreter is required. The `init.sh` script will create a local virtual environment and install all dependencies:

```bash
./init.sh
```

Alternatively you may use Docker for an isolated environment:

```bash
docker compose up -d --build
```

## Usage

Each Python file can be executed directly to perform an action. Below are a few common examples.

### Start and stop a host

```bash
./server_start.sh --ip 192.0.2.5 --user admin --password secret
./server_stop.sh  --ip 192.0.2.5 --user admin --password secret
```

### Manage virtual machines

```bash
./vm_start.sh --moid vm-123 --ip 198.51.100.10 --user admin --password secret
./vm_stop.sh --moid vm-123 --ip 198.51.100.10 --user admin --password secret
./vm_migration.sh --vm_moid vm-123 --dist_moid host-200 --ip 198.51.100.10 --user admin --password secret
```

### Run a migration plan

Update `plans/migration-example.yml` (or create your own file) with the information about your vCenter, hosts and vm order, then execute:

```bash
./migration_plan.sh
```

When power comes back, the recorded events can be replayed with:

```bash
./restart_plan.sh
```

### Query information

- `list_vm.py` lists all VMs from the given server.
- `server_info.py` and `server_metrics.py` return information or metrics for a host.
- `vm_metrics.py` returns metrics for a virtual machine.
- `ups_battery.sh` prints the remaining UPS battery time via SNMP.

All commands accept `--help` for detailed parameters.

## Example migration plan structure

```yaml
vCenter:
  ip: 172.1.2.3
  user: vCenterUser
  password: vCenterPassword
  port: 443

servers:
  - server:
      host:
        name: server_name
        moid: srv1_moid
        ilo:
          ip: 172.2.3.4
          user: user
          password: password
      destination:
        name: dist_name
        moid: srv2_moid
        ilo:
          ip: 172.2.3.4
          user: user
          password: password
      shutdown:
        vmOrder:
          - vmMoId: vm1
          - vmMoId: vm2
          - vmMoId: vm3
        delay: 60
      restart:
        delay: 60
```

This file is provided as `plans/migration-example.yml` and can be adapted to your environment.

---

The scripts print JSON formatted results to stdout and exit with a message describing the executed operation.
They can easily be integrated into automation tools or other monitoring systems.
