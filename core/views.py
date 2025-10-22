# core/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Product, Category, Order, User
from rest_framework.permissions import BasePermission

from .serializers import (
    RegisterCustomerSerializer,
    RegisterVendorSerializer,
    RegisterBodabodaSerializer,
    CustomTokenObtainPairSerializer,
    ProductSerializer,
    CategorySerializer,
    OrderSerializer
)

# AUTH
class RegisterCustomerView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterCustomerSerializer
    permission_classes = [AllowAny]

class RegisterVendorView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterVendorSerializer
    permission_classes = [AllowAny]

class RegisterBodabodaView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterBodabodaSerializer
    permission_classes = [AllowAny]

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# PRODUCTS
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # Anyone can browse

    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset

# core/views.py

class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'vendor'

class VendorProductListView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)


# CATEGORIES
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


# ORDERS
class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        total = product.price * quantity
        serializer.save(customer=self.request.user, total_price=total)


class CustomerOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)


class BodabodaOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type != 'bodaboda':
            return Order.objects.none()
        return Order.objects.filter(bodaboda=self.request.user, status__in=['assigned', 'picked_up'])