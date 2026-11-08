"""
Plateforme de gestion et de partage des cas cliniques veterinaires - EISMV.

Fiche clinique structuree en 10 etapes, moteur d'aide au diagnostic local
(TF-IDF + similarite cosinus, entraine sur la base), authentification a roles,
uploads multiples (images/videos), export CSV.
"""

import os
import csv
import json
import uuid
import math
import functools
from io import StringIO
from datetime import date, datetime
from collections import Counter, defaultdict

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

app = Flask(__name__)
app.config.from_object(get_config())

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour acceder a cette page."
login_manager.login_message_category = "warning"


# ===========================================================================
# Modeles
# ===========================================================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="etudiant")
    date_inscription = db.Column(db.DateTime, default=db.func.current_timestamp())

    cas = db.relationship("CasClinique", backref="auteur", lazy=True,
                          cascade="all, delete-orphan")

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class Espece(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(60), unique=True, nullable=False)


class CasClinique(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # --- Etape 1 : Identification ---
    date_consultation = db.Column(db.Date, default=date.today)
    titre = db.Column(db.String(200), nullable=False)
    proprietaire_nom = db.Column(db.String(150))
    proprietaire_telephone = db.Column(db.String(50))
    proprietaire_adresse = db.Column(db.String(255))
    animal_nom = db.Column(db.String(100))
    espece = db.Column(db.String(60), nullable=False)
    race = db.Column(db.String(80))
    age = db.Column(db.Float)
    sexe = db.Column(db.String(10))
    poids = db.Column(db.Float)
    robe = db.Column(db.String(80))

    # --- Etape 2 : Motif & anamnese ---
    motif_consultation = db.Column(db.Text, nullable=False)
    alimentation = db.Column(db.String(255))
    mode_vie = db.Column(db.String(30))
    vaccination = db.Column(db.String(30))
    vaccination_detail = db.Column(db.String(255))
    vermifugation = db.Column(db.String(30))
    vermifugation_detail = db.Column(db.String(255))
    contact_animaux = db.Column(db.String(10))
    evolution_signes = db.Column(db.String(30))
    traitements_anterieurs = db.Column(db.Text)

    # --- Etape 3 : Examen a distance ---
    etat_conscience = db.Column(db.String(30))
    comportement = db.Column(db.String(40))
    posture = db.Column(db.String(40))
    demarche = db.Column(db.String(50))
    nec = db.Column(db.String(30))
    pelage = db.Column(db.String(40))
    jetage = db.Column(db.String(40))
    respiration_type = db.Column(db.String(40))
    ptyalisme = db.Column(db.String(30))
    examen_distance_autres = db.Column(db.Text)

    # --- Etape 4 : Examen rapproche ---
    temperature = db.Column(db.Float)
    pouls = db.Column(db.String(50))
    frequence_respiratoire = db.Column(db.String(50))
    muqueuse_couleur = db.Column(db.String(40))
    muqueuse_humidite = db.Column(db.String(40))
    pli_peau = db.Column(db.String(40))
    noeuds_lymphatiques = db.Column(db.Text)          # JSON (liste)
    auscultation_cardiaque = db.Column(db.String(255))
    auscultation_pulmonaire = db.Column(db.String(255))
    auscultation_digestive = db.Column(db.String(255))
    examen_rapproche_autres = db.Column(db.Text)
    photos = db.Column(db.Text)                        # JSON (liste de chemins)
    videos = db.Column(db.Text)                        # JSON (liste de chemins)

    # --- Etape 5 : Suspicions ---
    hypotheses_diagnostiques = db.Column(db.Text, nullable=False)
    raisonnement_clinique = db.Column(db.Text)

    # --- Etape 6 : Examens complementaires ---
    examens_complementaires = db.Column(db.Text)       # JSON (liste)
    examens_complementaires_notes = db.Column(db.Text)

    # --- Etape 7 : Diagnostic ---
    diagnostic = db.Column(db.String(255))
    diagnostic_differentiel = db.Column(db.Text)

    # --- Etape 8 : Pronostic ---
    pronostic = db.Column(db.String(30))
    pronostic_justification = db.Column(db.Text)

    # --- Etape 9 : Traitements ---
    traitement = db.Column(db.Text)

    # --- Etape 10 : Suivi ---
    suivi = db.Column(db.Text)
    resultat = db.Column(db.String(40))

    # --- Meta ---
    statut = db.Column(db.String(20), default="brouillon")
    auteur_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    date_creation = db.Column(db.DateTime, default=db.func.current_timestamp())

    # ---- Helpers d'affichage / recherche ----
    def liste(self, champ):
        """Renvoie une liste Python a partir d'un champ JSON."""
        val = getattr(self, champ)
        if not val:
            return []
        try:
            data = json.loads(val)
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @property
    def corpus_diagnostic(self):
        """Texte agrege des signes cliniques, utilise par le moteur."""
        parties = [
            self.motif_consultation, self.evolution_signes,
            self.comportement, self.posture, self.demarche, self.pelage,
            self.jetage, self.respiration_type, self.ptyalisme,
            self.examen_distance_autres,
            self.muqueuse_couleur, self.muqueuse_humidite, self.pli_peau,
            self.auscultation_cardiaque, self.auscultation_pulmonaire,
            self.auscultation_digestive, self.examen_rapproche_autres,
            self.hypotheses_diagnostiques,
            " ".join(self.liste("noeuds_lymphatiques")),
            " ".join(self.liste("examens_complementaires")),
        ]
        return " ".join(p for p in parties if p)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def obtenir_ou_creer_espece(nom):
    nom = (nom or "").strip()
    if not nom:
        return
    existe = Espece.query.filter(db.func.lower(Espece.nom) == nom.lower()).first()
    if not existe:
        db.session.add(Espece(nom=nom))


@app.context_processor
def injecter_globaux():
    especes = []
    try:
        especes = [e.nom for e in Espece.query.order_by(Espece.nom).all()]
    except Exception:
        pass
    return {
        "especes_disponibles": especes,
        "peut_creer": (current_user.is_authenticated and current_user.role in ROLES_CONTRIBUTEURS),
    }


@app.template_filter("fromjson")
def _fromjson(val):
    if not val:
        return []
    try:
        data = json.loads(val)
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


# ===========================================================================
# Securite : CSRF
# ===========================================================================
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


# ===========================================================================
# Securite : roles et permissions
# ===========================================================================
ROLES = ["etudiant", "medecin", "enseignant", "admin"]
ROLES_DESCRIPTION = {
    "etudiant": "Consulte uniquement les cas publies.",
    "medecin": "Medecin traitant : ajoute des cas ; modifie, supprime et exporte uniquement les siens.",
    "enseignant": "Ajoute des cas ; modifie, supprime et exporte uniquement les siens.",
    "admin": "Tous les droits sur tous les cas + gestion des utilisateurs.",
}
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


def peut_modifier(cas):
    if current_user.role == "admin":
        return True
    return (cas.auteur_id == current_user.id
            and current_user.role in ("medecin", "enseignant"))


def peut_voir(cas):
    return (cas.statut == "publie"
            or cas.auteur_id == current_user.id
            or current_user.role == "admin")


# ===========================================================================
# Uploads (images / videos, potentiellement multiples)
# ===========================================================================
def _extension(nom):
    return nom.rsplit(".", 1)[-1].lower() if "." in nom else ""


def _sauver_un(fichier, type_attendu):
    ext = _extension(fichier.filename)
    if type_attendu == "image":
        autorisees = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
        sous = "img"
    else:
        autorisees = current_app.config["ALLOWED_VIDEO_EXTENSIONS"]
        sous = "video"
    if ext not in autorisees:
        return None
    nom_unique = f"{uuid.uuid4().hex}_{secure_filename(fichier.filename)}"
    dossier = os.path.join(current_app.config["UPLOAD_FOLDER"], sous)
    os.makedirs(dossier, exist_ok=True)
    fichier.save(os.path.join(dossier, nom_unique))
    return f"uploads/{sous}/{nom_unique}"


def sauvegarder_fichiers(champ, type_attendu):
    """Sauvegarde tous les fichiers d'un champ multiple. Renvoie une liste de chemins."""
    chemins = []
    for fichier in request.files.getlist(champ):
        if fichier and fichier.filename:
            chemin = _sauver_un(fichier, type_attendu)
            if chemin:
                chemins.append(chemin)
    return chemins


# ===========================================================================
# Moteur d'aide au diagnostic : TF-IDF + cosinus (hors-ligne, sur la base)
# ===========================================================================
MOTS_VIDES = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "a", "au",
    "aux", "en", "dans", "sur", "avec", "sans", "pour", "par", "ce", "cette",
    "ces", "son", "sa", "ses", "il", "elle", "est", "depuis", "plus", "tres",
    "peu", "pas", "non", "oui", "chez", "que", "qui", "aux", "leur", "vers",
}


def tokeniser(texte):
    if not texte:
        return []
    for sep in [",", ";", ".", ":", "/", "(", ")", "-", "\n", "\t", "'", "\""]:
        texte = texte.replace(sep, " ")
    return [m for m in texte.lower().split() if len(m) > 2 and m not in MOTS_VIDES]


def construire_index(cas_list):
    """Construit l'index TF-IDF a partir d'une liste de cas."""
    docs = {}
    df = Counter()
    for c in cas_list:
        toks = tokeniser(c.corpus_diagnostic)
        if not toks:
            continue
        tf = Counter(toks)
        docs[c.id] = tf
        for terme in tf:
            df[terme] += 1
    n = max(len(docs), 1)
    idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
    # Vecteurs TF-IDF normalises
    vecteurs = {}
    for cid, tf in docs.items():
        total = sum(tf.values())
        vec = {t: (c / total) * idf.get(t, 0) for t, c in tf.items()}
        norme = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vecteurs[cid] = ({t: v / norme for t, v in vec.items()})
    return {"idf": idf, "vecteurs": vecteurs}


def vectoriser_requete(texte, idf):
    tf = Counter(tokeniser(texte))
    if not tf:
        return {}
    total = sum(tf.values())
    vec = {t: (c / total) * idf.get(t, 0) for t, c in tf.items()}
    norme = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norme for t, v in vec.items()}


def cosinus(v1, v2):
    if len(v1) > len(v2):
        v1, v2 = v2, v1
    return sum(poids * v2.get(t, 0) for t, poids in v1.items())


def aide_au_diagnostic(termes, espece_filtre="", top=8):
    """Renvoie (resultats_cas, suggestions_diagnostics)."""
    query = CasClinique.query.filter(
        db.or_(CasClinique.statut == "publie",
               CasClinique.auteur_id == current_user.id)
    )
    if espece_filtre:
        query = query.filter_by(espece=espece_filtre)
    cas_list = query.all()
    if not cas_list:
        return [], []

    index = construire_index(cas_list)
    q = vectoriser_requete(termes, index["idf"])
    if not q:
        return [], []

    scores = []
    par_id = {c.id: c for c in cas_list}
    for cid, vec in index["vecteurs"].items():
        s = cosinus(q, vec)
        if s > 0:
            scores.append((par_id[cid], s))
    scores.sort(key=lambda x: x[1], reverse=True)
    scores = scores[:top]

    resultats = [{"cas": c, "score": int(round(s * 100))} for c, s in scores]

    # Agregation des diagnostics parmi les cas proches (ponderee par le score)
    poids_diag = defaultdict(float)
    for c, s in scores:
        diag = (c.diagnostic or "").strip()
        if diag:
            poids_diag[diag] += s
    total_poids = sum(poids_diag.values()) or 1.0
    suggestions = sorted(
        ({"diagnostic": d, "score": int(round(p / total_poids * 100)),
          "occurrences": sum(1 for c, _ in scores if (c.diagnostic or "").strip() == d)}
         for d, p in poids_diag.items()),
        key=lambda x: x["score"], reverse=True,
    )[:5]
    return resultats, suggestions


# ===========================================================================
# Pages publiques & authentification
# ===========================================================================
@app.route("/")
def index():
    stats = {
        "cas": CasClinique.query.filter_by(statut="publie").count(),
        "especes": Espece.query.count(),
        "contributeurs": User.query.count(),
    }
    return render_template("index.html", stats=stats)


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
        user = User(nom=nom, prenom=prenom, email=email,
                    mot_de_passe=generate_password_hash(mot_de_passe))
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


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "etudiant":
        stats = {
            "cas_publies": CasClinique.query.filter_by(statut="publie").count(),
            "especes": Espece.query.count(),
        }
        return render_template("dashboard.html", user=current_user, stats=stats, recents=[])
    mes = CasClinique.query.filter_by(auteur_id=current_user.id)
    stats = {
        "total": mes.count(),
        "publies": mes.filter_by(statut="publie").count(),
        "brouillons": mes.filter_by(statut="brouillon").count(),
    }
    if current_user.role == "admin":
        stats["total_plateforme"] = CasClinique.query.count()
    recents = mes.order_by(CasClinique.date_creation.desc()).limit(5).all()
    return render_template("dashboard.html", user=current_user, stats=stats, recents=recents)


# ===========================================================================
# CRUD des cas cliniques (fiche en 10 etapes)
# ===========================================================================
CHAMPS_TEXTE = [
    "titre", "proprietaire_nom", "proprietaire_telephone", "proprietaire_adresse",
    "animal_nom", "espece", "race", "sexe", "robe",
    "motif_consultation", "alimentation", "mode_vie", "vaccination",
    "vaccination_detail", "vermifugation", "vermifugation_detail",
    "contact_animaux", "evolution_signes", "traitements_anterieurs",
    "etat_conscience", "comportement", "posture", "demarche", "nec", "pelage",
    "jetage", "respiration_type", "ptyalisme", "examen_distance_autres",
    "pouls", "frequence_respiratoire", "muqueuse_couleur", "muqueuse_humidite",
    "pli_peau", "auscultation_cardiaque", "auscultation_pulmonaire",
    "auscultation_digestive", "examen_rapproche_autres",
    "hypotheses_diagnostiques", "raisonnement_clinique",
    "examens_complementaires_notes", "diagnostic", "diagnostic_differentiel",
    "pronostic", "pronostic_justification", "traitement", "suivi", "resultat",
]
CHAMPS_NUM = ["age", "poids", "temperature"]
CHAMPS_OBLIGATOIRES = {
    "titre": "Titre du cas",
    "espece": "Espece",
    "motif_consultation": "Motif de consultation",
    "hypotheses_diagnostiques": "Suspicions cliniques",
}


def _lire_formulaire():
    d = {c: request.form.get(c, "").strip() for c in CHAMPS_TEXTE}
    for c in CHAMPS_NUM:
        val = request.form.get(c, "").strip().replace(",", ".")
        try:
            d[c] = float(val) if val else None
        except ValueError:
            d[c] = None
    dc = request.form.get("date_consultation", "").strip()
    try:
        d["date_consultation"] = datetime.strptime(dc, "%Y-%m-%d").date() if dc else date.today()
    except ValueError:
        d["date_consultation"] = date.today()
    d["noeuds_lymphatiques"] = json.dumps(request.form.getlist("noeuds_lymphatiques"), ensure_ascii=False)
    d["examens_complementaires"] = json.dumps(request.form.getlist("examens_complementaires"), ensure_ascii=False)
    d["statut"] = "publie" if request.form.get("statut") == "publie" else "brouillon"
    return d


def _valider(d):
    return [lib for cle, lib in CHAMPS_OBLIGATOIRES.items() if not d.get(cle)]


def _num_str(v):
    if v is None:
        return ""
    return str(int(v)) if float(v).is_integer() else str(v)


def _valeurs_depuis_cas(cas):
    d = {c: (getattr(cas, c) or "") for c in CHAMPS_TEXTE}
    for c in CHAMPS_NUM:
        d[c] = _num_str(getattr(cas, c))
    d["date_consultation"] = cas.date_consultation.isoformat() if cas.date_consultation else ""
    d["statut"] = cas.statut or "brouillon"
    return d


def _contexte_formulaire_post():
    return {
        "f": request.form.to_dict(),
        "noeuds": request.form.getlist("noeuds_lymphatiques"),
        "exams": request.form.getlist("examens_complementaires"),
    }


@app.route("/nouveau-cas", methods=["GET", "POST"])
@role_requis("medecin", "enseignant", "admin")
def nouveau_cas():
    if request.method == "POST":
        d = _lire_formulaire()
        manquants = _valider(d)
        if manquants:
            flash("Champs obligatoires manquants : " + ", ".join(manquants), "danger")
            return render_template("nouveau_cas.html", photos=[], videos=[],
                                   **_contexte_formulaire_post())
        cas = CasClinique(**d, auteur_id=current_user.id)
        cas.photos = json.dumps(sauvegarder_fichiers("photos", "image"), ensure_ascii=False)
        cas.videos = json.dumps(sauvegarder_fichiers("videos", "video"), ensure_ascii=False)
        db.session.add(cas)
        obtenir_ou_creer_espece(d["espece"])
        db.session.commit()
        flash("Cas clinique enregistre avec succes.", "success")
        return redirect(url_for("detail_cas", id=cas.id))
    return render_template("nouveau_cas.html", f={}, noeuds=[], exams=[], photos=[], videos=[])


@app.route("/mes-cas")
@role_requis("medecin", "enseignant", "admin")
def mes_cas():
    cas_liste = (CasClinique.query.filter_by(auteur_id=current_user.id)
                 .order_by(CasClinique.date_creation.desc()).all())
    return render_template("mes_cas.html", cas_liste=cas_liste)


@app.route("/cas")
@login_required
def consulter_cas():
    espece_filtre = request.args.get("espece", "").strip()
    query = CasClinique.query.filter_by(statut="publie")
    if espece_filtre:
        query = query.filter_by(espece=espece_filtre)
    cas_liste = query.order_by(CasClinique.date_creation.desc()).all()
    especes = [e.nom for e in Espece.query.order_by(Espece.nom).all()]
    return render_template("consulter_cas.html", cas_liste=cas_liste,
                           especes=especes, espece_filtre=espece_filtre)


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
        d = _lire_formulaire()
        manquants = _valider(d)
        if manquants:
            flash("Champs obligatoires manquants : " + ", ".join(manquants), "danger")
            return render_template("modifier_cas.html", cas=cas, photos=cas.liste("photos"),
                                   videos=cas.liste("videos"), **_contexte_formulaire_post())
        for cle, val in d.items():
            setattr(cas, cle, val)
        nouvelles_photos = sauvegarder_fichiers("photos", "image")
        nouvelles_videos = sauvegarder_fichiers("videos", "video")
        if nouvelles_photos:
            cas.photos = json.dumps(cas.liste("photos") + nouvelles_photos, ensure_ascii=False)
        if nouvelles_videos:
            cas.videos = json.dumps(cas.liste("videos") + nouvelles_videos, ensure_ascii=False)
        obtenir_ou_creer_espece(d["espece"])
        db.session.commit()
        flash("Cas clinique mis a jour.", "success")
        return redirect(url_for("detail_cas", id=cas.id))
    return render_template("modifier_cas.html", cas=cas,
                           f=_valeurs_depuis_cas(cas),
                           noeuds=cas.liste("noeuds_lymphatiques"),
                           exams=cas.liste("examens_complementaires"),
                           photos=cas.liste("photos"), videos=cas.liste("videos"))


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


# ===========================================================================
# Aide au diagnostic
# ===========================================================================
@app.route("/recherche", methods=["GET", "POST"])
@login_required
def recherche():
    resultats, suggestions, termes, espece_filtre = [], [], "", ""
    if request.method == "POST":
        termes = request.form.get("termes", "").strip()
        espece_filtre = request.form.get("espece", "").strip()
        if termes:
            resultats, suggestions = aide_au_diagnostic(termes, espece_filtre)
    especes = [e.nom for e in Espece.query.order_by(Espece.nom).all()]
    return render_template("recherche.html", resultats=resultats,
                           suggestions=suggestions, termes=termes,
                           espece_filtre=espece_filtre, especes=especes)


# ===========================================================================
# Export CSV
# ===========================================================================
@app.route("/export-csv")
@role_requis("medecin", "enseignant", "admin")
def export_csv():
    if current_user.role == "admin":
        cas_liste = CasClinique.query.all()
    else:
        cas_liste = CasClinique.query.filter_by(auteur_id=current_user.id).all()
    output = StringIO()
    output.write("\ufeff")
    w = csv.writer(output, delimiter=";")
    w.writerow(["ID", "Date", "Titre", "Espece", "Race", "Age", "Sexe", "Poids",
                "Motif", "Evolution", "Suspicions", "Examens complementaires",
                "Diagnostic", "Pronostic", "Traitement", "Resultat", "Statut", "Auteur"])
    for c in cas_liste:
        w.writerow([
            c.id, c.date_consultation or "", c.titre, c.espece, c.race or "",
            c.age or "", c.sexe or "", c.poids or "",
            c.motif_consultation, c.evolution_signes or "",
            c.hypotheses_diagnostiques, " | ".join(c.liste("examens_complementaires")),
            c.diagnostic or "", c.pronostic or "", (c.traitement or "")[:500],
            c.resultat or "", c.statut, c.auteur.nom_complet if c.auteur else "",
        ])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=cas_cliniques.csv"})


# ===========================================================================
# Profil
# ===========================================================================
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
            current_user.nom, current_user.prenom, current_user.email = nom, prenom, email
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


# ===========================================================================
# Administration des utilisateurs
# ===========================================================================
@app.route("/admin/utilisateurs")
@role_requis("admin")
def admin_utilisateurs():
    utilisateurs = User.query.order_by(User.role, User.nom).all()
    nb_admins = User.query.filter_by(role="admin").count()
    return render_template("admin_utilisateurs.html", utilisateurs=utilisateurs,
                           roles=ROLES, roles_description=ROLES_DESCRIPTION, nb_admins=nb_admins)


@app.route("/admin/utilisateurs/<int:id>/role", methods=["POST"])
@role_requis("admin")
def admin_changer_role(id):
    user = db.get_or_404(User, id)
    nouveau_role = request.form.get("role", "")
    if nouveau_role not in ROLES:
        flash("Role invalide.", "danger")
        return redirect(url_for("admin_utilisateurs"))
    if user.role == "admin" and nouveau_role != "admin" and User.query.filter_by(role="admin").count() <= 1:
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
    db.session.delete(user)
    db.session.commit()
    flash(f"Compte de {user.nom_complet} supprime.", "info")
    return redirect(url_for("admin_utilisateurs"))


# ===========================================================================
# Erreurs
# ===========================================================================
@app.errorhandler(400)
def err_400(e):
    return render_template("erreur.html", code=400, message="Requete invalide."), 400


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get("DEBUG", False))
