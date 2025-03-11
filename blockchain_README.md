# Aratro Blockchain Integration

This document explains how to set up and use the blockchain functionality in the Aratro application.

## Overview

The Aratro application has been enhanced with blockchain functionality to provide transparency, traceability, and immutability for agricultural stock transactions. The blockchain integration allows for:

1. Recording stock creation and status updates on the blockchain
2. Recording stock requests and their status updates on the blockchain
3. Verifying the integrity of stock data by comparing database records with blockchain records
4. Visualizing blockchain transactions and blocks

## Prerequisites

To use the blockchain functionality, you need:

1. [Ganache](https://trufflesuite.com/ganache/) - A personal Ethereum blockchain for local development
2. Python 3.8 or higher
3. The required Python packages (listed in requirements.txt)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Ganache

Download and install Ganache from [https://trufflesuite.com/ganache/](https://trufflesuite.com/ganache/).

Start Ganache and create a new workspace. Make note of the RPC Server URL (usually http://127.0.0.1:7545).

### 3. Configure Environment Variables

Create or update your `.env` file with the following variables:

```
BLOCKCHAIN_URL=http://127.0.0.1:7545
PRIVATE_KEY=<your_private_key>
```

To get a private key from Ganache:
1. Click on the key icon next to any account in Ganache
2. Copy the private key
3. Add it to your `.env` file with the `PRIVATE_KEY` variable

### 4. Initialize the Blockchain Environment

Run the initialization script to compile and deploy the smart contract:

```bash
python init_blockchain.py
```

This will:
1. Install the Solidity compiler
2. Compile the AratroCrop.sol smart contract
3. Deploy the contract to your local Ganache blockchain
4. Save the contract address to your .env file

### 5. Run Database Migrations

Run the blockchain migration script to update your database schema:

```bash
python migrations/blockchain_migration.py
```

This will:
1. Add blockchain-related columns to your database tables
2. Generate Ethereum addresses for existing users, farmers, warehouses, etc.

### 6. Sync Existing Data to Blockchain

If you have existing data that you want to sync to the blockchain:

```bash
python blockchain_integration.py sync_stocks
python blockchain_integration.py sync_requests
```

## Usage

### Accessing the Blockchain Dashboard

The blockchain dashboard is available at `/blockchain/dashboard`. This page shows:

1. Blockchain statistics (total stocks, total requests, etc.)
2. Visualization of recent blocks
3. Recent blockchain transactions
4. Stocks recorded on the blockchain

### Viewing Stock Details

You can view detailed blockchain information for a stock at `/blockchain/stock/<stock_id>`. This page shows:

1. Stock information from the database
2. Blockchain information for the stock
3. Transaction history for the stock
4. Verification status (comparing database and blockchain data)

### API Endpoints

The following API endpoints are available:

- `/blockchain/api/stock/<stock_id>` - Get stock data from both database and blockchain
- `/blockchain/api/transactions` - Get blockchain transactions (can filter by entity type and ID)
- `/blockchain/api/blocks` - Get recent blockchain blocks

### Integration with Existing Processes

The blockchain integration is designed to work alongside the existing stock and request processes. When a stock or request is created or updated, the corresponding blockchain functions are called to record the transaction on the blockchain.

## Smart Contract

The AratroCrop smart contract (located in `contracts/AratroCrop.sol`) provides the following functionality:

1. Creating and tracking stocks
2. Updating stock status
3. Creating and tracking stock requests
4. Updating stock request status
5. Creating and tracking warehouse requests
6. Creating and tracking ration stock requests

## Troubleshooting

### Contract Deployment Issues

If you encounter issues deploying the contract:

1. Make sure Ganache is running
2. Check that your BLOCKCHAIN_URL is correct
3. Ensure your PRIVATE_KEY is valid
4. Check the logs for specific error messages

### Transaction Issues

If blockchain transactions are failing:

1. Check that your contract is deployed correctly
2. Ensure your Ganache instance has enough ETH in the account
3. Check the logs for specific error messages

### Database Issues

If you encounter database issues:

1. Make sure your database migrations have been applied
2. Check that the blockchain-related columns exist in your tables
3. Ensure Ethereum addresses have been generated for users, farmers, warehouses, etc.

## Development

### Adding New Blockchain Functionality

To add new functionality to the blockchain integration:

1. Update the AratroCrop.sol contract with new functions
2. Add corresponding methods to the blockchain.py module
3. Create integration functions in blockchain_integration.py
4. Update the blockchain_routes.py file with new routes if needed

### Testing

To test the blockchain functionality:

1. Make sure Ganache is running
2. Run the initialization script
3. Create test data in the application
4. Verify that the data is correctly recorded on the blockchain

## Security Considerations

In a production environment, consider the following security measures:

1. Use a secure Ethereum node provider instead of Ganache
2. Store private keys securely (not in .env files)
3. Implement proper access controls for blockchain operations
4. Use a production-ready Ethereum network (mainnet or a suitable testnet)
5. Implement transaction signing with user-specific keys rather than a single application key 