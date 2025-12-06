"""
Django settings for exam_system project.
"""

<<<<<<< HEAD
=======
from decouple import config
import dj_database_url



>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

<<<<<<< HEAD
# -------------------------------------------------
# SECURITY
# -------------------------------------------------
=======
# ----------------------------------
# Security
# ----------------------------------
# ⚠️ Replace with your own Django secret key
>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "3ag%uo*p5t4!_qydefc71ksd7w*9n-b9rdxcz&_no_e0d6(^33"
)
<<<<<<< HEAD

DEBUG = os.getenv("DEBUG", "True") == "True"
=======
DEBUG = os.getenv("DEBUG", "False") == "True"
>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
<<<<<<< HEAD
    os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
]

# -------------------------------------------------
# EMAIL (Gmail SMTP)
# -------------------------------------------------
=======
    os.getenv("RENDER_EXTERNAL_HOSTNAME", "vk-develops.onrender.com"),
]

# ----------------------------------
# Email (Gmail SMTP)
# ----------------------------------
>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
<<<<<<< HEAD
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "your-email@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "your-app-password")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# -------------------------------------------------
# INSTALLED APPS
# -------------------------------------------------
=======
# ⚠️ Enter your Gmail address here
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "your-email@gmail.com")
# ⚠️ Enter your Gmail app password here
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "your-app-password")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ----------------------------------
# Installed Apps
# ----------------------------------
>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
<<<<<<< HEAD

    # Your App
    "exams",
]

# -------------------------------------------------
# DATABASE (SQLite)
# -------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
=======
    "exams",
    "storages",  # S3-compatible backend for Supabase
]


DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'))
}



# ----------------------------------
# Supabase Storage
# ----------------------------------
SUPABASE_PROJECT_REF = "qkxxhddodrctsdeqiruy"
SUPABASE_BUCKET = "meida"
SUPABASE_URL = f"https://{SUPABASE_PROJECT_REF}.supabase.co"

STORAGES = {
    "default": {  # Media files
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            # ⚠️ Put your Supabase access key here
            "access_key": os.getenv("SUPABASE_ACCESS_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFreHhoZGRvZHJjdHNkZXFpcnV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU5MjY0NzIsImV4cCI6MjA3MTUwMjQ3Mn0.7WfqCis2NurtX-09tSwCrRujqaLtWZDMCSiudPP0Gic"),
            # ⚠️ Put your Supabase secret key here
            "secret_key": os.getenv("SUPABASE_SECRET_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFreHhoZGRvZHJjdHNkZXFpcnV5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTkyNjQ3MiwiZXhwIjoyMDcxNTAyNDcyfQ.B7p_hf-x28nzXLlRkLrGjXLwODyP-AFPWOiP7uSZYls"),
            "bucket_name": "media",
            "region_name": "ap-south-1",  # fixed region
            "endpoint_url": "https://qkxxhddodrctsdeqiruy.storage.supabase.co/storage/v1/s3",
            "addressing_style": "path",
        },
    },
    "staticfiles": {  # Static files (via whitenoise)
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ⚠️ Media files will be served from Supabase public bucket
MEDIA_URL = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/"
MEDIA_ROOT = ""

# ----------------------------------
# Middleware
# ----------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

<<<<<<< HEAD
ROOT_URLCONF = "exam_system.urls"

# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
=======
# ----------------------------------
# Templates
# ----------------------------------
ROOT_URLCONF = "exam_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "exam_system.wsgi.application"

<<<<<<< HEAD
# -------------------------------------------------
# STATIC FILES (Admin UI FIX)
# -------------------------------------------------
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# -------------------------------------------------
# MEDIA FILES (Local)
# -------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------
# DEFAULT AUTO FIELD
# -------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------
# LOGGING
# -------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler"
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
}
=======
# ----------------------------------
# Logging
# ----------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"]},
    "loggers": {
        "django": {"handlers": ["console"], "level": "ERROR", "propagate": False}
    },
}

# ----------------------------------
# Password validation
# ----------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------
# Internationalization
# ----------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ----------------------------------
# Static files
# ----------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ----------------------------------
# Default PK type
# ----------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
>>>>>>> 1809d5fa0d72951630748801c8b41425097d079e
