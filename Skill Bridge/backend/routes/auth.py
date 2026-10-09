"""Authentication routes: login, signup."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, UserRole, StudentProfile, FacultyProfile, IndustryProfile, Institute
from backend.schemas import (
    LoginRequest, SignupRequest, AuthResponse,
    StudentProfileCreate, StudentProfileResponse,
    FacultyProfileCreate, FacultyProfileResponse,
    IndustryProfileCreate, IndustryProfileResponse
)
from werkzeug.security import generate_password_hash, check_password_hash
import json

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def serialize_user(user: User) -> dict:
    """Serialize user to response format."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value if user.role else None,
        "institute_id": user.institute_id
    }


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return session info."""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not check_password_hash(user.password_hash, request.password):
        return AuthResponse(
            success=False,
            message="Invalid email or password"
        )
    
    return AuthResponse(
        success=True,
        user_id=user.id,
        name=user.name,
        role=user.role.value if user.role else None
    )


@router.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        return AuthResponse(
            success=False,
            message="Email already registered"
        )
    
    # Create user
    password_hash = generate_password_hash(request.password)
    user = User(
        email=request.email,
        password_hash=password_hash,
        name=request.name,
        role=UserRole(request.role)
    )
    db.add(user)
    db.flush()  # Get the user ID
    
    # Create institute if this is an institute signup
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
        profile = IndustryProfile(
            user_id=user.id,
            company_name=request.name  # Default company name to user name
        )
        db.add(profile)
    
    db.commit()
    
    return AuthResponse(
        success=True,
        user_id=user.id,
        name=user.name,
        role=user.role.value
    )


@router.get("/me/{user_id}", response_model=dict)
def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """Get current user info."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return serialize_user(user)


# ============== Student Profile Routes ==============

@router.post("/student/profile/{user_id}", response_model=StudentProfileResponse)
def create_student_profile(
    user_id: int,
    profile_data: StudentProfileCreate,
    db: Session = Depends(get_db)
):
    """Create student profile after signup."""
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


@router.get("/student/profile/{user_id}", response_model=StudentProfileResponse)
def get_student_profile(user_id: int, db: Session = Depends(get_db)):
    """Get student profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.STUDENT).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student user not found")
    
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile_to_response(profile, user)


@router.put("/student/profile/{user_id}", response_model=StudentProfileResponse)
def update_student_profile(
    user_id: int,
    profile_data: StudentProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update student profile."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_fields = []
    if profile_data.branch is not None:
        profile.branch = profile_data.branch
        update_fields.append("branch")
    if profile_data.department is not None:
        profile.department = profile_data.department
        update_fields.append("department")
    if profile_data.batch is not None:
        profile.batch = profile_data.batch
        update_fields.append("batch")
    if profile_data.course is not None:
        profile.course = profile_data.course
        update_fields.append("course")
    if profile_data.semester is not None:
        profile.semester = profile_data.semester
        update_fields.append("semester")
    if profile_data.skills is not None:
        profile.skills = json.dumps(profile_data.skills)
        update_fields.append("skills")
    if profile_data.technical_skills is not None:
        profile.technical_skills = json.dumps(profile_data.technical_skills)
        update_fields.append("technical_skills")
    if profile_data.certifications is not None:
        profile.certifications = json.dumps(profile_data.certifications)
        update_fields.append("certifications")
    if profile_data.projects is not None:
        profile.projects = json.dumps(profile_data.projects)
        update_fields.append("projects")
    if profile_data.interests is not None:
        profile.interests = json.dumps(profile_data.interests)
        update_fields.append("interests")
    if profile_data.career_goal is not None:
        profile.career_goal = profile_data.career_goal
        update_fields.append("career_goal")
    if profile_data.preferred_industry is not None:
        profile.preferred_industry = profile_data.preferred_industry
        update_fields.append("preferred_industry")
    if profile_data.other_info is not None:
        profile.other_info = profile_data.other_info
        update_fields.append("other_info")
    
    if update_fields:
        db.commit()
        db.refresh(profile)
    
    user = db.query(User).filter(User.id == user_id).first()
    return profile_to_response(profile, user)


# ============== Faculty Profile Routes ==============

@router.post("/faculty/profile/{user_id}", response_model=FacultyProfileResponse)
def create_faculty_profile(
    user_id: int,
    profile_data: FacultyProfileCreate,
    db: Session = Depends(get_db)
):
    """Create faculty profile after signup."""
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


@router.get("/faculty/profile/{user_id}", response_model=FacultyProfileResponse)
def get_faculty_profile(user_id: int, db: Session = Depends(get_db)):
    """Get faculty profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.FACULTY).first()
    if not user:
        raise HTTPException(status_code=404, detail="Faculty user not found")
    
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return faculty_profile_to_response(profile, user)


@router.put("/faculty/profile/{user_id}", response_model=FacultyProfileResponse)
def update_faculty_profile(
    user_id: int,
    profile_data: FacultyProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update faculty profile."""
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if profile_data.department is not None:
        profile.department = profile_data.department
    if profile_data.designation is not None:
        profile.designation = profile_data.designation
    if profile_data.subjects_teaching is not None:
        profile.subjects_teaching = json.dumps(profile_data.subjects_teaching)
    if profile_data.expertise_areas is not None:
        profile.expertise_areas = json.dumps(profile_data.expertise_areas)
    if profile_data.skills is not None:
        profile.skills = json.dumps(profile_data.skills)
    if profile_data.experience_years is not None:
        profile.experience_years = profile_data.experience_years
    if profile_data.certifications is not None:
        profile.certifications = json.dumps(profile_data.certifications)
    if profile_data.research_projects is not None:
        profile.research_projects = json.dumps(profile_data.research_projects)
    
    db.commit()
    db.refresh(profile)
    
    user = db.query(User).filter(User.id == user_id).first()
    return faculty_profile_to_response(profile, user)


# ============== Industry Profile Routes ==============

@router.post("/industry/profile/{user_id}", response_model=IndustryProfileResponse)
def create_industry_profile(
    user_id: int,
    profile_data: IndustryProfileCreate,
    db: Session = Depends(get_db)
):
    """Create industry/company profile."""
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
    
    return profile_to_response(profile, user)


@router.get("/industry/profile/{user_id}", response_model=IndustryProfileResponse)
def get_industry_profile(user_id: int, db: Session = Depends(get_db)):
    """Get industry profile."""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.INDUSTRY).first()
    if not user:
        raise HTTPException(status_code=404, detail="Industry user not found")
    
    profile = db.query(IndustryProfile).filter(IndustryProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile_to_response(profile, user)


@router.put("/industry/profile/{user_id}", response_model=IndustryProfileResponse)
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
    
    db.commit()
    db.refresh(profile)
    
    return profile_to_response(profile, user)


# ============== Helpers ==============

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


def profile_to_response(profile: IndustryProfile, user: User) -> IndustryProfileResponse:
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
