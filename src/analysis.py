import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind
import json
from pathlib import Path
from typing import Dict, Any

def load_experiment_data(log_file: str) -> pd.DataFrame:
    df = pd.read_csv(log_file)
    df['conversion'] = df['conversion'].astype(bool)
    return df

def calculate_conversion_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    results = {}
    
    for variant in df['variant'].unique():
        variant_data = df[df['variant'] == variant]
        n = len(variant_data)
        conversions = variant_data['conversion'].sum()
        conversion_rate = conversions / n if n > 0 else 0
        
        se = np.sqrt(conversion_rate * (1 - conversion_rate) / n) if n > 0 else 0
        ci_margin = 1.96 * se
        
        results[variant] = {
            'sample_size': int(n),
            'conversions': int(conversions),
            'conversion_rate': float(conversion_rate),
            'standard_error': float(se),
            'ci_lower': float(max(0, conversion_rate - ci_margin)),
            'ci_upper': float(min(1, conversion_rate + ci_margin))
        }
    
    return results

def calculate_latency_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    results = {}
    
    for variant in df['variant'].unique():
        variant_data = df[df['variant'] == variant]
        latencies = variant_data['latency_ms']
        
        n = len(latencies)
        mean_latency = latencies.mean()
        std_latency = latencies.std()
        se = std_latency / np.sqrt(n) if n > 0 else 0
        ci_margin = 1.96 * se
        
        results[variant] = {
            'sample_size': int(n),
            'mean_latency': float(mean_latency),
            'std_latency': float(std_latency),
            'median_latency': float(latencies.median()),
            'p50': float(latencies.quantile(0.50)),
            'p95': float(latencies.quantile(0.95)),
            'p99': float(latencies.quantile(0.99)),
            'ci_lower': float(mean_latency - ci_margin),
            'ci_upper': float(mean_latency + ci_margin)
        }
    
    return results

def perform_chi_square_test(df: pd.DataFrame) -> Dict[str, Any]:
    contingency_table = pd.crosstab(df['variant'], df['conversion'])
    
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    
    return {
        'test_name': 'Chi-Square Test for Conversion',
        'chi2_statistic': float(chi2),
        'p_value': float(p_value),
        'degrees_of_freedom': int(dof),
        'is_significant': bool(p_value < 0.05),
        'contingency_table': contingency_table.to_dict()
    }

def perform_t_test(df: pd.DataFrame) -> Dict[str, Any]:
    model_a_latency = df[df['variant'] == 'model_a']['latency_ms']
    model_b_latency = df[df['variant'] == 'model_b']['latency_ms']
    
    t_stat, p_value = ttest_ind(model_a_latency, model_b_latency)
    
    mean_diff = model_a_latency.mean() - model_b_latency.mean()
    pooled_std = np.sqrt((model_a_latency.var() + model_b_latency.var()) / 2)
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
    
    return {
        'test_name': 'Independent T-Test for Latency',
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'mean_difference': float(mean_diff),
        'cohens_d': float(cohens_d),
        'is_significant': bool(p_value < 0.05)
    }

def determine_winner(conversion_metrics: Dict, latency_metrics: Dict, 
                     chi_square_result: Dict, t_test_result: Dict) -> Dict[str, Any]:
    
    model_a_conv = conversion_metrics['model_a']['conversion_rate']
    model_b_conv = conversion_metrics['model_b']['conversion_rate']
    
    model_a_lat = latency_metrics['model_a']['mean_latency']
    model_b_lat = latency_metrics['model_b']['mean_latency']
    
    conversion_winner = None
    latency_winner = None
    
    if chi_square_result['is_significant']:
        conversion_winner = 'model_b' if model_b_conv > model_a_conv else 'model_a'
        conv_lift = ((model_b_conv - model_a_conv) / model_a_conv * 100) if conversion_winner == 'model_b' else ((model_a_conv - model_b_conv) / model_b_conv * 100)
    else:
        conv_lift = 0
    
    if t_test_result['is_significant']:
        latency_winner = 'model_b' if model_b_lat < model_a_lat else 'model_a'
        lat_improvement = ((model_a_lat - model_b_lat) / model_a_lat * 100) if latency_winner == 'model_b' else ((model_b_lat - model_a_lat) / model_b_lat * 100)
    else:
        lat_improvement = 0
    
    overall_winner = None
    recommendation = ""
    
    if conversion_winner and latency_winner:
        if conversion_winner == latency_winner:
            overall_winner = conversion_winner
            recommendation = f"{overall_winner.replace('_', ' ').title()} is the clear winner with significantly better conversion rate (+{conv_lift:.2f}%) and latency (-{lat_improvement:.2f}%)."
        else:
            overall_winner = conversion_winner
            recommendation = f"{conversion_winner.replace('_', ' ').title()} wins on conversion (+{conv_lift:.2f}%), but {latency_winner.replace('_', ' ').title()} has better latency. Recommend {conversion_winner.replace('_', ' ').title()} as conversion is typically more critical."
    elif conversion_winner:
        overall_winner = conversion_winner
        recommendation = f"{conversion_winner.replace('_', ' ').title()} is the winner with significantly better conversion rate (+{conv_lift:.2f}%). Latency difference is not statistically significant."
    elif latency_winner:
        overall_winner = latency_winner
        recommendation = f"{latency_winner.replace('_', ' ').title()} has significantly better latency (-{lat_improvement:.2f}%), but conversion rates are similar. Consider business priorities."
    else:
        recommendation = "No significant differences detected between models. Either model can be selected, or continue testing with larger sample size."
    
    return {
        'overall_winner': overall_winner,
        'conversion_winner': conversion_winner,
        'latency_winner': latency_winner,
        'recommendation': recommendation
    }

def run_analysis():
    print("Loading experiment data...")
    df = load_experiment_data('/root/AB_testing/data/experiment_logs.csv')
    
    print(f"Total records: {len(df)}")
    print(f"\nTraffic distribution:")
    print(df['variant'].value_counts())
    
    print("\n" + "="*60)
    print("SANITY CHECK: Sample Sizes")
    print("="*60)
    variant_counts = df['variant'].value_counts()
    for variant, count in variant_counts.items():
        print(f"{variant}: {count} ({count/len(df)*100:.1f}%)")
    
    print("\n" + "="*60)
    print("CONVERSION METRICS")
    print("="*60)
    conversion_metrics = calculate_conversion_metrics(df)
    for variant, metrics in conversion_metrics.items():
        print(f"\n{variant.upper()}:")
        print(f"  Sample Size: {metrics['sample_size']}")
        print(f"  Conversions: {metrics['conversions']}")
        print(f"  Conversion Rate: {metrics['conversion_rate']:.4f} ({metrics['conversion_rate']*100:.2f}%)")
        print(f"  95% CI: [{metrics['ci_lower']:.4f}, {metrics['ci_upper']:.4f}]")
    
    print("\n" + "="*60)
    print("LATENCY METRICS")
    print("="*60)
    latency_metrics = calculate_latency_metrics(df)
    for variant, metrics in latency_metrics.items():
        print(f"\n{variant.upper()}:")
        print(f"  Sample Size: {metrics['sample_size']}")
        print(f"  Mean Latency: {metrics['mean_latency']:.2f} ms")
        print(f"  Median Latency: {metrics['median_latency']:.2f} ms")
        print(f"  Std Dev: {metrics['std_latency']:.2f} ms")
        print(f"  95% CI: [{metrics['ci_lower']:.2f}, {metrics['ci_upper']:.2f}]")
        print(f"  P95: {metrics['p95']:.2f} ms")
        print(f"  P99: {metrics['p99']:.2f} ms")
    
    print("\n" + "="*60)
    print("STATISTICAL TESTS")
    print("="*60)
    
    chi_square_result = perform_chi_square_test(df)
    print(f"\n{chi_square_result['test_name']}:")
    print(f"  Chi-Square Statistic: {chi_square_result['chi2_statistic']:.4f}")
    print(f"  P-value: {chi_square_result['p_value']:.6f}")
    print(f"  Significant (α=0.05): {chi_square_result['is_significant']}")
    
    t_test_result = perform_t_test(df)
    print(f"\n{t_test_result['test_name']}:")
    print(f"  T-Statistic: {t_test_result['t_statistic']:.4f}")
    print(f"  P-value: {t_test_result['p_value']:.6f}")
    print(f"  Mean Difference: {t_test_result['mean_difference']:.2f} ms")
    print(f"  Cohen's d (Effect Size): {t_test_result['cohens_d']:.4f}")
    print(f"  Significant (α=0.05): {t_test_result['is_significant']}")
    
    print("\n" + "="*60)
    print("FINAL RECOMMENDATION")
    print("="*60)
    winner_analysis = determine_winner(conversion_metrics, latency_metrics, 
                                       chi_square_result, t_test_result)
    print(f"\nOverall Winner: {winner_analysis['overall_winner'] or 'Inconclusive'}")
    print(f"\nRecommendation:\n{winner_analysis['recommendation']}")
    
    results = {
        'experiment_summary': {
            'total_requests': int(len(df)),
            'traffic_distribution': {k: int(v) for k, v in variant_counts.items()}
        },
        'conversion_metrics': conversion_metrics,
        'latency_metrics': latency_metrics,
        'statistical_tests': {
            'chi_square_test': chi_square_result,
            't_test': t_test_result
        },
        'winner_analysis': winner_analysis
    }
    
    output_path = Path('/root/AB_testing/results/analysis_summary.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_path}")

if __name__ == "__main__":
    run_analysis()