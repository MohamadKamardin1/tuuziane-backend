from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/customer/', views.RegisterCustomerView.as_view()),
    path('auth/register/vendor/', views.RegisterVendorView.as_view()),
    path('auth/register/bodaboda/', views.RegisterBodabodaView.as_view()),
    path('auth/login/', views.LoginView.as_view()),

    # Products
    path('products/', views.ProductListView.as_view()),
    path('my-products/', views.VendorProductListView.as_view()),

    # Categories
    path('categories/', views.CategoryListView.as_view()),

    # Orders
    path('orders/', views.OrderCreateView.as_view()),
    path('my-orders/', views.CustomerOrderListView.as_view()),
    path('bodaboda-orders/', views.BodabodaOrderListView.as_view()),
]