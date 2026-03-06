import os
import datetime
import json

# GEE Dependencies
try:
    import ee
    from google.oauth2 import service_account
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    print("   [GEE] 'earthengine-api' not installed.")


def initialize_gee():
    """
    Initializes Google Earth Engine.
    Prioritizes Service Account (server-side) auth.
    """
    if not GEE_AVAILABLE: return False

    try:
        # Check if already initialized to avoid overhead
        if ee.data._credentials:
            return True
            
        # 1. Look for Service Account Key Path in ENV
        key_path = os.environ.get('GEE_SERVICE_ACCOUNT_KEY_FILE')
        
        if key_path and os.path.exists(key_path):
            # Server-side Auth
            print(f"   [GEE] Authenticating with Service Account: {key_path}")
            credentials = service_account.Credentials.from_service_account_file(key_path)
            scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
            ee.Initialize(credentials=scoped_credentials)
            return True
        else:
            # 2. Fallback: Try Default Auth (if user ran 'earthengine authenticate' locally)
            # This works for local dev machines without a service account file
            print("   [GEE] No Service Account found. Trying default credentials...")
            try:
                ee.Initialize()
                return True
            except Exception:
                print("   [GEE] Authentication Failed. Please set GEE_SERVICE_ACCOUNT_KEY_FILE.")
                return False

    except Exception as e:
        print(f"   [GEE] Init Error: {e}")
        return False

def fetch_sentinel_ndvi(lat, lon):
    """
    Fetches real NDVI from Google Earth Engine (Sentinel-2 Surface Reflectance).
    """
    if not initialize_gee():
        print("   [NDVI] GEE Not Initialized. Returning None.")
        return None

    try:
        # 1. Define Point of Interest
        point = ee.Geometry.Point([lon, lat])
        
        # 2. Define Date Range (Last 30 days)
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)
        
        # 3. Load Sentinel-2 Harmonic (Surface Reflectance)
        # Using 'COPERNICUS/S2_SR_HARMONIZED' for best ready-to-use data
        s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(point) \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .sort('CLOUDY_PIXEL_PERCENTAGE')

        # 4. Check if we have images
        count = s2.size().getInfo()
        if count == 0:
            print("   [NDVI] No clear satellite images found in last 30 days.")
            return None

        # 5. Get Best Image (Least Cloudy)
        image = s2.first()
        
        # 6. Compute NDVI
        # NDVI = (NIR - Red) / (NIR + Red) -> (B8 - B4) / (B8 + B4)
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # 7. Reduce Region (Get value at the specific point)
        # Scale 10m is Sentinel-2 resolution
        result = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10,
            maxPixels=1e9
        ).getInfo()

        ndvi_value = result.get('NDVI')
        
        if ndvi_value is not None:
             return float(ndvi_value)
        return None

    except Exception as e:
        print(f"   [GEE] Calculation Error: {e}")
        return None

def correlate_ndvi(ndvi, is_biomass):
    """
    Interprets the NDVI value.
    """
    if ndvi is None:
        return "N/A (GEE Error or No Data)", True 

    # Real GEE NDVI Interpretation
    # > 0.4: Healthy Vegetation
    # 0.2 - 0.4: Sparse Vegetation
    # < 0.2: Soil/Urban/Water

    if is_biomass:
        if ndvi > 0.35:
            return "Consistent (Healthy Vegetation)", True
        elif ndvi < 0.2:
            return "Warning: Low Satellite Greenery", False
        else:
            return "Plausible", True
    else:
        if ndvi > 0.5:
            return "Discrepancy: High Sat. Vegetation", False
        else:
            return "Consistent (No Vegetation)", True
