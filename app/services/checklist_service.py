"""
Checklist service for business logic and checklist generation.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, select
from fastapi import HTTPException, status

from app.models.checklist import Checklist, ChecklistItem, ChecklistStatus, ChecklistCategory
from app.schemas.checklist import (
    ChecklistCreate, 
    ChecklistUpdate, 
    ChecklistItemCreate,
    ChecklistItemUpdate,
    ChecklistGenerateRequest
)


class ChecklistService:
    """Service class for checklist operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_checklist(self, user_id: int, request: ChecklistGenerateRequest) -> Checklist:
        """Generate a personalized checklist based on migration details."""
        
        # Validate country codes are different
        if request.origin_country_code.upper() == request.destination_country_code.upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Origin and destination countries must be different"
            )
        
        # Create checklist title
        title = f"Migration from {request.origin_country_code.upper()} to {request.destination_country_code.upper()}"
        
        # Create the checklist
        checklist_data = ChecklistCreate(
            title=title,
            description=f"Personalized migration checklist for moving from {request.origin_country_code.upper()} to {request.destination_country_code.upper()}",
            origin_country_code=request.origin_country_code.upper(),
            destination_country_code=request.destination_country_code.upper(),
            reason_for_moving=request.reason_for_moving,
            items=[]
        )
        
        # Create checklist in database
        checklist = await self.create_checklist(user_id, checklist_data)
        
        # Generate checklist items based on country pair and user profile
        items = self._generate_checklist_items(
            origin_country=request.origin_country_code.upper(),
            destination_country=request.destination_country_code.upper(),
            reason_for_moving=request.reason_for_moving,
            user_profile=request.user_profile
        )
        
        # Add items to checklist
        for item_data in items:
            await self.add_checklist_item(checklist.id, item_data)
        
        # Refresh checklist to get updated items
        await self.db.refresh(checklist)
        
        return checklist
    
    def create_checklist(self, user_id: int, checklist_data: ChecklistCreate) -> Checklist:
        """Create a new checklist."""
        checklist = Checklist(
            user_id=user_id,
            title=checklist_data.title,
            description=checklist_data.description,
            origin_country_code=checklist_data.origin_country_code,
            destination_country_code=checklist_data.destination_country_code,
            reason_for_moving=checklist_data.reason_for_moving,
            status=ChecklistStatus.DRAFT,
            progress_percentage=0
        )
        
        self.db.add(checklist)
        self.db.commit()
        self.db.refresh(checklist)
        
        return checklist
    
    def get_user_checklists(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Checklist]:
        """Get all checklists for a user."""
        return self.db.query(Checklist).filter(
            Checklist.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_checklist(self, checklist_id: int, user_id: int) -> Optional[Checklist]:
        """Get a specific checklist by ID."""
        return self.db.query(Checklist).filter(
            and_(
                Checklist.id == checklist_id,
                Checklist.user_id == user_id
            )
        ).first()
    
    def update_checklist(self, checklist_id: int, user_id: int, update_data: ChecklistUpdate) -> Optional[Checklist]:
        """Update a checklist."""
        checklist = self.get_checklist(checklist_id, user_id)
        if not checklist:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(checklist, field, value)
        
        checklist.updated_at = datetime.utcnow()
        
        # Update progress if status changed to completed
        if update_data.status == ChecklistStatus.COMPLETED and checklist.status != ChecklistStatus.COMPLETED:
            checklist.completed_at = datetime.utcnow()
            checklist.progress_percentage = 100
        
        self.db.commit()
        self.db.refresh(checklist)
        
        return checklist
    
    def delete_checklist(self, checklist_id: int, user_id: int) -> bool:
        """Delete a checklist."""
        checklist = self.get_checklist(checklist_id, user_id)
        if not checklist:
            return False
        
        self.db.delete(checklist)
        self.db.commit()
        return True
    
    def add_checklist_item(self, checklist_id: int, item_data: ChecklistItemCreate) -> ChecklistItem:
        """Add an item to a checklist."""
        # Verify checklist exists
        checklist = self.db.query(Checklist).filter(Checklist.id == checklist_id).first()
        if not checklist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checklist not found"
            )
        
        # Get next order index
        max_order = self.db.query(func.max(ChecklistItem.order_index)).filter(
            ChecklistItem.checklist_id == checklist_id
        ).scalar() or 0
        
        item = ChecklistItem(
            checklist_id=checklist_id,
            title=item_data.title,
            description=item_data.description,
            category=item_data.category,
            priority=item_data.priority,
            order_index=max_order + 1,
            estimated_duration_days=item_data.estimated_duration_days,
            cost_estimate=item_data.cost_estimate,
            notes=item_data.notes,
            due_date=item_data.due_date
        )
        
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        # Update checklist progress
        self._update_checklist_progress(checklist_id)
        
        return item
    
    def update_checklist_item(self, item_id: int, checklist_id: int, update_data: ChecklistItemUpdate) -> Optional[ChecklistItem]:
        """Update a checklist item."""
        item = self.db.query(ChecklistItem).filter(
            and_(
                ChecklistItem.id == item_id,
                ChecklistItem.checklist_id == checklist_id
            )
        ).first()
        
        if not item:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        # Handle completion
        if update_data.is_completed is not None:
            if update_data.is_completed and not item.is_completed:
                item.completed_at = datetime.utcnow()
            elif not update_data.is_completed:
                item.completed_at = None
        
        item.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(item)
        
        # Update checklist progress
        self._update_checklist_progress(checklist_id)
        
        return item
    
    def delete_checklist_item(self, item_id: int, checklist_id: int) -> bool:
        """Delete a checklist item."""
        item = self.db.query(ChecklistItem).filter(
            and_(
                ChecklistItem.id == item_id,
                ChecklistItem.checklist_id == checklist_id
            )
        ).first()
        
        if not item:
            return False
        
        self.db.delete(item)
        self.db.commit()
        
        # Update checklist progress
        self._update_checklist_progress(checklist_id)
        
        return True
    
    def _update_checklist_progress(self, checklist_id: int) -> None:
        """Update checklist progress percentage."""
        checklist = self.db.query(Checklist).filter(Checklist.id == checklist_id).first()
        if not checklist:
            return
        
        # Count total and completed items
        total_items = self.db.query(ChecklistItem).filter(
            ChecklistItem.checklist_id == checklist_id
        ).count()
        
        completed_items = self.db.query(ChecklistItem).filter(
            and_(
                ChecklistItem.checklist_id == checklist_id,
                ChecklistItem.is_completed == True
            )
        ).count()
        
        # Calculate progress percentage
        if total_items > 0:
            progress_percentage = int((completed_items / total_items) * 100)
        else:
            progress_percentage = 0
        
        # Update checklist
        checklist.progress_percentage = progress_percentage
        checklist.updated_at = datetime.utcnow()
        
        # Update status based on progress
        if progress_percentage == 100 and checklist.status != ChecklistStatus.COMPLETED:
            checklist.status = ChecklistStatus.COMPLETED
            checklist.completed_at = datetime.utcnow()
        elif progress_percentage > 0 and checklist.status == ChecklistStatus.DRAFT:
            checklist.status = ChecklistStatus.IN_PROGRESS
        
        self.db.commit()
    
    def _generate_checklist_items(
        self, 
        origin_country: str, 
        destination_country: str, 
        reason_for_moving: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> List[ChecklistItemCreate]:
        """Generate checklist items based on migration details."""
        
        items = []
        
        # Pre-departure items
        items.extend([
            ChecklistItemCreate(
                title="Research visa requirements",
                description=f"Check visa requirements for {destination_country} from {origin_country}",
                category=ChecklistCategory.LEGAL,
                priority=1,
                estimated_duration_days=7,
                cost_estimate=5000,  # $50
                notes="Check official government websites for most current requirements"
            ),
            ChecklistItemCreate(
                title="Gather required documents",
                description="Collect all necessary documents for visa application",
                category=ChecklistCategory.LEGAL,
                priority=1,
                estimated_duration_days=14,
                cost_estimate=2000,  # $20
                notes="Passport, birth certificate, police certificates, etc."
            ),
            ChecklistItemCreate(
                title="Apply for visa",
                description=f"Submit visa application for {destination_country}",
                category=ChecklistCategory.LEGAL,
                priority=1,
                estimated_duration_days=1,
                cost_estimate=50000,  # $500
                notes="Follow official application process"
            ),
            ChecklistItemCreate(
                title="Book travel arrangements",
                description="Book flights and accommodation for initial arrival",
                category=ChecklistCategory.TRANSPORTATION,
                priority=2,
                estimated_duration_days=3,
                cost_estimate=200000,  # $2000
                notes="Consider booking flexible tickets"
            ),
            ChecklistItemCreate(
                title="Arrange temporary accommodation",
                description="Book temporary housing for first few weeks",
                category=ChecklistCategory.HOUSING,
                priority=2,
                estimated_duration_days=5,
                cost_estimate=150000,  # $1500
                notes="Consider hotels, Airbnb, or short-term rentals"
            ),
        ])
        
        # Arrival items
        items.extend([
            ChecklistItemCreate(
                title="Complete immigration process",
                description="Go through immigration and customs upon arrival",
                category=ChecklistCategory.LEGAL,
                priority=1,
                estimated_duration_days=1,
                cost_estimate=0,
                notes="Have all documents ready"
            ),
            ChecklistItemCreate(
                title="Register with local authorities",
                description="Register your presence with local government if required",
                category=ChecklistCategory.LEGAL,
                priority=2,
                estimated_duration_days=7,
                cost_estimate=5000,  # $50
                notes="Check local requirements"
            ),
            ChecklistItemCreate(
                title="Open local bank account",
                description="Set up a bank account in the destination country",
                category=ChecklistCategory.FINANCIAL,
                priority=2,
                estimated_duration_days=7,
                cost_estimate=1000,  # $10
                notes="Bring required identification documents"
            ),
        ])
        
        # Setup items
        items.extend([
            ChecklistItemCreate(
                title="Find permanent accommodation",
                description="Secure long-term housing",
                category=ChecklistCategory.HOUSING,
                priority=1,
                estimated_duration_days=30,
                cost_estimate=500000,  # $5000
                notes="Consider rental agreements and deposits"
            ),
            ChecklistItemCreate(
                title="Set up utilities and services",
                description="Connect electricity, water, internet, etc.",
                category=ChecklistCategory.HOUSING,
                priority=2,
                estimated_duration_days=7,
                cost_estimate=50000,  # $500
                notes="May require proof of address"
            ),
            ChecklistItemCreate(
                title="Obtain local phone number",
                description="Get a local mobile phone number",
                category=ChecklistCategory.OTHER,
                priority=2,
                estimated_duration_days=1,
                cost_estimate=10000,  # $100
                notes="Consider prepaid vs contract options"
            ),
            ChecklistItemCreate(
                title="Register for healthcare",
                description="Enroll in local healthcare system",
                category=ChecklistCategory.HEALTH,
                priority=1,
                estimated_duration_days=14,
                cost_estimate=20000,  # $200
                notes="Check eligibility requirements"
            ),
        ])
        
        # Add reason-specific items
        if reason_for_moving:
            if "work" in reason_for_moving.lower():
                items.extend([
                    ChecklistItemCreate(
                        title="Obtain work permit",
                        description="Secure work authorization if not included in visa",
                        category=ChecklistCategory.LEGAL,
                        priority=1,
                        estimated_duration_days=30,
                        cost_estimate=100000,  # $1000
                        notes="May require employer sponsorship"
                    ),
                    ChecklistItemCreate(
                        title="Set up tax identification",
                        description="Register for tax purposes",
                        category=ChecklistCategory.FINANCIAL,
                        priority=2,
                        estimated_duration_days=14,
                        cost_estimate=5000,  # $50
                        notes="Required for employment"
                    ),
                ])
            elif "education" in reason_for_moving.lower():
                items.extend([
                    ChecklistItemCreate(
                        title="Enroll in educational institution",
                        description="Complete enrollment process",
                        category=ChecklistCategory.EDUCATION,
                        priority=1,
                        estimated_duration_days=7,
                        cost_estimate=50000,  # $500
                        notes="May require additional documentation"
                    ),
                    ChecklistItemCreate(
                        title="Obtain student ID",
                        description="Get student identification card",
                        category=ChecklistCategory.EDUCATION,
                        priority=2,
                        estimated_duration_days=1,
                        cost_estimate=1000,  # $10
                        notes="Useful for discounts and access"
                    ),
                ])
        
        return items 