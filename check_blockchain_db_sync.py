from app import app, db
from models import Stock, StockRequest, BlockchainTransaction
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('check_blockchain_db_sync')

def check_blockchain_db_sync():
    """Check if blockchain transactions are being properly recorded in the database."""
    with app.app_context():
        print("Checking blockchain-database synchronization...")
        
        # Check BlockchainTransaction table
        transactions = BlockchainTransaction.query.all()
        print(f"\nTotal blockchain transactions in database: {len(transactions)}")
        
        if transactions:
            print("\nLast 5 blockchain transactions:")
            for tx in transactions[-5:]:
                print(f"ID: {tx.id}")
                print(f"TX Hash: {tx.tx_hash}")
                print(f"TX Type: {tx.tx_type}")
                print(f"Entity Type: {tx.entity_type}")
                print(f"Entity ID: {tx.entity_id}")
                print(f"Blockchain ID: {tx.blockchain_id}")
                print(f"Status: {tx.status}")
                print(f"Created At: {tx.created_at}")
                print(f"Confirmed At: {tx.confirmed_at}")
                print("---")
        else:
            print("No blockchain transactions found in database.")
        
        # Check Stock table for blockchain IDs
        stocks = Stock.query.filter(Stock.blockchain_id.isnot(None)).all()
        print(f"\nStocks with blockchain IDs: {len(stocks)}")
        
        if stocks:
            print("\nLast 5 stocks with blockchain IDs:")
            for stock in stocks[-5:]:
                print(f"ID: {stock.id}")
                print(f"Type: {stock.type}")
                print(f"Quantity: {stock.quantity}")
                print(f"Status: {stock.status}")
                print(f"Blockchain ID: {stock.blockchain_id}")
                print(f"Blockchain TX Hash: {stock.blockchain_tx_hash}")
                print(f"Created At: {stock.created_at}")
                print("---")
        else:
            print("No stocks with blockchain IDs found in database.")
        
        # Check StockRequest table for blockchain IDs
        requests = StockRequest.query.filter(StockRequest.blockchain_id.isnot(None)).all()
        print(f"\nStock requests with blockchain IDs: {len(requests)}")
        
        if requests:
            print("\nLast 5 stock requests with blockchain IDs:")
            for request in requests[-5:]:
                print(f"ID: {request.id}")
                print(f"From: {request.from_id}")
                print(f"To: {request.to_id}")
                print(f"Stock ID: {request.stock_id}")
                print(f"Status: {request.status}")
                print(f"Blockchain ID: {request.blockchain_id}")
                print(f"Blockchain TX Hash: {request.blockchain_tx_hash}")
                print(f"Created At: {request.created_at}")
                print("---")
        else:
            print("No stock requests with blockchain IDs found in database.")
        
        # Check for stocks without blockchain IDs
        stocks_no_blockchain = Stock.query.filter(Stock.blockchain_id.is_(None)).all()
        print(f"\nStocks without blockchain IDs: {len(stocks_no_blockchain)}")
        
        if stocks_no_blockchain:
            print("\nLast 5 stocks without blockchain IDs:")
            for stock in stocks_no_blockchain[-5:]:
                print(f"ID: {stock.id}")
                print(f"Type: {stock.type}")
                print(f"Quantity: {stock.quantity}")
                print(f"Status: {stock.status}")
                print(f"Created At: {stock.created_at}")
                print("---")
        
        # Check for stock requests without blockchain IDs
        requests_no_blockchain = StockRequest.query.filter(StockRequest.blockchain_id.is_(None)).all()
        print(f"\nStock requests without blockchain IDs: {len(requests_no_blockchain)}")
        
        if requests_no_blockchain:
            print("\nLast 5 stock requests without blockchain IDs:")
            for request in requests_no_blockchain[-5:]:
                print(f"ID: {request.id}")
                print(f"From: {request.from_id}")
                print(f"To: {request.to_id}")
                print(f"Stock ID: {request.stock_id}")
                print(f"Status: {request.status}")
                print(f"Created At: {request.created_at}")
                print("---")

if __name__ == "__main__":
    check_blockchain_db_sync() 