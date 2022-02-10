#!/usr/bin/env python

# Import des modules.
import config
import serveur

# Partie initialisation config
config.connect()
config.getConfig("ilo")
config.updateConfigIni()

# Partie serveur
serveur.getEtatServeurs()
serveur.arret("esxsrv5")

# Partie controle (en developpement)...


