import yaml
from time import sleep
import argparse


def restart_plan(plan):
    for server in plan['servers']:
        print(f"Migration du serveur {server['name']}")
        ip = server['ip']
        destination = server['destination']
        vms = server['vms']['restart']['order']
        start_delay = int(server['vms']['restart']['delay'])
        for vm in vms:
            print(f"Power ON: {vm}")
            sleep(start_delay)

def shutdown_plan(plan):
    for server in plan['servers']:
        print(f"Migration du serveur {server['name']}")
        ip = server['ip']
        destination = server['destination']
        vms = server['vms']['shutdown']['order']
        stop_delay = int(server['vms']['shutdown']['delay'])
        for vm in vms:
            print(f"Power OFF: {vm}")
            sleep(stop_delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migration des vms")
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument("--plan", required=True, help="Fichier contenant le plan de migration")
    group.add_argument("--shutdown", action="store_true", help="Éteindre les VM et migrer sur le serveur distant")
    group.add_argument("--restart", action="store_true", help="Migrer les VM depuis le serveur distant et les redémarrer")

    args = parser.parse_args()

    with open(args.plan, "r") as file:
        plan = yaml.safe_load(file)

    if args.shutdown:
        print("Lancement du plan de migration...")
        shutdown_plan(plan)
    elif args.restart:
        print("Lancement du plan de redémarrage...")
        restart_plan(plan)
    else:
        print("ERREUR: Utilisez --shutdown ou --restart")
