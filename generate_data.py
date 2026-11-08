# -*- coding: utf-8 -*-
"""
Generateur de cas cliniques de demonstration pour l'aide au diagnostic.

Cree des cas coherents (signes -> suspicion -> diagnostic) a partir de modeles
de pathologies frequentes en Afrique de l'Ouest, avec variation realiste.

Usage : importe par init_db.py, ou lance seul :  python generate_data.py 500
"""

import sys
import json
import random
from datetime import date, timedelta

# --- Pools de valeurs pour l'identification ---
PROPRIOS = ["Ndiaye", "Diop", "Fall", "Sow", "Ba", "Sarr", "Gueye", "Faye",
            "Diallo", "Cisse", "Kane", "Sy", "Toure", "Mbaye", "Sene", "Thiam",
            "Diouf", "Camara", "Barry", "Ndao", "Wade", "Niang", "Seck", "Kone"]
PRENOMS = ["Amadou", "Fatou", "Ibrahima", "Awa", "Moussa", "Aissatou", "Cheikh",
           "Mariama", "Ousmane", "Khady", "Modou", "Bineta", "Aliou", "Rama"]
VILLES = ["Dakar", "Thies", "Rufisque", "Pikine", "Guediawaye", "Mbour",
          "Saint-Louis", "Kaolack", "Ziguinchor", "Louga", "Cotonou", "Abomey-Calavi"]
NOMS_ANIMAUX = {
    "Chien": ["Rex", "Bobby", "Simba", "Max", "Bella", "Rocky", "Dolly", "Pongo", "Nero"],
    "Chat": ["Minou", "Felix", "Nala", "Simba", "Kitty", "Grisou", "Mimi"],
    "Bovin": ["Ndama", "Zebu", "Blanche", "Taureau", "Marguerite", "Sokh"],
    "Ovin": ["Belier", "Ladoum", "Blanchette", "Mouton"],
    "Caprin": ["Biquette", "Chevre", "Djolof"],
    "Volaille": ["Lot A", "Lot B", "Poule 1", "Bande 12", "Poulailler 3"],
    "Equin": ["Etalon", "Tornade", "Bijou", "Sultan"],
}
RACES = {
    "Chien": ["Berger allemand", "Berger belge", "Labrador", "Pitbull", "Croise",
              "Rottweiler", "Basset", "Beauceron", "Local"],
    "Chat": ["Europeen", "Siamois", "Persan", "Croise", "Local"],
    "Bovin": ["Ndama", "Zebu Gobra", "Zebu Maure", "Metis", "Montbeliarde"],
    "Ovin": ["Ladoum", "Peul-peul", "Touabire", "Bali-bali"],
    "Caprin": ["Guera", "Sahelienne", "Naine"],
    "Volaille": ["Poulet de chair", "Pondeuse", "Poulet local", "Cobb 500"],
    "Equin": ["Pur-sang", "Barbe", "Local"],
}
SEXES = ["M", "F"]
ROBES = {
    "Chien": ["Fauve", "Noir et feu", "Blanc", "Noir", "Bringe", "Tricolore"],
    "Chat": ["Tigre", "Noir", "Blanc", "Roux", "Ecaille"],
    "Bovin": ["Robe claire", "Pie noire", "Fauve", "Grise"],
    "Ovin": ["Blanche", "Pie", "Noire"],
    "Caprin": ["Brune", "Blanche", "Noire"],
    "Volaille": ["Plumage roux", "Plumage blanc", "Plumage varie"],
    "Equin": ["Bai", "Alezan", "Noir", "Gris"],
}
MODE_VIE = ["Interieur", "Exterieur", "Mixte"]
CONSCIENCE = ["Conscient", "Somnolent"]

# ---------------------------------------------------------------------------
# Modeles de pathologies : signes coherents -> diagnostic
# Chaque modele fournit les champs cliniques discriminants.
# ---------------------------------------------------------------------------
T = []
def modele(**kw): T.append(kw)

# ---- CHIEN ----
modele(espece="Chien", diagnostic="Parvovirose canine", poids=(3, 20), age=(0.3, 2),
       motif="Vomissements repetes, diarrhee hemorragique nauseabonde, anorexie totale et abattement marque",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Tachypneique",
       muq_c="Congestionnee", muq_h="Seche", pli="Persistant (deshydratation)", temp=(39.8, 41.0),
       hypotheses="Parvovirose canine, gastro-enterite hemorragique, intoxication alimentaire",
       exams=["Test antigenique (Parvo, Corona...)", "NFS (Numeration Formule Sanguine)", "Hematocrite"],
       pronostic="Reserve", traitement="Rehydratation IV (Ringer lactate), antiemetiques, antibiotherapie de couverture, nutrition assistee",
       resultat=["Amelioration", "Guerison", "Aggravation", "Deces"])
modele(espece="Chien", diagnostic="Maladie de Carre", poids=(4, 22), age=(0.4, 3),
       motif="Jetage oculo-nasal muco-purulent, toux, hyperthermie et apparition de myoclonies",
       evolution="Progressive", comportement="Deprime / Abattu", demarche="Ataxie",
       pelage="Terne / Mat", jetage="Muco-purulent", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(39.5, 40.8),
       hypotheses="Maladie de Carre, pneumonie infectieuse, affection nerveuse",
       exams=["PCR virale", "Serologie (ELISA, SNT, IHA)", "Radiographie thoracique"],
       pronostic="Reserve", traitement="Traitement symptomatique, antibiotiques contre surinfections, anticonvulsivants, soins de support",
       resultat=["Amelioration", "Stationnaire", "Aggravation", "Deces"])
modele(espece="Chien", diagnostic="Babesiose (piroplasmose)", poids=(5, 30), age=(0.5, 9),
       motif="Abattement, hyperthermie, muqueuses pales puis icteriques, urines foncees, presence de tiques",
       evolution="Brutale", comportement="Apathique", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Tachypneique",
       muq_c="Icterique", muq_h="Normale", pli="Normal", temp=(39.8, 41.2),
       hypotheses="Babesiose, ehrlichiose, anemie hemolytique",
       exams=["Frottis sanguin", "NFS (Numeration Formule Sanguine)", "Hematocrite", "Analyse d'urine (bandelette)"],
       pronostic="Reserve", traitement="Diminazene (Berenil) ou imidocarbe, transfusion si anemie severe, soins de support",
       resultat=["Guerison", "Amelioration", "Aggravation"])
modele(espece="Chien", diagnostic="Ehrlichiose canine", poids=(6, 30), age=(1, 10),
       motif="Hyperthermie, epistaxis, adenomegalie generalisee, abattement, presence de tiques",
       evolution="Progressive", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Hemorragique", respiration="Normale (Costo-abdominale)",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(39.3, 40.5),
       hypotheses="Ehrlichiose, babesiose, trouble de la coagulation",
       exams=["Serologie (ELISA, SNT, IHA)", "Frottis sanguin", "NFS (Numeration Formule Sanguine)", "Temps de coagulation"],
       pronostic="Reserve", traitement="Doxycycline pendant 28 jours, soins de support, transfusion si besoin",
       resultat=["Guerison", "Amelioration", "Stationnaire"])
modele(espece="Chien", diagnostic="Gastro-enterite d'origine alimentaire", poids=(4, 30), age=(0.5, 12),
       motif="Vomissements et diarrhee apparus apres un changement d'alimentation, animal encore alerte",
       evolution="Brutale", comportement="Normal", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(38.2, 39.4),
       hypotheses="Gastro-enterite alimentaire, indigestion, parasitisme digestif",
       exams=["Coproscopie par flottation"],
       pronostic="Favorable", traitement="Diete hydrique, pansements digestifs, rehydratation orale, reprise alimentaire progressive",
       resultat=["Guerison", "Amelioration"])
modele(espece="Chien", diagnostic="Gale sarcoptique", poids=(4, 28), age=(0.5, 10),
       motif="Prurit intense, alopecie, squames et lesions cutanees de grattage sur le corps",
       evolution="Progressive", comportement="Agite / Excite", demarche="Normale",
       pelage="Alopecie diffuse", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(38.2, 39.2),
       hypotheses="Gale sarcoptique, dermatite allergique, teigne",
       exams=["Raclage cutane", "Culture fongique (DTM)", "Examen au scotch-test"],
       pronostic="Favorable", traitement="Acaricide (ivermectine ou isoxazolines), shampooings, traitement de l'environnement",
       resultat=["Guerison", "Amelioration"])
modele(espece="Chien", diagnostic="Otite externe", poids=(4, 30), age=(0.5, 12),
       motif="Secousses de tete, prurit auriculaire, ecoulement et mauvaise odeur de l'oreille",
       evolution="Progressive", comportement="Agite / Excite", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(38.2, 39.2),
       hypotheses="Otite externe bacterienne, otite a Malassezia, gale d'oreille",
       exams=["Frottis colore (Gram, Giemsa...)", "Culture bacterienne + antibiogramme"],
       pronostic="Favorable", traitement="Nettoyage auriculaire, gouttes auriculaires antibiotiques et anti-inflammatoires",
       resultat=["Guerison", "Amelioration"])
modele(espece="Chien", diagnostic="Insuffisance renale chronique", poids=(4, 25), age=(6, 15),
       motif="Amaigrissement, polyuro-polydipsie, vomissements intermittents et haleine uremique",
       evolution="Progressive", comportement="Apathique", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Pales", muq_h="Seche", pli="Persistant (deshydratation)", temp=(37.8, 38.8),
       hypotheses="Insuffisance renale chronique, leishmaniose, affection tumorale",
       exams=["Uree sanguine (BUN)", "Creatinine", "Analyse d'urine (bandelette)", "Echographie renale et vesicale"],
       pronostic="Defavorable", traitement="Fluidotherapie, regime renal, chelateurs du phosphore, soutien",
       resultat=["Stationnaire", "Aggravation", "Amelioration"])
modele(espece="Chien", diagnostic="Fracture des membres", poids=(4, 35), age=(0.5, 12),
       motif="Boiterie aigue avec impotence apres un accident, douleur vive et oedeme localise",
       evolution="Brutale", comportement="Normal", demarche="Boiterie anterieure droite",
       pelage="Normal / Brillant", jetage="Absent", respiration="Tachypneique",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(38.3, 39.3),
       hypotheses="Fracture, luxation, entorse grave",
       exams=["Radiographie osteo-articulaire"],
       pronostic="Favorable", traitement="Immobilisation ou osteosynthese, antalgiques, repos strict",
       resultat=["Guerison", "Amelioration"])
modele(espece="Chien", diagnostic="Rage (suspicion)", poids=(5, 30), age=(0.5, 8),
       motif="Modification brutale du comportement, agressivite, hypersalivation puis paralysie ascendante",
       evolution="Brutale", comportement="Agressif", demarche="Paralysie",
       pelage="Normal / Brillant", jetage="Absent", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(39.0, 40.5),
       hypotheses="Rage, maladie de Carre forme nerveuse, intoxication",
       exams=["Autopsie / necropsie"],
       pronostic="Sombre", traitement="Isolement, mise en observation, declaration obligatoire, pas de traitement",
       resultat=["Deces"])
modele(espece="Chien", diagnostic="Parasitisme digestif", poids=(2, 15), age=(0.2, 2),
       motif="Diarrhee chronique, ballonnement abdominal, retard de croissance et poil pique chez un jeune",
       evolution="Progressive", comportement="Normal", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(38.2, 39.2),
       hypotheses="Parasitisme digestif (ascaris, ankylostomes), coccidiose",
       exams=["Coproscopie par flottation", "Coproscopie directe"],
       pronostic="Favorable", traitement="Vermifugation adaptee, complementation, suivi coproscopique",
       resultat=["Guerison", "Amelioration"])
modele(espece="Chien", diagnostic="Trypanosomose canine", poids=(6, 30), age=(1, 10),
       motif="Hyperthermie intermittente, amaigrissement progressif, oedemes declives et anemie",
       evolution="Intermittente", comportement="Apathique", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Tachypneique",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(39.2, 40.8),
       hypotheses="Trypanosomose, babesiose, ehrlichiose",
       exams=["Frottis sanguin", "NFS (Numeration Formule Sanguine)", "Serologie (ELISA, SNT, IHA)"],
       pronostic="Reserve", traitement="Trypanocides (diminazene), soins de support, lutte anti-vectorielle",
       resultat=["Amelioration", "Guerison", "Aggravation"])

# ---- CHAT ----
modele(espece="Chat", diagnostic="Coryza felin", poids=(2, 6), age=(0.3, 12),
       motif="Eternuements, jetage nasal, ecoulement oculaire, conjonctivite et anorexie",
       evolution="Progressive", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Muco-purulent", respiration="Tachypneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(39.2, 40.5),
       hypotheses="Coryza felin (herpesvirus/calicivirus), rhinite bacterienne",
       exams=["PCR virale", "Test rapide antigenique"],
       pronostic="Favorable", traitement="Antibiotiques, mucolytiques, nettoyage des naseaux, stimulation de l'appetit",
       resultat=["Guerison", "Amelioration"])
modele(espece="Chat", diagnostic="Panleucopenie feline (typhus)", poids=(1.5, 5), age=(0.3, 3),
       motif="Vomissements, diarrhee, abattement severe et deshydratation chez un jeune chat",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Tachypneique",
       muq_c="Pales", muq_h="Seche", pli="Persistant (deshydratation)", temp=(39.5, 41.0),
       hypotheses="Panleucopenie feline, gastro-enterite virale, intoxication",
       exams=["Test antigenique (Parvo, Corona...)", "NFS (Numeration Formule Sanguine)"],
       pronostic="Reserve", traitement="Rehydratation IV, antiemetiques, antibiotiques, nutrition assistee",
       resultat=["Amelioration", "Deces", "Guerison"])
modele(espece="Chat", diagnostic="Insuffisance renale chronique", poids=(2, 6), age=(7, 18),
       motif="Amaigrissement, polyuro-polydipsie, anorexie et halitose uremique",
       evolution="Progressive", comportement="Apathique", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Pales", muq_h="Seche", pli="Persistant (deshydratation)", temp=(37.8, 38.8),
       hypotheses="Insuffisance renale chronique, hyperthyroidie, diabete",
       exams=["Uree sanguine (BUN)", "Creatinine", "Analyse d'urine (bandelette)", "Echographie renale et vesicale"],
       pronostic="Defavorable", traitement="Fluidotherapie, regime renal, phosphore chelateurs, soutien",
       resultat=["Stationnaire", "Aggravation"])
modele(espece="Chat", diagnostic="Syndrome urologique felin (obstruction)", poids=(3, 7), age=(1, 10),
       motif="Efforts pour uriner improductifs, abdomen tendu et douloureux, agitation chez un male",
       evolution="Brutale", comportement="Agite / Excite", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Tachypneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(37.5, 39.0),
       hypotheses="Obstruction uretrale, cystite, calculs urinaires",
       exams=["Echographie renale et vesicale", "Radiographie abdominale", "Analyse d'urine (bandelette)"],
       pronostic="Reserve", traitement="Sondage urinaire d'urgence, fluidotherapie, correction electrolytique, regime urinaire",
       resultat=["Guerison", "Amelioration", "Aggravation"])
modele(espece="Chat", diagnostic="Abces sous-cutane", poids=(2.5, 7), age=(0.5, 12),
       motif="Tumefaction chaude et douloureuse apparue apres une bagarre, avec fievre",
       evolution="Brutale", comportement="Craintif", demarche="Boiterie posterieure gauche",
       pelage="Normal / Brillant", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(39.2, 40.5),
       hypotheses="Abces sous-cutane, cellulite, morsure infectee",
       exams=["Cytoponction ganglionnaire", "Culture bacterienne + antibiogramme"],
       pronostic="Favorable", traitement="Drainage, nettoyage, antibiotiques, anti-inflammatoires",
       resultat=["Guerison", "Amelioration"])
modele(espece="Chat", diagnostic="Diabete sucre", poids=(3, 8), age=(6, 15),
       motif="Polyuro-polydipsie, polyphagie mais amaigrissement progressif",
       evolution="Progressive", comportement="Normal", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(38.0, 39.0),
       hypotheses="Diabete sucre, hyperthyroidie, insuffisance renale",
       exams=["Glycemie", "Analyse d'urine (bandelette)", "Dosage insuline"],
       pronostic="Reserve", traitement="Insulinotherapie, regime adapte, suivi glycemique",
       resultat=["Amelioration", "Stationnaire"])

# ---- BOVIN ----
modele(espece="Bovin", diagnostic="Fievre aphteuse", poids=(150, 450), age=(1, 10),
       motif="Hyperthermie, hypersalivation abondante, aphtes buccaux et podaux, boiterie et chute de production",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Boiterie anterieure droite",
       pelage="Normal / Brillant", jetage="Sereux", respiration="Normale (Costo-abdominale)",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(40.0, 41.5),
       hypotheses="Fievre aphteuse, stomatite vesiculeuse, IBR",
       exams=["PCR virale", "Serologie (ELISA, SNT, IHA)"],
       pronostic="Reserve", traitement="Traitement symptomatique, antiseptiques locaux, isolement, declaration obligatoire",
       resultat=["Amelioration", "Guerison", "Stationnaire"])
modele(espece="Bovin", diagnostic="Trypanosomose bovine", poids=(120, 400), age=(1, 12),
       motif="Amaigrissement progressif, anemie, muqueuses pales, oedemes et hyperthermie intermittente",
       evolution="Intermittente", comportement="Apathique", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Tachypneique",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(39.5, 41.0),
       hypotheses="Trypanosomose, babesiose, anaplasmose, fasciolose",
       exams=["Frottis sanguin", "NFS (Numeration Formule Sanguine)", "Hematocrite"],
       pronostic="Reserve", traitement="Trypanocides (diminazene, isometamidium), soins de support, lutte anti-tsetse",
       resultat=["Amelioration", "Guerison", "Aggravation"])
modele(espece="Bovin", diagnostic="Dermatophilose", poids=(120, 400), age=(0.5, 12),
       motif="Croutes cutanees adherentes sur le dos et l'encolure apparues en saison des pluies",
       evolution="Progressive", comportement="Normal", demarche="Normale",
       pelage="Lesions cutanees", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(38.5, 39.5),
       hypotheses="Dermatophilose, teigne, gale",
       exams=["Frottis colore (Gram, Giemsa...)", "Raclage cutane"],
       pronostic="Favorable", traitement="Antibiotiques (penicilline-streptomycine), soins locaux asechants",
       resultat=["Guerison", "Amelioration"])
modele(espece="Bovin", diagnostic="Fasciolose", poids=(120, 400), age=(1, 12),
       motif="Amaigrissement, oedeme sous-mandibulaire (bouteille), anemie et baisse de production",
       evolution="Progressive", comportement="Apathique", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(38.3, 39.3),
       hypotheses="Fasciolose, trypanosomose, haemonchose, carence",
       exams=["Coproscopie par sedimentation", "NFS (Numeration Formule Sanguine)"],
       pronostic="Favorable", traitement="Douvicide (triclabendazole), complementation, drainage des paturages",
       resultat=["Guerison", "Amelioration"])
modele(espece="Bovin", diagnostic="Babesiose bovine", poids=(120, 420), age=(1, 12),
       motif="Hyperthermie, urines rouges (hemoglobinurie), anemie et presence de tiques",
       evolution="Brutale", comportement="Apathique", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Tachypneique",
       muq_c="Icterique", muq_h="Normale", pli="Normal", temp=(40.0, 41.5),
       hypotheses="Babesiose, anaplasmose, trypanosomose",
       exams=["Frottis sanguin", "Hematocrite", "Analyse d'urine (bandelette)"],
       pronostic="Reserve", traitement="Imidocarbe ou diminazene, transfusion si besoin, lutte anti-tiques",
       resultat=["Guerison", "Amelioration", "Deces"])
modele(espece="Bovin", diagnostic="Mammite", poids=(150, 450), age=(2, 12),
       motif="Mamelle chaude, enflee et douloureuse avec lait anormal (grumeaux) et baisse de production",
       evolution="Brutale", comportement="Normal", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(39.0, 41.0),
       hypotheses="Mammite clinique, mammite gangreneuse",
       exams=["Culture bacterienne + antibiogramme", "Frottis colore (Gram, Giemsa...)"],
       pronostic="Reserve", traitement="Antibiotiques intramammaires et generaux, traite frequente, anti-inflammatoires",
       resultat=["Guerison", "Amelioration", "Stationnaire"])
modele(espece="Bovin", diagnostic="Meteorisation (tympanisme)", poids=(150, 450), age=(1, 12),
       motif="Distension brutale du flanc gauche, gene respiratoire et anxiete apres ingestion de fourrage",
       evolution="Brutale", comportement="Agite / Excite", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(38.5, 39.5),
       hypotheses="Meteorisation spumeuse, meteorisation gazeuse, obstruction oesophagienne",
       exams=["Radiographie abdominale"],
       pronostic="Reserve", traitement="Sonde oesophagienne, anti-moussants, trocardisation en urgence si asphyxie",
       resultat=["Guerison", "Amelioration", "Deces"])
modele(espece="Bovin", diagnostic="Peripneumonie contagieuse (PPCB)", poids=(120, 420), age=(1, 12),
       motif="Toux, dyspnee marquee, hyperthermie, jetage et posture cou tendu",
       evolution="Progressive", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Muco-purulent", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(40.0, 41.5),
       hypotheses="Peripneumonie contagieuse bovine, pasteurellose, tuberculose",
       exams=["Serologie (ELISA, SNT, IHA)", "Radiographie thoracique", "Autopsie / necropsie"],
       pronostic="Reserve", traitement="Antibiotiques (tylosine), isolement, declaration, vaccination du troupeau",
       resultat=["Amelioration", "Stationnaire", "Deces"])

# ---- PETITS RUMINANTS ----
modele(espece="Ovin", diagnostic="Peste des petits ruminants (PPR)", poids=(15, 40), age=(0.5, 6),
       motif="Hyperthermie, jetage, stomatite erosive, diarrhee profuse et signes respiratoires",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Muco-purulent", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Seche", pli="Persistant (deshydratation)", temp=(40.0, 41.5),
       hypotheses="Peste des petits ruminants, pasteurellose, coccidiose",
       exams=["Test rapide antigenique", "PCR virale", "Serologie (ELISA, SNT, IHA)"],
       pronostic="Reserve", traitement="Traitement symptomatique, antibiotiques contre surinfections, rehydratation, vaccination",
       resultat=["Amelioration", "Deces", "Stationnaire"])
modele(espece="Caprin", diagnostic="Peste des petits ruminants (PPR)", poids=(12, 35), age=(0.5, 6),
       motif="Fievre elevee, ecoulement nasal, ulceres buccaux et diarrhee liquide",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Muco-purulent", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Seche", pli="Persistant (deshydratation)", temp=(40.0, 41.5),
       hypotheses="Peste des petits ruminants, pasteurellose, entérotoxemie",
       exams=["Test rapide antigenique", "PCR virale"],
       pronostic="Reserve", traitement="Symptomatique, antibiotiques, rehydratation, vaccination du cheptel",
       resultat=["Amelioration", "Deces"])
modele(espece="Ovin", diagnostic="Entérotoxemie", poids=(15, 45), age=(0.3, 4),
       motif="Mort subite ou signes nerveux brutaux, diarrhee, chez un animal en bon etat bien nourri",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Ataxie",
       pelage="Normal / Brillant", jetage="Absent", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(38.5, 40.5),
       hypotheses="Entérotoxemie (Clostridium), intoxication, meningo-encephalite",
       exams=["Autopsie / necropsie", "Culture bacterienne des selles"],
       pronostic="Sombre", traitement="Anti-toxines, antibiotiques, vaccination preventive du troupeau",
       resultat=["Deces", "Aggravation"])
modele(espece="Caprin", diagnostic="Gale caprine", poids=(12, 35), age=(0.5, 8),
       motif="Prurit intense, croutes et alopecie s'etendant sur la tete et le corps",
       evolution="Progressive", comportement="Agite / Excite", demarche="Normale",
       pelage="Alopecie diffuse", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Roses", muq_h="Normale", pli="Normal", temp=(38.5, 39.5),
       hypotheses="Gale sarcoptique, teigne, dermatophilose",
       exams=["Raclage cutane"],
       pronostic="Favorable", traitement="Ivermectine, soins locaux, traitement de tout le troupeau",
       resultat=["Guerison", "Amelioration"])
modele(espece="Ovin", diagnostic="Haemonchose", poids=(15, 45), age=(0.5, 6),
       motif="Anemie marquee, oedeme sous-mandibulaire, amaigrissement et faiblesse",
       evolution="Progressive", comportement="Apathique", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Tachypneique",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(38.5, 39.5),
       hypotheses="Haemonchose, fasciolose, carence, trypanosomose",
       exams=["Coproscopie par flottation", "Hematocrite"],
       pronostic="Favorable", traitement="Anthelminthique (levamisole/albendazole), complementation, rotation des paturages",
       resultat=["Guerison", "Amelioration"])

# ---- VOLAILLE ----
modele(espece="Volaille", diagnostic="Maladie de Newcastle", poids=(0.5, 3), age=(0.1, 2),
       motif="Signes respiratoires, torticolis, diarrhee verdatre et forte mortalite dans le lot",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Ataxie",
       pelage="Terne / Mat", jetage="Sereux", respiration="Dyspneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(41.0, 43.0),
       hypotheses="Maladie de Newcastle, influenza aviaire, bronchite infectieuse",
       exams=["PCR virale", "Serologie (ELISA, SNT, IHA)", "Autopsie / necropsie"],
       pronostic="Sombre", traitement="Pas de traitement specifique, vaccination, biosecurite, elimination des sujets atteints",
       resultat=["Deces", "Aggravation"])
modele(espece="Volaille", diagnostic="Maladie de Gumboro", poids=(0.3, 2), age=(0.05, 0.5),
       motif="Abattement, plumes ebouriffees, diarrhee blanchatre et mortalite chez de jeunes sujets",
       evolution="Brutale", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(41.0, 43.0),
       hypotheses="Maladie de Gumboro, coccidiose, colibacillose",
       exams=["Autopsie / necropsie", "Serologie (ELISA, SNT, IHA)"],
       pronostic="Reserve", traitement="Support (vitamines, electrolytes), antibiotiques contre surinfections, vaccination",
       resultat=["Amelioration", "Deces"])
modele(espece="Volaille", diagnostic="Coccidiose", poids=(0.3, 2.5), age=(0.05, 1),
       motif="Diarrhee sanguinolente, plumes ebouriffees, prostration et mortalite progressive",
       evolution="Progressive", comportement="Deprime / Abattu", demarche="Normale",
       pelage="Terne / Mat", jetage="Absent", respiration="Normale (Costo-abdominale)",
       muq_c="Pales", muq_h="Normale", pli="Normal", temp=(41.0, 42.5),
       hypotheses="Coccidiose, entérite necrotique, salmonellose",
       exams=["Coproscopie par flottation", "Autopsie / necropsie"],
       pronostic="Favorable", traitement="Anticoccidiens (amprolium, sulfamides), vitamines, desinfection de la litiere",
       resultat=["Guerison", "Amelioration"])

# ---- EQUIN ----
modele(espece="Equin", diagnostic="Colique", poids=(200, 500), age=(1, 20),
       motif="Douleur abdominale intense, agitation, coups de pied vers le ventre et roulades",
       evolution="Brutale", comportement="Agite / Excite", demarche="Normale",
       pelage="Normal / Brillant", jetage="Absent", respiration="Tachypneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(38.0, 39.5),
       hypotheses="Colique spasmodique, colique obstructive, torsion intestinale",
       exams=["Echographie abdominale generale", "Radiographie abdominale"],
       pronostic="Reserve", traitement="Antispasmodiques, antalgiques, sondage naso-gastrique, chirurgie si obstruction",
       resultat=["Guerison", "Amelioration", "Deces"])
modele(espece="Equin", diagnostic="Tetanos", poids=(200, 500), age=(1, 20),
       motif="Raideur generalisee, trismus, procidence de la 3e paupiere apres une plaie souillee",
       evolution="Progressive", comportement="Agite / Excite", demarche="Position antalgique",
       pelage="Normal / Brillant", jetage="Absent", respiration="Tachypneique",
       muq_c="Congestionnee", muq_h="Normale", pli="Normal", temp=(38.5, 40.0),
       hypotheses="Tetanos, intoxication, affection neurologique",
       exams=["Test reflexes nerveux"],
       pronostic="Sombre", traitement="Serum et anatoxine tetaniques, antibiotiques, myorelaxants, calme et obscurite",
       resultat=["Aggravation", "Deces", "Amelioration"])


def _rand_texte_examens(t):
    return random.choice([
        "Souffle non ausculte", "Rythme regulier", "Bruits normaux",
        "Tachycardie", "Rien a signaler"])


def generer(n=500, auteurs=None, seed=None):
    """Cree n objets CasClinique (non ajoutes a la session)."""
    from app import CasClinique
    if seed is not None:
        random.seed(seed)
    auteurs = auteurs or [None]
    cas = []
    aujourd = date.today()
    for i in range(n):
        m = random.choice(T)
        espece = m["espece"]
        pmin, pmax = m["poids"]; amin, amax = m["age"]; tmin, tmax = m["temp"]
        publie = random.random() < 0.9  # 90% publies
        prop_prenom = random.choice(PRENOMS); prop_nom = random.choice(PROPRIOS)
        diag = m["diagnostic"]
        c = CasClinique(
            date_consultation=aujourd - timedelta(days=random.randint(0, 720)),
            titre=f"{diag} - {random.choice(NOMS_ANIMAUX.get(espece, ['Cas']))}",
            proprietaire_nom=f"{prop_prenom} {prop_nom}",
            proprietaire_telephone=f"+221 7{random.randint(0,8)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
            proprietaire_adresse=random.choice(VILLES),
            animal_nom=random.choice(NOMS_ANIMAUX.get(espece, ["Sans nom"])),
            espece=espece,
            race=random.choice(RACES.get(espece, ["Local"])),
            age=round(random.uniform(amin, amax), 1),
            sexe=random.choice(SEXES),
            poids=round(random.uniform(pmin, pmax), 1),
            robe=random.choice(ROBES.get(espece, ["Indefinie"])),
            motif_consultation=m["motif"],
            alimentation=random.choice(["Ration menagere", "Aliment industriel", "Paturage", "Mixte", "Grains"]),
            mode_vie=random.choice(MODE_VIE),
            vaccination=random.choice(["Oui - preciser", "Non", "Statut inconnu"]),
            vermifugation=random.choice(["Oui - preciser", "Non", "Statut inconnu"]),
            contact_animaux=random.choice(["Oui", "Non"]),
            evolution_signes=m["evolution"],
            traitements_anterieurs=random.choice(["Aucun", "Automedication", "Traitement traditionnel", ""]),
            etat_conscience=random.choice(CONSCIENCE),
            comportement=m["comportement"],
            posture=random.choice(["Normale", "Tete basse", "Position antalgique"]),
            demarche=m["demarche"],
            nec=random.choice(["1 - Tres maigre", "2 - Maigre", "3 - Moyen", "4 - Bon etat"]),
            pelage=m["pelage"],
            jetage=m["jetage"],
            respiration_type=m["respiration"],
            ptyalisme=random.choice(["Absent", "Present"]),
            temperature=round(random.uniform(tmin, tmax), 1),
            pouls=f"{random.randint(60, 140)} bpm",
            frequence_respiratoire=f"{random.randint(15, 60)}/min",
            muqueuse_couleur=m["muq_c"],
            muqueuse_humidite=m["muq_h"],
            pli_peau=m["pli"],
            noeuds_lymphatiques=json.dumps(
                random.choice([[], ["Mandibulaire G - Hypertrophie"], ["Prescapulaire G - Hypertrophie", "Prescapulaire D - Hypertrophie"]]),
                ensure_ascii=False),
            auscultation_cardiaque=_rand_texte_examens(m),
            auscultation_pulmonaire=random.choice(["Normale", "Crepitements", "Sibilants", "Rien a signaler"]),
            auscultation_digestive=random.choice(["Borborygmes presents", "Silence auscultatoire", "Normale"]),
            examen_rapproche_autres="",
            photos="[]", videos="[]",
            hypotheses_diagnostiques=m["hypotheses"],
            raisonnement_clinique="Orientation etablie a partir de l'anamnese, de l'examen clinique et du contexte epidemiologique.",
            examens_complementaires=json.dumps(m["exams"], ensure_ascii=False),
            examens_complementaires_notes="",
            diagnostic=diag,
            diagnostic_differentiel=m["hypotheses"],
            pronostic=m["pronostic"],
            pronostic_justification="Pronostic etabli selon la gravite des signes et la reponse attendue au traitement.",
            traitement=m["traitement"],
            suivi="Reevaluation clinique programmee ; adaptation du traitement selon l'evolution.",
            resultat=random.choice(m["resultat"]),
            statut="publie" if publie else "brouillon",
            auteur_id=random.choice(auteurs),
        )
        cas.append(c)
    return cas


if __name__ == "__main__":
    from app import app, db, User
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    with app.app_context():
        auteurs = [u.id for u in User.query.filter(User.role.in_(("medecin", "enseignant", "admin"))).all()]
        if not auteurs:
            print("Aucun contributeur trouve. Lancez d'abord python init_db.py.")
            sys.exit(1)
        cas = generer(n, auteurs=auteurs)
        db.session.add_all(cas)
        db.session.commit()
        print(f"{len(cas)} cas generes et ajoutes.")
