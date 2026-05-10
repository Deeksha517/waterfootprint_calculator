# Product WF builder
import sqlite3
import os
from .calculator import calculate_water_footprint
from .ml_model import get_recommendation

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "waterfootprint.db")


def save_transaction(material_name, weight_kg, processes_list, total_wf):
    """Save a calculation to Transaction_Log"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO Transaction_Log 
        (user_input_material, weight_entered, selected_finishes, calculated_output)
        VALUES (?, ?, ?, ?)
    """, (
        material_name,
        weight_kg,
        ",".join(processes_list),
        total_wf
    ))
    
    conn.commit()
    conn.close()


def build_product(material_name, weight_kg, processes_list):
    """
    Full workflow:
    1. Calculate water footprint
    2. Save transaction
    3. Get recommendation
    Returns a flat dict ready for frontend/demo.
    """
    # 1. Calculate water footprint
    result = calculate_water_footprint(material_name, weight_kg, processes_list)
    
    # 2. Save transaction
    save_transaction(
        material_name,
        weight_kg,
        processes_list,
        result["total_water_footprint"]
    )
    
    # 3. Get recommendation
    recommendation = get_recommendation(material_name)
    
    # 4. Merge into single dict for easy access
    result["recommendation"] = recommendation
    return result
