# views.py
from django.shortcuts import render
from django.http import HttpResponse
from .models import CarbonCreditData
from ..core.blockchain_utils import mint_static_credit

def test_mint_view(request):
    # For testing, we create/get a static farmer
    farmer, created = CarbonCreditData.objects.get_or_create(
        farmer_name="Kavya Test Farmer",
        farmer_wallet="0x123...PASTE_A_TEST_WALLET_ADDRESS_HERE" # Use a second MetaMask address
    )
    
    try:
        # Trigger the mint using static values
        tx_hash = mint_static_credit(farmer.farmer_wallet, farmer.static_co2_offset)
        
        # Update our DB
        farmer.tx_hash = tx_hash
        farmer.status = "Minted"
        farmer.save()
        
        return HttpResponse(f"Success! Tokens Minted. TX Hash: {tx_hash}")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")