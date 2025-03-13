#!/usr/bin/env python3
"""
Script to check ration shop Ethereum addresses.
"""
from app import app
from models import db, RationShop, Warehouse
from blockchain import get_eth_address

def main():
    """Main function to check ration shop Ethereum addresses."""
    with app.app_context():
        # Check ration shops
        total_shops = RationShop.query.count()
        shops_with_eth = RationShop.query.filter(RationShop.eth_address != None).count()
        print(f"Ration shops with Ethereum addresses: {shops_with_eth} out of {total_shops}")
        
        # Check warehouses
        total_warehouses = Warehouse.query.count()
        warehouses_with_eth = Warehouse.query.filter(Warehouse.eth_address != None).count()
        print(f"Warehouses with Ethereum addresses: {warehouses_with_eth} out of {total_warehouses}")
        
        # List ration shops without Ethereum addresses
        shops_without_eth = RationShop.query.filter(RationShop.eth_address == None).all()
        if shops_without_eth:
            print("\nRation shops without Ethereum addresses:")
            for shop in shops_without_eth:
                print(f"  - ID: {shop.id}, Name: {shop.name}, Status: {shop.status}")
        
        # List warehouses without Ethereum addresses
        warehouses_without_eth = Warehouse.query.filter(Warehouse.eth_address == None).all()
        if warehouses_without_eth:
            print("\nWarehouses without Ethereum addresses:")
            for warehouse in warehouses_without_eth:
                print(f"  - ID: {warehouse.id}, Name: {warehouse.name}")

if __name__ == "__main__":
    main() 