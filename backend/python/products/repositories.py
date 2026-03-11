from typing import Any, Dict, List, Optional

from mongoengine.connection import get_db

from .models import ProductDocument


class ProductRepository:
    def create(self, data: Dict[str, Any]) -> ProductDocument:
        # This layer is the only place that talks directly to MongoEngine.
        product = ProductDocument(**data)
        product.save()
        return product

    def list(self) -> List[ProductDocument]:
        # Ordering by id makes list responses stable and easier to test.
        return list(ProductDocument.objects.order_by("id"))

    def get_by_id(self, product_id: int) -> Optional[ProductDocument]:
        return ProductDocument.objects(id=product_id).first()

    def replace(self, product_id: int, data: Dict[str, Any]) -> Optional[ProductDocument]:
        product = self.get_by_id(product_id)
        if not product:
            return None

        # Full updates and partial updates both reuse the document save flow.
        for key, value in data.items():
            setattr(product, key, value)
        product.save()
        return product

    def patch(self, product_id: int, data: Dict[str, Any]) -> Optional[ProductDocument]:
        product = self.get_by_id(product_id)
        if not product:
            return None

        # Partial updates only touch fields that survived request validation.
        for key, value in data.items():
            setattr(product, key, value)
        product.save()
        return product

    def delete(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        product.delete()
        return True

    def clear_all(self) -> None:
        # Tests use this to clear both product documents and the SequenceField counter.
        ProductDocument.drop_collection()
        sequence_field = ProductDocument._fields["id"]
        sequence_id = f"{sequence_field.get_sequence_name()}.{sequence_field.name}"
        get_db()[sequence_field.collection_name].delete_one({"_id": sequence_id})
