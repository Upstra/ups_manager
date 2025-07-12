from requests import get as http_get, post as http_post
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PayloadException(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code


class Ilo:
    def __init__(self, ip: str, user: str, password: str, verify_ssl=False):
        self.ip = ip
        self.verify_ssl = verify_ssl
        self._auth = HTTPBasicAuth(user, password)
        self._reset_uri = ""
        self._headers = {"Content-Type": "application/json"}

    def get_server_status(self) -> str:
        """
        Get the server power status
        Returns:
            str: Eather "ON", "OFF", "UNKNOWN" if power status couldn't be retrieved, or any unexpected power status
        Raises:
            requests.exceptions.RequestException: If connection couldn't be established
            Exception: If process fails for any reason
        """
        resp = http_get(
            f"https://{self.ip}/redfish/v1/Systems/1/",
            headers=self._headers,
            auth=self._auth,
            verify=self.verify_ssl
        )
        resp.raise_for_status()
        self._reset_uri = resp.json()["Actions"]["#ComputerSystem.Reset"]["target"]
        power_state = resp.json().get("PowerState", "UNKNOWN").upper()
        return power_state

    def stop_server(self):
        """
        Send a stop request to the Ilo of the server. get_server_status() has to be called before calling stop_server()
        Raises:
            requests.exceptions.RequestException: If connection couldn't be established
            PayloadException: If response from Ilo is not successful
            RuntimeError: If get_server_status() hasn't been called before stop_server()
            Exception: If process fails for any reason
        """
        if not self._reset_uri:
            raise RuntimeError("get_server_status() must be called before stop_server()")
        payload = {"ResetType": "ForceOff"}
        self._send_payload(payload)

    def start_server(self):
        """
        Send a start request to the Ilo of the server. get_server_status() has to be called before calling start_server()
        Raises:
            requests.exceptions.RequestException: If connection couldn't be established
            PayloadException: If response from Ilo is not successful
            RuntimeError: If get_server_status() hasn't been called before start_server()
            Exception: If process fails for any reason
        """
        if not self._reset_uri:
            raise RuntimeError("get_server_status() must be called before start_server()")
        payload = {"ResetType": "On"}
        self._send_payload(payload)

    def _send_payload(self, payload):
        """
        Send a payload to Ilo with a post request
        Args:
            payload (dict): Payload to send to Ilo. Usually, either {"ResetType": "ForceOff"} or {"ResetType": "On"}
        Raises:
            requests.exceptions.RequestException: If connection couldn't be established
            PayloadException: If response from Ilo is not successful
            Exception: If process fails for any reason
        """
        resp = http_post(
            f"https://{self.ip}{self._reset_uri}",
            json=payload,
            headers=self._headers,
            auth=self._auth,
            verify=self.verify_ssl
        )
        resp.raise_for_status()
        if resp.status_code not in [200, 202, 204]:
            raise PayloadException(resp.text, resp.status_code)
