from django.urls import path
from . import views
urlpatterns = [
    path('', views.HomePage.as_view(), name = 'home-page' ),
    path('products/<slug:slug>/', views.SingleProduct.as_view(), name = 'single-product'),
    path('collections/<str:type>/', views.ProductsShop.as_view(),name = 'products-shop'),
    path('brand/<slug:slug>', views.ProductsByBrand.as_view(), name = 'products-by-brand'),
    path('search/', views.SearchProduct.as_view(), name='search-product'),
    path('instrument/<slug:slug>',views.ProductsByType.as_view(),name='products-by-type'),
    path('category/<slug:slug>',views.ProductsByCategory.as_view(), name='products-by-category'),
    path('brand/all/', views.ShowAllBrands.as_view(), name='all-brands'),
    path('get-product/', views.get_product, name='get-product'),
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.ProductsCart.as_view(),name='show-cart'),
    path('delete-in-cart/', views.delete_in_cart, name='delete-in-cart'),
    path('checkout/', views.Checkout.as_view(), name='check-out'),

    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.logout, name = 'logout'),
    path('register/', views.Register.as_view(), name = 'register'),
    path('activate/<uidb64>/<token>/', views.activate_user, name='activate'),
    path('password-recover/', views.PasswordRecover.as_view(), name='password-recover'),
    path('password-confirm/<uidb64>/<token>/', views.PasswordRecoverConfirm.as_view(), name='password-recover-confirm'),
    path('personal/', views.PersonalInfo.as_view(), name='personal-info'),
]