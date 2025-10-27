from math import radians, sin, cos, sqrt, atan2
from django.db import models
from .models import User

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers."""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')  # Invalid coords → treat as very far
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def find_nearest_bodaboda(customer_lat, customer_lng):
    """Return the nearest available & verified bodaboda user."""
    candidates = User.objects.filter(
        user_type='bodaboda',
        bodaboda_profile__verified=True,
        bodaboda_profile__is_available=True,
        latitude__isnull=False,
        longitude__isnull=False
    )

    if not candidates.exists():
        return None

    bodabodas = []
    for boda in candidates:
        dist = haversine_distance(customer_lat, customer_lng, boda.latitude, boda.longitude)
        bodabodas.append((dist, boda))
        nearest = min(bodabodas, key=lambda x: x[0])
    return nearest[1]