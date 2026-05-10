# 💧 Water Footprint Assessment Tool

A professional-grade web application built to calculate and visualize the environmental impact of textile production. This tool uses **Machine Learning (K-Means Clustering)** to provide sustainable recommendations and **Matplotlib** to generate deep analytical insights.

## 🚀 Live Demo
[Insert your Render URL here after deployment]

---

## 🌟 Key Features
* **Batch Calculation:** Calculate the cumulative water footprint for multiple materials in one session.
* **Narrative Visualizations:** * **100% Normalized Bars:** Compare pollution profiles regardless of material weight.
    * **Waterfall Charts:** Track cumulative impact build-up across Green, Blue, and Grey water.
    * **Radar Geometry:** Visualize material "shapes" on a logarithmic scale.
* **ML-Powered Recommendations:** Get real-time sustainability advice based on material clusters.
* **Data Export:** Download your full assessment as a professional CSV report.

---

## 🛠️ Technology Stack
* **Backend:** Python (Flask)
* **Database:** SQLite3 (Relational Schema)
* **Data Science:** NumPy, Scikit-Learn (K-Means)
* **Visualization:** Matplotlib (Agg Backend for Cloud)
* **Frontend:** HTML5, CSS3 (Streamlit-inspired Dark Theme), Bootstrap 5

---

## 📊 Database Architecture
The project uses a structured relational database (`waterfootprint.db`) containing:
* `Material_Master`: Base environmental data for various fibers.
* `Process_Master`: Impact data for industrial wet-processing.
* `Overhead_Master`: Fixed manufacturing water costs.
* `Cluster_Map`: Pre-computed ML labels for materials.

---

## ⚙️ How to Run Locally


**Clone the repository:**
   ```bash
   git clone [https://github.com/Deeksha517/waterfootprint_calculator.git](https://github.com/Deeksha517/waterfootprint_calculator.git)