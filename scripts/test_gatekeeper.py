
import os
import sys
import django
from PIL import Image, ImageDraw
import numpy as np

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from core.services.vision import detect_tree, analyze_depth, check_live_capture

def create_dummy_image(filename, color=(0, 255, 0), size=(224, 224)):
    img = Image.new('RGB', size, color)
    # Add some noise/patterns to simulate texture for depth
    draw = ImageDraw.Draw(img)
    for i in range(0, size[0], 20):
        for j in range(0, size[1], 20):
            draw.rectangle([i, j, i+10, j+10], fill=(color[0], color[1]-50, color[2]))
    img.save(filename, quality=95)
    print(f"Created dummy image: {filename}")
    return filename

def test_gatekeeper():
    print("--- STARTING GATEKEEPER TEST ---")
    
    # 1. Test with a Generated "Fake" Image
    fake_img_path = create_dummy_image("test_fake_tree.jpg", color=(0, 200, 0)) # Green-ish
    
    print("\n[TEST 1] Testing Generated Image (Should fail Live Capture & Depth)...")
    try:
        is_biomass, conf, labels, checks = detect_tree(fake_img_path)
        
        print(f"Biomass: {is_biomass}")
        print(f"Confidence: {conf}")
        print(f"Labels: {labels}")
        print("Checks:")
        for k, v in checks.items():
            print(f"  - {k}: {v}")
            
        # Assertions
        if checks['live_capture']['status'] is False:
            print("✅ Live Capture correctly rejected generated image.")
        else:
            print("❌ Live Capture FAILED (Accepted generated image).")
            
    except Exception as e:
        print(f"❌ Error during Test 1: {e}")

    # Clean up
    if os.path.exists(fake_img_path):
        os.remove(fake_img_path)

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    test_gatekeeper()
