import os
import datetime
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Try importing Google Earth Engine
try:
    import ee
    from google.oauth2 import service_account
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    logger.error("⚠️ [GEE] 'earthengine-api' not installed. CANNOT RUN LIVE SATELLITE.")

# Global flag to track initialization safely (Fixes the crash)
_GEE_INITIALIZED = False

def initialize_gee():
    """
    Initializes Google Earth Engine using the Service Account.
    """
    global _GEE_INITIALIZED
    
    # 1. If libraries are missing, we can't be live.
    if not GEE_AVAILABLE: 
        return False
    
    # 2. If already connected, don't reconnect (saves time)
    if _GEE_INITIALIZED:
        return True

    try:
        # 3. Load Key from Root Folder
        # Looks for the specific file you downloaded
        key_filename = os.environ.get('GEE_SERVICE_ACCOUNT_KEY_FILE', 'carbonverse-d73f871957f0.json')
        key_path = os.path.join(os.getcwd(), key_filename)
        
        if os.path.exists(key_path):
            # AUTHENTICATE WITH SERVICE ACCOUNT (Robust & Live)
            logger.info(f"🔑 [GEE] Loading Key: {key_filename}")
            credentials = service_account.Credentials.from_service_account_file(key_path)
            scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
            
            ee.Initialize(credentials=scoped_credentials)
            
            _GEE_INITIALIZED = True
            logger.info("✅ [GEE] Live Satellite Connection Established!")
            return True
        else:
            logger.error(f"❌ [GEE] Key file not found at: {key_path}")
            # Fallback to local auth if key is missing
            try:
                ee.Initialize()
                _GEE_INITIALIZED = True
                return True
            except:
                return False
                
    except Exception as e:
        logger.error(f"⚠️ [GEE] Connection Failed: {e}")
        return False

def fetch_sentinel_ndvi(lat, lon):
    """
    Fetches REAL NDVI from Sentinel-2 Satellite (Live Data).
    Returns: Float (0.0 to 1.0) or None.
    """
    if not initialize_gee():
        logger.warning("[NDVI] GEE not initialized. Skipping live fetch.")
        return None

    try:
        # 1. Define Point
        point = ee.Geometry.Point([float(lon), float(lat)])
        
        # 2. Define Date Range (Last 30 Days)
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)
        
        # 3. Query Sentinel-2 (Harmonized)
        s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(point) \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .sort('CLOUDY_PIXEL_PERCENTAGE')

        # 4. Check if image exists
        count = s2.size().getInfo()
        if count == 0:
            logger.warning(f"[NDVI] No clear satellite images found for {lat}, {lon} in last 30 days.")
            return None

        # 5. Calculate NDVI
        image = s2.first()
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # 6. Extract Value at Point
        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10,
            maxPixels=1e9
        ).getInfo()

        ndvi_val = stats.get('NDVI')
        
        if ndvi_val is not None:
            logger.info(f"✅ [LIVE SATELLITE] Retrieved NDVI: {ndvi_val}")
            return float(ndvi_val)
            
        return None

    except Exception as e:
        logger.error(f"⚠️ [NDVI] Fetch Error: {e}")
        return None

def correlate_ndvi(ndvi, is_biomass):
    """
    Interprets the NDVI value for the User Interface.
    """
    if ndvi is None:
        return "Satellite Data Unavailable (Soft Pass)", True

    # Real Logic: If image shows tree, satellite should show green (>0.2)
    if is_biomass:
        if ndvi > 0.30:
            return f"Verified: Healthy Veg (NDVI {ndvi:.2f})", True
        elif ndvi < 0.15:
            return f"Warning: Low Greenery (NDVI {ndvi:.2f})", False
        else:
            return f"Plausible (NDVI {ndvi:.2f})", True
    else:
        return "Not Applicable", True
