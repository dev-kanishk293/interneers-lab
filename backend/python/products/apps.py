from django.apps import AppConfig
from django.conf import settings
from mongoengine import connect
from mongoengine.connection import get_connection

from .seeds import seed_product_categories


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

        if getattr(settings, "ENABLE_CATEGORY_SEEDING", True):
            seed_product_categories()
