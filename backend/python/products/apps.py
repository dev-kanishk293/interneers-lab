from django.apps import AppConfig
from django.conf import settings
from mongoengine import connect
from mongoengine.connection import get_connection


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products"

    def ready(self):
        try:
            get_connection(alias="default")
            return
        except Exception:
            pass

        connect(alias="default", **settings.MONGODB_SETTINGS)
