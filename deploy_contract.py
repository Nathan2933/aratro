from app import app
from blockchain import BlockchainManager
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('deploy_contract')

# Load environment variables
load_dotenv()

def deploy_new_contract():
    """Deploy a new contract with the new private key."""
    with app.app_context():
        # Delete the existing contract_address.txt file
        if os.path.exists('contract_address.txt'):
            os.remove('contract_address.txt')
            print("Deleted existing contract_address.txt file")
        
        # Initialize a new BlockchainManager with the correct contract file path
        bm = BlockchainManager(contract_file='contracts/contracts/AratroCrop.sol')
        
        print(f"Using account: {bm.account}")
        print(f"New contract deployed at address: {bm.contract_address}")
        
        # Verify the contract is accessible
        try:
            total_stocks = bm.get_total_stocks()
            print(f"Contract is accessible. Total stocks: {total_stocks}")
            print("Contract deployment successful!")
        except Exception as e:
            print(f"Error accessing contract: {e}")
            print("Contract deployment may have failed!")

if __name__ == "__main__":
    deploy_new_contract() 