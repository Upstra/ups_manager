#!/usr/bin/env python

import configparser
import paramiko as paramiko
import pymysql.cursors

ini = configparser.ConfigParser()
ini.read('config.ini')
mysql = ini['mysql']
nomServeur = ""
identifiants = []

# CONF DE LA BASE DE DONNEE
def startDB():
    global conn, cur
    # La fonction renvoie une connexion.
    # Vous pouvez changer les arguments de la connexion.
    conn = pymysql.connect(host=mysql['host'],
                           user=mysql['username'],
                           password=mysql['password'],
                           db=mysql['db'],
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    # Création du cursor
    cur = conn.cursor()

def closeDB():

    conn.commit()
    conn.close()


# Connecter python à la base de donnée
def connect():
    startDB()
    closeDB()
connect()

# Insérer des données à la base de donnée (pas optimisé pour l'upsmgr)
def insert(title, author, year, isbn):
    startDB()
    # SQL queries to insert
    cur.execute("INSERT INTO ilo VALUES (NULL,?,?,?,?)", (title, author, year, isbn))
    closeDB()


# Récupérer la config pour la table passé en paramêtre
def getConfig(table):
    global identifiants
    startDB()
    #cur.execute("SELECT nom, host, port, username, passwd FROM %s" % (table))

    cur.execute("SELECT ilo.nom, ilo.host, ilo.port, ilo.username, ilo.passwd, serveur.nom, serveur.host, serveur.port, serveur.username, serveur.passwd FROM ilo INNER join serveur on id_serv = serveur.id")
    rows = cur.fetchall()
    conn.close()

    # x va s'incrémenter pour chercher tous les noms esx && ILO
    x = 0



    # Tableau qui va contenir les identifiants des esx && ILO
    identifiants = []

    for row in rows :
        # Récupération des identifiants des ILO
        nomIlo = row['nom']
        hostIlo = row['host']
        portIlo = row['port']
        usernameIlo = row['username']
        passwordIlo = row['passwd']
        # Récupération des identifiants des Serveurs
        nomServeur = row['serveur.nom']
        hostServeur = row['serveur.host']
        portServeur = row['serveur.port']
        usernameServeur = row['serveur.username']
        passwordServeur = row['serveur.passwd']

        # On formalise, pour que dans le config.ini ça s'affiche proprement...
        identifiants += ["\n[%s]" % nomIlo, "\nhost = %s" % hostIlo, "\nport = %s" % portIlo,
                         "\nusername = %s" % usernameIlo,
                         "\npassword = %s \n" % passwordIlo, "\n[%s]" % nomServeur, "\nhost = %s" % hostServeur,
                         "\nport = %s" % portServeur, "\nusername = %s" % usernameServeur,
                         "\npassword = %s \n" % passwordServeur]
        x += 1

# Fonction qui va mettre à jour le fichier config.ini
def updateConfigIni():
    global nomServeur
    # Pointeurs pour la position
    k, i = 0, 0
    nomServeur = []

    # On ouvre le fichier en read only
    with open("config.ini", "r") as f :
        lines = f.readlines()

    # On autorise a python de pouvoir supprimer/écrire dans le fichier
    with open("config.ini", "w") as f:
        # Cette boucle va effacer les lignes pour faire place aux nouveaux identifiants
        for vide in lines:
            if k != 5:
                f.write(vide)
                k += 1

        # Cette boucle va écrire les identifiants des ilo actuels dans la config.ini
        for data in lines:
            while i < len(identifiants):
                if not i % 5:
                    nomServeur.append(identifiants[i])

                f.write(identifiants[i])
                i += 1

# SSH (module fonctionnel, mais pas pour les ILO)
def getConnexionSSH(host, port, username, password, command):
    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(host, port, username, password)

    stdin, stdout, stderr = ssh.exec_command(command)

    connection = stdout.readlines()

    return connection

def getAllNomServeur():
    return nomServeur