# Unit test

# test_calculator.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Adds project root

from modules.calculator import calculate_water_footprint

def run_calculator_tests():
    print("=== Calculator Tests ===")
    
    test_cases = [
        ("Cotton (Conv.)", 1, []),
        ("Polyester", 2, ["Stone Wash (Denim)"]),
        ("Linen (Flax)", 0.5, ["Enzyme Wash", "Garment Dyeing (Dip)"])
    ]
    
    for material, weight, processes in test_cases:
        result = calculate_water_footprint(material, weight, processes)
        print(f"\nMaterial: {material}")
        print(f"Weight: {weight} kg")
        print(f"Processes: {processes}")
        print(f"Breakdown: {result['breakdown']}")
        print(f"Total WF: {result['total_water_footprint']} Liters")

if __name__ == "__main__":
    run_calculator_tests()
