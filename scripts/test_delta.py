
import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile
import json

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from core.models import Upload
from core.views import test_mint_view
from django.test import RequestFactory
from unittest.mock import patch, MagicMock

def create_mock_image(name="test.jpg", content=None):
    if content is None:
        content = f"dummy_content_{name}".encode('utf-8') # Unique content based on name
    return SimpleUploadedFile(name, content, content_type="image/jpeg")

@patch('core.views.analyze_carbon_from_image')
@patch('core.views.mint_static_credit')
def run_delta_simulation(mock_mint, mock_analyze):
    print("\n--- STARTING BIOMASS DELTA SIMULATION ---")
    
    # Setup Factory
    factory = RequestFactory()
    
    # Scenario: Same Location (Lat: 10.0, Lon: 20.0)
    lat = "10.00000"
    lon = "20.00000"

    print(f"Location Fixed at: {lat}, {lon}")

    # --- STEP 1: INITIAL UPLOAD (10 Tons) ---
    print("\n[STEP 1] Uploading Baseline Tree (10.0 Tons)...")
    mock_analyze.return_value = (10.0, 1, True, {'environment': {'status': True, 'msg': 'OK'}})
    mock_mint.return_value = "0xHash1"
    
    request1 = factory.post('/api/mint/', {'latitude': lat, 'longitude': lon, 'image': create_mock_image("tree1.jpg")})
    response1 = test_mint_view(request1)
    data1 = json.loads(response1.content)
    
    print(f"   Minted: {data1['ai_data']['co2_tons']} tons")
    print(f"   Blockchain TX: {data1['tx_hash']}")
    
    if data1['ai_data']['co2_tons'] == 10.0:
        print("✅ Step 1 Success: Full mint for new tree.")
    else:
        print(f"❌ Step 1 Failed: Expected 10.0, got {data1['ai_data']['co2_tons']}")

    # --- STEP 2: DUPLICATE UPLOAD (Same 10 Tons) ---
    print("\n[STEP 2] Uploading Same Tree Again (10.0 Tons)...")
    # Simulate user coming back 5 mins later with specific non-duplicate content but same AI result
    # We must ensure content is different from tree1 to bypass Hash Check, or we test hash check.
    # Let's test Delta Logic, so we need different file content.
    mock_analyze.return_value = (10.0, 1, True, {'environment': {'status': True, 'msg': 'Old Growth'}})
    
    request2 = factory.post('/api/mint/', {'latitude': lat, 'longitude': lon, 'image': create_mock_image("tree2_new_angle.jpg")})
    response2 = test_mint_view(request2)
    data2 = json.loads(response2.content)
    
    print(f"   Minted: {data2['ai_data']['co2_tons']} tons")
    
    if data2['ai_data']['co2_tons'] == 0.0:
        print("✅ Step 2 Success: Zero mint for identical biomass (Delta Logic).")
    else:
        print(f"❌ Step 2 Failed: Expected 0.0, got {data2['ai_data']['co2_tons']}")

    # --- STEP 3: GROWTH UPLOAD (12 Tons - Growth of 2 Tons) ---

    print("\n[STEP 3] Uploading Tree After Growth (12.0 Tons)...")
    # Simulate user coming back next year
    mock_analyze.return_value = (12.0, 1, True, {'environment': {'status': True, 'msg': 'OK'}})
    mock_mint.return_value = "0xHash3"
    
    request3 = factory.post('/api/mint/', {'latitude': lat, 'longitude': lon, 'image': create_mock_image("tree3.jpg")})
    response3 = test_mint_view(request3)
    data3 = json.loads(response3.content)
    
    print(f"   Minted: {data3['ai_data']['co2_tons']} tons")
    
    if abs(data3['ai_data']['co2_tons'] - 2.0) < 0.001:
        print("✅ Step 3 Success: Minted only the delta (2.0 tons).")
    else:
        print(f"❌ Step 3 Failed: Expected 2.0, got {data3['ai_data']['co2_tons']}")

    # --- STEP 4: LESS BIOMASS (8 Tons - Pruning/Error) ---
    print("\n[STEP 4] Uploading Tree with Less Biomass (8.0 Tons)...")
    mock_analyze.return_value = (8.0, 1, True, {'environment': {'status': True, 'msg': 'OK'}})
    
    request4 = factory.post('/api/mint/', {'latitude': lat, 'longitude': lon, 'image': create_mock_image("tree4.jpg")})
    response4 = test_mint_view(request4)
    data4 = json.loads(response4.content)
    
    print(f"   Minted: {data4['ai_data']['co2_tons']} tons")
    
    if data4['ai_data']['co2_tons'] == 0.0:
        print("✅ Step 4 Success: Zero mint for negative delta.")
    else:
        print(f"❌ Step 4 Failed: Expected 0.0, got {data4['ai_data']['co2_tons']}")
        
    print("\n--- SIMULATION COMPLETE ---")

if __name__ == "__main__":
    # Clean DB first
    Upload.objects.all().delete()
    run_delta_simulation()
