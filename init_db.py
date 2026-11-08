"""
Initialisation de la base MySQL.

Prerequis : base "cas_cliniques" creee dans phpMyAdmin.
Lancer :  python init_db.py

Cree les tables, 4 comptes (un par role), les especes de reference,
puis genere ~500 cas cliniques coherents pour l'aide au diagnostic.
"""

from app import app, db, User, CasClinique, Espece
from werkzeug.security import generate_password_hash
from generate_data import generer

ESPECES = ["Chien", "Chat", "Bovin", "Ovin", "Caprin", "Equin", "Volaille",
           "Lapin", "Porcin"]

NB_CAS = 500

with app.app_context():
    print("Suppression des tables existantes...")
    db.drop_all()
    print("Creation des tables...")
    db.create_all()

    print("Ajout des especes de reference...")
    db.session.add_all([Espece(nom=n) for n in ESPECES])

    print("Ajout des utilisateurs...")
    admin = User(nom="Admin", prenom="Admin", email="admin@eismv.org",
                 mot_de_passe=generate_password_hash("admin123"), role="admin")
    enseignant = User(nom="Smith", prenom="John", email="john.smith@eismv.org",
                      mot_de_passe=generate_password_hash("enseignant123"), role="enseignant")
    medecin = User(nom="Ndiaye", prenom="Fatou", email="fatou.ndiaye@eismv.org",
                   mot_de_passe=generate_password_hash("medecin123"), role="medecin")
    etudiant = User(nom="Diop", prenom="Aminata", email="aminata.diop@eismv.org",
                    mot_de_passe=generate_password_hash("etudiant123"), role="etudiant")
    db.session.add_all([admin, enseignant, medecin, etudiant])
    db.session.flush()

    print(f"Generation de {NB_CAS} cas cliniques (aide au diagnostic)...")
    auteurs = [admin.id, enseignant.id, medecin.id]
    cas = generer(NB_CAS, auteurs=auteurs, seed=42)
    db.session.add_all(cas)

    db.session.commit()

    print("\nBase initialisee avec succes !")
    print(f"  Especes : {Espece.query.count()}")
    print(f"  Users   : {User.query.count()}")
    print(f"  Cas     : {CasClinique.query.count()} "
          f"(publies : {CasClinique.query.filter_by(statut='publie').count()})")
    print("\nComptes de test :")
    print("  admin@eismv.org        / admin123      (admin)")
    print("  john.smith@eismv.org   / enseignant123 (enseignant)")
    print("  fatou.ndiaye@eismv.org / medecin123    (medecin traitant)")
    print("  aminata.diop@eismv.org / etudiant123   (etudiant)")
