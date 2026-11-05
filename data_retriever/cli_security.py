import os
import ssl
from argparse import ArgumentParser
from typing import Union

PASSWORD_ENV = "UPSTRA_PASSWORD"
SNMP_COMMUNITY_ENV = "UPSTRA_SNMP_COMMUNITY"
VERIFY_SSL_ENV = "UPSTRA_VERIFY_SSL"
CA_BUNDLE_ENV = "UPSTRA_CA_BUNDLE"
TRUE_VALUES = ("1", "true", "yes", "on")


def add_password_argument(parser: ArgumentParser, help: str, flag: str = "--password", env: str = PASSWORD_ENV):
    default = os.environ.get(env)
    parser.add_argument(
        flag,
        required=default is None,
        default=default,
        help=f"{help} (préférer la variable d'environnement {env}, invisible dans la liste des processus)",
    )


def verify_ssl_enabled() -> bool:
    return os.environ.get(VERIFY_SSL_ENV, "false").strip().lower() in TRUE_VALUES


def requests_verify(force: bool = False) -> Union[bool, str]:
    if not (force or verify_ssl_enabled()):
        return False
    return os.environ.get(CA_BUNDLE_ENV) or True


def ssl_context(force: bool = False) -> ssl.SSLContext:
    if force or verify_ssl_enabled():
        return ssl.create_default_context(cafile=os.environ.get(CA_BUNDLE_ENV) or None)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context
