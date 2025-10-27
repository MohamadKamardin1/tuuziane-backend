# core/views.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from exponent_server_sdk import PushClient, PushMessage
from .models import BodabodaDevice

import cloudinary.uploader
from .models import Product, Category, Order, User
from .serializers import (
    RegisterCustomerSerializer,
    RegisterVendorSerializer,
    RegisterBodabodaSerializer,
    CustomTokenObtainPairSerializer,
    ProductSerializer,
    CategorySerializer,
    OrderSerializer
)


# ======================
# AUTHENTICATION
# ======================

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'phone': request.user.phone,
        'user_type': request.user.user_type,
    })


# ======================
# PERMISSIONS
# ======================

class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'vendor'


# ======================
# PRODUCTS & CATEGORIES
# ======================

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset

    def get_serializer_context(self):
        return {'request': self.request}


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
    lookup_field = 'pk'

    def get_serializer_context(self):
        return {'request': self.request}


class VendorProductListView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)

    def perform_create(self, serializer):
        image = self.request.FILES.get('image')
        image_url = None

        if image:
            try:
                upload_result = cloudinary.uploader.upload(
                    image,
                    folder="tuuziane/products",
                    resource_type="image"
                )
                image_url = upload_result['secure_url']
            except Exception as e:
                print("Cloudinary upload error:", e)

        serializer.save(vendor=self.request.user, image=image_url)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


# ======================
# ORDERS (Customer)
# ======================

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    

    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        total = product.price * quantity
        order = serializer.save(
            customer=self.request.user,
            total_price=total,
            status='pending'
        )

        try:
            tokens = BodabodaDevice.objects.filter(
                is_active=True,
                user__bodaboda_profile__verified=True
            ).values_list('expo_token', flat=True)

            valid_tokens = [token for token in tokens if PushClient.is_exponent_push_token(token)]
            
            if valid_tokens:
                client = PushClient()
                messages = [
                    PushMessage(
                        to=token,
                        title="New Order Available!",
                        body=f"{product.name} • TZS {total:,}",
                        data={"order_id": order.id},
                        sound="default"
                    )
                    for token in valid_tokens
                ]
                client.publish_multiple(messages)
        except Exception as e:
            print("Push notification error:", e)


class CustomerOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)


# ======================
# BODABODA ORDERS & ACTIONS
# ======================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_orders(request):
    if request.user.user_type != 'bodaboda':
        return Response({"error": "Only bodabodas"}, status=403)
    orders = Order.objects.filter(
        status='pending',
        claimed_by__isnull=True
    ).select_related('customer', 'product')
    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_claimed_orders(request):
    if request.user.user_type != 'bodaboda':
        return Response({"error": "Only bodabodas"}, status=403)
    orders = Order.objects.filter(claimed_by=request.user).exclude(status='delivered')
    return Response(OrderSerializer(orders, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_order(request, order_id):
    if request.user.user_type != 'bodaboda':
        return Response({"error": "Only bodabodas can claim orders"}, status=403)
    
    with transaction.atomic():
        order = get_object_or_404(Order, id=order_id, status='pending')
        if order.claimed_by is not None:
            return Response({"error": "Order already claimed"}, status=409)
        
        order.claimed_by = request.user
        order.claimed_at = timezone.now()
        order.status = 'assigned'
        order.save()
    
    return Response({"status": "Order claimed successfully"}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id, claimed_by=request.user)
    order.status = 'delivered'
    order.is_delivered = True
    order.delivered_at = timezone.now()
    
    # Increase bodaboda rating
    from django.db.models import F
    profile = request.user.bodaboda_profile
    profile.rating = F('rating') + 1
    profile.save(update_fields=['rating'])
    
    order.save()
    return Response({"status": "Delivery completed"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_phone(request, order_id):
    if request.user.user_type != 'bodaboda':
        return Response({"error": "Access denied"}, status=403)
    
    order = get_object_or_404(Order, id=order_id, claimed_by=request.user)
    return Response({"phone": order.customer.phone})


# ======================
# LOCATION
# ======================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_location(request):
    if request.user.user_type != 'bodaboda':
        return Response(
            {"error": "Only bodaboda riders can update location"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    lat = request.data.get('latitude')
    lng = request.data.get('longitude')
    
    if lat is None or lng is None:
        return Response(
            {"error": "latitude and longitude are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        request.user.latitude = float(lat)
        request.user.longitude = float(lng)
        request.user.save(update_fields=['latitude', 'longitude'])
        return Response({"status": "Location updated"}, status=status.HTTP_200_OK)
    except (ValueError, TypeError):
        return Response(
            {"error": "Invalid coordinates"},
            status=status.HTTP_400_BAD_REQUEST
        )


# core/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bodaboda_order_detail(request, order_id):
    """Bodaboda can view details of an order (claimed or unclaimed)"""
    if request.user.user_type != 'bodaboda':
        return Response({"error": "Access denied"}, status=403)
    
    # Allow viewing any order (claimed or not) — useful before claiming
    order = get_object_or_404(Order, id=order_id)
    
    # Optional: Only allow if order is nearby or claimed by this rider
    # But for simplicity, allow all (since it's public info like address)
    
    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data)


# core/views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_device_token(request):
    if request.user.user_type != 'bodaboda':
        return Response({"error": "Only bodabodas"}, status=403)
    
    token = request.data.get('expo_token')
    if not token:
        return Response({"error": "expo_token required"}, status=400)
    
    BodabodaDevice.objects.update_or_create(
        expo_token=token,
        defaults={'user': request.user, 'is_active': True}
    )
    return Response({"status": "Token saved"})