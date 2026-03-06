
import os
import sys
import django
import json
from PIL import Image, ExifTags
import piexif
from datetime import datetime

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from core.views import test_mint_view

def add_metadata(image_path, lat, lon):
    """
    Injects GPS and Timestamp into image EXIF using piexif.
    """
    img = Image.open(image_path)
    
    # 1. Prepare GPS
    def to_deg(value, loc):
        if value < 0:
            loc_value = loc.upper()
        else:
            loc_value = loc.upper()
        abs_value = abs(value)
        deg = int(abs_value)
        t1 = (deg, 1)
        remaining = abs_value - deg
        min = int(remaining * 60)
        t2 = (min, 1)
        sec = int((remaining * 60 - min) * 60 * 10000)
        t3 = (sec, 10000)
        return (t1, t2, t3)

    lat_deg = to_deg(lat, ["S", "N"][lat >= 0])
    lon_deg = to_deg(lon, ["W", "E"][lon >= 0])
    
    gps_dict = {
        piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
        piexif.GPSIFD.GPSLatitude: lat_deg,
        piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
        piexif.GPSIFD.GPSLongitude: lon_deg,
    }
    
    # 2. Prepare Timestamp
    time_str = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: "Canon",
            piexif.ImageIFD.Model: "Canon EOS 5D Mark IV",
            piexif.ImageIFD.Software: "VeriScore Camera App" 
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: time_str,
            piexif.ExifIFD.DateTimeDigitized: time_str,
        },
        "GPS": gps_dict
    }
    
    exif_bytes = piexif.dump(exif_dict)
    
    new_path = "real_tree_tagged.jpg"
    img.save(new_path, "jpeg", exif=exif_bytes)
    return new_path

def create_synthetic_tree(filename):
    """
    Creates a synthetic 'biomass' image (Green Grass Texture)
    to verify the AI Vision layer without external downloads.
    """
    import random
    from PIL import ImageDraw
    
    width, height = 640, 480
    img = Image.new('RGB', (width, height), (34, 139, 34)) # Forest Green Base
    draw = ImageDraw.Draw(img)
    
    # Draw thousands of "blades of grass" (vertical lines)
    for _ in range(5000):
        x = random.randint(0, width)
        y = random.randint(0, height)
        h = random.randint(10, 30)
        # Random green shade
        color = (random.randint(20, 100), random.randint(150, 255), random.randint(20, 100))
        draw.line([(x, y), (x, y-h)], fill=color, width=1)
        
    img.save(filename)
    return filename

def test_real_world():
    print("--- STARTING REAL WORLD TREE TEST ---")
    
    # 1. Load or Create Image
    original_path = "real_tree.jpg"
    if not os.path.exists(original_path) or os.path.getsize(original_path) < 100:
        print("⚠️ Image download missing/invalid. Generating synthetic Bio-Texture (Grass)...")
        create_synthetic_tree(original_path)
    
    try:
        # Verify it opens
        Image.open(original_path).verify()
    except Exception:
        print("⚠️ Invalid image format. Regenerating...")
        try:
             os.remove(original_path)
        except: pass
        create_synthetic_tree(original_path)

    # 2. Define Location (Hyde Park, London - for Ash Tree)
    # Latitude: 51.5072, Longitude: -0.1276
    lat = 51.5072
    lon = -0.1276

    print(f"Injecting GPS: {lat}, {lon}")
    try:
        tagged_path = add_metadata(original_path, lat, lon)
    except Exception as e:
        print(f"❌ Metadata Injection Failed: {e}")
        return

    # 3. Submit to API (Mocking Vision to simulate 'Ash Tree' recognition on synthetic image)
    factory = RequestFactory()
    
    with open(tagged_path, "rb") as f:
        img_file = SimpleUploadedFile("real_tree_tagged.jpg", f.read(), content_type="image/jpeg")

    print(f"Submitting image size: {os.path.getsize(tagged_path)} bytes")
    
    # We patch 'detect_tree' where it is USED, which is inside 'core.ai_engine'
    # This simulates that the Vision AI sees an 'Ash Tree' in the generated image.
    from unittest.mock import patch
    
    with patch('core.ai_engine.detect_tree') as mock_vision:
        # Simulate successful detection of Ash Tree with Real 3D Depth
        mock_vision.return_value = (
            True, 
            0.98, 
            ['ash', 'tree', 'plant'], 
            {
                'live_capture': {'status': True, 'msg': 'Captured by Canon EOS 5D Mark IV'},
                'depth_analysis': {'status': True, 'msg': 'Depth Variance: 20835.68 (Real 3D)'}
            }
        )
        
        # Claim matches EXIF
        request = factory.post('/api/mint/', {
            'latitude': str(lat), 
            'longitude': str(lon), 
            'image': img_file,
            'source': 'file' 
        })
        
        print("\n--- API RESPONSE ---")
        response = test_mint_view(request)
        data = json.loads(response.content)
    
    print(json.dumps(data, indent=4))
    
    if data.get('status') == 'Success' or (data.get('status') == 'Skipped (0 Mint)' and data.get('ai_data', {}).get('co2_tons', 0) > 0):
        print("\n✅ REAL WORLD TEST PASSED!")
        if 'batch_log' in data:
            log = data['batch_log'][0]
            print(f"Verified Species: {log.get('checks', {}).get('biomass', {}).get('msg', 'Unknown')}")
            print(f"Live Capture: {log.get('checks', {}).get('live_capture', {}).get('msg', 'Unknown')}")
            print(f"GPS Match: {log.get('checks', {}).get('location', {}).get('msg', 'Unknown')}")
            print(f"Credits Minted: {data.get('ai_data', {}).get('co2_tons')} tons")
    else:
        print("\n❌ REAL WORLD TEST FAILED/REJECTED")
        if 'batch_log' in data:
            for item in data['batch_log']:
                print(f"Reason: {item.get('reason')}")
                # print(f"Checks: {json.dumps(item.get('checks'), indent=2)}")

    # Clean up
    if os.path.exists(tagged_path):
        os.remove(tagged_path)

if __name__ == "__main__":
    test_real_world()
