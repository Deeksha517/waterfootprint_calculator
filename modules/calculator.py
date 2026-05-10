# modules/calculator.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "waterfootprint.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def fetch_material(material_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT material_name, WF_Green, WF_Blue_Agri, WF_Grey_Agri,
               WF_Blue_Ind, WF_Grey_Ind, total_WF
        FROM Material_Master
        WHERE material_name = ?
    """, (material_name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "material_name": row[0],
        "wf_green": row[1],
        "wf_blue_agri": row[2],
        "wf_grey_agri": row[3],
        "wf_blue_ind": row[4],
        "wf_grey_ind": row[5],
        "total_wf": row[6]
    }

def fetch_process(process_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT process_name, blue_add, grey_add
        FROM Process_Master
        WHERE process_name = ?
    """, (process_name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "process_name": row[0],
        "blue_add": row[1],
        "grey_add": row[2],
    }

def fetch_overhead(process_name):
    """Fetch overhead water use for a given process, fallback to Default."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT overhead FROM Overhead_Master WHERE process_name = ?", (process_name,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
    # fallback to Default
    cursor.execute("SELECT overhead FROM Overhead_Master WHERE process_name = 'Default'")
    default_row = cursor.fetchone()
    conn.close()
    return default_row[0] if default_row else 5.0

def calculate_water_footprint(material_name, weight_kg, processes_list):
    material = fetch_material(material_name)
    if material is None:
        raise ValueError(f"Material '{material_name}' not found")

    # Base rates (L/kg)
    rate_green = material["wf_green"]
    rate_blue  = material["wf_blue_agri"] + material["wf_blue_ind"]
    rate_grey  = material["wf_grey_agri"] + material["wf_grey_ind"]

    # Process additions
    rate_process_blue = 0
    rate_process_grey = 0
    overhead_total = 0
    valid_processes = []

    for p in processes_list:
        proc = fetch_process(p)
        if proc:
            rate_process_blue += proc["blue_add"]
            rate_process_grey += proc["grey_add"]
            overhead_total += fetch_overhead(p)
            valid_processes.append(p)

    # If no processes selected, use default overhead
    if not valid_processes:
        overhead_total = fetch_overhead("Default")

    # Compute volumes
    vol_green = rate_green * weight_kg
    vol_blue  = (rate_blue + rate_process_blue) * weight_kg
    vol_grey  = (rate_grey + rate_process_grey) * weight_kg

    final_wf = vol_green + vol_blue + vol_grey + overhead_total

    return {
        "material": material_name,
        "weight_kg": weight_kg,
        "processes": valid_processes,
        "breakdown": {
            "green": round(vol_green, 2),
            "blue": round(vol_blue, 2),
            "grey": round(vol_grey, 2),
            "overhead": round(overhead_total, 2)
        },
        "total_water_footprint": round(final_wf, 2)
    }

def calculate_batch_water_footprint(batch_items):
    """
    batch_items: list of dicts like
        [
            {"material": "Cotton (Conv.)", "weight_kg": 1.0, "processes": ["Reactive Dyeing"]},
            {"material": "Polyester", "weight_kg": 0.5, "processes": ["Printing", "Finishing"]}
        ]
    """
    results = []
    cumulative_total = 0.0

    for item in batch_items:
        try:
            res = calculate_water_footprint(
                material_name=item["material"],
                weight_kg=item["weight_kg"],
                processes_list=item.get("processes", [])
            )
            results.append(res)
            cumulative_total += res["total_water_footprint"]
        except Exception as e:
            results.append({"error": str(e), "item": item})

    return {
        "batch_results": results,
        "cumulative_total": round(cumulative_total, 2)
    }
