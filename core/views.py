import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .blockchain_utils import mint_static_credit
from .ai_engine import analyze_carbon_from_image

FARMER_WALLET = "0x1E0e1AF120ddec6acF5AE07D327C392E82966bAE"

# MEMORY STORAGE for file hashes (Simple double-spend check)
# The AI Engine handles the advanced "Semantic" (Visual) duplicate check.
USED_FILE_HASHES = set()

@csrf_exempt
def test_mint_view(request):
    if request.method == 'POST':
        try:
            # 1. GET DATA (Support Batch)
            images = request.FILES.getlist('images') # <--- KEY CHANGE
            if not images:
                # Fallback for single file
                if 'image' in request.FILES:
                    images = [request.FILES['image']]
                else:
                    return JsonResponse({"status": "Error", "message": "No images uploaded"}, status=400)
            
            gps_lat = request.POST.get('latitude', '0.0')
            gps_lon = request.POST.get('longitude', '0.0')

            print(f"RECEIVED BATCH: {len(images)} files from {gps_lat}, {gps_lon}")

            batch_total_tons = 0.0
            batch_total_trees = 0
            processed_details = []
            valid_hashes = []

            # 2. LOOP THROUGH EACH IMAGE
            for idx, img in enumerate(images):
                print(f"   --- Processing Image {idx+1}/{len(images)}: {img.name} ---")
                
                # A. HASH CHECK (Exact file duplicate)
                img.seek(0)
                file_hash = hashlib.md5(img.read()).hexdigest()
                if file_hash in USED_FILE_HASHES:
                    print(f"   SKIPPED: Exact duplicate file.")
                    processed_details.append(f"DUPLICATE {img.name}: Duplicate File")
                    continue
                
                # B. AI ANALYSIS (Hybrid: TF + YOLO + Geo)
                source = request.POST.get('source', 'file')
                
                # Create DB Record
                from .models import Upload
                import imagehash
                from PIL import Image as PilImage
                
                # Get hash for DB
                img.seek(0)
                try:
                    with PilImage.open(img) as pil_img:
                        img_hash_val = str(imagehash.phash(pil_img))
                except:
                    img_hash_val = None

                # Pass to AI
                img.seek(0)
                co2, trees, success, checks = analyze_carbon_from_image(img, claimed_lat=gps_lat, claimed_lon=gps_lon, source=source)

                # Save to DB
                try:
                    Upload.objects.create(
                        image=img,
                        latitude=float(gps_lat) if gps_lat else 0.0,
                        longitude=float(gps_lon) if gps_lon else 0.0,
                        image_hash=img_hash_val,
                        status="APPROVED" if success else "REJECTED"
                    )
                except Exception as e:
                    print(f"   DB Save Error: {e}")

                # C. EVALUATE RESULT
                if not success:
                    # Construct reason string from failed checks
                    failed_items = [k for k, v in checks.items() if not v['status']]
                    reason_str = ", ".join(failed_items).title() + " Failed"
                    
                    print(f"   REJECTED: {reason_str}")
                    processed_details.append({
                        "file": img.name,
                        "status": "REJECTED",
                        "reason": reason_str,
                        "checks": checks, # <--- PASS FULL REPORT
                        "co2": 0.0
                    })
                else:
                    print(f"   ACCEPTED: {co2} tons.")
                    batch_total_tons += co2
                    batch_total_trees += trees
                    processed_details.append({
                        "file": img.name,
                        "status": "ACCEPTED",
                        "reason": "Verified",
                        "checks": checks, # <--- PASS FULL REPORT
                        "co2": co2
                    })
                    valid_hashes.append(file_hash)

            if batch_total_tons <= 0:
                # If all rejected, we still want to return the structured log so the UI can show WHY
                return JsonResponse({
                    "status": "Error", 
                    "message": "Verification Completed",
                    "batch_log": processed_details
                }, status=200)

            # 4. MINT TOTAL TO BLOCKCHAIN
            print(f"MINTING BATCH TOTAL: {batch_total_tons} tons...")
            tx_hash_str = mint_static_credit(FARMER_WALLET, batch_total_tons) 
            
            # 5. LOCK HASHES
            for h in valid_hashes:
                USED_FILE_HASHES.add(h)

            return JsonResponse({
                "status": "Success",
                "tx_hash": tx_hash_str,
                "ai_data": {
                    "trees_detected": batch_total_trees,
                    "co2_tons": round(batch_total_tons, 4),
                    "location": f"{gps_lat}, {gps_lon}"
                },
                "batch_log": processed_details, # Send log to UI
                "message": f"Successfully minted {round(batch_total_tons, 4)} tons from {len(valid_hashes)} valid images."
            })

        except Exception as e:
            print(f"Server Error: {e}")
            return JsonResponse({"status": "Error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "Error", "message": "Use POST method"}, status=405)