"""Opportunities routes: jobs, internships, events."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import Opportunity, IndustryProfile, User, UserRole
from backend.schemas import OpportunityCreate, OpportunityResponse, MessageResponse
import json

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities"])


@router.post("", response_model=OpportunityResponse)
def create_opportunity(
    opportunity: OpportunityCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create a new opportunity (job/internship/event)."""
    # Verify industry user
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.INDUSTRY).first()
    if not user:
        raise HTTPException(status_code=403, detail="Only industry users can post opportunities")
    
    industry_profile = db.query(IndustryProfile).filter(IndustryProfile.user_id == user_id).first()
    if not industry_profile:
        raise HTTPException(status_code=404, detail="Industry profile not found")
    
    opp = Opportunity(
        industry_id=industry_profile.id,
        title=opportunity.title,
        opportunity_type=opportunity.opportunity_type.value,
        required_skills=json.dumps(opportunity.required_skills or []),
        eligibility=json.dumps(opportunity.eligibility) if opportunity.eligibility else None,
        description=opportunity.description,
        location=opportunity.location,
        mode=opportunity.mode,
        deadline=opportunity.deadline,
        stipend=opportunity.stipend
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    
    return opportunity_to_response(opp)


@router.get("", response_model=List[OpportunityResponse])
def list_opportunities(
    type: Optional[str] = Query(None, description="Filter by type: internship, job, event, skill-program"),
    skills: Optional[str] = Query(None, description="Filter by skills (comma separated)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all opportunities with optional filtering."""
    query = db.query(Opportunity)
    
    if type:
        query = query.filter(Opportunity.opportunity_type == type.lower())
    
    opportunities = query.offset(offset).limit(limit).all()
    
    # Apply skills filter in Python if specified
    if skills:
        desired_skills = [s.strip().lower() for s in skills.split(",")]
        filtered = []
        for opp in opportunities:
            opp_skills = json.loads(opp.required_skills) if opp.required_skills else []
            opp_skills_lower = [s.lower() for s in opp_skills]
            if any(ds in opp_skills_lower for ds in desired_skills):
                filtered.append(opp)
        opportunities = filtered
    
    return [opportunity_to_response(opp) for opp in opportunities]


@router.get("/{opp_id}", response_model=OpportunityResponse)
def get_opportunity(opp_id: int, db: Session = Depends(get_db)):
    """Get a specific opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return opportunity_to_response(opp)


@router.put("/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(
    opp_id: int,
    opportunity: OpportunityCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Update an opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Verify ownership
    user = db.query(User).filter(User.id == user_id).first()
    if not user or opp.industry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this opportunity")
    
    opp.title = opportunity.title
    opp.opportunity_type = opportunity.opportunity_type.value
    opp.required_skills = json.dumps(opportunity.required_skills or [])
    opp.eligibility = json.dumps(opportunity.eligibility) if opportunity.eligibility else None
    opp.description = opportunity.description
    opp.location = opportunity.location
    opp.mode = opportunity.mode
    opp.deadline = opportunity.deadline
    opp.stipend = opportunity.stipend
    
    db.commit()
    db.refresh(opp)
    
    return opportunity_to_response(opp)


@router.delete("/{opp_id}", response_model=MessageResponse)
def delete_opportunity(
    opp_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete an opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Verify ownership
    user = db.query(User).filter(User.id == user_id).first()
    if not user or opp.industry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this opportunity")
    
    db.delete(opp)
    db.commit()
    
    return MessageResponse(message="Opportunity deleted successfully")


def opportunity_to_response(opp: Opportunity) -> OpportunityResponse:
    """Convert opportunity to response format."""
    return OpportunityResponse(
        id=opp.id,
        title=opp.title,
        opportunity_type=opp.opportunity_type,
        required_skills=json.loads(opp.required_skills) if opp.required_skills else [],
        eligibility=json.loads(opp.eligibility) if opp.eligibility else None,
        description=opp.description,
        location=opp.location,
        mode=opp.mode,
        deadline=opp.deadline,
        stipend=opp.stipend,
        company_name=opp.industry.company_name if opp.industry else None,
        created_at=opp.created_at
    )
