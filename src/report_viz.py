import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
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
    fig, ax = plt.subplots(figsize=(10, 6))
    
    conv_metrics = analysis['conversion_metrics']
    variants = list(conv_metrics.keys())
    
    conversion_rates = [conv_metrics[v]['conversion_rate'] * 100 for v in variants]
    ci_lower = [conv_metrics[v]['ci_lower'] * 100 for v in variants]
    ci_upper = [conv_metrics[v]['ci_upper'] * 100 for v in variants]
    
    errors = [[conversion_rates[i] - ci_lower[i] for i in range(len(variants))],
              [ci_upper[i] - conversion_rates[i] for i in range(len(variants))]]
    
    x_pos = range(len(variants))
    colors = ['#3498db', '#e74c3c']
    
    bars = ax.bar(x_pos, conversion_rates, color=colors, alpha=0.7, edgecolor='black')
    ax.errorbar(x_pos, conversion_rates, yerr=errors, fmt='none', color='black', 
                capsize=5, capthick=2, elinewidth=2)
    
    ax.set_xlabel('Model Variant', fontsize=12, fontweight='bold')
    ax.set_ylabel('Conversion Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Conversion Rate Comparison with 95% Confidence Intervals', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([v.replace('_', ' ').title() for v in variants])
    
    for i, (bar, rate) in enumerate(zip(bars, conversion_rates)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{rate:.2f}%\n(n={conv_metrics[variants[i]]["sample_size"]})',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'conversion_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_latency_comparison(df, analysis, output_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    lat_metrics = analysis['latency_metrics']
    variants = list(lat_metrics.keys())
    
    mean_latencies = [lat_metrics[v]['mean_latency'] for v in variants]
    ci_lower = [lat_metrics[v]['ci_lower'] for v in variants]
    ci_upper = [lat_metrics[v]['ci_upper'] for v in variants]
    
    errors = [[mean_latencies[i] - ci_lower[i] for i in range(len(variants))],
              [ci_upper[i] - mean_latencies[i] for i in range(len(variants))]]
    
    x_pos = range(len(variants))
    colors = ['#3498db', '#e74c3c']
    
    bars = ax1.bar(x_pos, mean_latencies, color=colors, alpha=0.7, edgecolor='black')
    ax1.errorbar(x_pos, mean_latencies, yerr=errors, fmt='none', color='black',
                 capsize=5, capthick=2, elinewidth=2)
    
    ax1.set_xlabel('Model Variant', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mean Latency (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('Mean Latency Comparison with 95% CI', fontsize=12, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([v.replace('_', ' ').title() for v in variants])
    
    for i, (bar, lat) in enumerate(zip(bars, mean_latencies)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                 f'{lat:.2f}ms',
                 ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    violin_data = [df[df['variant'] == v]['latency_ms'].values for v in variants]
    parts = ax2.violinplot(violin_data, positions=x_pos, showmeans=True, showmedians=True)
    
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
    
    ax2.set_xlabel('Model Variant', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Latency Distribution (Violin Plot)', fontsize=12, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([v.replace('_', ' ').title() for v in variants])
    
    plt.tight_layout()
    plt.savefig(output_dir / 'latency_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_traffic_distribution(df, output_dir):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    variant_counts = df['variant'].value_counts()
    labels = [v.replace('_', ' ').title() for v in variant_counts.index]
    sizes = variant_counts.values
    colors = ['#3498db', '#e74c3c']
    explode = (0.05, 0.05)
    
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                        autopct='%1.1f%%', shadow=True, startangle=90)
    
    for text in texts:
        text.set_fontsize(12)
        text.set_fontweight('bold')
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')
    
    ax.set_title('Traffic Distribution Between Variants', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'traffic_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    print("Loading data and analysis results...")
    df, analysis = load_data()
    
    output_dir = Path('/root/AB_testing/results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating conversion comparison chart...")
    create_conversion_comparison(df, analysis, output_dir)
    
    print("Creating latency comparison chart...")
    create_latency_comparison(df, analysis, output_dir)
    
    print("Creating traffic distribution chart...")
    create_traffic_distribution(df, output_dir)
    
    print("\nVisualization complete!")
    print(f"Charts saved to: {output_dir}")
    print("  - conversion_comparison.png")
    print("  - latency_comparison.png")
    print("  - traffic_distribution.png")

if __name__ == "__main__":
    main()