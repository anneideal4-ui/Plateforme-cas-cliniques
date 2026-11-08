# Déploiement gratuit sur PythonAnywhere (test en ligne)

Ce guide met la plateforme en ligne gratuitement, en base **SQLite**
(le MySQL gratuit n'est plus proposé aux nouveaux comptes PythonAnywhere).
Aucune modification du code n'est nécessaire.

Remplacez partout `VOTRE_USER` par votre nom d'utilisateur PythonAnywhere.

## 1. Créer un compte
Aller sur https://www.pythonanywhere.com → « Pricing & signup » →
« Create a Beginner account » (gratuit, sans carte). Confirmer l'email.

## 2. Envoyer le projet
Onglet **Files** → en haut à droite « Upload a file » → envoyer
`plateforme_cas_cliniques.zip`.

## 3. Console Bash : décompresser et installer
Onglet **Consoles** → « Bash ». Puis :

```bash
unzip plateforme_cas_cliniques.zip
cd plateforme_cas_cliniques
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Créer la base SQLite + les 500 cas
Toujours dans la même console :

```bash
export DATABASE_URL="sqlite:////home/VOTRE_USER/plateforme_cas_cliniques/database.db"
export SECRET_KEY="mettez-une-cle-longue-et-aleatoire"
export FLASK_ENV=production
python init_db.py
```
(Message attendu : « Base initialisee avec succes ! ... Cas : 500 ».)

## 5. Créer l'application web
Onglet **Web** → « Add a new web app » → « Next » →
choisir **Manual configuration** (surtout pas « Flask ») →
choisir **Python 3.10** → « Next ».

## 6. Indiquer le virtualenv
Sur la page Web, section **Virtualenv**, saisir :
```
/home/VOTRE_USER/plateforme_cas_cliniques/venv
```

## 7. Configurer le fichier WSGI
Section **Code** → cliquer sur le lien du fichier WSGI
(`/var/www/VOTRE_USER_pythonanywhere_com_wsgi.py`).
**Tout effacer** et coller ceci (adapter VOTRE_USER et la clé) :

```python
import os
import sys

path = "/home/VOTRE_USER/plateforme_cas_cliniques"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["FLASK_ENV"] = "production"
os.environ["SECRET_KEY"] = "mettez-la-meme-cle-qu-a-l-etape-4"
os.environ["DATABASE_URL"] = "sqlite:////home/VOTRE_USER/plateforme_cas_cliniques/database.db"

from app import app as application
```
Enregistrer (Save).

## 8. (Optionnel) Servir les fichiers statiques plus vite
Section **Static files** :
- URL : `/static/`
- Directory : `/home/VOTRE_USER/plateforme_cas_cliniques/static`

## 9. Recharger et tester
Bouton vert **Reload** en haut de la page Web, puis ouvrir :
```
https://VOTRE_USER.pythonanywhere.com
```

## Comptes de test
| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Admin | admin@eismv.org | admin123 |
| Enseignant | john.smith@eismv.org | enseignant123 |
| Médecin | fatou.ndiaye@eismv.org | medecin123 |
| Étudiant | aminata.diop@eismv.org | etudiant123 |

## En cas de souci
- **Erreur au chargement** : onglet Web → « Error log », lire la dernière ligne.
- **Page sans style (CSS)** : vérifier l'étape 8 (Static files) puis Reload.
- **« unable to open database file »** : le chemin `DATABASE_URL` doit contenir
  **quatre** barres après `sqlite:` et pointer vers le dossier du projet.
- Chaque modification de code ou du fichier WSGI nécessite un **Reload**.

> Rappel : ceci est un déploiement de test en SQLite. Pour un usage réel en
> MySQL/phpMyAdmin, il faut un VPS (ex. Hostinger VPS) — voir le README.
