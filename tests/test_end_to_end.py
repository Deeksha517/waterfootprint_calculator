# End-to-end test

# db_end_to_end.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Adds project root


from modules.db import run_schema, load_materials, load_processes
from modules.product_builder import build_product

def run_db_tests():
    print("=== Database End-to-End Test ===")
    
    print("\n1. Running schema...")
    run_schema()
    
    print("\n2. Loading materials...")
    load_materials()
    
    print("\n3. Loading processes...")
    load_processes()
    
    print("\n4. Testing product build (calculation + transaction)...")
    result = build_product("Cotton (Conv.)", 1, ["Stone Wash (Denim)"])
    print("Product Build Result:", result)

if __name__ == "__main__":
    run_db_tests()
