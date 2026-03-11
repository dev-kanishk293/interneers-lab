from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .repositories import ProductRepository
from .serializers import (
    ProductPatchRequestSerializer,
    ProductRequestSerializer,
    ProductResponseSerializer,
)
from .services import ProductService

# The controller stays thin: it validates HTTP input and delegates business work.
product_service = ProductService(ProductRepository())


class ProductCollectionAPIView(APIView):
    pagination_class = PageNumberPagination

    def get(self, request):
        # Return a paginated list of products for the collection endpoint.
        products = product_service.list_products()
        paginator = self.pagination_class()
        paginator.page_size = 10
        paginator.page_size_query_param = "page_size"
        paginator.max_page_size = 100

        # Pagination is handled at the API boundary so the service can stay transport-agnostic.
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
        product, error = self._get_product_or_404(product_id)
        if error:
            return error

        serializer = ProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = product_service.replace_product(product_id, serializer.validated_data)
        response_serializer = ProductResponseSerializer(updated)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, product_id: int):
        # PATCH accepts partial fields and only updates what is provided.
        product, error = self._get_product_or_404(product_id)
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
