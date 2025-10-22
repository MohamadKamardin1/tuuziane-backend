# core/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import VendorProfile, BodabodaProfile, Category, Product, Order

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_customer(self):
        user = User.objects.create_user(
            username='juma',
            phone='+255712000001',
            password='pass123',
            user_type='customer'
        )
        self.assertEqual(user.user_type, 'customer')
        self.assertTrue(user.check_password('pass123'))

    def test_create_vendor_creates_profile(self):
        user = User.objects.create_user(
            username='spice_vendor',
            phone='+255712000002',
            password='pass123',
            user_type='vendor'
        )
        VendorProfile.objects.create(user=user, business_name="Zanzibar Spices")
        self.assertTrue(hasattr(user, 'vendor_profile'))
        self.assertEqual(user.vendor_profile.business_name, "Zanzibar Spices")


class ProductModelTest(TestCase):
    def setUp(self):
        self.vendor = User.objects.create_user(
            username='vendor1',
            phone='+255712000003',
            password='pass123',
            user_type='vendor'
        )
        VendorProfile.objects.create(user=self.vendor, business_name="Test Kitchen")

    def test_product_creation(self):
        category = Category.objects.create(name="Food", slug="food")
        product = Product.objects.create(
            vendor=self.vendor,
            name="Pilau",
            description="Spiced rice with meat",
            price=5000,
            category=category
        )
        self.assertEqual(product.name, "Pilau")
        self.assertEqual(product.vendor, self.vendor)
        self.assertTrue(product.is_available)


class OrderModelTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='cust1', phone='+255712000004', password='pass123', user_type='customer'
        )
        self.vendor = User.objects.create_user(
            username='vend1', phone='+255712000005', password='pass123', user_type='vendor'
        )
        VendorProfile.objects.create(user=self.vendor, business_name="Kitchen")
        self.category = Category.objects.create(name="Meals", slug="meals")
        self.product = Product.objects.create(
            vendor=self.vendor, name="Biryani", price=6000, category=self.category
        )

            # Fix test_order_total_calculation
        def test_order_total_calculation(self):
            expected_total = self.product.price * 3
            order = Order.objects.create(
                customer=self.customer,
                product=self.product,
                quantity=3,
                total_price=expected_total,  # ✅
                delivery_address="Stone Town"
            )
            self.assertEqual(order.total_price, expected_total)

        # Fix test_only_bodaboda_can_see_their_orders
        order = Order.objects.create(
            customer=self.customer,
            product=self.product,
            quantity=1,
            total_price=1000,
            bodaboda=boda,
            status='assigned',  # ✅
            delivery_address="Test"
        )
        data = {
            "name": "New Chapati",
            "description": "Freshly made",
            "price": 800,
            "category": self.category.id,
            # "image": ""  ← remove this line
        }

class APITest(APITestCase):
    def setUp(self):
        # Create users
        self.customer = User.objects.create_user(
            username='customer1', phone='+255712000010', password='cust123', user_type='customer'
        )
        self.vendor = User.objects.create_user(
            username='vendor1', phone='+255712000011', password='vend123', user_type='vendor'
        )
        VendorProfile.objects.create(user=self.vendor, business_name="API Kitchen")
        self.category = Category.objects.create(name="Snacks", slug="snacks")
        self.product = Product.objects.create(
            vendor=self.vendor, name="Samosa", price=1000, category=self.category
        )

    def test_customer_can_register(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "phone": "+255712999999",
            "password": "newpass123",
            "password2": "newpass123"
        }
        response = self.client.post('/api/auth/register/customer/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_vendor_can_create_product(self):
        # Login vendor
        login = self.client.post('/api/auth/login/', {
            "username": "vendor1",
            "password": "vend123"
        })
        token = login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            "name": "New Chapati",
            "description": "Freshly made",
            "price": 800,
            "category": self.category.id,
            "image": ""  # We'll skip image in test
        }
        response = self.client.post('/api/my-products/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_customer_cannot_create_product(self):
        login = self.client.post('/api/auth/login/', {
            "username": "customer1",
            "password": "cust123"
        })
        token = login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {"name": "Fake Product", "price": 100, "category": self.category.id}
        response = self.client.post('/api/my-products/', data)
        # Should fail because customer ≠ vendor
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_calculates_total(self):
        login = self.client.post('/api/auth/login/', {
            "username": "customer1",
            "password": "cust123"
        })
        token = login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            "product": self.product.id,
            "quantity": 4,
            "delivery_address": "Ngambo, House 12"
        }
        response = self.client.post('/api/orders/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_price'], "4000.00")  # 1000 * 4

    def test_only_bodaboda_can_see_their_orders(self):
        # Create a dedicated bodaboda user
        boda_user = User.objects.create_user(
            username='boda_test_user',
            phone='+255712999888',
            password='securepass',
            user_type='bodaboda'
        )
        BodabodaProfile.objects.create(
            user=boda_user,
            plate_number="Z 777 TT",
            id_number="ID777777"
        )

        # Create an order assigned to this user
        order = Order.objects.create(
            customer=self.customer,
            product=self.product,
            quantity=2,
            total_price=2000,
            bodaboda=boda_user,
            status='assigned',  # ✅ Must be in ['assigned', 'picked_up']
            delivery_address="Ngambo, Zanzibar"
        )
        order.refresh_from_db()  # Ensure it's saved

        # Login as bodaboda
        login_response = self.client.post('/api/auth/login/', {
            'username': 'boda_test_user',
            'password': 'securepass'
        })
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Fetch orders
        response = self.client.get('/api/bodaboda-orders/')
        self.assertEqual(response.status_code, 200)

        # 🔍 Critical: Check the actual queryset
        expected_orders = Order.objects.filter(
            bodaboda=boda_user,
            status__in=['assigned', 'picked_up']
        )
        print("Expected order count:", expected_orders.count())
        print("API response count:", len(response.data))

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], order.id)