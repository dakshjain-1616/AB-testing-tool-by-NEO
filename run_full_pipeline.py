import sys
import os
import subprocess

os.chdir('/root/AB_testing')

print("="*70)
print("MULTI-VARIANT A/B/N TESTING FRAMEWORK - FULL PIPELINE")
print("="*70)

python_exec = '/root/AB_testing/venv/bin/python3'

print("\n[Step 1/3] Running simulation with 3 variants...")
print("-"*70)
result = subprocess.run([python_exec, 'src/simulate.py'], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"ERROR: {result.stderr}")
    sys.exit(1)

print("\n[Step 2/3] Running statistical analysis...")
print("-"*70)
result = subprocess.run([python_exec, 'src/analysis.py'], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"ERROR: {result.stderr}")
    sys.exit(1)

print("\n[Step 3/3] Generating visualizations...")
print("-"*70)
result = subprocess.run([python_exec, 'src/report_viz.py'], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"ERROR: {result.stderr}")
    sys.exit(1)

print("\n" + "="*70)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("="*70)
print("\nGenerated artifacts:")
print("  - Data: /root/AB_testing/data/experiment_logs.csv")
print("  - Analysis: /root/AB_testing/results/analysis_summary.json")
print("  - Visualizations: /root/AB_testing/results/*.png")