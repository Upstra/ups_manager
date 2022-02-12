from re import search

import config
import serveur
import configparser

def getListeVms() :
    ilo_str = "ilo"
    listeServ = []

    for serveur in config.nomServeur:
        # Le serveur[2:-1] c'est pout transformer "\n[esxsrv4]" <-- en --> esxsrv4
        infoConfig = config.ini[serveur[2 :-1]]

        # Là, on cherche à vérifier si l'index du serveur n'est pas un ilo sinon on ne fait rien
        if not search(ilo_str, infoConfig['host']):
            result = config.getConnexionSSH(infoConfig['host'], infoConfig['port'],infoConfig['username'], infoConfig['password'],"vim-cmd vmsvc/getallvms | grep '\[' | awk '{print$2}'")
            # Dernière ligne éditée
            # Le souci qui n'a pas été réglé avant la fin du stage est :
            # Le resultat de la requête passé sur les serveur sort sous la forme d'un tableau.
            # Hors vu le nombre de VM ca fait beaucoup, le soucis étant que ce tableau n'est composé que
            # de 2 index c'est à dire le nombre de serveur. pour chaque tour de boucle donc 2 toutes les vm sont affectée
            # A un index, par exemple l'array result[0] affiche toute les vm de l'esxsrv4 et pareillement pour result[1] pour l'esx5
            # La ce que j'aurai aimé faire mais que je n'ai pas trouvé c'est de pouvoir séparer tout ça mais je n'ai pas réussi
            #Cette commmande permet de séparer une string a partir d'un délémiteur, le soucis c'est que result n'est pas une string
            #Il faudrait la transformer en string puis utiliser le split pour retransformer en list...
            #listeServ += list(result.split(","))

        # Enfin on insert les vms dans la base de donnée
        #insertVM("vm", etat, vm[5:-1])
        else:
            pass
def getEtatvms(nom_serveur) :
    return 0
