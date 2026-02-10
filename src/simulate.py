import sys
import os
import yaml
import time
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ModelA, ModelB
from ab_core import Router, AsyncLogger

def generate_user_ids(num_users: int) -> List[str]:
    return [f"user_{i:06d}" for i in range(num_users)]

def run_simulation(num_requests: int = 2000):
    print(f"Starting A/B test simulation with {num_requests} requests...")
    
    config_path = "/root/AB_testing/experiment_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    traffic_split = config['experiment']['traffic_split']
    router = Router(traffic_split)
    logger = AsyncLogger("/root/AB_testing/data/experiment_logs.csv", buffer_size=50)
    
    model_a = ModelA()
    model_b = ModelB()
    
    models = {
        "model_a": model_a,
        "model_b": model_b
    }
    
    user_ids = generate_user_ids(num_requests)
    
    variant_counts = {"model_a": 0, "model_b": 0}
    
    for i, user_id in enumerate(user_ids):
        variant = router.assign_variant(user_id)
        variant_counts[variant] += 1
        
        model = models[variant]
        result = model.predict(user_id)
        
        logger.log(user_id, variant, result)
        
        if (i + 1) % 500 == 0:
            print(f"Processed {i + 1}/{num_requests} requests")
    
    print("\nSimulation complete!")
    print(f"Traffic distribution:")
    print(f"  Model A: {variant_counts['model_a']} ({variant_counts['model_a']/num_requests*100:.1f}%)")
    print(f"  Model B: {variant_counts['model_b']} ({variant_counts['model_b']/num_requests*100:.1f}%)")
    
    time.sleep(2)
    logger.close()
    
    print(f"\nData logged to: /root/AB_testing/data/experiment_logs.csv")

if __name__ == "__main__":
    run_simulation(2000)