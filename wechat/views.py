# coding=utf-8
import models, json, serializers
from django.shortcuts import render
from rest_framework.decorators import api_view
from tinyStore.settings import WX_API_Jscode2session, STATUS_SUCCESS, STATUS_ERROR
from tinyStore.utils import get_no_empty_dict
import requests
from django.db.models import Q
from django.http import JsonResponse
from django.utils.translation import ugettext as _
import datetime, time


# Create your views here.


def error_resp(msg, data=None):
    """
    通用的错误响应
    :param msg:错误描述
    :param data:错误响应内容
    :return:JsonResponse
    """
    return common_resp(data, msg, STATUS_ERROR)


def success_resp(data, msg):
    """
    通用的成功响应
    :param data:响应内容
    :param msg:成功描述
    :param integer_status:是否返回整形status，默认为否
    :return:JsonResponse
    """
    return common_resp(data, msg, STATUS_SUCCESS)


def common_resp(data, msg, status):
    """
    通用的响应
    :param data:响应内容
    :param msg:响应消息
    :param status:响应状态
    :return:JsonResponse
    """
    return JsonResponse(get_no_empty_dict({'data': data, 'msg': msg, 'status': status}))


def read_dict(request):
    """
    将request获取到的值json.loads为python数据格式
    :param request:
    :return:
    """
    try:
        req = request.read()
        dic = json.loads(req)
    except Exception as e:
        print e.message
        return {}
    return dic


@api_view(['GET'])
def h5_auth(request):
    try:
        user = models.User.objects.get(openid="h5-test")
    except models.User.DoesNotExist:
        user = models.User(openid="h5-test",
                           nickname="Test",
                           language="zh_CN")
        user.save()
    request.session["openid"] = "h5-test"
    print serializers.UserSerializer(user).data
    return success_resp(data=serializers.UserSerializer(user).data,
                        msg="授权登陆成功")


@api_view(['POST'])
def wx_auth(request):
    """
    微信授权
    :param request:
    :return:
    """
    req_data = read_dict(request)
    code = req_data.get("code")
    if not code:
        print "授权登陆失败：code缺失"
        return error_resp("授权登陆失败")
    # 调用第三方（微信）接口，使用 code 换取 openid 和 session_key 等信息
    url = WX_API_Jscode2session % code
    resp = requests.get(url)
    wx_data = None
    if resp.status_code == 200:
        wx_data = json.loads(resp.text)
    if (not wx_data) or resp.status_code != 200:
        print "授权登陆失败：调用微信第三方接口失败"
        return error_resp("授权登陆失败")
    openid = wx_data.get('openid')
    if not openid:
        print "授权登陆失败：调用微信第三方接口返回数据中不包含openid"
        return error_resp("授权登陆失败")
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        user = models.User()
    user.openid = openid
    user.nickname = req_data.get("nickName")
    user.avatarurl = req_data.get("avatarUrl")
    user.country = req_data.get("country")
    user.province = req_data.get("province")
    user.city = req_data.get("city")
    user.gender = req_data.get("gender")
    user.language = req_data.get("language")
    user.last_login_time = datetime.datetime.now()
    user.save()
    # 将用户openid添加至cookie
    request.session["openid"] = user.openid
    return success_resp(data={}, msg="授权登陆成功")


@api_view(['GET'])
def index_data(request):
    """
    获取轮播图和商品信息
    :param request:http请求体
            参数：
            无
    :return:http响应体>轮播图列表的json数据
    """
    banners = models.Banner.objects.filter(is_showing=True, type=0).order_by("-weight", "-create_time").all()
    goods = models.Goods.objects.filter(is_showing=True).order_by("-weight", "-create_time").all()
    return success_resp({
        "banners": serializers.BannerSerializer(banners, many=True).data,
        "goodses": serializers.IndexGoodsSerializer(goods, many=True).data
    }, _(u"获取首页数据成功"))


@api_view(['GET'])
def goods_detail(request):
    """
    获取商品类信息
    :param request:
    :return:
    """
    goods_id = request.GET.get("goods_id")
    if (not goods_id) or goods_id == "undefined":
        return error_resp("无效的商品ID")
    try:
        goods = models.Goods.objects.get(id=goods_id)
    except models.Goods.DoesNotExist:
        print "查询商品失败：无效的商品ID%s" % goods_id
        return error_resp("无效的商品ID")
    goods_types = goods.goodstype_set.filter(is_showing=True).order_by("description").all()
    return success_resp({
        "goods": serializers.IndexGoodsSerializer(goods).data,
        "goods_types": serializers.GoodsTypeSerializer(goods_types, many=True).data
    }, _(u"获取商品详情数据成功"))


@api_view(['GET'])
def order_confirm_data(request):
    """
    获取确认订单页的数据：用户收货地址，订单商品条目，价格
    :param request:
    :return:
    """
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "查询用户失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    req_datas = request.GET.get("goods_types")
    if not req_datas:
        print "查询订单数据失败：无效的参数"
        return error_resp("无效的参数")

    total_price = total_count = 0
    freight = 0
    req_datas = json.loads(req_datas)
    # 获取订单数据
    order_datas = []
    for req_data in req_datas:
        try:
            goods_type = models.GoodsType.objects.get(id=req_data["id"])
        except models.GoodsType.DoesNotExist:
            continue
        count = req_data["count"]
        total_count += count
        total_price += (goods_type.price * count)
        order_data = {"id": goods_type.id,
                      "img": goods_type.img.url,
                      "name": goods_type.goods.name,
                      "goods_type_name": goods_type.description,
                      "price": goods_type.price,
                      "count": count}
        order_datas.append(order_data)
    addresses = user.address_set.filter(is_showing=True).order_by("-is_default", "-create_time")
    return success_resp({
        "total_price": round(total_price, 2),
        "total_count": total_count,
        "freight": freight,
        "addresses": serializers.AddressSerializer(addresses, many=True).data,
        "order_datas": order_datas
    }, _(u"获取订单确认数据成功"))


@api_view(['POST'])
def address_edit(request):
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "查询用户失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    req_data = read_dict(request)
    if not req_data:
        print "添加地址失败：无效的参数"
        return error_resp("无效的参数")
    if req_data.get("is_default"):
        user.address_set.filter(is_default=True).update(is_default=False)
    else:
        if user.address_set.filter(is_showing=True, is_default=True).count() == 0:
            req_data["is_default"] = True
    address_id = req_data.pop("id", None)
    if address_id:
        ft = user.address_set.filter(~Q(id=address_id), is_showing=True)
        if req_data.get("is_showing") == False and ft.filter(is_default=True).count() == 0:
            first_addr = ft.order_by("-create_time").first()
            first_addr.is_default = True
            first_addr.save()
        try:
            address = models.Address.objects.get(id=address_id)
        except models.Address.DoesNotExist:
            print "修改地址失败：无效的ID%s" % address_id
            return error_resp("无效的地址ID")
    else:
        address = models.Address()
    address.user = user
    for k, v in req_data.iteritems():
        setattr(address, k, v)
    address.save()
    return success_resp({}, _(u"添加地址成功"))


@api_view(['GET'])
def address_list(request):
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "查询用户失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    addresses = user.address_set.filter(is_showing=True).order_by("-is_default", "-create_time")
    return success_resp({
        "addresses": serializers.AddressSerializer(addresses, many=True).data,
    }, _(u"获取用户地址数据成功"))


@api_view(['GET'])
def address_detail(request):
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "查询地址详情失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    address_id = request.GET.get("id")
    if not address_id:
        print "查询地址详情失败：地址ID为空"
        return error_resp("无效的地址ID")
    try:
        address = user.address_set.get(is_showing=True, id=address_id)
    except models.Address.DoesNotExist:
        print "查询地址详情失败：无效的地址ID %s" % address_id
        return error_resp("无效的地址ID")
    return success_resp({
        "address": serializers.AddressSerializer(address).data,
    }, _(u"获取用户地址详情数据成功"))


@api_view(['POST'])
def order_submit(request):
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "创建订单失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    req_data = read_dict(request)
    address_id = req_data.get("address_id")
    try:
        address = models.Address.objects.get(id=address_id)
    except models.Address.DoesNotExist:
        print "创建订单失败：无效的地址ID%s" % address_id
        return error_resp("无效的用户地址")
    order = None
    remark = req_data.get("remark")
    total_price = total_count = 0
    freight = 0
    order_name = ""
    for order_data in req_data.get("order_datas", []):
        goods_type_id = order_data.get("id")
        goods_type_count = order_data.get("count")
        try:
            goods_type = models.GoodsType.objects.get(id=goods_type_id, count__gt=0, is_showing=True)
        except models.GoodsType.DoesNotExist:
            continue
        if not goods_type_count:
            continue
        if order is None:
            order = models.Order(
                user=user,
                address=address,
                freight=freight,
                status=0,
                remark=remark,
                addressee_name=address.name,
                addressee_phone=address.phone,
                addressee_province=address.province,
                addressee_city=address.city,
                addressee_area=address.area,
                addressee_detail=address.detail
            )
            order.save()
        models.OrderItem(
            order=order,
            goods_type=goods_type,
            count=goods_type_count,
            price=goods_type.price,
            name=goods_type.goods.name,
            goods_type_name=goods_type.description,
            description=goods_type.goods.description,
            img=goods_type.img
        ).save()
        total_count += goods_type_count
        total_price += (goods_type_count * goods_type.price)
        if goods_type.goods.name:
            order_name += (goods_type.goods.name + u"、")
    if order is None:
        print "创建订单失败：无效的订单数据"
        return error_resp("创建订单失败")
    order.total_count = total_count
    order.total_price = round(total_price, 2)
    order.code = "{:.0f}".format(time.time()) + "{:0>5d}".format(order.id)

    if order_name:
        order.name = order_name[:-1]
    order.save()
    return success_resp({"order_id": order.id}, _(u"创建订单成功"))


@api_view(['GET'])
def qrcode_data(request):
    """
    获取付款码
    :param request: 订单ID
    :return:
    """
    order_ids = request.GET.get("order_ids")
    if not order_ids:
        print "查询付款码失败：关键参数缺失"
        return error_resp("无效的订单ID")
    orders = models.Order.objects.filter(id__in=json.loads(order_ids))
    if orders.count() == 0:
        print "查询付款码失败：无效的订单ID%s" % order_ids
        return error_resp("无效的订单ID")
    total_price = 0
    for order in orders:
        total_price += order.total_price + order.freight
    qrcode = models.PayQRCode.objects.filter(price=total_price).order_by("-id").first()
    if qrcode is None:
        qrcode = models.PayQRCode.objects.filter(is_default=True).order_by("-id").first()
    if qrcode is None:
        print "查询付款码失败：无法获取价格（%s）对应的付款码" % total_price
        return error_resp("获取付款码失败")
    return success_resp({
        "qrcode": qrcode.img.url,
        "qrcode_price": total_price
    }, _(u"获取付款码成功"))


@api_view(['GET'])
def order_list(request):
    """
    查询用户的订单列表
    :param request:
    :return:
    """
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "查询用户订单列表失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    status = request.GET.get('status')
    if status is None or (not str(status).isdigit()):
        print "查询用户订单列表失败：无效的状态码%s" % status
        return error_resp("无效的状态码")
    status = int(status)
    if status in (0, 1, 2):
        orders = user.order_set.filter(status=status).order_by("-create_time").all()
    else:
        orders = user.order_set.filter(~Q(status__in=(0, 1, 2))).order_by("status", "-create_time").all()
    return success_resp(serializers.OrderListSerializer(orders, many=type).data,
                        _(u"获取用户订单成功"))


@api_view(['POST'])
def order_edit(request):
    """
    更改订单的状态
    :param request:
    :return:
    """
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "修改用户订单失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    req_data = read_dict(request)
    order_ids = req_data.get("order_ids")
    if not order_ids:
        print "修改用户订单失败：订单ID为空"
        return error_resp("无效的订单ID")
    orders = user.order_set.filter(id__in=order_ids)
    if orders.count() == 0:
        print "修改用户订单失败：无效的订单ID%s" % order_ids
        return error_resp("无效的订单ID")
    status = req_data.get("status")
    if status is None or (not str(status).isdigit()):
        print "修改用户订单失败：无效的状态码%s" % status
        return error_resp("无效的状态码")
    status = int(status)
    for order in orders:
        order.status = status
        if status == 3:
            order.pay_time = datetime.datetime.now()
        elif status == 2:
            order.close_time = datetime.datetime.now()
        order.save()
    return success_resp({}, _(u"修改订单数据成功"))


@api_view(['GET'])
def order_detail(request):
    openid = request.session["openid"]
    try:
        user = models.User.objects.get(openid=openid)
    except models.User.DoesNotExist:
        print "查询用户订单详情失败：无效的用户ID%s" % openid
        return error_resp("无效的用户ID")
    order_id = request.GET.get("id")
    try:
        order = user.order_set.get(id=order_id)
        order.create_time += datetime.timedelta(hours=8)
    except models.Order.DoesNotExist:
        print "查询用户订单详情失败：无效的订单ID%s" % order_id
        return error_resp("无效的订单ID")
    res_data = serializers.OrderSerializer(order).data
    express_trace = None
    if order.express_code:
        express_trace = models.ExpressTrace.objects.filter(express_code=order.express_code).order_by("-id").first()
    if express_trace:
        try:
            res_data["expresstrace_set"] = eval(express_trace.info)
        except Exception:
            pass
    return success_resp(res_data, _(u"获取订单详情数据成功"))


@api_view(['GET'])
def cart_list(request):
    """
    获取购物车页的数据：订单商品条目，数量
    :param request:
    :return:
    """
    req_datas = request.GET.get("goods_types")
    if not req_datas:
        print "查询订单数据失败：无效的参数"
        return error_resp("无效的参数")
    req_datas = json.loads(req_datas)
    datas = []
    for req_data in req_datas:
        try:
            goods_type = models.GoodsType.objects.get(id=int(req_data["id"]))
        except models.GoodsType.DoesNotExist:
            continue
        data = serializers.GoodsTypeCartSerializer(goods_type).data
        data['select_count'] = min(int(req_data["count"]), goods_type.count)
        datas.append(data)
    return success_resp({"cart_list": datas}, _(u"获取购物车数据成功"))
