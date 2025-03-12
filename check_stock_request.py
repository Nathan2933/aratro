from app import app
from blockchain import BlockchainManager
import logging
from web3 import Web3
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_stock_request')

# Load environment variables
load_dotenv()

def check_stock_request():
    """Test creating a stock request on the blockchain."""
    with app.app_context():
        bm = BlockchainManager()
        
        print(f"Using account: {bm.account}")
        print(f"Contract address: {bm.contract_address}")
        
        # Check total stock requests
        total_requests = bm.get_total_stock_requests()
        print(f"Total stock requests on blockchain: {total_requests}")
        
        # Get the account from private key for testing
        private_key = os.environ.get('PRIVATE_KEY')
        if not private_key:
            print("No private key found in environment variables")
            return
        
        if not private_key.startswith('0x'):
            private_key = f'0x{private_key}'
        
        from eth_account import Account
        account = Account.from_key(private_key)
        address = account.address
        
        # First, create a test stock
        print("\nStep 1: Creating a test stock...")
        stock_result = bm.create_stock(
            crop_type="Test Crop for Request",
            quantity=1000,  # 1 ton = 1000 kg
            requested_quantity=1000,
            farmer_address=address,
            warehouse_address=address
        )
        
        if not stock_result:
            print("Failed to create test stock! Cannot proceed with stock request test.")
            return
        
        print(f"Test stock created successfully!")
        print(f"Stock Blockchain ID: {stock_result['blockchain_id']}")
        print(f"Stock Transaction hash: {stock_result['tx_hash']}")
        
        # Now create a stock request for this stock
        print("\nStep 2: Creating a test stock request...")
        request_result = bm.create_stock_request(
            farmer_address=address,
            warehouse_address=address,
            stock_id=stock_result['blockchain_id']
        )
        
        if request_result:
            print(f"Test stock request created successfully!")
            print(f"Request Blockchain ID: {request_result['blockchain_id']}")
            print(f"Request Transaction hash: {request_result['tx_hash']}")
            
            # Verify the request was created
            new_total_requests = bm.get_total_stock_requests()
            print(f"New total stock requests on blockchain: {new_total_requests}")
            
            if new_total_requests > total_requests:
                print("Stock request count increased, request was created successfully!")
            else:
                print("Stock request count did not increase, request creation may have failed!")
                
            # Try to get the stock request details
            try:
                request_data = bm.get_stock_request(request_result['blockchain_id'])
                print("\nStock request details:")
                print(f"ID: {request_data['id']}")
                print(f"From: {request_data['from']}")
                print(f"To: {request_data['to']}")
                print(f"Stock ID: {request_data['stock_id']}")
                print(f"Status: {request_data['status']}")
            except Exception as e:
                print(f"Error getting stock request details: {e}")
        else:
            print("Failed to create test stock request!")
            
        print("\nDiagnostic information:")
        print("1. Check if the account has enough ETH for gas fees")
        print("2. Check if the contract allows this account to create stock requests")
        print("3. Check if the stock ID exists and is valid")
        print("4. Check if there are any permission issues with the addresses")

if __name__ == "__main__":
    check_stock_request() 