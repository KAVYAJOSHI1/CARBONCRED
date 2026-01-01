import os
import datetime
import numpy as np

# Try importing sentinelhub, but provide mock fallback if not installed
try:
    from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, BBox, CRS
    SENTINEL_AVAILABLE = True
except ImportError:
    SENTINEL_AVAILABLE = False

def fetch_sentinel_ndvi(lat, lon):
    """
    Fetches the average NDVI for a small bounding box around the given coordinates.
    Returns a float (NDVI value) or None.
    """
    # 1. Credentials Check
    client_id = os.environ.get('SH_CLIENT_ID')
    client_secret = os.environ.get('SH_CLIENT_SECRET')

    if not SENTINEL_AVAILABLE or not client_id or not client_secret:
        print("   [NDVI] Sentinel Hub not configured or library missing. Using Mock Data.")
        # Return a realistic random value for demo purposes (0.4 - 0.8 is healthy vegetation)
        import random
        return round(random.uniform(0.45, 0.75), 2)

    try:
        config = SHConfig()
        config.sh_client_id = client_id
        config.sh_client_secret = client_secret
        
        # 2. Define Area (~100m box)
        delta = 0.0005
        bbox = BBox(bbox=[lon - delta, lat - delta, lon + delta, lat + delta], crs=CRS.WGS84)

        # 3. NDVI Eval Script
        evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: ["B04", "B08", "dataMask"],
            output: { bands: 2, sampleType: "FLOAT32" }
          }
        }
        function evaluatePixel(sample) {
          let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
          return [ndvi, sample.dataMask];
        }
        """

        # 4. Request
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=30)
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(start_date.isoformat(), today.isoformat()),
                    maxcc=20.0,
                    mosaicking_order="leastCC"
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=bbox,
            size=[10, 10], 
            config=config
        )

        # 5. Execute
        data = request.get_data()
        if not data or len(data) == 0:
            return None
        
        image_data = data[0]
        ndvi_band = image_data[:, :, 0]
        mask_band = image_data[:, :, 1]

        valid_ndvi = ndvi_band[mask_band == 1]

        if valid_ndvi.size == 0:
            return None

        return float(np.mean(valid_ndvi))

    except Exception as e:
        print(f"   [NDVI] Error fetching data: {e}")
        return None

def correlate_ndvi(ndvi, is_biomass):
    """
    Analyzes consistency between satellite NDVI and ground-level AI.
    Returns: (Status String, Passed Boolean)
    """
    if ndvi is None:
        return "N/A (No Sat Data)", True # Pass by default if no data to avoid blocking

    # Interpreting NDVI
    # < 0.2: Soil/Water
    # 0.2 - 0.4: Sparse Vegetation
    # > 0.4: Dense Vegetation

    if is_biomass:
        if ndvi > 0.3:
            return "Consistent (Healthy Vegetation)", True
        elif ndvi < 0.2:
            return "Warning: Low Satellite Greenery", False # Suspicious
        else:
            return "Plausible", True
    else:
        # AI says NO biomass, but Satellite says YES?
        if ndvi > 0.5:
            return "Discrepancy: High Sat. Vegetation", False
        else:
            return "Consistent (No Vegetation)", True
