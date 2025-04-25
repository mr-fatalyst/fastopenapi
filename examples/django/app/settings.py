SECRET_KEY = "__CHANGEME__"
DEBUG = True
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"
