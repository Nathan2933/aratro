from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Stock, StockRequest, WarehouseRequest, RationStockRequest, BlockchainTransaction, Farmer, Warehouse, RationShop
from blockchain import blockchain_manager, init_blockchain, BlockchainManager
from web3 import Web3
import json
from datetime import datetime, timedelta
import logging
import traceback
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('blockchain_routes')

# Create blueprint
blockchain = Blueprint('blockchain', __name__, url_prefix='/blockchain')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize blockchain manager
if blockchain_manager is None:
    logger.info("Initializing blockchain manager in blockchain_routes")
    blockchain_manager = init_blockchain()
    if blockchain_manager:
        logger.info(f"Blockchain manager initialized successfully. Connected to {blockchain_manager.w3.provider.endpoint_uri}")
        logger.info(f"Contract address: {blockchain_manager.contract_address}")
    else:
        logger.error("Failed to initialize blockchain manager")

@blockchain.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Blockchain dashboard page - Admin only."""
    # Add debug logging
    start_time = datetime.utcnow()
    logger.info("Accessing blockchain dashboard")
    
    # Check blockchain manager initialization
    logger.info(f"Blockchain manager exists: {blockchain_manager is not None}")
    if blockchain_manager:
        logger.info(f"Blockchain manager has web3: {hasattr(blockchain_manager, 'w3')}")
        if hasattr(blockchain_manager, 'w3'):
            logger.info(f"Web3 connection status: {blockchain_manager.w3.isConnected()}")
            logger.info(f"Contract address: {blockchain_manager.contract_address}")
    else:
        logger.error("Blockchain manager is not initialized")
        flash("Error: Blockchain manager is not initialized", "error")
        return render_template('blockchain/dashboard.html',
                             contract_address='Not deployed',
                             total_stocks=0,
                             total_requests=0,
                             total_ration_requests=0,
                             pending_transactions=0,
                             confirmed_transactions=0,
                             blocks=[],
                             transactions=[],
                             stocks=[],
                             stock_requests=[],
                             ration_stock_requests=[])
    
    # Use a single database query with joins instead of multiple queries
    # Get blockchain transactions - limit to 20 instead of 50 for faster loading
    transactions = BlockchainTransaction.query.order_by(BlockchainTransaction.created_at.desc()).limit(20).all()
    logger.info(f"Found {len(transactions)} blockchain transactions - Query time: {(datetime.utcnow() - start_time).total_seconds():.2f}s")
    
    # Format transactions for display
    formatted_transactions = []
    for tx in transactions:
        status_color = {
            'pending': 'warning',
            'confirmed': 'success',
            'failed': 'danger'
        }.get(tx.status, 'info')
        
        formatted_transactions.append({
            'id': tx.id,
            'tx_hash': tx.tx_hash,
            'tx_type': tx.tx_type,
            'entity_type': tx.entity_type,
            'entity_id': tx.entity_id,
            'status': tx.status,
            'status_color': status_color,
            'created_at': tx.created_at
        })
    
    # Get recent stocks with blockchain data - limit to 10 instead of 20
    # Use a join to get farmer and warehouse data in a single query
    stocks_query_time = datetime.utcnow()
    stocks = db.session.query(Stock, Farmer, Warehouse)\
        .join(Farmer, Stock.farmer_id == Farmer.id)\
        .join(Warehouse, Stock.warehouse_id == Warehouse.id)\
        .filter(Stock.blockchain_id.isnot(None))\
        .order_by(Stock.created_at.desc())\
        .limit(10).all()
    logger.info(f"Found {len(stocks)} stocks with blockchain data - Query time: {(datetime.utcnow() - stocks_query_time).total_seconds():.2f}s")
    
    # Format stocks for display
    formatted_stocks = []
    for stock, farmer, warehouse in stocks:
        status_color = {
            'pending': 'warning',
            'stored': 'success',
            'rejected': 'danger'
        }.get(stock.status, 'secondary')
        
        formatted_stocks.append({
            'id': stock.id,
            'blockchain_id': stock.blockchain_id,
            'farmer_name': farmer.name if farmer else 'Unknown',
            'warehouse_name': warehouse.name if warehouse else 'Unknown',
            'type': stock.type,
            'quantity': stock.quantity,
            'status': stock.status,
            'status_color': status_color,
            'created_at': stock.created_at
        })
    
    # Get stock requests with blockchain data - limit to 10
    requests_query_time = datetime.utcnow()
    stock_requests = db.session.query(StockRequest, Farmer, Warehouse)\
        .join(Farmer, StockRequest.from_id == Farmer.id)\
        .join(Warehouse, StockRequest.to_id == Warehouse.id)\
        .filter(StockRequest.blockchain_id.isnot(None))\
        .order_by(StockRequest.created_at.desc())\
        .limit(10).all()
    logger.info(f"Found {len(stock_requests)} stock requests with blockchain data - Query time: {(datetime.utcnow() - requests_query_time).total_seconds():.2f}s")
    
    # Format stock requests for display
    formatted_requests = []
    for request, farmer, warehouse in stock_requests:
        status_color = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }.get(request.status, 'secondary')
        
        formatted_requests.append({
            'id': request.id,
            'blockchain_id': request.blockchain_id,
            'farmer_name': farmer.name if farmer else 'Unknown',
            'warehouse_name': warehouse.name if warehouse else 'Unknown',
            'status': request.status,
            'status_color': status_color,
            'created_at': request.created_at
        })
    
    # Get ration stock requests with blockchain data - limit to 10
    ration_requests_query_time = datetime.utcnow()
    ration_stock_requests = db.session.query(RationStockRequest, RationShop, Warehouse)\
        .join(RationShop, RationStockRequest.ration_shop_id == RationShop.id)\
        .join(Warehouse, RationStockRequest.warehouse_id == Warehouse.id)\
        .filter(RationStockRequest.blockchain_id.isnot(None))\
        .order_by(RationStockRequest.created_at.desc())\
        .limit(10).all()
    logger.info(f"Found {len(ration_stock_requests)} ration stock requests with blockchain data - Query time: {(datetime.utcnow() - ration_requests_query_time).total_seconds():.2f}s")
    
    # Format ration stock requests for display
    formatted_ration_requests = []
    for request, ration_shop, warehouse in ration_stock_requests:
        status_color = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'canceled': 'secondary'
        }.get(request.status, 'secondary')
        
        formatted_ration_requests.append({
            'id': request.id,
            'blockchain_id': request.blockchain_id,
            'ration_shop_name': ration_shop.name if ration_shop else 'Unknown',
            'warehouse_name': warehouse.name if warehouse else 'Unknown',
            'stock_type': request.stock_type,
            'quantity': request.quantity,
            'status': request.status,
            'status_color': status_color,
            'created_at': request.created_at
        })
    
    # Get blockchain statistics
    blockchain_query_time = datetime.utcnow()
    if blockchain_manager and blockchain_manager.w3 and blockchain_manager.w3.isConnected():
        try:
            logger.info("Retrieving blockchain statistics...")
            total_stocks = blockchain_manager.get_total_stocks()
            logger.info(f"Total stocks retrieved: {total_stocks}")
            total_requests = blockchain_manager.get_total_stock_requests()
            logger.info(f"Total requests retrieved: {total_requests}")
            total_ration_requests = blockchain_manager.get_total_ration_stock_requests()
            logger.info(f"Total ration requests retrieved: {total_ration_requests}")
            
            # Get transaction counts
            pending_transactions = BlockchainTransaction.query.filter_by(status='pending').count()
            confirmed_transactions = BlockchainTransaction.query.filter_by(status='confirmed').count()
            logger.info(f"Transaction counts - Pending: {pending_transactions}, Confirmed: {confirmed_transactions}")
            
            # Get recent blocks
            current_block = blockchain_manager.w3.eth.block_number
            blocks = []
            for block_number in range(max(0, current_block - 4), current_block + 1):
                block = blockchain_manager.w3.eth.get_block(block_number)
                blocks.append({
                    'number': block_number,
                    'hash': block['hash'].hex(),
                    'timestamp': datetime.fromtimestamp(block['timestamp']),
                    'transactions': len(block['transactions'])
                })
            blocks.reverse()  # Show newest blocks first
            
            logger.info(f"Blockchain stats: stocks={total_stocks}, requests={total_requests}, ration_requests={total_ration_requests}")
        except Exception as e:
            logger.error(f"Error getting blockchain statistics: {e}")
            total_stocks = 0
            total_requests = 0
            total_ration_requests = 0
            pending_transactions = 0
            confirmed_transactions = 0
            blocks = []
    else:
        logger.warning("Blockchain manager not initialized or not connected")
        total_stocks = 0
        total_requests = 0
        total_ration_requests = 0
        pending_transactions = 0
        confirmed_transactions = 0
        blocks = []
    
    logger.info(f"Blockchain queries completed - Query time: {(datetime.utcnow() - blockchain_query_time).total_seconds():.2f}s")
    logger.info(f"Total dashboard loading time: {(datetime.utcnow() - start_time).total_seconds():.2f}s")
    
    return render_template('blockchain/dashboard.html',
                          contract_address=blockchain_manager.contract_address if blockchain_manager else 'Not deployed',
                          total_stocks=total_stocks,
                          total_requests=total_requests,
                          total_ration_requests=total_ration_requests,
                          pending_transactions=pending_transactions,
                          confirmed_transactions=confirmed_transactions,
                          blocks=blocks,
                          transactions=formatted_transactions,
                          stocks=formatted_stocks,
                          stock_requests=formatted_requests,
                          ration_stock_requests=formatted_ration_requests)

@blockchain.route('/stock/<int:stock_id>')
@login_required
def view_stock(stock_id):
    """View stock details on the blockchain."""
    start_time = datetime.utcnow()
    logger.info(f"Viewing stock details for stock {stock_id}")
    
    # Get stock from database with a single query that includes farmer and warehouse
    stock_query_time = datetime.utcnow()
    stock_data = db.session.query(Stock, Farmer, Warehouse)\
        .join(Farmer, Stock.farmer_id == Farmer.id)\
        .join(Warehouse, Stock.warehouse_id == Warehouse.id)\
        .filter(Stock.id == stock_id).first_or_404()
    
    stock, farmer, warehouse = stock_data
    logger.info(f"Stock query completed - Query time: {(datetime.utcnow() - stock_query_time).total_seconds():.2f}s")
    
    # Get transactions related to this stock - limit to 10 for faster loading
    tx_query_time = datetime.utcnow()
    transactions = BlockchainTransaction.query.filter_by(
        entity_type='stock',
        entity_id=stock.id
    ).order_by(BlockchainTransaction.created_at.desc()).limit(10).all()
    logger.info(f"Found {len(transactions)} transactions - Query time: {(datetime.utcnow() - tx_query_time).total_seconds():.2f}s")
    
    # Format transactions for display
    formatted_transactions = []
    for tx in transactions:
        status_color = {
            'pending': 'warning',
            'confirmed': 'success',
            'failed': 'danger'
        }.get(tx.status, 'info')
        
        formatted_transactions.append({
            'id': tx.id,
            'tx_hash': tx.tx_hash,
            'tx_type': tx.tx_type,
            'status': tx.status,
            'status_color': status_color,
            'created_at': tx.created_at
        })
    
    # Format stock data for display
    formatted_stock = {
        'id': stock.id,
        'blockchain_id': stock.blockchain_id,
        'blockchain_tx_hash': stock.blockchain_tx_hash,
        'crop_type': stock.type,
        'quantity': stock.quantity,
        'requested_quantity': stock.requested_quantity,
        'status': stock.status,
        'created_at': stock.created_at,
        'updated_at': stock.updated_at,
        'farmer_name': farmer.name if farmer else 'Unknown',
        'farmer_address': farmer.eth_address if farmer else 'Unknown',
        'warehouse_name': warehouse.name if warehouse else 'Unknown',
        'warehouse_address': warehouse.eth_address if warehouse else 'Unknown'
    }
    
    # Prepare data for comparison
    db_data = {
        'id': stock.id,
        'type': stock.type,
        'quantity': stock.quantity,
        'requested_quantity': stock.requested_quantity,
        'status': stock.status,
        'farmer_id': stock.farmer_id,
        'warehouse_id': stock.warehouse_id
    }
    
    # Get blockchain data if available - do this after database queries
    blockchain_query_time = datetime.utcnow()
    blockchain_data = None
    is_verified = False
    
    if stock.blockchain_id and blockchain_manager:
        try:
            blockchain_data = blockchain_manager.get_stock(stock.blockchain_id)
            
            # Verify that blockchain data matches database data
            is_verified = (
                blockchain_data['crop_type'] == stock.type and
                abs(blockchain_data['quantity'] - stock.quantity) < 0.001 and
                blockchain_data['status'] == stock.status
            )
        except Exception as e:
            logger.error(f"Error getting blockchain data for stock {stock_id}: {e}")
    
    logger.info(f"Blockchain query completed - Query time: {(datetime.utcnow() - blockchain_query_time).total_seconds():.2f}s")
    logger.info(f"Total stock view loading time: {(datetime.utcnow() - start_time).total_seconds():.2f}s")
    
    return render_template('blockchain/stock_details.html',
                          stock=formatted_stock,
                          transactions=formatted_transactions,
                          blockchain_data=blockchain_data,
                          db_data=db_data,
                          is_verified=is_verified)

@blockchain.route('/api/stock/<int:stock_id>')
@login_required
def api_stock(stock_id):
    """API endpoint for stock blockchain data."""
    # Get stock from database
    stock = Stock.query.get_or_404(stock_id)
    
    # Get blockchain data if available
    blockchain_data = None
    
    if stock.blockchain_id and blockchain_manager:
        try:
            blockchain_data = blockchain_manager.get_stock(stock.blockchain_id)
        except Exception as e:
            logger.error(f"Error getting blockchain data for stock {stock_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Return JSON response
    return jsonify({
        'stock': {
            'id': stock.id,
            'blockchain_id': stock.blockchain_id,
            'blockchain_tx_hash': stock.blockchain_tx_hash,
            'type': stock.type,
            'quantity': stock.quantity,
            'requested_quantity': stock.requested_quantity,
            'status': stock.status,
            'farmer_id': stock.farmer_id,
            'warehouse_id': stock.warehouse_id,
            'created_at': stock.created_at.isoformat(),
            'updated_at': stock.updated_at.isoformat()
        },
        'blockchain_data': blockchain_data
    })

@blockchain.route('/api/transactions')
@login_required
def api_transactions():
    """API endpoint for blockchain transactions."""
    # Get query parameters
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')
    
    # Build query
    query = BlockchainTransaction.query
    
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    
    # Get transactions
    transactions = query.order_by(BlockchainTransaction.created_at.desc()).all()
    
    # Format transactions for JSON response
    formatted_transactions = []
    for tx in transactions:
        formatted_transactions.append({
            'id': tx.id,
            'tx_hash': tx.tx_hash,
            'tx_type': tx.tx_type,
            'entity_type': tx.entity_type,
            'entity_id': tx.entity_id,
            'blockchain_id': tx.blockchain_id,
            'status': tx.status,
            'created_at': tx.created_at.isoformat(),
            'confirmed_at': tx.confirmed_at.isoformat() if tx.confirmed_at else None,
            'data': json.loads(tx.data) if tx.data else None
        })
    
    # Return JSON response
    return jsonify({'transactions': formatted_transactions})

@blockchain.route('/api/blocks')
@login_required
def api_blocks():
    """API endpoint for blockchain blocks."""
    blocks = []
    if blockchain_manager and blockchain_manager.w3:
        try:
            # Get the latest block number
            latest_block = blockchain_manager.w3.eth.block_number
            
            # Get the last 10 blocks
            for i in range(min(10, latest_block + 1)):
                block_number = latest_block - i
                block = blockchain_manager.w3.eth.get_block(block_number)
                
                blocks.append({
                    'number': block_number,
                    'hash': block['hash'].hex(),
                    'timestamp': datetime.fromtimestamp(block['timestamp']).isoformat(),
                    'transaction_count': len(block['transactions']),
                    'transactions': [tx.hex() for tx in block['transactions']]
                })
        except Exception as e:
            logger.error(f"Error getting blockchain blocks: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Return JSON response
    return jsonify({'blocks': blocks})

@blockchain.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    """View stock request details on the blockchain."""
    start_time = datetime.utcnow()
    logger.info(f"Viewing request details for request {request_id}")
    
    # Get request from database with a single query that includes farmer, warehouse, and stock
    query_time = datetime.utcnow()
    request_data = db.session.query(StockRequest, Farmer, Warehouse, Stock)\
        .join(Farmer, StockRequest.from_id == Farmer.id)\
        .join(Warehouse, StockRequest.to_id == Warehouse.id)\
        .join(Stock, StockRequest.stock_id == Stock.id)\
        .filter(StockRequest.id == request_id).first_or_404()
    
    stock_request, farmer, warehouse, stock = request_data
    logger.info(f"Request query completed - Query time: {(datetime.utcnow() - query_time).total_seconds():.2f}s")
    
    # Get transactions related to this request - limit to 10 for faster loading
    tx_query_time = datetime.utcnow()
    transactions = BlockchainTransaction.query.filter_by(
        entity_type='stock_request',
        entity_id=stock_request.id
    ).order_by(BlockchainTransaction.created_at.desc()).limit(10).all()
    logger.info(f"Found {len(transactions)} transactions - Query time: {(datetime.utcnow() - tx_query_time).total_seconds():.2f}s")
    
    # Format transactions for display
    formatted_transactions = []
    for tx in transactions:
        status_color = {
            'pending': 'warning',
            'confirmed': 'success',
            'failed': 'danger'
        }.get(tx.status, 'info')
        
        formatted_transactions.append({
            'id': tx.id,
            'tx_hash': tx.tx_hash,
            'tx_type': tx.tx_type,
            'status': tx.status,
            'status_color': status_color,
            'created_at': tx.created_at
        })
    
    # Format request data for display
    formatted_request = {
        'id': stock_request.id,
        'blockchain_id': stock_request.blockchain_id,
        'blockchain_tx_hash': stock_request.blockchain_tx_hash,
        'stock_id': stock_request.stock_id,
        'stock_type': stock.type if stock else 'Unknown',
        'stock_quantity': stock.quantity if stock else 0,
        'status': stock_request.status,
        'request_date': stock_request.request_date,
        'created_at': stock_request.created_at,
        'updated_at': stock_request.updated_at,
        'farmer_name': farmer.name if farmer else 'Unknown',
        'farmer_address': farmer.eth_address if farmer else 'Unknown',
        'warehouse_name': warehouse.name if warehouse else 'Unknown',
        'warehouse_address': warehouse.eth_address if warehouse else 'Unknown'
    }
    
    # Prepare data for comparison
    db_data = {
        'id': stock_request.id,
        'from_id': stock_request.from_id,
        'to_id': stock_request.to_id,
        'stock_id': stock_request.stock_id,
        'status': stock_request.status,
        'request_date': stock_request.request_date.isoformat() if stock_request.request_date else None
    }
    
    # Get blockchain data if available - do this after database queries
    blockchain_query_time = datetime.utcnow()
    blockchain_data = None
    is_verified = False
    
    if stock_request.blockchain_id and blockchain_manager:
        try:
            # Call the getStockRequest function on the smart contract
            blockchain_data = blockchain_manager.get_stock_request(stock_request.blockchain_id)
            
            # Verify that blockchain data matches database data
            is_verified = (
                blockchain_data['from'] == farmer.eth_address.lower() and
                blockchain_data['to'] == warehouse.eth_address.lower() and
                int(blockchain_data['status']) == {'pending': 0, 'approved': 1, 'rejected': 2}.get(stock_request.status, 0)
            )
        except Exception as e:
            logger.error(f"Error getting blockchain data for request {request_id}: {e}")
    
    logger.info(f"Blockchain query completed - Query time: {(datetime.utcnow() - blockchain_query_time).total_seconds():.2f}s")
    logger.info(f"Total request view loading time: {(datetime.utcnow() - start_time).total_seconds():.2f}s")
    
    return render_template('blockchain/request_details.html',
                          request=formatted_request,
                          transactions=formatted_transactions,
                          blockchain_data=blockchain_data,
                          db_data=db_data,
                          is_verified=is_verified)

@blockchain.route('/transaction/<tx_hash>')
@login_required
def view_transaction(tx_hash):
    """View transaction details from the local blockchain."""
    start_time = datetime.utcnow()
    logger.info(f"Viewing transaction details for hash {tx_hash}")
    
    # Initialize variables with default values
    db_tx = None
    entity_details = None
    tx_data = None
    block_data = None
    raw_tx = None
    raw_receipt = None
    blockchain_tx_not_found = True
    debug_info = {
        'blockchain_tx_not_found': True,
        'exception': None,
        'exception_type': None,
        'has_raw_tx': False,
        'has_raw_receipt': False,
        'has_block_data': False,
        'tx_data_keys': [],
        'block_data_keys': []
    }
    
    try:
        # Check if the transaction hash is valid
        if not tx_hash.startswith('0x') or len(tx_hash) != 66 or not all(c in '0123456789abcdefABCDEF' for c in tx_hash[2:]):
            flash(f"Invalid transaction hash format: {tx_hash}", "danger")
            return redirect(url_for('blockchain.dashboard'))
        
        # Get transaction from database first - this is fast
        db_query_time = datetime.utcnow()
        db_tx = BlockchainTransaction.query.filter_by(tx_hash=tx_hash).first()
        logger.info(f"Database query completed - Query time: {(datetime.utcnow() - db_query_time).total_seconds():.2f}s")
        logger.info(f"Database transaction found: {db_tx is not None}")
        
        if db_tx:
            logger.info(f"Transaction details: ID={db_tx.id}, Type={db_tx.tx_type}, Entity={db_tx.entity_type}, EntityID={db_tx.entity_id}, Status={db_tx.status}")
            # Prepare entity details if we have the transaction in our database
            entity_query_time = datetime.utcnow()
            # Get entity details with a single query based on entity type
            if db_tx.entity_type == 'stock':
                entity = Stock.query.get(db_tx.entity_id)
                if entity:
                    entity_details = {
                        'type': entity.type,
                        'quantity': entity.quantity,
                        'status': entity.status,
                        'farmer_id': entity.farmer_id,
                        'warehouse_id': entity.warehouse_id
                    }
                    logger.info(f"Stock entity found: ID={entity.id}, Type={entity.type}, Status={entity.status}")
            elif db_tx.entity_type == 'stock_request':
                entity = StockRequest.query.get(db_tx.entity_id)
                if entity:
                    entity_details = {
                        'from_id': entity.from_id,
                        'to_id': entity.to_id,
                        'stock_id': entity.stock_id,
                        'status': entity.status
                    }
                    logger.info(f"StockRequest entity found: ID={entity.id}, Status={entity.status}")
            
            logger.info(f"Entity query completed - Query time: {(datetime.utcnow() - entity_query_time).total_seconds():.2f}s")
            tx_data = {
                'hash': tx_hash,
                'blockNumber': 'Unknown',
                'from': 'Unknown',
                'to': 'Unknown',
                'value': 0,
                'gasPrice': 0,
                'gas': 0,
                'nonce': 0,
                'input': 'Not available',
                'status': db_tx.status,  # Use the status from the database
                'timestamp': datetime.now(),
                'type': db_tx.tx_type,
                'entity_type': db_tx.entity_type,
                'entity_id': db_tx.entity_id,
                'blockchain_id': db_tx.blockchain_id,
                'db_status': db_tx.status,
                'created_at': db_tx.created_at,
                'confirmed_at': db_tx.confirmed_at,
                'entity_details': entity_details
            }
            
            # Update debug info with transaction data keys
            debug_info['tx_data_keys'] = list(tx_data.keys())
        else:
            logger.warning(f"Transaction {tx_hash} not found in database")
        
        # Get transaction from blockchain - this can be slow
        blockchain_query_time = datetime.utcnow()
        
        try:
            # Initialize blockchain manager
            blockchain_manager = init_blockchain()
            w3 = blockchain_manager.w3  # Access the Web3 instance through the blockchain manager
            
            # Check blockchain connection by trying to get the block number
            try:
                block_number = w3.eth.block_number
                logger.info(f"Blockchain connection successful. Current block number: {block_number}")
            except Exception as e:
                logger.error(f"Failed to connect to blockchain: {e}")
                debug_info['exception'] = str(e)
                debug_info['exception_type'] = str(type(e))
                raise Exception(f"Failed to connect to blockchain: {e}")
            
            # Get transaction from blockchain
            logger.info(f"Attempting to get transaction from blockchain: {tx_hash}")
            raw_tx = w3.eth.get_transaction(tx_hash)
            logger.info(f"Transaction found on blockchain: BlockNumber={raw_tx.get('blockNumber')}, From={raw_tx.get('from')}, To={raw_tx.get('to')}")
            
            # Get transaction receipt
            raw_receipt = w3.eth.get_transaction_receipt(tx_hash)
            logger.info(f"Transaction receipt found: Status={raw_receipt.get('status')}, BlockNumber={raw_receipt.get('blockNumber')}")
            
            # Format transaction data for display
            tx_data = tx_data or {}  # Use existing tx_data if available, otherwise create new dict
            
            # Use w3.fromWei instead of Web3.from_wei
            value_wei = raw_tx.get('value', 0)
            gas_price_wei = raw_tx.get('gasPrice', 0)
            
            # Convert wei to ether and gwei manually if fromWei is not available
            try:
                value_ether = w3.fromWei(value_wei, 'ether')
                gas_price_gwei = w3.fromWei(gas_price_wei, 'gwei')
            except AttributeError:
                # Manual conversion as fallback
                value_ether = float(value_wei) / 1e18  # 1 ether = 10^18 wei
                gas_price_gwei = float(gas_price_wei) / 1e9  # 1 gwei = 10^9 wei
                logger.info(f"Using manual conversion for wei values: value_wei={value_wei}, gas_price_wei={gas_price_wei}")
            
            tx_data.update({
                'hash': tx_hash,
                'blockNumber': raw_tx.get('blockNumber'),
                'from': raw_tx.get('from'),
                'to': raw_tx.get('to'),
                'value': value_ether,
                'gasPrice': gas_price_gwei,
                'gas': raw_tx.get('gas'),
                'nonce': raw_tx.get('nonce'),
                'input': raw_tx.get('input'),
                'status': 'Success' if raw_receipt.get('status') == 1 else 'Failed',
                'timestamp': datetime.now(),  # Ganache doesn't provide timestamp, using current time
            })
            
            # Get block details
            logger.info(f"Getting block details for block number: {raw_tx.get('blockNumber')}")
            block = w3.eth.get_block(raw_tx.get('blockNumber'))
            block_data = {
                'number': block.get('number'),
                'hash': block.get('hash').hex(),
                'parentHash': block.get('parentHash').hex(),
                'timestamp': block.get('timestamp', 0),
                'transactions': len(block.get('transactions', [])),
                'gasUsed': block.get('gasUsed', 0),
                'gasLimit': block.get('gasLimit', 0)
            }
            logger.info(f"Block details found: Number={block_data['number']}, Hash={block_data['hash'][:10]}...")
            
            # Mark blockchain transaction as found
            blockchain_tx_not_found = False
            debug_info['blockchain_tx_not_found'] = False
            debug_info['has_raw_tx'] = True
            debug_info['has_raw_receipt'] = True
            debug_info['has_block_data'] = True
            debug_info['tx_data_keys'] = list(tx_data.keys())
            debug_info['block_data_keys'] = list(block_data.keys())
            
            logger.info(f"Blockchain query completed - Query time: {(datetime.utcnow() - blockchain_query_time).total_seconds():.2f}s")
            
            # If we have a database transaction, update its status if needed
            if db_tx and db_tx.status == 'pending':
                db_tx.status = 'confirmed'
                db_tx.confirmed_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Updated transaction {tx_hash} status to confirmed in database")
            
        except Exception as e:
            logger.error(f"Error getting transaction from blockchain: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            
            debug_info['exception'] = str(e)
            debug_info['exception_type'] = str(type(e))
            
            # Create placeholder block data if not already set
            if not block_data:
                block_data = {
                    'number': 'Unknown',
                    'hash': 'Unknown',
                    'parentHash': 'Unknown',
                    'timestamp': 0,
                    'transactions': 0,
                    'gasUsed': 0,
                    'gasLimit': 0
                }
                debug_info['has_block_data'] = True
                debug_info['block_data_keys'] = list(block_data.keys())
            
            # If we have the transaction in our database, show a warning
            if db_tx:
                logger.warning(f"Transaction {tx_hash} exists in database but not found on blockchain: {e}")
                
                # If the transaction is pending and has been for more than an hour, mark it as failed
                if db_tx.status == 'pending' and datetime.utcnow() - db_tx.created_at > timedelta(hours=1):
                    db_tx.status = 'failed'
                    db.session.commit()
                    logger.info(f"Updated transaction {tx_hash} status to failed in database")
                    tx_data['status'] = 'Failed (Not found on blockchain)'
                    tx_data['db_status'] = 'failed'
                
                flash("Transaction exists in database but not found on blockchain. This could mean the transaction is still pending, or it failed to be included in a block.", "warning")
            else:
                flash(f"Transaction {tx_hash} not found in database or blockchain: {e}", "danger")
                return redirect(url_for('blockchain.dashboard'))
        
        # Update debug info
        debug_info.update({
            'tx_data_keys': list(tx_data.keys()) if tx_data else [],
            'block_data_keys': list(block_data.keys()) if block_data else [],
            'has_raw_tx': raw_tx is not None,
            'has_raw_receipt': raw_receipt is not None,
            'has_block_data': block_data is not None,
        })
        
        logger.info(f"Total transaction view loading time: {(datetime.utcnow() - start_time).total_seconds():.2f}s")
        logger.info(f"Rendering template with blockchain_tx_not_found={blockchain_tx_not_found}")
        
        # Render the template with all available data
        return render_template(
            'blockchain/transaction_details.html',
            tx=tx_data,
            block=block_data,
            tx_receipt=raw_receipt,
            raw_tx=raw_tx,
            raw_receipt=raw_receipt,
            blockchain_tx_not_found=blockchain_tx_not_found,
            debug_info=debug_info
        )
    
    except Exception as e:
        logger.error(f"Error viewing transaction {tx_hash}: {e}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        
        flash(f"Error viewing transaction: {e}", "danger")
        return redirect(url_for('blockchain.dashboard')) 

@blockchain.route('/ration_stock_request/<int:request_id>')
@login_required
def view_ration_stock_request(request_id):
    """View ration stock request details on the blockchain."""
    start_time = datetime.utcnow()
    logger.info(f"Viewing ration stock request details for request {request_id}")
    
    # Get ration stock request from database with a single query that includes ration shop and warehouse
    request_query_time = datetime.utcnow()
    request_data = db.session.query(RationStockRequest, RationShop, Warehouse)\
        .join(RationShop, RationStockRequest.ration_shop_id == RationShop.id)\
        .join(Warehouse, RationStockRequest.warehouse_id == Warehouse.id)\
        .filter(RationStockRequest.id == request_id).first_or_404()
    
    request, ration_shop, warehouse = request_data
    logger.info(f"Ration stock request query completed - Query time: {(datetime.utcnow() - request_query_time).total_seconds():.2f}s")
    
    # Get transactions related to this request - limit to 10 for faster loading
    tx_query_time = datetime.utcnow()
    transactions = BlockchainTransaction.query.filter_by(
        entity_type='ration_stock_request',
        entity_id=request.id
    ).order_by(BlockchainTransaction.created_at.desc()).limit(10).all()
    logger.info(f"Found {len(transactions)} transactions - Query time: {(datetime.utcnow() - tx_query_time).total_seconds():.2f}s")
    
    # Format transactions for display
    formatted_transactions = []
    for tx in transactions:
        status_color = {
            'pending': 'warning',
            'confirmed': 'success',
            'failed': 'danger'
        }.get(tx.status, 'info')
        
        formatted_transactions.append({
            'id': tx.id,
            'tx_hash': tx.tx_hash,
            'tx_type': tx.tx_type,
            'status': tx.status,
            'status_color': status_color,
            'created_at': tx.created_at,
            'confirmed_at': tx.confirmed_at
        })
    
    # Get blockchain data if available
    blockchain_data = None
    if request.blockchain_id:
        try:
            blockchain_data = blockchain_manager.get_ration_stock_request(request.blockchain_id)
            logger.info(f"Blockchain data: {blockchain_data}")
        except Exception as e:
            logger.error(f"Error getting blockchain data: {e}")
    
    # Format status for display
    status_color = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'canceled': 'secondary'
    }.get(request.status, 'secondary')
    
    logger.info(f"Total view time: {(datetime.utcnow() - start_time).total_seconds():.2f}s")
    
    return render_template('blockchain/ration_stock_request.html',
                          request=request,
                          ration_shop=ration_shop,
                          warehouse=warehouse,
                          transactions=formatted_transactions,
                          blockchain_data=blockchain_data,
                          status_color=status_color)

@blockchain.route('/api/stats')
@login_required
def get_stats():
    """Get blockchain statistics."""
    if blockchain_manager and blockchain_manager.w3 and blockchain_manager.w3.isConnected():
        try:
            total_stocks = blockchain_manager.get_total_stocks()
            total_requests = blockchain_manager.get_total_stock_requests()
            total_ration_requests = blockchain_manager.get_total_ration_stock_requests()
            
            # Get transaction counts
            pending_transactions = BlockchainTransaction.query.filter_by(status='pending').count()
            confirmed_transactions = BlockchainTransaction.query.filter_by(status='confirmed').count()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_stocks': total_stocks,
                    'total_requests': total_requests,
                    'total_ration_requests': total_ration_requests,
                    'pending_transactions': pending_transactions,
                    'confirmed_transactions': confirmed_transactions
                }
            })
        except Exception as e:
            logger.error(f"Error getting blockchain statistics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    else:
        return jsonify({
            'success': False,
            'error': 'Blockchain manager not initialized or not connected'
        }), 503 