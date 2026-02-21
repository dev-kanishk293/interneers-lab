# from django.db import models (commented out for now, will be used later)
from dataclasses import asdict, dataclass


@dataclass
class Product:
    id: int
    name: str
    description: str
    category: str
    price: float
    brand: str
    quantity: int

    def to_dict(self) -> dict:
        return asdict(self)
