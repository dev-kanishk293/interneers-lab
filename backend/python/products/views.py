import csv
import io

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .repositories import ProductCategoryRepository, ProductRepository
from .serializers import (
    ProductBulkUploadSerializer,
    ProductCategoryPatchRequestSerializer,
    ProductCategoryRequestSerializer,
    ProductCategoryResponseSerializer,
    ProductPatchRequestSerializer,
    ProductRequestSerializer,
    ProductResponseSerializer,
)
from .services import ProductCategoryService, ProductService

# Controllers stay thin: they validate HTTP input and delegate business work.
product_repository = ProductRepository()
category_repository = ProductCategoryRepository()
product_service = ProductService(product_repository, category_repository)
product_category_service = ProductCategoryService(category_repository, product_repository)


class ProductCollectionAPIView(APIView):
    pagination_class = PageNumberPagination

    def get(self, request):
        # Return a paginated list of products for the collection endpoint.
        products = product_service.list_products()
        paginator = self.pagination_class()
        paginator.page_size = 10
        paginator.page_size_query_param = "page_size"
        paginator.max_page_size = 100

        paginated_products = paginator.paginate_queryset(products, request)
        serializer = ProductResponseSerializer(paginated_products, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        # Validate the request body before handing creation to the service layer.
        serializer = ProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = product_service.create_product(serializer.validated_data)
        response_serializer = ProductResponseSerializer(product)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ProductBulkUploadAPIView(APIView):
    def post(self, request):
        upload_serializer = ProductBulkUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        uploaded_file = upload_serializer.validated_data["file"]
        decoded_csv = uploaded_file.read().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(decoded_csv)))

        if not rows:
            return Response(
                {"error": "CSV file must contain at least one product row."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_rows = []
        row_errors = []

        for index, row in enumerate(rows, start=2):
            serializer = ProductRequestSerializer(data=row)
            if serializer.is_valid():
                validated_rows.append(serializer.validated_data)
            else:
                row_errors.append({"row": index, "errors": serializer.errors})

        if row_errors:
            return Response(
                {"errors": row_errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_products = product_service.bulk_create_products(validated_rows)
        response_serializer = ProductResponseSerializer(created_products, many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(APIView):
    def _get_product_or_404(self, product_id: int):
        # Centralize the not-found response used by detail operations.
        product = product_service.get_product(product_id)
        if not product:
            return None, Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return product, None

    def get(self, request, product_id: int):
        # Return a single product by its application-level id.
        product, error = self._get_product_or_404(product_id)
        if error:
            return error
        response_serializer = ProductResponseSerializer(product)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, product_id: int):
        # PUT replaces the full resource, so all required fields are validated.
        _, error = self._get_product_or_404(product_id)
        if error:
            return error

        serializer = ProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = product_service.replace_product(product_id, serializer.validated_data)
        response_serializer = ProductResponseSerializer(updated)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, product_id: int):
        # PATCH accepts partial fields and only updates what is provided.
        _, error = self._get_product_or_404(product_id)
        if error:
            return error

        serializer = ProductPatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = product_service.patch_product(product_id, serializer.validated_data)
        response_serializer = ProductResponseSerializer(updated)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, product_id: int):
        # Delete returns no body once the target product has been removed.
        _, error = self._get_product_or_404(product_id)
        if error:
            return error

        product_service.delete_product(product_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductCategoryCollectionAPIView(APIView):
    def get(self, request):
        categories = product_category_service.list_categories()
        serializer = ProductCategoryResponseSerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductCategoryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = product_category_service.create_category(serializer.validated_data)
        response_serializer = ProductCategoryResponseSerializer(category)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ProductCategoryDetailAPIView(APIView):
    def _get_category_or_404(self, category_id: int):
        category = product_category_service.get_category(category_id)
        if not category:
            return None, Response(
                {"error": "Product category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return category, None

    def get(self, request, category_id: int):
        category, error = self._get_category_or_404(category_id)
        if error:
            return error
        serializer = ProductCategoryResponseSerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, category_id: int):
        _, error = self._get_category_or_404(category_id)
        if error:
            return error

        serializer = ProductCategoryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = product_category_service.replace_category(category_id, serializer.validated_data)
        response_serializer = ProductCategoryResponseSerializer(updated)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, category_id: int):
        _, error = self._get_category_or_404(category_id)
        if error:
            return error

        serializer = ProductCategoryPatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = product_category_service.patch_category(category_id, serializer.validated_data)
        response_serializer = ProductCategoryResponseSerializer(updated)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, category_id: int):
        _, error = self._get_category_or_404(category_id)
        if error:
            return error

        product_category_service.delete_category(category_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductCategoryProductsAPIView(APIView):
    def get(self, request, category_id: int):
        category = product_category_service.get_category(category_id)
        if not category:
            return Response(
                {"error": "Product category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        products = product_service.list_products_by_category(category_id)
        serializer = ProductResponseSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductCategoryMembershipAPIView(APIView):
    def post(self, request, category_id: int, product_id: int):
        category = product_category_service.get_category(category_id)
        if not category:
            return Response(
                {"error": "Product category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        product = product_service.add_product_to_category(product_id, category_id)
        if not product:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductResponseSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, category_id: int, product_id: int):
        category = product_category_service.get_category(category_id)
        if not category:
            return Response(
                {"error": "Product category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        product = product_service.remove_product_from_category(product_id, category_id)
        if not product:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductResponseSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
