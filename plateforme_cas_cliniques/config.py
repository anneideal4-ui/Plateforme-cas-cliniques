"""
Configuration de la plateforme de cas cliniques veterinaires - EISMV.

La configuration est separee du code applicatif et lit les valeurs sensibles
depuis les variables d'environnement (voir le fichier .env.example).
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Racine du projet (dossier contenant ce fichier)
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Configuration commune a tous les environnements."""

    # --- Securite -----------------------------------------------------------
    # La cle secrete NE DOIT JAMAIS etre ecrite en dur en production.
    # Elle est lue depuis l'environnement ; une valeur de repli est fournie
    # uniquement pour faciliter le developpement local.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-a-changer-en-production")

    # --- Base de donnees (MySQL / MariaDB via phpMyAdmin) -------------------
    # Les identifiants sont lus depuis l'environnement. Les valeurs par defaut
    # correspondent a une installation locale type XAMPP / WAMP / Laragon
    # (utilisateur "root", sans mot de passe, base "cas_cliniques").
    #
    # On peut aussi tout surcharger d'un coup avec la variable DATABASE_URL,
    # par ex. : mysql+pymysql://root:@localhost/cas_cliniques?charset=utf8mb4
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "cas_cliniques")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Recyclage des connexions pour eviter les coupures MySQL ("server has gone away")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 280, "pool_pre_ping": True}

    # --- Uploads (images / videos des examens) ------------------------------
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    # Taille maximale d'une requete : 50 Mo (pour autoriser les videos courtes)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "ogg", "m4v"}

    # --- Cookies de session : durcissement ----------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Passe a True automatiquement en production (HTTPS requis)
    SESSION_COOKIE_SECURE = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


# Selection de la configuration via la variable FLASK_ENV
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)
