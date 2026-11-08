"""
Point d'entree WSGI pour le deploiement en production.

Exemple avec gunicorn :
    FLASK_ENV=production gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
"""

from app import app

if __name__ == "__main__":
    app.run()
