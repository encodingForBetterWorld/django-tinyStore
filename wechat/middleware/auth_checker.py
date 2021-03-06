# coding=utf-8
from django.http import JsonResponse
from tinyStore.settings import STATUS_NONE_AUTH

class AuthMiddleWare():

    def process_request(self, request):
        if not request.path.startswith("/api"):
            return
        if request.path.startswith("/api/auth"):
            return
        if request.path.startswith("/api/h5_auth"):
            return
        openid = request.session.get('openid', None)
        if openid is None:
            return JsonResponse({
                "status": STATUS_NONE_AUTH,
                "msg": "未能获取openid，请重新授权登陆"
            })