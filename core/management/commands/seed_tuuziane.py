# core/management/commands/seed_tuuziane.py
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import VendorProfile, BodabodaProfile, Category, Product, Order
from django.utils.text import slugify

User = get_user_model()

# Realistic fake data for Zanzibar/Tanzania context
VENDOR_BUSINESSES = [
    "Mama Nia's Kitchen", "Zanzibar Spice Corner", "Stone Town Fresh Fish",
    "Urojo Soup Stall", "Forodhani Night Grill", "Pongwe Coconut Delights",
    "Dar Fresh Fruits", "Mwanza Street Chips", "Arusha Honey & Herbs"
]

PRODUCTS_DATA = [
    {"name": "Zanzibar Pizza", "desc": "Stuffed flatbread with egg, meat, and veggies", "price": 3500},
    {"name": "Urojo Soup", "desc": "Tangy street soup with lentils and spices", "price": 2000},
    {"name": "Grilled Octopus", "desc": "Fresh octopus grilled with coconut oil", "price": 8000},
    {"name": "Mandazi", "desc": "East African coconut donuts", "price": 500},
    {"name": "Fresh Coconut", "desc": "Chilled young coconut with straw", "price": 1500},
    {"name": "Chapati & Beans", "desc": "Homemade chapati with spiced beans", "price": 2500},
    {"name": "Mango Juice", "desc": "Freshly squeezed Alphonso mango", "price": 3000},
    {"name": "Zanzibar Mix", "desc": "Spiced mix of fruits, nuts, and tamarind", "price": 4000},
]

CATEGORIES = ["Street Food", "Fresh Produce", "Spices", "Drinks", "Snacks"]

BODABODA_PLATES = ["T 123 AB", "Z 456 CD", "T 789 EF", "Z 101 GH", "T 202 IJ"]
NAMES = ["Juma", "Aisha", "Hussein", "Fatma", "Rashid", "Zainab", "Khalid", "Mwanaidi"]

class Command(BaseCommand):
    help = 'Seed database with realistic TUUZIANE data'

    def handle(self, *args, **options):
        self.stdout.write('⚠️  Deleting old data...')
        Order.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        VendorProfile.objects.all().delete()
        BodabodaProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write('✅ Old data cleared.')

        # === 1. Create Categories ===
        categories = {}
        for cat_name in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                name=cat_name,
                slug=slugify(cat_name)
            )
            categories[cat_name] = cat
            self.stdout.write(f'  🏷️  Category: {cat_name}')

        # === 2. Create Vendors ===
        vendors = []
        for i, biz in enumerate(VENDOR_BUSINESSES):
            username = f"vendor{i+1}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@tuuziane.tz",
                phone=f"+255712000{i+1:03d}",
                password="vendor123",
                user_type="vendor"
            )
            vendor_profile = VendorProfile.objects.create(
                user=user,
                business_name=biz,
                location_description=f"Near {biz.split()[-1]} Market"
            )
            vendors.append(user)
            self.stdout.write(f'  🏪 Vendor: {biz}')

        # === 3. Create Products ===
        products = []
        for vendor in vendors:
            # Each vendor adds 2-4 products
            num_products = random.randint(2, 4)
            selected_products = random.sample(PRODUCTS_DATA, num_products)
            for p in selected_products:
                product = Product.objects.create(
                    vendor=vendor,
                    name=p["name"],
                    description=p["desc"],
                    price=p["price"],
                    image="products/default.jpg",  # We'll use a placeholder
                    category=random.choice(list(categories.values())),
                    is_available=True
                )
                products.append(product)
                self.stdout.write(f'    🥘 Product: {p["name"]} (by {vendor.vendor_profile.business_name})')

        # === 4. Create Bodaboda Riders ===
        bodabodas = []
        for i in range(5):
            username = f"boda{i+1}"
            user = User.objects.create_user(
                username=username,
                phone=f"+255742000{i+1:03d}",
                password="boda123",
                user_type="bodaboda"
            )
            boda_profile = BodabodaProfile.objects.create(
                user=user,
                plate_number=BODABODA_PLATES[i],
                id_number=f"ID{i+1}000000",
                verified=True,
                is_available=True
            )
            bodabodas.append(user)
            self.stdout.write(f'  🏍️ Bodaboda: {BODABODA_PLATES[i]} ({username})')

        # === 5. Create Customers ===
        customers = []
        for i in range(8):
            name = random.choice(NAMES)
            username = f"customer{i+1}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@gmail.com",
                phone=f"+255752000{i+1:03d}",
                password="customer123",
                user_type="customer"
            )
            customers.append(user)
            self.stdout.write(f'  👤 Customer: {username}')

        # === 6. Create Orders ===
        for _ in range(12):
            customer = random.choice(customers)
            product = random.choice(products)
            quantity = random.randint(1, 3)
            total = product.price * quantity
            bodaboda = random.choice(bodabodas)
            
            order = Order.objects.create(
                customer=customer,
                product=product,
                quantity=quantity,
                total_price=total,
                status=random.choice(['pending', 'assigned', 'delivered']),
                bodaboda=bodaboda,
                delivery_address=f"House {random.randint(1,100)}, {random.choice(['Ngambo', 'Stone Town', 'Mwanakwerekwe'])}"
            )
            self.stdout.write(f'  📦 Order #{order.id}: {product.name} x{quantity} → {bodaboda.username}')

        self.stdout.write(self.style.SUCCESS('✨ TUUZIANE database seeded successfully!'))
        self.stdout.write('🔑 Login credentials:')
        self.stdout.write('   Customer: customer1 / customer123')
        self.stdout.write('   Vendor: vendor1 / vendor123')
        self.stdout.write('   Bodaboda: boda1 / boda123')