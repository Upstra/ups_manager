from argparse import ArgumentParser

import requests
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Ilo:
    def __init__(self, ip: str, verify_ssl=False):
        self.ip = ip
        self.verify_ssl = verify_ssl
        self._session = None
        self._reset_uri = None
        self._headers = {"Content-Type": "application/json"}

    def connect(self, user: str, password: str):
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(user, password)
        self._session.verify = self.verify_ssl

    def get_server_status(self):
        resp = self._session.get(f"https://{self.ip}/redfish/v1/Systems/1/", headers=self._headers)
        if resp.status_code != 200:
            print(resp)
            return "Error"
        self._reset_uri = resp.json()["Actions"]["#ComputerSystem.Reset"]["target"]
        power_state = resp.json().get("PowerState", "Unknown")
        print(f"json: {resp.json()}")
        print(f"PowerState: {power_state}")
        return power_state

    def stop_server(self):
        power_state = self.get_server_status()
        if power_state == "ON":
            payload = {"ResetType": "ForceOff"}
            resp = self._session.post(f"https://{self.ip}{self._reset_uri}", json=payload, headers=self._headers)
            print(resp.status_code, resp.text)

    def start_server(self):
        power_state = self.get_server_status()
        if power_state == "OFF":
            payload = {"ResetType": "On"}
            resp = self._session.post(f"https://{self.ip}{self._reset_uri}", json=payload, headers=self._headers)
            print(resp.status_code, resp.text)


if __name__ == "__main__":
    parser = ArgumentParser(description="Éteindre et allumer un serveur grâce à son ilo")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stop", action="store_true", help="Éteindre le serveur")
    group.add_argument("--start", action="store_true", help="Allumer le serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP de l'Ilo")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur de l'Ilo du serveur")
    parser.add_argument("--password", required=True, help="Mot de passe de l'Ilo du serveur")

    args = parser.parse_args()

    ilo = Ilo(args.ip)
    print(f"Connection avec l'utilisateur: {args.user} et mot de passe: {args.password}")
    ilo.connect(args.user, args.password)
    if args.start:
        ilo.start_server()
    elif args.stop:
        ilo.stop_server()
    else:
        print("ERREUR: Utilisez --start ou --stop")
