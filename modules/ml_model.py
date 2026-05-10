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

    # --- KMeans clustering ---
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['kmeans_label'] = kmeans.fit_predict(X)
    cluster_means = df.groupby('kmeans_label')['total_wf'].mean().sort_values()
    mapping = {old:new for new,old in enumerate(cluster_means.index)}
    df['cluster_id'] = df['kmeans_label'].map(mapping)

    # --- Hierarchical clustering ---
    hc = AgglomerativeClustering(n_clusters=3)
    df['hier_label'] = hc.fit_predict(X)

    # --- Quantile classification ---
    q_low = df['total_wf'].quantile(0.33)
    q_high = df['total_wf'].quantile(0.66)
    def classify(wf):
        if wf <= q_low: return 0
        elif wf <= q_high: return 1
        else: return 2
    df['quantile_id'] = df['total_wf'].apply(classify)

    # --- Regression model (train & save coefficients) ---
    reg = LinearRegression()
    reg.fit(X, df['total_wf'])
    coef = list(reg.coef_)
    intercept = reg.intercept_

    # --- Save results ---
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Cluster_Map (
            material_name TEXT PRIMARY KEY,
            cluster_id INTEGER,
            hier_label INTEGER,
            quantile_id INTEGER
        )
    ''')
    data_to_save = list(zip(df['material_name'], df['cluster_id'], df['hier_label'], df['quantile_id']))
    conn.executemany('INSERT OR REPLACE INTO Cluster_Map VALUES (?, ?, ?, ?)', data_to_save)

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
    print("✅ Hybrid models trained: KMeans, Hierarchical, Quantiles, Regression.")

def get_recommendation(material_name, processes_list=None):
    # --- Step 1: Material suggestion from ML clusters ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantile_id FROM Cluster_Map WHERE material_name=?", (material_name,))
    row = cursor.fetchone()
    conn.close()

    material_suggestion = "✅ Current material is acceptable"
    if row:
        quantile_id = row[0]
        if quantile_id == 2:  # high-impact material
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT material_name FROM Cluster_Map WHERE quantile_id=0 LIMIT 1")
            alt = cursor.fetchone()
            conn.close()
            if alt:
                material_suggestion = f"🌿 Recommendation: Switch to {alt[0]}"

    # --- Step 2: Process suggestions ---
    process_suggestions = []
    if processes_list and material_name in PROCESS_RECOMMENDATIONS:
        for proc in processes_list:
            if proc in PROCESS_RECOMMENDATIONS[material_name]:
                process_suggestions.append(PROCESS_RECOMMENDATIONS[material_name][proc])

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
