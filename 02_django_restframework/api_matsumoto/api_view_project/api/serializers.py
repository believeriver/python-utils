from rest_framework import serializers
from . models import Item


def check_divide_by_10(value):
    if value % 10 != 0:
        raise serializers.ValidationError("Value must be a multiple of 10.")
    return value

class ItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=20)
    price = serializers.IntegerField(min_value=0)
    discount = serializers.IntegerField(
        min_value=0, required=False, validators=[check_divide_by_10])

    def validate_name(self, value):
        print(f"validate_name: {value}")
        if value[0].islower():
            raise serializers.ValidationError("Name must start with an uppercase letter.")
        return value

    def validate_price(self, value):
        print(f"validate_price: {value}")
        if value % 10 < 0:
            raise serializers.ValidationError("Price must be a non-negative integer.")

        if value % 10 > 0:
            raise serializers.ValidationError("Price must be a multiple of 10.")
        return value

    def validate(self, data):
        print(f"validate: {data}")
        discount = data.get('discount', 0)
        price = data['price']
        if discount and discount >= price:
            raise serializers.ValidationError("Discount must be less than the price.")
        return data

    def create(self, validated_data):
        print(f"serializer create: {validated_data}")
        return Item.objects.create(**validated_data)

    def update(self, instance, validated_data):
        print(f"serializer update: {validated_data}")
        # instance.name = validated_data.get('name', instance.name)
        # instance.price = validated_data.get('price', instance.price)
        # instance.discount = validated_data.get('discount', instance.discount)
        return instance

