from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..core.database import get_db
from ..models.database_models import Model, ModelStatus

router = APIRouter(prefix="/models", tags=["models"])

class ModelCreate(BaseModel):
    model_id: str
    provider_id: str
    display_name: str
    context_window: Optional[int] = 0
    input_price: Optional[str] = "UNKNOWN"
    output_price: Optional[str] = "UNKNOWN"
    input_price_float: Optional[float] = None
    output_price_float: Optional[float] = None
    free_tier: bool = False
    coding_score: float = 0
    reasoning_score: float = 0
    speed_score: float = 0
    reliability_score: float = 0
    tool_calling_score: float = 0
    json_score: float = 0
    overall_score: float = 0
    confidence_score: float = 0
    capabilities: Optional[dict] = {}

@router.get("")
def list_models(provider_id: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Model)
    if provider_id:
        q = q.filter(Model.provider_id == provider_id)
    if status:
        q = q.filter(Model.status == status)
    models = q.all()
    # Sort by overall score desc
    models_sorted = sorted(models, key=lambda x: x.overall_score, reverse=True)
    return [
        {
            "id": m.id,
            "model_id": m.model_id,
            "provider_id": m.provider_id,
            "display_name": m.display_name,
            "context_window": m.context_window if m.context_window and m.context_window > 0 else "UNKNOWN",
            "context_window_raw": m.context_window,
            "input_price": m.input_price,
            "output_price": m.output_price,
            "input_price_float": m.input_price_float,
            "output_price_float": m.output_price_float,
            "free_tier": m.free_tier,
            "coding_score": m.coding_score,
            "reasoning_score": m.reasoning_score,
            "speed_score": m.speed_score,
            "reliability_score": m.reliability_score,
            "tool_calling_score": m.tool_calling_score,
            "json_score": m.json_score,
            "overall_score": m.overall_score,
            "confidence_score": m.confidence_score,
            "test_count": m.test_count,
            "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
            "capabilities": m.capabilities or {},
            "last_verified": m.last_verified.isoformat() if m.last_verified else None
        }
        for m in models_sorted
    ]

@router.post("")
def create_model(data: ModelCreate, db: Session = Depends(get_db)):
    # Check provider exists
    from ..models.database_models import Provider
    provider = db.query(Provider).filter(Provider.provider_id == data.provider_id).first()
    if not provider:
        raise HTTPException(404, f"Provider {data.provider_id} not found - create provider first")
    
    existing = db.query(Model).filter(Model.model_id == data.model_id, Model.provider_id == data.provider_id).first()
    if existing:
        raise HTTPException(409, "Model already exists for this provider")
    
    model = Model(
        model_id=data.model_id,
        provider_id=data.provider_id,
        display_name=data.display_name,
        context_window=data.context_window or 0,
        input_price=data.input_price,
        output_price=data.output_price,
        input_price_float=data.input_price_float,
        output_price_float=data.output_price_float,
        free_tier=data.free_tier,
        coding_score=data.coding_score,
        reasoning_score=data.reasoning_score,
        speed_score=data.speed_score,
        reliability_score=data.reliability_score,
        tool_calling_score=data.tool_calling_score,
        json_score=data.json_score,
        overall_score=data.overall_score,
        confidence_score=data.confidence_score,
        capabilities=data.capabilities or {},
        status=ModelStatus.DISCOVERED,
        test_count=0
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return {"id": model.id, "model_id": model.model_id, "status": "DISCOVERED"}

@router.delete("/{model_id}")
def delete_model(model_id: str, provider_id: str, db: Session = Depends(get_db)):
    m = db.query(Model).filter(Model.model_id == model_id, Model.provider_id == provider_id).first()
    if not m:
        raise HTTPException(404, "Model not found")
    db.delete(m)
    db.commit()
    return {"deleted": f"{provider_id}/{model_id}"}

@router.get("/benchmark")
def benchmark_table(db: Session = Depends(get_db)):
    models = db.query(Model).all()
    # Return table format as per spec item 25
    table = []
    for m in sorted(models, key=lambda x: x.overall_score, reverse=True):
        table.append({
            "MODEL": f"{m.display_name} ({m.provider_id})",
            "model_id": m.model_id,
            "provider_id": m.provider_id,
            "CODING": m.coding_score,
            "REASONING": m.reasoning_score,
            "SPEED": m.speed_score,
            "RELIABILITY": m.reliability_score,
            "TOOL_CALLING": m.tool_calling_score,
            "JSON": m.json_score,
            "OVERALL": m.overall_score,
            "CONFIDENCE": m.confidence_score,
            "TEST_COUNT": m.test_count,
            "STATUS": m.status.value if hasattr(m.status, 'value') else str(m.status)
        })
    return table
