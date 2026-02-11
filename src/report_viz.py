import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import json
from pathlib import Path

sns.set_style("whitegrid")
sns.set_palette("husl")

def load_data():
    df = pd.read_csv('/root/AB_testing/data/experiment_logs.csv')
    with open('/root/AB_testing/results/analysis_summary.json', 'r') as f:
        analysis = json.load(f)
    return df, analysis

def create_conversion_comparison(df, analysis, output_dir):
    fig, ax = plt.subplots(figsize=(12, 7))
    
    conv_metrics = analysis['conversion_metrics']
    variants = sorted(conv_metrics.keys())
    
    conversion_rates = [conv_metrics[v]['conversion_rate'] * 100 for v in variants]
    ci_lower = [conv_metrics[v]['ci_lower'] * 100 for v in variants]
    ci_upper = [conv_metrics[v]['ci_upper'] * 100 for v in variants]
    
    errors = [[conversion_rates[i] - ci_lower[i] for i in range(len(variants))],
              [ci_upper[i] - conversion_rates[i] for i in range(len(variants))]]
    
    x_pos = range(len(variants))
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(variants)))
    
    bars = ax.bar(x_pos, conversion_rates, color=colors, alpha=0.7, edgecolor='black')
    ax.errorbar(x_pos, conversion_rates, yerr=errors, fmt='none', color='black', 
                capsize=5, capthick=2, elinewidth=2)
    
    ax.set_xlabel('Model Variant', fontsize=12, fontweight='bold')
    ax.set_ylabel('Conversion Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Conversion Rate Comparison with 95% Confidence Intervals', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([v.replace('_', ' ').title() for v in variants], rotation=15, ha='right')
    
    for i, (bar, rate) in enumerate(zip(bars, conversion_rates)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{rate:.2f}%\n(n={conv_metrics[variants[i]]["sample_size"]})',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    output_path = output_dir / 'conversion_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def create_latency_comparison(df, analysis, output_dir):
    fig, ax = plt.subplots(figsize=(12, 7))
    
    lat_metrics = analysis['latency_metrics']
    variants = sorted(lat_metrics.keys())
    
    mean_latencies = [lat_metrics[v]['mean_latency'] for v in variants]
    ci_lower = [lat_metrics[v]['ci_lower'] for v in variants]
    ci_upper = [lat_metrics[v]['ci_upper'] for v in variants]
    
    errors = [[mean_latencies[i] - ci_lower[i] for i in range(len(variants))],
              [ci_upper[i] - mean_latencies[i] for i in range(len(variants))]]
    
    x_pos = range(len(variants))
    colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(variants)))
    
    bars = ax.bar(x_pos, mean_latencies, color=colors, alpha=0.7, edgecolor='black')
    ax.errorbar(x_pos, mean_latencies, yerr=errors, fmt='none', color='black',
                capsize=5, capthick=2, elinewidth=2)
    
    ax.set_xlabel('Model Variant', fontsize=12, fontweight='bold')
    ax.set_ylabel('Mean Latency (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Comparison with 95% Confidence Intervals',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([v.replace('_', ' ').title() for v in variants], rotation=15, ha='right')
    
    for i, (bar, latency) in enumerate(zip(bars, mean_latencies)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{latency:.1f} ms\n(n={lat_metrics[variants[i]]["sample_size"]})',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    output_path = output_dir / 'latency_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def create_traffic_distribution(df, analysis, output_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    traffic_dist = analysis['experiment_summary']['traffic_distribution']
    variants = sorted(traffic_dist.keys())
    counts = [traffic_dist[v] for v in variants]
    colors = plt.cm.Set3(np.linspace(0, 1, len(variants)))
    
    ax1.pie(counts, labels=[v.replace('_', ' ').title() for v in variants],
            autopct='%1.1f%%', colors=colors, startangle=90,
            wedgeprops={'edgecolor': 'black', 'linewidth': 1.5})
    ax1.set_title('Traffic Distribution', fontsize=14, fontweight='bold')
    
    x_pos = range(len(variants))
    bars = ax2.bar(x_pos, counts, color=colors, alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Variant', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Request Count', fontsize=12, fontweight='bold')
    ax2.set_title('Request Count by Variant', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([v.replace('_', ' ').title() for v in variants], rotation=15, ha='right')
    
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    output_path = output_dir / 'traffic_distribution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def create_latency_distribution(df, analysis, output_dir):
    fig, ax = plt.subplots(figsize=(14, 7))
    
    variants = sorted(df['variant'].unique())
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(variants)))
    
    for i, variant in enumerate(variants):
        variant_data = df[df['variant'] == variant]['latency_ms']
        ax.hist(variant_data, bins=30, alpha=0.5, label=variant.replace('_', ' ').title(),
                color=colors[i], edgecolor='black')
    
    ax.set_xlabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('Latency Distribution by Variant', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = output_dir / 'latency_distribution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def create_conversion_boxplot(df, analysis, output_dir):
    fig, ax = plt.subplots(figsize=(12, 7))
    
    variants = sorted(df['variant'].unique())
    colors = plt.cm.Set2(np.linspace(0, 1, len(variants)))
    
    conversion_data = []
    labels = []
    for variant in variants:
        variant_conversions = df[df['variant'] == variant]['conversion'].astype(int)
        conversion_data.append(variant_conversions)
        labels.append(variant.replace('_', ' ').title())
    
    bp = ax.boxplot(conversion_data, labels=labels, patch_artist=True,
                     showmeans=True, meanline=True)
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xlabel('Variant', fontsize=12, fontweight='bold')
    ax.set_ylabel('Conversion (0=No, 1=Yes)', fontsize=12, fontweight='bold')
    ax.set_title('Conversion Distribution by Variant', fontsize=14, fontweight='bold')
    plt.xticks(rotation=15, ha='right')
    
    plt.tight_layout()
    output_path = output_dir / 'conversion_boxplot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def generate_visualizations():
    print("Loading data and analysis results...")
    df, analysis = load_data()
    
    output_dir = Path('/root/AB_testing/results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating visualizations...")
    
    create_conversion_comparison(df, analysis, output_dir)
    create_latency_comparison(df, analysis, output_dir)
    create_traffic_distribution(df, analysis, output_dir)
    create_latency_distribution(df, analysis, output_dir)
    create_conversion_boxplot(df, analysis, output_dir)
    
    print("\nAll visualizations generated successfully!")

if __name__ == "__main__":
    generate_visualizations()