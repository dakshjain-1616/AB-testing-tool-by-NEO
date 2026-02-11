import hashlib
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import csv
from queue import Queue

class Router:
    def __init__(self, traffic_split: Dict[str, float]):
        self._validate_traffic_split(traffic_split)
        self.traffic_split = traffic_split
        self.variant_names = list(traffic_split.keys())
        self.cumulative_weights = []
        cumsum = 0
        for variant in self.variant_names:
            cumsum += traffic_split[variant]
            self.cumulative_weights.append(cumsum)
    
    def _validate_traffic_split(self, traffic_split: Dict[str, float]) -> None:
        if not traffic_split:
            raise ValueError("Traffic split cannot be empty")
        
        total_weight = sum(traffic_split.values())
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(
                f"Traffic split weights must sum to 1.0, got {total_weight:.4f}. "
                f"Weights: {traffic_split}"
            )
        
        for variant, weight in traffic_split.items():
            if not (0 <= weight <= 1):
                raise ValueError(
                    f"Weight for variant '{variant}' must be between 0 and 1, got {weight}"
                )
    
    def assign_variant(self, user_id: str) -> str:
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = (hash_value % 10000) / 10000.0
        
        for i, threshold in enumerate(self.cumulative_weights):
            if bucket < threshold:
                return self.variant_names[i]
        
        return self.variant_names[-1]


class AsyncLogger:
    def __init__(self, log_file_path: str, buffer_size: int = 100):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.buffer_size = buffer_size
        self.queue = Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        self._initialize_file()
    
    def _initialize_file(self):
        if not self.log_file_path.exists():
            with open(self.log_file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'user_id', 'variant', 'timestamp', 'conversion', 
                    'latency_ms', 'model_version'
                ])
                writer.writeheader()
    
    def _worker(self):
        buffer = []
        while self.running or not self.queue.empty():
            try:
                log_entry = self.queue.get(timeout=0.1)
                buffer.append(log_entry)
                
                if len(buffer) >= self.buffer_size:
                    self._flush_buffer(buffer)
                    buffer = []
            except:
                if buffer and not self.running:
                    self._flush_buffer(buffer)
                    buffer = []
                continue
    
    def _flush_buffer(self, buffer):
        if not buffer:
            return
        
        with open(self.log_file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'user_id', 'variant', 'timestamp', 'conversion', 
                'latency_ms', 'model_version'
            ])
            writer.writerows(buffer)
    
    def log(self, user_id: str, variant: str, result: Dict[str, Any]):
        log_entry = {
            'user_id': user_id,
            'variant': variant,
            'timestamp': datetime.utcnow().isoformat(),
            'conversion': result.get('conversion', False),
            'latency_ms': result.get('latency_ms', 0),
            'model_version': result.get('model_version', variant)
        }
        self.queue.put(log_entry)
    
    def close(self):
        self.running = False
        self.worker_thread.join(timeout=5)