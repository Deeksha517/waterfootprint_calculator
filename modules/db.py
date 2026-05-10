# modules/db.py (refined loader with constraints support)
import sqlite3
import csv
import os
import sys

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.join(BASE_DIR, "..")
DB_PATH = os.path.join(PROJECT_ROOT, "waterfootprint.db")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "schema.sql")
MATERIALS_CSV = os.path.join(PROJECT_ROOT, "data", "materials.csv")
PROCESSES_CSV = os.path.join(PROJECT_ROOT, "data", "processes.csv")


def run_schema():
    """Run schema.sql to create tables with constraints and indexes."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                sql = f.read()
            conn.executescript(sql)
        print("✅ Database schema created successfully.")
    except Exception as e:
        print("❌ ERROR running schema:", e)
        raise


def safe_float(value, colname=""):
    """Convert CSV values to float safely, enforcing non-empty numeric values."""
    if value is None:
        raise ValueError(f"Missing numeric value for {colname}")
    v = str(value).strip().replace(",", "")
    if v == "":
        raise ValueError(f"Empty numeric value for {colname}")
    try:
        f = float(v)
    except ValueError:
        raise ValueError(f"Invalid numeric value '{value}' for {colname}")
    if f < 0:
        raise ValueError(f"Negative value not allowed for {colname}")
    return f


def load_materials():
    """Load materials.csv into Material_Master table."""
    if not os.path.exists(MATERIALS_CSV):
        raise FileNotFoundError(f"{MATERIALS_CSV} not found")

    with sqlite3.connect(DB_PATH) as conn, open(MATERIALS_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = ["Fiber", "Green Water (Rain)", "Blue Water (Agri)",
                    "Grey Water (Agri)", "Blue Water (Ind)", "Grey Water (Ind)", "TOTAL"]
        for h in required:
            if h not in reader.fieldnames:
                raise KeyError(f"materials.csv missing expected column: {h}")

        cur = conn.cursor()
        inserted = 0
        for i, row in enumerate(reader, start=1):
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO Material_Master
                    (material_name, WF_Green, WF_Blue_Agri, WF_Grey_Agri,
                     WF_Blue_Ind, WF_Grey_Ind, total_WF)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["Fiber"].strip(),
                    safe_float(row["Green Water (Rain)"], "Green Water (Rain)"),
                    safe_float(row["Blue Water (Agri)"], "Blue Water (Agri)"),
                    safe_float(row["Grey Water (Agri)"], "Grey Water (Agri)"),
                    safe_float(row["Blue Water (Ind)"], "Blue Water (Ind)"),
                    safe_float(row["Grey Water (Ind)"], "Grey Water (Ind)"),
                    safe_float(row["TOTAL"], "TOTAL")
                ))
                inserted += cur.rowcount
            except Exception as e:
                print(f"❌ Error on materials.csv line {i}: {e}")
                raise
        conn.commit()
    print(f"✅ Materials loaded. Rows attempted: {i}, rows inserted: {inserted}")


def load_processes():
    """Load processes.csv into Process_Master table."""
    if not os.path.exists(PROCESSES_CSV):
        raise FileNotFoundError(f"{PROCESSES_CSV} not found")

    with sqlite3.connect(DB_PATH) as conn, open(PROCESSES_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = ["Process", "Blue_Add", "Grey_Add"]
        for h in required:
            if h not in reader.fieldnames:
                raise KeyError(f"processes.csv missing expected column: {h}")

        cur = conn.cursor()
        inserted = 0
        for i, row in enumerate(reader, start=1):
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO Process_Master
                    (process_name, blue_add, grey_add)
                    VALUES (?, ?, ?)
                """, (
                    row["Process"].strip(),
                    safe_float(row["Blue_Add"], "Blue_Add"),
                    safe_float(row["Grey_Add"], "Grey_Add")
                ))
                inserted += cur.rowcount
            except Exception as e:
                print(f"❌ Error on processes.csv line {i}: {e}")
                raise
        conn.commit()
    print(f"✅ Processes loaded. Rows attempted: {i}, rows inserted: {inserted}")


if __name__ == "__main__":
    print("🚀 Initializing DB and loading CSV data...")
    try:
        run_schema()
        load_materials()
        load_processes()
    except Exception as exc:
        print("❌ Setup failed:", exc)
        sys.exit(1)
    print("🎉 DATABASE SETUP COMPLETED.")
