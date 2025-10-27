# core/serializers.py
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, VendorProfile, BodabodaProfile, Product, Category, Order


class RegisterCustomerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(user_type='customer', **validated_data)
        return user


class RegisterVendorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    business_name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password', 'password2', 'business_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        business_name = validated_data.pop('business_name')
        validated_data.pop('password2')
        user = User.objects.create_user(user_type='vendor', **validated_data)
        VendorProfile.objects.create(user=user, business_name=business_name)
        return user


class RegisterBodabodaSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    plate_number = serializers.CharField(write_only=True, required=True)
    id_number = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'phone', 'password', 'password2', 'plate_number', 'id_number')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        plate = validated_data.pop('plate_number')
        id_num = validated_data.pop('id_number')
        validated_data.pop('password2')
        user = User.objects.create_user(user_type='bodaboda', email='', **validated_data)
        BodabodaProfile.objects.create(user=user, plate_number=plate, id_number=id_num)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        token['phone'] = user.phone
        return token


class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.vendor_profile.business_name', read_only=True)
    vendor_image = serializers.ImageField(source='vendor.profile_image', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image', 'category', 'vendor_name', 'vendor_image']


# core/serializers.py
class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    customer_location_available = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'product', 'quantity', 'total_price', 'status',
            'bodaboda', 'delivery_address', 'created_at', 'delivered_at',
            'claimed_at', 'claimed_by', 'is_delivered',
            'product_name', 'customer_location_available'
        ]
        extra_kwargs = {
            'customer': {'read_only': True}, 
            'bodaboda': {'read_only': True}, 
            'total_price': {'read_only': True}, 
            'status': {'read_only': True}, 
            'product': {'required': True},
            'quantity': {'required': True},
            'delivery_address': {'required': True, 'write_only': False},
        }

    def get_customer_location_available(self, obj):
        return bool(obj.customer and obj.customer.latitude and obj.customer.longitude)
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']