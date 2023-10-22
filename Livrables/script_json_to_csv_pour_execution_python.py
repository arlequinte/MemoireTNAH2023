# # # # # # # # # # # # # # # # #  Code de transformation des notices Agorha en Contenus Omeka S pour La Fabrique de l'Art # # # # # # # # # # # # # # # # # 

# # # #  Version éditée en stage de fin d'études master Ecole des Chartes - TNAH ; 27 juillet 2023 ; autrice: Anne Bugner # # # # 

#  Librairies Python nécessaires à l'exécution du code
import json
import re
import csv

# ********** Renseignement préliminaire **********
# Nous utilisons ici un fichier constitué manuellement des notices corrigées selon les dernières consignes décidées début juin 2023. L'extraction automatique de la totalité des notices (en se connectant en tant que contributeur.ice à Agorha, pour accéder aux centaines de notices "en cours") se fait en entrant l'URL suivante:
# https://agorha.inha.fr/api/notice/exportjson?noticeType=ARTWORK&database=88  (pour la base Panneaux de l'INHA)
# https://agorha.inha.fr/api/notice/exportjson?noticeType=ARTWORK&database=89  (pour la base Enluminure des MSS)

# Quel fichier utilise-t-on?
input_file = 'train89.json'
# input_file = 'train88.json' (A inverser tant que je n'ai pas trouvé comment générer la meta-fonction du siècle)

# Préambule nécessaire à toute opération sur fichier JSON: ouverture du fichier en mode lecture
with open(input_file, 'r', encoding='utf-8') as f:
    # Lecture du contenu
    main_data = json.load(f)

# Rechercher les notices de type Oeuvre (notices mères) et de type Image au sein des databases
# Définir une procédure de tri
def art_notices_partition(data):

    # Initier la définition d'une fonction crée un espace indépendant : on réédite donc le préambule
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f) # (Nom de variable légèrement modifié pour ne pas confondre avec l'environnement général du script)

        # Création des 2 listes dans lesquelles les notices de la base seront réparties
        oeuvres = []
        images = []
            
        # Notre fichier = 1 liste des notices, téléchargées et concaténées depuis Agorha
        # Placement du curseur sur cette liste principale
        for notice in data["train"]: 

            # Choix de la liste de destination pour chaque notice en fonction des critères suivants:

            # Si la notice comprend un bloc Matérialité : c'est une Image
            if "content" in notice and "descriptionInformation" in notice["content"] and "materiality" in notice["content"]["descriptionInformation"]:

                # Sauf si elle comporte **aussi** un bloc Imprimé/Manuscrit : c'est une Oeuvre
                if "content" in notice and "manuscriptPrintedInformation" in notice["content"]:

                    # Sauf, encore, si son titre mentionne un feuillet, ou "Pelliot", ou un "Mexicain" ; auquel cas, c'est de nouveau une Image
                    if "internal" in notice and "digest" in notice["internal"] and "displayLabelLink" in notice["internal"]["digest"]:
                        title = notice["internal"]["digest"]["displayLabelLink"]
                        regex_liste = ["( Mexicain )", "( Pelliot )", "( f\.)"]
                        if any(re.search(regex, title) for regex in regex_liste):
                            images.append(notice)
                        else:
                            oeuvres.append(notice)
                    else:
                        oeuvres.append(notice)
                else:
                    images.append(notice)
            else:
                oeuvres.append(notice)

    # Résultat souhaité: les 2 listes remplies de leurs notices respectives.            
    return oeuvres, images     

# Application de la fonction à l'environnement principal du script
Notices_Oeuvre, Notices_Image=art_notices_partition(main_data)

# Une fois que les notices ont rejoint leur groupe respectif : qu'en faire?
# Définition des valeurs à cibler au sein du JSON, ainsi que de leurs modalités d'extraction, selon le modèle de ressource concerné
# Ici, le modèle de ressource "Oeuvre"

# Chaque information extraite = 1 propriété du modèle de ressource Omeka S
# 1 modèle à plusieurs propriétés = 1 classe, en Python. Chaque classe comporte les fonctions nécessaires à la définition de ses propriétés.

# *********** Définition des propriétés du modèle de ressource suivant : Oeuvre ***********
# 1 unité documentaire (1 manuscrit, qu'il soit un recueil ou non, 1 polyptyque)

class Oeuvre:

    # De nouveau un préambule, puisque comme pour les fonctions, la définition de classe crée un nouvel espace propre
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

        #  Première fonction, obligatoire: déclaration de ce que l'on définira au sein de la classe
        # Ici : pour chaque instance de la classe, on définira chaque propriété, avec leurs valeurs, dans la fonction "extract_properties".
        # Propriétés du modèle de ressource "Oeuvre" dans Omeka S : titre, Item type, titre alternatif, cote/n° d'inventaire, lieu de conservation, coordonnées du lieu de conservation, période de création (nom courant), période de création (dates chiffrées), période de création (nom propre), lieu de création (nom), lieu de création (coordonnées), créateur, contributeur, inspirations, langue(s), conditionnement, Couches matérielles de support, état de conservation, restauration(s), date de restauration, notices externes, Images contenues dans l'oeuvre, numérisation, ark
        def __init__(self, data):
            self.title, self.item_type, self.alternate_title, self.inv_cote, self.localization, self.coord_localization, self.period_name, self.period_chrono, self.period_surname, self.place_name, self.place_coord, self.creator, self.contributor, self.inspirations, self.languages, self.wrapping, self.support_layer, self.condition_state, self.restorations, self.restoration_date, self.sources, self.child_image, self.num_pictures, self.ark = self.extract_properties(data)
  
        def extract_properties(self, data):

            # Déclaration d'une liste de réception pour chaque variable de sortie  (colonnes du tableur CSV à venir)
       
                title = []
                item_type = []
                alternate_title = []
                inv_cote = []
                localization = []
                coord_localization = []
                period_name = []
                period_chrono = []
                period_surname = []
                place_name = []
                place_coord = []
                creator = []
                contributor = []
                inspirations = []
                languages = []
                wrapping = []
                support_layer = []
                condition_state = []
                restorations = [] 
                restoration_date = []
                sources = []
                num_pictures = []
                child_image = []
                ark = []

                # Extraction de l'ark dans le résumé ouvrant chaque fichier JSON ("internal")
                # (on procède par boucles "if-else", avec un "Null" systématique en cas d'absence de réponse. On part du principe que toute information peut s'avérer manquante, sans pour autant stopper l'exécution du script.)
                if "internal" in notice and "uuid" in notice["internal"]:
                    target_ark = notice["internal"]["uuid"]
                    # Ajout de la valeur au sein de la liste de réception
                    ark.append(target_ark)
                else:
                    ark.append("Null")    
                                   
                # Titre d'usage, Item type, Titre alternatif

                # Au départ, ces trois informations sont comprises dans un même bloc JSON, que l'on nommera le bloc "infos_id"
                if "content" in notice and "identificationInformation" in notice["content"] :
                    infos_id = notice["content"]["identificationInformation"]

                    # Récupération du titre 
                    if "title" in infos_id:

                        # Il peut également potentiellement figurer plusieurs titres principaux dans une notice (improbable, mais pas inévitable ; il est plus prudent de ne pas renseigner directement un numéro)
                        infos_title = infos_id["title"]

                        for info_title in infos_title:
                            # Récupération de la valeur textuelle du titre
                            if "label" in info_title and "value" in info_title["label"] :
                                        title1 = info_title["label"]["value"]
                                        title.append(title1)
                            
                            # Si un titre alternatif est renseigné en Commentaire Titre  
                            if "comment" in info_title:
                                alt_beta = info_title["comment"]
                                # Suppression des balises HTML de ce potentiel titre alternatif   
                                # On utilise une regex (= formule de sélection de caractères au sein d'une chaîne de caractères) pour sélectionner tout texte compris entre les caractères '>' (fin de balise HTML ouvrante) et '</' (balise HTML fermante) - sous réserve que ce texte ne soit lui-même pas une balise.
                                regex_alt = r">([^<]+)</[\w]+>"
                                match_alt = re.search(regex_alt, alt_beta)
                                if match_alt:
                                    # C'est ce texte sélectionné qu'on ajoutera, comme valeur, à la liste de réception "Titre alternatif"
                                    alternative_title = match_alt.group(1)
                                    alternate_title.append(alternative_title)
                                else:
                                    alternative_title = ""
                                    alternate_title.append(alternative_title)
                            else:
                                alternate_title.append("Null")     

                    # S'il n'y a pas de titre d'usage renseigné là : chercher celui dans le résumé de la notice Agorha
                    elif "internal" in notice and "digest" in notice["internal"] and "title" in notice["internal"]["digest"] :
                        title2 = notice["internal"]["digest"]["title"]
                        title.append(title2)
                    # S'il devait encore ne pas y en avoir, sélectionner ce qui est affiché par défaut comme étiquette dans Agorha    
                    elif "internal" in notice and "digest" in notice["internal"] and "displayLabelLink" in notice["internal"]["digest"]:
                        title3 = notice["internal"]["digest"]["displayLabelLink"]
                        title.append(title3)    
                   # Sinon, admettre que l'on aura pas de titre de tout.
                    else :
                        title.append("Null")

                    # Sélection du tyoe d'oeuvre: item type
                    if "type" in infos_id and "thesaurus" in infos_id["type"]:
                        infos_type = infos_id["type"]["thesaurus"]
                        # Il y en a souvent plusieurs ; les sélectionner tous
                        for info_type in infos_type:
                            if "prefLabels" in info_type and "value" in info_type["prefLabels"][0]:
                                        type = info_type["prefLabels"][0]["value"]
                                        item_type.append(type)
                            else:
                                item_type.append("Null")            
                    else:
                        item_type.append("Null")      

                # Cote | n° inventaire (renseignée directement dans le résumé de chaque notice JSON)
                if "internal" in notice and "digest" in notice["internal"] and "shelfMark" in notice["internal"]["digest"]:
                    nb_inv = notice["internal"]["digest"]["shelfMark"]
                    inv_cote.append(nb_inv)

                else:
                    inv_cote.append("Null")    

                
                # Recherche du lieu de conservation et ses coordonnées géographiques

                #  Ciblage du bloc "localization" commun à ces deux informations:
                if "content" in notice and "localizationInformation" in notice["content"] and "localization" in notice["content"]["localizationInformation"] :
                    infos_loc = notice["content"]["localizationInformation"]["localization"]

                    for locs in infos_loc:
                        # Lieu de conservation principal
                        if "place" in locs and "thesaurus" in locs["place"] and "prefLabels" in locs["place"]["thesaurus"] :
                            target_loc = locs["place"]["thesaurus"]["prefLabels"]
                            if "value" in target_loc:
                                loc = target_loc["value"]
                                localization.append(loc)

                            # Lieu de conservation secondaire (si un dépôt renseigné, par exemple) - sans ses balises HTML   
                            if "place" in locs and "comment" in locs["place"]:
                                loc2_beta = locs["place"]["comment"]
                                regex_loc = r">([^<]+)</[\w]+>"
                                match_loc = re.search(regex_loc, loc2_beta)
                                if match_loc:
                                    loc2 = match_loc.group(1)
                                    # S'il y en a un, il est ajouté à la liste de réception du lieu de conservation ; s'il n'y en a pas, cette instruction sera négligée.
                                    # On ne crée pas de liste de réception propre, au vu de la rareté des lieux de conservation secondaires
                                    localization.append(loc2)
                                else:
                                    pass
                        # ... Dans le cas où un seul lieu de conservation, serait renseigné en commentaire, mais **pas** en valeur principale
                        elif "place" in locs and "comment" in locs["place"]:
                            loc2_beta = locs["place"]["comment"]
                            regex_loc = r">([^<]+)</[\w]+>"
                            match_loc = re.search(regex_loc, loc2_beta)
                            if match_loc:
                                loc2 = match_loc.group(1)
                                localization.append(loc2)
                            else:
                                pass        
                        else:
                            localization.append("Null")

                        # Coordonnées du lieu de conservation principal (celles du secondaire ne sont pas renseignées)
                        if "place" in locs and "thesaurus" in locs["place"] and "geoPoint" in locs["place"]["thesaurus"]:
                            coord = locs["place"]["thesaurus"]["geoPoint"]
                            coord_localization.append(coord)
                        else:
                            coord_localization.append("Null") 
                  
                # Dans le cas où l'on a pas de bloc "localization" 
                #  Lieu de conservation comme coordonnées seront nuls par défaut.
                else:
                    localization.append("Null")
                    coord_localization.append("Null")                     


                # Créateur, Contributeur, Inspirations

                # Définition au préalable de ces différentes catégories de **rôle dans la création de l'oeuvre**, à partir des rôles renseignés dans le thesaurus Agorha.
                # L'objectif est de distinguer grossièrement les différents types de contribution, afin de mettre en valeur les créateurs directement identifiés / les circulations des esthétiques, dans un futur proche.
                # Il est préférable toutefois de limiter le nombre de catégories, puisque chacune requiert une liste d'arrivée.
                cat_creator = ["de", "collaboration", "associé à", "attribué à", "anciennement attribué à"]
                cat_contributor = ["achevé par", "commencé par", "copié par", "édité par", "gravé par", "dessiné par", "peint par", "atelier de", "inventé par", "restauré par", "retouché par"]
                cat_inspirations = ["cercle de", "école de", "entourage de", "lié à", "près de", "proche de", "suite de", "copié d'après", "d'après", "inspiré par", "genre de", "comparé à", "manière de"]                        

                # Bloc contenant l'ensemble des ***informations relatives à la création de l'oeuvre*** (auteur, date, lieu) dans le JSON
                if "content" in notice and "creationInformation" in notice["content"] and "creation" in notice["content"]["creationInformation"] :
                    infos_creation = notice["content"]["creationInformation"]["creation"]

                    for info in infos_creation :

                        # Ciblage de la valeur du nom de personne (ou personne morale) considérée comme auteur
                        # L'indication d'un auteur impliquera ici toujours la présence d'un bloc "person"
                        if "person" in info and "value" in info["person"]:
                            auteur = info["person"]["value"]

                        elif "person" in info and "conceptPath" in info["person"]:
                            # Parfois l'auteur est renseigné uniquement à partir du **chemin d'accès thesaurus** (ex: Raban Maur) ; il convient donc de sélectionner son nom seul, sans les éléments relatifs au thesaurus
                            auteur_beta = info["person"]["conceptPath"]
                            # On sélectionne toute chaîne de caractères après un '/' et commençant par une majuscule
                            regex_auteur = r'\/([A-Z].*?)"'
                            match_auteur = re.search(regex_auteur, auteur_beta)
                            if match_auteur:
                                auteur = match_auteur.group(1)

                        # Si l'auteur n'est renseigné qu'en commentaire, puisque incertain, ou anonyme
                        elif "person" in info and "comment" in info["person"]:
                            no_name_beta = info["person"]["comment"]
                            regex_auteur2 = r">([^<]+)</[\w]+>"
                            match2_auteur = re.search(regex_auteur2, no_name_beta)
                            if match2_auteur:
                                auteur = match2_auteur.group(1)
                                # Parfois, néanmoins, le commentaire renseigne une valeur, mais qui ne contient que des **balises HTML vides.** On instruit donc au script de la négliger
                                if auteur == "":
                                   pass

                            # On vérifie dans **quelle catégorie** le rôle assigné à cette personne se trouve
                            if "personRole" in info and "thesaurus" in info["personRole"]:
                                roles = info["personRole"]["thesaurus"]
                                for each_role in roles :
                                    if "prefLabels" in each_role and "value" in each_role["prefLabels"][0]:
                                        role = each_role["prefLabels"][0]["value"]
                                        
                                        # Si toutefois notre partition devait manquer des cas de figure, ou des anonymes: placement automatique dans la catégorie "créateur"
                                        if role not in cat_creator and cat_contributor and cat_inspirations:
                                            creator.append(auteur)

                                        # Ajout dans la catégorie "créateur" si le rôle de la personne est dans la liste cat_creator
                                        if role in cat_creator:
                                            creator.append(auteur)
                                        # Si au terme de l'opération la liste de réception est vide: ajouter "Null"
                                        if role not in cat_creator and len(creator) == 0:
                                            creator.append("Null")

                                        # Ajout dans la catégorie "contributeur" si le rôle est dans la liste cat_contributor
                                        if role in cat_contributor:
                                            contributor.append(auteur)
                                        # Si au terme de l'opération la liste de réception est vide: ajouter "Null"
                                        if role not in cat_contributor and len(contributor) == 0:
                                            contributor.append("Null") 

                                        # Ajout dans la catégorie "inspirations" si le rôle est dans la liste cat_inspirations
                                        if role in cat_inspirations:
                                            inspirations.append(auteur)
                                        # Si au terme de l'opération la liste de réception est vide: ajouter "Null"
                                        if role not in cat_inspirations and len(inspirations) == 0:
                                            inspirations.append("Null")
                                        else:
                                            pass    
                        # Si aucun bloc "person" n'est détaillé: "Null" par défaut
                        else:
                            creator.append("Null")    
                            contributor.append("Null")
                            inspirations.append("Null")

                        # Pour une raison que je suis bien en peine d'expliquer, on a toutefois encore des listes vides en résultat. Ce qui ne **devrait pas** arriver. Si tel est encore le cas, on y implémente la valeur "Null" artificiellement.
                        if creator == []:
                            creator = ["Null"]
                        if contributor == []:
                            contributor = ["Null"]
                        if inspirations == []:
                            inspirations = ["Null"]
                        # Si ce n'est pas le cas, négliger cette instruction.
                        else:
                            pass    

                        # Période de création : dates (en lettres, comme "8e siècle-2e moitié du 10e siècle")
                                
                        if "date" in info and "start" in info["date"] and "siecle" in info["date"]["start"] and "thesaurus" in info["date"]["start"]["siecle"] and "prefLabels" in info["date"]["start"]["siecle"]["thesaurus"] and "value" in info["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]:
                            # Sélection de la date de début (parfois unique, si la notice se contente d'un "1re moitié 11e siècle", par exemple)
                            begin = info["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                            if "end" in info["date"] and "siecle" in info["date"]["end"] and "thesaurus" in info["date"]["end"]["siecle"] and "prefLabels" in info["date"]["end"]["siecle"]["thesaurus"] and "value" in info["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]:
                                # Sélection de la date de fin, le cas échéant
                                end = info["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                                # Concaténation des deux expressions, afin qu'elles soient affichées au sein d'une même valeur
                                once_upon_a_time = begin + " - " + end
                            
                            # S'il n'y a pas de valeur de fin renseignée (l'expression se limite à "12e siècle", par exemple)
                            else: 
                                once_upon_a_time = begin
                            period_name.append(once_upon_a_time)
                        else:
                            period_name.append("Null")      
                                

                        # Période de création : bornes chronologiques numériques

                        # La difficulté ici est que les chiffres peuvent être renseignés de diverses manières ; et puisqu'ils renseignent la même information, il est prévu de les implémenter au sein de la même liste de réception. 
                        chrono = []
                        if "date" in info and "startDateComputed" in info["date"]:
                            debut = info["date"]["startDateComputed"]
                            chrono.append(debut)
                            if "endDateComputed" in info["date"]:
                                fin = info["date"]["endDateComputed"]
                                chrono.append(fin)
                            else:
                                pass    
                            period_chrono.append(chrono)

                        elif "date" in info and "start" in info["date"] and "earliest" in info["date"]["start"] and "date" in info["date"]["start"]["earliest"]:
                            debut2 = info["date"]["start"]["earliest"]["date"]
                            chrono.append(debut2)
                            if "latest" in info["date"]["start"] and "date" in info["date"]["start"]["latest"]:
                                debut3 = info["date"]["start"]["latest"]["date"]
                                chrono.append(debut3)
                            else:
                                pass    
                            if "end" in info["date"] and "earliest" in info["date"]["end"] and "date" in info["date"]["end"]["earliest"]:
                                fin2 = info["date"]["end"]["earliest"]["date"]
                                chrono.append(fin2)
                            else:
                                pass
                            if "end" in info["date"] and "latest" in info["date"]["end"] and "date" in info["date"]["end"]["latest"]:
                                fin3 = info["date"]["end"]["latest"]["date"]
                                chrono.append(fin3)    
                            else:
                                pass
                            period_chrono.append(chrono)    
                        else:
                            period_chrono.append("Null")

                        # Période de création : chrononyme ( comme "Antiquité tardive") - qui peuvent être entrés comme termes de recherche par les utilisateurs potentiels de la base d'exploitation
                        
                        if "period" in info and "thesaurus" in info["period"]:
                            chrononyms = info["period"]["thesaurus"]
                            for each_chrononym in chrononyms:
                                if "prefLabels" in each_chrononym  and "value" in each_chrononym["prefLabels"][0] :
                                    chrononym = info["period"]["thesaurus"][0]["prefLabels"][0]["value"]
                                    period_surname.append(chrononym)
                                else: pass    
                        else:
                            period_surname.append("Null")

                        # Lieu(x) de création : nom(s)
                        if "place" in info and "thesaurus" in info["place"]:
                            places = info["place"]["thesaurus"]
                            for place in places:
                                if "prefLabels" in place and "value" in place["prefLabels"][0]:
                                    name = place["prefLabels"][0]["value"]
                                    place_name.append(name)

                                    # Comme pour le lieu de conservation, un commentaire peut également renseigner des choses utiles (sélectionné hors de ses balises HTML)
                                    if "place" in info and "comment" in info["place"]:
                                        place2_beta =  info["place"]["comment"]
                                        regex_place = r">([^<]+)</[\w]+>"
                                        match_place = re.search(regex_place, place2_beta)
                                        if match_place:
                                            place2 = match_place.group(1)
                                            place_name.append(place2)
                                        else:
                                            pass
                                    else:
                                        pass    

                                # Coordonnées géographiques
                                if "geoPoint" in place:
                                    target_coord = place["geoPoint"]
                                    place_coord.append(target_coord)
                                else:
                                    place_coord.append("Null")   

                        # Sait-on jamais qu'il y aurait encore un commentaire tout seul...
                        elif "place" in info and "comment" in info["place"]:
                            place2_beta =  info["place"]["comment"]
                            regex_place = r">([^<]+)</[\w]+>"
                            match_place = re.search(regex_place, place2_beta)
                            if match_place:
                                place2 = match_place.group(1)
                                place_name.append(place2)
                            else:
                                pass
                        else:
                            place_name.append("Null")
                            place_coord.append("Null")         
                
                # Et si aucun bloc "infos création" n'est détaillé:
                else:
                    creator.append("Null")
                    contributor.append("Null")
                    inspirations.append("Null")
                    period_name.append("Null")
                    period_chrono.append("Null")
                    period_surname.append("Null")
                    place_name.append("Null")
                    place_coord.append("Null")                                               
                    
                    # Il conviendrait ici de modifier les choses en intégrant les préfixes - "Vers, Avant" - en vue d'adapter les visualisations. Mais un "Avant" ne modifie pas la valeur de la date; il requiert simplement d'être signalé, et simplement signaler une valeur ne va pas de soi. Faut-il ajouter une propriété, qui ne s'afficherait pas dans l'interface utilisateur d'Omeka S?

                # Langue(s) : (une Oeuvre de type "manuscrit" renseigne fréquemment une langue. Un polyptyque peut toujours comporter des inscriptions, bien que cela concerne plutôt chaque panneau au singulier)

                if "content" in notice and "manuscriptPrintedInformation" in notice["content"] and "bookContent" in notice["content"]["manuscriptPrintedInformation"] :
                    infos_text = notice["content"]["manuscriptPrintedInformation"]["bookContent"]
                    for info_text in infos_text:
                        if "language" in info_text and "thesaurus" in info_text["language"]:
                            langs = info_text["language"]["thesaurus"]
                            for lang in langs:
                                if "prefLabels" in lang and "value" in lang["prefLabels"][0]:
                                    language = lang["prefLabels"][0]["value"]
                                    languages.append(language)
                                else:
                                    languages.append("Null")    
                        else:
                            languages.append("Null")    
                else:
                    languages.append("Null")   

                # Reliure, cadre - et lien vers d'éventuelles Couches Support

                # On cible le Commentaire associé à la date de création - sans ses balises HTML
                if "content" in notice and "creationInformation" in notice["content"] and "creation" in notice["content"]["creationInformation"]:
                    infos_creation = notice["content"]["creationInformation"]["creation"]
                    for info in infos_creation:
                        if "date" in info and "comment" in info["date"] :
                            wrap_beta = info["date"]["comment"]
                            regex_wrap = r">([^<]+)</[\w]+>"
                            match_wrap = re.search(regex_wrap, wrap_beta)
                            if match_wrap:
                                wrap = match_wrap.group(1)
                                wrapping.append(wrap)
                            else:
                                wrap = "Null"
                                wrapping.append(wrap)
                        else:
                            wrapping.append("Null")        
                
                # Parfois, des notices Oeuvre comportent des blocs Matérialité (cf fonction de répartition). On traitera ces derniers comme des Couches, et on les reliera à leur objet parent (ici l'Oeuvre, donc) à cet emplacement:
                if "content" in notice and "descriptionInformation" in notice["content"] and "materiality" in notice["content"]["descriptionInformation"]:
                    support_layer.append("Layer Coming Here")
                else:
                    support_layer.append("Null")              

                # Etat de conservation :

                # Ciblage du bloc dédié à l'état de conservation dans JSON
                if "content" in notice and "descriptionInformation" in notice["content"] and "conservationState" in notice["content"]["descriptionInformation"] and "label" in notice["content"]["descriptionInformation"]["conservationState"] and "thesaurus" in notice["content"]["descriptionInformation"]["conservationState"]["label"]:
                    infos_conservation = notice["content"]["descriptionInformation"]["conservationState"]["label"]["thesaurus"]
                    for info_cv in infos_conservation:
                        if "prefLabels" in info_cv and "value" in info_cv["prefLabels"][0]:
                            statement = info_cv["prefLabels"][0]["value"]
                            condition_state.append(statement)
          
                # On intègre également tout commentaire fait à propos des restaurations, qui, lorsqu'aucun bloc "état de conservation" n'est détaillé, explique les opérations effectuées par l'état de conservation de l'oeuvre
                elif "content" in notice and "descriptionInformation" in notice["content"] and "restoration" in notice["content"]["descriptionInformation"]:
                    state_notes =  notice["content"]["descriptionInformation"]["restoration"]
                    for state_note in state_notes:
                        if "label" in state_note and "comment" in state_note["label"]:    
                            note_beta = notice["content"]["descriptionInformation"]["restoration"][0]["label"]["comment"]
                            regex_conservation = r">([^<]+)</[\w]+>"
                            match_conservation = re.search(regex_conservation, note_beta)
                            if match_conservation:
                                note = match_conservation.group(1)
                                condition_state.append(note)
                            else:
                                pass         
                        else:
                            condition_state.append("Null")    
                else:
                    condition_state.append("Null")      

                # Restaurations opérées
                        
                # Ciblage du bloc "restoration" dédié dans le JSON
                if "content" in notice and "descriptionInformation" in notice["content"] and "restoration" in notice["content"]["descriptionInformation"]:
                    infos_restoration = notice["content"]["descriptionInformation"]["restoration"]

                    for info_rs in infos_restoration:
                        if "label" in info_rs and "thesaurus" in info_rs["label"]:
                            operations = info_rs["label"]["thesaurus"]
                            for ope in operations:
                                if "prefLabels" in ope and "value" in ope["prefLabels"][0]:
                                    operation = ope["prefLabels"][0]["value"]   
                                    restorations.append(operation)
                        # C'est au niveau "label" qu'un commentaire portant sur les manipulations effectuées se trouve
                        elif "label" in info_rs and  "comment" in info_rs["label"]["comment"]:
                            operation2_beta = info_rs["label"]["comment"]
                            regex_restoration = r">([^<]+)</[\w]+>"
                            match_restoration = re.search(regex_restoration, operation2_beta)
                            if match_restoration:
                                operation2 = match_restoration.group(1)
                                restorations.append(operation2)
                            else:
                               pass
                        else: restorations.append("Null")

                        # Date de restauration

                        # Renseignée directement au sein du bloc Restoration du JSON, et posant le même souci de versatilité de la syntaxe employée
                        if "date" in info_rs and "startDateComputed" in info_rs["date"]:
                            begin2 = info_rs["date"]["startDateComputed"]
                            restoration_date.append(begin2)
                            if "date" in info_rs and "endDateComputed" in info_rs["date"]:
                                end2 = info_rs["date"]["endDateComputed"]
                                restoration_date.append(end2)
                            else:
                                pass    

                        elif "date" in info_rs and "start" in info_rs["date"] and "siecle" in info_rs["date"]["start"] and "thesaurus" in info_rs["date"]["start"]["siecle"] and "prefLabels" in info_rs["date"]["start"]["siecle"]["thesaurus"] and "value" in info_rs["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]:
                            begin = info_rs["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                            restoration_date.append(begin)
                            if "end" in info_rs["date"] and "siecle" in info_rs["date"]["end"] and "thesaurus" in info_rs["date"]["end"]["siecle"] and "prefLabels" in info_rs["date"]["end"]["siecle"]["thesaurus"] and "value" in info_rs["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]:
                                end = info_rs["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                                restoration_date.append(end)
                            else:
                                pass            

                        elif "date" in info_rs and "start" in info_rs["date"] and "earliest" in info_rs["date"]["start"] and "date" in info_rs["date"]["start"]["earliest"]:
                            begin3 = info_rs["date"]["start"]["earliest"]["date"]
                            restoration_date.append(begin3)
                            if "latest" in info_rs["date"]["start"] and "date" in info_rs["date"]["start"]["latest"]:
                                end3 = info_rs["date"]["start"]["latest"]["date"]
                                restoration_date.append(end3)
                            else:
                                pass    
                        else: 
                            restoration_date.append("Null")    

                        if "content" in notice and "identificationInformation" in notice["content"] and "note" in notice["content"]["identificationInformation"] and "generalNote" in notice["content"]["identificationInformation"]["note"][0] and "value" in notice["content"]["identificationInformation"]["note"][0]["generalNote"]:
                            restoration_comment_beta = notice["content"]["identificationInformation"]["note"][0]["generalNote"]["value"]
                            regex_restoration2 = r">([^<]+)</[\w]+>"
                            match_restoration2 = re.search(regex_restoration2, restoration_comment_beta)
                            if match_restoration2:
                                restoration_comment = match_restoration2.group(1)
                                restorations.append(restoration_comment)
                            else:
                                pass     
                # Et si aucun bloc Restoration n'est renseigné:
                else:
                    restorations.append("Null")
                    restoration_date.append("Null")

                # Notices externes

                # Les liens externes impliquant de remplir deux champs dans Omeka S - "URI" et "label" - il a été conseillé de les remplir plus tard, par Bulk Edit. On distinguera toutefois les notices qui renseignent des sources externes de celles qui ne le font pas.
                if "content" in notice and "referenceInformation" in notice["content"] and "onlineSource" in notice["content"]["referenceInformation"]:
                    sources.append("Sources Coming")
                else:
                    sources.append("Null")    
                        
                # Fichiers de numérisation

                #  L'essentiel des fichiers de numérisation se résume à une URL, pourvu que l'on indique celle du fichier le plus important ("original"). 
                some_num = []
                if "content" in notice and "mediaInformation" in notice["content"] and "prefPicture" in notice["content"]["mediaInformation"] and "thumbnail" in notice["content"]["mediaInformation"]["prefPicture"]:
                    little_num = notice["content"]["mediaInformation"]["prefPicture"]["thumbnail"]
                    if "thumbnail" in little_num:
                        big_num = little_num.replace("thumbnail", "original")
                    elif "default" in little_num:    
                        big_num = little_num.replace("default", "original")
                    else:
                        big_num = little_num
                    some_num.append(big_num)
                    num_pictures.append(some_num)
                else:
                    num_pictures.append("Null")

                # Liens vers Images  
                #  On peut pour l'instant se reposer sur un échange d'arks, en attendant de faire les jointures avec les ID de notices Omeka S depuis le logiciel d'installation d'Omeka S (Laragon)    
                if "content" in notice and "artworkLinkInformation" in notice["content"] and "artworkLink" in notice["content"]["artworkLinkInformation"]:
                    internal_links = notice["content"]["artworkLinkInformation"]["artworkLink"]
                    for internal_link in internal_links:
                        if "verticalType" in internal_link and "artwork" in internal_link and "ref" in internal_link["artwork"]:
                            child_ark = internal_link["artwork"]["ref"]
                            child_image.append(child_ark)
                        else:
                            child_image.append("Null")
                else:
                    child_image.append("Null")
            
                # Résultat souhaité : toutes les listes de réception garnies de leurs valeurs, ou d'une valeur "Null", dans l'ordre correspondant à celui des Propriétés associées dans leur modèle de ressource Omeka S
                return title, item_type, alternate_title, inv_cote, localization, coord_localization, period_name, period_chrono, period_surname, place_name, place_coord, creator, contributor, inspirations, languages, wrapping, support_layer, condition_state, restorations, restoration_date, sources, child_image, num_pictures, ark                

# Instancier la classe Oeuvre : **implémenter dans le script** définissant la classe tous les éléments de la liste d'arrivée "Oeuvres" de notre ***fonction de tri***

# On remarque, avec l'indentation portée à gauche, que l'on quitte l'espace de code de la Classe pour rejoindre l'espace principal

oeuvre_instances = []
for notice in Notices_Oeuvre: # C'est ici que le script de définition de classe retient que tout élément de la liste de dictionnaires JSON - la liste de notices - se nomme "notice" (variable principale sur les définitions de classe Image et Oeuvre)
    # A chaque notice est donc attribuée individuellement la classe "Oeuvre"
    instance1 = Oeuvre(notice)

    # C'est dans une ***dernière liste*** que l'on retrouvera la totalité des notices qui passeront donc par le script "class: Oeuvre"
    # Elle se distingue de "Notices_Oeuvre" en ce que cette dernière regroupe simplement des JSON ; "oeuvre_instances" concerne les notices qui sont **passées à travers le script de définition** des propriétés Omeka S.

    # Elle est nécessaire du fait qu'***une classe n'est pas itérable*** : on ne peut pas directement parcourir la classe comme on parcourt une liste, pour y donner des instructions collectives.
    oeuvre_instances.append(instance1)

    # On crée un tableur CSV à partir des résultats générés par le script de définition de classe "Oeuvre":

# Ouverture d'un nouveau document de type CSV, en utf-8, et en mode écriture (ce qui revient à en créer un ex nihilo, pour lui imposer l'intégralité de son contenu)
with open('oeuvres89.csv', 'w', newline='', encoding='utf-8') as csvfile:

# Son nom est à permuter avec 'oeuvres88.csv' tant que je n'ai pas conçu la meta-fonction du siècle susceptible de créer les deux en même temps

    # Défintion du nom des colonnes, qui n'est pas celui des listes de réception, mais des propriétés des différents schémas que nous utiliserons dans Omeka S à l'arrivée, lors de l'import automatique du tableur.
    column_names_oeuvres = ["dcterms:title", "cld:itemType", "dcterms:alternative", "dcterms:identifier", "cld:isLocatedAt", "schema:geo", "dcterms:temporal", "dcterms:created", "cld:dateItemsCreated", "schema:locationCreated", "dcterms:spatial", "dcterms:creator", "dcterms:contributor", "crm:P15_was_influenced_by", "dcterms:language", "schema:artworkSurface", "crm:P106_is_composed_of", "schema:itemCondition", "crm:P31i_was_modified_by", "dcterms:modified", "dcterms:source", "dcterms:hasPart", "dcterms:hasVersion", "dcterms:isReferencedBy"]

    # On écrit le tableur en donnant à chaque colonne nommée le contenu d'une liste de réception
    writer = csv.DictWriter(csvfile, fieldnames=column_names_oeuvres)
    writer.writeheader()

    # Chaque notice de la classe représente 1 ligne du tableur.
    for oeuvre in oeuvre_instances:
        writer.writerow({
            "dcterms:title": oeuvre.title,                  
            "cld:itemType": oeuvre.item_type, 
            "dcterms:alternative": oeuvre.alternate_title, 
            "dcterms:identifier": oeuvre.inv_cote, 
            "cld:isLocatedAt": oeuvre.localization,
            "schema:geo": oeuvre.coord_localization,
            "dcterms:temporal": oeuvre.period_name,
            "dcterms:created": oeuvre.period_chrono,
            "cld:dateItemsCreated": oeuvre.period_surname,
            "schema:locationCreated": oeuvre.place_name,
            "dcterms:spatial": oeuvre.place_coord,
            "dcterms:creator": oeuvre.creator,
            "dcterms:contributor": oeuvre.contributor,
            "crm:P15_was_influenced_by": oeuvre.inspirations,
            "dcterms:language": oeuvre.languages,
            "schema:artworkSurface": oeuvre.wrapping,
            "crm:P106_is_composed_of": oeuvre.support_layer,
            "schema:itemCondition": oeuvre.condition_state,
            "crm:P31i_was_modified_by": oeuvre.restorations,
            "dcterms:modified": oeuvre.restoration_date,
            "dcterms:source": oeuvre.sources,
            "dcterms:hasPart": oeuvre.child_image,
            "dcterms:hasVersion": oeuvre.num_pictures,
            "dcterms:isReferencedBy": oeuvre.ark 
        })    

# *********** Définition des propriétés du modèle de ressource suivant : Image ***********
# (1 unité picturale au sein d'une Oeuvre ; ou auto-suffisante)

# Le procédé est exactement le même que précédemment, à l'exception de l'ajout de la propriété "Subject" (sujet de l'Image), de la limitation du conditionnement renseigné aux Couches Support liées, et de la mention d'une Oeuvre comme objet parent.

class Image:  

    # Nouvel espace indépendant, nouveau prémabule
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
        # Définition des propriétés du modèle de ressource "Image": titre, Item type, titre alternatif, cote/n° d'inventaire, lieu de conservation, coordonnées du lieu de conservation, période de création (nom courant), période de création (dates chiffrées), période de création (nom propre), lieu de création (nom), lieu de création (coordonnées), créateur, contributeur, inspirations, langue(s), sujet(s), notice mère (Oeuvre), motifs iconographiques présentés, couches matérielles de support, Image présente au sein de la même Oeuvre, état de conservation, restauration(s), date de restauration, notices externes, numérisation, ark
        def __init__(self, data):
            self.title, self.item_type, self.alternate_title, self.inv_cote, self.localization, self.coord_localization, self.period_name, self.period_chrono, self.period_surname, self.place_name,  self.place_coord, self.creator, self.contributor, self.inspirations, self.languages, self.subject, self.parent_image, self.child_pattern, self.support_layer, self.sibling_image, self.condition_state, self.restorations, self.restoration_date, self.sources, self.num_pictures, self.ark = self.extract_properties(data)

        def extract_properties(self, data):
                
            # Valeurs de sortie - colonnes CSV
               
                title = []
                item_type = [] 
                alternate_title = [] 
                inv_cote = [] 
                localization  = [] 
                coord_localization = [] 
                period_name  = [] 
                period_chrono = [] 
                period_surname = [] 
                place_name = []
                place_coord = [] 
                creator = [] 
                contributor = [] 
                inspirations  = [] 
                languages = [] 
                subject  = [] 
                parent_image = [] 
                child_patterns = [] 
                support_layer = [] 
                sibling_image = [] 
                condition_state = [] 
                restorations = [] 
                restoration_date = [] 
                sources = [] 
                num_pictures = [] 
                ark = []

                # ark donc
                if "internal" in notice and "uuid" in notice["internal"]:
                    target_ark = notice["internal"]["uuid"]
                    ark.append(target_ark)
                        
                # Titre d'usage, Item type, Titre alternatif

                    if "content" in notice and "identificationInformation" in notice["content"] :
                        infos_id = notice["content"]["identificationInformation"]

                        if "title" in infos_id:

                            infos_title = infos_id["title"]

                            for info_title in infos_title:

                                if "label" in info_title and "value" in info_title["label"] :
                                    title1 = info_title["label"]["value"]
                                    title.append(title1)
                                  
                                if "comment" in info_title:
                                    alt_beta = info_title["comment"]
                                       
                                    regex_alt = r">([^<]+)</[\w]+>"
                                    match_alt = re.search(regex_alt, alt_beta)
                                    if match_alt:
                                        alternate = match_alt.group(1)
                                        alternate_title.append(alternate)
                                    else:
                                        alternate = ""
                                        alternate_title.append(alternate)
                                else:
                                    alternate_title.append("Null")     

                        elif "internal" in notice and "digest" in notice["internal"] and "title" in notice["internal"]["digest"] :
                            title2 = notice["internal"]["digest"]["title"]
                            title.append(title2)
   
                        elif "internal" in notice and "digest" in notice["internal"] and "displayLabelLink" in notice["internal"]["digest"]:
                            title3 = notice["internal"]["digest"]["displayLabelLink"]
                            title.append(title3)    
                        else :
                            title.append("Null")

                    # Sélection de l'item type : "type d'oeuvre" dans Agorha
                        if "type" in infos_id and "thesaurus" in infos_id["type"]:

                            infos_type = infos_id["type"]["thesaurus"]
                            for info_type in infos_type:
                                if "prefLabels" in info_type and "value" in info_type["prefLabels"][0]:
                                            type = info_type["prefLabels"][0]["value"]
                                            item_type.append(type)
                                else:
                                    item_type.append("Null")            
                        else:
                                item_type.append("Null")          

                # Cote | n° inventaire
                if "internal" in notice and "digest" in notice["internal"] and "shelfMark" in notice["internal"]["digest"]:
                    nb_inv = notice["internal"]["digest"]["shelfMark"]
                    inv_cote.append(nb_inv)

                else:
                    inv_cote.append("Null")    

                # Lieu de conservation et ses coordonnées géographiques

                if "content" in notice and "localizationInformation" in notice["content"] and "localization" in notice["content"]["localizationInformation"] :
                    infos_loc = notice["content"]["localizationInformation"]["localization"]

                    for locs in infos_loc:
                        # Lieu de conservation principal
                        if "place" in locs and "thesaurus" in locs["place"] and "prefLabels" in locs["place"]["thesaurus"] :
                            target_loc = locs["place"]["thesaurus"]["prefLabels"]
                            if "value" in target_loc:
                                loc = target_loc["value"]
                                localization.append(loc)          
                        # Lieu de conservation secondaire (si dépôt renseigné, par exemple), sans ses balises HTML   
                        if "place" in locs and "comment" in locs["place"]:
                            loc2_beta = locs["place"]["comment"]
                            regex_loc = r">([^<]+)</[\w]+>"
                            match_loc = re.search(regex_loc, loc2_beta)
                            if match_loc:
                                loc2 = match_loc.group(1)
                                localization.append(loc2)
                            else:
                                loc2 = ""
                                localization.append(loc2)   
                        else:
                            localization.append("Null")

                        # Coordonnées du lieu de conservation principal
                        if "place" in locs and "thesaurus" in locs["place"] and "geoPoint" in locs["place"]["thesaurus"]:
                            coord = locs["place"]["thesaurus"]["geoPoint"]
                            coord_localization.append(coord)
                        else:
                            coord_localization.append("Null") 
                  
                else:
                    localization.append("Null")
                    coord_localization.append("Null")


                # Informations descriptives relatives à la création de l'oeuvre

                # Créateur, Contributeur, Inspirations

                cat_creator = ["de", "collaboration", "associé à", "attribué à", "anciennement attribué à"]
                cat_contributor = ["achevé par", "commencé par", "copié par", "édité par", "gravé par", "dessiné par", "peint par", "atelier de", "inventé par", "restauré par", "retouché par"]
                cat_inspirations = ["cercle de", "école de", "entourage de", "lié à", "près de", "proche de", "suite de", "copié d'après", "d'après", "inspiré par", "genre de", "comparé à", "manière de"]                        

                if "content" in notice and "creationInformation" in notice["content"] and "creation" in notice["content"]["creationInformation"] :
                    infos_creation = notice["content"]["creationInformation"]["creation"]

                    for info in infos_creation :

                        # Ciblage de la valeur du nom de personne (ou personne morale)
                        if "person" in info and "value" in info["person"]:
                            auteur = info["person"]["value"]
                        elif "person" in info and "conceptPath" in info["person"]:
                            auteur_beta = info["person"]["conceptPath"]
                            regex_auteur = r'\/([A-Z].*?)"'
                            match_auteur = re.search(regex_auteur, auteur_beta)
                            if match_auteur:
                                auteur = match_auteur.group(1)
                        elif "person" in info and "comment" in info["person"]:
                            no_name_beta = info["person"]["comment"]
                            regex_auteur2 = r">([^<]+)</[\w]+>"
                            match2_auteur = re.search(regex_auteur2, no_name_beta)
                            if match2_auteur:
                                auteur = match2_auteur.group(1)
                                if auteur == "":
                                   pass

                            # On vérifie dans quelle catégorie le rôle assigné à cette personne se trouve
                            if "personRole" in info and "thesaurus" in info["personRole"]:
                                roles = info["personRole"]["thesaurus"]
                                for each_role in roles :
                                    if "prefLabels" in each_role and "value" in each_role["prefLabels"][0]:
                                        role = each_role["prefLabels"][0]["value"]
                                        
                                        if role not in cat_creator and cat_contributor and cat_inspirations:
                                            creator.append(auteur)
                                        # Ajout dans la catégorie "créateur" si le rôle de la personne est dans la liste cat_creator
                                        if role in cat_creator:
                                            creator.append(auteur)
                                        if role not in cat_creator and len(creator) == 0:
                                            creator.append("Null")
                                        # Ajout dans la catégorie "contributeur" si le rôle est dans la liste cat_contributor
                                        if role in cat_contributor:
                                            contributor.append(auteur)
                                        if role not in cat_contributor and len(contributor) == 0:
                                            contributor.append("Null")  
                                        # Ajout dans la catégorie "inspirations" si le rôle est dans la liste cat_inspirations
                                        if role in cat_inspirations:
                                            inspirations.append(auteur)
                                        if role not in cat_inspirations and len(inspirations) == 0:
                                            inspirations.append("Null")
                                        else:
                                            pass    
                        else:
                            creator.append("Null")    
                            contributor.append("Null")
                            inspirations.append("Null")

                        if creator == []:
                            creator = ["Null"]
                        if contributor == []:
                            contributor = ["Null"]
                        if inspirations == []:
                            inspirations = ["Null"]
                        else:
                            pass                        

                        # Période de création : dates (en lettres, genre "8e siècle-2e moitié du 10e siècle")

                        if "date" in info and "start" in info["date"] and "siecle" in info["date"]["start"] and "thesaurus" in info["date"]["start"]["siecle"] and "prefLabels" in info["date"]["start"]["siecle"]["thesaurus"] and "value" in info["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]:

                            begin = info["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                            if "end" in info["date"] and "siecle" in info["date"]["end"] and "thesaurus" in info["date"]["end"]["siecle"] and "prefLabels" in info["date"]["end"]["siecle"]["thesaurus"] and "value" in info["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]:
                                end = info["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                                once_upon_a_time = begin + " - " + end
                            else: 
                                once_upon_a_time = begin
                            period_name.append(once_upon_a_time)
                        else:
                            period_name.append("Null")      
                                

                        # Période de création : bornes chronologiques numériques

                        chrono = []
                        if "date" in info and "startDateComputed" in info["date"]:
                            debut = info["date"]["startDateComputed"]
                            chrono.append(debut)
                            if "endDateComputed" in info["date"]:
                                fin = info["date"]["endDateComputed"]
                                chrono.append(fin)
                            else:
                                pass    
                            period_chrono.append(chrono)

                        elif "date" in info and "start" in info["date"] and "earliest" in info["date"]["start"] and "date" in info["date"]["start"]["earliest"]:
                            debut2 = info["date"]["start"]["earliest"]["date"]
                            chrono.append(debut2)
                            if "latest" in info["date"]["start"] and "date" in info["date"]["start"]["latest"]:
                                debut3 = info["date"]["start"]["latest"]["date"]
                                chrono.append(debut3)
                            else:
                                pass    
                            if "end" in info["date"] and "earliest" in info["date"]["end"] and "date" in info["date"]["end"]["earliest"]:
                                fin2 = info["date"]["end"]["earliest"]["date"]
                                chrono.append(fin2)
                            else:
                                pass
                            if "end" in info["date"] and "latest" in info["date"]["end"] and "date" in info["date"]["end"]["latest"]:
                                fin3 = info["date"]["end"]["latest"]["date"]
                                chrono.append(fin3)    
                            else:
                                pass
                            period_chrono.append(chrono)    
                        else:
                            period_chrono.append("Null")

                        # Période de création : chrononyme ( comme "Antiquité tardive")
                        
                        if "period" in info and "thesaurus" in info["period"]:
                            chrononyms = info["period"]["thesaurus"]
                            for each_chrononym in chrononyms:
                                if "prefLabels" in each_chrononym  and "value" in each_chrononym["prefLabels"][0] :
                                    chrononym = info["period"]["thesaurus"][0]["prefLabels"][0]["value"]
                                    period_surname.append(chrononym)
                                else: pass    
                        else:
                            period_surname.append("Null")


                        # Lieu(x) de création : nom(s)

                        if "place" in info and "thesaurus" in info["place"]:
                            places = info["place"]["thesaurus"]
                            for place in places:
                                if "prefLabels" in place and "value" in place["prefLabels"][0]:
                                    name = place["prefLabels"][0]["value"]
                                    place_name.append(name)
                                    if "place" in info and "comment" in info["place"]:
                                        place2_beta =  info["place"]["comment"]
                                        regex_place = r">([^<]+)</[\w]+>"
                                        match_place = re.search(regex_place, place2_beta)
                                        if match_place:
                                            place2 = match_place.group(1)
                                            place_name.append(place2)
                                        else:
                                            pass
                                    else:
                                        pass    

                                # Coordonnées géographiques
                                if "geoPoint" in place:
                                    target_coord = place["geoPoint"]
                                    place_coord.append(target_coord)
                                else:
                                    place_coord.append("Null")   

                        elif "place" in info and "comment" in info["place"]:
                            place2_beta =  info["place"]["comment"]
                            regex_place = r">([^<]+)</[\w]+>"
                            match_place = re.search(regex_place, place2_beta)
                            if match_place:
                                place2 = match_place.group(1)
                                place_name.append(place2)
                            else:
                                pass
                        else:
                            place_name.append("Null")
                            place_coord.append("Null")         
                else:
                    creator.append("Null")
                    contributor.append("Null")
                    inspirations.append("Null")
                    period_name.append("Null")
                    period_chrono.append("Null")
                    period_surname.append("Null")
                    place_name.append("Null")
                    place_coord.append("Null")

                # Sujet général de l'Image : indexation
                        
                # Cibler le bloc dédié - "subject" - dans le JSON
                if "content" in notice and "descriptionInformation" in notice["content"] and "subject" in notice["content"]["descriptionInformation"]:
                    subjects = notice["content"]["descriptionInformation"]["subject"]
                    for some_subject in subjects:
                        # Premier emplacement d'un sujet: dans le champ "legend"
                        if "legend" in some_subject and "value" in some_subject["legend"]:
                            main_subject = some_subject["legend"]["value"]
                            subject.append(main_subject)
                        else:
                            pass    
                        # Deuxième emplacement possible : champ "garnier"
                        if "garnier" in some_subject and "thesaurus" in some_subject["garnier"]:    
                            spec_subjects = some_subject["garnier"]["thesaurus"]
                            for spec_subject in spec_subjects:
                                if "prefLabels" in spec_subject and "value" in spec_subject["prefLabels"][0]:
                                    spec_subject_target = spec_subject["prefLabels"][0]["value"]
                                    subject.append(spec_subject_target)
                                else:
                                    pass
                        # Troisième emplacement possible : commentaire appliqué au Garnier
                        if "content" in notice and "manuscriptPrintedInformation" in notice["content"] and "printedSubject" in notice["content"]["manuscriptPrintedInformation"]:
                            other_subjects = notice["content"]["manuscriptPrintedInformation"]["printedSubject"]
                            for other_subject in other_subjects:
                                if "garnier" in other_subject and "comment" in other_subject["garnier"]:
                                    other_subject_target_beta = other_subject["garnier"]["comment"]
                                    # Sélection de la valeur textuelle sans les balises HTML    
                                    regex_subject = r">([^<]+)</[\w]+>"
                                    match_subject = re.search(regex_subject, other_subject_target_beta)
                                    if match_subject:
                                        other_subject_target = match_subject.group(1)
                                        subject.append(other_subject_target)
                                    else:
                                        pass

                # S'il n'y a qu'un commentaire Garnier (pour un terme non thesaurisé, par exemple) mais pas le reste:
                elif "content" in notice and "manuscriptPrintedInformation" in notice["content"] and "printedSubject" in notice["content"]["manuscriptPrintedInformation"]:
                    other_subjects1 = notice["content"]["manuscriptPrintedInformation"]["printedSubject"]
                    for other_subject1 in other_subjects1:
                        if "garnier" in other_subject1 and "comment" in other_subject1["garnier"]:
                            other_subject_target_beta1 = other_subject1["garnier"]["comment"]
                            # Sélection de la valeur textuelle sans les balises HTML    
                            regex_subject = r">([^<]+)</[\w]+>"
                            match_subject1 = re.search(regex_subject, other_subject_target_beta1)
                            if match_subject1:
                                other_subject_target1 = match_subject1.group(1)
                                subject.append(other_subject_target1)
                            else:
                                subject.append("Null")
                # Et s'il n'y a pas de bloc Subject du tout
                else:
                    subject.append("Null")    

                # Langue(s) :
                if "content" in notice and "manuscriptPrintedInformation" in notice["content"] and "bookContent" in notice["content"]["manuscriptPrintedInformation"] :
                    infos_text = notice["content"]["manuscriptPrintedInformation"]["bookContent"]
                    for info_text in infos_text:
                        if "language" in info_text and "thesaurus" in info_text["language"]:
                            langs = info_text["language"]["thesaurus"]
                            for lang in langs:
                                if "prefLabels" in lang and "value" in lang["prefLabels"][0]:
                                    language = lang["prefLabels"][0]["value"]
                                    languages.append(language)
                                else:
                                    languages.append("Null")    
                        else:
                            languages.append("Null")    
                else:
                    languages.append("Null")    

                # Etat de conservation :

                if "content" in notice and "descriptionInformation" in notice["content"] and "conservationState" in notice["content"]["descriptionInformation"] and "label" in notice["content"]["descriptionInformation"]["conservationState"] and "thesaurus" in notice["content"]["descriptionInformation"]["conservationState"]["label"]:
                    infos_conservation = notice["content"]["descriptionInformation"]["conservationState"]["label"]["thesaurus"]
                    for info_cv in infos_conservation:
                        if "prefLabels" in info_cv and "value" in info_cv["prefLabels"][0]:
                            statement = info_cv["prefLabels"][0]["value"]
                            condition_state.append(statement)
          
                elif "content" in notice and "descriptionInformation" in notice["content"] and "restoration" in notice["content"]["descriptionInformation"]:
                    state_notes =  notice["content"]["descriptionInformation"]["restoration"]
                    for state_note in state_notes:
                        if "label" in state_note and "comment" in state_note["label"]:    
                            note_beta = notice["content"]["descriptionInformation"]["restoration"][0]["label"]["comment"]
                            regex_conservation = r">([^<]+)</[\w]+>"
                            match_conservation = re.search(regex_conservation, note_beta)
                            if match_conservation:
                                note = match_conservation.group(1)
                                condition_state.append(note)
                            else:
                                pass         
                        else:
                            condition_state.append("Null")    
                else:
                    condition_state.append("Null")       

                # Restaurations opérées
                        
                if "content" in notice and "descriptionInformation" in notice["content"] and "restoration" in notice["content"]["descriptionInformation"]:
                    infos_restoration = notice["content"]["descriptionInformation"]["restoration"]

                    for info_rs in infos_restoration:
                        if "label" in info_rs and "thesaurus" in info_rs["label"]:
                            operations = info_rs["label"]["thesaurus"]
                            for ope in operations:
                                if "prefLabels" in ope and "value" in ope["prefLabels"][0]:
                                    operation = ope["prefLabels"][0]["value"]   
                                    restorations.append(operation)
                        elif "label" in info_rs and  "comment" in info_rs["label"]["comment"]:
                            operation2_beta = info_rs["label"]["comment"]
                            regex_restoration = r">([^<]+)</[\w]+>"
                            match_restoration = re.search(regex_restoration, operation2_beta)
                            if match_restoration:
                                operation2 = match_restoration.group(1)
                                restorations.append(operation2)
                            else:
                                operation2 = "Null"
                                restorations.append(operation2)
                        else: restorations.append("Null")

                        # Date de restauration

                        if "date" in info_rs and "startDateComputed" in info_rs["date"]:
                            begin2 = info_rs["date"]["startDateComputed"]
                            restoration_date.append(begin2)
                            if "date" in info_rs and "endDateComputed" in info_rs["date"]:
                                end2 = info_rs["date"]["endDateComputed"]
                                restoration_date.append(end2)
                            else:
                                pass    

                        elif "date" in info_rs and "start" in info_rs["date"] and "siecle" in info_rs["date"]["start"] and "thesaurus" in info_rs["date"]["start"]["siecle"] and "prefLabels" in info_rs["date"]["start"]["siecle"]["thesaurus"] and "value" in info_rs["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]:
                            begin = info_rs["date"]["start"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                            restoration_date.append(begin)
                            if "end" in info_rs["date"] and "siecle" in info_rs["date"]["end"] and "thesaurus" in info_rs["date"]["end"]["siecle"] and "prefLabels" in info_rs["date"]["end"]["siecle"]["thesaurus"] and "value" in info_rs["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]:
                                end = info_rs["date"]["end"]["siecle"]["thesaurus"]["prefLabels"][0]["value"]
                                restoration_date.append(end)
                            else:
                                pass            

                        elif "date" in info_rs and "start" in info_rs["date"] and "earliest" in info_rs["date"]["start"] and "date" in info_rs["date"]["start"]["earliest"]:
                            begin3 = info_rs["date"]["start"]["earliest"]["date"]
                            restoration_date.append(begin3)
                            if "latest" in info_rs["date"]["start"] and "date" in info_rs["date"]["start"]["latest"]:
                                end3 = info_rs["date"]["start"]["latest"]["date"]
                                restoration_date.append(end3)
                            else:
                                pass    
                        else: 
                            restoration_date.append("Null")    

                        if "content" in notice and "identificationInformation" in notice["content"] and "note" in notice["content"]["identificationInformation"] and "generalNote" in notice["content"]["identificationInformation"]["note"][0] and "value" in notice["content"]["identificationInformation"]["note"][0]["generalNote"]:
                            restoration_comment_beta = notice["content"]["identificationInformation"]["note"][0]["generalNote"]["value"]
                            regex_restoration2 = r">([^<]+)</[\w]+>"
                            match_restoration2 = re.search(regex_restoration2, restoration_comment_beta)
                            if match_restoration2:
                                restoration_comment = match_restoration2.group(1)
                                restorations.append(restoration_comment)
                            else:
                                restoration_comment = "Null"
                                restorations.append(restoration_comment)     
                else:
                    restorations.append("Null")
                    restoration_date.append("Null")

                # Fichiers de numérisation    
                some_num = []
                if "content" in notice and "mediaInformation" in notice["content"] and "prefPicture" in notice["content"]["mediaInformation"] and "thumbnail" in notice["content"]["mediaInformation"]["prefPicture"]:
                    little_num = notice["content"]["mediaInformation"]["prefPicture"]["thumbnail"]
                    if "thumbnail" in little_num:
                        big_num = little_num.replace("thumbnail", "original")
                    elif "default" in little_num:    
                        big_num = little_num.replace("default", "original")
                    else:
                        big_num = little_num
                    some_num.append(big_num)
                    num_pictures.append(some_num)
                else:
                    num_pictures.append("Null")    

                # Notices externes
                if "content" in notice and "referenceInformation" in notice["content"] and "onlineSource" in notice["content"]["referenceInformation"]:
                    sources.append("Sources Coming")
                else: 
                    sources.append("Null")    

                # Liens vers Oeuvre  
                #  Même principe que précédemment : renseigné l'ark de la notice liée, et le remplacer par l'ID Omeka S une fois que celui-ci sera créé  
                if "content" in notice and "artworkLinkInformation" in notice["content"] and "artworkLink" in notice["content"]["artworkLinkInformation"]:
                    internal_links = notice["content"]["artworkLinkInformation"]["artworkLink"]
                    for internal_link in internal_links:
                        if "verticalType" in internal_link and "artwork" in internal_link and "ref" in internal_link["artwork"]:
                            parent_ark = internal_link["artwork"]["ref"]
                            parent_image.append(parent_ark)
                        else:
                            parent_image.append("Null")
                else:
                    parent_image.append("Null")  

                # Liens vers Motifs
                child_patterns.append("Patterns Coming")

                # Liens vers Supports
                support_layer.append("Layers Coming")

                # Liens vers les autres Images comprises dans la même Oeuvre
                sibling_image.append("Siblings Coming")
                
                return title, item_type, alternate_title, inv_cote, localization, coord_localization, period_name, period_chrono, period_surname, place_name,  place_coord, creator, contributor, inspirations, languages, subject, parent_image, child_patterns, support_layer, sibling_image, condition_state, restorations, restoration_date, sources, num_pictures, ark

# Instancier la classe dans l'espace principal : attribuer la classe "Image" à chaque notice composant la liste "Notices_Image" résultant de notre fonction de tri
image_instances = []
for notice in Notices_Image:
    instance2 = Image(notice)
    image_instances.append(instance2)

# Création du fichier CSV pour l'import des notices de type Image

with open('images89.csv', 'w', newline='', encoding='utf-8') as csvfile:
# A permuter avec 'images88.csv' tant que je n'ai pas conçu la meta-fonction du siècle

    column_names_images = ["dcterms:title", "cld:itemType", "dcterms:alternative", "dcterms:identifier", "cld:isLocatedAt", "schema:geo", "dcterms:temporal", "dcterms:created", "cld:dateItemsCreated", "schema:locationCreated", "dcterms:spatial", "dcterms:creator", "dcterms:contributor", "crm:P15_was_influenced_by", "dcterms:language", "dcterms:subject", "dcterms:isPartOf", "dcterms:hasPart", "crm:P106_is_composed_of", "schema:itemCondition", "crm:P31i_was_modified_by", "dcterms:modified", "dcterms:source", "dcterms:hasVersion", "dcterms:isReferencedBy"]

    writer = csv.DictWriter(csvfile, fieldnames=column_names_images)
    writer.writeheader()

    for image in image_instances:
        writer.writerow({
            "dcterms:title": image.title,                   
            "cld:itemType": image.item_type, 
            "dcterms:alternative": image.alternate_title, 
            "dcterms:identifier": image.inv_cote, 
            "cld:isLocatedAt": image.localization,
            "schema:geo": image.coord_localization,
            "dcterms:temporal": image.period_name,
            "dcterms:created": image.period_chrono,
            "cld:dateItemsCreated": image.period_surname,
            "schema:locationCreated": image.place_name,
            "dcterms:spatial": image.place_coord,
            "dcterms:creator": image.creator,
            "dcterms:contributor": image.contributor,
            "crm:P15_was_influenced_by": image.inspirations,
            "dcterms:language": image.languages,
            "dcterms:subject": image.subject, 
            "dcterms:isPartOf": image.parent_image, 
            "dcterms:hasPart": image.child_pattern,
            "crm:P106_is_composed_of": image.support_layer,
            "schema:itemCondition": image.condition_state,
            "crm:P31i_was_modified_by": image.restorations,
            "dcterms:modified": image.restoration_date,
            "dcterms:source": image.sources,
            "dcterms:hasVersion": image.num_pictures,
            "dcterms:isReferencedBy": image.ark
            })

# ************** Modèle de ressource "Motif iconographique"**************

class Motif:

    # Nouvelle définition de classe, nouvel espace de code, nouveau préambule
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)    

        # Définition des propriétés du modèle de ressource "Motif iconographique": Item type, nom du motif, ID propre, couleur, localisation dans l'image, Image parente, autres Motifs présents au sein de cette Image, Couches matérielles composant le motif, notices externes
        def __init__(self, data): 
            self.item_type_pattern, self.pattern_name, self.pattern_id, self.pattern_color, self.pattern_localization, self.whole_image, self.sibling_patterns, self.material_layers, self.sources, = self.extract_properties(data)

        def extract_properties(self, data):

            pattern_name = [] # dcterms:subject
            pattern_localization = [] # schema:position
            pattern_color = [] # schema:color
            pattern_id = [] # dcterms:identifier
            item_type_pattern = ["Motif iconographique"] # cld:itemType # valeur par défaut
            sources = [] # dcterms:source
            whole_image = [] # dcterms:isPartOf
            sibling_patterns = [] # schema:isRelatedTo
            material_layers = [] # crm:P106_is_composed_of

            # Informations issues du Commentaire TDM : ID, emplacement, nom et couleur du motif 

            # Nom(s) du motif iconographique
            # Le nom du motif est renseigné dans le "Commentaire Type de Description Matérielle", théoriquement après les caractères "motif :" (dans les dernières corrections apportées à Agorha)

            # On utilise la variable "pattern" pour désigner tout Bloc Matérialité d'Agorha ; celle-ci est définie après la classe, avec les instances adéquates.

            if "descriptionType" in pattern and "comment" in pattern["descriptionType"]:
                com_tdm = pattern["descriptionType"]["comment"]
                # Nom du motif par regex: sélection de tout texte situé entre 'motif :' et un tiret - ou une balise fermante HTML - on une fin de ligne.
                pattern_nm = r"motif : (.*?)(?:-|<|$)"
                match1 = re.search(pattern_nm, com_tdm)
                if match1:
                    name = match1.group(1).strip()
                    pattern_name.append(name)
                else:
                    pattern_name.append("Null")    

                # Même procédé pour la sélection de l'emplacement du motif, aussi situé dans le Commentaire TDM
                pattern_loc = r"localisation : (.*?)(?:-|<|$)"
                match2 = re.search(pattern_loc, com_tdm)
                if match2:
                    localization = match2.group(1).strip()
                    pattern_localization.append(localization)
                else :
                    pattern_localization.append("Null")

                # Même procédé pour la sélection de son identifiant
                pattern_nb = r"identifiant : (.*?)(?:-|<|$)"
                match4 = re.search(pattern_nb, com_tdm)
                if match4:
                    id_m = match4.group(1).strip()
                    pattern_id.append(id_m)
                    if pattern_id == ['']:
                        pattern_id = ["Null"] 
                else:
                    pattern_id.append("Null")

                # Couleur(s) du motif

            # Si la couleur est renseignée dans le commentaire TDM
            pattern_clr = r"couleur : (.*?)(?:-|<|$)"
            match3 = re.search(pattern_clr, com_tdm)    
            if "descriptionType" in pattern and "comment" in pattern["descriptionType"] and match3:    
                color = match3.group(1).strip()
                pattern_color.append(color)    
                       
            # Si la couleur est renseignée dans les Caractéristiques    
            elif "support" in pattern and "thesaurus" in pattern["support"]:
                caracteristics = pattern["support"]["thesaurus"]
                for carac in caracteristics :
                    # On distingue la couleur des autres informations renseignées en Caractéristiques du fait qu'un 'Concept Path' leur est joint, de nom 'Couleur'
                    if "conceptPath" in carac :
                        concepts = carac["conceptPath"]
                        target_concept = r"(\/Couleur\/)"
                        match3_1 = re.search(target_concept, concepts)
                        if match3_1:
                            color2 = carac["prefLabels"][0]["value"]
                            pattern_color.append(color2)
                        else:
                            pass
                    else:
                        pass             
            else:
                pattern_color.append("Null")
            # Comme l'on a encore des listes vides qui apparaissent, on les remplit artificiellement de "Null" ici
            if pattern_color == []:
                pattern_color = ["Null"]
            else:
                pass                             

            # Notices externes
            if "content" in notice and "referenceInformation" in notice["content"] and "onlineSource" in notice["content"]["referenceInformation"]:
                target_sources = notice["content"]["referenceInformation"]["onlineSource"]
                for target_source in target_sources:
                    if "documentUrl" in target_source:
                        sources = ["Sources Coming Here"]
                    else:
                        pass
            else:
                sources = ["Null"]        

            # Si on pouvait avoir trace de l'indexation Garnier ce serait pas mal

            # Lien vers Image  
            if "internal" in notice and "permalink" in notice["internal"]:
                image_ref = notice["internal"]["permalink"]
                whole_image.append(image_ref)
            else:
                whole_image.append("Null")    
                                
            # Liens vers autres Motifs de l'Image 
            sibling_patterns.append("Motifs voisins Coming") 

            # Liens vers Couches matérielles
            material_layers.append("Couches matérielles Coming")

            # Résultat souhaité : retour de toutes les listes de réception dans le même ordre que les propriétés du modèle de ressource Omeka S
            return item_type_pattern, pattern_name, pattern_id, pattern_color, pattern_localization, whole_image, sibling_patterns, material_layers, sources


#  Instancier la classe Motif : 

#  On sélectionne tous les ***Blocs Matérialité***, opération que l'on **reconduira** pour la création des **classes Couches** : car les blocs Matérialité renseignent l'ensemble des informations utiles. Nous les divisons en 1. **Informations documentaires** (motifs iconographiques) et 2. Informations sur la **composition matérielle** (Couches)

#  Sélectionner ici tous les Blocs Matérialité de chaque notice Agorha, ****sous réserve que**** ces derniers renseignent effectivement des motifs, et non des Couches matérielles couvrant toute la surface de l'oeuvre.
#  Critère de choix: que le Commentaire Type de Description Matérielle comporte une étiquette "motif :"

# Liste d'arrivée des instances
motif_instances = []
# Parcours des notices à la recherche de blocs Matérialité
for notice in main_data["train"]:
        if "content" in notice and "descriptionInformation" in notice["content"] and "materiality" in notice["content"]["descriptionInformation"]:
                    
                    # Définition de la variable "pattern" ici: tout bloc Matérialité au sein d'une notice Agorha
                    patterns = notice["content"]["descriptionInformation"]["materiality"]
                    for pattern in patterns : 
                        # On interroge le Commentaire TDM de chaque bloc Matérialité et cerne s'il concerne un motif iconographique
                        if "descriptionType" in pattern and "comment" in pattern["descriptionType"]:
                            com_tdm = pattern["descriptionType"]["comment"]
                            pattern_nm = r"motif : (.*?)(?:-|<|$)"
                            # Si tel est le cas : le bloc Matérialité est ajouté aux instances de la classe Motif.
                            if re.search(pattern_nm, com_tdm):
                                motif_instance = Motif(notice["content"]["descriptionInformation"]["materiality"])
                                motif_instances.append(motif_instance)
                            else:
                                pass
                        else:
                            pass
        else:
            pass                                        

# Création du tableur CSV des Motifs iconographiques

with open('motifs88.csv', 'w', newline='', encoding='utf-8') as csvfile:
# A permuter avec 'motifs89.csv' tant que je n'ai pas conçu la meta-fonction du siècle

    # Noms des propriétés choisis pour le modèle de ressource "Motif iconographique", qui seront les titres des colonnes de notre tableur CSV
    column_names_motifs = ["cld:itemType", "dcterms:subject", "dcterms:identifier", "schema:color", "schema:position", "dcterms:isPartOf", "schema:isRelatedTo", "crm:P106_is_composed_of", "dcterms:source"]

    writer = csv.DictWriter(csvfile, fieldnames=column_names_motifs)
    writer.writeheader()

    for motif in motif_instances:
        writer.writerow({
            "cld:itemType": motif.item_type_pattern,
            "dcterms:subject": motif.pattern_name,
            "dcterms:identifier": motif.pattern_id,
            "schema:color": motif.pattern_color,
            "schema:position": motif.pattern_localization,
            "dcterms:isPartOf": motif.whole_image,
            "schema:isRelatedTo": motif.sibling_patterns,
            "crm:P106_is_composed_of": motif.material_layers,
            "dcterms:source": motif.sources,
        })                    

# ************** Modèle de ressource: Couche matérielle **************


# Nous convoquons donc ***deux types de couches***: les couches associées à un **motif** nommé, et les couches concernant l'**entièreté** de l'Image (renseignant les matériaux du panneau, du parchemin) ou de l'Oeuvre (renseignant les matériaux du cadre d'un polyptyque, ou la couvrure d'un manuscrit)

# Nous créons donc une classe pour chaque modèle de couche.

# Ici la fonction de tri:

def layer_sorting(data):

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

        # Listes d'arrivée de chaque Couche triée
        subclass1_instances = []
        subclass2_instances = []

        # Cibler l'emplacement des Couches dans le JSON : le bloc Matérialité de chaque notice
        for notice in data["train"]:
            if "content" in notice and "descriptionInformation" in notice["content"] and "materiality" in notice["content"]["descriptionInformation"]:
                patterns = notice["content"]["descriptionInformation"]["materiality"]
                for pattern in patterns:
                    if "descriptionType" in pattern and "comment" in pattern["descriptionType"]:
                        com_tdm = pattern["descriptionType"]["comment"]
                        pattern_nm = r"motif : (.*?)(?:;|-|<|$)"
                        this_match = re.search(pattern_nm, com_tdm)
                        
                        # Si le bloc Matérialité est associé à un Motif iconographique: la Couche est de 1er type
                        if this_match:
                            subclass1_instances.append(pattern)
                        # Sinon : la Couche renseigne un support (Image, Oeuvre), et est de 2e type
                        else:
                            subclass2_instances.append(pattern)
                    # S'il n'y a pas de commentaire TDM dans la Couche : on ne saura pas, et la Couche ne pourra pas être traitée
                    else:
                        pass
            # S'il n'y a pas de bloc Matérialité : il n'y a pas de couche à traiter
            else:
                pass                

    # Objectif: obtenir les 2 listes garnies de leurs Couches
    return subclass1_instances, subclass2_instances
    
# Application de la fonction à l'environnment de code principal
PatternLayer_instances, SupportLayer_instances = layer_sorting(main_data)                    

# Définition de la classe des Couches de premier type: celles détaillant des Motifs

class CouchedeMotif:

    # Nouveau préambule
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
                
        # Définition des propriétés de la classe Couches: nature de la couche, fonction de la couche, technique picturale, couleur, ID, emplacement, épaisseur, matériau(x), certitude de l'identification des matériaux, technique d'analyse, dimensions de la zone analysée, année de l'analyse, objet parent (Motif, Image, ou Oeuvre), Couches liées, Autre(s) Couches, renseignements annexes, notices externes
        def __init__(self, data):
            self.item_type_layer, self.layer_function, self.pictorial_technique, self.layer_color, self.layer_id, self.layer_localization, self.thickness, self.alteration, self.material, self.certainty, self.analysis_technique, self.dim, self.analysis_year, self.parent_object, self.linked_layers, self.other_layer, self.some_more, self.layer_sources = self.extract_properties(data)

        # Listes de réception pour chaque propriété
        def extract_properties(self, data):    
            item_type_layer = [] # cld:itemType
            layer_function = [] # dcterms:type
            pictorial_technique = [] # schema:artMedium
            layer_color = [] # schema:color
            layer_id = [] # dcterms:identifier
            alteration = [] # schema:itemCondition
            material = [] # schema:material
            certainty = [] # schema:interactivityType
            analysis_technique = [] # schema:measurementTechnique
            dim = [] # schema:hasMeasurement
            analysis_year = [] # schema:observationDate
            some_more = [] # dcterms:abstract
            layer_sources = [] # dcterms:source
            other_layer = [] # schema:isRelatedTo
            layer_localization = [] # schema:position
            thickness = [] # schema:materialExtent
            linked_layers = [] # crm:P134_continued # crm:P134i_was_continued_by
            parent_object = [] # crm:P106i_forms_part_of
                        
            # Item Type : nature de la couche : cibler le bloc "DescriptionType" de chaque bloc Matérialité
            if "descriptionType" in pattern and "thesaurus" in pattern["descriptionType"]:
                layers = pattern["descriptionType"]["thesaurus"]
                for layer_type in layers:
                    if "prefLabels" in layer_type and "value" in layer_type["prefLabels"][0]:
                        nature = layer_type["prefLabels"][0]["value"]
                        item_type_layer.append(nature)
                    else :
                        item_type_layer.append("Null")
            else : item_type_layer.append("Null")          

            # Fonction de la couche - couleur exclue! : cibler le bloc "support" de chaque bloc Matérialité
            if "support" in pattern and "thesaurus" in pattern["support"]:
                caracteristics = pattern["support"]["thesaurus"]
                for carac in caracteristics :
                    if "prefLabels" in carac and "value" in carac["prefLabels"][0]:
                        purpose = carac["prefLabels"][0]["value"]
                        # Vérifier que le concept renseigné par le thesaurus n'est ***pas*** une Couleur
                        if "conceptPath" in carac :
                            concepts = carac["conceptPath"]
                            target_concept = r"(\/Couleur\/)"
                            match_concept = re.search(target_concept, concepts)
                            # Si le concept est ue Couleur:
                            if match_concept:
                                # L'ajouter à la liste de réception des Couleurs
                                layer_color.append(purpose)
                            else:
                                # Sinon : l'ajouter à la liste de réception des Fonctions de la Couche
                                layer_function.append(purpose)
                        else:
                            layer_function.append(purpose)
                    else:
                        layer_function.append("Null")
            else:
                layer_function.append("Null")                                             

            # Technique picturale : cibler le bloc "technical" du bloc Matérialité
            if "technical" in pattern and "thesaurus" in pattern["technical"]:
                techniques = pattern["technical"]["thesaurus"]
                for some_technique in techniques:
                    # Premier emplacement : termes thésaurisés du bloc "Technique"
                    if "prefLabels" in some_technique and "value" in some_technique["prefLabels"][0]:
                        technique = some_technique["prefLabels"][0]["value"]
                        pictorial_technique.append(technique)
                        # Deuxième emplacement : en Commentaire Technique
                        if "technical" in pattern and "comment" in pattern["technical"]:
                            technique2_beta = pattern["technical"]["comment"]
                            # Sélection de la valeur textuelle sans les balises HTML    
                            regex_tech = r">([^<]+)</[\w]+>"
                            match_tech = re.search(regex_tech, technique2_beta)
                            if match_tech:
                                technique2 = match_tech.group(1)
                                pictorial_technique.append(technique2)
                            else:
                                pass
                        else:
                            pass    
            # En l'attente de publication du thesaurus "Technique" par Teresa, l'essentiel des informations seront de fait renseignées en Commentaire Technique, ***sans*** valeurs renseignées dans le champ "Technique" officiel
            elif "technical" in pattern and "comment" in pattern["technical"]:
                technique2_beta = pattern["technical"]["comment"]
                # Sélection de la valeur textuelle sans les balises HTML    
                regex_tech = r">([^<]+)</[\w]+>"
                match_tech = re.search(regex_tech, technique2_beta)
                if match_tech:
                    technique2 = match_tech.group(1)
                    pictorial_technique.append(technique2)
                    if pictorial_technique == '':
                        pictorial_technique = ["Null"]
                else:
                    technique2 = "Null"
                    pictorial_technique.append(technique2)
            
            # Et s'il n'y a rien, ni dans le champ "Technique", ni dans son Commentaire
            else:
                pictorial_technique.append("Null")                        

            # Informations isses du Commentaire Caractéristique

            # Couleur(s) de la couche : cibler le bloc "Support" ("Caractéristique") dans Agorha
            # Cibler le Commentaire Caractéristique, et le texte étiqueté "couleur :"
            if "support" in pattern and "comment" in pattern["support"]:
                com_car = pattern["support"]["comment"]

                # Sélection de tout texte compris entre l'étiquette "couleur : ", un point-virgule (délimiteur de sous-champ en Commentaire Caractéristique (parfois délimiteur de champ) un tiret, une balise HTML fermante ou une fin de ligne)
                pattern_clr = r"couleur : (.*?)(?:;|-|<|$)"
                match10 = re.search(pattern_clr, com_car)
                if match10:
                    color1 = match10.group(1).strip()
                    layer_color.append(color1)              
            else:
                if layer_color == []:
                    layer_color.append("Null")
                else:
                    pass    
                        
            # ID d'analyse labo de la couche : toujours renseigné dans le Commentaire Caractéristique, avec l'étiquette "position:" (oui, "position", pour un identifiant)
            if "support" in pattern and "comment" in pattern["support"]:
                com_car = pattern["support"]["comment"]    
                pattern_nb = r"position : (.*?)(?:;|-|<|$)"
                match11 = re.search(pattern_nb, com_car)
                if match11:
                    id = match11.group(1).strip()
                    layer_id.append(id)
                
                # Si le Commentaire Caractéristique ne renseigne pas de position, prendre l'identifiant renseigné pour le Motif iconographique, en Commentaire Type de Description Matérielle, et lui ajouter ".00": car un Motif peut compter plusieurs Couches.
                elif "descriptionType" in pattern and "comment" in pattern["descriptionType"]:
                    com_tdm = pattern["descriptionType"]["comment"]
                    pattern_id = r"identifiant : (.*?)(?:;|-|<|$)"
                    # S'il y a une étiquette "identifiant :", et du texte derrière: il y a un ID motif
                    match4 = re.search(pattern_id, com_tdm)
                    if match4:
                        # On sélectionne l'ID du motif
                        id_m = match4.group(1).strip()
                        # Et on compte chaque couche à l'unité au sein de ce motif
                        counter = 1 # Car on compte à l'unité
                        id2 = f"{id_m}.{counter:02}" # Mais comme on ignore le nombre potentiel de Couches par motif (tout en supposant qu'il n'y en a pas plus de 99) on comptera sur 2 chiffres: 01, 02, 10, 11...
                        layer_id.append(id2)
                    else:
                        pass    
                # Et puis si aucun identifiant n'est renseigné dans Agorha: valeur "Null"
                else:
                    layer_id.append("Null")
            else:
                layer_id.append("Null")                      

            # Etat de conservation de la couche : étiquette "altération : " au sein du Commentaire Caractéristique
            if "support" in pattern and "comment" in pattern["support"]:
                com_car = pattern["support"]["comment"]      
                pattern_alteration = r"altération : (.*?)(?:;|-|<|$)"
                match13 = re.search(pattern_alteration, com_car)
                if match13:
                    statement = match13.group(1).strip()
                    alteration.append(statement)
                else :
                    alteration.append("Null")
            else:
                alteration.append("Null")           
                                
            # Informations issues du Commentaire Matériau : cibler le commentaire du bloc "material" dans JSON

            # Matériau
            if "material" in pattern and "thesaurus" in pattern["material"]:
                matters = pattern["material"]["thesaurus"]
                # Si des termes thésaurisés sont renseignés:
                for matter in matters:
                    if "prefLabels" in matter and "value" in matter["prefLabels"][0]:
                        target_material = matter["prefLabels"][0]["value"]
                        material.append(target_material)
            else :
                pass  

            # Toutefois, l'essentiel des termes étant encore en attente de la publication du thesaurus "Matériau" de Teresa à l'heure où ce code est fait, ils se trouveront dans le Commentaire Matériau
            if "material" in pattern and "comment" in pattern["material"]:
                com_mat = pattern["material"]["comment"]
                
                # Le Commentaire Matériau peut renseigner plusieurs campagnes d'analyse, et donc plusieurs fois l'étiquette "matériau :" et ses valeurs. On teste ici la méthode "finditer", qui groupera ensemble toutes les occurrences de cette étiquette.

                # On recherche donc, par regex, tout texte obligatoirement encadré par les caractères "matériau :" au début, et ";" (séparateur entre l'étiquette "matériau" et "certitude" ou "-" (séparateur entre deux campagnes d'analyse) ou "<" (balise fermante HTML, toujours présente dans un Commentaire)

                # Dans les faits, la regex prend tout caractère qui n'est pas ces trois délimiteurs de fin, jusqu'à ce qu'elle en rencontre un.
                for other_material in re.finditer(r"(?<=matériau\s:)[^;-<]+", com_mat):
                    material.append(other_material.group())
                
                # Puisque nous avons ciblé deux emplacements, nous avons encore parfois des listes vides en résultat. On y implémente donc la valeur "Null" pour le tableur CSV.
                if material == []:
                    material = ["Null"]    

         # N'oublions pas que lorsqu'aucun matériau n'est identifié, ou supposé, on le nomme "indéterminé". Ce qui ne signifie pas que les données se sont décalées, et que l'on vient de sélectionner les valeurs de l'étiquette "certitude :"; ce mot peut être renseigné dans chaque catégorie.

                # Degré de certitude de l'analyse : étiquette "certitude :"
                pattern_cert = r"(?<=certitude\s:)[^;-<]+"
                match6 = re.findall(pattern_cert, com_mat)
                if match6:
                    certainty.extend(match6)
                else :
                    certainty.append("Null")   

                # Méthode d'analyse : étiquette "technique :"
                pattern_tech = r"(?<=technique\s:)[^;-<]+"
                match7 = re.findall(pattern_tech, com_mat)
                if match7 :
                    analysis_technique.extend(match7)
                else :
                    analysis_technique.append("Null")

                # Dimensions de la zone analysée : étiquette "dimension :"
                pattern_dim = r"(?<=dimension\s:)[^;-<]+"
                match8 = re.findall(pattern_dim, com_mat)    
                if match8:
                    dim.extend(match8)
                else :
                    dim.append("Null")

                # Année de l'analyse : étiquette "date :"
                pattern_year = r"(?<=date\s:)[^;-<]+"
                match9 = re.findall(pattern_year, com_mat)
                if match9:
                    analysis_year.extend(match9)
                else:
                    analysis_year.append("Null")
            else:
                certainty.append("Null")
                analysis_technique.append("Null")
                dim.append("Null")
                analysis_year.append("Null")      

            # Ajout des précisions documentaires renseignées en langage naturel au sein du Commentaire Matérialité
            
            if "comment" in pattern:
                speech_beta = pattern["comment"]
                # Suppression des éléments HTML
                pattern_speech = r">([^<]+)</[\w]+>"
                match0 = re.search(pattern_speech, speech_beta)
                if match0:
                    speech = match0.group(1)
                    some_more.append(speech)
                else:
                    pass
            else:
                some_more.append("Null")    

            # Notices externes - manoeuvre a priori trop complexe pour un import CSV
            if "sourcing" in pattern:
                some_sources = pattern["sourcing"]
                for some_source in some_sources:
                    if "biblioRef" in some_source:
                        layer_sources = ["Sources Coming Here"]
                        # Ce ne sont bien que les rapports d'analyse
                    else:
                        pass
            else:
                layer_sources.append("Null")          
                        
            # Autre Couche indépendante - manoeuvre a priori trop complexe pour un import CSV
            other_layer.append("ID Couches Coming")

            # Localisation : "Null" par défaut ici, car la localisation renseignée par le Motif lié, ou l'ID de la Couche, est suffisante.
            layer_localization.append("Null")

            # Epaisseur de la couche : cibler le Commentaire Caractéristique.
            if "support" in pattern and "comment" in pattern["support"]:
                com_car = pattern["support"]["comment"]  
                pattern_ep = r"épaisseur : (.*?)(?:;|-|<|$)"
                match12 = re.search(pattern_ep, com_car)
                if match12:
                    thickness_target = match12.group(1).strip()
                    thickness.append(thickness_target)
                else:
                    thickness.append("Null")
            else:
                thickness.append("Null")        

            linked_layers.append("Wait") 

            # Extrait de code au cas où il deviendrait envisageable de renseigner les ID de couches liées depuis le JSON
                
                #  # Couches liées parce que mélange
                #  more_id = r"- =|>.?=(.*?)(?-|<|$)"
                #  match14 = re.search(more_id, com_car)
                #  if match14:
                #      id_linked = match14.group(1).strip()
                #      linked_layers.append(id_linked)
                #  else :
                #      linked_layers.append("Null")       

            # Lien vers le Motif iconographique parent

            # Pour l'instant, on se contente de renseigner son identifiant, qu'on remplacera par l'ID Omeka S de la notice Motif créée plus tard.
            if "descriptionType" in pattern and "comment" in pattern["descriptionType"]:
                com_tdm = pattern["descriptionType"]["comment"]
                pattern_id = r"identifiant : (.*?)(?:;|-|<|$)"
                match4 = re.search(pattern_id, com_tdm)
                if match4:
                    id_m = match4.group(1).strip()
                    parent_object.append(id_m)
                else:
                    parent_object.append("Null")
            else:
                parent_object.append("Null")        
                
            # Résultat : obtention de toutes les listes de sortie, avec leurs valeurs adéquates
            return item_type_layer, layer_function, pictorial_technique, layer_color, layer_id, layer_localization, thickness, alteration, material, certainty, analysis_technique, dim, analysis_year, parent_object, linked_layers, other_layer, some_more, layer_sources

# Instancier la classe de ce premier type de Couches matérielles:

# Création de la liste vide de réception des instances
patternlayer_instances = []

# Sélectionner chaque élément présent dans la liste résultant de la fonction de tri
# La liste recensait des blocs Matérialité : chaque élément est donc un bloc Matérialité. C'est le même niveau d'information que le Motif iconographique, donc la même variable utilisée pour parcourir les informations ("pattern")
for pattern in PatternLayer_instances: 
    patternlayer_instance = CouchedeMotif(pattern)
    patternlayer_instances.append(patternlayer_instance)

# Définition de la classe des Couches de deuxième type : celles liées à l'ensemble de l'Image ou de l'Oeuvre, pour renseigner l'essentiel des matériaux qui en constituent le support.

class CoucheSupport:
                
    # Nouveau préambule
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
                
        # Définition des propriétés de la classe Couches - pareilles à celui du modèle précédent ; seules les modalités d'attribution de valeurs vont changer pour quelques-unes d'entre elles.
        def __init__(self, data):
            self.item_type_layer, self.layer_function, self.pictorial_technique, self.layer_color, self.layer_id, self.layer_localization, self.thickness, self.alteration, self.material, self.certainty, self.analysis_technique, self.dim, self.analysis_year, self.parent_object, self.linked_layers, self.other_layer, self.some_more, self.layer_sources = self.extract_properties(data)

        def extract_properties(self, data): 
            item_type_layer = [] # cld:itemType
            layer_function = [] # dcterms:type
            pictorial_technique = [] # schema:artMedium
            layer_color = [] # schema:color
            layer_id = [] # dcterms:identifier
            alteration = [] # schema:itemCondition
            material = [] # schema:material
            certainty = [] # schema:interactivityType
            analysis_technique = [] # schema:measurementTechnique
            dim = [] # schema:hasMeasurement
            analysis_year = [] # schema:observationDate
            some_more = [] # dcterms:abstract
            layer_sources = [] # dcterms:source
            other_layer = [] # schema:isRelatedTo
# Ces paramètres-ci sont modifiés par rapport à la classe 'Couches' précédente:
            layer_localization = [] # schema:position
            thickness = [] # schema:materialExtent
            linked_layers = [] # crm:P134_continued # crm:P134i_was_continued_by
            parent_object = [] # crm:P106i_forms_part_of
                        
            # Item Type : nature de la couche
            if "descriptionType" in pattern and "thesaurus" in pattern["descriptionType"]:
                layers = pattern["descriptionType"]["thesaurus"]
                for layer_type in layers:
                    if "prefLabels" in layer_type and "value" in layer_type["prefLabels"][0]:
                        nature = layer_type["prefLabels"][0]["value"]
                        item_type_layer.append(nature)
                    else :
                        item_type_layer.append("Null")
            else : item_type_layer.append("Null")          

             # Fonction de la couche - couleur exclue!
            if "support" in pattern and "thesaurus" in pattern["support"]:
                caracteristics = pattern["support"]["thesaurus"]
                for carac in caracteristics :
                    if "prefLabels" in carac and "value" in carac["prefLabels"][0]:
                        purpose = carac["prefLabels"][0]["value"]
                        if "conceptPath" in carac :
                            concepts = carac["conceptPath"]
                            target_concept = r"(\/Couleur\/)"
                            match_concept = re.search(target_concept, concepts)
                            if match_concept:
                                layer_color.append(purpose)
                            else:
                                layer_function.append(purpose)
                        else:
                            layer_function.append(purpose)
                    else:
                        layer_function.append("Null")
            else:
                layer_function.append("Null")                     

            # Technique picturale
            if "technical" in pattern and "thesaurus" in pattern["technical"]:
                techniques = pattern["technical"]["thesaurus"]
                for some_technique in techniques:
                    if "prefLabels" in some_technique and "value" in some_technique["prefLabels"][0]:
                        technique = some_technique["prefLabels"][0]["value"]
                        pictorial_technique.append(technique)
                        if "technical" in pattern and "comment" in pattern["technical"]:
                            technique2_beta = pattern["technical"]["comment"]
                            # Sélection de la valeur textuelle sans les balises HTML    
                            regex_tech = r">([^<]+)</[\w]+>"
                            match_tech = re.search(regex_tech, technique2_beta)
                            if match_tech:
                                technique2 = match_tech.group(1)
                                pictorial_technique.append(technique2)
                            else:
                                technique2 = ""
                                pictorial_technique.append(technique2)
                        else:
                            pass    
            elif "technical" in pattern and "comment" in pattern["technical"]:
                technique2_beta = pattern["technical"]["comment"]
                # Sélection de la valeur textuelle sans les balises HTML    
                regex_tech = r">([^<]+)</[\w]+>"
                match_tech = re.search(regex_tech, technique2_beta)
                if match_tech:
                    technique2 = match_tech.group(1)
                    pictorial_technique.append(technique2)
                    if pictorial_technique == '':
                        pictorial_technique = ["Null"]
                else:
                    technique2 = "Null"
                    pictorial_technique.append(technique2)
            else:
                pictorial_technique.append("Null")                    

            # Informations isses du Commentaire Caractéristique

            # Couleur(s) de la couche
            
            if "support" in pattern and "comment" in pattern["support"]:
                com_car = pattern["support"]["comment"]
                pattern_clr = r"couleur : (.*?)(?:;|-|<|$)"
                match10 = re.search(pattern_clr, com_car)
                if match10:
                    color1 = match10.group(1).strip()
                    layer_color.append(color1)              
            else:
                if layer_color == []:
                    layer_color.append("Null")
                else:
                    pass      
                        
            # ID d'analyse labo de la couche
            if "support" in pattern and "comment" in pattern["support"]:
                com_car = pattern["support"]["comment"]    
                pattern_nb = r"position : (.*?)(?:;|-|<|$)"
                match11 = re.search(pattern_nb, com_car)
                if match11:
                    id = match11.group(1).strip()
                    layer_id.append(id)
                elif "descriptionType" in pattern and "comment" in pattern["descriptionType"]:
                    com_tdm = pattern["descriptionType"]["comment"]
                    pattern_id = r"identifiant : (.*?)(?:;|-|<|$)"
                    match4 = re.search(pattern_id, com_tdm)
                    if match4:
                        id_m = match4.group(1).strip()
                        counter = 1
                        id2 = f"{id_m}.{counter:02}"
                        layer_id.append(id2)
                    else:
                        pass    
                else:
                    layer_id.append("Null")
            else: layer_id.append("Null")                      

            # Etat de conservation de la couche
            if "support" in pattern and "comment" in pattern["support"]:
                com_car = pattern["support"]["comment"]      
                pattern_alteration = r"altération : (.*?)(?:;|-|<|$)"
                match13 = re.search(pattern_alteration, com_car)
                if match13:
                    statement = match13.group(1).strip()
                    alteration.append(statement)
                else :
                    alteration.append("Null")
            else:
                alteration.append("Null")           
                                
            # Informations issues du Commentaire Matériau

            # Matériau
            if "material" in pattern and "thesaurus" in pattern["material"]:
                matters = pattern["material"]["thesaurus"]
                for matter in matters:
                    if "prefLabels" in matter and "value" in matter["prefLabels"][0]:
                        target_material = matter["prefLabels"][0]["value"]
                        material.append(target_material)
            else :
                pass  

            if "material" in pattern and "comment" in pattern["material"]:
                com_mat = pattern["material"]["comment"]
                pattern_mat = r"(?<=matériau\s:)[^;-<]+"
                match5 = re.findall(pattern_mat, com_mat)
                if match5:
                    material.extend(match5)
                else:
                    pass    
                if material == []:
                        material = ["Null"]         

                # Degré de certitude de l'analyse
                pattern_cert = r"(?<=certitude\s:)[^;-<]+"
                match6 = re.findall(pattern_cert, com_mat)
                if match6:
                    certainty.extend(match6)
                else :
                    certainty.append("Null")     

                # Méthode d'analyse
                pattern_tech = r"(?<=technique\s:)[^;-<]+"
                match7 = re.findall(pattern_tech, com_mat)
                if match7 :
                    analysis_technique.extend(match7)
                else :
                    analysis_technique.append("Null")  

                # Dimensions de la zone analysée
                pattern_dim = r"(?<=dimension\s:)[^;-<]+"
                match8 = re.findall(pattern_dim, com_mat)    
                if match8:
                    dim.extend(match8)
                else :
                    dim.append("Null")

                # Année de l'analyse
                pattern_year = r"(?<=date\s:)[^;-<]+"
                match9 = re.findall(pattern_year, com_mat)
                if match9:
                    analysis_year.extend(match9)
                else:
                    analysis_year.append("Null")
            else:
                material.append("Null")
                certainty.append("Null")
                analysis_technique.append("Null")
                dim.append("Null")
                analysis_year.append("Null")          

            # Commentaire Matérialité
            if "comment" in pattern:
                speech_beta = pattern["comment"]
                # Suppression des éléments HTML
                pattern_speech = r">([^<]+)</[\w]+>"
                match0 = re.search(pattern_speech, speech_beta)
                if match0:
                    speech = match0.group(1)
                    some_more.append(speech)
                else:
                    pass
            else:
                some_more.append("Null")    

            # Notices externes
            if "sourcing" in pattern:
                some_sources = pattern["sourcing"]
                for some_source in some_sources:
                    if "biblioRef" in some_source:
                        layer_sources = ["Sources Coming Here"]
                        # Ce ne sont bien que les rapports d'analyse
                    else:
                        pass
            else:
                layer_sources.append("Null")         
                        
            # Autre Couche indépendante
            other_layer.append("ID Couches Coming")

            # Puisqu'aucun nom de Motif n'est renseigné, on précisera donc la localisation de la couche (souvent désignée par "localisation : ensemble du panneau", ou "ensemble de la Page", ou "feuillet") à des fins de clarté pour les utilisateur.ices.
            
            # Localisation de la couche : transfert de celle présentée en Commentaire Type de Description Matérielle
            # Car, de toute manière, elle n'est pas utilisé pour un Motif iconographique : les Couches Support n'en ont pas (condition initiale remplie par la fonction de tri)
            if "descriptionType" in pattern and "comment" in pattern["descriptionType"]:
                com_tdm = pattern["descriptionType"]["comment"]
                target_localization = r"localisation : (.*?)(?:;|-|<|$)"
                match2 = re.search(target_localization, com_tdm)
                if match2:
                    layer_loc = match2.group(1).strip()
                    layer_localization.append(layer_loc)
                else :
                    layer_localization.append("Null")
            else:
                layer_localization.append("Null")        
                                         
            # Lien vers Image | Oeuvre : à faire via Bulk Edit sur Omeka S
            parent_object.append("Parent Coming Here")
            #  Renseigner un ark était théoriquement possible, mais difficile du fait que la variable autour de laquelle nous parcourons les données est "pattern", soit celle des blocs Matérialité, et non "notice", celles des notices entières. Le script de définition de classe "Couches" ne reconnaît donc pas facilement un niveau d'information supérieur à celui des blocs Matérialité.

            # On constate, à la lecture, que les Couches Support ne renseignent pas d'épaisseur, ni d'équivalences avec d'autres souches analysées ; d'où le passage ici à une valeur par défaut, par opposition à la classe précédente.            
            thickness.append("Null")
            linked_layers.append("Null")    
            # Si cela doit être réfuté, le modèle de classe sera modifié en conséquence.

            # Résultat : obtention de toutes les listes remplies.
            return item_type_layer, layer_function, pictorial_technique, layer_color, layer_id, layer_localization, thickness, alteration, material, certainty, analysis_technique, dim, analysis_year, parent_object, linked_layers, other_layer, some_more, layer_sources

# Instanciation de la classe, sur le même procédé que la classe précédente: récupération des blocs Matérialité triés dans la liste 2 par la fonction de tri.
supportlayer_instances = []
for pattern in SupportLayer_instances: # C'est donc cette ligne qui renseigne à quoi la variable "pattern" correspond pour cette classe.
    supportlayer_instance = CoucheSupport(pattern)
    supportlayer_instances.append(supportlayer_instance)

# Création du tableur CSV pour les Couches

# Comme les propriétés des deux classes sont les mêmes, et que seules changent leurs modalités d'attribution de valeurs, nous ferons un seul tableur réunissant les instances des deux classes.

# Il est plus aisé de passer par une fonction, pour que le tableur se crée automatiquement quel que soit le nom et le contenu des listes d'instances des classes Couches.
def layers_csv(list1, list2):

    with open('couches88.csv', 'w', newline='', encoding='utf-8') as csvfile:
# A permuter avec 'couches89.csv' tant que je n'ai pas conçu la meta-fonction du siècle

        # Nom des colonnes : propriétés choisies pour le Modèle de ressource "Couche(s) matérielle(s)" dans Omeka S
        column_names_couches = ["cld:itemType", "dcterms:type", "schema:artMedium", "schema:color", "dcterms:identifier", "schema:position", "schema:materialExtent", "schema:itemCondition", "schema:material", "schema:interactivityType", "schema:measurementTechnique", "schema:hasMeasurement", "schema:observationDate", "crm:P106i_forms_part_of", "crm:P134_continued", "schema:isRelatedTo", "dcterms:abstract", "dcterms:source"]

        writer = csv.DictWriter(csvfile, fieldnames=column_names_couches)
        writer.writeheader()

        # Une ligne pour chaque instance de la classe Couche de premier type
        for layer1 in list1:
            writer.writerow({
                "cld:itemType": layer1.item_type_layer, 
                "dcterms:type": layer1.layer_function, 
                "schema:artMedium": layer1.pictorial_technique,
                "schema:color": layer1.layer_color,
                "dcterms:identifier": layer1.layer_id, 
                "schema:position": layer1.layer_localization,
                "schema:materialExtent": layer1.thickness,
                "schema:itemCondition": layer1.alteration,  
                "schema:material": layer1.material,  
                "schema:interactivityType": layer1.certainty, 
                "schema:measurementTechnique": layer1.analysis_technique, 
                "schema:hasMeasurement": layer1.dim, 
                "schema:observationDate": layer1.analysis_year, 
                "crm:P106i_forms_part_of": layer1.parent_object, 
                "crm:P134_continued": layer1.linked_layers, 
                "schema:isRelatedTo": layer1.other_layer,    
                "dcterms:abstract": layer1.some_more,  
                "dcterms:source": layer1.layer_sources            
            })
        # Et, une fois la liste d'instances de cette dernière épuisée, une ligne pour chaque instance de la classe Couche de deuxième type
        for layer2 in list2:
            writer.writerow({
                "cld:itemType": layer2.item_type_layer, 
                "dcterms:type": layer2.layer_function, 
                "schema:artMedium": layer2.pictorial_technique,
                "schema:color": layer2.layer_color,
                "dcterms:identifier": layer2.layer_id,  
                "schema:position": layer2.layer_localization,
                "schema:materialExtent": layer2.thickness,
                "schema:itemCondition": layer2.alteration,   
                "schema:material": layer2.material,  
                "schema:interactivityType": layer2.certainty, 
                "schema:measurementTechnique": layer2.analysis_technique, 
                "schema:hasMeasurement": layer2.dim, 
                "schema:observationDate": layer2.analysis_year, 
                "crm:P106i_forms_part_of": layer2.parent_object, 
                "crm:P134_continued": layer2.linked_layers, 
                "schema:isRelatedTo": layer2.other_layer,   
                "dcterms:abstract": layer2.some_more,  
                "dcterms:source": layer2.layer_sources            
            })
    # Résultat : un document CSV réunissant toutes les Couches, une à chaque ligne
    return csvfile

# Appliquer la fonction CSV aux classes précédemment définies
couches88 = layers_csv(patternlayer_instances, supportlayer_instances)
# Là encore, le nom sera à permuter avec celui de l'autre base     


# ********** Gestion des fichiers CSV *************

# Ne pas indiquer le point-virgule comme séparateur, en ouverture des fichiers CSV

# Passer de la typographie des listes de chaînes de caractères Python à celle de valeurs de type 'texte brut' dans un tableur CSV:

# Nettoyer les guillemets doubles (Chercher-remplacer " par rien)
# Regex de nettoyage (apostrophes de début) : (?<=\[|\s)'
# Regex de nettoyage (apostrophe de fin) : '(?=,|\])
# Regex de nettoyage (crochets) : (\]|\[)

# Intégrer les § à la place des virgules et des points-virgule quand c'est possible (champs non titres)
# Intégrer des "Null" à toute cellule qui se trouverait encore vide