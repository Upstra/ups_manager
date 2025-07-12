from argparse import ArgumentParser

from requests.exceptions import RequestException

from data_retriever.dto import result_message
from data_retriever.ilo import Ilo, PayloadException


def server_start(ip: str, user: str, password: str) -> str:
    """
    Start a server
    Args:
        ip (str): The ip of the Ilo of the server
        user (str): The username of the Ilo of the server
        password (str): The password of the Ilo of the server
    Returns:
        str: A string formatted json dump of the result message. See result_message() function in dto.py
    """
    ilo = Ilo(ip, user, password)
    try:
        power_status = ilo.get_server_status()
        if power_status == "ON":
            return result_message("Server is already ON", 403)
        elif power_status != "OFF":
            return result_message(f"Power Status unsupported: {power_status}", 403)

        ilo.start_server()
        return result_message("Server has been successfully started", 200)

    except RequestException as e:
        return result_message(f"Error sending requests: {e}", 400)
    except PayloadException as e:
        return result_message(f"Error sending payload: {e.message}", e.status_code)
    except Exception as e:
        return result_message(f"Error sending requests: {e}", 500)


if __name__ == "__main__":
    parser = ArgumentParser(description="Allumer un serveur grâce à son ilo")
    parser.add_argument("--ip", required=True, help="Adresse IP de l'Ilo")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur de l'Ilo du serveur")
    parser.add_argument("--password", required=True, help="Mot de passe de l'Ilo du serveur")

    args = parser.parse_args()

    print(server_start(args.ip, args.user, args.password))
