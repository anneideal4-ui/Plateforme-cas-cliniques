"""
Plateforme de gestion et de partage des cas cliniques veterinaires.
EISMV de Dakar - These de doctorat veterinaire.

Application Flask complete :
  - Authentification (inscription, connexion, deconnexion) avec roles
  - Gestion CRUD des cas cliniques (modele clinique riche)
  - Upload securise d'images et de videos d'examens
  - Moteur de recherche par similarite (aide au diagnostic)
  - Export CSV pour la valorisation en recherche
  - Protection CSRF, controle d'acces par role et par proprietaire
"""

import os
import csv
import uuid
import functools
from io import StringIO

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    Response, abort, session, current_app,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import get_config

# ---------------------------------------------------------------------------
# Initialisation de l'application et des extensions
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(get_config())

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour acceder a cette page."
login_manager.login_message_category = "warning"


# ---------------------------------------------------------------------------
# Modeles
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="etudiant")
    date_inscription = db.Column(db.DateTime, default=db.func.current_timestamp())

    cas = db.relationship(
        "CasClinique", backref="auteur", lazy=True,
        cascade="all, delete-orphan",
    )

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class CasClinique(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Identification
    titre = db.Column(db.String(200), nullable=False)
    espece = db.Column(db.String(50), nullable=False)
    race = db.Column(db.String(50))
    age = db.Column(db.Integer)
    sexe = db.Column(db.String(10))

    # Demarche clinique
    motif_consultation = db.Column(db.Text, nullable=False)
    anamnese_commemoratif = db.Column(db.Text, nullable=False)

    examen_distance_texte = db.Column(db.Text, nullable=False)
    examen_distance_image = db.Column(db.String(255), nullable=False, default="")
    examen_distance_video = db.Column(db.String(255), nullable=False, default="")

    examen_rapproche_texte = db.Column(db.Text, nullable=False)
    examen_rapproche_image = db.Column(db.String(255), nullable=False, default="")
    examen_rapproche_video = db.Column(db.String(255), nullable=False, default="")

    examen_special_texte = db.Column(db.Text)
    examen_special_image = db.Column(db.String(255))
    examen_special_video = db.Column(db.String(255))

    suspicion = db.Column(db.Text, nullable=False)

    examen_complementaire_texte = db.Column(db.Text)
    examen_complementaire_image = db.Column(db.String(255))

    diagnostic = db.Column(db.Text)

    traitement_texte = db.Column(db.Text, nullable=False)
    traitement_image = db.Column(db.String(255), nullable=False, default="")

    resultat_suivi = db.Column(db.Text, nullable=False)

    statut = db.Column(db.String(20), default="brouillon")
    auteur_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    date_creation = db.Column(db.DateTime, default=db.func.current_timestamp())

    @property
    def corpus_recherche(self):
        """Texte agrege utilise par le moteur de similarite."""
        parties = [
            self.titre, self.motif_consultation, self.anamnese_commemoratif,
            self.examen_distance_texte, self.examen_rapproche_texte,
            self.examen_special_texte or "", self.suspicion,
            self.diagnostic or "",
        ]
        return " ".join(parties)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Espece(db.Model):
    """Table de reference des especes (alimentee dynamiquement)."""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(60), unique=True, nullable=False)


def obtenir_ou_creer_espece(nom):
    """Enregistre une nouvelle espece si elle n'existe pas encore."""
    nom = (nom or "").strip()
    if not nom:
        return
    existe = Espece.query.filter(db.func.lower(Espece.nom) == nom.lower()).first()
    if not existe:
        db.session.add(Espece(nom=nom))


@app.context_processor
def injecter_especes():
    """Rend la liste des especes disponible dans tous les templates."""
    try:
        noms = [e.nom for e in Espece.query.order_by(Espece.nom).all()]
    except Exception:
        noms = []
    return {"especes_disponibles": noms}


# ---------------------------------------------------------------------------
# Securite : protection CSRF (jeton de session injecte dans les formulaires)
# ---------------------------------------------------------------------------
def generer_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = uuid.uuid4().hex
    return session["_csrf_token"]


@app.context_processor
def injecter_csrf():
    return {"csrf_token": generer_csrf_token}


@app.before_request
def proteger_contre_csrf():
    if request.method == "POST":
        jeton_session = session.get("_csrf_token")
        jeton_formulaire = request.form.get("_csrf_token")
        if not jeton_session or jeton_session != jeton_formulaire:
            abort(400, description="Jeton CSRF invalide ou expire.")


# ---------------------------------------------------------------------------
# Securite : controle d'acces par role
# ---------------------------------------------------------------------------
# Roles disponibles et description des permissions associees.
ROLES = ["etudiant", "medecin", "enseignant", "admin"]
ROLES_DESCRIPTION = {
    "etudiant": "Consulte uniquement les cas publies.",
    "medecin": "Medecin traitant : ajoute des cas ; modifie, supprime et exporte uniquement les siens.",
    "enseignant": "Ajoute des cas ; modifie, supprime et exporte uniquement les siens.",
    "admin": "Tous les droits sur tous les cas + gestion des utilisateurs.",
}

# Roles autorises a creer / gerer des cas (l'etudiant en est exclu)
ROLES_CONTRIBUTEURS = ("medecin", "enseignant", "admin")


def role_requis(*roles):
    def decorateur(vue):
        @functools.wraps(vue)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return vue(*args, **kwargs)
        return wrapper
    return decorateur


def peut_creer():
    """Seuls medecins, enseignants et admins peuvent creer un cas."""
    return current_user.role in ROLES_CONTRIBUTEURS


def peut_modifier(cas):
    """Un cas est modifiable par son auteur (medecin/enseignant) ou par un admin."""
    if current_user.role == "admin":
        return True
    return (
        cas.auteur_id == current_user.id
        and current_user.role in ("medecin", "enseignant")
    )


def peut_voir(cas):
    """Visible si publie, ou par l'auteur, ou par un admin."""
    return (
        cas.statut == "publie"
        or cas.auteur_id == current_user.id
        or current_user.role == "admin"
    )


@app.context_processor
def injecter_permissions():
    """Expose les helpers de permission dans les templates."""
    if current_user.is_authenticated:
        return {"peut_creer": peut_creer(), "ROLES_CONTRIBUTEURS": ROLES_CONTRIBUTEURS}
    return {"peut_creer": False, "ROLES_CONTRIBUTEURS": ROLES_CONTRIBUTEURS}



# ---------------------------------------------------------------------------
# Uploads : sauvegarde securisee des fichiers
# ---------------------------------------------------------------------------
def _extension(nom_fichier):
    return nom_fichier.rsplit(".", 1)[-1].lower() if "." in nom_fichier else ""


def sauvegarder_fichier(champ, type_attendu):
    """
    Sauvegarde un fichier uploade et renvoie son chemin relatif a /static,
    ou une chaine vide si aucun fichier valide n'a ete fourni.

    type_attendu : "image" ou "video".
    """
    fichier = request.files.get(champ)
    if not fichier or fichier.filename == "":
        return ""

    ext = _extension(fichier.filename)
    if type_attendu == "image":
        autorisees = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
        sous_dossier = "img"
    else:
        autorisees = current_app.config["ALLOWED_VIDEO_EXTENSIONS"]
        sous_dossier = "video"

    if ext not in autorisees:
        flash(
            f"Format de fichier non autorise pour « {champ} » "
            f"(.{ext}). Fichier ignore.",
            "warning",
        )
        return ""

    nom_sur = secure_filename(fichier.filename)
    nom_unique = f"{uuid.uuid4().hex}_{nom_sur}"
    dossier = os.path.join(current_app.config["UPLOAD_FOLDER"], sous_dossier)
    os.makedirs(dossier, exist_ok=True)
    fichier.save(os.path.join(dossier, nom_unique))

    # Chemin relatif au dossier static (utilise par url_for('static', ...))
    return f"uploads/{sous_dossier}/{nom_unique}"


# ---------------------------------------------------------------------------
# Moteur de recherche par similarite
# ---------------------------------------------------------------------------
MOTS_VIDES = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "a",
    "au", "aux", "en", "dans", "sur", "avec", "sans", "pour", "par", "ce",
    "cette", "ces", "son", "sa", "ses", "il", "elle", "est", "depuis",
}


def _tokeniser(texte):
    if not texte:
        return set()
    for sep in [",", ";", ".", ":", "/", "(", ")", "-", "\n", "\t"]:
        texte = texte.replace(sep, " ")
    mots = {m.strip() for m in texte.lower().split() if len(m.strip()) > 2}
    return mots - MOTS_VIDES


def calculer_similarite(termes_recherche, corpus_cas):
    """Score de similarite entre 0 et 1 (proportion de termes retrouves)."""
    mots_recherche = _tokeniser(termes_recherche)
    mots_cas = _tokeniser(corpus_cas)
    if not mots_recherche or not mots_cas:
        return 0.0
    intersection = mots_recherche & mots_cas
    return round(len(intersection) / len(mots_recherche), 2)


# ---------------------------------------------------------------------------
# Routes : pages publiques
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    stats = {
        "cas": CasClinique.query.filter_by(statut="publie").count(),
        "especes": Espece.query.count(),
        "contributeurs": User.query.count(),
    }
    return render_template("index.html", stats=stats)


# ---------------------------------------------------------------------------
# Routes : authentification
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()
        email = request.form.get("email", "").strip().lower()
        mot_de_passe = request.form.get("mot_de_passe", "")
        confirmation = request.form.get("confirmation", "")

        if not all([nom, prenom, email, mot_de_passe]):
            flash("Tous les champs sont obligatoires.", "danger")
            return redirect(url_for("register"))

        if mot_de_passe != confirmation:
            flash("Les deux mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("register"))

        if len(mot_de_passe) < 6:
            flash("Le mot de passe doit contenir au moins 6 caracteres.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Cet email est deja utilise.", "danger")
            return redirect(url_for("register"))

        user = User(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe=generate_password_hash(mot_de_passe),
        )
        db.session.add(user)
        db.session.commit()
        flash("Inscription reussie. Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        mot_de_passe = request.form.get("mot_de_passe", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.mot_de_passe, mot_de_passe):
            login_user(user)
            flash(f"Bienvenue, {user.prenom} !", "success")
            suivant = request.args.get("next")
            # Redirection sure uniquement vers une URL interne
            if suivant and suivant.startswith("/"):
                return redirect(suivant)
            return redirect(url_for("dashboard"))

        flash("Email ou mot de passe incorrect.", "danger")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Vous avez ete deconnecte.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Routes : tableau de bord
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "etudiant":
        # L'etudiant ne possede pas de cas : on lui montre le catalogue public.
        stats = {
            "cas_publies": CasClinique.query.filter_by(statut="publie").count(),
            "especes": Espece.query.count(),
        }
        return render_template(
            "dashboard.html", user=current_user, stats=stats, recents=[]
        )

    mes_cas = CasClinique.query.filter_by(auteur_id=current_user.id)
    stats = {
        "total": mes_cas.count(),
        "publies": mes_cas.filter_by(statut="publie").count(),
        "brouillons": mes_cas.filter_by(statut="brouillon").count(),
    }
    if current_user.role == "admin":
        stats["total_plateforme"] = CasClinique.query.count()

    recents = (
        mes_cas.order_by(CasClinique.date_creation.desc()).limit(5).all()
    )
    return render_template(
        "dashboard.html", user=current_user, stats=stats, recents=recents
    )


# ---------------------------------------------------------------------------
# Routes : CRUD des cas cliniques
# ---------------------------------------------------------------------------
def _lire_champs_cas():
    """Lit les champs texte communs aux formulaires de creation / edition."""
    return {
        "titre": request.form.get("titre", "").strip(),
        "espece": request.form.get("espece", "").strip(),
        "race": request.form.get("race", "").strip(),
        "age": request.form.get("age") or None,
        "sexe": request.form.get("sexe", "").strip(),
        "motif_consultation": request.form.get("motif_consultation", "").strip(),
        "anamnese_commemoratif": request.form.get("anamnese_commemoratif", "").strip(),
        "examen_distance_texte": request.form.get("examen_distance_texte", "").strip(),
        "examen_rapproche_texte": request.form.get("examen_rapproche_texte", "").strip(),
        "examen_special_texte": request.form.get("examen_special_texte", "").strip(),
        "suspicion": request.form.get("suspicion", "").strip(),
        "examen_complementaire_texte": request.form.get("examen_complementaire_texte", "").strip(),
        "diagnostic": request.form.get("diagnostic", "").strip(),
        "traitement_texte": request.form.get("traitement_texte", "").strip(),
        "resultat_suivi": request.form.get("resultat_suivi", "").strip(),
        "statut": request.form.get("statut", "brouillon").strip(),
    }


CHAMPS_OBLIGATOIRES = {
    "titre": "Titre",
    "espece": "Espece",
    "motif_consultation": "Motif de consultation",
    "anamnese_commemoratif": "Anamnese / commemoratifs",
    "examen_distance_texte": "Examen a distance",
    "examen_rapproche_texte": "Examen rapproche",
    "suspicion": "Suspicion",
    "traitement_texte": "Traitement",
    "resultat_suivi": "Resultat / suivi",
}


def _valider_obligatoires(champs):
    manquants = [
        libelle for cle, libelle in CHAMPS_OBLIGATOIRES.items()
        if not champs.get(cle)
    ]
    return manquants


@app.route("/nouveau-cas", methods=["GET", "POST"])
@role_requis("medecin", "enseignant", "admin")
def nouveau_cas():
    if request.method == "POST":
        champs = _lire_champs_cas()
        manquants = _valider_obligatoires(champs)
        if manquants:
            flash("Champs obligatoires manquants : " + ", ".join(manquants), "danger")
            return render_template("nouveau_cas.html", form=champs)

        try:
            age = int(champs["age"]) if champs["age"] else None
        except ValueError:
            age = None

        cas = CasClinique(
            **{k: v for k, v in champs.items() if k != "age"},
            age=age,
            examen_distance_image=sauvegarder_fichier("examen_distance_image", "image"),
            examen_distance_video=sauvegarder_fichier("examen_distance_video", "video"),
            examen_rapproche_image=sauvegarder_fichier("examen_rapproche_image", "image"),
            examen_rapproche_video=sauvegarder_fichier("examen_rapproche_video", "video"),
            examen_special_image=sauvegarder_fichier("examen_special_image", "image"),
            examen_special_video=sauvegarder_fichier("examen_special_video", "video"),
            examen_complementaire_image=sauvegarder_fichier("examen_complementaire_image", "image"),
            traitement_image=sauvegarder_fichier("traitement_image", "image"),
            auteur_id=current_user.id,
        )
        db.session.add(cas)
        obtenir_ou_creer_espece(champs["espece"])
        db.session.commit()
        flash("Cas clinique enregistre avec succes.", "success")
        return redirect(url_for("detail_cas", id=cas.id))

    return render_template("nouveau_cas.html", form={})


@app.route("/mes-cas")
@role_requis("medecin", "enseignant", "admin")
def mes_cas():
    cas_liste = (
        CasClinique.query.filter_by(auteur_id=current_user.id)
        .order_by(CasClinique.date_creation.desc())
        .all()
    )
    return render_template("mes_cas.html", cas_liste=cas_liste)


@app.route("/cas")
@login_required
def consulter_cas():
    """Catalogue des cas publies, consultable par tous les utilisateurs."""
    espece_filtre = request.args.get("espece", "").strip()
    query = CasClinique.query.filter_by(statut="publie")
    if espece_filtre:
        query = query.filter_by(espece=espece_filtre)
    cas_liste = query.order_by(CasClinique.date_creation.desc()).all()
    especes = [e.nom for e in Espece.query.order_by(Espece.nom).all()]
    return render_template(
        "consulter_cas.html",
        cas_liste=cas_liste,
        especes=especes,
        espece_filtre=espece_filtre,
    )


@app.route("/cas/<int:id>")
@login_required
def detail_cas(id):
    cas = db.get_or_404(CasClinique, id)
    if not peut_voir(cas):
        abort(403)
    return render_template("detail_cas.html", cas=cas, peut_modifier=peut_modifier(cas))


@app.route("/cas/<int:id>/modifier", methods=["GET", "POST"])
@login_required
def modifier_cas(id):
    cas = db.get_or_404(CasClinique, id)
    if not peut_modifier(cas):
        abort(403)

    if request.method == "POST":
        champs = _lire_champs_cas()
        manquants = _valider_obligatoires(champs)
        if manquants:
            flash("Champs obligatoires manquants : " + ", ".join(manquants), "danger")
            return render_template("modifier_cas.html", cas=cas)

        for cle, valeur in champs.items():
            if cle == "age":
                continue
            setattr(cas, cle, valeur)
        try:
            cas.age = int(champs["age"]) if champs["age"] else None
        except ValueError:
            cas.age = None

        # On ne remplace un media que si un nouveau fichier est fourni
        for champ, type_ in [
            ("examen_distance_image", "image"),
            ("examen_distance_video", "video"),
            ("examen_rapproche_image", "image"),
            ("examen_rapproche_video", "video"),
            ("examen_special_image", "image"),
            ("examen_special_video", "video"),
            ("examen_complementaire_image", "image"),
            ("traitement_image", "image"),
        ]:
            nouveau = sauvegarder_fichier(champ, type_)
            if nouveau:
                setattr(cas, champ, nouveau)

        db.session.commit()
        obtenir_ou_creer_espece(champs["espece"])
        db.session.commit()
        flash("Cas clinique mis a jour.", "success")
        return redirect(url_for("detail_cas", id=cas.id))

    return render_template("modifier_cas.html", cas=cas)


@app.route("/cas/<int:id>/supprimer", methods=["POST"])
@login_required
def supprimer_cas(id):
    cas = db.get_or_404(CasClinique, id)
    if not peut_modifier(cas):
        abort(403)
    db.session.delete(cas)
    db.session.commit()
    flash("Cas clinique supprime.", "info")
    return redirect(url_for("mes_cas"))


# ---------------------------------------------------------------------------
# Route : aide au diagnostic (recherche par similarite)
# ---------------------------------------------------------------------------
@app.route("/recherche", methods=["GET", "POST"])
@login_required
def recherche():
    resultats = []
    termes = ""
    espece_filtre = ""

    if request.method == "POST":
        termes = request.form.get("termes", "").strip()
        espece_filtre = request.form.get("espece", "").strip()

        # On cherche parmi les cas publies + ses propres cas
        query = CasClinique.query.filter(
            db.or_(
                CasClinique.statut == "publie",
                CasClinique.auteur_id == current_user.id,
            )
        )
        if espece_filtre:
            query = query.filter_by(espece=espece_filtre)

        for cas in query.all():
            score = calculer_similarite(termes, cas.corpus_recherche)
            if score > 0:
                resultats.append({"cas": cas, "score": int(score * 100)})

        resultats.sort(key=lambda r: r["score"], reverse=True)
        resultats = resultats[:10]

    especes = [e.nom for e in Espece.query.order_by(Espece.nom).all()]
    return render_template(
        "recherche.html",
        resultats=resultats,
        termes=termes,
        espece_filtre=espece_filtre,
        especes=especes,
    )


# ---------------------------------------------------------------------------
# Route : export CSV
# ---------------------------------------------------------------------------
@app.route("/export-csv")
@role_requis("medecin", "enseignant", "admin")
def export_csv():
    if current_user.role == "admin":
        cas_liste = CasClinique.query.all()
    else:
        cas_liste = CasClinique.query.filter_by(auteur_id=current_user.id).all()

    output = StringIO()
    output.write("\ufeff")  # BOM pour une ouverture correcte dans Excel
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "ID", "Titre", "Espece", "Race", "Age", "Sexe",
        "Motif", "Anamnese", "Examen a distance", "Examen rapproche",
        "Examen special", "Suspicion", "Examen complementaire",
        "Diagnostic", "Traitement", "Resultat / suivi", "Statut", "Auteur",
    ])
    for c in cas_liste:
        writer.writerow([
            c.id, c.titre, c.espece, c.race or "", c.age or "", c.sexe or "",
            c.motif_consultation, c.anamnese_commemoratif,
            c.examen_distance_texte, c.examen_rapproche_texte,
            c.examen_special_texte or "", c.suspicion,
            c.examen_complementaire_texte or "", c.diagnostic or "",
            c.traitement_texte, c.resultat_suivi, c.statut,
            c.auteur.nom_complet if c.auteur else "",
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=cas_cliniques.csv"},
    )


# ---------------------------------------------------------------------------
# Route : profil de l'utilisateur connecte
# ---------------------------------------------------------------------------
@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "infos":
            nom = request.form.get("nom", "").strip()
            prenom = request.form.get("prenom", "").strip()
            email = request.form.get("email", "").strip().lower()

            if not all([nom, prenom, email]):
                flash("Tous les champs sont obligatoires.", "danger")
                return redirect(url_for("profil"))

            doublon = User.query.filter(User.email == email, User.id != current_user.id).first()
            if doublon:
                flash("Cet email est deja utilise par un autre compte.", "danger")
                return redirect(url_for("profil"))

            current_user.nom = nom
            current_user.prenom = prenom
            current_user.email = email
            db.session.commit()
            flash("Profil mis a jour.", "success")

        elif action == "mot_de_passe":
            actuel = request.form.get("mdp_actuel", "")
            nouveau = request.form.get("mdp_nouveau", "")
            confirme = request.form.get("mdp_confirme", "")

            if not check_password_hash(current_user.mot_de_passe, actuel):
                flash("Mot de passe actuel incorrect.", "danger")
            elif len(nouveau) < 6:
                flash("Le nouveau mot de passe doit contenir au moins 6 caracteres.", "danger")
            elif nouveau != confirme:
                flash("Les deux nouveaux mots de passe ne correspondent pas.", "danger")
            else:
                current_user.mot_de_passe = generate_password_hash(nouveau)
                db.session.commit()
                flash("Mot de passe modifie.", "success")

        return redirect(url_for("profil"))

    return render_template("profil.html")


# ---------------------------------------------------------------------------
# Routes : administration des utilisateurs (admin uniquement)
# ---------------------------------------------------------------------------
@app.route("/admin/utilisateurs")
@role_requis("admin")
def admin_utilisateurs():
    utilisateurs = User.query.order_by(User.role, User.nom).all()
    nb_admins = User.query.filter_by(role="admin").count()
    return render_template(
        "admin_utilisateurs.html",
        utilisateurs=utilisateurs,
        roles=ROLES,
        roles_description=ROLES_DESCRIPTION,
        nb_admins=nb_admins,
    )


@app.route("/admin/utilisateurs/<int:id>/role", methods=["POST"])
@role_requis("admin")
def admin_changer_role(id):
    user = db.get_or_404(User, id)
    nouveau_role = request.form.get("role", "")

    if nouveau_role not in ROLES:
        flash("Role invalide.", "danger")
        return redirect(url_for("admin_utilisateurs"))

    # Empeche de retirer le dernier administrateur
    if user.role == "admin" and nouveau_role != "admin":
        if User.query.filter_by(role="admin").count() <= 1:
            flash("Impossible : il doit rester au moins un administrateur.", "danger")
            return redirect(url_for("admin_utilisateurs"))

    user.role = nouveau_role
    db.session.commit()
    flash(f"Role de {user.nom_complet} mis a jour : {nouveau_role}.", "success")
    return redirect(url_for("admin_utilisateurs"))


@app.route("/admin/utilisateurs/<int:id>/supprimer", methods=["POST"])
@role_requis("admin")
def admin_supprimer_utilisateur(id):
    user = db.get_or_404(User, id)

    if user.id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for("admin_utilisateurs"))

    if user.role == "admin" and User.query.filter_by(role="admin").count() <= 1:
        flash("Impossible : il doit rester au moins un administrateur.", "danger")
        return redirect(url_for("admin_utilisateurs"))

    db.session.delete(user)  # supprime aussi ses cas (cascade)
    db.session.commit()
    flash(f"Compte de {user.nom_complet} supprime.", "info")
    return redirect(url_for("admin_utilisateurs"))


# ---------------------------------------------------------------------------
# Gestion des erreurs
# ---------------------------------------------------------------------------
@app.errorhandler(400)
def err_400(e):
    return render_template("erreur.html", code=400,
                           message="Requete invalide."), 400


@app.errorhandler(403)
def err_403(e):
    return render_template("erreur.html", code=403,
                           message="Vous n'avez pas l'autorisation d'acceder a cette ressource."), 403


@app.errorhandler(404)
def err_404(e):
    return render_template("erreur.html", code=404,
                           message="La page demandee est introuvable."), 404


@app.errorhandler(413)
def err_413(e):
    return render_template("erreur.html", code=413,
                           message="Fichier trop volumineux (50 Mo maximum)."), 413


@app.errorhandler(500)
def err_500(e):
    return render_template("erreur.html", code=500,
                           message="Une erreur interne est survenue."), 500


# ---------------------------------------------------------------------------
# Point d'entree (developpement uniquement)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get("DEBUG", False))
