from configparser import ConfigParser
from time import sleep


def last_ups_status(log_file_path: str):
    with open(log_file_path, "r") as f:
        lines = f.readlines()

    for line in reversed(lines):
        if "OB" in line.lower():
            # On Battery
            continue
        elif "OL" in line.lower():
            # On Line
            continue


if __name__ == "__main__":
    ini = ConfigParser()
    ini.read('config.ini')
    ups_log_file = ini['ups']['log_file']
    status_delay = int(ini['ups']['status_delay'])

    while True:
        print(last_ups_status(ups_log_file))
        sleep(status_delay)
