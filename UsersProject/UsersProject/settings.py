"""
Django settings for UsersProject project.

Generated by 'django-admin startproject' using Django 4.2.18.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from decouple import config, Config, RepositoryEnv
import dj_database_url
import os
from datetime import timedelta
from celery.schedules import crontab
from django.utils import timezone

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Load .env from project root
env_config = Config(RepositoryEnv(PROJECT_ROOT / '.env'))

# Directory for storing scanned PDFs
SCAN_ROOT = os.path.join(BASE_DIR, 'scans')

# Create scan directory if it doesn't exist
os.makedirs(SCAN_ROOT, exist_ok=True)

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Directory for storing scanned files
DESTINATION_ROOT = env_config('DESTINATION_ROOT', default=os.path.join(BASE_DIR, 'media', 'pdfs'))

# Create destination directory if it doesn't exist
os.makedirs(DESTINATION_ROOT, exist_ok=True)

# Create media and pdfs directories if they don't exist
os.makedirs(os.path.join(MEDIA_ROOT, 'pdfs'), exist_ok=True)

# Media files configuration
PDF_UPLOAD_PATH = 'pdfs/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-_!qm3)vk2i#gbihh%#yjar+82f0=mfk^7kvi2ibyn$oey5*62t"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# CSRF settings
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access to CSRF token
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False  # More secure
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = ['content-type', 'x-csrftoken']
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'corsheaders',  # Add CORS support
    'rest_framework',
    'rest_framework.authtoken',  # Required for token authentication
    'user_management',
    'channels',  # Add channels for WebSocket support
    'notifications',  # Add our new notifications app
    'tickets',  # Add the tickets app
]

# Middleware - order is important!
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS must be first
    'user_management.middleware.CustomCorsMiddleware',  # Our custom CORS middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',  # After CORS, before CSRF
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user_management.middleware.SessionTrackingMiddleware',
    'user_management.middleware.LoginAttemptMiddleware',
    'user_management.middleware.PasswordPolicyMiddleware',
]

ROOT_URLCONF = "UsersProject.urls"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'user_management', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = "UsersProject.wsgi.application"

ASGI_APPLICATION = 'UsersProject.asgi.application'

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    },
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'user_management.validators.PasswordPolicyValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True

# File Operation Settings
SOURCE_DIR = os.path.join(BASE_DIR, 'source_files')
BACKUP_DIR = os.path.join(BASE_DIR, 'backup_files')

# Create directories if they don't exist
os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Network credentials for remote computer access
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'infotech')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'gidget003')
USER_PROFILES = ["Client"]
CSV_FILE = os.getenv('CSV_FILE', 'Lab-Computers.csv')

# Network share settings
NETWORK_SHARE_PATH = 'shared/scans'  # Path to scan on network shares

# Remote computer settings
REMOTE_USERNAME = 'admin'  # Default username for remote computers
REMOTE_PASSWORD = 'password'  # Default password for remote computers
REMOTE_SCAN_PATH = '/path/to/scan'  # Default path to scan on remote computers

# Security settings for development
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Session settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Authentication settings
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Token Authentication settings
AUTH_HEADER_PREFIX = 'Token'

# Custom user model
AUTH_USER_MODEL = 'user_management.CustomUser'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'user_management.authentication.CookieTokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

# Token expiry settings
TOKEN_EXPIRED_AFTER_SECONDS = 86400  # 24 hours

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'analyze_logs': {
        'task': 'user_management.tasks.analyze_logs',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
    'check-scan-schedules': {
        'task': 'user_management.tasks.check_and_run_scheduled_scans',
        'schedule': crontab(minute='*'),  # Run every minute
    },
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'scan_ops': {
            'format': '[{asctime}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'scan_operations': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', f'scan_operations_{timezone.now().strftime("%Y%m%d")}.log'),
            'formatter': 'scan_ops',
            'mode': 'a',
        },
        'debug_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'debug.log'),
            'formatter': 'verbose',
            'mode': 'a',
        },
    },
    'loggers': {
        'user_management': {  # This is your app name
            'handlers': ['console', 'scan_operations', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Email notification settings
NOTIFICATION_EMAIL_DIGEST = env_config('NOTIFICATION_EMAIL_DIGEST', default=True, cast=bool)
NOTIFICATION_DIGEST_INTERVAL = env_config('NOTIFICATION_DIGEST_INTERVAL', default=24, cast=int)  # hours

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"