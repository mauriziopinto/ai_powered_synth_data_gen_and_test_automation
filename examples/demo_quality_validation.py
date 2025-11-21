"""Demo of Quality Validation for Synthetic Data."""

import pandas as pd
import numpy as np
from pathlib import Path

from shared.utils.quality_validator import QualityValidator


def create_sample_data():
    """Create sample real and synthetic data for demo."""
    np.random.seed(42)
    
    # Real data - simulating production data
    n_real = 1000
    real_data = pd.DataFrame({
        'customer_id': range(1, n_real + 1),
        'age': np.random.normal(45, 15, n_real).clip(18, 90).astype(int),
        'income': np.random.lognormal(10.5, 0.5, n_real).clip(20000, 200000),
        'credit_score': np.random.normal(700, 100, n_real).clip(300, 850).astype(int),
        'account_balance': np.random.exponential(5000, n_real).clip(0, 50000),
        'num_transactions': np.random.poisson(25, n_real),
        'account_type': np.random.choice(['Checking', 'Savings', 'Premium'], n_real, p=[0.5, 0.3, 0.2]),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_real),
        'is_active': np.random.choice([True, False], n_real, p=[0.85, 0.15])
    })
    
    # Add some correlations
    real_data['income'] = real_data['income'] + real_data['age'] * 500
    real_data['credit_score'] = (real_data['credit_score'] + 
                                  real_data['income'] / 500).clip(300, 850).astype(int)
    
    # Synthetic data - good quality (similar distributions)
    n_synth = 1000
    synthetic_good = pd.DataFrame({
        'customer_id': range(10001, 10001 + n_synth),
        'age': np.random.normal(45, 15, n_synth).clip(18, 90).astype(int),
        'income': np.random.lognormal(10.5, 0.5, n_synth).clip(20000, 200000),
        'credit_score': np.random.normal(700, 100, n_synth).clip(300, 850).astype(int),
        'account_balance': np.random.exponential(5000, n_synth).clip(0, 50000),
        'num_transactions': np.random.poisson(25, n_synth),
        'account_type': np.random.choice(['Checking', 'Savings', 'Premium'], n_synth, p=[0.5, 0.3, 0.2]),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_synth),
        'is_active': np.random.choice([True, False], n_synth, p=[0.85, 0.15])
    })
    
    # Preserve correlations
    synthetic_good['income'] = synthetic_good['income'] + synthetic_good['age'] * 500
    synthetic_good['credit_score'] = (synthetic_good['credit_score'] + 
                                       synthetic_good['income'] / 500).clip(300, 850).astype(int)
    
    # Synthetic data - poor quality (different distributions)
    synthetic_poor = pd.DataFrame({
        'customer_id': range(20001, 20001 + n_synth),
        'age': np.random.normal(35, 20, n_synth).clip(18, 90).astype(int),  # Different mean/std
        'income': np.random.lognormal(11.0, 0.8, n_synth).clip(20000, 200000),  # Different distribution
        'credit_score': np.random.normal(650, 150, n_synth).clip(300, 850).astype(int),  # Different mean/std
        'account_balance': np.random.exponential(8000, n_synth).clip(0, 50000),  # Different scale
        'num_transactions': np.random.poisson(15, n_synth),  # Different rate
        'account_type': np.random.choice(['Checking', 'Savings', 'Premium'], n_synth, p=[0.3, 0.5, 0.2]),  # Different distribution
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_synth),
        'is_active': np.random.choice([True, False], n_synth, p=[0.7, 0.3])  # Different distribution
    })
    
    # No correlation preservation
    
    return real_data, synthetic_good, synthetic_poor


def demo_good_quality():
    """Demo: High quality synthetic data validation."""
    print("\n" + "="*80)
    print("DEMO 1: High Quality Synthetic Data")
    print("="*80)
    
    real_data, synthetic_good, _ = create_sample_data()
    
    print(f"\n📊 Real Data: {len(real_data)} records")
    print(f"📊 Synthetic Data: {len(synthetic_good)} records")
    
    # Create validator
    validator = QualityValidator(output_dir=Path('results/quality_good'))
    
    print("\n🔍 Validating synthetic data quality...")
    report = validator.validate(real_data, synthetic_good)
    
    print("\n" + "="*80)
    print("QUALITY METRICS")
    print("="*80)
    print(report.metrics.get_summary())
    
    print("\n" + "="*80)
    print("DATA SUMMARIES")
    print("="*80)
    print(f"\nReal Data:")
    for key, value in report.real_data_summary.items():
        print(f"  {key}: {value}")
    
    print(f"\nSynthetic Data:")
    for key, value in report.synthetic_data_summary.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    print("STATISTICAL TESTS")
    print("="*80)
    
    # KS Tests
    print("\n📈 Kolmogorov-Smirnov Tests (numeric columns):")
    for col, result in list(report.metrics.ks_tests.items())[:5]:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {col}: {status} (p-value: {result['pvalue']:.4f})")
    
    # Chi-Squared Tests
    if report.metrics.chi_squared_tests:
        print("\n📊 Chi-Squared Tests (categorical columns):")
        for col, result in report.metrics.chi_squared_tests.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {col}: {status} (p-value: {result['pvalue']:.4f})")
    
    # Wasserstein Distances
    print("\n📏 Wasserstein Distances (lower is better):")
    for col, distance in list(report.metrics.wasserstein_distances.items())[:5]:
        print(f"  {col}: {distance:.2f}")
    
    if report.warnings:
        print("\n" + "="*80)
        print("⚠️  WARNINGS")
        print("="*80)
        for warning in report.warnings:
            print(f"  • {warning}")
    
    if report.recommendations:
        print("\n" + "="*80)
        print("💡 RECOMMENDATIONS")
        print("="*80)
        for rec in report.recommendations:
            print(f"  • {rec}")
    
    print("\n" + "="*80)
    print("📁 VISUALIZATIONS")
    print("="*80)
    for viz_type, path in report.metrics.visualizations.items():
        print(f"  {viz_type}: {path}")
    
    print("\n✅ High quality synthetic data validated successfully!")


def demo_poor_quality():
    """Demo: Low quality synthetic data validation."""
    print("\n" + "="*80)
    print("DEMO 2: Low Quality Synthetic Data")
    print("="*80)
    
    real_data, _, synthetic_poor = create_sample_data()
    
    print(f"\n📊 Real Data: {len(real_data)} records")
    print(f"📊 Synthetic Data: {len(synthetic_poor)} records")
    
    # Create validator
    validator = QualityValidator(output_dir=Path('results/quality_poor'))
    
    print("\n🔍 Validating synthetic data quality...")
    report = validator.validate(real_data, synthetic_poor)
    
    print("\n" + "="*80)
    print("QUALITY METRICS")
    print("="*80)
    print(report.metrics.get_summary())
    
    print("\n" + "="*80)
    print("STATISTICAL TESTS")
    print("="*80)
    
    # KS Tests
    print("\n📈 Kolmogorov-Smirnov Tests (numeric columns):")
    for col, result in list(report.metrics.ks_tests.items())[:5]:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {col}: {status} (p-value: {result['pvalue']:.4f})")
    
    # Chi-Squared Tests
    if report.metrics.chi_squared_tests:
        print("\n📊 Chi-Squared Tests (categorical columns):")
        for col, result in report.metrics.chi_squared_tests.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {col}: {status} (p-value: {result['pvalue']:.4f})")
    
    if report.warnings:
        print("\n" + "="*80)
        print("⚠️  WARNINGS")
        print("="*80)
        for warning in report.warnings:
            print(f"  • {warning}")
    
    if report.recommendations:
        print("\n" + "="*80)
        print("💡 RECOMMENDATIONS")
        print("="*80)
        for rec in report.recommendations:
            print(f"  • {rec}")
    
    print("\n" + "="*80)
    print("📁 VISUALIZATIONS")
    print("="*80)
    for viz_type, path in report.metrics.visualizations.items():
        print(f"  {viz_type}: {path}")
    
    print("\n⚠️  Low quality synthetic data detected - see warnings above!")


def demo_comparison():
    """Demo: Side-by-side comparison of good vs poor quality."""
    print("\n" + "="*80)
    print("DEMO 3: Quality Comparison")
    print("="*80)
    
    real_data, synthetic_good, synthetic_poor = create_sample_data()
    
    validator = QualityValidator()
    
    print("\n🔍 Validating both synthetic datasets...")
    report_good = validator.validate(real_data, synthetic_good)
    report_poor = validator.validate(real_data, synthetic_poor)
    
    print("\n" + "="*80)
    print("QUALITY COMPARISON")
    print("="*80)
    
    metrics = [
        ('Overall Quality Score', 'sdv_quality_score'),
        ('Correlation Preservation', 'correlation_preservation'),
        ('Edge Case Frequency Match', 'edge_case_frequency_match')
    ]
    
    print(f"\n{'Metric':<30} {'Good Quality':<15} {'Poor Quality':<15} {'Difference':<15}")
    print("-" * 75)
    
    for name, attr in metrics:
        good_val = getattr(report_good.metrics, attr)
        poor_val = getattr(report_poor.metrics, attr)
        diff = good_val - poor_val
        
        print(f"{name:<30} {good_val:>14.3f} {poor_val:>14.3f} {diff:>+14.3f}")
    
    print("\n" + "="*80)
    print("STATISTICAL TEST PASS RATES")
    print("="*80)
    
    # KS test pass rate
    good_ks_pass = sum(1 for r in report_good.metrics.ks_tests.values() if r['passed'])
    good_ks_total = len(report_good.metrics.ks_tests)
    poor_ks_pass = sum(1 for r in report_poor.metrics.ks_tests.values() if r['passed'])
    poor_ks_total = len(report_poor.metrics.ks_tests)
    
    print(f"\nKS Tests:")
    print(f"  Good Quality: {good_ks_pass}/{good_ks_total} passed ({good_ks_pass/good_ks_total*100:.1f}%)")
    print(f"  Poor Quality: {poor_ks_pass}/{poor_ks_total} passed ({poor_ks_pass/poor_ks_total*100:.1f}%)")
    
    # Chi-squared test pass rate
    if report_good.metrics.chi_squared_tests:
        good_chi_pass = sum(1 for r in report_good.metrics.chi_squared_tests.values() if r['passed'])
        good_chi_total = len(report_good.metrics.chi_squared_tests)
        poor_chi_pass = sum(1 for r in report_poor.metrics.chi_squared_tests.values() if r['passed'])
        poor_chi_total = len(report_poor.metrics.chi_squared_tests)
        
        print(f"\nChi-Squared Tests:")
        print(f"  Good Quality: {good_chi_pass}/{good_chi_total} passed ({good_chi_pass/good_chi_total*100:.1f}%)")
        print(f"  Poor Quality: {poor_chi_pass}/{poor_chi_total} passed ({poor_chi_pass/poor_chi_total*100:.1f}%)")
    
    print("\n✅ Comparison complete!")


def main():
    """Run all quality validation demos."""
    print("\n" + "="*80)
    print("QUALITY VALIDATION DEMO")
    print("="*80)
    print("\nThis demo shows how to validate synthetic data quality using")
    print("statistical tests, correlation analysis, and visualizations.")
    
    demo_good_quality()
    demo_poor_quality()
    demo_comparison()
    
    print("\n" + "="*80)
    print("✅ All quality validation demos completed!")
    print("="*80)
    print("\n💡 Key Features Demonstrated:")
    print("   • Overall quality scoring")
    print("   • Statistical tests (KS, Chi-squared, Wasserstein)")
    print("   • Correlation preservation analysis")
    print("   • Edge case frequency matching")
    print("   • Automated warnings and recommendations")
    print("   • Visualization generation (histograms, heatmaps, Q-Q plots)")
    print("\n📁 Check the results/ directory for generated visualizations!")


if __name__ == '__main__':
    main()
