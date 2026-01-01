import json
import os
from web3 import Web3
from django.conf import settings

def get_contract_and_w3():
    # Setup connection to Sepolia
    w3 = Web3(Web3.HTTPProvider(settings.INFURA_URL))
    
    # Locate the ABI file in your artifacts folder
    abi_path = os.path.join(settings.BASE_DIR, 'artifacts/contracts/CarbonCreditMarket.sol/CarbonCreditMarket.json')
    
    with open(abi_path) as f:
        artifact = json.load(f)
        
    contract = w3.eth.contract(address=settings.CONTRACT_ADDRESS, abi=artifact['abi'])
    return contract, w3

def mint_static_credit(farmer_wallet, amount_tons):
    contract, w3 = get_contract_and_w3()
    admin_account = w3.eth.account.from_key(settings.PRIVATE_KEY)
    
    nonce = w3.eth.get_transaction_count(admin_account.address)
    tx = contract.functions.mintVerifiedCredit(
        farmer_wallet, 
        w3.to_wei(amount_tons, 'ether')
    ).build_transaction({
        'chainId': 11155111, # Sepolia ID
        'gas': 300000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return w3.to_hex(tx_hash)

# THIS IS THE MISSING FUNCTION CAUSING THE ERROR
def get_rcc_balance(wallet_address):
    try:
        contract, w3 = get_contract_and_w3()
        balance_wei = contract.functions.balanceOf(wallet_address).call()
        return w3.from_wei(balance_wei, 'ether')
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return 0