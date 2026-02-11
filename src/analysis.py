import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, f_oneway
from itertools import combinations
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

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

def perform_anova_test(df: pd.DataFrame) -> Dict[str, Any]:
    variants = df['variant'].unique()
    groups = [df[df['variant'] == v]['latency_ms'].values for v in variants]
    
    f_stat, p_value = f_oneway(*groups)
    
    return {
        'test_name': 'One-Way ANOVA for Latency',
        'f_statistic': float(f_stat),
        'p_value': float(p_value),
        'is_significant': bool(p_value < 0.05),
        'num_groups': len(variants)
    }

def perform_pairwise_t_tests(df: pd.DataFrame, baseline: str = None, 
                              correction: str = 'bonferroni') -> Dict[str, Any]:
    variants = sorted(df['variant'].unique())
    
    if baseline and baseline in variants:
        comparisons = [(baseline, v) for v in variants if v != baseline]
    else:
        comparisons = list(combinations(variants, 2))
    
    results = {}
    p_values = []
    
    for var1, var2 in comparisons:
        group1 = df[df['variant'] == var1]['latency_ms']
        group2 = df[df['variant'] == var2]['latency_ms']
        
        t_stat, p_value = ttest_ind(group1, group2)
        
        mean_diff = group1.mean() - group2.mean()
        pooled_std = np.sqrt((group1.var() + group2.var()) / 2)
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
        
        comparison_key = f"{var1}_vs_{var2}"
        results[comparison_key] = {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'mean_difference': float(mean_diff),
            'cohens_d': float(cohens_d)
        }
        p_values.append(p_value)
    
    if correction == 'bonferroni' and len(p_values) > 0:
        adjusted_alpha = 0.05 / len(comparisons)
        for comp_key in results:
            results[comp_key]['adjusted_alpha'] = float(adjusted_alpha)
            results[comp_key]['is_significant'] = bool(
                results[comp_key]['p_value'] < adjusted_alpha
            )
    else:
        for comp_key in results:
            results[comp_key]['is_significant'] = bool(
                results[comp_key]['p_value'] < 0.05
            )
    
    return {
        'test_name': f'Pairwise T-Tests with {correction.title()} Correction',
        'num_comparisons': len(comparisons),
        'comparisons': results,
        'correction_method': correction
    }

def perform_pairwise_proportion_tests(df: pd.DataFrame, baseline: str = None,
                                       correction: str = 'bonferroni') -> Dict[str, Any]:
    variants = sorted(df['variant'].unique())
    
    if baseline and baseline in variants:
        comparisons = [(baseline, v) for v in variants if v != baseline]
    else:
        comparisons = list(combinations(variants, 2))
    
    results = {}
    p_values = []
    
    for var1, var2 in comparisons:
        group1 = df[df['variant'] == var1]
        group2 = df[df['variant'] == var2]
        
        n1 = len(group1)
        n2 = len(group2)
        x1 = group1['conversion'].sum()
        x2 = group2['conversion'].sum()
        
        p1 = x1 / n1 if n1 > 0 else 0
        p2 = x2 / n2 if n2 > 0 else 0
        p_pooled = (x1 + x2) / (n1 + n2) if (n1 + n2) > 0 else 0
        
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2)) if p_pooled > 0 else 1e-10
        z_stat = (p1 - p2) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        relative_lift = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
        
        comparison_key = f"{var1}_vs_{var2}"
        results[comparison_key] = {
            'z_statistic': float(z_stat),
            'p_value': float(p_value),
            'conversion_diff': float(p2 - p1),
            'relative_lift_pct': float(relative_lift)
        }
        p_values.append(p_value)
    
    if correction == 'bonferroni' and len(p_values) > 0:
        adjusted_alpha = 0.05 / len(comparisons)
        for comp_key in results:
            results[comp_key]['adjusted_alpha'] = float(adjusted_alpha)
            results[comp_key]['is_significant'] = bool(
                results[comp_key]['p_value'] < adjusted_alpha
            )
    else:
        for comp_key in results:
            results[comp_key]['is_significant'] = bool(
                results[comp_key]['p_value'] < 0.05
            )
    
    return {
        'test_name': f'Pairwise Proportion Tests with {correction.title()} Correction',
        'num_comparisons': len(comparisons),
        'comparisons': results,
        'correction_method': correction
    }

def determine_winner_multivariant(conversion_metrics: Dict, latency_metrics: Dict,
                                   chi_square_result: Dict, anova_result: Dict,
                                   pairwise_conversion: Dict, pairwise_latency: Dict,
                                   baseline: str = 'baseline') -> Dict[str, Any]:
    
    variants = list(conversion_metrics.keys())
    
    conversion_winner = None
    latency_winner = None
    overall_winner = None
    
    if chi_square_result['is_significant']:
        best_conversion_rate = max(
            [(v, conversion_metrics[v]['conversion_rate']) for v in variants],
            key=lambda x: x[1]
        )
        conversion_winner = best_conversion_rate[0]
        
        if baseline in variants:
            baseline_vs_winner = f"{baseline}_vs_{conversion_winner}"
            winner_vs_baseline = f"{conversion_winner}_vs_{baseline}"
            
            if baseline_vs_winner in pairwise_conversion['comparisons']:
                is_sig = pairwise_conversion['comparisons'][baseline_vs_winner]['is_significant']
            elif winner_vs_baseline in pairwise_conversion['comparisons']:
                is_sig = pairwise_conversion['comparisons'][winner_vs_baseline]['is_significant']
            else:
                is_sig = False
            
            if not is_sig and conversion_winner != baseline:
                conversion_winner = None
    
    if anova_result['is_significant']:
        best_latency = min(
            [(v, latency_metrics[v]['mean_latency']) for v in variants],
            key=lambda x: x[1]
        )
        latency_winner = best_latency[0]
        
        if baseline in variants:
            baseline_vs_winner = f"{baseline}_vs_{latency_winner}"
            winner_vs_baseline = f"{latency_winner}_vs_{baseline}"
            
            if baseline_vs_winner in pairwise_latency['comparisons']:
                is_sig = pairwise_latency['comparisons'][baseline_vs_winner]['is_significant']
            elif winner_vs_baseline in pairwise_latency['comparisons']:
                is_sig = pairwise_latency['comparisons'][winner_vs_baseline]['is_significant']
            else:
                is_sig = False
            
            if not is_sig and latency_winner != baseline:
                latency_winner = None
    
    recommendation_parts = []
    
    if conversion_winner:
        conv_rate = conversion_metrics[conversion_winner]['conversion_rate']
        baseline_conv = conversion_metrics.get(baseline, {}).get('conversion_rate', 0)
        
        if baseline in variants and conversion_winner != baseline:
            lift = ((conv_rate - baseline_conv) / baseline_conv * 100) if baseline_conv > 0 else 0
            recommendation_parts.append(
                f"{conversion_winner.replace('_', ' ').title()} shows significantly better conversion "
                f"rate ({conv_rate*100:.2f}%) with +{lift:.2f}% lift over baseline"
            )
            overall_winner = conversion_winner
        else:
            recommendation_parts.append(
                f"{conversion_winner.replace('_', ' ').title()} has the best conversion rate ({conv_rate*100:.2f}%)"
            )
            overall_winner = conversion_winner
    
    if latency_winner:
        lat = latency_metrics[latency_winner]['mean_latency']
        baseline_lat = latency_metrics.get(baseline, {}).get('mean_latency', float('inf'))
        
        if baseline in variants and latency_winner != baseline:
            improvement = ((baseline_lat - lat) / baseline_lat * 100) if baseline_lat > 0 else 0
            recommendation_parts.append(
                f"{latency_winner.replace('_', ' ').title()} has significantly better latency "
                f"({lat:.2f}ms) with {improvement:.2f}% improvement over baseline"
            )
            if not overall_winner:
                overall_winner = latency_winner
        else:
            recommendation_parts.append(
                f"{latency_winner.replace('_', ' ').title()} has the best latency ({lat:.2f}ms)"
            )
            if not overall_winner:
                overall_winner = latency_winner
    
    if not recommendation_parts:
        recommendation_parts.append(
            "No statistically significant differences detected across variants. "
            "Consider increasing sample size or continuing the experiment."
        )
    
    recommendation = " ".join(recommendation_parts)
    
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
    
    variants = sorted(df['variant'].unique())
    baseline = 'baseline' if 'baseline' in variants else variants[0]
    
    print("\n" + "="*60)
    print("SANITY CHECK: Sample Sizes")
    print("="*60)
    variant_counts = df['variant'].value_counts()
    for variant in variants:
        count = variant_counts[variant]
        print(f"{variant}: {count} ({count/len(df)*100:.1f}%)")
    
    print("\n" + "="*60)
    print("CONVERSION METRICS")
    print("="*60)
    conversion_metrics = calculate_conversion_metrics(df)
    for variant in variants:
        metrics = conversion_metrics[variant]
        print(f"\n{variant.upper()}:")
        print(f"  Sample Size: {metrics['sample_size']}")
        print(f"  Conversions: {metrics['conversions']}")
        print(f"  Conversion Rate: {metrics['conversion_rate']:.4f} ({metrics['conversion_rate']*100:.2f}%)")
        print(f"  95% CI: [{metrics['ci_lower']:.4f}, {metrics['ci_upper']:.4f}]")
    
    print("\n" + "="*60)
    print("LATENCY METRICS")
    print("="*60)
    latency_metrics = calculate_latency_metrics(df)
    for variant in variants:
        metrics = latency_metrics[variant]
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
    
    anova_result = perform_anova_test(df)
    print(f"\n{anova_result['test_name']}:")
    print(f"  F-Statistic: {anova_result['f_statistic']:.4f}")
    print(f"  P-value: {anova_result['p_value']:.6f}")
    print(f"  Significant (α=0.05): {anova_result['is_significant']}")
    
    pairwise_conversion = perform_pairwise_proportion_tests(df, baseline=baseline)
    print(f"\n{pairwise_conversion['test_name']}:")
    for comp_key, comp_result in pairwise_conversion['comparisons'].items():
        print(f"  {comp_key}:")
        print(f"    P-value: {comp_result['p_value']:.6f}")
        print(f"    Relative Lift: {comp_result['relative_lift_pct']:.2f}%")
        print(f"    Significant: {comp_result['is_significant']}")
    
    pairwise_latency = perform_pairwise_t_tests(df, baseline=baseline)
    print(f"\n{pairwise_latency['test_name']}:")
    for comp_key, comp_result in pairwise_latency['comparisons'].items():
        print(f"  {comp_key}:")
        print(f"    P-value: {comp_result['p_value']:.6f}")
        print(f"    Mean Difference: {comp_result['mean_difference']:.2f} ms")
        print(f"    Cohen's d: {comp_result['cohens_d']:.4f}")
        print(f"    Significant: {comp_result['is_significant']}")
    
    print("\n" + "="*60)
    print("FINAL RECOMMENDATION")
    print("="*60)
    winner_analysis = determine_winner_multivariant(
        conversion_metrics, latency_metrics,
        chi_square_result, anova_result,
        pairwise_conversion, pairwise_latency,
        baseline=baseline
    )
    print(f"\nOverall Winner: {winner_analysis['overall_winner'] or 'Inconclusive'}")
    print(f"\nRecommendation:\n{winner_analysis['recommendation']}")
    
    results = {
        'experiment_summary': {
            'total_requests': int(len(df)),
            'num_variants': len(variants),
            'baseline_variant': baseline,
            'traffic_distribution': {k: int(v) for k, v in variant_counts.items()}
        },
        'conversion_metrics': conversion_metrics,
        'latency_metrics': latency_metrics,
        'statistical_tests': {
            'chi_square_test': chi_square_result,
            'anova_test': anova_result,
            'pairwise_conversion_tests': pairwise_conversion,
            'pairwise_latency_tests': pairwise_latency
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