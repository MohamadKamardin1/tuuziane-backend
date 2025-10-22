# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, VendorProfile, BodabodaProfile, Product, Category, Order

# --- USER REGISTRATION ---
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
        user = User.objects.create_user(
            user_type='customer',
            **validated_data
        )
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
        user = User.objects.create_user(
            user_type='vendor',
            **validated_data
        )
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
        user = User.objects.create_user(
            user_type='bodaboda',
            email='',  # optional for bodaboda
            **validated_data
        )
        BodabodaProfile.objects.create(
            user=user,
            plate_number=plate,
            id_number=id_num
        )
        return user


# --- LOGIN (JWT) ---
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        token['phone'] = user.phone
        return token


# --- PRODUCT SERIALIZER ---
class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.vendor_profile.business_name', read_only=True)
    vendor_image = serializers.ImageField(source='vendor.profile_image', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image', 'category', 'vendor_name', 'vendor_image']


# --- ORDER SERIALIZER ---
class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    bodaboda_name = serializers.CharField(source='bodaboda.username', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('customer', 'total_price', 'created_at')


# --- CATEGORY SERIALIZER ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']