# Plateforme de gestion et de partage des cas cliniques vétérinaires

Projet de thèse de doctorat vétérinaire — **EISMV de Dakar**.
Application web Flask permettant de documenter des cas cliniques selon une
démarche structurée, de les illustrer (images / vidéos), de rechercher des cas
similaires (aide au diagnostic) et d'exporter les données pour la recherche.

- **Backend** : Python / Flask + SQLAlchemy
- **Base de données** : MySQL / MariaDB (administrable via **phpMyAdmin**)
- **Frontend** : HTML, CSS, JavaScript (sans framework)
- **Authentification** : Flask-Login, mots de passe hachés, rôles (admin / enseignant / étudiant)

---

## 1. Prérequis

- Python 3.10 ou supérieur
- Un serveur MySQL / MariaDB avec phpMyAdmin (XAMPP, WAMP, Laragon, MAMP…)

## 2. Installation

```bash
# Se placer dans le dossier du projet
cd plateforme_cas_cliniques

# Créer et activer un environnement virtuel
python -m venv venv
# Windows :
venv\Scripts\activate
# macOS / Linux :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## 3. Créer la base de données dans phpMyAdmin

1. Démarrer MySQL (via XAMPP / WAMP / Laragon) puis ouvrir **phpMyAdmin**
   (`http://localhost/phpmyadmin`).
2. Onglet **Bases de données** → créer une base nommée **`cas_cliniques`**,
   en choisissant l'interclassement **`utf8mb4_unicode_ci`**.
3. Ne créez aucune table : elles seront générées automatiquement à l'étape 5.

> La base reste vide ; c'est l'application qui crée les tables
> (`user`, `cas_clinique`, `espece`).

## 4. Configurer la connexion

Copier le fichier d'exemple puis l'adapter :

```bash
cp .env.example .env
```

Dans `.env`, renseignez vos identifiants MySQL. Valeurs par défaut (installation
locale typique, utilisateur `root` sans mot de passe) :

```
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=cas_cliniques
SECRET_KEY=remplacez-par-une-cle-aleatoire
```

Pour générer une clé secrète robuste :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 5. Initialiser les tables et les données de démonstration

```bash
python init_db.py
```

Cela crée les tables et insère 4 comptes de test (un par rôle), 9 espèces et
génère environ **500 cas cliniques cohérents** pour l'aide au diagnostic
(comptez quelques secondes) :

| Rôle       | Email                    | Mot de passe   |
|------------|--------------------------|----------------|
| Admin      | admin@eismv.org          | admin123       |
| Enseignant | john.smith@eismv.org     | enseignant123  |
| Médecin    | fatou.ndiaye@eismv.org   | medecin123     |
| Étudiant   | aminata.diop@eismv.org   | etudiant123    |

> Changez ces mots de passe (ou supprimez ces comptes) avant toute mise en ligne.

## 6. Lancer l'application

```bash
python app.py
```

Ouvrir ensuite **http://127.0.0.1:5000**.

---

## Fonctionnalités

- **Inscription / connexion** avec rôles et mots de passe hachés.
- **Fiche clinique structurée en 10 étapes** (assistant guidé) : Identification →
  Motif & Anamnèse → Examen à distance → Examen rapproché → Suspicions cliniques →
  Examens complémentaires → Diagnostic → Pronostic → Traitements → Suivi. Les signes
  cliniques sont saisis via des listes normalisées (états, comportement, muqueuses…)
  et des cases à cocher (nœuds lymphatiques, examens complémentaires par système),
  avec ajout de plusieurs photos et vidéos par cas.
- **Aide au diagnostic (moteur local intelligent)** : à partir des signes saisis,
  un moteur TF-IDF + similarité cosinus « entraîné » sur les cas publiés retrouve
  les cas les plus proches **et agrège leurs diagnostics** en suggestions classées
  par score. Entièrement hors-ligne (aucune API, aucun accès Internet requis).
- **Base de démonstration** : `init_db.py` génère environ **500 cas cohérents**
  couvrant les pathologies fréquentes en Afrique de l'Ouest (parvovirose, babésiose,
  fièvre aphteuse, PPR, Newcastle, coccidiose, colique…), afin que l'aide au
  diagnostic dispose immédiatement d'une vraie base de travail.
- **Tout est dynamique** : les espèces sont stockées en base ; saisir une nouvelle
  espèce l'ajoute automatiquement à la liste réutilisable. Les statistiques de la
  page d'accueil et du tableau de bord sont calculées en temps réel depuis la base.
- **Export CSV** : le médecin et l'enseignant exportent leurs cas ; l'admin exporte tout.
- **CRUD complet** avec contrôle d'accès (un cas n'est modifiable/supprimable que
  par son auteur — médecin ou enseignant — ou par un admin).

## Aide au diagnostic : comment ça marche

Le moteur ne fait appel à aucun service externe. Il construit, à la volée, un index
TF-IDF (Term Frequency – Inverse Document Frequency) sur le texte clinique agrégé de
tous les cas publiés (motif, évolution, signes d'examen, hypothèses, examens
complémentaires). La requête de l'utilisateur (les signes observés) est vectorisée de
la même façon, puis comparée à chaque cas par **similarité cosinus**. Les cas les plus
proches sont affichés avec leur score, et leurs diagnostics sont agrégés (pondérés par
le score) pour proposer les hypothèses les plus probables. Plus la base contient de
cas, plus les suggestions sont pertinentes — d'où la génération des 500 cas.

Les suggestions sont fournies à titre indicatif et ne remplacent pas le jugement
clinique du praticien. Le code est structuré pour pouvoir brancher ultérieurement un
modèle de langage (LLM) en complément, si besoin.

## Rôles et permissions

À l'inscription, tout nouveau compte est **étudiant** par défaut. Un **administrateur**
peut ensuite faire évoluer ce rôle depuis le menu **Utilisateurs**.

| Action                                | Étudiant | Médecin | Enseignant | Admin |
|---------------------------------------|:--------:|:-------:|:----------:|:-----:|
| Consulter les cas **publiés**         |    ✅    |   ✅    |     ✅     |  ✅   |
| Ajouter un cas                        |    ❌    |   ✅    |     ✅     |  ✅   |
| Modifier / supprimer SES cas          |    ❌    |   ✅    |     ✅     |  ✅   |
| Modifier / supprimer les cas d'autrui |    ❌    |   ❌    |     ❌     |  ✅   |
| Exporter en CSV                       |    ❌    | (siens) |  (siens)   | (tous)|
| Gérer les utilisateurs et les rôles   |    ❌    |   ❌    |     ❌     |  ✅   |

- L'**étudiant** est en consultation seule : il parcourt le catalogue des cas
  publiés (menu **Consulter les cas**) et utilise l'aide au diagnostic, mais ne
  peut ni créer, ni modifier, ni supprimer, ni exporter. Les routes correspondantes
  lui renvoient un refus (403) même par accès direct à l'URL.
- Le **médecin traitant** et l'**enseignant** créent des cas et gèrent uniquement
  les leurs.
- L'**admin** a tous les droits sur tous les cas et gère les comptes.

- **Mon profil** (`/profil`) : chaque utilisateur modifie ses informations et son
  mot de passe (l'ancien mot de passe est exigé pour le changer).
- **Utilisateurs** (`/admin/utilisateurs`, admin uniquement) : liste des membres,
  attribution du rôle via menu déroulant, suppression d'un compte. Garde-fous :
  on ne peut pas supprimer son propre compte ni retirer le dernier administrateur ;
  supprimer un utilisateur supprime aussi ses cas (cascade).

## Sécurité mise en place

- Clé secrète et identifiants de base lus depuis l'environnement (jamais en dur).
- Mots de passe **hachés** (Werkzeug), jamais stockés en clair.
- **Protection CSRF** sur tous les formulaires POST (jeton de session).
- **Uploads sécurisés** : extensions vérifiées (images / vidéos uniquement),
  noms de fichiers assainis et rendus uniques, taille limitée à 50 Mo.
- **Contrôle d'accès** par rôle et par propriétaire (renvoi 403 si non autorisé).
- Cookies de session `HttpOnly` + `SameSite` (et `Secure` en production).
- Pages d'erreur dédiées (400 / 403 / 404 / 413 / 500).

## Déploiement en production

```bash
export FLASK_ENV=production
export SECRET_KEY="votre-cle-robuste"
# servir avec gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

En production : utiliser un mot de passe MySQL dédié (pas `root`), servir derrière
HTTPS (Nginx en reverse proxy), et conserver `FLASK_ENV=production` (désactive le
mode debug et active les cookies sécurisés).

## Structure du projet

```
plateforme_cas_cliniques/
├── app.py              # Application : modèles, routes, sécurité, recherche, export
├── config.py           # Configuration (dev / prod), connexion MySQL via .env
├── init_db.py          # Création des tables + données de démonstration
├── generate_data.py    # Générateur des ~500 cas cliniques (modèles de pathologies)
├── wsgi.py             # Point d'entrée production (gunicorn)
├── requirements.txt
├── .env.example        # Modèle de configuration (à copier en .env)
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── uploads/        # Images et vidéos des examens
└── templates/          # 11 gabarits HTML (base, accueil, auth, cas, recherche, erreur)
```
#   P l a t e f o r m e - c a s - c l i n i q u e s  
 