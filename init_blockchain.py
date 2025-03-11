"""
Script to initialize the blockchain environment.
This script will:
1. Install the Solidity compiler
2. Compile the smart contract
3. Deploy the smart contract to the blockchain
4. Save the contract address to the .env file
"""
import os
import sys
import logging
from dotenv import load_dotenv
from solcx import install_solc, compile_source
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_utils import to_wei

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('init_blockchain')

# Load environment variables
load_dotenv()

def install_solidity_compiler():
    """Install the Solidity compiler."""
    try:
        install_solc('0.8.0')
        logger.info("Solidity compiler installed successfully")
        return True
    except Exception as e:
        logger.error(f"Error installing Solidity compiler: {e}")
        return False

def compile_contract(contract_file='contracts/AratroCrop.sol'):
    """Compile the Solidity contract."""
    try:
        with open(contract_file, 'r') as file:
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

def connect_to_blockchain():
    """Connect to the blockchain network."""
    # Use Ganache for local development
    ganache_url = os.environ.get('BLOCKCHAIN_URL', 'http://127.0.0.1:7545')
    
    try:
        w3 = Web3(Web3.HTTPProvider(ganache_url))
        # Add middleware for compatibility with PoA chains like Ganache
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Check connection
        try:
            # Try to get the block number to check connection
            block_number = w3.eth.block_number
            logger.info(f"Connected to blockchain at {ganache_url}, current block: {block_number}")
            # Set default account
            account = w3.eth.accounts[0]
            logger.info(f"Using account: {account}")
            return w3, account
        except Exception as e:
            logger.error(f"Failed to connect to blockchain at {ganache_url}: {e}")
            return None, None
    except Exception as e:
        logger.error(f"Error connecting to blockchain: {e}")
        return None, None

def deploy_contract(w3, account, abi, bytecode):
    """Deploy the contract to the blockchain."""
    try:
        # Create contract
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Get private key from environment
        private_key = os.environ.get('PRIVATE_KEY')
        
        # If private key is not set, use a default one for development
        if not private_key or private_key == '0x0000000000000000000000000000000000000000000000000000000000000000':
            logger.warning("Private key not set in environment. Using default account without signing.")
            # Build transaction
            tx_hash = w3.eth.send_transaction({
                'from': account,
                'gas': 5000000,
                'gasPrice': to_wei('50', 'gwei'),
                'data': bytecode
            })
        else:
            # Build transaction
            transaction = Contract.constructor().build_transaction({
                'from': account,
                'nonce': w3.eth.get_transaction_count(account),
                'gas': 5000000,
                'gasPrice': to_wei('50', 'gwei')
            })
            
            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        
        logger.info(f"Contract deployed at address: {contract_address}")
        
        # Save ABI to file for future use
        with open('contract_abi.json', 'w') as f:
            import json
            json.dump(abi, f)
        
        return contract_address
    except Exception as e:
        logger.error(f"Error deploying contract: {e}")
        return None

def update_env_file(contract_address):
    """Update the .env file with the contract address."""
    try:
        # Read the current .env file
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        # Check if CONTRACT_ADDRESS already exists
        contract_address_exists = False
        for i, line in enumerate(env_lines):
            if line.startswith('CONTRACT_ADDRESS='):
                env_lines[i] = f'CONTRACT_ADDRESS={contract_address}\n'
                contract_address_exists = True
                break
        
        # If CONTRACT_ADDRESS doesn't exist, add it
        if not contract_address_exists:
            env_lines.append(f'CONTRACT_ADDRESS={contract_address}\n')
        
        # Write the updated .env file
        with open('.env', 'w') as f:
            f.writelines(env_lines)
        
        logger.info(f"Updated .env file with CONTRACT_ADDRESS={contract_address}")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        return False

def main():
    """Main function to initialize the blockchain environment."""
    # Install Solidity compiler
    if not install_solidity_compiler():
        logger.error("Failed to install Solidity compiler. Exiting.")
        return False
    
    # Compile contract
    abi, bytecode = compile_contract()
    if not abi or not bytecode:
        logger.error("Failed to compile contract. Exiting.")
        return False
    
    # Connect to blockchain
    w3, account = connect_to_blockchain()
    if not w3 or not account:
        logger.error("Failed to connect to blockchain. Exiting.")
        return False
    
    # Deploy contract
    contract_address = deploy_contract(w3, account, abi, bytecode)
    if not contract_address:
        logger.error("Failed to deploy contract. Exiting.")
        return False
    
    # Update .env file
    if not update_env_file(contract_address):
        logger.error("Failed to update .env file. Exiting.")
        return False
    
    logger.info("Blockchain environment initialized successfully!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 