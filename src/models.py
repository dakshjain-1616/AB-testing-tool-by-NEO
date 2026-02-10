import time
import random
from typing import Dict, Any

class ModelA:
    def __init__(self):
        self.name = "Model_A"
        self.conversion_rate = 0.10
        self.base_latency_ms = 50
        self.latency_std = 10
    
    def predict(self, user_id: str, features: Dict[str, Any] = None) -> Dict[str, Any]:
        random.seed(hash(user_id + self.name) % (2**32))
        
        conversion = random.random() < self.conversion_rate
        latency = max(1, random.gauss(self.base_latency_ms, self.latency_std))
        
        return {
            "conversion": conversion,
            "latency_ms": latency,
            "model_version": self.name
        }


class ModelB:
    def __init__(self):
        self.name = "Model_B"
        self.conversion_rate = 0.12
        self.base_latency_ms = 48
        self.latency_std = 10
    
    def predict(self, user_id: str, features: Dict[str, Any] = None) -> Dict[str, Any]:
        random.seed(hash(user_id + self.name) % (2**32))
        
        conversion = random.random() < self.conversion_rate
        latency = max(1, random.gauss(self.base_latency_ms, self.latency_std))
        
        return {
            "conversion": conversion,
            "latency_ms": latency,
            "model_version": self.name
        }