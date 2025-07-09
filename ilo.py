from argparse import ArgumentParser
from time import sleep
from requests import get as http_get, post as http_post
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Ilo:
    def __init__(self, ip: str, user: str, password: str, verify_ssl=False):
        self.ip = ip
        self.verify_ssl = verify_ssl
        self._auth = HTTPBasicAuth(user, password)
        self._reset_uri = ""
        self._headers = {"Content-Type": "application/json"}

    def get_server_status(self):
        try:
            resp = http_get(
                f"https://{self.ip}/redfish/v1/Systems/1/",
                headers=self._headers,
                auth=self._auth,
                verify=self.verify_ssl
            )
            resp.raise_for_status()
        except RequestException as e:
            print(f"Error getting server status: {e}")
            return "Error"
        if resp.status_code != 200:
            print(resp)
            return "Error"
        self._reset_uri = resp.json()["Actions"]["#ComputerSystem.Reset"]["target"]
        power_state = resp.json().get("PowerState", "Unknown").upper()
        print(f"PowerState: {power_state}")
        return power_state

    def stop_server(self) -> bool:
        power_state = self.get_server_status()
        if power_state == "ON":
            payload = {"ResetType": "ForceOff"}
            return self._send_payload(payload)
        elif power_state == "OFF":
            print("Server already OFF")
        else:
            print(f"Power State unsupported: {power_state}")
        return False

    def start_server(self) -> bool:
        power_state = self.get_server_status()
        if power_state == "OFF":
            payload = {"ResetType": "On"}
            return self._send_payload(payload)
        elif power_state == "ON":
            print("Server already ON")
        else:
            print(f"Power State unsupported: {power_state}")
        return False

    def _send_payload(self, payload) -> bool:
        try:
            resp = http_post(
                f"https://{self.ip}{self._reset_uri}",
                json=payload,
                headers=self._headers,
                auth=self._auth,
                verify=self.verify_ssl
            )
            print(resp.status_code, resp.text)
            return True
        except RequestException as e:
            print(f"Error posting request: {e}")
        return False


if __name__ == "__main__":
    parser = ArgumentParser(description="Éteindre et allumer un serveur grâce à son ilo")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stop", action="store_true", help="Éteindre le serveur")
    group.add_argument("--start", action="store_true", help="Allumer le serveur")
    parser.add_argument("--ip", required=True, help="Adresse IP de l'Ilo")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur de l'Ilo du serveur")
    parser.add_argument("--password", required=True, help="Mot de passe de l'Ilo du serveur")

    args = parser.parse_args()

    ilo = Ilo(args.ip, args.user, args.password)
    if args.start:
        if ilo.start_server():
            sleep(5)
            print(ilo.get_server_status())
    elif args.stop:
        if ilo.stop_server():
            sleep(5)
            print(ilo.get_server_status())
    else:
        print("ERREUR: Utilisez --start ou --stop")
