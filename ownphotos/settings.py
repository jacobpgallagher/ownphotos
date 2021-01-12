"""
Django settings for ownphotos project.

Generated by 'django-admin startproject' using Django 1.11.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import datetime
from api.im2txt.build_vocab import Vocabulary

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']
RQ_API_TOKEN = os.environ['SECRET_KEY']
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (os.environ.get('DEBUG', '').lower() == 'true')

ALLOWED_HOSTS = [
    os.environ.get('BACKEND_IP', '192.168.1.100'), 'localhost', 'ownphotos-api.local','backend',
    os.environ.get('BACKEND_HOST'), 'ownphotos.local'
]

AUTH_USER_MODEL = 'api.User'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=5),
    # 'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=7),
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'api',
    'nextcloud',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'django_extensions',
    "django_rq",
    'constance',
    'constance.backends.database',
    # 'silk',
    #     'cachalot',
    #     'cacheops',
]

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_DATABASE_CACHE_BACKEND = 'default'

CONSTANCE_CONFIG = {
    'ALLOW_REGISTRATION': (False, 'Publicly allow user registration', bool)
}

INTERNAL_IPS = ('127.0.0.1', 'localhost', '192.168.1.100')

# CACHEOPS_REDIS = {
#     'host': os.environ['REDIS_HOST'], # redis-server is on same machine
#     'port': os.environ["REDIS_PORT"], # default redis port
#     'db': 1             # SELECT non-default redis database
# }
#
# CACHEOPS_DEFAULTS = {
#     'timeout': 60*60
# }
#
# CACHEOPS = {
#     # 'auth.user': {'ops': 'get', 'timeout': 60*15},
#     # 'auth.*': {'ops': ('fetch', 'get')},
#     # 'auth.permission': {'ops': 'all'},
#     '*.*': {'ops':'all', 'timeout': 60*15}
# }

CORS_ALLOW_HEADERS = (
    'cache-control',
    'accept',
    'accept-encoding',
    'allow-credentials',
    'withcredentials',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)

CORS_ORIGIN_WHITELIST = (
    'localhost:3000',
    '192.168.1.100:3000',
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        # 'rest_framework.permissions.IsAdminUser',
        'rest_framework.permissions.IsAuthenticated', ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        #         'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS':
    ('django_filters.rest_framework.DjangoFilterBackend', ),
    'DEFAULT_PAGINATION_CLASS':
    'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE':
    20000,
}

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_OBJECT_CACHE_KEY_FUNC':
    'rest_framework_extensions.utils.default_object_cache_key_func',
    'DEFAULT_LIST_CACHE_KEY_FUNC':
    'rest_framework_extensions.utils.default_list_cache_key_func',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'silk.middleware.SilkyMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.FingerPrintMiddleware',
]

ROOT_URLCONF = 'ownphotos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'ownphotos.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + os.environ['DB_BACKEND'],
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASS'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    },
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': 'dev.db',
    # }
}

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#         'LOCATION': os.environ['CACHE_HOST_PORT'],
#         'TIMEOUT': 60 * 60 * 24 , # 1 day
#         'OPTIONS': {
#             'server_max_value_length': 1024 * 1024 * 128, #50mb
#         }
#     }
# }

CACHES = {
    "default": {
        "BACKEND":
        "django_redis.cache.RedisCache",
        "LOCATION":
        "redis://" + os.environ['REDIS_HOST'] + ":" + os.environ["REDIS_PORT"]
        + "/1",
        "TIMEOUT":
        60 * 60 * 24,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# RQ_QUEUES = {
#     'default': {
#         'USE_REDIS_CACHE': 'default',
#         'DEFAULT_TIMEOUT': -1,
#         'DB':0
#     }
# }

RQ_QUEUES = {
    'default': {
        'HOST': os.environ['REDIS_HOST'],
        'PORT': os.environ['REDIS_PORT'],
        'DB': 0,
        'DEFAULT_TIMEOUT': -1,
    }
}

# RQ_QUEUES = {
#     'default': {
#         'DB': 'ownhotos',
#         'NAME': os.environ['DB_NAME'],
#         'USER': os.environ['DB_USER'],
#         'PASSWORD': os.environ['DB_PASS'],
#         'HOST': os.environ['DB_HOST'],
#         'PORT': os.environ['DB_PORT'],
#         'DEFAULT_TIMEOUT': -1,
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.environ['TIME_ZONE']

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATIC_URL = '/django_static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'protected_media')
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

THUMBNAIL_SIZE_TINY = (30, 30)
THUMBNAIL_SIZE_SMALL = (100, 100)
THUMBNAIL_SIZE_MEDIUM = (500, 500)
THUMBNAIL_SIZE = (500, 500)
THUMBNAIL_SIZE_BIG = (2048, 2048)

FULLPHOTO_SIZE = (1000, 1000)

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True

IMAGE_SIMILARITY_SERVER = 'http://localhost:8002'

# SILKY_PYTHON_PROFILER = True
# SILKY_PYTHON_PROFILER_BINARY = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} : {name}.{module} : {funcName} : {lineno} : {levelname} : {message}',
            'style': '{',
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': ['require_debug_true'],
        },
        'file': {
            'class' : 'logging.handlers.RotatingFileHandler',
            'filename' : os.path.join(os.getenv('LOG_DIR', './logs'), 'ownphotos.log'),
            'maxBytes' : 1024*1024*100, # 100MB
            'backupCount' : 10,
            'formatter' : 'standard',
        }
    },
    'loggers': {
        'api': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'nextcloud': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}
