from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from . import store
from .serializers import ProductSerializer


class ProductCollectionAPIView(APIView):
    pagination_class = PageNumberPagination

    def get(self, request):
        products = [product.to_dict() for product in store.list_products()]
        paginator = self.pagination_class()
        paginator.page_size = 10
        paginator.page_size_query_param = "page_size"
        paginator.max_page_size = 100

        paginated_products = paginator.paginate_queryset(products, request)
        return paginator.get_paginated_response(paginated_products)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = store.create_product(serializer.validated_data)
        return Response(product.to_dict(), status=status.HTTP_201_CREATED)


class ProductDetailAPIView(APIView):
    def _get_product_or_404(self, product_id: int):
        product = store.get_product(product_id)
        if not product:
            return None, Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return product, None

    def get(self, request, product_id: int):
        product, error = self._get_product_or_404(product_id)
        if error:
            return error
        return Response(product.to_dict(), status=status.HTTP_200_OK)

    def put(self, request, product_id: int):
        product, error = self._get_product_or_404(product_id)
        if error:
            return error

        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = store.update_product(product_id, serializer.validated_data)
        return Response(updated.to_dict(), status=status.HTTP_200_OK)

    def patch(self, request, product_id: int):
        product, error = self._get_product_or_404(product_id)
        if error:
            return error

        serializer = ProductSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_data = product.to_dict()
        updated_data.update(serializer.validated_data)
        updated_data.pop("id", None)

        updated = store.update_product(product_id, updated_data)
        return Response(updated.to_dict(), status=status.HTTP_200_OK)

    def delete(self, request, product_id: int):
        _, error = self._get_product_or_404(product_id)
        if error:
            return error

        store.delete_product(product_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
