DEBUG = True

SMS_SEND_SERVICE = {
    'host': 'localhost',
    'port': 13013,
    'username': 'kannel',
    'password': 'kannel',
    }

DLR_URL = "http://localhost:8080/kannel"

PATTERNS = "cvs.patterns"

ROOT_URLCONF = "cvs.urls"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'sms.db'
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'router',
    'registration',
    'health',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    )

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.csrf",
    )
