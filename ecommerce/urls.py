from django.urls import path
from . import views
urlpatterns = [
    path('', views.Home.as_view(), name = 'home' ),
    path('product/', views.SingleProduct.as_view(), name = 'single-product')
]