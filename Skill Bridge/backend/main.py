"""SIH Platform - Main FastAPI Application.

SIH Problem Statement 26044: Skill Development & Industry-Academia Connect Platform
A platform connecting Students, Faculty, Institutes/Colleges and Industries
to improve skill development, identify skill gaps and connect academic skills
with industry requirements.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
import os
import json
import shutil

from backend.database import get_db, engine, Base
from backend.models import (
    User, UserRole, StudentProfile, FacultyProfile, 
    IndustryProfile, Institute, Opportunity, Quiz, QuizQuestion, QuizAttempt, AttemptAnswer
)
from backend.schemas import (
    LoginRequest, SignupRequest, AuthResponse,
    StudentProfileCreate, StudentProfileUpdate, StudentProfileResponse,
    FacultyProfileCreate, FacultyProfileUpdate, FacultyProfileResponse,
    IndustryProfileCreate, IndustryProfileResponse,
    OpportunityCreate, OpportunityResponse,
    QuizCreate, QuizResponse, QuizDetailResponse,
    QuizAttemptSubmit, QuizAttemptResponse, StudentQuizResult
)
from backend.routes.auth import router as auth_router
from backend.routes.opportunities import router as opportunities_router
from backend.routes.analytics import router as analytics_router
from werkzeug.security import generate_password_hash

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SIH Platform - Skill Development & Industry-Academia Connect",
    description="Platform connecting Students, Faculty, Institutes and Industries for skill development",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(opportunities_router)
app.include_router(analytics_router)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


# ============== Root & Health Endpoints ==============

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the landing page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>SIH Platform</h1><p>Frontend not found.</p>")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "SIH Platform API"}


@app.get("/api")
def api_root():
    """API root endpoint."""
    return {
        "message": "SIH Platform API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "opportunities": "/api/opportunities",
            "analytics": "/api/analytics"
        }
    }


# ============== Authentication Endpoints ==============

@app.post("/api/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user."""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not check_password_hash(user.password_hash, request.password):
        return AuthResponse(success=False, message="Invalid email or password")
    
    return AuthResponse(
        success=True,
        user_id=user.id,
        name=user.name,
        role=user.role.value if user.role else None
    )


@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register new user."""
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        return AuthResponse(success=False, message="Email already registered")
    
    password_hash = generate_password_hash(request.password)
    user = User(
        email=request.email,
        password_hash=password_hash,
        name=request.name,
        role=UserRole(request.role)
    )
    db.add(user)
    db.flush()
    
    # Create institute if institute signup
    if request.role == "institute" and request.institute_name:
        institute = Institute(name=request.institute_name)
        db.add(institute)
        db.flush()
        user.institute_id = institute.id
    
    # Create role-specific profile
    if request.role == "student":
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
    elif request.role == "faculty":
        profile = FacultyProfile(user_id=user.id)
        db.add(profile)
    elif request.role == "industry":
        profile = IndustryProfile(user_id=user.id, company_name=request.name)
        db.add(profile)
    
    db.commit()
    
    return AuthResponse(
        success=True,
        user_id=user.id,
        name=user.name,
        role=user.role.value
    )


@app.get("/api/auth/me/{user_id}")
def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """Get current user info."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value if user.role else None,
        "institute_id": user.institute_id
    }


# ============== Student Profile Endpoints ==============

@app.post("/api/student/profile/{user_id}", response_model=StudentProfileResponse)
def create_student_profile(
    user_id: int,
    profile_data: StudentProfileCreate,
    db: Session = Depends(get_db)
):
    """Create student profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.STUDENT).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student user not found")
    
    existing = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile = StudentProfile(
        user_id=user_id,
        branch=profile_data.branch,
        department=profile_data.department,
        batch=profile_data.batch,
        course=profile_data.course,
        semester=profile_data.semester,
        skills=json.dumps(profile_data.skills or []),
        technical_skills=json.dumps(profile_data.technical_skills or []),
        certifications=json.dumps(profile_data.certifications or []),
        projects=json.dumps(profile_data.projects or []),
        interests=json.dumps(profile_data.interests or []),
        career_goal=profile_data.career_goal,
        preferred_industry=profile_data.preferred_industry,
        other_info=profile_data.other_info
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile_to_response(profile, user)


@app.get("/api/student/profile/{user_id}", response_model=StudentProfileResponse)
def get_student_profile(user_id: int, db: Session = Depends(get_db)):
    """Get student profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.STUDENT).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student user not found")
    
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile_to_response(profile, user)


@app.put("/api/student/profile/{user_id}", response_model=StudentProfileResponse)
def update_student_profile(
    user_id: int,
    profile_data: StudentProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update student profile."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field in ["skills", "technical_skills", "certifications", "projects", "interests"]:
                setattr(profile, field, json.dumps(value))
            else:
                setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    user = db.query(User).filter(User.id == user_id).first()
    return profile_to_response(profile, user)

@app.get("/api/institute/{institute_id}")
def get_institute(institute_id: int, db: Session = Depends(get_db)):
    institute = db.query(Institute).filter(Institute.id == institute_id).first()

    if not institute:
        raise HTTPException(status_code=404, detail="Institute not found")

    return {
        "id": institute.id,
        "name": institute.name,
        "location": institute.location,
        "type": institute.type,
        "established_year": institute.established_year
    }


# ============== Faculty Profile Endpoints ==============

@app.post("/api/faculty/profile/{user_id}", response_model=FacultyProfileResponse)
def create_faculty_profile(
    user_id: int,
    profile_data: FacultyProfileCreate,
    db: Session = Depends(get_db)
):
    """Create faculty profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.FACULTY).first()
    if not user:
        raise HTTPException(status_code=404, detail="Faculty user not found")
    
    existing = db.query(FacultyProfile).filter(FacultyProfile.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile = FacultyProfile(
        user_id=user_id,
        department=profile_data.department,
        designation=profile_data.designation,
        subjects_teaching=json.dumps(profile_data.subjects_teaching or []),
        expertise_areas=json.dumps(profile_data.expertise_areas or []),
        skills=json.dumps(profile_data.skills or []),
        experience_years=profile_data.experience_years,
        certifications=json.dumps(profile_data.certifications or []),
        research_projects=json.dumps(profile_data.research_projects or [])
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return faculty_profile_to_response(profile, user)


@app.get("/api/faculty/profile/{user_id}", response_model=FacultyProfileResponse)
def get_faculty_profile(user_id: int, db: Session = Depends(get_db)):
    """Get faculty profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.FACULTY).first()
    if not user:
        raise HTTPException(status_code=404, detail="Faculty user not found")
    
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return faculty_profile_to_response(profile, user)


@app.put("/api/faculty/profile/{user_id}", response_model=FacultyProfileResponse)
def update_faculty_profile(
    user_id: int,
    profile_data: FacultyProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update faculty profile."""
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field in ["subjects_teaching", "expertise_areas", "skills", "certifications", "research_projects"]:
                setattr(profile, field, json.dumps(value))
            else:
                setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    user = db.query(User).filter(User.id == user_id).first()
    return faculty_profile_to_response(profile, user)


# ============== Industry Profile Endpoints ==============

@app.post("/api/industry/profile/{user_id}", response_model=IndustryProfileResponse)
def create_industry_profile(
    user_id: int,
    profile_data: IndustryProfileCreate,
    db: Session = Depends(get_db)
):
    """Create industry profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.INDUSTRY).first()
    if not user:
        raise HTTPException(status_code=404, detail="Industry user not found")
    
    existing = db.query(IndustryProfile).filter(IndustryProfile.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile = IndustryProfile(
        user_id=user_id,
        company_name=profile_data.company_name,
        industry_type=profile_data.industry_type,
        location=profile_data.location,
        size=profile_data.size,
        description=profile_data.description
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return industry_profile_to_response(profile, user)


@app.get("/api/industry/profile/{user_id}", response_model=IndustryProfileResponse)
def get_industry_profile(user_id: int, db: Session = Depends(get_db)):
    """Get industry profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.INDUSTRY).first()
    if not user:
        raise HTTPException(status_code=404, detail="Industry user not found")
    
    profile = db.query(IndustryProfile).filter(IndustryProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return industry_profile_to_response(profile, user)


@app.put("/api/industry/profile/{user_id}", response_model=IndustryProfileResponse)
def update_industry_profile(
    user_id: int,
    profile_data: IndustryProfileCreate,
    db: Session = Depends(get_db)
):
    """Update industry profile."""
    profile = db.query(IndustryProfile).filter(IndustryProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile.company_name = profile_data.company_name
    profile.industry_type = profile_data.industry_type
    profile.location = profile_data.location
    profile.size = profile_data.size
    profile.description = profile_data.description

    user = db.query(User).filter(User.id == user_id).first()
    
    db.commit()
    db.refresh(profile)
    
    return industry_profile_to_response(profile, user)


# ============== Opportunity Endpoints ==============

@app.post("/api/opportunities", response_model=OpportunityResponse)
def create_opportunity(
    opportunity: OpportunityCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create new opportunity."""
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


@app.get("/api/opportunities", response_model=list[OpportunityResponse])
def list_opportunities(
    type: str = None,
    skills: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List opportunities with filtering."""
    query = db.query(Opportunity)
    
    if type:
        query = query.filter(Opportunity.opportunity_type == type.lower())
    
    opportunities = query.offset(offset).limit(limit).all()
    
    # Apply skills filter
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


@app.get("/api/opportunities/{opp_id}", response_model=OpportunityResponse)
def get_opportunity(opp_id: int, db: Session = Depends(get_db)):
    """Get single opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return opportunity_to_response(opp)


@app.put("/api/opportunities/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(
    opp_id: int,
    opportunity: OpportunityCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Update opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or opp.industry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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


@app.delete("/api/opportunities/{opp_id}")
def delete_opportunity(opp_id: int, user_id: int, db: Session = Depends(get_db)):
    """Delete opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or opp.industry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(opp)
    db.commit()
    
    return {"message": "Opportunity deleted successfully", "success": True}


# ============== Helper Functions ==============

def profile_to_response(profile: StudentProfile, user: User) -> StudentProfileResponse:
    """Convert student profile to response."""
    return StudentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=user.name,
        email=user.email,
        branch=profile.branch,
        department=profile.department,
        batch=profile.batch,
        course=profile.course,
        semester=profile.semester,
        skills=json.loads(profile.skills) if profile.skills else [],
        technical_skills=json.loads(profile.technical_skills) if profile.technical_skills else [],
        certifications=json.loads(profile.certifications) if profile.certifications else [],
        projects=json.loads(profile.projects) if profile.projects else [],
        interests=json.loads(profile.interests) if profile.interests else [],
        career_goal=profile.career_goal,
        preferred_industry=profile.preferred_industry,
        other_info=profile.other_info
    )


def faculty_profile_to_response(profile: FacultyProfile, user: User) -> FacultyProfileResponse:
    """Convert faculty profile to response."""
    return FacultyProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        institute_id=profile.institute_id,
        name=user.name,
        email=user.email,
        department=profile.department,
        designation=profile.designation,
        subjects_teaching=json.loads(profile.subjects_teaching) if profile.subjects_teaching else [],
        expertise_areas=json.loads(profile.expertise_areas) if profile.expertise_areas else [],
        skills=json.loads(profile.skills) if profile.skills else [],
        experience_years=profile.experience_years,
        certifications=json.loads(profile.certifications) if profile.certifications else [],
        research_projects=json.loads(profile.research_projects) if profile.research_projects else []
    )


def industry_profile_to_response(profile: IndustryProfile, user: User) -> IndustryProfileResponse:
    """Convert industry profile to response."""
    return IndustryProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        company_name=profile.company_name,
        industry_type=profile.industry_type,
        location=profile.location,
        size=profile.size,
        description=profile.description
    )


def opportunity_to_response(opp: Opportunity) -> OpportunityResponse:
    """Convert opportunity to response."""
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


# ============== Sample Data Seeding ==============

@app.post("/api/seed/sample-data")
def seed_sample_data(db: Session = Depends(get_db)):
    """Seed sample data for demonstration."""
    # Check if data already exists
    if db.query(User).first():
        return {"message": "Sample data already exists", "success": False}
    
    # Create demo institutes (fictional AYUSH institutes - prototype data only)
    institutes = [
        Institute(name="Demo Institute of AYUSH Sciences", location="Pune, Maharashtra (Demo)", type="Demo / Fictional"),
        Institute(name="Demo College of Ayurveda", location="Lucknow, Uttar Pradesh (Demo)", type="Demo / Fictional"),
        Institute(name="Demo Homoeopathy & Wellness College", location="Rishikesh, Uttarakhand (Demo)", type="Demo / Fictional"),
        Institute(name="Demo Siddha & Unani College", location="Coimbatore, Tamil Nadu (Demo)", type="Demo / Fictional"),
    ]
    for inst in institutes:
        db.add(inst)
    db.flush()
    
    # Sample students
    students_data = [
        {
            "name": "Arjun Sharma",
            "email": "arjun.sharma@student.demoayush.edu",
            "password": "student123",
            "role": "student",
            "institute_id": 1,
            "profile": {
                "institute_id": 1,
                "branch": "Ayurveda",
                "department": "BAMS",
                "batch": 2028,
                "course": "Bachelor of Ayurvedic Medicine and Surgery",
                "semester": 6,
                "skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Research Methodology", "Research Design", "Literature Review", "Clinical Research", "Data Collection", "Research Documentation", "Basic Statistics", "Scientific Writing", "Research Ethics", "Communication", "Teamwork", "Critical Thinking"],
                "technical_skills": ["Spreadsheet Analysis", "Data Visualization", "Laboratory Techniques"],
                "certifications": ["Good Clinical Practice (GCP) Foundations (Demo)", "Research Methodology Workshop (Demo)"],
                "projects": [
                    {"title": "Panchakarma Outcome Documentation", "description": "Demo student project documenting observed Panchakarma outcomes (prototype data)"},
                    {"title": "AYUSH Research Data Dashboard", "description": "Demo spreadsheet dashboard built from a small AYUSH survey dataset"}
                ],
                "interests": ["Clinical Research", "Panchakarma", "Rasashastra & Bhaishajya Kalpana"],
                "career_goal": "Build a career in Clinical Research within the Ayurveda ecosystem (demo profile)",
                "preferred_industry": "AYUSH Research & Academia",
                "other_info": "Prototype demo record - fictional AYUSH student profile. Not a real person."
            }
        },
        {
            "name": "Priya Patel",
            "email": "priya.patel@student.demoayush.edu",
            "password": "student123",
            "role": "student",
            "institute_id": 2,
            "profile": {
                "institute_id": 2,
                "branch": "Yoga & Naturopathy",
                "department": "Yoga & Naturopathy Programme",
                "batch": 2027,
                "course": "Programme / Training in Yoga & Naturopathy",
                "semester": 4,
                "skills": ["Yoga Therapy", "Naturopathy Practices", "Lifestyle Counselling", "AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Communication", "Time Management", "Presentation", "Research Methodology", "Data Collection"],
                "technical_skills": ["Spreadsheet Analysis", "Data Visualization", "Research Documentation"],
                "certifications": ["Yoga Therapy Foundation Course (Demo)"],
                "projects": [
                    {"title": "Yoga Therapy Wellness Survey", "description": "Demo survey of yoga therapy and lifestyle practices"},
                    {"title": "AYUSH Research Data Dashboard", "description": "Demo spreadsheet dashboard built from a small AYUSH survey dataset"}
                ],
                "interests": ["Yoga Therapy", "Lifestyle & Wellness", "Public Health"],
                "career_goal": "Build a career in Yoga Therapy within the Yoga & Naturopathy ecosystem (demo profile)",
                "preferred_industry": "AYUSH Wellness & Yoga",
                "other_info": "Prototype demo record - fictional AYUSH student profile. Not a real person."
            }
        },
        {
            "name": "Rahul Kumar",
            "email": "rahul.kumar@student.demoayush.edu",
            "password": "student123",
            "role": "student",
            "institute_id": 3,
            "profile": {
                "institute_id": 3,
                "branch": "Unani",
                "department": "BUMS",
                "batch": 2027,
                "course": "Bachelor of Unani Medicine and Surgery",
                "semester": 8,
                "skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Pharmacology", "Materia Medica", "Pharmacy", "Laboratory Techniques", "Quality Control", "Professional Ethics", "Communication", "Critical Thinking"],
                "technical_skills": ["Instrumentation", "Laboratory Documentation", "Sample Handling"],
                "certifications": ["AYUSH Drug Quality Basics (Demo)", "Laboratory Safety & Good Lab Practices (Demo)"],
                "projects": [
                    {"title": "Unani Drug Quality Checklist", "description": "Demo checklist for quality parameters of Unani formulations"},
                    {"title": "Medicinal Plant Herbarium Record", "description": "Demo project cataloguing locally available medicinal plants (prototype data)"}
                ],
                "interests": ["Ilmul Advia", "Saidla / Pharmacy", "Clinical Practice"],
                "career_goal": "Build a career in Ilmul Advia within the Unani ecosystem (demo profile)",
                "preferred_industry": "AYUSH Pharmaceuticals",
                "other_info": "Prototype demo record - fictional AYUSH student profile. Not a real person."
            }
        },
        {
            "name": "Sneha Reddy",
            "email": "sneha.reddy@student.demoayush.edu",
            "password": "student123",
            "role": "student",
            "institute_id": 1,
            "profile": {
                "institute_id": 1,
                "branch": "Siddha",
                "department": "BSMS",
                "batch": 2028,
                "course": "Bachelor of Siddha Medicine and Surgery",
                "semester": 6,
                "skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Pharmacology", "Medicinal Plant Knowledge", "Laboratory Techniques", "Quality Control", "Quality Testing", "Research Methodology", "Data Collection", "Communication"],
                "technical_skills": ["Sample Handling", "Laboratory Documentation", "Statistical Interpretation"],
                "certifications": ["Medicinal Plant Identification Workshop (Demo)"],
                "projects": [
                    {"title": "Siddha Formulation Literature Review", "description": "Demo literature review of classical Siddha formulations"},
                    {"title": "Medicinal Plant Herbarium Record", "description": "Demo project cataloguing locally available medicinal plants (prototype data)"}
                ],
                "interests": ["Gunapadam", "Drug Standardization", "Medicinal Plant Research"],
                "career_goal": "Build a career in Drug Standardization within the Siddha ecosystem (demo profile)",
                "preferred_industry": "AYUSH Medicinal Plants",
                "other_info": "Prototype demo record - fictional AYUSH student profile. Not a real person."
            }
        },
        {
            "name": "Mohit Verma",
            "email": "mohit.verma@student.demoayush.edu",
            "password": "student123",
            "role": "student",
            "institute_id": 2,
            "profile": {
                "institute_id": 2,
                "branch": "Homoeopathy",
                "department": "BHMS",
                "batch": 2027,
                "course": "Bachelor of Homoeopathic Medicine and Surgery",
                "semester": 8,
                "skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Materia Medica", "Pharmacology", "Pharmacy", "Research Methodology", "Research Documentation", "Scientific Writing", "Communication", "Problem Solving"],
                "technical_skills": ["Laboratory Techniques", "Laboratory Documentation", "Presentation"],
                "certifications": ["Research Documentation & Ethics (Demo)"],
                "projects": [
                    {"title": "Homoeopathic Case Record Study", "description": "Demo compilation of teaching case records for academic practice"},
                    {"title": "AYUSH Research Data Dashboard", "description": "Demo spreadsheet dashboard built from a small AYUSH survey dataset"}
                ],
                "interests": ["Materia Medica", "Clinical Practice", "Clinical Research"],
                "career_goal": "Build a career in Materia Medica within the Homoeopathy ecosystem (demo profile)",
                "preferred_industry": "AYUSH Clinical Care",
                "other_info": "Prototype demo record - fictional AYUSH student profile. Not a real person."
            }
        },
        {
            "name": "Sonam Wangchuk",
            "email": "sonam.wangchuk@student.demoayush.edu",
            "password": "student123",
            "role": "student",
            "institute_id": 3,
            "profile": {
                "institute_id": 3,
                "branch": "Sowa-Rigpa",
                "department": "BSRMS",
                "batch": 2029,
                "course": "Bachelor of Sowa-Rigpa Medicine and Surgery",
                "semester": 4,
                "skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Materia Medica", "Medicinal Plant Knowledge", "Research Documentation", "Literature Review", "Communication", "Professional Ethics", "Data Collection"],
                "technical_skills": ["Laboratory Techniques", "Spreadsheet Analysis", "Presentation"],
                "certifications": ["Research Documentation & Ethics (Demo)"],
                "projects": [
                    {"title": "Sowa-Rigpa Practice Documentation", "description": "Demo documentation of traditional Sowa-Rigpa practice workflows"},
                    {"title": "Medicinal Plant Herbarium Record", "description": "Demo project cataloguing locally available medicinal plants (prototype data)"}
                ],
                "interests": ["Traditional Medicine Research", "Documentation", "Clinical Practice"],
                "career_goal": "Build a career in Traditional Medicine Research within the Sowa-Rigpa ecosystem (demo profile)",
                "preferred_industry": "AYUSH Research & Academia",
                "other_info": "Prototype demo record - fictional AYUSH student profile. Not a real person."
            }
        },
    ]
    
    for s_data in students_data:
        user = User(
            email=s_data["email"],
            password_hash=generate_password_hash(s_data["password"]),
            name=s_data["name"],
            role=UserRole.STUDENT,
            institute_id=s_data["institute_id"]
        )
        db.add(user)
        db.flush()
        
        profile = StudentProfile(
            user_id=user.id,
            **s_data["profile"]
        )
        # Convert lists to JSON strings
        for field in ["skills", "technical_skills", "certifications", "projects", "interests"]:
            if field in s_data["profile"]:
                setattr(profile, field, json.dumps(s_data["profile"][field]))
        
        db.add(profile)
    
    # Sample faculty
    faculty_data = [
        {
            "name": "Dr. Vikram Singh",
            "email": "vikram.singh@demoayush.edu",
            "password": "faculty123",
            "role": "faculty",
            "institute_id": 1,
            "profile": {
                "institute_id": 1,
                "department": "Ayurveda - Kayachikitsa",
                "designation": "Professor",
                "subjects_teaching": ["Kayachikitsa", "Roga Nidana & Vikriti Vigyana", "Samhita & Siddhanta", "Research Methodology"],
                "expertise_areas": ["Ayurveda Clinical Practice", "Clinical Research", "Research Methodology"],
                "skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Research Methodology", "Clinical Research", "Scientific Writing", "Project Management", "Professional Ethics"],
                "experience_years": 18,
                "certifications": ["Good Clinical Practice (GCP) Foundations (Demo)", "Research Methodology Workshop (Demo)"],
                "research_projects": [
                    {"title": "Panchakarma Outcome Documentation", "funding": "Demo Institute Seed Grant (fictional)"},
                    {"title": "Ayurveda Case Record Registry", "funding": "Demo Research Fund (fictional)"}
                ]
            }
        },
        {
            "name": "Prof. Anjali Mehta",
            "email": "anjali.mehta@demoayush.edu",
            "password": "faculty123",
            "role": "faculty",
            "institute_id": 2,
            "profile": {
                "institute_id": 2,
                "department": "Yoga & Naturopathy",
                "designation": "Associate Professor",
                "subjects_teaching": ["Yoga Therapy", "Naturopathy Practices", "Lifestyle & Wellness", "Yoga Research"],
                "expertise_areas": ["Yoga Therapy", "Lifestyle & Wellness", "Public Health"],
                "skills": ["Yoga Therapy", "Naturopathy Practices", "Lifestyle Counselling", "Healthcare Practices", "Research Methodology", "Data Collection", "Communication"],
                "experience_years": 12,
                "certifications": ["Yoga Therapy Foundation Course (Demo)"],
                "research_projects": [
                    {"title": "Yoga Therapy for Lifestyle Disorders", "funding": "Demo Wellness Grant (fictional)"},
                    {"title": "Wellness Programme Survey", "funding": "Demo Institute Seed Grant (fictional)"}
                ]
            }
        },
    ]
    
    for f_data in faculty_data:
        user = User(
            email=f_data["email"],
            password_hash=generate_password_hash(f_data["password"]),
            name=f_data["name"],
            role=UserRole.FACULTY,
            institute_id=f_data["institute_id"]
        )
        db.add(user)
        db.flush()
        
        profile = FacultyProfile(
            user_id=user.id,
            **f_data["profile"]
        )
        for field in ["subjects_teaching", "expertise_areas", "skills", "certifications", "research_projects"]:
            if field in f_data["profile"]:
                setattr(profile, field, json.dumps(f_data["profile"][field]))
        
        db.add(profile)
    
    # Sample industry profiles
    industry_data = [
        {
            "name": "Demo Clinical Research Organisation",
            "email": "hr@democro.example.com",
            "password": "industry123",
            "role": "industry",
            "profile": {
                "company_name": "Demo Clinical Research Organisation",
                "industry_type": "Clinical Research",
                "location": "Hyderabad, Telangana (Demo)",
                "size": "Medium",
                "description": "Fictional contract research organisation used in this prototype. Runs demo AYUSH clinical research and documentation workflows. (Fictional demo organisation used only for prototype demonstration.)"
            }
        },
        {
            "name": "Demo AYUSH Pharmaceutical Pvt. Ltd.",
            "email": "hr@demoayushpharma.example.com",
            "password": "industry123",
            "role": "industry",
            "profile": {
                "company_name": "Demo AYUSH Pharmaceutical Pvt. Ltd.",
                "industry_type": "AYUSH Pharmaceuticals",
                "location": "Pune, Maharashtra (Demo)",
                "size": "Medium",
                "description": "Fictional AYUSH pharmaceutical company used for prototype demonstration. (Fictional demo organisation used only for prototype demonstration.)"
            }
        },
        {
            "name": "Demo AYUSH Hospital",
            "email": "admin@demoayushhospital.example.com",
            "password": "industry123",
            "role": "industry",
            "profile": {
                "company_name": "Demo AYUSH Hospital",
                "industry_type": "AYUSH Healthcare",
                "location": "Lucknow, Uttar Pradesh (Demo)",
                "size": "Large",
                "description": "Fictional multi-system AYUSH hospital used only for prototype demonstration. (Fictional demo organisation used only for prototype demonstration.)"
            }
        },
        {
            "name": "Demo Wellness Institute",
            "email": "contact@demowellness.example.com",
            "password": "industry123",
            "role": "industry",
            "profile": {
                "company_name": "Demo Wellness Institute",
                "industry_type": "Wellness & Yoga",
                "location": "Rishikesh, Uttarakhand (Demo)",
                "size": "Small",
                "description": "Fictional yoga and naturopathy wellness institute created for demo data. (Fictional demo organisation used only for prototype demonstration.)"
            }
        },
    ]
    
    for i_data in industry_data:
        user = User(
            email=i_data["email"],
            password_hash=generate_password_hash(i_data["password"]),
            name=i_data["name"],
            role=UserRole.INDUSTRY
        )
        db.add(user)
        db.flush()
        
        profile = IndustryProfile(
            user_id=user.id,
            **i_data["profile"]
        )
        db.add(profile)
    
    # Sample opportunities
    opportunities_data = [
        {
            "industry_email": "hr@democro.example.com",
            "profile": {
                "title": "Clinical Research Internship - Ayurveda",
                "opportunity_type": "internship",
                "required_skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Research Methodology", "Clinical Research", "Data Collection", "Research Documentation", "Basic Statistics", "Scientific Writing"],
                "eligibility": {"ayush_system": ["Ayurveda"], "programme": "BAMS / MD (Ayurveda)", "year": "3rd year UG and above", "career_area": "Clinical Research", "skill_level": "Intermediate", "duration": "6 months"},
                "description": "Demo/prototype opportunity (fictional). Support a demo AYUSH clinical research team with literature review, case-record documentation and basic data entry. Open only to Ayurveda (BAMS / MD Ayurveda) candidates.",
                "location": "Hyderabad, Telangana (Demo)",
                "mode": "On-site",
                "deadline": "2027-01-31",
                "stipend": "Rs.15,000/month (demo)"
            }
        },
        {
            "industry_email": "contact@demowellness.example.com",
            "profile": {
                "title": "Yoga Therapy Internship",
                "opportunity_type": "internship",
                "required_skills": ["Yoga Therapy", "Naturopathy Practices", "Lifestyle Counselling", "AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Communication", "Presentation"],
                "eligibility": {"ayush_system": ["Yoga & Naturopathy"], "programme": "Yoga & Naturopathy Programme / Certificate in Yoga Therapy", "year": "2nd year and above", "career_area": "Yoga Therapy", "skill_level": "Beginner", "duration": "4 months"},
                "description": "Demo/prototype opportunity (fictional). Assist with demo yoga therapy and lifestyle counselling sessions for wellness programme participants. Open only to Yoga & Naturopathy candidates.",
                "location": "Rishikesh, Uttarakhand (Demo)",
                "mode": "On-site",
                "deadline": "2027-02-10",
                "stipend": "Rs.8,000/month (demo)"
            }
        },
        {
            "industry_email": "admin@demoayushhospital.example.com",
            "profile": {
                "title": "Homoeopathic Physician",
                "opportunity_type": "job",
                "required_skills": ["AYUSH System Knowledge", "Clinical Knowledge", "Healthcare Practices", "Materia Medica", "Communication", "Critical Thinking", "Professional Ethics"],
                "eligibility": {"ayush_system": ["Homoeopathy"], "programme": "BHMS (MD Homoeopathy preferred)", "year": "Graduates / PG", "career_area": "Clinical Practice", "skill_level": "Intermediate", "duration": "Full time"},
                "description": "Demo/prototype opportunity (fictional). Homoeopathic outpatient practice with case taking and Materia Medica reference work. Open only to Homoeopathy (BHMS / MD Homoeopathy) candidates.",
                "location": "Lucknow, Uttar Pradesh (Demo)",
                "mode": "On-site",
                "deadline": "2027-05-15",
                "stipend": "Rs.5-8 LPA (demo)"
            }
        },
        {
            "industry_email": "hr@demoayushpharma.example.com",
            "profile": {
                "title": "Quality Control Analyst - AYUSH Formulations",
                "opportunity_type": "job",
                "required_skills": ["Quality Control", "Quality Testing", "Laboratory Documentation", "Laboratory Techniques", "Sample Handling", "Instrumentation", "Pharmacology"],
                "eligibility": {"ayush_system": ["Ayurveda", "Unani", "Homoeopathy", "Siddha"], "programme": "BAMS / BUMS / BHMS / BSMS", "year": "Graduates / PG", "career_area": "Quality Control", "skill_level": "Intermediate", "duration": "Full time"},
                "description": "Demo/prototype opportunity (fictional). Sample testing, documentation and specification checks for AYUSH formulations. Open only to the four listed AYUSH systems.",
                "location": "Pune, Maharashtra (Demo)",
                "mode": "On-site",
                "deadline": "2027-04-20",
                "stipend": "Rs.4-7 LPA (demo)"
            }
        },
        {
            "industry_email": "hr@democro.example.com",
            "profile": {
                "title": "Workshop - Scientific Writing for AYUSH Journals",
                "opportunity_type": "event",
                "required_skills": ["Scientific Writing", "Research Methodology", "Evidence Synthesis", "Research Documentation", "Presentation"],
                "eligibility": {"ayush_system": ["Ayurveda", "Yoga & Naturopathy", "Unani", "Siddha", "Homoeopathy", "Sowa-Rigpa"], "programme": "Any AYUSH programme", "year": "PG and faculty", "career_area": "Research & Development", "skill_level": "Intermediate", "duration": "2 days"},
                "description": "Demo/prototype workshop (fictional) on structuring manuscripts, reporting standards and referencing for AYUSH research outputs. Open to candidates from all six AYUSH systems listed in eligibility.",
                "location": "Online (Demo)",
                "mode": "Remote",
                "deadline": "2026-12-10",
                "stipend": "Free (demo)"
            }
        },
        {
            "industry_email": "hr@democro.example.com",
            "profile": {
                "title": "Training Programme - Medical Statistics for AYUSH Research",
                "opportunity_type": "skill-program",
                "required_skills": ["Basic Statistics", "Biostatistics", "Data Analysis", "Data Visualization", "Statistical Interpretation", "Spreadsheet Analysis", "Data Cleaning"],
                "eligibility": {"ayush_system": ["Ayurveda", "Yoga & Naturopathy", "Unani", "Siddha", "Homoeopathy", "Sowa-Rigpa"], "programme": "Any AYUSH programme (PG preferred)", "year": "PG / early career", "career_area": "Data & Research Analytics", "skill_level": "Beginner", "duration": "6 weeks"},
                "description": "Demo/prototype training programme (fictional) covering descriptive statistics, spreadsheet analysis and reporting for AYUSH research. Open to candidates from all six AYUSH systems listed in eligibility.",
                "location": "Online (Demo)",
                "mode": "Remote",
                "deadline": "2026-12-15",
                "stipend": "Free (demo)"
            }
        },
    ]
    
    for o_data in opportunities_data:
        industry_user = db.query(User).filter(User.email == o_data["industry_email"]).first()
        if industry_user:
            industry_profile = db.query(IndustryProfile).filter(IndustryProfile.user_id == industry_user.id).first()
            if industry_profile:
                opp = Opportunity(
                    industry_id=industry_profile.id,
                    **o_data["profile"]
                )
                for field in ["required_skills", "eligibility"]:
                    if field in o_data["profile"]:
                        setattr(opp, field, json.dumps(o_data["profile"][field]))
                
                db.add(opp)
    
    db.commit()
    
    return {
        "message": "Sample data seeded successfully",
        "success": True,
        "data": {
            "students": len(students_data),
            "faculty": len(faculty_data),
            "industries": len(industry_data),
            "opportunities": len(opportunities_data),
            "institutes": len(institutes)
        }
    }


# ============== Quiz Endpoints ================

@app.get("/api/jobs/{job_id}/quiz")
def get_quiz_for_opportunity(job_id: int, db: Session = Depends(get_db)):
    """Get quiz associated with a job/internship opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == job_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    if not opp.quiz or not opp.quiz.is_active:
        return {"quiz": None, "message": "No active quiz available for this opportunity"}
    
    quiz = opp.quiz
    questions = []
    for q in quiz.questions:
        questions.append({
            "id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "skill_tag": q.skill_tag,
            "difficulty": q.difficulty
        })
    
    return {
        "quiz": {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "passing_score": quiz.passing_score,
            "time_limit_minutes": quiz.time_limit_minutes,
            "question_count": len(quiz.questions),
            "questions": questions
        }
    }


@app.post("/api/jobs/{job_id}/quiz/attempt")
def submit_quiz_attempt(job_id: int, attempt_data: QuizAttemptSubmit, user_id: int, db: Session = Depends(get_db)):
    """Submit a quiz attempt."""
    # Get the opportunity and quiz
    opp = db.query(Opportunity).filter(Opportunity.id == job_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    if not opp.quiz or not opp.quiz.is_active:
        raise HTTPException(status_code=404, detail="No active quiz for this opportunity")
    
    quiz = opp.quiz
    
    # Validate answers
    answers = []
    correct_count = 0
    skill_stats = {}  # skill_tag -> {correct, total}
    
    for answer_submit in attempt_data.answers:
        question = db.query(QuizQuestion).filter(QuizQuestion.id == answer_submit.question_id).first()
        if not question or question.quiz_id != quiz.id:
            raise HTTPException(status_code=400, detail=f"Invalid question ID: {answer_submit.question_id}")
        
        is_correct = answer_submit.selected_option == question.correct_option
        if is_correct:
            correct_count += 1
        
        # Track by skill
        skill_tag = question.skill_tag or "general"
        if skill_tag not in skill_stats:
            skill_stats[skill_tag] = {"correct": 0, "total": 0}
        skill_stats[skill_tag]["total"] += 1
        if is_correct:
            skill_stats[skill_tag]["correct"] += 1
        
        answers.append({
            "question_id": question.id,
            "selected_option": answer_submit.selected_option,
            "correct_option": question.correct_option,
            "is_correct": is_correct,
            "skill_tag": question.skill_tag
        })
    
    # Calculate score
    total_questions = len(quiz.questions)
    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    passed = score_percentage >= (quiz.passing_score or 50)
    
    # Create attempt record
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=user_id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=score_percentage
    )
    db.add(attempt)
    db.flush()
    
    # Create answer records
    for ans in answers:
        attempt_answer = AttemptAnswer(
            attempt_id=attempt.id,
            question_id=ans["question_id"],
            selected_option=ans["selected_option"],
            is_correct=ans["is_correct"],
            skill_tag=ans["skill_tag"]
        )
        db.add(attempt_answer)
    
    db.commit()
    
    # Build skill scores
    skill_scores = []
    for skill_tag, stats in skill_stats.items():
        percentage = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        skill_scores.append({
            "skill_tag": skill_tag,
            "total_questions": stats["total"],
            "correct_answers": stats["correct"],
            "percentage": round(percentage, 2)
        })
    
    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "total_questions": total_questions,
        "correct_answers": correct_count,
        "score_percentage": round(score_percentage, 2),
        "passed": passed,
        "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
        "answers": answers,
        "skill_scores": skill_scores
    }


@app.get("/api/students/{student_id}/quiz-results")
def get_student_quiz_results(student_id: int, db: Session = Depends(get_db)):
    """Get quiz results for a student."""
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    
    attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == student_id).all()
    
    results = []
    for attempt in attempts:
        quiz = attempt.quiz
        
        # Calculate skill scores
        skill_stats = {}
        for answer in attempt.answers:
            skill_tag = answer.skill_tag or "general"
            if skill_tag not in skill_stats:
                skill_stats[skill_tag] = {"correct": 0, "total": 0}
            skill_stats[skill_tag]["total"] += 1
            if answer.is_correct:
                skill_stats[skill_tag]["correct"] += 1
        
        skill_scores = []
        for skill_tag, stats in skill_stats.items():
            percentage = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            skill_scores.append({
                "skill_tag": skill_tag,
                "total_questions": stats["total"],
                "correct_answers": stats["correct"],
                "percentage": round(percentage, 2)
            })
        
        results.append({
            "attempt_id": attempt.id,
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "score_percentage": round(attempt.score_percentage, 2),
            "passed": attempt.score_percentage >= (quiz.passing_score or 50),
            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
            "skill_scores": skill_scores
        })
    
    return {"results": results, "total_attempts": len(results)}


@app.post("/api/opportunities/{opp_id}/quiz", response_model=QuizResponse)
def create_quiz_for_opportunity(opp_id: int, quiz_data: QuizCreate, user_id: int, db: Session = Depends(get_db)):
    """Create a quiz for an opportunity (industry only)."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.INDUSTRY).first()
    if not user:
        raise HTTPException(status_code=403, detail="Only industry users can create quizzes")
    
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Verify ownership
    if opp.industry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to add quiz to this opportunity")
    
    # Check if quiz already exists
    existing_quiz = db.query(Quiz).filter(Quiz.opportunity_id == opp_id).first()
    if existing_quiz:
        raise HTTPException(status_code=400, detail="Quiz already exists for this opportunity")
    
    # Create quiz
    quiz = Quiz(
        opportunity_id=opp_id,
        title=quiz_data.title,
        description=quiz_data.description,
        passing_score=quiz_data.passing_score,
        time_limit_minutes=quiz_data.time_limit_minutes,
        is_active=True
    )
    db.add(quiz)
    db.flush()
    
    # Create questions
    for q_data in quiz_data.questions:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q_data.question_text,
            option_a=q_data.option_a,
            option_b=q_data.option_b,
            option_c=q_data.option_c,
            option_d=q_data.option_d,
            correct_option=q_data.correct_option,
            skill_tag=q_data.skill_tag,
            difficulty=q_data.difficulty
        )
        db.add(question)
    
    db.commit()
    db.refresh(quiz)
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "passing_score": quiz.passing_score,
        "time_limit_minutes": quiz.time_limit_minutes,
        "is_active": quiz.is_active,
        "question_count": len(quiz_data.questions),
        "created_at": quiz.created_at
    }


# ============== Institute Analytics Endpoints ================

@app.get("/api/institute/{institute_id}/skill-distribution")
def get_institute_skill_distribution(institute_id: int, db: Session = Depends(get_db)):
    """Get skill distribution for an institute."""
    students = db.query(StudentProfile).filter(StudentProfile.institute_id == institute_id).all()
    
    # Count skills
    skill_counts = {}
    skill_levels = {}  # For average proficiency
    
    for student in students:
        skills = json.loads(student.skills) if student.skills else []
        technical_skills = json.loads(student.technical_skills) if student.technical_skills else []
        all_skills = skills + technical_skills
        
        for skill in all_skills:
            skill = skill.strip()
            if skill:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
                # For proficiency, we track count (in real app would have proficiency level)
                if skill not in skill_levels:
                    skill_levels[skill] = []
                skill_levels[skill].append(3.0)  # Default level (would come from profile)
    
    # Calculate averages
    skill_distribution = []
    for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True):
        avg_level = sum(skill_levels[skill]) / len(skill_levels[skill]) if skill_levels[skill] else 0
        skill_distribution.append({
            "skill": skill,
            "count": count,
            "percentage": round(count / len(students) * 100, 1) if students else 0,
            "average_proficiency": round(avg_level, 2)
        })
    
    return {
        "institute_id": institute_id,
        "total_students": len(students),
        "skill_distribution": skill_distribution[:20],  # Top 20 skills
        "total_skills": len(skill_counts)
    }


@app.get("/api/institute/{institute_id}/internships")
def get_institute_internship_analytics(institute_id: int, db: Session = Depends(get_db)):
    """Get internship/employment analytics for an institute."""
    students = db.query(StudentProfile).filter(StudentProfile.institute_id == institute_id).all()
    
    total_students = len(students)
    
    # Get all opportunities
    opportunities = db.query(Opportunity).all()
    
    # Categorize opportunities
    internship_count = sum(1 for o in opportunities if o.opportunity_type == "internship")
    job_count = sum(1 for o in opportunities if o.opportunity_type == "job")
    event_count = sum(1 for o in opportunities if o.opportunity_type == "event")
    skill_program_count = sum(1 for o in opportunities if o.opportunity_type == "skill-program")
    
    # Count students by preferred industry
    industry_interests = {}
    for student in students:
        industry = student.preferred_industry or "Unspecified"
        industry_interests[industry] = industry_interests.get(industry, 0) + 1
    
    # Count students by career goal
    career_goals = {}
    for student in students:
        goal = student.career_goal or "Not specified"
        career_goals[goal] = career_goals.get(goal, 0) + 1
    
    return {
        "institute_id": institute_id,
        "total_students": total_students,
        "internship_opportunities": internship_count,
        "job_opportunities": job_count,
        "event_opportunities": event_count,
        "skill_program_opportunities": skill_program_count,
        "total_opportunities": len(opportunities),
        "industry_interests": [
            {"industry": k, "count": v, "percentage": round(v / total_students * 100, 1) if total_students else 0}
            for k, v in sorted(industry_interests.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
        "career_goals": [
            {"goal": k, "count": v}
            for k, v in sorted(career_goals.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
    }


# Import at end to avoid circular imports
from werkzeug.security import check_password_hash
