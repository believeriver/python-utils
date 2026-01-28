from rest_framework import serializers
from api.models import Item


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
        extra_kwargs = {
            'name': {'write_only': True, 'required': False},
        }

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
        discount = data.get('discount', self.instance.discount if self.instance.discount is not None else 0)
        price = data.get('price', self.instance.price if self.instance.price is not None else 0)
        if discount and discount >= price:
            raise serializers.ValidationError("Discount must be less than the price.")
        return data


