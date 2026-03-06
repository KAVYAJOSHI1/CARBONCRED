from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime

def extract_metadata(image_path):
    """
    Extracts GPS coordinates and Timestamp from image EXIF.
    Returns: {
        'lat': float,
        'lon': float,
        'timestamp': datetime object or None,
        'has_exif': bool
    }
    """
    try:
        if hasattr(image_path, 'seek'):
            image_path.seek(0)
        
        img = Image.open(image_path)
        exif_raw = img._getexif()
        
        if not exif_raw:
            return {'lat': None, 'lon': None, 'timestamp': None, 'has_exif': False}

        exif = {TAGS.get(k, k): v for k, v in exif_raw.items()}
        
        # 1. Extract GPS
        gps_info = exif.get("GPSInfo")
        lat, lon = None, None
        
        if gps_info:
            gps_data = {}
            for key in gps_info.keys():
                name = GPSTAGS.get(key, key)
                gps_data[name] = gps_info[key]

            def convert_to_degrees(value):
                d, m, s = value
                return float(d) + float(m) / 60.0 + float(s) / 3600.0

            if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                lat = convert_to_degrees(gps_data["GPSLatitude"])
                if gps_data.get("GPSLatitudeRef") != "N":
                    lat = -lat
                
                lon = convert_to_degrees(gps_data["GPSLongitude"])
                if gps_data.get("GPSLongitudeRef") != "E":
                    lon = -lon

        # 2. Extract Timestamp (DateTimeOriginal)
        timestamp = None
        date_str = exif.get("DateTimeOriginal")
        if date_str:
            try:
                # Format: "YYYY:MM:DD HH:MM:SS"
                timestamp = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                pass

        return {
            'lat': lat,
            'lon': lon,
            'timestamp': timestamp,
            'has_exif': True
        }

    except Exception as e:
        print(f"Metadata Extraction Error: {e}")
        return {'lat': None, 'lon': None, 'timestamp': None, 'has_exif': False}

