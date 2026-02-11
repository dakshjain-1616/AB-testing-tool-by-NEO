import sys
import os
import yaml
import time
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import get_model_registry
from ab_core import Router, AsyncLogger

def generate_user_ids(num_users: int) -> List[str]:
    return [f"user_{i:06d}" for i in range(num_users)]

def run_simulation(num_requests: int = 2000):
    print(f"Starting Multi-Variant test simulation with {num_requests} requests...")
    
    config_path = "/root/AB_testing/experiment_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    traffic_split = config['experiment']['traffic_split']
    
    print(f"\nConfigured traffic split: {traffic_split}")
    print(f"Total weight: {sum(traffic_split.values()):.4f}")
    
    router = Router(traffic_split)
    logger = AsyncLogger("/root/AB_testing/data/experiment_logs.csv", buffer_size=50)
    
    models = get_model_registry()
    
    available_variants = list(traffic_split.keys())
    for variant in available_variants:
        if variant not in models:
            raise ValueError(f"Variant '{variant}' not found in model registry. Available: {list(models.keys())}")
    
    user_ids = generate_user_ids(num_requests)
    
    variant_counts = {variant: 0 for variant in available_variants}
    
    for i, user_id in enumerate(user_ids):
        variant = router.assign_variant(user_id)
        variant_counts[variant] += 1
        
        model = models[variant]
        result = model.predict(user_id)
        
        logger.log(user_id, variant, result)
        
        if (i + 1) % 500 == 0:
            print(f"Processed {i + 1}/{num_requests} requests")
    
    print("\nSimulation complete!")
    print(f"\nActual traffic distribution:")
    for variant in sorted(variant_counts.keys()):
        count = variant_counts[variant]
        expected = traffic_split[variant] * num_requests
        diff = abs(count - expected) / expected * 100 if expected > 0 else 0
        print(f"  {variant}: {count} ({count/num_requests*100:.1f}%) [Expected: {expected:.0f}, Diff: {diff:.2f}%]")
    
    time.sleep(2)
    logger.close()
    
    print(f"\nData logged to: /root/AB_testing/data/experiment_logs.csv")

if __name__ == "__main__":
    run_simulation(2000)