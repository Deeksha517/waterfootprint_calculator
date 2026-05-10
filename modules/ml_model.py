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
    """
    Trains the K-Means Clustering and Linear Regression models.
    K-Means is used for sustainability categorization (0=Best, 1=Avg, 2=Worst).
    Regression is used to predict the total water footprint based on component rates.
    """
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
    # We use 3 clusters to differentiate between Low, Medium, and High impact materials.
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['kmeans_label'] = kmeans.fit_predict(X)
    
    # CRITICAL: Sort clusters by mean total footprint to ensure labels are consistent:
    # 0 = Best (Low impact), 1 = Average (Medium impact), 2 = Worst (High impact)
    cluster_means = df.groupby('kmeans_label')['total_wf'].mean().sort_values()
    mapping = {old:new for new,old in enumerate(cluster_means.index)}
    df['cluster_id'] = df['kmeans_label'].map(mapping)

    # --- Regression model (train & save coefficients) ---
    # Used for predictive analytics of the water footprint build-up.
    reg = LinearRegression()
    reg.fit(X, df['total_wf'])
    coef = list(reg.coef_)
    intercept = reg.intercept_

    # --- Save results to Cluster_Map ---
    # We save 'cluster_id' into the database for real-time recommendation retrieval.
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
            # Instead of LIMIT 1, fetch ALL low-impact materials and pick one different from current
            cursor.execute("SELECT material_name FROM Cluster_Map WHERE quantile_id=0 AND material_name != ?", (material_name,))
            alt = cursor.fetchone()
            conn.close()
            if alt:
                material_suggestion = f"🌿 Recommendation: Switch to {alt[0]}"

    # --- Step 2: Process suggestions ---
    process_suggestions = []
    if processes_list:
        # Check if material has specific process rules
        if material_name in PROCESS_RECOMMENDATIONS:
            for proc in processes_list:
                if proc in PROCESS_RECOMMENDATIONS[material_name]:
                    process_suggestions.append(PROCESS_RECOMMENDATIONS[material_name][proc])
        else:
            # Fallback: generic process rules (optional)
            for proc in processes_list:
                if "Screen Printing" in proc:
                    process_suggestions.append("Prefer Digital Printing for lower water use")
                elif "Bleach Wash" in proc:
                    process_suggestions.append("Avoid Bleach Wash; prefer Enzyme Wash")

    # --- Step 3: Combine ---
    if process_suggestions:
        return f"{material_suggestion}; " + "; ".join(process_suggestions)
    return material_suggestion


def predict_footprint(green, blue, grey):
    """Predict total water footprint using regression model coefficients."""
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