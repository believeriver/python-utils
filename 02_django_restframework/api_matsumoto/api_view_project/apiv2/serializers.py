from rest_framework import serializers
from rest_framework.serializers import UniqueTogetherValidator
from django.contrib.auth import get_user_model

from api.models import Item, Product


class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'user')
        read_only_fields = ('id',)


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'password')
        # read_only_fields = ('id', 'username', 'email')
        extra_kwargs = {'password': {'write_only': True}}


def check_divide_by_10(value):
    if value % 10 != 0:
        raise serializers.ValidationError("Value must be a multiple of 10.")
    return value


"""
ModelSerializerを使ったSerializerの実装例
Field定義、create/updateメソッドの実装が不要になる
"""

class ItemModelSerializer(serializers.ModelSerializer):
    # user defined field
    discount = serializers.IntegerField(
        min_value=0, required=False, validators=[check_divide_by_10])

    class Meta:
        model = Item
        # fields = '__all__'
        fields = ('id', 'name', 'price', 'discount')
        read_only_fields = ('id',)
        # extra_kwargs = {
        #     'name': {'write_only': True, 'required': False},
        # }
        validators = [
            UniqueTogetherValidator(
                queryset=Item.objects.all(),
                fields=['name', 'price'],
                message="The combination of name and price must be unique.")
        ]


    def validate_name(self, value):
        if self.partial and value is None:
            return value
        if value[0].islower():
            raise serializers.ValidationError("Name must start with an uppercase letter.")
        return value

    def validate_price(self, value):
        if self.partial and value is None:
            return value
        if value % 10 < 0:
            raise serializers.ValidationError("Price must be a non-negative integer.")

        if value % 10 > 0:
            raise serializers.ValidationError("Price must be a multiple of 10.")
        return value

    def validate(self, data):
        print(f"validate: {data}")
        # discount = data.get(
        #     'discount',
        #     getattr(self.instance.discount,'discount',0) if self.instance.discount is not None else 0)
        # price = data.get(
        #     'price',
        #     getattr(self.instance.price, 'price', 0) if self.instance.price is not None else 0)

        # 最初に既存の値を安全に取得
        discount = data.get('discount')
        if discount is None and self.instance is not None:
            discount = getattr(self.instance, 'discount', 0)

        price = data.get('price')
        if price is None and self.instance is not None:
            price = getattr(self.instance, 'price', 0)

        # discount = data.get('discount') or (getattr(self.instance, 'discount', 0) if self.instance else 0)
        # price = data.get('price') or (getattr(self.instance, 'price', 0) if self.instance else 0)
        if discount and discount >= price:
            raise serializers.ValidationError("Discount must be less than the price.")
        return data


