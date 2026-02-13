
import unittest
from datetime import datetime, timedelta
import sys
import os

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from core.services.geo import validate_location, validate_timestamp

class TestLayer2(unittest.TestCase):
    def test_location_validation(self):
        # 1. Exact Match
        valid, msg = validate_location(12.9716, 77.5946, 12.9716, 77.5946)
        self.assertTrue(valid)
        self.assertIn("Match", msg)

        # 2. Within 50m (approx 0.00045 degrees lat)
        valid, msg = validate_location(12.9716, 77.5946, 12.97165, 77.5946) # Small shift
        self.assertTrue(valid)
        
        # 3. Far away
        valid, msg = validate_location(12.9716, 77.5946, 12.9800, 77.5946) # ~1km away
        self.assertFalse(valid)
        self.assertIn("Mismatch", msg)
        
        # 4. Missing Data
        valid, msg = validate_location(12.9716, 77.5946, None, None)
        self.assertFalse(valid)
        self.assertIn("No GPS", msg)

    def test_timestamp_validation(self):
        now = datetime.now()
        
        # 1. Recent (1 hour ago)
        valid, msg = validate_timestamp(now - timedelta(hours=1))
        self.assertTrue(valid)
        self.assertIn("Recent", msg)
        
        # 2. Too Old (25 hours ago)
        valid, msg = validate_timestamp(now - timedelta(hours=25))
        self.assertFalse(valid)
        self.assertIn("too old", msg)
        
        # 3. Future (1 hour ahead)
        valid, msg = validate_timestamp(now + timedelta(hours=1))
        self.assertFalse(valid)
        self.assertIn("future", msg)
        
        # 4. Missing
        valid, msg = validate_timestamp(None)
        self.assertFalse(valid)

if __name__ == '__main__':
    unittest.main()
