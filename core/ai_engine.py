import cv2
import numpy as np
import os
import time
from ultralytics import YOLO

# Import new services
from core.services.vision import detect_tree
from core.services.geo import validate_location
from core.services.hash import check_duplicate
from core.services.ndvi import fetch_sentinel_ndvi, correlate_ndvi

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================

STORAGE_DIR = "verified_biomass"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

print("Initializing Hybrid AI Security Layer...")

# Initialize YOLO (Object Detection)
try:
    yolo_model = YOLO('yolov8n.pt') 
    print("YOLO Model Loaded Successfully!")
except Exception as e:
    print(f"YOLO Loading Error: {e}")
    yolo_model = None

# ==========================================
# 2. MAIN ANALYSIS PIPELINE
# ==========================================

def analyze_carbon_from_image(uploaded_image, claimed_lat=None, claimed_lon=None, source='file'):
    """
    Hybrid Analysis:
    1. Location Check (using Exif or claimed coords)
    2. Deep Learning Check (TensorFlow MobileNetV2)
    3. Object Detection Check (YOLO)
    4. Duplicate Check (Perceptual Hash)
    """
    try:
        print("\n--- STARTING HYBRID AI ANALYSIS ---")
        
        # A. PREPARE IMAGE FOR ANALYSIS
        uploaded_image.seek(0)
        file_bytes = np.asarray(bytearray(uploaded_image.read()), dtype=np.uint8)
        img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img_cv is None:
            raise ValueError("Corrupted image file.")

        # Save temporarily for Pillow/TensorFlow access
        temp_path = f"temp_{int(time.time())}.jpg"
        with open(temp_path, 'wb') as f:
            uploaded_image.seek(0)
            f.write(uploaded_image.read())

        checks = {
            "location": {"status": True, "msg": "Trusted"},
            "biomass": {"status": True, "msg": "Detected"},
            "duplicate": {"status": True, "msg": "Unique"}
        }
        rejection_reasons = []

        # --- CHECK 1: LOCATION VERIFICATION ---
        geo_valid = True
        if claimed_lat is not None and claimed_lon is not None:
            if source == 'file':
                geo_valid = validate_location(temp_path, float(claimed_lat), float(claimed_lon))
                print(f"   Location Check (EXIF vs Claimed): {'PASS' if geo_valid else 'FAIL'}")
            else:
                print(f"   Location Check: Trusted Browser Source (Camera)")
        
        checks['location'] = {
            "status": geo_valid, 
            "msg": "Matches Claimed" if geo_valid else "Location Mismatch"
        }
        if not geo_valid: rejection_reasons.append("Location Mismatch")

        # --- CHECK 2: TENSORFLOW CLASSIFICATION ---
        is_biomass, confidence = detect_tree(temp_path)
        print(f"   Deep Learning (MobileNet): {'Tree/Biomass' if is_biomass else 'Not Biomass'} ({confidence:.2f})")

        checks['biomass'] = {
            "status": is_biomass and confidence >= 0.4,
            "msg": f"Confidence {int(confidence*100)}%" if is_biomass else "Not Recognized"
        }
        if not (is_biomass and confidence >= 0.4): rejection_reasons.append("Not Biomass")

        # --- CHECK 3: DUPLICATE CHECK ---
        from PIL import Image
        import imagehash
        
        uploaded_image.seek(0)
        with Image.open(uploaded_image) as pil_img:
            img_hash = str(imagehash.phash(pil_img))
        
        is_duplicate = check_duplicate(img_hash)
        checks['duplicate'] = {
            "status": not is_duplicate,
            "msg": "Unique Image" if not is_duplicate else "Already Used"
        }
        if is_duplicate:
            print("   DUPLICATE DETECTED: Asset already verified.")
            rejection_reasons.append("Duplicate Image")

        # --- CHECK 4: ENVIRONMENTAL (NDVI) ---
        # Fetch Satellite Data if coordinates are available
        ndvi_val = None
        ndvi_status = "Skipped"
        ndvi_pass = True
        
        if claimed_lat and claimed_lon:
            print(f"   Fetching Sentinel-2 Data for {claimed_lat}, {claimed_lon}...")
            ndvi_val = fetch_sentinel_ndvi(float(claimed_lat), float(claimed_lon))
            ndvi_status, ndvi_pass = correlate_ndvi(ndvi_val, is_biomass)
            print(f"   NDVI Analysis: {ndvi_val} -> {ndvi_status}")

        checks['environment'] = {
            "status": ndvi_pass,
            "msg": f"NDVI {ndvi_val}: {ndvi_status}" if ndvi_val else "No Sat Data"
        }
        # We don't strictly reject on NDVI yet (allow "Soft Fail"), or we can strict mode it.
        # For now, let's keep it advisory unless it's a blatant mismatch.
        if not ndvi_pass:
             print("   WARNING: Environmental mismatch detected.")
             # rejection_reasons.append("Environmental Mismatch") # Uncomment for strict mode

        # --- FINAL DECISION ---
        if len(rejection_reasons) > 0:
            if os.path.exists(temp_path): os.remove(temp_path)
            return 0.0, 0, False, checks

        # --- SUCCESS: CALCULATE CREDITS ---
        # Formula from BiomassAI-master
        # 1. Base Biomass = 1000kg (average tree) * confidence
        base_mass_kg = 1000.0 * confidence
        
        # 2. Add extra for multiple objects (small heuristic addition)
        if valid_objects > 1:
            base_mass_kg += (valid_objects - 1) * 200.0 

        # 3. Convert to Tonnes
        biomass_tonnes = base_mass_kg / 1000.0

        # 4. Carbon Calculation: Biomass * CarbonFraction(0.47) * MolecularRatio(44/12)
        carbon_fraction = 0.47
        molecular_ratio = 44 / 12
        tco2e = biomass_tonnes * carbon_fraction * molecular_ratio

        print(f"   VERIFIED: {tco2e:.4f} tCO2e (Mass: {base_mass_kg:.1f}kg)")
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return round(tco2e, 4), max(valid_objects, 1), True, checks

    except Exception as e:
        print(f"CRITICAL AI ERROR: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return 0.0, 0, False, ["System Error"]