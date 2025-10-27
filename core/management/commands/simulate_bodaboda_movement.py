import random
from django.core.management.base import BaseCommand
from core.models import User

MIN_LAT, MAX_LAT = -6.1750, -6.1550
MIN_LNG, MAX_LNG = 39.1850, 39.2050

class Command(BaseCommand):
    help = 'Simulate bodaboda riders moving around Zanzibar'

    def handle(self, *args, **options):
        bodabodas = User.objects.filter(
            user_type='bodaboda',
            bodaboda_profile__verified=True
        )

        if not bodabodas.exists():
            self.stdout.write("No verified bodabodas found. Run `seed_tuuziane` first.")
            return

        for boda in bodabodas:
            boda.latitude = random.uniform(MIN_LAT, MAX_LAT)
            boda.longitude = random.uniform(MIN_LNG, MAX_LNG)
            boda.save(update_fields=['latitude', 'longitude'])
            self.stdout.write(
                f"📍 {boda.username} moved to ({boda.latitude:.4f}, {boda.longitude:.4f})"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Updated {bodabodas.count()} bodaboda locations.")
        )