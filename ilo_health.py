import sys
from argparse import ArgumentParser
from json import dumps as json_dumps

import requests
import urllib3
from requests.auth import HTTPBasicAuth

from data_retriever.redfish_health import parse_health
from data_retriever.cli_security import requests_verify
from data_retriever.cli_security import add_password_argument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RedfishClient:
    def __init__(self, ip: str, user: str, password: str, timeout: int, verify_ssl: bool):
        self.base = ip if ip.startswith(("http://", "https://")) else f"https://{ip}"
        self.base = self.base.rstrip("/")
        self.auth = HTTPBasicAuth(user, password)
        self.timeout = timeout
        self.verify_ssl = requests_verify(force=verify_ssl)

    def get(self, path: str) -> dict:
        response = requests.get(
            f"{self.base}{path}",
            auth=self.auth,
            timeout=self.timeout,
            verify=self.verify_ssl,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    def first_member(self, collection: str) -> str:
        members = self.get(collection).get("Members") or []
        if not members:
            raise LookupError(f"No member in {collection}")
        return members[0]["@odata.id"].rstrip("/")

    def optional(self, path: str) -> dict:
        try:
            return self.get(path)
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                return {}
            raise


def generation(client: RedfishClient):
    try:
        manager = client.get(client.first_member("/redfish/v1/Managers"))
    except (requests.RequestException, LookupError, KeyError):
        return None
    return manager.get("Model") or manager.get("FirmwareVersion")


def ilo_health(ip: str, user: str, password: str, timeout: int, verify_ssl: bool) -> dict:
    client = RedfishClient(ip, user, password, timeout, verify_ssl)
    chassis = client.first_member("/redfish/v1/Chassis")
    system = client.get(client.first_member("/redfish/v1/Systems"))
    thermal = client.optional(f"{chassis}/Thermal")
    power = client.optional(f"{chassis}/Power")
    return parse_health(thermal, power, system, generation(client))


def main() -> int:
    parser = ArgumentParser(description="Read hardware health sensors through the iLO Redfish API")
    parser.add_argument("--ip", required=True, help="iLO address")
    parser.add_argument("--user", required=True, help="iLO user")
    add_password_argument(parser, help="iLO password")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    parser.add_argument("--verify-ssl", action="store_true", help="Force certificate verification (otherwise UPSTRA_VERIFY_SSL decides)")
    args = parser.parse_args()

    try:
        print(json_dumps(ilo_health(args.ip, args.user, args.password, args.timeout, args.verify_ssl)))
        return 0
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else "?"
        print(f"iLO answered HTTP {status}", file=sys.stderr)
        return 2 if status == 401 else 1
    except (requests.RequestException, LookupError, KeyError, ValueError) as error:
        print(f"iLO health failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
