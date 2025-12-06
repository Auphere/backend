"""Plans router - CRUD operations for saved plans using local PostgreSQL."""

from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.dependencies import get_current_user
from app.models.plans import PlanCreateRequest, PlanResponse
from app.config import settings

router = APIRouter(prefix="/plans", tags=["plans"])

# Database setup - usando una base de datos local
# TODO: Mover esto a un archivo de models separado
Base = declarative_base()

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    vibe = Column(String, nullable=True)
    total_duration = Column(Integer, nullable=True)
    total_distance = Column(Float, nullable=True)
    stops = Column(JSON, nullable=False, default=list)
    extra_data = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create engine - usando SQLite para desarrollo, cambiar a PostgreSQL en producción
# TODO: Usar settings.database_url cuando esté configurado
SQLALCHEMY_DATABASE_URL = "sqlite:///./auphere_backend.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[PlanResponse])
async def list_plans(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all plans for the current user."""
    plans = db.query(Plan).filter(Plan.user_id == current_user["id"]).order_by(Plan.created_at.desc()).all()
    return [
        PlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            name=plan.name,
            description=plan.description,
            vibe=plan.vibe,
            total_duration=plan.total_duration,
            total_distance=plan.total_distance,
            stops=plan.stops,
            metadata=plan.extra_data,
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat()
        )
        for plan in plans
    ]


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new plan."""
    plan = Plan(
        id=str(uuid4()),
        user_id=current_user["id"],
        name=payload.name,
        description=payload.description,
        vibe=payload.vibe,
        total_duration=payload.total_duration,
        total_distance=payload.total_distance,
        stops=payload.stops,
        extra_data=payload.metadata or {}
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        vibe=plan.vibe,
        total_duration=plan.total_duration,
        total_distance=plan.total_distance,
        stops=plan.stops,
        metadata=plan.extra_data,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat()
    )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific plan."""
    plan = db.query(Plan).filter(
        Plan.id == plan_id,
        Plan.user_id == current_user["id"]
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        vibe=plan.vibe,
        total_duration=plan.total_duration,
        total_distance=plan.total_distance,
        stops=plan.stops,
        metadata=plan.extra_data,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat()
    )


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: str,
    payload: PlanCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a plan."""
    plan = db.query(Plan).filter(
        Plan.id == plan_id,
        Plan.user_id == current_user["id"]
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan.name = payload.name
    plan.description = payload.description
    plan.vibe = payload.vibe
    plan.total_duration = payload.total_duration
    plan.total_distance = payload.total_distance
    plan.stops = payload.stops
    plan.extra_data = payload.metadata or {}
    plan.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(plan)
    
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        vibe=plan.vibe,
        total_duration=plan.total_duration,
        total_distance=plan.total_distance,
        stops=plan.stops,
        metadata=plan.extra_data,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat()
    )


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a plan."""
    plan = db.query(Plan).filter(
        Plan.id == plan_id,
        Plan.user_id == current_user["id"]
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    db.delete(plan)
    db.commit()
    
    return {"message": "Plan deleted successfully"}

