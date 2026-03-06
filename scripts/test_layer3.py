
import unittest
import sys
import os

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from core.services.ndvi import initialize_gee, fetch_sentinel_ndvi, correlate_ndvi

class TestLayer3(unittest.TestCase):
    def test_initialization(self):
        print("Testing GEE Initialization...")
        success = initialize_gee()
        if success:
            print("✅ GEE Initialized successfully.")
        else:
            print("⚠️ GEE Initialization failed (expected if no valid key).")
            
    def test_correlation_logic(self):
        # 1. High NDVI + Biomass = Pass
        msg, status = correlate_ndvi(0.6, True)
        self.assertTrue(status)
        self.assertIn("Verified", msg)
        
        # 2. Low NDVI + Biomass = Fail
        msg, status = correlate_ndvi(0.1, True)
        self.assertFalse(status)
        self.assertIn("Low Greenery", msg)
        
        # 3. No NDVI (Cloud/Error) = Soft Pass
        msg, status = correlate_ndvi(None, True)
        self.assertTrue(status)
        self.assertIn("Unavailable", msg)
        
    def test_live_fetch(self):
        # Only run if GEE is available
        if initialize_gee():
            print("Fetching NDVI for Central Park...")
            ndvi = fetch_sentinel_ndvi(40.785091, -73.968285)
            print(f"Central Park NDVI: {ndvi}")
            if ndvi is not None:
                self.assertGreater(ndvi, 0.2)
        else:
            print("Skipping Live Fetch test (GEE not authorized)")

if __name__ == '__main__':
    unittest.main()
