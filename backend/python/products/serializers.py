from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
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
