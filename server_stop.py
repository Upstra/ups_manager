from argparse import ArgumentParser
from requests.exceptions import RequestException, HTTPError

from data_retriever.dto import result_message, output
from data_retriever.ilo import Ilo, PayloadException


def server_stop(ip: str, user: str, password: str) -> dict:
    """
    Stop a server
    Args:
        ip (str): The ip of the Ilo of the server
        user (str): The username of the Ilo of the server
        password (str): The password of the Ilo of the server
    Returns:
        dict: A dictionary formatted for json dump containing the result message. See result_message() function in dto.py
    """
    ilo = Ilo(ip, user, password)
    try:
        power_status = ilo.get_server_status()
        if power_status == "OFF":
            return result_message("Server is already off", 403)
        elif power_status != "ON":
            return result_message(f"Power Status unsupported: {power_status}", 403)

        ilo.stop_server()
        return result_message("Server has been successfully stopped", 200)

    except RequestException as e:
        if isinstance(e, HTTPError) and e.response is not None:
            return result_message(str(e), e.response.status_code)
        else:
            return result_message(f"Error sending requests: {e}", 400)
    except PayloadException as e:
        return result_message(f"Error sending payload: {e.message}", e.status_code)
    except Exception as e:
        return result_message(f"Error sending requests: {e}", 500)


if __name__ == "__main__":
    parser = ArgumentParser(description="Éteindre un serveur grâce à son ilo")
    parser.add_argument("--ip", required=True, help="Adresse IP de l'Ilo")
    parser.add_argument("--user", required=True, help="Nom d'utilisateur de l'Ilo du serveur")
    parser.add_argument("--password", required=True, help="Mot de passe de l'Ilo du serveur")

    args = parser.parse_args()

    output(server_stop(args.ip, args.user, args.password))
