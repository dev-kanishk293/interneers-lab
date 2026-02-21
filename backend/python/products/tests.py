from django.test import TestCase
from rest_framework.test import APIClient

from .store import clear_store


class ProductApiTests(TestCase):
    def setUp(self):
        clear_store()
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
