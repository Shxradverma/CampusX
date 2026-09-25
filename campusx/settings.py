"""
Django settings for CampusX project.

Generated using Django 6.1.1.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# =========================================================
# BASE DIRECTORY & ENVIRONMENT VARIABLES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")


# =========================================================
# SECURITY
# =========================================================

# Secret key must be stored inside .env
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Development mode
# We will configure production mode separately during deployment.
DEBUG = os.getenv(
    "DJANGO_DEBUG",
    "True",
).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "",
    ).split(",")
    if host.strip()
]
# Empty is correct for local development.
# Production domain will be added during deployment.


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # CampusX apps
    "accounts",
    "events",
    "registrations",
    "dashboard",
    "chatbot",
    "notifications",
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URL / WSGI
# =========================================================

ROOT_URLCONF = "campusx.urls"

WSGI_APPLICATION = "campusx.wsgi.application"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "notifications.context_processors.notification_context",
            ],
        },
    },
]


# =========================================================
# DATABASE
# =========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================================================
# CUSTOM USER MODEL
# =========================================================

AUTH_USER_MODEL = "accounts.User"


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================
STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
# =========================================================
# MEDIA FILES
# =========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# AUTHENTICATION REDIRECTS
# =========================================================

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/dashboard/"

LOGOUT_REDIRECT_URL = "/login/"


# =========================================================
# EMAIL
# =========================================================

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": os.getenv(
                "EMAIL_HOST_USER",
                "",
            ),
            "password": os.getenv(
                "EMAIL_HOST_PASSWORD",
                "",
            ),
            "use_tls": True,
            "timeout": 20,
        },
    },
}

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    os.getenv(
        "EMAIL_HOST_USER",
        "",
    ),
)
# =========================================================
# PRODUCTION SECURITY
# =========================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"

    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )