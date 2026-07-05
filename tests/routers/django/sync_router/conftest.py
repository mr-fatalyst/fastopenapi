"""Minimal Django setup so this suite can run standalone."""

from django.conf import settings

if not settings.configured:
    settings.configure(ROOT_URLCONF=__name__, ALLOWED_HOSTS=["*"])

urlpatterns: list = []
