from typing import Any, Dict, List, Optional

from mongoengine.connection import get_db

from .models import ProductCategoryDocument, ProductDocument


def _reset_sequence(document_class, field_name: str = "id") -> None:
    sequence_field = document_class._fields[field_name]
    sequence_id = f"{sequence_field.get_sequence_name()}.{sequence_field.name}"
    get_db()[sequence_field.collection_name].delete_one({"_id": sequence_id})


class ProductRepository:
    def create(self, data: Dict[str, Any]) -> ProductDocument:
        # This layer is the only place that talks directly to MongoEngine.
        product = ProductDocument(**data)
        product.save()
        return product

    def bulk_create(self, products: List[Dict[str, Any]]) -> List[ProductDocument]:
        created_products: List[ProductDocument] = []
        for product_data in products:
            created_products.append(self.create(product_data))
        return created_products

    def list(self) -> List[ProductDocument]:
        # Ordering by id makes list responses stable and easier to test.
        return list(ProductDocument.objects.order_by("id"))

    def get_by_id(self, product_id: int) -> Optional[ProductDocument]:
        return ProductDocument.objects(id=product_id).first()

    def list_by_category_id(self, category_id: int) -> List[ProductDocument]:
        return list(ProductDocument.objects(category_ids=category_id).order_by("id"))

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

    def add_category(self, product_id: int, category_id: int) -> Optional[ProductDocument]:
        product = self.get_by_id(product_id)
        if not product:
            return None

        if category_id not in product.category_ids:
            product.category_ids.append(category_id)
            product.save()
        return product

    def remove_category(self, product_id: int, category_id: int) -> Optional[ProductDocument]:
        product = self.get_by_id(product_id)
        if not product:
            return None

        if category_id in product.category_ids:
            product.category_ids.remove(category_id)
            product.save()
        return product

    def remove_category_from_all_products(self, category_id: int) -> None:
        for product in ProductDocument.objects(category_ids=category_id):
            product.category_ids.remove(category_id)
            product.save()

    def delete(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        product.delete()
        return True

    def clear_all(self) -> None:
        # Tests use this to clear both product documents and the SequenceField counter.
        ProductDocument.drop_collection()
        _reset_sequence(ProductDocument)


class ProductCategoryRepository:
    def create(self, data: Dict[str, Any]) -> ProductCategoryDocument:
        category = ProductCategoryDocument(**data)
        category.save()
        return category

    def list(self) -> List[ProductCategoryDocument]:
        return list(ProductCategoryDocument.objects.order_by("id"))

    def get_by_id(self, category_id: int) -> Optional[ProductCategoryDocument]:
        return ProductCategoryDocument.objects(id=category_id).first()

    def get_by_title(self, title: str) -> Optional[ProductCategoryDocument]:
        return ProductCategoryDocument.objects(title=title).first()

    def replace(
        self, category_id: int, data: Dict[str, Any]
    ) -> Optional[ProductCategoryDocument]:
        category = self.get_by_id(category_id)
        if not category:
            return None

        for key, value in data.items():
            setattr(category, key, value)
        category.save()
        return category

    def patch(
        self, category_id: int, data: Dict[str, Any]
    ) -> Optional[ProductCategoryDocument]:
        category = self.get_by_id(category_id)
        if not category:
            return None

        for key, value in data.items():
            setattr(category, key, value)
        category.save()
        return category

    def upsert_by_title(self, data: Dict[str, Any]) -> ProductCategoryDocument:
        category = self.get_by_title(data["title"])
        if category:
            category.description = data["description"]
            category.save()
            return category
        return self.create(data)

    def delete(self, category_id: int) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False
        category.delete()
        return True

    def clear_all(self) -> None:
        ProductCategoryDocument.drop_collection()
        _reset_sequence(ProductCategoryDocument)
