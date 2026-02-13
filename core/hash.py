import os
import json
import imagehash

# --- HACKATHON MODE SETTING ---
# Set to True so you can upload the same image repeatedly for demos
ALLOW_DUPLICATES = True 

HASH_FILE = "image_hashes.json"

def load_hashes():
    if not os.path.exists(HASH_FILE):
        return []
    with open(HASH_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

def save_hash(hash_str):
    hashes = load_hashes()
    if hash_str not in hashes:
        hashes.append(hash_str)
        with open(HASH_FILE, 'w') as f:
            json.dump(hashes, f)

def check_duplicate(current_hash_str):
    """
    Checks if image has been seen before.
    """
    # 1. IMMEDIATE BYPASS FOR DEMO
    if ALLOW_DUPLICATES:
        return False  # Always returns "Unique" (False = Not a duplicate)

    # 2. Standard Logic (Ignored if ALLOW_DUPLICATES is True)
    existing_hashes = load_hashes()
    
    if current_hash_str in existing_hashes:
        return True
            
    # Save the new hash for future reference
    save_hash(current_hash_str)
    return False