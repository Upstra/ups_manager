from hpilo import Ilo
from time import sleep


def get_server_state(host: str, username: str, password: str) -> str:
    ilo = Ilo(host, username, password)
    state = ilo.get_host_power_status()
    return state


def start_server(host: str, username: str, password: str):
    server_state = get_server_state(host, username, password)

    if server_state == "OFF":
        # DÉMARRAGE DU SERVEUR VIA UNE COMMANDE DE L'ILO
        # nom_serveur.set_host_power(host_power=True)

        # La, avec la variable temps de grace que l'on à récupéré, on décrémente pour chaque seconde passée et on
        # attend une seconde pour chaque exécution
        sleep(60)
    elif server_state == "ON":
        print(f"{host} déjà démarré : {server_state}")
    else:
        print("[ERREUR] Vous cherchez à démarrer autre chose qu'un serveur...")


def stop_server(host: str, username: str, password: str):
    server_state = get_server_state(host, username, password)

    # Cette condition va vérifier si on possède bien le même nom de serveur que celui récupéré sur la BDD
    # Il va checker si l'utilisateur ne tente pas d'éteindre un ILO (ce qui serait impossible)
    if server_state == "ON":
        # Commande qui éteint proprement le serveur en allant la chercher dans la base de donnée selon le serveur
        #config.getConnexionSSH(config.ini[nom_serveur]['host'],config.ini[nom_serveur]['port'],config.ini[nom_serveur]['username'], config.ini[nom_serveur]['password'], shutdown_command)

        # Arrêt propre
        print(f"[INFO] Arrêt propre en cours pour le serveur {host}...")

        if server_state == "OFF":
            print(f"{host} a été éteint")
        else:
            sleep(60)

        # Arrêt Brutal
        print(f"[ERREUR] Arrêt propre impossible pour {host}, Arrêt brutal en cours...")

        # On réalise l'arrêt brutal via une commande de l'ilo...
        # nom_serveur.set_host_power(host_power=False)
        for k in range(10, 0, -1):
            if server_state == "ON":
                sleep(1)
            elif server_state == "OFF":
                print(f"{host} a été éteint")
                break
            else:
                print(f"[ERREUR] {host} n'est nis éteint, ni allumé")

        if server_state == "ON":
            print(f"[ERREUR] {host} ne s'éteint pas !")
        elif server_state == "OFF":
            print(f"{host} a été éteint")
        else:
            print(f"[ERREUR] {host} n'a pas d'état (ON ou OFF) !!")

    elif server_state == "OFF":
        print(f"{host} déja éteint: {server_state}")
    else:
        print("[ERREUR] Vous cherchez à arrêter autre chose qu'un serveur...")
