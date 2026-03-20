from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from .repositories import ProductCategoryRepository, ProductRepository


class ProductApiTests(TestCase):
    def setUp(self):
        ProductRepository().clear_all()
        ProductCategoryRepository().clear_all()
        self.client = APIClient()

    def test_create_product(self):
        payload = {
            "name": "Laptop",
            "description": "Developer machine",
            "category": "Electronics",
            "price": 1999.99,
            "brand": "Lenovo",
            "quantity": 10,
        }

        response = self.client.post(
            "/products/",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 1)
        self.assertEqual(response.json()["name"], "Laptop")

    def test_create_product_requires_brand(self):
        payload = {
            "name": "Laptop",
            "description": "Developer machine",
            "category": "Electronics",
            "price": 1999.99,
            "quantity": 10,
        }

        response = self.client.post(
            "/products/",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("brand", response.json())

    def test_create_product_validation_error(self):
        payload = {
            "name": "",
            "description": "Missing details",
            "category": "Electronics",
            "price": -1,
            "brand": "",
            "quantity": -5,
        }

        response = self.client.post(
            "/products/",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        self.assertIn("price", response.json())
        self.assertIn("quantity", response.json())

    def test_list_and_get_product(self):
        create_response = self.client.post(
            "/products/",
            data={
                "name": "Phone",
                "description": "Smartphone",
                "category": "Electronics",
                "price": 899.5,
                "brand": "Google",
                "quantity": 25,
            },
            content_type="application/json",
        )
        product_id = create_response.json()["id"]

        list_response = self.client.get("/products/")
        get_response = self.client.get(f"/products/{product_id}/")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["count"], 1)
        self.assertEqual(len(list_response.json()["results"]), 1)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["brand"], "Google")

    def test_list_products_pagination(self):
        for index in range(1, 4):
            self.client.post(
                "/products/",
                data={
                    "name": f"Product {index}",
                    "description": "Sample",
                    "category": "General",
                    "price": 10.0 + index,
                    "brand": "BrandX",
                    "quantity": index,
                },
                content_type="application/json",
            )

        response = self.client.get("/products/?page=1&page_size=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 3)
        self.assertEqual(len(response.json()["results"]), 2)
        self.assertIsNotNone(response.json()["next"])

    def test_put_patch_and_delete(self):
        create_response = self.client.post(
            "/products/",
            data={
                "name": "Tablet",
                "description": "10-inch tablet",
                "category": "Electronics",
                "price": 499.0,
                "brand": "Samsung",
                "quantity": 12,
            },
            content_type="application/json",
        )
        product_id = create_response.json()["id"]

        put_response = self.client.put(
            f"/products/{product_id}/",
            data={
                "name": "Tablet Pro",
                "description": "12-inch tablet",
                "category": "Electronics",
                "price": 699.0,
                "brand": "Samsung",
                "quantity": 8,
            },
            content_type="application/json",
        )
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json()["name"], "Tablet Pro")

        patch_response = self.client.patch(
            f"/products/{product_id}/",
            data={"quantity": 6},
            content_type="application/json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["quantity"], 6)

        delete_response = self.client.delete(f"/products/{product_id}/")
        self.assertEqual(delete_response.status_code, 204)

        missing_response = self.client.get(f"/products/{product_id}/")
        self.assertEqual(missing_response.status_code, 404)

    def test_bulk_upload_products_from_csv(self):
        csv_payload = (
            "name,description,category,price,brand,quantity\n"
            "Mixer,Kitchen helper,Kitchen Essentials,149.99,Philips,4\n"
            "Headphones,Noise cancelling,Electronics,299.50,Sony,7\n"
        )
        upload = SimpleUploadedFile(
            "products.csv",
            csv_payload.encode("utf-8"),
            content_type="text/csv",
        )

        response = self.client.post(
            "/products/bulk-upload/",
            data={"file": upload},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["name"], "Mixer")


class ProductCategoryApiTests(TestCase):
    def setUp(self):
        ProductRepository().clear_all()
        ProductCategoryRepository().clear_all()
        self.client = APIClient()

    def test_category_crud_flow(self):
        create_response = self.client.post(
            "/products/categories/",
            data={
                "title": "Kitchen Essentials",
                "description": "Tools used every day in the kitchen",
            },
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        category_id = create_response.json()["id"]

        list_response = self.client.get("/products/categories/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        patch_response = self.client.patch(
            f"/products/categories/{category_id}/",
            data={"description": "Updated description"},
            content_type="application/json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(
            patch_response.json()["description"],
            "Updated description",
        )

        delete_response = self.client.delete(f"/products/categories/{category_id}/")
        self.assertEqual(delete_response.status_code, 204)

    def test_add_remove_and_list_products_for_category(self):
        category_response = self.client.post(
            "/products/categories/",
            data={
                "title": "Food",
                "description": "Groceries and pantry items",
            },
            content_type="application/json",
        )
        category_id = category_response.json()["id"]

        product_response = self.client.post(
            "/products/",
            data={
                "name": "Pasta",
                "description": "Durum wheat pasta",
                "category": "Food",
                "price": 3.99,
                "brand": "Barilla",
                "quantity": 20,
            },
            content_type="application/json",
        )
        product_id = product_response.json()["id"]

        self.assertIn(category_id, product_response.json()["category_ids"])

        add_response = self.client.post(
            f"/products/categories/{category_id}/products/{product_id}/",
        )
        self.assertEqual(add_response.status_code, 200)

        list_response = self.client.get(f"/products/categories/{category_id}/products/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]["name"], "Pasta")

        remove_response = self.client.delete(
            f"/products/categories/{category_id}/products/{product_id}/",
        )
        self.assertEqual(remove_response.status_code, 200)
        self.assertNotIn(category_id, remove_response.json()["category_ids"])
