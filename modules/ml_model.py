# modules/ml_model.py
import sqlite3, os
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from .process_recommendations import PROCESS_RECOMMENDATIONS

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "waterfootprint.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def train_hybrid_models():
    """
    Train hybrid ML models:
    - KMeans clustering for sustainability categorization (0=Low, 1=Medium, 2=High impact).
    - Linear Regression for predictive analytics of total water footprint.
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
        print("❌ Error: No data in Material_Master!")
        return

    X = df[['wf_green','wf_blue','wf_grey']]

    # --- KMeans clustering ---
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['kmeans_label'] = kmeans.fit_predict(X)

    # Sort clusters by mean total footprint to ensure consistent labeling
    cluster_means = df.groupby('kmeans_label')['total_wf'].mean().sort_values()
    mapping = {old:new for new,old in enumerate(cluster_means.index)}
    df['cluster_id'] = df['kmeans_label'].map(mapping)

    # --- Regression model ---
    reg = LinearRegression()
    reg.fit(X, df['total_wf'])
    coef = list(reg.coef_)
    intercept = reg.intercept_

    # --- Save results to Cluster_Map ---
    data_to_save = list(zip(df['material_name'], df['cluster_id']))
    conn.executemany(
        'INSERT OR REPLACE INTO Cluster_Map (material_name, quantile_id) VALUES (?, ?)',
        data_to_save
    )

    # --- Save regression coefficients ---
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
    conn.execute(
        'INSERT INTO Regression_Model (coef_green,coef_blue,coef_grey,intercept) VALUES (?,?,?,?)',
        (coef[0],coef[1],coef[2],intercept)
    )

    conn.commit()
    conn.close()
    print("✅ Hybrid models trained: KMeans clusters + Regression wired to DB.")

def get_recommendation(material_name, processes_list=None):
    # Normalize material name
    material_name = material_name.strip()

    # --- Step 1: Material suggestion ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantile_id FROM Cluster_Map WHERE material_name=?", (material_name,))
    row = cursor.fetchone()
    conn.close()

    quantile_label = None
    if row:
        quantile_label = row[0]

    # Debug logging
    print(f"DEBUG: Material={material_name}, quantile_id={quantile_label}")

    impact_map = {0: "Low impact", 1: "Medium impact", 2: "High impact"}
    impact_text = impact_map.get(quantile_label, "Unknown impact")

    if quantile_label == 2:  # high-impact
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT material_name FROM Cluster_Map WHERE quantile_id=0 AND material_name != ?", (material_name,))
        alt = cursor.fetchone()
        conn.close()
        if alt:
            material_suggestion = f"{material_name} ({impact_text}): 🌿 Recommendation: Switch to {alt[0]}"
        else:
            material_suggestion = f"{material_name} ({impact_text}): 🌿 High impact material, consider alternatives"
    elif quantile_label is not None:
        material_suggestion = f"{material_name} ({impact_text}): ✅ Current material is acceptable"
    else:
        material_suggestion = f"{material_name}: ⚠️ No quantile data found, retrain models!"

    # --- Step 2: Process suggestions ---
    process_suggestions = []
    if processes_list:
        if material_name in PROCESS_RECOMMENDATIONS:
            for proc in processes_list:
                if proc in PROCESS_RECOMMENDATIONS[material_name]:
                    suggestion = PROCESS_RECOMMENDATIONS[material_name][proc]
                    if not suggestion.lower().startswith(("avoid", "prefer", "use", "switch")):
                        suggestion = "Recommendation: " + suggestion
                    process_suggestions.append(suggestion)

    # --- Step 3: Combine ---
    if process_suggestions:
        return "; ".join([material_suggestion] + process_suggestions)
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
