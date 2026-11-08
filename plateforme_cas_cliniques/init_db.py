"""
Initialisation de la base de donnees MySQL.

Prerequis : avoir cree une base vide (ex. "cas_cliniques") dans phpMyAdmin,
puis lancer :  python init_db.py

Ce script cree les tables et insere des donnees de demonstration :
  - 3 utilisateurs (admin, enseignant, etudiant)
  - une liste d'especes de reference
  - 2 cas cliniques d'exemple
"""

from app import app, db, User, CasClinique, Espece
from werkzeug.security import generate_password_hash

ESPECES = [
    "Chien", "Chat", "Bovin", "Ovin", "Caprin",
    "Equin", "Volaille", "Lapin", "Porcin",
]

with app.app_context():
    print("Suppression des tables existantes…")
    db.drop_all()
    print("Creation des tables…")
    db.create_all()

    print("Ajout des especes de reference…")
    db.session.add_all([Espece(nom=nom) for nom in ESPECES])

    print("Ajout des utilisateurs…")
    admin = User(
        nom="Admin", prenom="Admin", email="admin@eismv.org",
        mot_de_passe=generate_password_hash("admin123"), role="admin",
    )
    enseignant = User(
        nom="Smith", prenom="John", email="john.smith@eismv.org",
        mot_de_passe=generate_password_hash("enseignant123"), role="enseignant",
    )
    medecin = User(
        nom="Ndiaye", prenom="Fatou", email="fatou.ndiaye@eismv.org",
        mot_de_passe=generate_password_hash("medecin123"), role="medecin",
    )
    etudiant = User(
        nom="Diop", prenom="Aminata", email="aminata.diop@eismv.org",
        mot_de_passe=generate_password_hash("etudiant123"), role="etudiant",
    )
    db.session.add_all([admin, enseignant, medecin, etudiant])
    db.session.flush()  # pour obtenir les identifiants

    print("Ajout des cas cliniques d'exemple…")
    db.session.add_all([
        CasClinique(
            titre="Chien boiteux",
            espece="Chien", race="Berger Allemand", age=3, sexe="M",
            motif_consultation="Boiterie du membre anterieur droit",
            anamnese_commemoratif="Apparue il y a 3 jours apres une chute",
            examen_distance_texte="Animal craintif, appui difficile sur le membre",
            examen_rapproche_texte="Douleur a la palpation du carpe, chaleur locale",
            suspicion="Entorse ou fracture du carpe",
            examen_complementaire_texte="Radiographie du carpe",
            diagnostic="Entorse du carpe",
            traitement_texte="Anti-inflammatoires + repos strict 2 semaines",
            resultat_suivi="Amelioration nette apres 10 jours",
            statut="publie", auteur_id=admin.id,
        ),
        CasClinique(
            titre="Chat anorexique",
            espece="Chat", race="Siamois", age=5, sexe="F",
            motif_consultation="Perte d'appetit depuis 5 jours",
            anamnese_commemoratif="Chat sterilise vivant en appartement",
            examen_distance_texte="Animal abattu, poil terne",
            examen_rapproche_texte="Douleur abdominale, ictere leger",
            suspicion="Lipidose hepatique",
            examen_complementaire_texte="Bilan sanguin hepatique, echographie",
            diagnostic="Lipidose hepatique confirmee",
            traitement_texte="Alimentation assistee + perfusion de glucose",
            resultat_suivi="Reprise alimentaire apres 7 jours",
            statut="publie", auteur_id=medecin.id,
        ),
    ])

    db.session.commit()

    print("\nBase initialisee avec succes !")
    print(f"  Especes : {Espece.query.count()}")
    print(f"  Users   : {User.query.count()}")
    print(f"  Cas     : {CasClinique.query.count()}")
    print("\nComptes de test :")
    print("  admin@eismv.org        / admin123      (admin)")
    print("  john.smith@eismv.org   / enseignant123 (enseignant)")
    print("  fatou.ndiaye@eismv.org / medecin123    (medecin traitant)")
    print("  aminata.diop@eismv.org / etudiant123   (etudiant)")
