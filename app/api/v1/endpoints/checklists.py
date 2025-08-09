"""
Checklist management endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.checklist import Checklist, ChecklistItem, ChecklistStatus
from app.schemas.checklist import (
    ChecklistResponse,
    ChecklistCreate,
    ChecklistUpdate,
    ChecklistItemCreate,
    ChecklistItemUpdate,
    ChecklistItemResponse,
    ChecklistGenerateRequest,
    ChecklistGenerationResponse,
    ChecklistSummary,
    ChecklistError
)

router = APIRouter()


@router.get("/", response_model=List[ChecklistSummary])
async def get_checklists(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user checklists for the authenticated user."""
    result = await db.execute(
        select(Checklist)
        .options(selectinload(Checklist.items))
        .where(Checklist.user_id == str(current_user.id))
        .offset(skip)
        .limit(limit)
    )
    checklists = result.scalars().all()

    summaries: List[ChecklistSummary] = []
    for cl in checklists:
        total_items = len(cl.items)
        completed_items = len([i for i in cl.items if i.is_completed])
        summaries.append(
            ChecklistSummary(
                id=cl.id,
                title=cl.title,
                origin_country_code=cl.origin_country,
                destination_country_code=cl.destination_country,
                status=cl.status,
                progress_percentage=cl.progress_percentage,
                total_items=total_items,
                completed_items=completed_items,
                created_at=cl.created_at,
                updated_at=cl.updated_at,
            )
        )
    return summaries


@router.post("/generate", response_model=dict)
async def generate_checklist(
    request: ChecklistGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a personalized checklist."""
    # TODO: Implement actual checklist generation
    return {
        "checklist": {
            "id": 1,
            "title": f"Migration from {request.origin_country_code} to {request.destination_country_code}",
            "description": f"Personalized migration checklist",
            "origin_country_code": request.origin_country_code,
            "destination_country_code": request.destination_country_code,
            "reason_for_moving": request.reason_for_moving,
            "user_id": current_user.id,
            "status": "draft",
            "progress_percentage": 0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "completed_at": None,
            "items": []
        },
        "generated_items_count": 0,
        "estimated_completion_days": 0,
        "total_estimated_cost": 0,
        "message": "Checklist generated successfully"
    }


@router.post("/", response_model=ChecklistResponse, status_code=status.HTTP_201_CREATED)
async def create_checklist(
    checklist_data: ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new checklist and persist to DB."""
    # Create checklist row
    checklist = Checklist(
        user_id=str(current_user.id),
        title=checklist_data.title,
        description=checklist_data.description,
        origin_country=checklist_data.origin_country_code.upper(),
        destination_country=checklist_data.destination_country_code.upper(),
        reason_for_moving=checklist_data.reason_for_moving,
        status="draft",
    )
    db.add(checklist)
    await db.flush()  # obtain checklist.id

    # Create items if provided
    created_items: List[ChecklistItem] = []
    for idx, item in enumerate(checklist_data.items or []):
        checklist_item = ChecklistItem(
            checklist_id=checklist.id,
            title=item.title,
            description=item.description,
            category=item.category,
            priority=item.priority,
            order_index=item.order_index if item.order_index is not None else idx,
            estimated_duration_days=item.estimated_duration_days,
            cost_estimate=item.cost_estimate,
            notes=item.notes,
            due_date=item.due_date,
        )
        db.add(checklist_item)
        created_items.append(checklist_item)

    await db.commit()
    await db.refresh(checklist)
    for ci in created_items:
        await db.refresh(ci)

    # Build response
    return ChecklistResponse(
        id=checklist.id,
        user_id=checklist.user_id,
        title=checklist.title,
        description=checklist.description,
        origin_country_code=checklist.origin_country,
        destination_country_code=checklist.destination_country,
        reason_for_moving=checklist.reason_for_moving,
        status=checklist.status,
        progress_percentage=checklist.progress_percentage,
        created_at=checklist.created_at,
        updated_at=checklist.updated_at,
        completed_at=checklist.completed_at,
        items=[
            ChecklistItemResponse(
                id=i.id,
                checklist_id=i.checklist_id,
                title=i.title,
                description=i.description,
                category=i.category,
                priority=i.priority,
                order_index=i.order_index,
                estimated_duration_days=i.estimated_duration_days,
                cost_estimate=i.cost_estimate,
                notes=i.notes,
                due_date=i.due_date,
                is_completed=i.is_completed,
                completed_at=i.completed_at,
                created_at=i.created_at,
                updated_at=i.updated_at,
            )
            for i in created_items
        ],
    )


@router.get("/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(
    checklist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific checklist for the authenticated user."""
    result = await db.execute(
        select(Checklist)
        .options(selectinload(Checklist.items))
        .where(Checklist.id == checklist_id, Checklist.user_id == str(current_user.id))
    )
    checklist = result.scalar_one_or_none()
    if checklist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist not found")

    return ChecklistResponse(
        id=checklist.id,
        user_id=checklist.user_id,
        title=checklist.title,
        description=checklist.description,
        origin_country_code=checklist.origin_country,
        destination_country_code=checklist.destination_country,
        reason_for_moving=checklist.reason_for_moving,
        status=checklist.status,
        progress_percentage=checklist.progress_percentage,
        created_at=checklist.created_at,
        updated_at=checklist.updated_at,
        completed_at=checklist.completed_at,
        items=[
            ChecklistItemResponse(
                id=i.id,
                checklist_id=i.checklist_id,
                title=i.title,
                description=i.description,
                category=i.category,
                priority=i.priority,
                order_index=i.order_index,
                estimated_duration_days=i.estimated_duration_days,
                cost_estimate=i.cost_estimate,
                notes=i.notes,
                due_date=i.due_date,
                is_completed=i.is_completed,
                completed_at=i.completed_at,
                created_at=i.created_at,
                updated_at=i.updated_at,
            )
            for i in checklist.items
        ],
    )


@router.put("/{checklist_id}", response_model=dict)
async def update_checklist(
    checklist_id: int,
    update_data: ChecklistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update checklist."""
    # TODO: Implement actual checklist update
    return {
        "id": checklist_id,
        "title": update_data.title or f"Updated Checklist {checklist_id}",
        "description": update_data.description or "Updated description",
        "origin_country_code": update_data.origin_country_code or "US",
        "destination_country_code": update_data.destination_country_code or "CA",
        "reason_for_moving": update_data.reason_for_moving or "Work",
        "user_id": current_user.id,
        "status": update_data.status or "draft",
        "progress_percentage": update_data.progress_percentage or 0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "completed_at": None,
        "items": []
    }


@router.delete("/{checklist_id}")
async def delete_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete checklist."""
    # TODO: Implement actual checklist deletion
    return {"message": "Checklist deleted successfully"}


# Checklist items endpoints
@router.post("/{checklist_id}/items", response_model=dict)
async def add_checklist_item(
    checklist_id: int,
    item_data: ChecklistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add item to checklist."""
    # TODO: Implement actual item addition
    return {
        "id": 1,
        "checklist_id": checklist_id,
        "title": item_data.title,
        "description": item_data.description,
        "category": item_data.category,
        "priority": item_data.priority,
        "order_index": item_data.order_index,
        "estimated_duration_days": item_data.estimated_duration_days,
        "cost_estimate": item_data.cost_estimate,
        "notes": item_data.notes,
        "due_date": item_data.due_date,
        "is_completed": False,
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@router.put("/{checklist_id}/items/{item_id}", response_model=dict)
async def update_checklist_item(
    checklist_id: int,
    item_id: int,
    update_data: ChecklistItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update checklist item."""
    # TODO: Implement actual item update
    return {
        "id": item_id,
        "checklist_id": checklist_id,
        "title": update_data.title or f"Item {item_id}",
        "description": update_data.description,
        "category": update_data.category or "other",
        "priority": update_data.priority or 1,
        "order_index": update_data.order_index or 0,
        "estimated_duration_days": update_data.estimated_duration_days,
        "cost_estimate": update_data.cost_estimate,
        "notes": update_data.notes,
        "due_date": update_data.due_date,
        "is_completed": update_data.is_completed or False,
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@router.delete("/{checklist_id}/items/{item_id}")
async def delete_checklist_item(
    checklist_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete checklist item."""
    # TODO: Implement actual item deletion
    return {"message": "Checklist item deleted successfully"} 