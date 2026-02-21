from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.ProductCollectionAPIView.as_view(),
        name="products_collection",
    ),
    path(
        "<int:product_id>/",
        views.ProductDetailAPIView.as_view(),
        name="product_detail",
    ),
]
