import json
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_utils import to_wei, is_address, to_checksum_address
from solcx import compile_source, install_solc
from dotenv import load_dotenv
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('blockchain')

# Load environment variables
load_dotenv()

# Install solc compiler if not already installed
try:
    install_solc('0.8.0')
    logger.info("Solidity compiler installed successfully")
except Exception as e:
    logger.warning(f"Solidity compiler installation warning: {e}")

class BlockchainManager:
    def __init__(self, contract_file='contracts/AratroCrop.sol'):
        """Initialize the blockchain manager with the contract file."""
        self.contract_file = contract_file
        self.contract_address = None
        self.w3 = None
        self.contract = None
        self.account = None
        
        # Connect to blockchain
        self.connect_to_blockchain()
        
        # Try to load contract address from file
        self.load_contract_address()
        
        # Deploy contract if not already deployed
        if not self.contract_address:
            self.deploy_contract()
        else:
            self.load_contract()
    
    def load_contract_address(self):
        """Load contract address from file."""
        try:
            if os.path.exists('contract_address.txt'):
                with open('contract_address.txt', 'r') as f:
                    self.contract_address = f.read().strip()
                logger.info(f"Loaded contract address from file: {self.contract_address}")
        except Exception as e:
            logger.error(f"Error loading contract address from file: {e}")
    
    def save_contract_address(self):
        """Save contract address to file."""
        try:
            with open('contract_address.txt', 'w') as f:
                f.write(self.contract_address)
            logger.info(f"Saved contract address to file: {self.contract_address}")
        except Exception as e:
            logger.error(f"Error saving contract address to file: {e}")
    
    def connect_to_blockchain(self):
        """Connect to the blockchain network."""
        # Use Ganache for local development
        ganache_url = os.environ.get('BLOCKCHAIN_URL', 'http://127.0.0.1:7545')
        
        # Log the blockchain URL being used
        logger.info(f"Attempting to connect to blockchain at {ganache_url}")
        logger.info("To use a different blockchain URL, set the BLOCKCHAIN_URL environment variable")
        logger.info("For network access, make sure the blockchain is accessible from other machines")
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(ganache_url))
            # Add middleware for compatibility with PoA chains like Ganache
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection
            try:
                # Try to get the block number to check connection
                block_number = self.w3.eth.block_number
                logger.info(f"Connected to blockchain at {ganache_url}, current block: {block_number}")
                # Set default account
                self.account = self.w3.eth.accounts[0]
                logger.info(f"Using account: {self.account}")
            except Exception as e:
                logger.error(f"Failed to connect to blockchain at {ganache_url}: {e}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to blockchain: {e}")
            return False
    
    def compile_contract(self):
        """Compile the Solidity contract."""
        try:
            with open(self.contract_file, 'r') as file:
                contract_source = file.read()
            
            compiled_sol = compile_source(
                contract_source,
                output_values=['abi', 'bin'],
                solc_version='0.8.0'
            )
            
            # Extract the contract interface
            contract_id, contract_interface = compiled_sol.popitem()
            abi = contract_interface['abi']
            bytecode = contract_interface['bin']
            
            logger.info(f"Contract compiled successfully: {contract_id}")
            return abi, bytecode
        except Exception as e:
            logger.error(f"Error compiling contract: {e}")
            return None, None
    
    def deploy_contract(self):
        """Deploy the contract to the blockchain."""
        try:
            abi, bytecode = self.compile_contract()
            if not abi or not bytecode:
                logger.error("Failed to compile contract")
                return
            
            # Create contract
            Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Build transaction
            transaction = Contract.constructor().build_transaction({
                'from': self.account,
                'nonce': self.w3.eth.get_transaction_count(self.account),
                'gas': 5000000,
                'gasPrice': to_wei('50', 'gwei')
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=os.environ.get('PRIVATE_KEY'))
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.contract_address = tx_receipt.contractAddress
            
            # Save contract address to file
            self.save_contract_address()
            
            # Load the deployed contract
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)
            
            logger.info(f"Contract deployed at address: {self.contract_address}")
            
            # Save ABI to file for future use
            with open('contract_abi.json', 'w') as f:
                json.dump(abi, f)
            
            return self.contract_address
        except Exception as e:
            logger.error(f"Error deploying contract: {e}")
            return None
    
    def load_contract(self):
        """Load an existing contract."""
        try:
            # Load ABI from file
            try:
                with open('contract_abi.json', 'r') as f:
                    abi = json.load(f)
            except FileNotFoundError:
                # If ABI file doesn't exist, compile the contract
                abi, _ = self.compile_contract()
            
            if not abi:
                logger.error("Failed to load contract ABI")
                return
            
            # Create contract instance
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)
            logger.info(f"Contract loaded from address: {self.contract_address}")
            return self.contract
        except Exception as e:
            logger.error(f"Error loading contract: {e}")
            return None
    
    def create_stock(self, crop_type, quantity, requested_quantity, farmer_address, warehouse_address):
        """Create a new stock entry on the blockchain."""
        try:
            logger.info(f"Creating stock with type={crop_type}, quantity={quantity}, requested_quantity={requested_quantity}")
            
            # Ensure addresses have 0x prefix
            if not farmer_address.startswith('0x'):
                farmer_address = f'0x{farmer_address}'
            if not warehouse_address.startswith('0x'):
                warehouse_address = f'0x{warehouse_address}'
                
            # Validate addresses
            if not is_address(farmer_address):
                logger.error(f"Invalid farmer address: {farmer_address}")
                return None
            if not is_address(warehouse_address):
                logger.error(f"Invalid warehouse address: {warehouse_address}")
                return None
            
            # Convert addresses to checksum format
            farmer_address = to_checksum_address(farmer_address)
            warehouse_address = to_checksum_address(warehouse_address)
            
            # Ensure quantity is an integer (blockchain uses kg, not tons)
            try:
                quantity = int(quantity)
                requested_quantity = int(requested_quantity)
                logger.info(f"Using quantity={quantity}kg, requested_quantity={requested_quantity}kg")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid quantity values: {e}")
                return None
            
            # Build transaction
            tx = self.contract.functions.createStock(
                crop_type,
                quantity,
                requested_quantity,
                farmer_address,
                warehouse_address
            ).build_transaction({
                'from': self.account,
                'nonce': self.w3.eth.get_transaction_count(self.account),
                'gas': 2000000,
                'gasPrice': to_wei('50', 'gwei')
            })
            
            # Sign and send transaction
            try:
                private_key = os.environ.get('PRIVATE_KEY')
                if not private_key:
                    logger.error("No private key found in environment variables")
                    return None
                
                if not private_key.startswith('0x'):
                    private_key = f'0x{private_key}'
                
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()  # Convert bytes to hex string
                
                logger.info(f"Transaction sent with hash: {tx_hash_hex}")
            except Exception as e:
                logger.error(f"Error signing or sending transaction: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Wait for transaction receipt
            try:
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                logger.info(f"Transaction receipt received: status={tx_receipt.status}")
            except Exception as e:
                logger.error(f"Error waiting for transaction receipt: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Extract the stock ID from the event logs
            stock_id = None
            try:
                # Try to get the stock ID from the event logs
                logs = self.contract.events.StockCreated().process_receipt(tx_receipt)
                stock_id = logs[0]['args']['id']
                logger.info(f"Extracted stock ID from logs: {stock_id}")
            except Exception as e:
                logger.warning(f"Could not extract stock ID from logs: {e}")
                # Fallback: Extract from the logs directly
                if tx_receipt.logs and len(tx_receipt.logs) > 0:
                    # The first topic is the event signature, the second is the indexed id
                    if len(tx_receipt.logs[0]['topics']) > 1:
                        # Convert the hex topic to an integer
                        stock_id = int(tx_receipt.logs[0]['topics'][1].hex(), 16)
                        logger.info(f"Extracted stock ID from topics: {stock_id}")
                    else:
                        # If we can't get it from topics, try to decode the data
                        stock_id = int.from_bytes(tx_receipt.logs[0]['data'][:32], byteorder='big')
                        logger.info(f"Extracted stock ID from data: {stock_id}")
                else:
                    # Last resort: use the transaction count as an approximation
                    stock_id = self.w3.eth.get_transaction_count(self.account)
                    logger.warning(f"Using fallback stock ID: {stock_id}")
            
            logger.info(f"Stock created with ID: {stock_id} and transaction hash: {tx_hash_hex}")
            
            # Return both the blockchain ID and transaction hash
            return {
                'blockchain_id': stock_id,
                'tx_hash': tx_hash_hex
            }
        except Exception as e:
            logger.error(f"Error creating stock: {e}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return None
    
    def update_stock_status(self, stock_id, status):
        """Update the status of a stock."""
        try:
            # Convert status string to enum value
            status_map = {
                'pending': 0,
                'stored': 1,
                'rejected': 2,
                'transferred': 3
            }
            status_value = status_map.get(status.lower(), 0)
            
            # Build transaction
            tx = self.contract.functions.updateStockStatus(
                stock_id,
                status_value
            ).build_transaction({
                'from': self.account,
                'nonce': self.w3.eth.get_transaction_count(self.account),
                'gas': 2000000,
                'gasPrice': to_wei('50', 'gwei')
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=os.environ.get('PRIVATE_KEY'))
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Stock {stock_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating stock status: {e}")
            return False
    
    def create_stock_request(self, farmer_address, warehouse_address, stock_id):
        """Create a stock request on the blockchain."""
        try:
            logger.info(f"Creating stock request for stock {stock_id} from {farmer_address} to {warehouse_address}")
            
            # Ensure addresses have 0x prefix
            if not farmer_address.startswith('0x'):
                farmer_address = f'0x{farmer_address}'
            if not warehouse_address.startswith('0x'):
                warehouse_address = f'0x{warehouse_address}'
                
            # Validate addresses
            if not is_address(farmer_address):
                logger.error(f"Invalid farmer address: {farmer_address}")
                return None
            if not is_address(warehouse_address):
                logger.error(f"Invalid warehouse address: {warehouse_address}")
                return None
            
            # Convert addresses to checksum format
            farmer_address = to_checksum_address(farmer_address)
            warehouse_address = to_checksum_address(warehouse_address)
            
            # Ensure stock_id is an integer
            try:
                stock_id = int(stock_id)
                logger.info(f"Using stock_id={stock_id}")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid stock_id: {e}")
                return None
            
            # Build transaction
            try:
                tx = self.contract.functions.createStockRequest(
                    farmer_address,
                    warehouse_address,
                    stock_id
                ).build_transaction({
                    'from': self.account,
                    'nonce': self.w3.eth.get_transaction_count(self.account),
                    'gas': 2000000,
                    'gasPrice': to_wei('50', 'gwei')
                })
                logger.info(f"Transaction built successfully")
            except Exception as e:
                logger.error(f"Error building transaction: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Sign and send transaction
            try:
                private_key = os.environ.get('PRIVATE_KEY')
                if not private_key:
                    logger.error("No private key found in environment variables")
                    return None
                
                if not private_key.startswith('0x'):
                    private_key = f'0x{private_key}'
                
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()  # Convert bytes to hex string
                
                logger.info(f"Transaction sent with hash: {tx_hash_hex}")
            except Exception as e:
                logger.error(f"Error signing or sending transaction: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Wait for transaction receipt
            try:
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                logger.info(f"Transaction receipt received: status={tx_receipt.status}")
                
                if tx_receipt.status != 1:
                    logger.error(f"Transaction failed with status: {tx_receipt.status}")
                    return None
            except Exception as e:
                logger.error(f"Error waiting for transaction receipt: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Extract the request ID from the event logs
            request_id = None
            try:
                # Get the event signature for StockRequestCreated
                event_signature = self.w3.keccak(text="StockRequestCreated(uint256,address,address,uint256)").hex()
                logger.info(f"Event signature: {event_signature}")
                
                # Find the log with the matching event signature
                for log in tx_receipt.logs:
                    if len(log['topics']) > 0 and log['topics'][0].hex() == event_signature:
                        # The first topic is the event signature, the second is the indexed id
                        request_id = int(log['topics'][1].hex(), 16)
                        logger.info(f"Extracted request ID from topics: {request_id}")
                        break
                
                if request_id is None:
                    # Try using the contract events API
                    try:
                        logs = self.contract.events.StockRequestCreated().process_receipt(tx_receipt)
                        request_id = logs[0]['args']['id']
                        logger.info(f"Extracted request ID from events API: {request_id}")
                    except Exception as e:
                        logger.warning(f"Could not extract request ID from events API: {e}")
                        
                        # Fallback: try to get the request ID from the transaction data
                        request_id = self.w3.eth.get_transaction_count(self.account)
                        logger.warning(f"Could not extract request ID from logs, using fallback: {request_id}")
            except Exception as e:
                logger.warning(f"Could not extract request ID from logs: {e}")
                logger.warning(f"Exception traceback: {traceback.format_exc()}")
                # Fallback: use the transaction count as an approximation
                request_id = self.w3.eth.get_transaction_count(self.account)
                logger.warning(f"Using fallback request ID: {request_id}")
            
            logger.info(f"Stock request created with ID: {request_id} and transaction hash: {tx_hash_hex}")
            
            # Return both the blockchain ID and transaction hash
            return {
                'blockchain_id': request_id,
                'tx_hash': tx_hash_hex
            }
        except Exception as e:
            logger.error(f"Error creating stock request: {e}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return None
    
    def update_stock_request_status(self, request_id, status):
        """Update the status of a stock request."""
        try:
            # Convert status string to enum value
            status_map = {
                'pending': 0,
                'stored': 1,
                'rejected': 2,
                'transferred': 3,
                'approved': 1  # Map 'approved' to the same value as 'stored'
            }
            status_value = status_map.get(status.lower(), 0)
            
            # Build transaction
            tx = self.contract.functions.updateStockRequestStatus(
                request_id,
                status_value
            ).build_transaction({
                'from': self.account,
                'nonce': self.w3.eth.get_transaction_count(self.account),
                'gas': 2000000,
                'gasPrice': to_wei('50', 'gwei')
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=os.environ.get('PRIVATE_KEY'))
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Stock request {request_id} status updated to {status}")
            
            # Return both success status and transaction hash
            return {
                'success': True,
                'tx_hash': tx_hash.hex()
            }
        except Exception as e:
            logger.error(f"Error updating stock request status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_stock(self, stock_id):
        """Get stock details from the blockchain."""
        try:
            stock = self.contract.functions.getStock(stock_id).call()
            
            # Convert to a more readable format
            status_map = {
                0: 'pending',
                1: 'stored',
                2: 'rejected',
                3: 'transferred'
            }
            
            stock_data = {
                'id': stock[0],
                'crop_type': stock[1],
                'quantity': stock[2] / 1000,  # Convert from kg to tons
                'requested_quantity': stock[3] / 1000,  # Convert from kg to tons
                'status': status_map.get(stock[4], 'unknown'),
                'farmer': stock[5],
                'warehouse': stock[6],
                'timestamp': stock[7],
                'updated_at': stock[8]
            }
            
            return stock_data
        except Exception as e:
            logger.error(f"Error getting stock: {e}")
            return None
    
    def get_stock_request(self, request_id):
        """Get stock request details from the blockchain."""
        try:
            request = self.contract.functions.getStockRequest(request_id).call()
            
            # Convert to a more readable format
            status_map = {
                0: 'pending',
                1: 'stored',
                2: 'rejected',
                3: 'transferred'
            }
            
            request_data = {
                'id': request[0],
                'from': request[1],
                'to': request[2],
                'stock_id': request[3],
                'request_date': request[4],
                'status': status_map.get(request[5], 'unknown'),
                'created_at': request[6],
                'updated_at': request[7]
            }
            
            return request_data
        except Exception as e:
            logger.error(f"Error getting stock request: {e}")
            return None
    
    def get_total_stocks(self):
        """Get the total number of stocks on the blockchain."""
        try:
            return self.contract.functions.getTotalStocks().call()
        except Exception as e:
            logger.error(f"Error getting total stocks: {e}")
            return 0
    
    def get_total_stock_requests(self):
        """Get the total number of stock requests on the blockchain."""
        try:
            return self.contract.functions.getTotalStockRequests().call()
        except Exception as e:
            logger.error(f"Error getting total stock requests: {e}")
            return 0
    
    def get_total_ration_stock_requests(self):
        """Get the total number of ration stock requests on the blockchain."""
        try:
            return self.contract.functions.getTotalRationStockRequests().call()
        except Exception as e:
            logger.error(f"Error getting total ration stock requests: {e}")
            return 0
    
    def create_ration_stock_request(self, ration_shop_address, warehouse_address, stock_type, quantity, notes=""):
        """Create a ration stock request on the blockchain."""
        try:
            logger.info(f"Creating ration stock request for {stock_type} from {ration_shop_address} to {warehouse_address}")
            
            # Ensure addresses have 0x prefix
            if not ration_shop_address.startswith('0x'):
                ration_shop_address = f'0x{ration_shop_address}'
            if not warehouse_address.startswith('0x'):
                warehouse_address = f'0x{warehouse_address}'
                
            # Validate addresses
            if not is_address(ration_shop_address):
                logger.error(f"Invalid ration shop address: {ration_shop_address}")
                return None
            if not is_address(warehouse_address):
                logger.error(f"Invalid warehouse address: {warehouse_address}")
                return None
            
            # Convert addresses to checksum format
            ration_shop_address = to_checksum_address(ration_shop_address)
            warehouse_address = to_checksum_address(warehouse_address)
            
            # Ensure quantity is an integer (blockchain uses kg)
            try:
                quantity = int(quantity)
                logger.info(f"Using quantity={quantity}kg")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid quantity value: {e}")
                return None
            
            # Build transaction
            try:
                tx = self.contract.functions.createRationStockRequest(
                    ration_shop_address,
                    warehouse_address,
                    stock_type,
                    quantity,
                    notes
                ).build_transaction({
                    'from': self.account,
                    'nonce': self.w3.eth.get_transaction_count(self.account),
                    'gas': 2000000,
                    'gasPrice': to_wei('50', 'gwei')
                })
                logger.info(f"Transaction built successfully")
            except Exception as e:
                logger.error(f"Error building transaction: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Sign and send transaction
            try:
                private_key = os.environ.get('PRIVATE_KEY')
                if not private_key:
                    logger.error("No private key found in environment variables")
                    return None
                
                if not private_key.startswith('0x'):
                    private_key = f'0x{private_key}'
                
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()  # Convert bytes to hex string
                
                logger.info(f"Transaction sent with hash: {tx_hash_hex}")
            except Exception as e:
                logger.error(f"Error signing or sending transaction: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Wait for transaction receipt
            try:
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                logger.info(f"Transaction receipt received: status={tx_receipt.status}")
                
                if tx_receipt.status != 1:
                    logger.error(f"Transaction failed with status: {tx_receipt.status}")
                    return None
            except Exception as e:
                logger.error(f"Error waiting for transaction receipt: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return None
            
            # Extract the request ID from the event logs
            request_id = None
            try:
                # Get the event signature for RationStockRequestCreated
                event_signature = self.w3.keccak(text="RationStockRequestCreated(uint256,address,address,string)").hex()
                logger.info(f"Event signature: {event_signature}")
                
                # Find the log with the matching event signature
                for log in tx_receipt.logs:
                    if len(log['topics']) > 0 and log['topics'][0].hex() == event_signature:
                        # The first topic is the event signature, the second is the indexed id
                        request_id = int(log['topics'][1].hex(), 16)
                        logger.info(f"Extracted request ID from topics: {request_id}")
                        break
                
                if request_id is None:
                    # Try using the contract events API
                    try:
                        logs = self.contract.events.RationStockRequestCreated().process_receipt(tx_receipt)
                        request_id = logs[0]['args']['id']
                        logger.info(f"Extracted request ID from events API: {request_id}")
                    except Exception as e:
                        logger.warning(f"Could not extract request ID from events API: {e}")
                        
                        # Fallback: use the transaction count as an approximation
                        request_id = self.w3.eth.get_transaction_count(self.account)
                        logger.warning(f"Could not extract request ID from logs, using fallback: {request_id}")
            except Exception as e:
                logger.warning(f"Could not extract request ID from logs: {e}")
                logger.warning(f"Exception traceback: {traceback.format_exc()}")
                # Fallback: use the transaction count as an approximation
                request_id = self.w3.eth.get_transaction_count(self.account)
                logger.warning(f"Using fallback request ID: {request_id}")
            
            logger.info(f"Ration stock request created with ID: {request_id} and transaction hash: {tx_hash_hex}")
            
            # Return both the blockchain ID and transaction hash
            return {
                'blockchain_id': request_id,
                'tx_hash': tx_hash_hex
            }
        except Exception as e:
            logger.error(f"Error creating ration stock request: {e}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return None
    
    def update_ration_stock_request_status(self, request_id, status, admin_notes=""):
        """Update the status of a ration stock request."""
        try:
            # Convert status string to enum value
            status_map = {
                'pending': 0,
                'approved': 1,
                'rejected': 2,
                'transferred': 3
            }
            status_value = status_map.get(status.lower(), 0)
            
            # Build transaction
            try:
                tx = self.contract.functions.updateRationStockRequestStatus(
                    request_id,
                    status_value,
                    admin_notes
                ).build_transaction({
                    'from': self.account,
                    'nonce': self.w3.eth.get_transaction_count(self.account),
                    'gas': 2000000,
                    'gasPrice': to_wei('50', 'gwei')
                })
                logger.info(f"Transaction built successfully")
            except Exception as e:
                logger.error(f"Error building transaction: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': str(e)
                }
            
            try:
                private_key = os.environ.get('PRIVATE_KEY')
                if not private_key:
                    logger.error("No private key found in environment variables")
                    return {
                        'success': False,
                        'error': "No private key found in environment variables"
                    }
                
                if not private_key.startswith('0x'):
                    private_key = f'0x{private_key}'
                
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()  # Convert bytes to hex string
                
                logger.info(f"Transaction sent with hash: {tx_hash_hex}")
            except Exception as e:
                logger.error(f"Error signing or sending transaction: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': str(e)
                }
            
            # Wait for transaction receipt
            try:
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                logger.info(f"Transaction receipt received: status={tx_receipt.status}")
                
                if tx_receipt.status != 1:
                    logger.error(f"Transaction failed with status: {tx_receipt.status}")
                    return {
                        'success': False,
                        'error': f"Transaction failed with status: {tx_receipt.status}"
                    }
            except Exception as e:
                logger.error(f"Error waiting for transaction receipt: {e}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': str(e)
                }
            
            logger.info(f"Ration stock request {request_id} status updated to {status}")
            
            # Return both success status and transaction hash
            return {
                'success': True,
                'tx_hash': tx_hash_hex
            }
        except Exception as e:
            logger.error(f"Error updating ration stock request status: {e}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ration_stock_request(self, request_id):
        """Get ration stock request details from the blockchain."""
        try:
            # Call the contract function
            result = self.contract.functions.getRationStockRequest(request_id).call()
            
            # Convert to a more readable format
            status_map = {
                0: 'pending',
                1: 'approved',
                2: 'rejected',
                3: 'transferred'
            }
            
            request_data = {
                'id': result[0],
                'rationShop': result[1],
                'warehouse': result[2],
                'stockType': result[3],
                'quantity': result[4] / 1000,  # Convert from kg to tons
                'status': status_map.get(result[5], 'unknown'),
                'requestDate': result[6],
                'processedDate': result[7],
                'notes': result[8],
                'adminNotes': result[9],
                'createdAt': result[10],
                'updatedAt': result[11]
            }
            
            return request_data
        except Exception as e:
            logger.error(f"Error getting ration stock request: {e}")
            return None

# Initialize blockchain manager
blockchain_manager = None

def init_blockchain():
    """Initialize the blockchain manager."""
    global blockchain_manager
    try:
        blockchain_manager = BlockchainManager()
        return blockchain_manager
    except Exception as e:
        logger.error(f"Error initializing blockchain: {e}")
        return None

# Helper function to get Ethereum addresses for users
def get_eth_address(user_id, role):
    """
    Generate a deterministic Ethereum address for a user.
    In a real application, users would have their own wallets.
    """
    # This is a simplified approach for demo purposes
    # In production, users should have their own wallets and private keys
    return f"0x{user_id:040x}" 