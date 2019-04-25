# coding=utf-8
from __future__ import unicode_literals

from django.db import models
import uuid
# Create your models here.
EXPRESS_TYPES = (
    ("SFEXPRESS", "顺丰"),
    ("ZTO", "中通"),
    ("YUNDA", "韵达"),
    ("STO", "申通")
)


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    openid = models.CharField(max_length=100, verbose_name="微信OPENID", null=True, blank=True, unique=True)
    nickname = models.CharField(max_length=100, verbose_name="微信用户名", null=True)
    avatarurl = models.CharField(max_length=1000, verbose_name="微信用户头像", null=True)
    gender = models.IntegerField(null=True, verbose_name="微信用户性别", default=0, choices=((0, "未知"), (1, "男性"), (2, "女性")))
    country = models.CharField(max_length=100, verbose_name="微信用户所在国家")
    province = models.CharField(max_length=100, verbose_name="微信用户所在省份")
    city = models.CharField(max_length=100, verbose_name="微信用户所在城市")
    language = models.CharField(max_length=100, verbose_name="微信用户显示 country，province，city 所用的语言")
    last_login_time = models.DateTimeField(null=True, verbose_name="最后登录时间", blank=True, auto_now_add=True)
    create_time = models.DateTimeField(verbose_name="创建时间", null=True, blank=True, auto_now_add=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __unicode__(self):
        return self.nickname


class Goods(models.Model):
    name = models.CharField(max_length=100, verbose_name="名称", null=True)
    min_old_price = models.FloatField(verbose_name="最低原价", null=True, blank=True, editable=False)
    max_old_price = models.FloatField(verbose_name="最高原价", null=True, blank=True, editable=False)
    min_price = models.FloatField(verbose_name="最低现价", null=True, editable=False)
    max_price = models.FloatField(verbose_name="最高现价", null=True, editable=False)
    description = models.CharField(max_length=1000, verbose_name="描述", null=True, blank=True)
    weight = models.IntegerField(verbose_name="权重", null=True, default=0)
    type = models.IntegerField(verbose_name="商品类型", null=True, default=0, blank=True)
    is_showing = models.BooleanField(verbose_name="是否显示", default=True)
    img = models.FileField(verbose_name="商品图片", null=True, upload_to="goods", blank=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True, null=True)

    class Meta:
        verbose_name = "商品类"
        verbose_name_plural = "商品类"

    def __unicode__(self):
        return self.name


class GoodsType(models.Model):
    goods = models.ForeignKey(Goods, verbose_name="商品类", null=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=1000, verbose_name="描述", null=True, blank=True)
    weight = models.IntegerField(verbose_name="权重", null=True, default=0)
    is_showing = models.BooleanField(verbose_name="是否显示", default=True)
    img = models.FileField(verbose_name="商品图片", null=True, upload_to="goods", blank=True)
    count = models.IntegerField(verbose_name="库存", null=True)
    old_price = models.FloatField(verbose_name="原价", null=True, blank=True)
    price = models.FloatField(verbose_name="现价")
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True, null=True)

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"

    def save(self, **kwargs):
        if self.goods_id:
            try:
                goods = Goods.objects.get(id=self.goods_id)
            except Goods.DoesNotExist:
                pass
            else:
                sf = """
ft = goods.goodstype_set
if self.id:
    ft = goods.goodstype_set.filter(~models.Q(id=self.id))
max_price = ft.aggregate(max_price=models.Max('{0}price')).get('max_price')
min_price = ft.aggregate(min_price=models.Min('{0}price')).get('min_price')
if max_price is None:
    goods.max_{0}price = self.{0}price
else:
    goods.max_{0}price = max(max_price, self.{0}price)
if min_price is None:
    goods.min_{0}price = self.{0}price
else:
    goods.min_{0}price = min(min_price, self.{0}price)
                """
                exec sf.format('')
                exec sf.format('old_')
                goods.save()
        return super(GoodsType, self).save(**kwargs)

    def __unicode__(self):
        return self.description


class Address(models.Model):
    user = models.ForeignKey(User, verbose_name="用户", null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100, verbose_name="收件人", null=True)
    phone = models.CharField(max_length=100, verbose_name="电话", null=True)
    province = models.CharField(max_length=100, verbose_name="国家", null=True)
    city = models.CharField(max_length=100, verbose_name="省份", null=True)
    area = models.CharField(max_length=100, verbose_name="城市", null=True)
    detail = models.CharField(max_length=100, verbose_name="详细信息", null=True)
    is_default = models.BooleanField(verbose_name="是否默认地址", default=False)
    is_showing = models.BooleanField(verbose_name="是否显示", default=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True, null=True)

    class Meta:
        verbose_name = "用户地址"
        verbose_name_plural = "用户地址"

    def __unicode__(self):
        return self.receiver


class Order(models.Model):
    name = models.CharField(max_length=100, verbose_name="名称", null=True)
    description = models.CharField(max_length=1000, verbose_name="描述", null=True)
    remark = models.CharField(max_length=1000, verbose_name="留言", null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", null=True)
    expire_time = models.DateTimeField(verbose_name="过期时间", null=True)
    pay_time = models.DateTimeField(verbose_name="付款时间", null=True)
    finish_time = models.DateTimeField(verbose_name="完成时间", null=True)
    close_time = models.DateTimeField(verbose_name="关闭时间", null=True)
    user = models.ForeignKey(User, verbose_name="用户", null=True, on_delete=models.SET_NULL)
    address = models.ForeignKey(Address, verbose_name="收货地址", null=True, on_delete=models.SET_NULL)
    total_price = models.FloatField(verbose_name="总价", null=True, default=0)
    total_count = models.IntegerField(verbose_name="总数量", null=True, default=0)
    freight = models.FloatField(verbose_name="运费", null=True, default=0)
    status = models.IntegerField(verbose_name="订单状态",
                                 choices=((0, "待支付"), (1, "已完成"), (2, "已取消"), (3, "确认交易中"), (4, "安排发货中"),
                                          (5, "物流中")),
                                 null=True)
    pay_type = models.IntegerField(verbose_name="支付类型",
                                   choices=((0, "扫码支付"),),
                                   null=True, default=0)
    is_showing = models.BooleanField(verbose_name="是否显示", default=True)
    code = models.CharField(max_length=255, verbose_name="订单号", unique=True, null=True)
    express_code = models.CharField(null=True, verbose_name="快递单号", max_length=30)
    addressee_name = models.CharField(max_length=100, verbose_name="收件人", null=True)
    addressee_phone = models.CharField(max_length=100, verbose_name="电话", null=True)
    addressee_province = models.CharField(max_length=100, verbose_name="国家", null=True)
    addressee_city = models.CharField(max_length=100, verbose_name="省份", null=True)
    addressee_area = models.CharField(max_length=100, verbose_name="城市", null=True)
    addressee_detail = models.CharField(max_length=100, verbose_name="详细信息", null=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"

    def __unicode__(self):
        return self.code or ''


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='订单', null=True, on_delete=models.SET_NULL)
    goods_type = models.ForeignKey(GoodsType, null=True, verbose_name="商品", on_delete=models.SET_NULL)
    goods_type_name = models.CharField(verbose_name='型号', null=True, max_length=100)
    count = models.IntegerField(verbose_name="数量", null=True)
    price = models.FloatField(verbose_name="单价", null=True)
    name = models.CharField(verbose_name='名称', null=True, max_length=100)
    description = models.CharField(verbose_name="描述", null=True, max_length=1000, blank=True)
    img = models.FileField(verbose_name="图片", null=True, upload_to="order")

    class Meta:
        verbose_name = "订单条目"
        verbose_name_plural = "订单条目"

    def __unicode__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(User, verbose_name="用户", null=True, on_delete=models.SET_NULL)
    goods_type = models.ForeignKey(GoodsType, null=True, verbose_name="商品", on_delete=models.SET_NULL)
    count = models.IntegerField(verbose_name="数量", null=True)
    price = models.IntegerField(verbose_name="单价", null=True)
    name = models.CharField(verbose_name='名称', null=True, max_length=100)
    description = models.CharField(verbose_name="描述", null=True, max_length=1000)
    img = models.FileField(verbose_name="图片", null=True, upload_to="order")

    class Meta:
        verbose_name = "购物车条目"
        verbose_name_plural = "购物车条目"

    def __unicode__(self):
        return self.name


class PayQRCode(models.Model):
    img = models.FileField(verbose_name="图片", null=True, upload_to="payQRCode")
    price = models.FloatField(verbose_name="单价", null=True, blank=True, default=0)
    is_default = models.BooleanField(verbose_name="是否未设置价格的收款码", default=False)

    class Meta:
        verbose_name = "支付二维码"
        verbose_name_plural = "支付二维码"

    def __unicode__(self):
        return '{:.2f}'.format(self.price)


class Banner(models.Model):
    img = models.FileField(verbose_name="图片", null=True, upload_to="banner")
    title = models.CharField(verbose_name="标题", null=True, max_length=100)
    weight = models.IntegerField(null=True, verbose_name="权重", default=0)
    is_showing = models.BooleanField(verbose_name="是否显示", default=True)
    url = models.CharField(max_length=1000, verbose_name="跳转地址", null=True, blank=True)
    type = models.IntegerField(verbose_name="类型", choices=((0, "首页轮播图"),))
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    goods = models.ForeignKey(Goods, verbose_name="商品类", null=True, on_delete=models.SET_NULL, blank=True)

    class Meta:
        verbose_name = "轮播图"
        verbose_name_plural = "轮播图"

    def __unicode__(self):
        return self.title


class ExpressTrace(models.Model):
    last_update_time = models.DateTimeField(verbose_name="上次更新时间", null=True, editable=False)
    info = models.TextField(verbose_name="物流信息", null=True, editable=False)
    delivery_status = models.IntegerField(null=True, default=0,
                                          choices=((0, "待收递快件"), (1, "在途中"), (2, "派件中"),
                                                   (3, "已签收"), (4, "派送失败")), editable=False)
    is_sign = models.IntegerField(verbose_name="是否签收", choices=((0, "未签收"), (1, "已签收")), editable=False, null=True)
    express_code = models.CharField(null=True, verbose_name="快递单号", max_length=30)
    express_type = models.CharField(null=True, verbose_name="快递类型", max_length=10,
                                    choices=EXPRESS_TYPES)

    class Meta:
        verbose_name = "物流信息"
        verbose_name_plural = "物流信息"

    def __unicode__(self):
        return self.express_number or ''

