from .exif import extract_metadata
import math
from datetime import datetime, timedelta

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def validate_location(claimed_lat, claimed_lon, exif_lat, exif_lon, tolerance_meters=50):
    """
    Verifies if valid EXIF GPS data exists and matches the claimed location.
    """
    if exif_lat is None or exif_lon is None:
        return False, "No GPS data in image"

    distance = haversine(exif_lat, exif_lon, claimed_lat, claimed_lon)
    
    if distance <= tolerance_meters:
        return True, f"Match ({distance:.1f}m difference)"
    else:
        return False, f"Location Mismatch ({distance:.1f}m > {tolerance_meters}m)"

def validate_timestamp(captured_time, max_age_hours=24):
    """
    Verifies if the image was captured recently.
    """
    if not captured_time:
        return False, "No Timestamp in image"
        
    now = datetime.now()
    age = now - captured_time
    
    if age < timedelta(hours=0):
        return False, "Timestamp is in the future (Invalid)"
        
    if age > timedelta(hours=max_age_hours):
        return False, f"Image is too old ({age.days} days, {age.seconds//3600} hours)"
        
    return True, f"Recent Capture ({captured_time})"
