#!/usr/bin/env python

# Import des modules.
import config
import serveur

# Partie initialisation config
import vm

config.getConfig("ilo")
config.updateConfigIni()

# Partie serveur
serveur.getEtatServeurs()

# Il est impossible de démarrer ou d'éteindre des ilo #
serveur.arret("esxsrv5")

# ATTENTION - Cette fonction n'est pas finie, il faut la retravailler (mais elle est utilisable pour des test)
#vm.getListeVms()
