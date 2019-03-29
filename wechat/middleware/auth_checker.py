# coding=utf-8
from django.http import JsonResponse
from tinyStore.settings import STATUS_NONE_AUTH

class AuthMiddleWare():

    def process_request(self, request):
        if request.path.startswith("/admin"):
            return
        if request.path.startswith("/assets"):
            return
        if request.path.startswith("/tinystore/auth"):
            return
        openid = request.session.get('openid', None)
        if openid is None:
            return JsonResponse({
                "status": STATUS_NONE_AUTH,
                "msg": "未能获取openid，请重新授权登陆"
            })