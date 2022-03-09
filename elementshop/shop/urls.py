from django.urls import path
from . import views

app_name    = "shop"
urlpatterns = [
    path('', views.index, name="index"),
    path('<uuid:pk>/', views.product, name="product"), #商品のID
    path('cart/', views.cart, name="cart"),
    path('cart/<uuid:pk>/', views.cart, name="cart_single"), #カートのID
]

