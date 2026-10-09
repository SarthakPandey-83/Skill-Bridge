"""Analytics routes for institute dashboard and skill analysis."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models import User, UserRole, StudentProfile, Opportunity
from backend.schemas import (
    SkillAnalysisResponse, InstituteAnalyticsResponse, ChartData, MessageResponse
)
from backend.services.skill_analysis import skill_engine
from backend.services.analytics import analytics_service
import json

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/student/skill-gap/{user_id}", response_model=SkillAnalysisResponse)
def analyze_student_skill_gap(user_id: int, db: Session = Depends(get_db)):
    """Analyze skill gap for a student."""
    # Get student profile
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    # Get all opportunities for industry demand
    opportunities = db.query(Opportunity).all()
    
    # Parse student skills
    student_skills = json.loads(profile.skills) if profile.skills else []
    if not student_skills:
        student_skills = []
    
    # Calculate industry demand
    industry_demand = skill_engine.calculate_industry_demand(
        [{"required_skills": json.loads(o.required_skills) if o.required_skills else []} 
         for o in opportunities]
    )
    
    # Analyze gap
    analysis = skill_engine.analyze_skill_gap(
        student_skills=student_skills,
        industry_skills=industry_demand
    )
    
    return SkillAnalysisResponse(
        current_skills=analysis["current_skills"],
        missing_skills=analysis["missing_skills"],
        weak_skills=analysis["weak_skills"],
        industry_demanded_skills=analysis["industry_demanded_skills"],
        recommended_skills=analysis["recommended_skills"],
        skill_gaps=analysis["skill_gaps"],
        demand_rankings=[]  # Would be populated separately
    )


@router.get("/student/skills/{user_id}")
def get_student_skills_data(user_id: int, db: Session = Depends(get_db)):
    """Get student skills for visualization."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    skills = json.loads(profile.skills) if profile.skills else []
    technical_skills = json.loads(profile.technical_skills) if profile.technical_skills else []
    
    # Get skill categories
    categories = {}
    for skill in skills + technical_skills:
        category = skill_engine.categorize_skill(skill)
        if category not in categories:
            categories[category] = []
        if skill not in categories[category]:
            categories[category].append(skill)
    
    return {
        "skills": skills,
        "technical_skills": technical_skills,
        "categories": categories,
        "total_skills": len(skills) + len(technical_skills)
    }


@router.get("/institute/analytics/{institute_id}", response_model=InstituteAnalyticsResponse)
def get_institute_analytics(institute_id: int, db: Session = Depends(get_db)):
    """Get comprehensive analytics for an institute."""
    # Get all students from this institute
    students = db.query(StudentProfile).filter(StudentProfile.institute_id == institute_id).all()
    
    # Get all opportunities for demand analysis
    opportunities = db.query(Opportunity).all()
    
    # Convert to dicts
    student_data = []
    for s in students:
        student_data.append({
            "id": s.id,
            "branch": s.branch,
            "batch": s.batch,
            "skills": s.skills,
            "preferred_industry": s.preferred_industry,
            "career_goal": s.career_goal
        })
    
    # Calculate analytics
    analytics = analytics_service.generate_institute_analytics(
        students=student_data,
        opportunities=[{"required_skills": json.loads(o.required_skills) if o.required_skills else []} 
                      for o in opportunities]
    )
    
    # Get demand analysis
    if opportunities:
        demand_analysis = analytics_service.analyze_industry_demand(
            opportunities=[{"required_skills": json.loads(o.required_skills) if o.required_skills else []} 
                          for o in opportunities],
            student_skills=student_data
        )
        analytics["industry_demanded_skills"] = [
            {"skill": r["skill"], "demand_score": r["demand_score"], "supply_score": r["supply_score"]}
            for r in demand_analysis.get("rankings", [])[:10]
        ]
        analytics["skill_gaps"] = [
            {"skill": r["skill"], "gap": r["gap"], "priority": r["priority"]}
            for r in demand_analysis.get("high_demand_low_supply", [])[:10]
        ]
    
    return InstituteAnalyticsResponse(**analytics)


@router.get("/institute/charts/{institute_id}")
def get_institute_charts(institute_id: int, db: Session = Depends(get_db)):
    """Get chart images for institute analytics."""
    # Get analytics data
    students = db.query(StudentProfile).filter(StudentProfile.institute_id == institute_id).all()
    opportunities = db.query(Opportunity).all()
    
    student_data = []
    for s in students:
        student_data.append({
            "id": s.id,
            "branch": s.branch,
            "batch": s.batch,
            "skills": s.skills,
            "preferred_industry": s.preferred_industry,
            "career_goal": s.career_goal
        })
    
    analytics = analytics_service.generate_institute_analytics(
        students=student_data,
        opportunities=[{"required_skills": json.loads(o.required_skills) if o.required_skills else []} 
                      for o in opportunities]
    )
    
    charts = analytics_service.generate_institute_charts(analytics)
    
    return {
        "charts": charts,
        "analytics": analytics
    }


@router.get("/industry/demand-analysis")
def get_industry_demand_analysis(db: Session = Depends(get_db)):
    """Get industry skill demand analysis."""
    opportunities = db.query(Opportunity).all()
    
    # Get all students for supply comparison
    students = db.query(StudentProfile).all()
    student_skills = [
        {"skills": s.skills} for s in students
    ]
    
    analysis = analytics_service.analyze_industry_demand(
        opportunities=[{"required_skills": json.loads(o.required_skills) if o.required_skills else []} 
                      for o in opportunities],
        student_skills=student_skills
    )
    
    charts = analytics_service.generate_demand_charts(analysis)
    
    return {
        "analysis": analysis,
        "charts": charts
    }


@router.get("/skill-rankings")
def get_skill_rankings(db: Session = Depends(get_db)):
    """Get skills ranked by industry demand."""
    opportunities = db.query(Opportunity).all()
    
    rankings = skill_engine.calculate_skill_demand_rankings(
        all_opportunities=[{"required_skills": json.loads(o.required_skills) if o.required_skills else []} 
                          for o in opportunities]
    )
    
    return {
        "rankings": rankings[:20],
        "total_skills": len(rankings)
    }


@router.get("/skill-categories")
def get_skill_categories():
    """Get available skill categories."""
    return {
        "categories": list(skill_engine.skill_categories.keys()),
        "skills_by_category": skill_engine.skill_categories
    }
