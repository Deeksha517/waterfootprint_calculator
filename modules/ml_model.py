# modules/ml_model.py
import sqlite3, os
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.linear_model import LinearRegression
from .process_recommendations import PROCESS_RECOMMENDATIONS

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "waterfootprint.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def train_hybrid_models():
    conn = get_db_connection()
    query = """
        SELECT material_name, 
               WF_Green AS wf_green, 
               (WF_Blue_Agri + WF_Blue_Ind) AS wf_blue, 
               (WF_Grey_Agri + WF_Grey_Ind) AS wf_grey,
               total_WF AS total_wf
        FROM Material_Master
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        print("Error: No data in Material_Master!")
        return

    X = df[['wf_green','wf_blue','wf_grey']]

    # --- TRUE MACHINE LEARNING: KMeans clustering ---
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['kmeans_label'] = kmeans.fit_predict(X)
    
    # Sort clusters by total impact: 0 (Best), 1 (Average), 2 (Worst)
    cluster_means = df.groupby('kmeans_label')['total_wf'].mean().sort_values()
    mapping = {old:new for new,old in enumerate(cluster_means.index)}
    df['cluster_id'] = df['kmeans_label'].map(mapping)

    # --- Regression model (train & save coefficients) ---
    reg = LinearRegression()
    reg.fit(X, df['total_wf'])
    coef = list(reg.coef_)
    intercept = reg.intercept_

    # --- FIX: Save actual K-Means results to the DB ---
    # We map 'cluster_id' into the 'quantile_id' column so we don't break your SQL schema
    data_to_save = list(zip(df['material_name'], df['cluster_id']))
    conn.executemany('INSERT OR REPLACE INTO Cluster_Map (material_name, quantile_id) VALUES (?, ?)', data_to_save)

    # --- Save results to Regression_Model ---
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Regression_Model (
            id INTEGER PRIMARY KEY,
            coef_green REAL,
            coef_blue REAL,
            coef_grey REAL,
            intercept REAL
        )
    ''')
    conn.execute('DELETE FROM Regression_Model')
    conn.execute('INSERT INTO Regression_Model (coef_green,coef_blue,coef_grey,intercept) VALUES (?,?,?,?)',
                 (coef[0],coef[1],coef[2],intercept))

    conn.commit()
    conn.close()
    print("✅ Hybrid models trained: K-Means clusters successfully wired to database.")

def get_recommendation(material_name, processes_list=None):
    # --- Step 1: Material suggestion from TRUE ML clusters ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantile_id FROM Cluster_Map WHERE material_name=?", (material_name,))
    row = cursor.fetchone()
    conn.close()

    material_suggestion = "✅ Current material is acceptable"
    if row:
        # quantile_id is now actually holding the K-Means cluster_id (0, 1, or 2)
        cluster_level = row[0] 
        if cluster_level == 1:  # High-impact cluster
            conn = get_db_connection()
            cursor = conn.cursor()
            # Find an alternative from the safest cluster (Cluster 0)
            cursor.execute("SELECT material_name FROM Cluster_Map WHERE quantile_id=0 LIMIT 1")
            alt = cursor.fetchone()
            conn.close()
            if alt:
                material_suggestion = f"🌿 Recommendation: High Impact Material. Switch to {alt[0]}"

    # --- Step 2: Robust Process suggestions (With Global Fallback) ---
    process_suggestions = []
    
    # Global rules for terrible processes (applies to ANY material)
    GLOBAL_WARNINGS = {
        "Bleach Wash": "Global Warning: Bleach Wash highly pollutes Grey Water. Prefer Enzyme Wash.",
        "Desizing": "Consider eco-friendly bio-desizing to reduce water footprint."
    }

    if processes_list:
        for proc in processes_list:
            # 1. Check if there is a specific rule for this material
            if material_name in PROCESS_RECOMMENDATIONS and proc in PROCESS_RECOMMENDATIONS[material_name]:
                process_suggestions.append(PROCESS_RECOMMENDATIONS[material_name][proc])
            # 2. If no specific rule, check the global fallback warning
            elif proc in GLOBAL_WARNINGS:
                process_suggestions.append(GLOBAL_WARNINGS[proc])

    # --- Step 3: Combine ---
    if process_suggestions:
        return f"{material_suggestion}; " + "; ".join(process_suggestions)
    return material_suggestion

def predict_footprint(green, blue, grey):
    """Predict total water footprint using regression model."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT coef_green,coef_blue,coef_grey,intercept FROM Regression_Model LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    coef_green, coef_blue, coef_grey, intercept = row
    return round(coef_green*green + coef_blue*blue + coef_grey*grey + intercept, 2)

if __name__ == "__main__":
    train_hybrid_models()