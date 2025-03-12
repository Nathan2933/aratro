from app import app, db
from models import Stock, StockRequest, Farmer, Warehouse, BlockchainTransaction
from blockchain import BlockchainManager
import logging
from dotenv import load_dotenv
import os
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('register_existing_stocks')

# Load environment variables
load_dotenv()

def register_existing_stocks():
    """Register existing stocks and stock requests on the blockchain."""
    with app.app_context():
        # Initialize blockchain manager
        blockchain_manager = BlockchainManager()
        
        # Get stocks without blockchain IDs
        stocks_without_blockchain = Stock.query.filter(Stock.blockchain_id.is_(None)).all()
        print(f"Found {len(stocks_without_blockchain)} stocks without blockchain IDs")
        
        for stock in stocks_without_blockchain:
            try:
                # Get the farmer who owns this stock
                farmer = Farmer.query.get(stock.farmer_id)
                if not farmer or not farmer.eth_address:
                    print(f"Farmer {stock.farmer_id} not found or has no Ethereum address. Skipping stock {stock.id}")
                    continue
                
                # Get the warehouse for this stock
                warehouse = Warehouse.query.get(stock.warehouse_id)
                if not warehouse or not warehouse.eth_address:
                    print(f"Warehouse {stock.warehouse_id} not found or has no Ethereum address. Skipping stock {stock.id}")
                    continue
                
                print(f"Registering stock {stock.id} ({stock.type}, {stock.quantity}) for farmer {farmer.name}")
                
                # Convert quantity from tons to kg (blockchain uses kg)
                quantity_kg = int(stock.quantity * 1000)
                requested_quantity_kg = int(stock.quantity * 1000)  # Using same value for requested quantity
                
                # Register stock on blockchain
                result = blockchain_manager.create_stock(
                    stock.type,
                    quantity_kg,
                    requested_quantity_kg,
                    farmer.eth_address,
                    warehouse.eth_address
                )
                
                if not result:
                    print(f"Failed to register stock {stock.id} on blockchain")
                    continue
                
                # Extract blockchain ID and transaction hash
                blockchain_id = result.get('blockchain_id')
                tx_hash = result.get('tx_hash')
                
                if not blockchain_id or not tx_hash:
                    print(f"Failed to get blockchain ID or transaction hash for stock {stock.id}")
                    continue
                
                # Update stock with blockchain ID
                stock.blockchain_id = blockchain_id
                
                # Create blockchain transaction record
                transaction = BlockchainTransaction(
                    tx_hash=tx_hash,
                    tx_type='create_stock',
                    entity_type='stock',
                    entity_id=stock.id,
                    blockchain_id=blockchain_id,
                    status='confirmed',
                    confirmed_at=datetime.utcnow(),
                    data=f"Stock {stock.id} registered on blockchain with ID {blockchain_id}"
                )
                db.session.add(transaction)
                
                print(f"Successfully registered stock {stock.id} with blockchain ID {blockchain_id}")
                
                # Commit after each successful registration
                db.session.commit()
                
                # Sleep to avoid overwhelming the blockchain
                time.sleep(1)
                
            except Exception as e:
                db.session.rollback()
                print(f"Error registering stock {stock.id}: {e}")
        
        # Get stock requests without blockchain IDs
        requests_without_blockchain = StockRequest.query.filter(StockRequest.blockchain_id.is_(None)).all()
        print(f"Found {len(requests_without_blockchain)} stock requests without blockchain IDs")
        
        for request in requests_without_blockchain:
            try:
                # Get the stock associated with this request
                stock = Stock.query.get(request.stock_id)
                if not stock or not stock.blockchain_id:
                    print(f"Stock {request.stock_id} not found or has no blockchain ID. Skipping request {request.id}")
                    continue
                
                # Get the sender (farmer)
                sender = Farmer.query.get(request.from_id)
                if not sender or not sender.eth_address:
                    print(f"Sender {request.from_id} not found or has no Ethereum address. Skipping request {request.id}")
                    continue
                
                # Get the receiver (warehouse)
                receiver = Warehouse.query.get(request.to_id)
                if not receiver or not receiver.eth_address:
                    print(f"Receiver {request.to_id} not found or has no Ethereum address. Skipping request {request.id}")
                    continue
                
                print(f"Registering stock request {request.id} from {sender.name} to {receiver.name} for stock {stock.id}")
                
                # Register stock request on blockchain
                result = blockchain_manager.create_stock_request(
                    sender.eth_address,
                    receiver.eth_address,
                    int(stock.blockchain_id)
                )
                
                if not result:
                    print(f"Failed to register stock request {request.id} on blockchain")
                    continue
                
                # Extract blockchain ID and transaction hash
                blockchain_id = result.get('blockchain_id')
                tx_hash = result.get('tx_hash')
                
                if not blockchain_id or not tx_hash:
                    print(f"Failed to get blockchain ID or transaction hash for stock request {request.id}")
                    continue
                
                # Update stock request with blockchain ID
                request.blockchain_id = blockchain_id
                
                # Create blockchain transaction record
                transaction = BlockchainTransaction(
                    tx_hash=tx_hash,
                    tx_type='create_stock_request',
                    entity_type='stock_request',
                    entity_id=request.id,
                    blockchain_id=blockchain_id,
                    status='confirmed',
                    confirmed_at=datetime.utcnow(),
                    data=f"Stock request {request.id} registered on blockchain with ID {blockchain_id}"
                )
                db.session.add(transaction)
                
                print(f"Successfully registered stock request {request.id} with blockchain ID {blockchain_id}")
                
                # Commit after each successful registration
                db.session.commit()
                
                # Sleep to avoid overwhelming the blockchain
                time.sleep(1)
                
            except Exception as e:
                db.session.rollback()
                print(f"Error registering stock request {request.id}: {e}")
        
        print("Finished registering existing stocks and stock requests")

if __name__ == "__main__":
    register_existing_stocks() 