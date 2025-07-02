from configparser import ConfigParser
from time import sleep, time
from subprocess import check_output as command_run
from os.path import join as path_join
import logging


def get_ups_status(ups_name, host="localhost"):
    output = command_run(["upsc", f"{ups_name}@{host}"], text=True)
    status_lines = output.strip().splitlines()
    status_dict = {}
    for line in status_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            status_dict[key.strip()] = value.strip()
    return status_dict


if __name__ == "__main__":
    ini = ConfigParser()
    ini.read('config.ini')
    ups_name = "upstra"
    status_delay = int(ini['ups']['status_delay'])
    update_delay = int(ini['ups']['update_delay'])

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(path_join("logs", "ups_status.log"), mode='a', encoding='utf-8'),
            logging.StreamHandler() # Affichage dans la console
        ]
    )
    logger = logging.getLogger(ups_name)

    start_time = time()
    last_status = ""

    while True:
        try:
            status = get_ups_status(ups_name)
            ups_status = status.get("ups.status", "Inconnu")
        except Exception as e:
            message = f"Erreur : {e}"
            if last_status != message:
                last_status = message
                logger.error(message)
            sleep(status_delay)
            continue

        if ups_status != last_status:
            if "OL" in ups_status:
                logger.info("Onduleur sur secteur (On Line)")
            elif "OB" in ups_status:
                logger.warning("Onduleur sur batterie (On Battery)")
            elif "LB" in ups_status:
                logger.critical("Onduleur sur batterie critique (Low Battery)")
            elif "CHRG" in ups_status:
                logger.info("Onduleur en charge")
            else:
                logger.error("Statut inconnu ou non accessible")
        sleep(status_delay)
