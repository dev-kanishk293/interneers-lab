from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.ProductCollectionAPIView.as_view(),
        name="products_collection",
    ),
    path(
        "bulk-upload/",
        views.ProductBulkUploadAPIView.as_view(),
        name="products_bulk_upload",
    ),
    path(
        "categories/",
        views.ProductCategoryCollectionAPIView.as_view(),
        name="product_categories_collection",
    ),
    path(
        "categories/<int:category_id>/",
        views.ProductCategoryDetailAPIView.as_view(),
        name="product_category_detail",
    ),
    path(
        "categories/<int:category_id>/products/",
        views.ProductCategoryProductsAPIView.as_view(),
        name="product_category_products",
    ),
    path(
        "categories/<int:category_id>/products/<int:product_id>/",
        views.ProductCategoryMembershipAPIView.as_view(),
        name="product_category_membership",
    ),
    path(
        "<int:product_id>/",
        views.ProductDetailAPIView.as_view(),
        name="product_detail",
    ),
]
