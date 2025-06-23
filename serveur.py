#!/usr/bin/env python

# Import des modules.
from re import search
import hpilo
import config
from datetime import datetime
from time import sleep


# DATE + TIME (actuel)
timestamp = datetime.now().replace(second=0, microsecond=0)

# update de la table choisie dans les paramêtre (elle est adaptée pour la tbl serveur)
def updateEtatServeurs(table, etat, nom):
    config.startDB()

    # Les %s permettent d'incorporer des variables à un string, là, c'est la requête SQL
    query = "UPDATE %s SET etat = '%s', last_update = '%s' WHERE nom = '%s'" % (table, etat, timestamp, nom)
    config.cur.execute(query)
    config.closeDB()


def getEtatServeurs():
    global ilo_str
    ilo_str = "ilo"

    # On parcourt le tableau qui contient tous les noms de serveurs
    for serveur in config.nomServeur:
        # Le serveur[2:-1] c'est pout transformer "\n[esxsrv4]" <-- en --> esxsrv4
        infoConfig = config.ini[serveur[2:-1]]

        # Là, on cherche si le serveur choisi est un ilo sinon on ne fait rien
        if search(ilo_str, infoConfig['host']):

            # Avec configparser le module python, il va rechercher dans la config.ini les identifiants du serveur
            # Le module HPILO est un module qui permet de ce connecter à l'ilo && de passer des commandes
            ilo = hpilo.Ilo(infoConfig['host'], infoConfig['username'], infoConfig['password'])
            etat = ilo.get_host_power_status()

            # Enfin on update l'état du serveur dans la base de donnée
            updateEtatServeurs("serveur", etat, serveur[5:-1])
        else:
            pass


def selectEtatServeur(nom_serveur):
    global nom_serv, etat_serv, shutdown_command

    # getEtatServeurs() # Je l'ai mis en commentaie car en fait on peu juste appeler le select etat server tout en
    # faisant en même temps une update de la db mais le soucis c'est que c'est trop lent...
    config.startDB()
    config.cur.execute("SELECT nom, etat, shutdown_command FROM serveur WHERE nom = '%s'" % nom_serveur)
    rows = config.cur.fetchone()
    config.conn.close()

    # On transforme en variables les colonnes de la requête
    nom_serv = rows['nom']
    etat_serv = rows['etat']
    shutdown_command = rows['shutdown_command']


# Le type = "arrêt". signifie que c'est un paramètre optionnel, il sera de base sur le type arrêt
def selectTpsGrace(nom_serveur, type="arret"):
    global tps_grace

    config.startDB()
    config.cur.execute("SELECT temps_grace_OFF, temps_grace_ON FROM serveur WHERE nom = '%s'" % nom_serveur)

    # Le .fetchone() c'est pour préciser que l'on attend un seul résultat de la requête, cette commande permet
    # l'optimisation du script
    rows = config.cur.fetchone()
    config.conn.close()

    if type == "demarrage":
        tps_grace = rows['temps_grace_ON']
    else:
        tps_grace = rows['temps_grace_OFF']


def demarrage(nom_serveur):
    selectEtatServeur(nom_serveur)

    if nom_serveur == nom_serv and etat_serv == "OFF" and not search(ilo_str, nom_serveur):
        # DÉMARRAGE DU SERVEUR VIA UNE COMMANDE DE L'ILO
        # nom_serveur.set_host_power(host_power=True)

        selectEtatServeur(nom_serveur)

        selectTpsGrace(nom_serveur, "demarrage")

        # La, avec la variable temps de grace que l'on à récupéré, on décrémente pour chaque seconde passée et on
        # attend une seconde pour chaque exécution
        for k in range(tps_grace, 0, -1) :
            #print("%s pas encore démarré, temps de grace de %s secondes" % (nom_serveur, k))
            sleep(1)
    elif  nom_serveur == nom_serv and etat_serv == "ON":
        print(nom_serveur, "déja", etat_serv, "(démarré)")
    else:
        print("[ERREUR] Vous cherchez à démarrer autre chose qu'un serveur...")



def arret(nom_serveur):
    selectEtatServeur(nom_serveur)

    # Cette condition va vérifier si on possède bien le même nom de serveur que celui récupéré sur la BDD
    # Il va checker si l'utilisateur ne tente pas d'éteindre un ILO (ce qui serait impossible)
    if nom_serveur == nom_serv and etat_serv == "ON" and not search(ilo_str, nom_serveur):
        # Commande qui éteint proprement le serveur en allant la chercher dans la base de donnée selon le serveur
        #config.getConnexionSSH(config.ini[nom_serveur]['host'],config.ini[nom_serveur]['port'],config.ini[nom_serveur]['username'], config.ini[nom_serveur]['password'], shutdown_command)
        selectEtatServeur(nom_serveur)

        # Arrêt propre
        print("[INFO] Arrêt propre en cours pour le serveur %s..." % nom_serveur)

        selectTpsGrace(nom_serveur)

        for k in range(tps_grace, 0, -1):
            # A chaque tour de boucle, il va vérifier l'état des serv et les mettre a jour dans la db Il y a moyen
            # d'optimiser ça en retournant uniquement l'état des serv sans mettre a jour la db, je n'ai pas eu le
            # temps de réaliser ça
            getEtatServeurs()
            selectEtatServeur(nom_serveur)

            if etat_serv == "OFF":
                print("%s a été éteint", nom_serveur)
                break
            else:
                #print("%s pas encore éteint, temps de grace de %s secondes" % (nom_serveur, k))
                sleep(1)

        # Arrêt Brutal
        print("[ERREUR] Arrêt propre impossible pour %s, Arrêt brutal en cours..." % nom_serveur)


        # On réalise l'arrêt brutal via une commande de l'ilo...
        # nom_serveur.set_host_power(host_power=False)
        for k in range(10, 0, -1):
            getEtatServeurs()
            selectEtatServeur(nom_serveur)

            if etat_serv == "ON":
                #print("%s pas encore éteint, temps de grace de %s secondes" % (nom_serveur, k))
                selectEtatServeur(nom_serveur)
                sleep(1)
            elif etat_serv == "OFF":
                print(nom_serveur, "a été éteint")
                break
            else:
                print("[ERREUR] %s  n'est nis éteint, ni allumé" % nom_serveur)


        if etat_serv == "ON":
            print("[ERREUR] %s ne s'éteint pas !" % nom_serveur)
        elif etat_serv == "OFF":
            print(nom_serveur, "a été éteint")
        else:
            print("[ERREUR] %s n'a pas d'état (ON ou OFF) !!" % nom_serveur)

    elif nom_serveur == nom_serv and etat_serv == "OFF":
        print("%s déja %s (éteint)" % (nom_serveur, etat_serv))
    else:
        print("[ERREUR] Vous cherchez à arrêter autre chose qu'un serveur...")









# C'est pour avoir l'uptime, mais il est pas bon je ne comprend pas pourquoi
# Si tu veux rajouter l'uptime oublie pas de le mettre dans query après last_update et dans l'appel de la fonction
# if etat == "ON":
# uptime = ilo.get_server_power_on_time()
# print(uptime)
# else:
# uptime = 0
#
# dans les parametre de la fonction
# def updateEtatServeurs(table, etat, update ,nom):
# dans la fonction update :
#     query = "UPDATE %s SET etat = '%s', last_update = '%s', uptime = '%s'  WHERE nom = '%s'" % (table, etat, timestamp, uptime, nom)
