from rest_framework import serializers


class ProductRequestSerializer(serializers.Serializer):
    # Request model for create and full-update operations.
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000)
    category = serializers.CharField(max_length=255)
    price = serializers.FloatField()
    brand = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField()

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Name must be a non-empty string."
            )
        return value

    def validate_description(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Description must be a non-empty string."
            )
        return value

    def validate_category(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Category must be a non-empty string."
            )
        return value

    def validate_brand(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Brand must be a non-empty string."
            )
        return value

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
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Name must be a non-empty string."
            )
        return value

    def validate_description(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Description must be a non-empty string."
            )
        return value

    def validate_category(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Category must be a non-empty string."
            )
        return value

    def validate_brand(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Brand must be a non-empty string."
            )
        return value

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


class ProductResponseSerializer(serializers.Serializer):
    # Response model exposed by the API after service/repository processing.
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    price = serializers.FloatField()
    brand = serializers.CharField()
    quantity = serializers.IntegerField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
