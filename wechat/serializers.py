# coding=utf-8
import models
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = ("id", "openid", "last_login_time", "create_time")


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Banner
        fields = "__all__"


class GoodsTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoodsType
        fields = ("id", "description", "img", "price", "old_price", "count")


class GoodsSerializer(serializers.ModelSerializer):
    good_types = GoodsTypeSerializer(many=True, read_only=True)

    class Meta:
        model = models.Goods
        fields = ("id", "name", "description", "img", "min_price", "max_price", "good_types")


class GoodsCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Goods
        fields = ("name", "id")


class GoodsTypeCartSerializer(serializers.ModelSerializer):
    goods = GoodsCartSerializer(read_only=True)

    class Meta:
        model = models.GoodsType
        fields = ("id", "description", "img", "price", "old_price", "count", "goods")


class IndexGoodsSerializer(serializers.ModelSerializer):
    """
    首页商品
    """
    class Meta:
        model = models.Goods
        fields = ("id", "name", "description", "img", "min_price", "max_price")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Address
        exclude = ("is_showing", "create_time", "user")


class ExpressTraceSerializer(serializers.ModelSerializer):
    class Meta:
        models = models.ExpressTrace
        fields = "__all__"


class OderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderItem
        exclude = ('order', 'goods_type')


class OrderSerializer(serializers.ModelSerializer):

    orderitem_set = OderItemSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = models.Order
        exclude = ('is_showing', 'user')


class OrderListSerializer(serializers.ModelSerializer):

    orderitem_set = OderItemSerializer(many=True, read_only=True)

    class Meta:
        model = models.Order
        exclude = ('is_showing', 'user', 'address')