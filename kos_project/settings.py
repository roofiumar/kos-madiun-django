import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _muat_env():
    """Baca file .env (jika ada) ke environment. Dilewati saat menjalankan tes."""
    berkas = BASE_DIR / ".env"
    if "test" in sys.argv or not berkas.exists():
        return
    for baris in berkas.read_text(encoding="utf-8").splitlines():
        baris = baris.strip()
        if baris and not baris.startswith("#") and "=" in baris:
            kunci, nilai = baris.split("=", 1)
            os.environ.setdefault(kunci.strip(), nilai.strip().strip('"').strip("'"))


_muat_env()

SECRET_KEY = "ganti-ini-dengan-kunci-rahasia-sendiri-jika-dipublikasikan"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "prediksi",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kos_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "kos_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Lokasi data & model (dipakai oleh app prediksi)
DATA_PATH = BASE_DIR / "data" / "kos_madiun.csv"
MODEL_PATH = BASE_DIR / "model" / "model_kos.joblib"
