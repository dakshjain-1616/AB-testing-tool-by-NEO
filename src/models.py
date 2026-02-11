import time
import random
from typing import Dict, Any

class BaseModel:
    def __init__(self, name: str, conversion_rate: float, base_latency_ms: float, latency_std: float = 10):
        self.name = name
        self.conversion_rate = conversion_rate
        self.base_latency_ms = base_latency_ms
        self.latency_std = latency_std
    
    def predict(self, user_id: str, features: Dict[str, Any] = None) -> Dict[str, Any]:
        random.seed(hash(user_id + self.name) % (2**32))
        
        conversion = random.random() < self.conversion_rate
        latency = max(1, random.gauss(self.base_latency_ms, self.latency_std))
        
        return {
            "conversion": conversion,
            "latency_ms": latency,
            "model_version": self.name
        }


class ModelBaseline(BaseModel):
    def __init__(self):
        super().__init__(
            name="Baseline",
            conversion_rate=0.10,
            base_latency_ms=50,
            latency_std=10
        )


class ModelVariantA(BaseModel):
    def __init__(self):
        super().__init__(
            name="Variant_A",
            conversion_rate=0.12,
            base_latency_ms=48,
            latency_std=10
        )


class ModelVariantB(BaseModel):
    def __init__(self):
        super().__init__(
            name="Variant_B",
            conversion_rate=0.115,
            base_latency_ms=52,
            latency_std=12
        )


class ModelA(BaseModel):
    def __init__(self):
        super().__init__(
            name="Model_A",
            conversion_rate=0.10,
            base_latency_ms=50,
            latency_std=10
        )


class ModelB(BaseModel):
    def __init__(self):
        super().__init__(
            name="Model_B",
            conversion_rate=0.12,
            base_latency_ms=48,
            latency_std=10
        )


def get_model_registry() -> Dict[str, BaseModel]:
    return {
        "baseline": ModelBaseline(),
        "variant_a": ModelVariantA(),
        "variant_b": ModelVariantB(),
        "model_a": ModelA(),
        "model_b": ModelB()
    }