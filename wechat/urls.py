from django.conf.urls import url
from wechat import views

urlpatterns = [
    url(r'^auth$', views.wx_auth),
    url(r'^h5_auth$', views.h5_auth),
    url(r'^index_data$', views.index_data),
    url(r'^qrcode_data$', views.qrcode_data),

    url(r'^goods_list$', views.goods_list),
    url(r'^goods_detail$', views.goods_detail),
    url(r'^cart_list$', views.cart_list),

    url(r'^address_edit$', views.address_edit),
    url(r'^address_list$', views.address_list),
    url(r'^address_detail$', views.address_detail),

    url(r'^order_list$', views.order_list),
    url(r'^order_edit$', views.order_edit),
    url(r'^order_detail$', views.order_detail),
    url(r'^order_confirm_data$', views.order_confirm_data),
    url(r'^order_submit$', views.order_submit)
]