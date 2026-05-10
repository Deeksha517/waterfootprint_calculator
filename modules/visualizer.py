import matplotlib
matplotlib.use('Agg')  # This is CRITICAL for cloud deployment
import matplotlib.pyplot as plt

import numpy as np



def apply_dark_theme(ax, fig):
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#262730')
    ax.tick_params(colors='#fafafa') # Force tick labels to White
    for spine in ax.spines.values():
        spine.set_color('#444')
    ax.yaxis.label.set_color('#fafafa')
    ax.xaxis.label.set_color('#fafafa')
    ax.title.set_color('#fafafa')

# --- 1. FIXED Doughnut Chart ---
def plot_batch_doughnut(session_log):
    green = sum(item["Green (L)"] for item in session_log)
    blue = sum(item["Blue (L)"] for item in session_log)
    grey = sum(item["Grey (L)"] for item in session_log)
    overhead = sum(item["Overhead (L)"] for item in session_log)
    
    sizes = [green, blue, grey, overhead]
    labels = ['Green', 'Blue', 'Grey', 'Overhead']
    colors = ['#50cd89', '#60a5fa', '#a3a8b8', '#ffc107']
    
    filtered_sizes = []
    filtered_labels = []
    filtered_colors = []
    for s, l, c in zip(sizes, labels, colors):
        if s > 0:
            filtered_sizes.append(s)
            # Create label that includes percentage for the legend
            filtered_labels.append(f"{l} ({ (s/sum(sizes)*100):.1f}%)")
            filtered_colors.append(c)

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor('#1e1e1e')
    
    if not filtered_sizes: return fig

    # autopct is removed from pie to prevent overlapping white text
    patches, texts = ax.pie(
        filtered_sizes, 
        colors=filtered_colors, 
        startangle=90, 
        counterclock=False,
        wedgeprops={'edgecolor': '#1e1e1e', 'linewidth': 2}
    )
    
    centre_circle = plt.Circle((0,0), 0.70, fc='#1e1e1e')
    fig.gca().add_artist(centre_circle)
    
    total_wf = sum(filtered_sizes)
    ax.text(0, 0, f'{total_wf:,.0f} L\nTotal', ha='center', va='center', 
            fontsize=14, color='#fafafa', fontweight='bold')
    
    # FIX: Legend labels forced to White
    leg = ax.legend(
        patches, filtered_labels,
        title="Breakdown",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        facecolor='#262730', edgecolor='#444'
    )
    plt.setp(leg.get_texts(), color='#fafafa') # Force legend text to White
    plt.setp(leg.get_title(), color='#fafafa') # Force legend title to White
    
    ax.axis('equal')
    plt.tight_layout()
    return fig

# --- 2. 100% Normalized Bar ---
def plot_stacked_components(session_log):
    materials = [f"{item['Material']}\n({i})" for i, item in enumerate(session_log)]
    green = np.array([item['Green (L)'] for item in session_log], dtype=float)
    blue = np.array([item['Blue (L)'] for item in session_log], dtype=float)
    grey = np.array([item['Grey (L)'] for item in session_log], dtype=float)
    overhead = np.array([item['Overhead (L)'] for item in session_log], dtype=float)
    
    totals = green + blue + grey + overhead
    totals[totals == 0] = 1 
    
    fig, ax = plt.subplots(figsize=(10, 5))
    apply_dark_theme(ax, fig)

    ax.bar(materials, (green/totals)*100, label='Green %', color='#50cd89')
    ax.bar(materials, (blue/totals)*100, bottom=(green/totals)*100, label='Blue %', color='#60a5fa')
    ax.bar(materials, (grey/totals)*100, bottom=((green+blue)/totals)*100, label='Grey %', color='#a3a8b8')
    ax.bar(materials, (overhead/totals)*100, bottom=((green+blue+grey)/totals)*100, label='Overhead %', color='#ffc107')

    ax.set_ylabel('Percentage (%)', color='#fafafa')
    ax.set_title('100% Normalized Component Composition', color='#fafafa')
    leg = ax.legend(facecolor='#262730', edgecolor='#444', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.setp(leg.get_texts(), color='#fafafa')
    plt.tight_layout()
    return fig

# --- 3. FIXED Waterfall Chart (Tiny Bar Fix) ---
def plot_waterfall(session_log):
    green = sum(item["Green (L)"] for item in session_log)
    blue = sum(item["Blue (L)"] for item in session_log)
    grey = sum(item["Grey (L)"] for item in session_log)
    overhead = sum(item["Overhead (L)"] for item in session_log)
    total = green + blue + grey + overhead

    labels = ['Green', 'Blue', 'Grey', 'Overhead', 'Total WF']
    raw_values = [green, blue, grey, overhead, total]
    
    # SMART FIX: If a value is < 1% of total, give it a visible minimum height for the drawing
    # but keep the text label as the real raw value.
    min_height = total * 0.015 
    display_values = [max(v, min_height) if v > 0 else 0 for v in raw_values]
    
    colors = ['#50cd89', '#60a5fa', '#a3a8b8', '#ffc107', '#ff4b4b']
    
    # Calculate step-up positions
    bottoms = [0, green, green+blue, green+blue+grey, 0]

    fig, ax = plt.subplots(figsize=(10, 6))
    apply_dark_theme(ax, fig)

    bars = ax.bar(labels, display_values, bottom=bottoms, color=colors)
    
    ax.set_ylim(0, total * 1.4)

    for i, bar in enumerate(bars):
        real_val = raw_values[i]
        y_pos = bar.get_y() + bar.get_height()
        # Ensure numbers are strictly white and visible
        ax.text(bar.get_x() + bar.get_width()/2., y_pos + (total * 0.02),
                f'{real_val:,.0f}', ha='center', va='bottom', 
                color='#ffffff', fontsize=10, fontweight='bold')

    ax.set_ylabel('Water Footprint (L)', color='#fafafa')
    ax.set_title('Cumulative Impact Build-up', pad=40, fontsize=14, color='#fafafa')
    
    plt.tight_layout()
    return fig

# --- 4. Radar Chart ---
def plot_radar_chart(session_log):
    labels = ['Green', 'Blue', 'Grey', 'Overhead']
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1] 

    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#262730')
    
    for i, item in enumerate(session_log):
        raw_values = [item['Green (L)'], item['Blue (L)'], item['Grey (L)'], item['Overhead (L)']]
        values = [np.log10(v + 1) for v in raw_values]
        values += values[:1]
        ax.plot(angles, values, linewidth=2, label=f"{item['Material']} ({i})")
        ax.fill(angles, values, alpha=0.1)

    ax.set_thetagrids(np.degrees(angles[:-1]), labels, color='#fafafa')
    ax.set_rticks([1, 2, 3, 4, 5, 6])
    ax.set_yticklabels(['10', '100', '1K', '10K', '100K', '1M'], color='#666', fontsize=8)
    leg = ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), facecolor='#262730', edgecolor='#444')
    plt.setp(leg.get_texts(), color='#fafafa')
    plt.tight_layout()
    return fig