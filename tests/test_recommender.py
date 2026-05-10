# recommender.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Adds project root

from modules.ml_model import train_hybrid_models

if __name__ == "__main__":
    print("=== Training Hybrid Models ===")
    train_hybrid_models()
    print("✅ Cluster_Map rebuilt with cluster_id, hier_label, quantile_id.")
