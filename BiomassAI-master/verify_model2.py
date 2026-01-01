import os
import sys
import django
from unittest.mock import MagicMock, patch

# Setup Django environment
sys.path.append(os.path.join(os.getcwd(), 'core'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from verification.services.sentinel import fetch_sentinel_ndvi, correlate_ndvi

def test_correlation_logic():
    print("\nTesting Correlation Logic...")
    
    # Case 1: High NDVI + Tree = Confirmed
    status = correlate_ndvi(0.6, 0.9, True)
    print(f"NDVI 0.6, Tree=True -> {status}")
    assert status == "CONFIRMED"

    # Case 2: Low NDVI + Tree = Discrepancy
    status = correlate_ndvi(0.1, 0.9, True)
    print(f"NDVI 0.1, Tree=True -> {status}")
    assert "DISCREPANCY" in status

    # Case 3: High NDVI + No Tree = Discrepancy
    status = correlate_ndvi(0.8, 0.1, False)
    print(f"NDVI 0.8, Tree=False -> {status}")
    assert "DISCREPANCY" in status

    # Case 4: None NDVI
    status = correlate_ndvi(None, 0.5, True)
    print(f"NDVI None -> {status}")
    assert "INDETERMINATE" in status

    print("Correlation Logic Tests Passed!")

@patch('verification.services.sentinel.SentinelHubRequest')
@patch.dict(os.environ, {'SH_CLIENT_ID': 'mock_id', 'SH_CLIENT_SECRET': 'mock_secret'})
def test_fetch_ndvi_mock(mock_request):
    print("\nTesting Fetch NDVI (Mocked)...")
    
    # Mock the response data structure from Sentinel Hub
    # data[0] is the image, which has bands. We expect 2 bands: NDVI, Mask
    # Let's create a dummy 2x2 image
    import numpy as np
    
    # Shape: (height, width, bands) -> (10, 10, 2)
    # Band 0: NDVI values (mixed)
    # Band 1: Mask (1 for valid, 0 for invalid)
    
    # Create fake data: all valid, ndvi = 0.5
    fake_band_ndvi = np.full((10, 10), 0.5, dtype=np.float32)
    fake_band_mask = np.ones((10, 10), dtype=np.float32)
    fake_image = np.stack([fake_band_ndvi, fake_band_mask], axis=-1)
    
    # SentinelHubRequest.get_data returns a list of arrays
    mock_instance = mock_request.return_value
    mock_instance.get_data.return_value = [fake_image]

    # Call function
    # Coordinates don't matter as we mock the response
    ndvi = fetch_sentinel_ndvi(12.34, 56.78)
    
    print(f"Fetched NDVI: {ndvi}")
    assert ndvi == roughly
    
    # Test valid pixels filtering
    # Half valid (0.8), half invalid (0.2 but masked out)
    fake_band_ndvi = np.full((10, 10), 0.2, dtype=np.float32)
    fake_band_ndvi[:5, :] = 0.8
    fake_band_mask = np.zeros((10, 10), dtype=np.float32)
    fake_band_mask[:5, :] = 1 # Top half valid
    
    fake_image = np.stack([fake_band_ndvi, fake_band_mask], axis=-1)
    mock_instance.get_data.return_value = [fake_image]
    
    ndvi = fetch_sentinel_ndvi(12.34, 56.78)
    print(f"Fetched NDVI (half masked): {ndvi}")
    assert 0.79 < ndvi < 0.81

    print("Fetch NDVI Tests Passed!")

class Roughly:
    def __eq__(self, other):
        return abs(other - 0.5) < 0.001

roughly = Roughly()

if __name__ == "__main__":
    try:
        test_correlation_logic()
        test_fetch_ndvi_mock()
        print("\nAll automated tests passed!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
