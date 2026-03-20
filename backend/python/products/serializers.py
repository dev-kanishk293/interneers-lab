from rest_framework import serializers


def _validate_non_empty_text(value: str, field_name: str) -> str:
    cleaned_value = value.strip()
    if not cleaned_value:
        raise serializers.ValidationError(
            f"{field_name} must be a non-empty string."
        )
    return cleaned_value


class ProductRequestSerializer(serializers.Serializer):
    # Request model for create and full-update operations.
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000)
    category = serializers.CharField(max_length=255)
    price = serializers.FloatField()
    brand = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField()

    def validate_name(self, value: str) -> str:
        return _validate_non_empty_text(value, "Name")

    def validate_description(self, value: str) -> str:
        return _validate_non_empty_text(value, "Description")

    def validate_category(self, value: str) -> str:
        return _validate_non_empty_text(value, "Category")

    def validate_brand(self, value: str) -> str:
        return _validate_non_empty_text(value, "Brand")

    def validate_price(self, value: float) -> float:
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_quantity(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError(
                "Quantity must be an integer >= 0."
            )
        return value


class ProductPatchRequestSerializer(serializers.Serializer):
    # Request model for partial updates where every field is optional.
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=1000, required=False)
    category = serializers.CharField(max_length=255, required=False)
    price = serializers.FloatField(required=False)
    brand = serializers.CharField(max_length=255, required=False)
    quantity = serializers.IntegerField(required=False)

    def validate_name(self, value: str) -> str:
        return _validate_non_empty_text(value, "Name")

    def validate_description(self, value: str) -> str:
        return _validate_non_empty_text(value, "Description")

    def validate_category(self, value: str) -> str:
        return _validate_non_empty_text(value, "Category")

    def validate_brand(self, value: str) -> str:
        return _validate_non_empty_text(value, "Brand")

    def validate_price(self, value: float) -> float:
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_quantity(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError(
                "Quantity must be an integer >= 0."
            )
        return value


class ProductBulkUploadSerializer(serializers.Serializer):
    # Accept a CSV file upload for bulk product creation.
    file = serializers.FileField()


class ProductCategoryRequestSerializer(serializers.Serializer):
    # Request model for category create and full-update operations.
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000)

    def validate_title(self, value: str) -> str:
        return _validate_non_empty_text(value, "Title")

    def validate_description(self, value: str) -> str:
        return _validate_non_empty_text(value, "Description")


class ProductCategoryPatchRequestSerializer(serializers.Serializer):
    # Request model for category partial updates.
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=1000, required=False)

    def validate_title(self, value: str) -> str:
        return _validate_non_empty_text(value, "Title")

    def validate_description(self, value: str) -> str:
        return _validate_non_empty_text(value, "Description")


class ProductResponseSerializer(serializers.Serializer):
    # Response model exposed by the API after service/repository processing.
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    price = serializers.FloatField()
    brand = serializers.CharField(allow_blank=True, allow_null=True)
    quantity = serializers.IntegerField()
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        read_only=True,
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ProductCategoryResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
