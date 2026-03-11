from typing import Any, Dict, List, Optional

from .repositories import ProductRepository


class ProductService:
    def __init__(self, repository: ProductRepository):
        # Injecting the repository keeps business logic separate from persistence details.
        self.repository = repository

    def create_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Return plain dictionaries so controllers do not depend on MongoEngine documents.
        product = self.repository.create(data)
        return product.to_dict()

    def list_products(self) -> List[Dict[str, Any]]:
        # The service maps repository results into API-friendly payloads.
        return [product.to_dict() for product in self.repository.list()]

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        product = self.repository.get_by_id(product_id)
        if not product:
            return None
        return product.to_dict()

    def replace_product(self, product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        product = self.repository.replace(product_id, data)
        if not product:
            return None
        return product.to_dict()

    def patch_product(self, product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        product = self.repository.patch(product_id, data)
        if not product:
            return None
        return product.to_dict()

    def delete_product(self, product_id: int) -> bool:
        return self.repository.delete(product_id)
