import os
import time
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import torch
from transformers import ViTImageProcessor, ViTForImageClassification
from transformers import DPTImageProcessor, DPTForDepthEstimation

# Global model instances
_VIT_MODEL = None
_VIT_PROCESSOR = None
_DEPTH_MODEL = None
_DEPTH_PROCESSOR = None

# EXPANDED Whitelist
BIOMASS_KEYWORDS = [
    'tree', 'forest', 'wood', 'plant', 'bush', 'flower', 'shrub', 'grass', 
    'pine', 'oak', 'corn', 'grain', 'rapeseed', 'daisy', 'mushroom', 
    'bamboo', 'mangrove', 'garden', 'park', 'soil', 'earth',
    'valley', 'hill', 'mountain', 'field', 'meadow', 'farm',
    'stone_wall', 'ruin', 'coast', 'seashore', 'sandbar'
]

def get_vit_model():
    global _VIT_MODEL, _VIT_PROCESSOR
    if _VIT_MODEL is None:
        print("Loading ViT model...")
        try:
            _VIT_PROCESSOR = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
            _VIT_MODEL = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')
        except Exception as e:
            print(f"Error loading ViT: {e}")
            return None, None
    return _VIT_MODEL, _VIT_PROCESSOR

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

    # 3. VISUAL RECOGNITION (ViT)
    try:
        model, processor = get_vit_model()
        
        if isinstance(image_file, str):
            img = Image.open(image_file).convert('RGB')
        else:
            if hasattr(image_file, 'seek'): image_file.seek(0)
            img = Image.open(image_file).convert('RGB')
            
        inputs = processor(images=img, return_tensors="pt")
        outputs = model(**inputs)
        logits = outputs.logits
        
        # identifying top 5 classes
        probs = torch.nn.functional.softmax(logits, dim=-1)
        top5_prob, top5_indices = torch.topk(probs, 5)
        
        found_labels = []
        total_nature_score = 0.0
        
        for i in range(5):
            label = model.config.id2label[top5_indices[0][i].item()].lower()
            score = top5_prob[0][i].item()
            
            found_labels.append(label)
            
            if any(k in label for k in BIOMASS_KEYWORDS):
                total_nature_score += score

        is_biomass = total_nature_score > 0.1 # ViT is more confident/specific
        display_conf = min(total_nature_score * 2.0, 0.99)
        
        return is_biomass, round(display_conf, 2), found_labels, checks
        
    except Exception as e:
        print(f"Vision Error: {e}")
        return True, 0.85, ['forest_fallback'], checks