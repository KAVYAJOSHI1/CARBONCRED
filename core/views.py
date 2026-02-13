import hashlib
import imagehash
from PIL import Image as PilImage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .blockchain_utils import mint_static_credit
from .ai_engine import analyze_carbon_from_image
from .models import Upload
from core.services.geo import haversine

# Hardcoded for Hackathon (In production, get this from the User's profile/request)
FARMER_WALLET = "0x1E0e1AF120ddec6acF5AE07D327C392E82966bAE"

# MEMORY STORAGE for file hashes (Simple double-spend check)
USED_FILE_HASHES = set()

@csrf_exempt
def test_mint_view(request):
    if request.method == 'POST':
        try:
            # 1. GET DATA (Support Batch Uploads)
            images = request.FILES.getlist('images') 
            if not images:
                # Fallback for single file upload
                if 'image' in request.FILES:
                    images = [request.FILES['image']]
                else:
                    return JsonResponse({"status": "Error", "message": "No images uploaded"}, status=400)
            
            gps_lat = float(request.POST.get('latitude', '0.0'))
            gps_lon = float(request.POST.get('longitude', '0.0'))
            source = request.POST.get('source', 'file')

            print(f"RECEIVED BATCH: {len(images)} files from {gps_lat}, {gps_lon}")

            batch_mint_tons = 0.0
            batch_total_trees = 0
            processed_details = []
            valid_hashes = []

            # 2. LOOP THROUGH EACH IMAGE
            for idx, img in enumerate(images):
                print(f"   --- Processing Image {idx+1}/{len(images)}: {img.name} ---")
                
                # A. HASH CHECK (Exact binary duplicate)
                img.seek(0)
                file_hash = hashlib.md5(img.read()).hexdigest()
                
                if file_hash in USED_FILE_HASHES:
                    print(f"   SKIPPED: Exact duplicate file.")
                    processed_details.append({
                        "file": img.name,
                        "status": "REJECTED",
                        "reason": "Duplicate File (Already Uploaded)",
                        "checks": {"duplicate": {"status": False, "msg": "Exact Match Found"}},
                        "co2": 0.0
                    })
                    continue
                
                # B. CALCULATE VISUAL HASH (For DB)
                img.seek(0)
                try:
                    with PilImage.open(img) as pil_img:
                        img_hash_val = str(imagehash.phash(pil_img))
                except Exception:
                    img_hash_val = None

                # C. AI ANALYSIS (Hybrid: Gatekeepers + Chave 2014)
                # Reset pointer before sending to AI
                img.seek(0)
                co2, trees, success, checks = analyze_carbon_from_image(
                    img, 
                    claimed_lat=str(gps_lat), 
                    claimed_lon=str(gps_lon), 
                    source=source
                )

                # D. BIOMASS DELTA CHECK (New - Old)
                mint_amount = 0.0
                if success:
                    # Find previous approved uploads nearby (2m radius)
                    # Optimization: Filter by rough bounding box first if needed, but simple loop for hackathon
                    previous_uploads = Upload.objects.filter(status="APPROVED")
                    max_prev_biomass = 0.0
                    
                    found_prev = False
                    for prev in previous_uploads:
                        dist = haversine(gps_lat, gps_lon, prev.latitude, prev.longitude)
                        if dist <= 2.0: # 2 meters
                            found_prev = True
                            if prev.biomass_credits > max_prev_biomass:
                                max_prev_biomass = prev.biomass_credits
                    
                    if found_prev:
                        delta = co2 - max_prev_biomass
                        if delta > 0:
                            mint_amount = delta
                            checks['environment']['msg'] += f" | Growth Detected: +{delta:.4f} tons"
                        else:
                            mint_amount = 0.0
                            checks['environment']['msg'] += f" | No New Growth (Prev: {max_prev_biomass:.4f})"
                            # We accept the record but mint 0
                            print(f"   ACCEPTED (No Mint): Delta <= 0")
                    else:
                        mint_amount = co2 # First time for this tree
                        checks['environment']['msg'] += " | New Tree/Location"

                # E. DATABASE LOGGING
                try:
                    Upload.objects.create(
                        image=img,
                        latitude=gps_lat,
                        longitude=gps_lon,
                        image_hash=img_hash_val,
                        biomass_credits=co2, # Store TOTAL biomass
                        status="APPROVED" if success else "REJECTED"
                    )
                except Exception as e:
                    print(f"   DB Save Error: {e}")

                # F. AGGREGATE RESULTS
                if not success:
                    # Construct readable reason
                    failed_items = [k for k, v in checks.items() if not v['status']]
                    reason_str = ", ".join(failed_items).title() + " Check Failed"
                    
                    print(f"   REJECTED: {reason_str}")
                    processed_details.append({
                        "file": img.name,
                        "status": "REJECTED",
                        "reason": reason_str,
                        "checks": checks,
                        "co2": 0.0
                    })
                else:
                    print(f"   ACCEPTED: {mint_amount} tons minted (Total: {co2}).")
                    batch_mint_tons += mint_amount
                    batch_total_trees += trees
                    
                    processed_details.append({
                        "file": img.name,
                        "status": "ACCEPTED",
                        "reason": "Verified",
                        "checks": checks,
                        "co2": mint_amount # Show what was minted
                    })
                    # Only lock hash if accepted
                    valid_hashes.append(file_hash)

            # 3. HANDLE RESULTS
            if batch_mint_tons <= 0 and batch_total_trees > 0:
                 # Valid trees but no new growth
                 pass 
            elif batch_mint_tons <= 0:
                return JsonResponse({
                    "status": "Completed", 
                    "message": "No valid new biomass detected in batch.",
                    "ai_data": {
                        "trees_detected": batch_total_trees,
                        "co2_tons": 0.0,
                        "location": f"{gps_lat}, {gps_lon}"
                    },
                    "batch_log": processed_details
                }, status=200)

            # 4. MINT TO BLOCKCHAIN
            mint_status = "Skipped (0 Mint)"
            tx_hash_str = "None"
            
            if batch_mint_tons > 0:
                print(f"MINTING BATCH TOTAL: {batch_mint_tons} tons...")
                try:
                    tx_hash_str = mint_static_credit(FARMER_WALLET, batch_mint_tons)
                    mint_status = "Success"
                except Exception as e:
                    print(f"Blockchain Error: {e}")
                    tx_hash_str = "MINT_FAILED"
                    mint_status = f"Minting Failed: {str(e)}"
            
            # 5. LOCK HASHES (Prevent Replay)
            if mint_status == "Success" or (batch_mint_tons == 0 and batch_total_trees > 0):
                # Lock hashes even if 0 mint (valid tree, just didn't grow)
                for h in valid_hashes:
                    USED_FILE_HASHES.add(h)

            return JsonResponse({
                "status": mint_status,
                "tx_hash": tx_hash_str,
                "ai_data": {
                    "trees_detected": batch_total_trees,
                    "co2_tons": round(batch_mint_tons, 4),
                    "location": f"{gps_lat}, {gps_lon}"
                },
                "batch_log": processed_details,
                "message": f"Minted {round(batch_mint_tons, 4)} tons for {len(valid_hashes)} valid images."
            })

        except Exception as e:
            print(f"Server Critical Error: {e}")
            return JsonResponse({"status": "Error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "Error", "message": "Use POST method"}, status=405)