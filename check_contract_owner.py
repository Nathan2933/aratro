from app import app
from blockchain import BlockchainManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_contract')

def check_contract_owner():
    """Check the contract owner and compare it with the current account."""
    with app.app_context():
        bm = BlockchainManager()
        
        print(f"Using account: {bm.account}")
        print(f"Contract address: {bm.contract_address}")
        
        # Get the contract owner
        contract_owner = bm.contract.functions.owner().call()
        print(f"Contract owner: {contract_owner}")
        
        # Check if the current account is the contract owner
        if bm.account.lower() == contract_owner.lower():
            print("The current account is the contract owner.")
        else:
            print("The current account is NOT the contract owner.")
            print("You may need to redeploy the contract with the new account.")

if __name__ == "__main__":
    check_contract_owner() 