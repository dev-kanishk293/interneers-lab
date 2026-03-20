from .repositories import ProductCategoryRepository


DEFAULT_PRODUCT_CATEGORIES = [
    {
        "title": "Food",
        "description": "Everyday grocery and pantry products.",
    },
    {
        "title": "Kitchen Essentials",
        "description": "Useful kitchen tools and day-to-day cooking items.",
    },
    {
        "title": "Electronics",
        "description": "Consumer gadgets and electronic devices.",
    },
]


def seed_product_categories() -> None:
    repository = ProductCategoryRepository()
    for category in DEFAULT_PRODUCT_CATEGORIES:
        repository.upsert_by_title(category)
