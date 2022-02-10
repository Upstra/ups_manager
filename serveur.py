#!/usr/bin/env python

# Import des modules.
from re import search

import hpilo
import config
from datetime import datetime
from time import sleep

# DATE + TIME (actuel)
timestamp = datetime.now().replace(second=0, microsecond=0)


def updateEtatServeurs(table, etat, nom):
    config.startDB()

    # Les %s permettent d'incorporer des variables à un string, là, c'est la requête SQL
    query = "UPDATE %s SET etat = '%s', last_update = '%s'  WHERE nom = '%s'" % (table, etat, timestamp, nom)
    config.cur.execute(query)
    config.closeDB()


def getEtatServeurs():
    ilo = "ilo"

    # On parcourt le tableau qui contient tous les noms de serveurs
    for serveur in config.nomServeur:
        # Le serveur[2:-1] c'est pout transformer "\n[esxsrv4]" <-- en --> esxsrv4
        infoConfig = config.config[serveur[2:-1]]

        # Là, on cherche si le serveur choisi est un ilo sinon on ne fait rien
        if search(ilo, infoConfig['host']):

            # Avec configparser le module python, il va rechercher dans la config.ini les identifiants du serveur
            # Le module HPILO est un module qui permet de ce connecter à l'ilo && de passer des commandes
            ilo = hpilo.Ilo(infoConfig['host'], infoConfig['username'], infoConfig['password'])
            etat = ilo.get_host_power_status()

            # Enfin on update l'état du serveur dans la base de donnée
            updateEtatServeurs("serveur", etat, serveur[5:-1])
        else:
            pass


def selectEtatServeur(nom_serveur):
    global nom_serv, etat_serv

    #getEtatServeurs()
    config.startDB()
    config.cur.execute("SELECT nom, etat FROM serveur WHERE nom = '%s'" % nom_serveur)
    rows = config.cur.fetchone()
    config.conn.close()

    # On transforme en variables les colonnes de la requête
    nom_serv = rows['nom']
    etat_serv = rows['etat']


# Le type = "arrêt". signifie que c'est un paramètre optionnel, il sera de base sur le type arrêt
def selectTpsGrace(nom_serveur, type="arret") :
    global tps_grace

    config.startDB()
    config.cur.execute("SELECT temps_grace_OFF, temps_grace_ON FROM serveur WHERE nom = '%s'" % nom_serveur)
    rows = config.cur.fetchone()
    config.conn.close()

    if type == "demarrage":
        tps_grace = rows['temps_grace_ON']
    else:
        tps_grace = rows['temps_grace_OFF']


def demarrage(nom_serveur):
    selectEtatServeur(nom_serveur)

    if nom_serveur == nom_serv and etat_serv == "OFF":
        # nom_serveur.set_host_power(host_power=True)

        selectEtatServeur(nom_serveur)

        if etat_serv == "ON":
            print(nom_serveur, "a été démarré")
        else :
            selectTpsGrace(nom_serveur, "demarrage")

            # La, avec la variable temps de grace que l'on à récupéré, on décrémente pour chaque seconde passée et on
            # attend une seconde pour chaque exécution
            for k in range(tps_grace, 0, -1) :
                #print("%s pas encore démarré, temps de grace de %s secondes" % (nom_serveur, k))
                sleep(1)
    else :
        print(nom_serveur, "déja", etat_serv, "(démarré)")


def arret(nom_serveur):
    selectEtatServeur(nom_serveur)
    if nom_serveur == nom_serv and etat_serv == "ON":
        # nom_serveur.set_host_power(host_power=False)

        selectEtatServeur(nom_serveur)

        # Arrêt propre
        print("[INFO] Arrêt propre en cours...")
        if etat_serv == "OFF":
            print(nom_serveur, "a été éteint")
        else:
            selectTpsGrace(nom_serveur)

            for k in range(tps_grace, 0, -1):
                getEtatServeurs()
                selectEtatServeur(nom_serveur)

                if etat_serv == "OFF":
                    print(nom_serveur, "a été éteint")
                    break
                else:
                    #print("%s pas encore éteint, temps de grace de %s secondes" % (nom_serveur, k))
                    sleep(1)

            # Arrêt Brutal
            print("[ERREUR] Arrêt propre impossible, Arrêt brutal en cours...")
            if etat_serv == "ON":
                # nom_serveur.set_host_power(host_power=False)
                for k in range(10, 0, -1):
                    getEtatServeurs()
                    selectEtatServeur(nom_serveur)

                    if etat_serv == "ON" :
                        #print("%s pas encore éteint, temps de grace de %s secondes" % (nom_serveur, k))
                        selectEtatServeur(nom_serveur)
                        sleep(1)
                    elif etat_serv == "OFF" :
                        print(nom_serveur, "a été éteint")
                        break
                    else:
                        print("ERREUR sur %s il n'est nis éteint, ni allumé" % nom_serveur)
                if etat_serv == "ON":
                    print("ERREUR sur %s il ne s'éteint pas !" % nom_serveur)
                else:
                    print(nom_serveur, "a été éteint")
    else:
        print("%s déja %s (éteint)" % (nom_serveur, etat_serv))









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
