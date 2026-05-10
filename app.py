from flask import Flask, render_template, request, session, redirect, url_for, Response
import os
import sqlite3
import io
import base64
import csv
import matplotlib 
matplotlib.use('Agg')  # Use non-interactive backend for Matplotlib
import matplotlib.pyplot as plt

# Import your custom modules
from modules.product_builder import build_product
from modules.calculator import calculate_batch_water_footprint
from modules.ml_model import get_recommendation
from modules.visualizer import plot_stacked_components, plot_batch_doughnut, plot_radar_chart, plot_waterfall

app = Flask(__name__)
app.secret_key = "super_secret_btech_key"
DB_PATH = os.path.join(os.path.dirname(__file__), "waterfootprint.db")

def fetch_data(query):
    """Utility function to fetch data for dropdowns."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query)
    data = [row[0] for row in cursor.fetchall()]
    conn.close()
    return data

def fig_to_base64(fig):
    """Converts Matplotlib figures to base64 strings for HTML rendering."""
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', facecolor='#1e1e1e')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode('utf-8')

@app.route("/", methods=["GET", "POST"])
def index():
    # Load data for the form dropdowns
    materials = fetch_data("SELECT material_name FROM Material_Master ORDER BY material_name")
    processes = fetch_data("SELECT process_name FROM Process_Master ORDER BY process_name")
    
    if "log" not in session:
        session["log"] = []

    cumulative_total = 0
    chart1_b64 = chart2_b64 = chart3_b64 = chart4_b64 = None

    if request.method == "POST":
        # ACTION: Reset the entire session
        if "reset" in request.form:
            session["log"] = []
            return redirect(url_for("index"))
            
        # ACTION: Delete a specific entry from the table
        elif "delete_index" in request.form:
            idx_to_delete = int(request.form.get("delete_index"))
            temp_log = session["log"]
            if 0 <= idx_to_delete < len(temp_log):
                temp_log.pop(idx_to_delete)
                session["log"] = temp_log
                
        # ACTION: Perform a new calculation and add to session
        elif "calculate" in request.form:
            material = request.form.get("material")
            weight = float(request.form.get("weight", 1.0))

            # FIX: parse hidden input correctly
            proc_string = request.form.get("processes", "")
            selected_procs = [p.strip() for p in proc_string.split(",") if p.strip()]

            result = build_product(material, weight, selected_procs)
            rec = get_recommendation(material, selected_procs)

            new_entry = {
                "Material": material, 
                "Weight (kg)": weight,
                "Processes": ", ".join(selected_procs) if selected_procs else "None",
                "Green (L)": result["breakdown"]["green"], 
                "Blue (L)": result["breakdown"]["blue"],
                "Grey (L)": result["breakdown"]["grey"], 
                "Overhead (L)": result["breakdown"]["overhead"],
                "Total WF (L)": result["total_water_footprint"], 
                "Recommendation": rec
            }
            temp_log = session["log"]
            temp_log.append(new_entry)
            session["log"] = temp_log


        # ACTION: Export current session data to a CSV file
        elif "export_csv" in request.form:
            if session.get("log"):
                si = io.StringIO()
                fieldnames = ["Material", "Weight (kg)", "Processes", "Green (L)", "Blue (L)", "Grey (L)", "Overhead (L)", "Total WF (L)", "Recommendation"]
                writer = csv.DictWriter(si, fieldnames=fieldnames)
                writer.writeheader()
                for item in session["log"]:
                    clean_item = item.copy()
                    # Remove emojis and clean newlines for a tidy CSV file
                    clean_item["Recommendation"] = clean_item["Recommendation"].replace('✅', '').replace('🌿', '').replace('\n', ' ').strip()
                    writer.writerow(clean_item)
                
                return Response(
                    si.getvalue(), 
                    mimetype="text/csv", 
                    headers={"Content-disposition": "attachment; filename=Water_Footprint_Report.csv"}
                )

    # If data exists in the session, calculate batch totals and generate visualizations
    if session["log"]:
        batch_items = [
            {
                "material": item["Material"], 
                "weight_kg": item["Weight (kg)"], 
                "processes": item["Processes"].split(", ") if item["Processes"] != "None" else []
            }
            for item in session["log"]
        ]
        batch_output = calculate_batch_water_footprint(batch_items)
        cumulative_total = batch_output['cumulative_total']

        try:
            # Generate the four narrative charts
            chart1_b64 = fig_to_base64(plot_batch_doughnut(session["log"]))
            chart2_b64 = fig_to_base64(plot_stacked_components(session["log"]))
            chart3_b64 = fig_to_base64(plot_waterfall(session["log"]))
            chart4_b64 = fig_to_base64(plot_radar_chart(session["log"]))
        except Exception as e:
            print(f"Visualization generation error: {e}") 

    return render_template(
        "index.html", 
        materials=materials, 
        processes=processes, 
        session_log=session["log"], 
        cumulative_total=cumulative_total, 
        chart1=chart1_b64, 
        chart2=chart2_b64, 
        chart3=chart3_b64, 
        chart4=chart4_b64
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
