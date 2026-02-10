from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
import os
import yaml
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ModelA, ModelB
from ab_core import Router, AsyncLogger

app = FastAPI(title="A/B Testing Model Serving")

class PredictionRequest(BaseModel):
    user_id: str
    features: Optional[Dict[str, Any]] = None

class PredictionResponse(BaseModel):
    user_id: str
    variant: str
    prediction: Dict[str, Any]

config_path = "/root/AB_testing/experiment_config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

traffic_split = config['experiment']['traffic_split']
router = Router(traffic_split)
logger = AsyncLogger("/root/AB_testing/data/experiment_logs.csv")

model_a = ModelA()
model_b = ModelB()

models = {
    "model_a": model_a,
    "model_b": model_b
}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    variant = router.assign_variant(request.user_id)
    
    model = models.get(variant)
    if not model:
        raise HTTPException(status_code=500, detail=f"Model {variant} not found")
    
    result = model.predict(request.user_id, request.features)
    
    logger.log(request.user_id, variant, result)
    
    return PredictionResponse(
        user_id=request.user_id,
        variant=variant,
        prediction=result
    )

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/experiment/status")
async def experiment_status():
    return {
        "traffic_split": traffic_split,
        "active_models": list(models.keys())
    }

def shutdown():
    time.sleep(300)
    logger.close()
    os._exit(0)

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=shutdown, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)