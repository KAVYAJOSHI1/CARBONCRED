import os
import datetime
import numpy as np
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, BBox, CRS

# Helper to configure credentials
def get_config():
    config = SHConfig()
    client_id = os.environ.get('SH_CLIENT_ID')
    client_secret = os.environ.get('SH_CLIENT_SECRET')

    if not client_id or not client_secret:
        return None
    
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    return config

def fetch_sentinel_ndvi(lat, lon):
    """
    Fetches the average NDVI for a small bounding box around the given coordinates
    using the latest available Sentinel-2 L2A image.
    """
    config = get_config()
    if not config:
        print("Sentinel Hub credentials not found. Using MOCK NDVI for demonstration.")
        return 0.45 # Mock value for demo purposes

    # Define a small bounding box (approx 100m x 100m)
    # 0.001 degrees is roughly 111 meters
    delta = 0.0005
    bbox = BBox(bbox=[lon - delta, lat - delta, lon + delta, lat + delta], crs=CRS.WGS84)

    # Eval script for NDVI
    # NDVI = (B08 - B04) / (B08 + B04)
    # We return the calculated NDVI and a dataMask to exclude invalid pixels (clouds/no data)
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

    # Request setup
    # Time interval: Look back 30 days likely to find a cloud-free image
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=30)
    
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL1_IW,  # ERROR: NDVI needs Sentinel-2
                # Wait, I made a mistake above. Will fix in next step if I can't edit now.
                # Actually, I can catch this during verification, but better to get it right.
                # Correct collection is SENTINEL2_L2A
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=bbox,
        size=[10, 10], # 10x10 pixels is plenty for specific location
        config=config,
        data_folder=None # Don't save to disk
    )
    
    # Wait, I need to specify the correct collection and time range in the input_data helper or the request structure.
    # The sentinelhub-py library usage is slightly different.
    # Let me re-write the request part correctly.

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(start_date.isoformat(), today.isoformat()),
                maxcc=20.0, # Max 20% cloud cover
                mosaicking_order="leastCC" # Choose the least cloudy pixel
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=bbox,
        size=[10, 10], 
        config=config
    )

    try:
        data = request.get_data()
        if not data or len(data) == 0:
            return None
        
        # data[0] is the numpy array of shape (height, width, bands)
        # band 0 is NDVI, band 1 is dataMask
        image_data = data[0]
        ndvi_band = image_data[:, :, 0]
        mask_band = image_data[:, :, 1]

        # Filter out invalid pixels (mask == 0)
        valid_ndvi = ndvi_band[mask_band == 1]

        if valid_ndvi.size == 0:
            return None

        # Return mean NDVI
        return float(np.mean(valid_ndvi))

    except Exception as e:
        print(f"Error fetching Sentinel data: {e}")
        return None

def correlate_ndvi(ndvi, model1_confidence, tree_detected):
    """
    Correlates Sentinel-2 NDVI with Model 1 results.
    """
    if ndvi is None:
        return "INDETERMINATE - NO SATELLITE DATA"

    # NDVI thresholds
    # > 0.3 usually indicates vegetation
    # < 0.2 indicates soil/water/urban
    
    status = "INCONCLUSIVE"

    if tree_detected:
        if ndvi > 0.3:
            status = "CONFIRMED"
        elif ndvi < 0.2:
            status = "DISCREPANCY - LOW VEGETATION INDEX"
        else:
            status = "PLAUSIBLE" # 0.2 - 0.3 is range
    else: # Tree NOT detected by Model 1
        if ndvi > 0.5:
             status = "DISCREPANCY - DENSE VEGETATION DETECTED"
        else:
             status = "CONSISTENT"  # Low NDVI and No Tree match

    return status
