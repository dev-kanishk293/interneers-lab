from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    FloatField,
    IntField,
    ListField,
    SequenceField,
    StringField,
)


class TimestampedDocument(Document):
    created_at = DateTimeField(required=True, default=datetime.utcnow)
    updated_at = DateTimeField(required=True, default=datetime.utcnow)

    meta = {"abstract": True}

    def save(self, *args, **kwargs):
        # Keep timestamps consistent whenever MongoEngine persists the document.
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class ProductCategoryDocument(TimestampedDocument):
    # MongoEngine document stored in the "product_categories" collection.
    id = SequenceField(primary_key=True)
    title = StringField(required=True, max_length=255, unique=True)
    description = StringField(required=True, max_length=1000)

    meta = {"collection": "product_categories"}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ProductDocument(TimestampedDocument):
    # MongoEngine document stored in the "products" collection.
    id = SequenceField(primary_key=True)
    name = StringField(required=True, max_length=255)
    description = StringField(required=True, max_length=1000)
    category = StringField(required=True, max_length=255)
    price = FloatField(required=True, min_value=0)
    brand = StringField(required=False, null=True, max_length=255)
    quantity = IntField(required=True, min_value=0)
    category_ids = ListField(IntField(), default=list)

    meta = {"collection": "products"}

    def to_dict(self) -> dict:
        # Convert the document into a plain payload for serializers and responses.
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "brand": self.brand or "",
            "quantity": self.quantity,
            "category_ids": self.category_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
