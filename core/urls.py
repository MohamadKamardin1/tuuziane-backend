# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/customer/', views.RegisterCustomerView.as_view()),
    path('auth/register/vendor/', views.RegisterVendorView.as_view()),
    path('auth/register/bodaboda/', views.RegisterBodabodaView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('auth/user/', views.user_profile, name='user-profile'),

    # Products
    path('products/', views.ProductListView.as_view()),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('my-products/', views.VendorProductListView.as_view()),

    # Categories
    path('categories/', views.CategoryListView.as_view()),

    # Orders
    path('orders/', views.OrderCreateView.as_view()),
    path('my-orders/', views.CustomerOrderListView.as_view()),

    # Bodaboda
    path('bodaboda/orders/nearby/', views.nearby_orders, name='nearby-orders'),
    path('bodaboda/my-orders/', views.my_claimed_orders, name='my-claimed-orders'),
    path('bodaboda/order/<int:order_id>/claim/', views.claim_order, name='claim-order'),
    path('bodaboda/order/<int:order_id>/complete/', views.complete_delivery, name='complete-delivery'),
    path('bodaboda/order/<int:order_id>/customer-phone/', views.get_customer_phone, name='customer-phone'),
    path('bodaboda/order/<int:order_id>/', views.get_bodaboda_order_detail, name='bodaboda-order-detail'),

    # Location
    path('location/update/', views.update_location, name='update-location'),

    path('bodaboda/device-token/', views.save_device_token, name='save-device-token'),
]