#!/usr/bin/env python3
"""
Test script to check if a blockchain node is accessible.
Usage: python test_blockchain_connection.py [blockchain_url]
If blockchain_url is not provided, it will use the BLOCKCHAIN_URL environment variable
or default to http://127.0.0.1:7545
"""

import os
import sys
import requests
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware

def test_http_connection(url):
    """Test if the URL is accessible via HTTP"""
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ HTTP connection to {url} successful!")
        print(f"Status code: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP connection to {url} failed: {e}")
        return False

def test_web3_connection(url):
    """Test if Web3 can connect to the blockchain"""
    try:
        w3 = Web3(Web3.HTTPProvider(url))
        # Add middleware for compatibility with PoA chains like Ganache
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Check connection by trying to get the block number
        try:
            block_number = w3.eth.block_number
            print(f"✅ Web3 connection to {url} successful!")
            print(f"Current block number: {block_number}")
            
            # Get network ID
            network_id = w3.net.version
            print(f"Network ID: {network_id}")
            
            # Get accounts
            accounts = w3.eth.accounts
            print(f"Number of accounts: {len(accounts)}")
            if accounts:
                print(f"First account: {accounts[0]}")
            
            return True
        except Exception as e:
            print(f"❌ Web3 could not connect to {url}: {e}")
            return False
    except Exception as e:
        print(f"❌ Web3 connection to {url} failed: {e}")
        return False

def main():
    # Get blockchain URL from command line or environment variable or use default
    if len(sys.argv) > 1:
        blockchain_url = sys.argv[1]
    else:
        blockchain_url = os.environ.get('BLOCKCHAIN_URL', 'http://127.0.0.1:7545')
    
    print(f"Testing connection to blockchain at: {blockchain_url}")
    print("-" * 50)
    
    # Test HTTP connection
    http_success = test_http_connection(blockchain_url)
    
    print("-" * 50)
    
    # Test Web3 connection
    web3_success = test_web3_connection(blockchain_url)
    
    print("-" * 50)
    
    # Summary
    if http_success and web3_success:
        print("✅ All tests passed! The blockchain is accessible.")
    elif http_success:
        print("⚠️ HTTP connection works but Web3 connection failed.")
        print("This might indicate that the URL is accessible but it's not a valid blockchain node.")
    else:
        print("❌ Connection tests failed. The blockchain is not accessible.")
        print("Please check:")
        print("1. Is the blockchain node running?")
        print("2. Is the URL correct?")
        print("3. Is the blockchain configured to accept connections from other machines?")
        print("4. Are there any firewalls blocking the connection?")

if __name__ == "__main__":
    main() 