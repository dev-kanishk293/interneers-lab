from typing import Dict, List, Optional

from .models import Product

_products: Dict[int, Product] = {}
_next_id = 1


def create_product(data: dict) -> Product:
    global _next_id
    product = Product(id=_next_id, **data)
    _products[_next_id] = product
    _next_id += 1
    return product


def list_products() -> List[Product]:
    return list(_products.values())


def get_product(product_id: int) -> Optional[Product]:
    return _products.get(product_id)


def update_product(product_id: int, data: dict) -> Optional[Product]:
    if product_id not in _products:
        return None

    product = Product(id=product_id, **data)
    _products[product_id] = product
    return product


def delete_product(product_id: int) -> bool:
    if product_id not in _products:
        return False
    del _products[product_id]
    return True


def clear_store() -> None:
    global _next_id
    _products.clear()
    _next_id = 1
