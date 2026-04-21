# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

import logging
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('httplib2').setLevel(logging.WARNING)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'change-this-to-a-random-string'

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'djangae',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'djangae.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'img2xl_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'img2xl_project.urls'

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
                'django.contrib.auth.context_processors.auth',
                'img2xl_app.services.context_processors.global_user_data',
                'img2xl_app.services.context_processors.notification_context',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'djangae.db.backends.appengine',
    }
}

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
# ]

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_TZ = True  #

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Đọc từ app.yaml
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS')

# Email mặc định gửi đi
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER