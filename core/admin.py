# core/admin.py
from django.contrib import admin
from .models import User, VendorProfile, BodabodaProfile, Category, Product, Order
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# ======================
#  Custom User Admin
# ======================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'profile_image', 'latitude', 'longitude')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {
            'fields': ('user_type', 'phone'),
        }),
    )

    list_display = ('username', 'email', 'phone', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')
    ordering = ('id',)


# ======================
#  Vendor Profile Admin
# ======================
@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'license_number', 'location_description')
    search_fields = ('business_name', 'user__username', 'license_number')
    list_filter = ('user__user_type',)


# ======================
#  Bodaboda Profile Admin
# ======================
@admin.register(BodabodaProfile)
class BodabodaProfileAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'user', 'verified', 'is_available')
    list_filter = ('verified', 'is_available')
    search_fields = ('plate_number', 'id_number', 'user__username')


# ======================
#  Category Admin
# ======================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


# ======================
#  Product Admin
# ======================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'price', 'category', 'is_available', 'created_at')
    list_filter = ('is_available', 'category', 'vendor__user_type')
    search_fields = ('name', 'vendor__username', 'category__name')
    list_select_related = ('vendor', 'category')
    readonly_fields = ('created_at',)


# ======================
#  Order Admin
# ======================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'quantity', 'total_price', 'status', 'bodaboda', 'created_at', 'delivered_at')
    list_filter = ('status', 'created_at', 'delivered_at')
    search_fields = ('customer__username', 'bodaboda__username', 'product__name')
    list_select_related = ('customer', 'product', 'bodaboda')
    readonly_fields = ('created_at', 'delivered_at')

    # Optional: Group fields nicely
    fieldsets = (
        ('Order Info', {
            'fields': ('customer', 'product', 'quantity', 'total_price', 'status')
        }),
        ('Delivery', {
            'fields': ('bodaboda', 'delivery_address', 'created_at', 'delivered_at')
        }),
    )
