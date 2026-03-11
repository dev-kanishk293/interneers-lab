from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    FloatField,
    IntField,
    SequenceField,
    StringField,
)


class ProductDocument(Document):
    # MongoEngine document stored in the "products" collection.
    id = SequenceField(primary_key=True)
    name = StringField(required=True, max_length=255)
    description = StringField(required=True, max_length=1000)
    category = StringField(required=True, max_length=255)
    price = FloatField(required=True, min_value=0)
    brand = StringField(required=True, max_length=255)
    quantity = IntField(required=True, min_value=0)
    created_at = DateTimeField(required=True, default=datetime.utcnow)
    updated_at = DateTimeField(required=True, default=datetime.utcnow)

    meta = {"collection": "products"}

    def save(self, *args, **kwargs):
        # Keep timestamps consistent whenever MongoEngine persists the document.
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        # Convert the document into a plain payload for serializers and responses.
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "brand": self.brand,
            "quantity": self.quantity,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
