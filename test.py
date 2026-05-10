import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from modules.visualizer import (
    plot_batch_doughnut,
    plot_stacked_components,
    plot_waterfall,
    plot_radar_chart
)

# Dummy session_log data
session_log = [
    {"Material": "Cotton (Conv.)", "Green (L)": 12000, "Blue (L)": 4320, "Grey (L)": 2925, "Overhead (L)": 10},
    {"Material": "Polyester", "Green (L)": 0, "Blue (L)": 180, "Grey (L)": 1000, "Overhead (L)": 30},
    {"Material": "Viscose", "Green (L)": 1000, "Blue (L)": 1900, "Grey (L)": 8500, "Overhead (L)": 30},
]

def save_fig(fig, name):
    fig.savefig(f"{name}.png", bbox_inches="tight", facecolor="#1e1e1e")
    plt.close(fig)
    print(f"Saved {name}.png")

# Test each chart
save_fig(plot_batch_doughnut(session_log), "doughnut_test")
save_fig(plot_stacked_components(session_log), "stacked_test")
save_fig(plot_waterfall(session_log), "waterfall_test")
save_fig(plot_radar_chart(session_log), "radar_test")
