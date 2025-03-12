# Blockchain Dashboard Optimization

This document describes the process of resetting the database and optimizing the blockchain dashboard for fast data transfer.

## Overview

The optimization process involves several steps:

1. Resetting the database
2. Resetting blockchain IDs
3. Resetting any aborted transactions
4. Syncing data to the blockchain
5. Optimizing database indexes
6. Optimizing query performance
7. Clearing any stuck pending transactions
8. Running the blockchain transaction checker

## Optimization Scripts

Three scripts have been created to facilitate the optimization process:

### 1. `optimize_blockchain_dashboard.py`

This script performs the following operations:
- Resets the database
- Resets blockchain IDs
- Resets any aborted transactions
- Syncs data to the blockchain

Usage:
```bash
python optimize_blockchain_dashboard.py
```

### 2. `optimize_blockchain_transfer.py`

This script optimizes the blockchain data transfer speed:
- Creates database indexes for faster blockchain data retrieval
- Optimizes database query performance
- Clears any stuck pending transactions
- Runs the blockchain transaction checker

Usage:
```bash
python optimize_blockchain_transfer.py
```

### 3. `reset_and_optimize_blockchain.py`

This is a combined script that runs both optimization scripts in sequence:
- First runs `optimize_blockchain_dashboard.py`
- Then runs `optimize_blockchain_transfer.py`

Usage:
```bash
python reset_and_optimize_blockchain.py
```

## Running the Application

After optimization, run the application with the transaction checker:

```bash
./run_app_with_checker.sh
```

This will start the application and the transaction checker in the background, ensuring that blockchain transactions are processed efficiently.

## Monitoring

To monitor the blockchain dashboard performance:
1. Log in as an admin
2. Navigate to `/blockchain/dashboard`
3. Check the transaction processing times and status

## Troubleshooting

If you encounter issues with the blockchain dashboard:

1. Check the application logs for errors
2. Verify that the blockchain node is running and accessible
3. Run the optimization scripts again if necessary
4. Check for any stuck transactions in the database

## Performance Improvements

The optimization process makes several improvements:

1. **Database Indexes**: Creates indexes on frequently accessed columns for faster queries
2. **Query Optimization**: Updates database statistics for better query planning
3. **Transaction Management**: Clears stuck transactions and ensures proper processing
4. **Background Processing**: Runs the transaction checker in the background for continuous monitoring

These improvements ensure that data is transferred to the blockchain dashboard as fast as possible, providing a responsive and up-to-date view of blockchain activities. 