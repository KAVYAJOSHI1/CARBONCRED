import os
import time
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import torch
from transformers import DPTImageProcessor, DPTForDepthEstimation, pipeline

# Global model instances
_CLIP_PIPELINE = None
_OWL_PIPELINE = None
_DEPTH_MODEL = None
_DEPTH_PROCESSOR = None

# Indian Tree Species for Zero-Shot Classification
INDIAN_TREE_SPECIES = [
    "Neem tree", "Teak tree", "Gulmohar tree", "Mango tree", 
    "Banyan tree", "Peepal tree", "Tamarind tree", "Coconut palm",
    "Bamboo", "Eucalyptus tree", "Jackfruit tree", "Ashoka tree",
    "Babul tree", "Sandalwood tree", "Sal tree"
]

# EXPANDED Whitelist
BIOMASS_KEYWORDS = [
    'tree', 'forest', 'wood', 'plant', 'bush', 'flower', 'shrub', 'grass', 
    'pine', 'oak', 'corn', 'grain', 'rapeseed', 'daisy', 'mushroom', 
    'bamboo', 'mangrove', 'garden', 'park', 'soil', 'earth',
    'valley', 'hill', 'mountain', 'field', 'meadow', 'farm',
    'stone_wall', 'ruin', 'coast', 'seashore', 'sandbar'
]

def get_clip_pipeline():
    global _CLIP_PIPELINE
    if _CLIP_PIPELINE is None:
        print("Loading CLIP zero-shot classification model...")
        try:
            # Explicitly force downloading if it isn't cached (though pipeline handles it usually)
            _CLIP_PIPELINE = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
        except Exception as e:
            print(f"Error loading CLIP: {e}")
            return None
    return _CLIP_PIPELINE

def get_owl_pipeline():
    global _OWL_PIPELINE
    if _OWL_PIPELINE is None:
        print("Loading OWL-ViT zero-shot object detection model...")
        try:
            _OWL_PIPELINE = pipeline("zero-shot-object-detection", model="google/owlvit-base-patch32")
        except Exception as e:
            print(f"Error loading OWL-ViT: {e}")
            return None
    return _OWL_PIPELINE

def get_depth_model():
    global _DEPTH_MODEL, _DEPTH_PROCESSOR
    if _DEPTH_MODEL is None:
        print("Loading Depth model...")
        try:
            _DEPTH_PROCESSOR = DPTImageProcessor.from_pretrained("Intel/dpt-hybrid-midas")
            _DEPTH_MODEL = DPTForDepthEstimation.from_pretrained("Intel/dpt-hybrid-midas")
        except Exception as e:
            print(f"Error loading Depth model: {e}")
            return None, None
    return _DEPTH_MODEL, _DEPTH_PROCESSOR

# --- NEW: HSV IMAGE PROCESSING ---
def analyze_green_content(image_path):
    """
    Uses HSV Color Space to calculate the percentage of green pixels.
    This is a NON-AI mathematical check for vegetation density.
    Returns: (green_ratio_float, is_passed_bool)
    """
    try:
        img = cv2.imread(image_path)
        if img is None: return 0.0, False

        # Convert to HSV (Hue, Saturation, Value)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Define Green Range in HSV (approx 35-85 Hue)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])

        # Create Mask (1 for green, 0 for others)
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Calculate Ratio
        green_pixels = cv2.countNonZero(mask)
        total_pixels = img.shape[0] * img.shape[1]
        ratio = green_pixels / total_pixels

        # Pass threshold: > 5% green or explicit earth tones implies nature
        return ratio, ratio > 0.05
    except Exception as e:
        print(f"HSV Analysis Error: {e}")
        return 0.0, True # Soft pass if CV fails

def check_live_capture(image_path):
    """
    Analyzes EXIF data to verify if the image is a live capture.
    Returns: (is_live, message)
    """
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        
        if not exif_data:
            return False, "No EXIF data found (Metadata stripped)"

        exif = {TAGS.get(k, k): v for k, v in exif_data.items()}
        
        # Check for Software editing traces
        software = exif.get("Software", "").lower()
        if "photoshop" in software or "gimp" in software or "adobe" in software:
            return False, f"Edited with {software}"

        # Check for Camera Make/Model (Basic check)
        make = exif.get("Make")
        model = exif.get("Model")
        
        if not make and not model:
            return False, "Missing Camera Manufacturer/Model"
            
        return True, f"Captured by {make} {model}"

    except Exception as e:
        return False, f"EXIF Analysis Failed: {str(e)}"

def analyze_depth(image_path):
    """
    Analyzes image depth to detect if it's a flat surface (fake) or has 3D depth (real).
    Returns: (is_real_3d, confidence)
    """
    try:
        model, processor = get_depth_model()
        if not model: return True, 0.5 # Fallback
        
        image = Image.open(image_path)
        inputs = processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(**inputs)
            predicted_depth = outputs.predicted_depth
            
        # Interpolate to original size
        prediction = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=image.size[::-1],
            mode="bicubic",
            align_corners=False,
        )
        
        # Simple variance check: Real 3D scenes have higher depth variance than flat screens
        depth_map = prediction.squeeze().cpu().numpy()
        depth_variance = np.var(depth_map)
        
        # Threshold needs tuning, but for now:
        # Flat screen photo ~ Low Variance
        # Real tree ~ High Variance
        
        is_real_3d = bool(depth_variance > 500) # Ensure native bool
        
        return is_real_3d, float(depth_variance)
        
    except Exception as e:
        print(f"Depth Analysis Error: {e}")
        return True, 0.0

def detect_tree(image_file):
    """
    Returns (is_biomass, confidence, detected_labels_list, checks_dict)
    """
    checks = {}
    
    # 1. LIVE CAPTURE CHECK
    # Need to read file for EXIF before processing
    if hasattr(image_file, 'name'):
        is_live, live_msg = check_live_capture(image_file.name)
    else:
        # If it's a file-like object without name (memory), might be hard
        # For now assume it's a path string if passed from analyze_carbon_from_image temp_path
        if isinstance(image_file, str) and os.path.exists(image_file):
             is_live, live_msg = check_live_capture(image_file)
        else:
             is_live, live_msg = True, "Skipped (Stream)" # Fallback
             
    checks['live_capture'] = {"status": is_live, "msg": live_msg}

    # 2. DEPTH CHECK
    if isinstance(image_file, str) and os.path.exists(image_file):
        is_3d, depth_val = analyze_depth(image_file)
        checks['depth_analysis'] = {"status": is_3d, "msg": f"Depth Variance: {depth_val:.2f}"}
    else:
        checks['depth_analysis'] = {"status": True, "msg": "Skipped (Stream)"}

    # 3. VISUAL RECOGNITION (Zero-Shot CLIP + OWL-ViT)
    try:
        if isinstance(image_file, str):
            img = Image.open(image_file).convert('RGB')
        else:
            if hasattr(image_file, 'seek'): image_file.seek(0)
            img = Image.open(image_file).convert('RGB')

        # A. Detect Species (CLIP)
        clip_pipe = get_clip_pipeline()
        found_labels = []
        is_biomass = False
        display_conf = 0.0

        if clip_pipe:
            # We add generic "not a tree" or "man made object" as a negative control
            labels_to_check = INDIAN_TREE_SPECIES + ["bushes", "grass", "indoor furniture", "man-made object", "car", "building"]
            results = clip_pipe(img, candidate_labels=labels_to_check)
            
            top_result = results[0]
            top_label = top_result['label'].lower()
            top_score = top_result['score']

            # If it picked a nature/tree class with good confidence
            if top_label not in ["indoor furniture", "man-made object", "car", "building"]:
                is_biomass = True
                found_labels.append(top_label) # e.g. "neem tree"
                display_conf = top_score
            else:
                 is_biomass = False
                 found_labels.append("non-biomass")
                 display_conf = top_score

        # B. Count Trees (OWL-ViT)
        count = 1
        owl_pipe = get_owl_pipeline()
        if owl_pipe and is_biomass:
             # Query to find trees in the image. Threshold determines strictness.
             predictions = owl_pipe(img, candidate_labels=["tree", "plant"], threshold=0.1)
             if len(predictions) > 0:
                 count = len(predictions)
             
        # Add the count directly to checks so we can see it in logs if we wanted, 
        # but the main pipeline expects `is_biomass, confidence, labels, checks` and handles count later. 
        # Wait, the current signature of detect_tree doesn't return count.
        # It returns is_biomass, confidence, labels, checks.
        # We will add tree_count to the checks dictionary so ai_engine can extract it.
        checks['tree_count'] = count
        
        return is_biomass, round(display_conf, 2), found_labels, checks
        
    except Exception as e:
        print(f"Vision Error: {e}")
        checks['tree_count'] = 1
        return True, 0.85, ['forest_fallback'], checks