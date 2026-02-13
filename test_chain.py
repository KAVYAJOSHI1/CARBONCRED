import os
import json
from web3 import Web3
from dotenv import load_dotenv

# 1. Load Env
load_dotenv()

print("--- BLOCKCHAIN DIAGNOSTIC TOOL ---")

# 2. Check Keys
infura = os.getenv("INFURA_URL")
private_key = os.getenv("PRIVATE_KEY")
contract_addr = os.getenv("CONTRACT_ADDRESS")

print(f"1. INFURA_URL Found?   {'✅ Yes' if infura else '❌ NO'}")
print(f"2. PRIVATE_KEY Found?  {'✅ Yes' if private_key else '❌ NO'}")
print(f"3. ADDRESS Found?      {'✅ Yes' if contract_addr else '❌ NO'}")

if not (infura and private_key and contract_addr):
    print("\n🛑 STOP: Missing .env variables. The system is definitely using MOCK data.")
    exit()

# 3. Check Connection
try:
    w3 = Web3(Web3.HTTPProvider(infura))
    if w3.is_connected():
        print(f"4. Connection?         ✅ Connected to Sepolia (Block: {w3.eth.block_number})")
    else:
        print("4. Connection?         ❌ Failed to connect to Infura")
        exit()
except Exception as e:
    print(f"4. Connection?         ❌ Error: {e}")
    exit()

# 4. Check Artifact File
path = os.path.join(os.getcwd(), 'artifacts/contracts/CarbonCreditMarket.sol/CarbonCreditMarket.json')
if os.path.exists(path):
    print("5. Artifact File?      ✅ Found CarbonCreditMarket.json")
    
    # 5. Check Contract
    try:
        with open(path) as f:
            abi = json.load(f)['abi']
        contract = w3.eth.contract(address=contract_addr, abi=abi)
        symbol = contract.functions.symbol().call()
        print(f"6. Contract Valid?     ✅ Yes! Token Symbol: {symbol}")
        print("\n🎉 CONCLUSION: REAL BLOCKCHAIN IS WORKING!")
    except Exception as e:
        print(f"6. Contract Valid?     ❌ Error calling contract: {e}")
else:
    print(f"5. Artifact File?      ❌ NOT FOUND at {path}")
    print("   (Did you run 'npx hardhat compile'?)")
    print("\n⚠️ CONCLUSION: System is using MOCK data because the file is missing.")