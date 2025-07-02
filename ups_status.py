from time import sleep, strftime
from subprocess import check_output as command_run, CalledProcessError

def get_ups_status(ups_name="ondulerpi", host="localhost"):
    try:
        output = command_run(["upsc", f"{ups_name}@{host}"], text=True)
        status_lines = output.strip().splitlines()
        status_dict = {}
        for line in status_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                status_dict[key.strip()] = value.strip()
        return status_dict
    except CalledProcessError as e:
        print(f"Erreur lors de la commande upsc : {e}")
        return {}

if __name__ == "__main__":
    status = get_ups_status()
    ups_status = status.get("ups.status", "Inconnu")
    print(f"Statut de l'onduleur : {ups_status}")
    while True:
        try:
            ups_status = status.get("ups.status", "Inconnu")
            print(f"Statut UPS : {ups_status} - {strftime('%H:%M:%S')}")
            if "OL" in ups_status:
                print("Onduleur sur secteur (On Line)")
            elif "OB" in ups_status:
                print("Onduleur sur batterie (On Battery)")
            elif "LB" in ups_status:
                print("Onduleur sur batterie critique (Low Battery)")
            elif "CHRG" in ups_status:
                print("Onduleur en charge")
            else:
                print("⚠️ Statut inconnu ou non accessible")
        except Exception as e:
            print(f"Erreur : {e}")
        sleep(10)
        