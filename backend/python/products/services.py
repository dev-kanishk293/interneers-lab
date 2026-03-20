from typing import Any, Dict, List, Optional

from .repositories import ProductCategoryRepository, ProductRepository


class ProductService:
    def __init__(
        self,
        repository: ProductRepository,
        category_repository: Optional[ProductCategoryRepository] = None,
    ):
        # Injecting repositories keeps business logic separate from persistence details.
        self.repository = repository
        self.category_repository = category_repository or ProductCategoryRepository()

    def _attach_matching_category(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        # Keep the legacy category string while also linking to the new category model when possible.
        category = self.category_repository.get_by_title(product_data["category"])
        category_ids = list(product_data.get("category_ids", []))
        if category and category.id not in category_ids:
            category_ids.append(category.id)

        next_product_data = dict(product_data)
        next_product_data["category_ids"] = category_ids
        return next_product_data

    def create_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Return plain dictionaries so controllers do not depend on MongoEngine documents.
        product = self.repository.create(self._attach_matching_category(data))
        return product.to_dict()

    def bulk_create_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        created_products = self.repository.bulk_create(
            [self._attach_matching_category(product) for product in products]
        )
        return [product.to_dict() for product in created_products]

    def list_products(self) -> List[Dict[str, Any]]:
        # The service maps repository results into API-friendly payloads.
        return [product.to_dict() for product in self.repository.list()]

    def list_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        return [product.to_dict() for product in self.repository.list_by_category_id(category_id)]

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        product = self.repository.get_by_id(product_id)
        if not product:
            return None
        return product.to_dict()

    def replace_product(self, product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        product = self.repository.replace(product_id, self._attach_matching_category(data))
        if not product:
            return None
        return product.to_dict()

    def patch_product(self, product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_product = self.repository.get_by_id(product_id)
        if not current_product:
            return None

        merged_data = current_product.to_dict()
        merged_data.update(data)
        updated_data = {
            "name": merged_data["name"],
            "description": merged_data["description"],
            "category": merged_data["category"],
            "price": merged_data["price"],
            "brand": merged_data["brand"],
            "quantity": merged_data["quantity"],
            "category_ids": merged_data.get("category_ids", []),
        }
        product = self.repository.patch(product_id, self._attach_matching_category(updated_data))
        if not product:
            return None
        return product.to_dict()

    def add_product_to_category(
        self, product_id: int, category_id: int
    ) -> Optional[Dict[str, Any]]:
        product = self.repository.add_category(product_id, category_id)
        if not product:
            return None
        return product.to_dict()

    def remove_product_from_category(
        self, product_id: int, category_id: int
    ) -> Optional[Dict[str, Any]]:
        product = self.repository.remove_category(product_id, category_id)
        if not product:
            return None
        return product.to_dict()

    def delete_product(self, product_id: int) -> bool:
        return self.repository.delete(product_id)


class ProductCategoryService:
    def __init__(
        self,
        repository: ProductCategoryRepository,
        product_repository: Optional[ProductRepository] = None,
    ):
        self.repository = repository
        self.product_repository = product_repository or ProductRepository()

    def create_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        category = self.repository.create(data)
        return category.to_dict()

    def list_categories(self) -> List[Dict[str, Any]]:
        return [category.to_dict() for category in self.repository.list()]

    def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        category = self.repository.get_by_id(category_id)
        if not category:
            return None
        return category.to_dict()

    def replace_category(self, category_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        category = self.repository.replace(category_id, data)
        if not category:
            return None
        return category.to_dict()

    def patch_category(self, category_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        category = self.repository.patch(category_id, data)
        if not category:
            return None
        return category.to_dict()

    def delete_category(self, category_id: int) -> bool:
        self.product_repository.remove_category_from_all_products(category_id)
        return self.repository.delete(category_id)
