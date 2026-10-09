"""SIH Platform - AYUSH Ecosystem Seed Script for DEMO/PROTOTYPE DATA.

This script generates clearly-labelled SAMPLE data for the platform so that the
existing dashboards demonstrate the AYUSH ecosystem:

- 50 AYUSH students across the six AYUSH systems (Ayurveda, Yoga & Naturopathy,
  Unani, Siddha, Homoeopathy, Sowa-Rigpa) with programme, career area and skills
- Faculty members from each AYUSH system
- Fictional "Demo ..." organisations (no real company or government body is used)
- ~53 demo opportunities (internships, jobs, research projects, training
  programmes, FDPs, workshops, mentorship, consultancy and live projects)
- A couple of AYUSH skill-assessment quizzes

IMPORTANT: Every record created here is fictional demo/prototype data. It must
never be presented as a real opportunity, partnership, vacancy, statistic or
government endorsement.

Run with: python -m backend.seed
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal, Base
from backend.models import (
    User, UserRole, StudentProfile, FacultyProfile,
    IndustryProfile, Institute, Opportunity, Quiz, QuizQuestion
)
from werkzeug.security import generate_password_hash

# Shown to students in the free-text profile field so demo records are obvious.
DEMO_NOTE = (
    "Prototype demo record - fictional AYUSH student profile created for "
    "demonstration purposes. Not a real person, result or endorsement."
)

DEMO_ORG_NOTE = "(Fictional demo organisation used only for prototype demonstration.)"

# ============================================================================
# AYUSH reference data
# ============================================================================

AYUSH_SYSTEMS = [
    "Ayurveda",
    "Yoga & Naturopathy",
    "Unani",
    "Siddha",
    "Homoeopathy",
    "Sowa-Rigpa",
]

# Academic programmes. Yoga & Naturopathy intentionally uses programme/training
# labels only (no invented degree).
SYSTEM_PROGRAMMES = {
    "Ayurveda": {
        "ug": "BAMS",
        "ug_name": "Bachelor of Ayurvedic Medicine and Surgery",
        "pg": "MD (Ayurveda)",
        "pg_name": "MD Ayurveda",
    },
    "Yoga & Naturopathy": {
        "ug": "Yoga & Naturopathy Programme",
        "ug_name": "Programme / Training in Yoga & Naturopathy",
        "pg": "PG Diploma (Yoga Therapy)",
        "pg_name": "PG Diploma in Yoga Therapy / Advanced Yoga & Naturopathy Programme",
    },
    "Unani": {
        "ug": "BUMS",
        "ug_name": "Bachelor of Unani Medicine and Surgery",
        "pg": "MD (Unani)",
        "pg_name": "MD Unani",
    },
    "Siddha": {
        "ug": "BSMS",
        "ug_name": "Bachelor of Siddha Medicine and Surgery",
        "pg": "MD (Siddha)",
        "pg_name": "MD Siddha",
    },
    "Homoeopathy": {
        "ug": "BHMS",
        "ug_name": "Bachelor of Homoeopathic Medicine and Surgery",
        "pg": "MD (Homoeopathy)",
        "pg_name": "MD Homoeopathy",
    },
    "Sowa-Rigpa": {
        "ug": "BSRMS",
        "ug_name": "Bachelor of Sowa-Rigpa Medicine and Surgery",
        "pg": "MD (Sowa-Rigpa)",
        "pg_name": "MD Sowa-Rigpa",
    },
}

# Career areas that are shared across multiple AYUSH systems.
COMMON_CAREER_AREAS = [
    "Clinical Research",
    "Research & Development",
    "AYUSH Pharmacy",
    "Quality Control",
    "Quality Assurance",
    "Medicinal Plant Research",
    "Pharmacological Research",
    "Hospital Administration",
    "Healthcare Operations",
    "Public Health",
    "Data & Research Analytics",
    "Laboratory Research",
    "Digital Health",
    "Teaching / Academia",
    "Healthcare Management",
]

# System-specific career areas.
SYSTEM_CAREER_AREAS = {
    "Ayurveda": [
        "Kayachikitsa", "Shalya Tantra", "Shalakya Tantra", "Kaumarabhritya",
        "Prasuti Tantra & Stri Roga", "Panchakarma", "Dravyaguna Vigyana",
        "Rasashastra & Bhaishajya Kalpana", "Rachana Sharira", "Kriya Sharira",
        "Samhita & Siddhanta", "Swasthavritta & Yoga",
        "Roga Nidana & Vikriti Vigyana",
    ],
    "Yoga & Naturopathy": [
        "Yoga Instruction", "Yoga Therapy", "Yoga Wellness", "Naturopathy",
        "Lifestyle & Wellness", "Preventive Health", "Health Promotion",
        "Yoga Education", "Yoga Research", "Wellness Programme Management",
    ],
    "Unani": [
        "Clinical Practice", "Ilmul Advia", "Moalajat",
        "Tahaffuzi wa Samaji Tib", "Ilmul Qabalat-o-Nauma", "Saidla / Pharmacy",
        "Drug Standardization", "Research",
    ],
    "Siddha": [
        "Clinical Practice", "Siddha Pharmacology", "Gunapadam",
        "Traditional Medicine Research", "Drug Standardization",
        "Pharmacological Research",
    ],
    "Homoeopathy": [
        "Clinical Practice", "Materia Medica", "Organon / Clinical Studies",
        "Pharmacy", "Research Methodology", "Drug / Product Quality",
        "Documentation", "Health Research",
    ],
    "Sowa-Rigpa": [
        "Clinical Practice", "Traditional Medicine Research",
        "Pharmacology / Materia-related Studies", "Documentation",
        "Quality & Research", "Healthcare Administration",
    ],
}

# AYUSH sectors used as the student "preferred_industry" (drives the institute
# career-interest chart).
AYUSH_SECTORS = [
    "AYUSH Clinical Care",
    "AYUSH Pharmaceuticals",
    "AYUSH Research & Academia",
    "AYUSH Public Health",
    "AYUSH Wellness & Yoga",
    "AYUSH Quality & Regulatory",
    "AYUSH Digital Health",
    "AYUSH Medicinal Plants",
]

# ---------------------------------------------------------------------------
# Canonical AYUSH skill vocabulary (must match backend/services/skill_analysis.py
# and the required_skills of the demo opportunities for gap analysis to work).
# ---------------------------------------------------------------------------
S = {
    "sys": "AYUSH System Knowledge",
    "clin": "Clinical Knowledge",
    "prac": "Healthcare Practices",
    "pharm": "Pharmacology",
    "pharmacy": "Pharmacy",
    "materia": "Materia Medica",
    "plant": "Medicinal Plant Knowledge",
    "qc": "Quality Control",
    "rm": "Research Methodology",
    "rd": "Research Design",
    "lit": "Literature Review",
    "ev": "Evidence Synthesis",
    "cr": "Clinical Research",
    "fr": "Fundamental Research",
    "eth": "Research Ethics",
    "sw": "Scientific Writing",
    "doc": "Research Documentation",
    "dc": "Data Collection",
    "di": "Data Interpretation",
    "stat": "Basic Statistics",
    "bio": "Biostatistics",
    "clean": "Data Cleaning",
    "da": "Data Analysis",
    "dv": "Data Visualization",
    "spread": "Spreadsheet Analysis",
    "si": "Statistical Interpretation",
    "rdb": "Research Database Management",
    "lt": "Laboratory Techniques",
    "mb": "Molecular Biology",
    "sh": "Sample Handling",
    "ld": "Laboratory Documentation",
    "qt": "Quality Testing",
    "ls": "Laboratory Safety",
    "inst": "Instrumentation",
    "comm": "Communication",
    "team": "Teamwork",
    "ps": "Problem Solving",
    "ct": "Critical Thinking",
    "tm": "Time Management",
    "pres": "Presentation",
    "lead": "Leadership",
    "pm": "Project Management",
    "pe": "Professional Ethics",
    "yoga": "Yoga Therapy",
    "nat": "Naturopathy Practices",
    "lc": "Lifestyle Counselling",
}

# Reusable skill groups composed from the canonical vocabulary above.
DOMAIN_CORE = [S["sys"], S["clin"], S["prac"]]
PHARMACY_SKILLS = [S["pharm"], S["pharmacy"], S["materia"]]
PLANT_SKILLS = [S["plant"], S["pharm"]]
RESEARCH_SKILLS = [S["rm"], S["rd"], S["lit"], S["ev"], S["eth"]]
CLIN_RESEARCH_SKILLS = [S["cr"], S["dc"], S["doc"], S["stat"]]
WRITING_SKILLS = [S["sw"], S["doc"], S["pres"]]
DATA_SKILLS = [S["stat"], S["bio"], S["clean"], S["da"], S["dv"], S["spread"], S["si"], S["rdb"]]
LAB_SKILLS = [S["lt"], S["sh"], S["qt"], S["ld"], S["ls"], S["inst"], S["mb"]]
QUALITY_SKILLS = [S["qc"], S["qt"], S["ld"], S["pe"]]
PROFESSIONAL_SKILLS = [
    S["comm"], S["team"], S["ps"], S["ct"], S["tm"], S["pres"], S["lead"], S["pm"], S["pe"],
]
YOGA_SKILLS = [S["yoga"], S["nat"], S["lc"]]


def _skills(*groups):
    """Flatten skill groups into a de-duplicated ordered list."""
    merged = []
    for group in groups:
        for skill in group:
            if skill not in merged:
                merged.append(skill)
    return merged


# Student career focus per system -> (career_area, skill profile).
SYSTEM_FOCUS = {
    "Ayurveda": [
        ("Clinical Research", _skills(DOMAIN_CORE, RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS, PROFESSIONAL_SKILLS)),
        ("Panchakarma", _skills(DOMAIN_CORE, PROFESSIONAL_SKILLS, [S["tm"], S["comm"]])),
        ("Rasashastra & Bhaishajya Kalpana", _skills(PHARMACY_SKILLS, LAB_SKILLS, QUALITY_SKILLS, PROFESSIONAL_SKILLS)),
        ("Dravyaguna Vigyana", _skills(PLANT_SKILLS, LAB_SKILLS, RESEARCH_SKILLS, [S["fr"]], PROFESSIONAL_SKILLS)),
        ("Swasthavritta & Yoga", _skills(DOMAIN_CORE, DATA_SKILLS[:4], PROFESSIONAL_SKILLS)),
        ("Hospital Administration", _skills(DOMAIN_CORE, [S["pm"], S["lead"], S["comm"], S["tm"], S["da"], S["spread"]])),
    ],
    "Yoga & Naturopathy": [
        ("Yoga Therapy", _skills(YOGA_SKILLS, DOMAIN_CORE, PROFESSIONAL_SKILLS)),
        ("Naturopathy", _skills(YOGA_SKILLS, DOMAIN_CORE, [S["lc"], S["comm"]])),
        ("Yoga Research", _skills(YOGA_SKILLS, RESEARCH_SKILLS, WRITING_SKILLS, PROFESSIONAL_SKILLS)),
        ("Public Health", _skills(DOMAIN_CORE, DATA_SKILLS[:5], PROFESSIONAL_SKILLS)),
        ("Wellness Programme Management", _skills(YOGA_SKILLS, [S["pm"], S["lead"], S["comm"], S["tm"], S["pres"]])),
    ],
    "Unani": [
        ("Clinical Practice", _skills(DOMAIN_CORE, PROFESSIONAL_SKILLS)),
        ("Clinical Research", _skills(DOMAIN_CORE, RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS, PROFESSIONAL_SKILLS)),
        ("Ilmul Advia", _skills(PHARMACY_SKILLS, PLANT_SKILLS, LAB_SKILLS, PROFESSIONAL_SKILLS)),
        ("Saidla / Pharmacy", _skills(PHARMACY_SKILLS, QUALITY_SKILLS, LAB_SKILLS, PROFESSIONAL_SKILLS)),
        ("Moalajat", _skills(DOMAIN_CORE, [S["cr"], S["dc"], S["comm"], S["ct"], S["pe"]])),
        ("Tahaffuzi wa Samaji Tib", _skills(DOMAIN_CORE, DATA_SKILLS[:4], PROFESSIONAL_SKILLS)),
    ],
    "Siddha": [
        ("Clinical Practice", _skills(DOMAIN_CORE, PROFESSIONAL_SKILLS)),
        ("Gunapadam", _skills(PHARMACY_SKILLS, PLANT_SKILLS, LAB_SKILLS, PROFESSIONAL_SKILLS)),
        ("Drug Standardization", _skills(QUALITY_SKILLS, LAB_SKILLS, DATA_SKILLS[:4], PROFESSIONAL_SKILLS)),
        ("Traditional Medicine Research", _skills(DOMAIN_CORE, RESEARCH_SKILLS, WRITING_SKILLS, PROFESSIONAL_SKILLS)),
        ("Medicinal Plant Research", _skills(PLANT_SKILLS, LAB_SKILLS, RESEARCH_SKILLS, PROFESSIONAL_SKILLS)),
        ("Public Health", _skills(DOMAIN_CORE, DATA_SKILLS[:5], PROFESSIONAL_SKILLS)),
    ],
    "Homoeopathy": [
        ("Clinical Practice", _skills(DOMAIN_CORE, PROFESSIONAL_SKILLS)),
        ("Materia Medica", _skills(PHARMACY_SKILLS, RESEARCH_SKILLS, PROFESSIONAL_SKILLS)),
        ("Pharmacy", _skills(PHARMACY_SKILLS, QUALITY_SKILLS, LAB_SKILLS, PROFESSIONAL_SKILLS)),
        ("Clinical Research", _skills(DOMAIN_CORE, RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS, PROFESSIONAL_SKILLS)),
        ("Organon / Clinical Studies", _skills(DOMAIN_CORE, RESEARCH_SKILLS, [S["cr"], S["sw"], S["comm"]])),
        ("Public Health", _skills(DOMAIN_CORE, DATA_SKILLS[:4], PROFESSIONAL_SKILLS)),
    ],
    "Sowa-Rigpa": [
        ("Clinical Practice", _skills(DOMAIN_CORE, PROFESSIONAL_SKILLS)),
        ("Traditional Medicine Research", _skills(DOMAIN_CORE, RESEARCH_SKILLS, WRITING_SKILLS, PROFESSIONAL_SKILLS)),
        ("Pharmacology / Materia-related Studies", _skills(PHARMACY_SKILLS, PLANT_SKILLS, LAB_SKILLS, PROFESSIONAL_SKILLS)),
        ("Documentation", _skills(WRITING_SKILLS, RESEARCH_SKILLS, [S["comm"], S["pe"]])),
        ("Public Health", _skills(DOMAIN_CORE, DATA_SKILLS[:4], PROFESSIONAL_SKILLS)),
    ],
}

# Number of demo students per AYUSH system (50 total).
SYSTEM_STUDENT_COUNTS = {
    "Ayurveda": 12,
    "Yoga & Naturopathy": 8,
    "Unani": 8,
    "Siddha": 8,
    "Homoeopathy": 8,
    "Sowa-Rigpa": 6,
}

FIRST_NAMES = [
    "Arjun", "Priya", "Rahul", "Sneha", "Vikram", "Anjali", "Karthik", "Divya",
    "Suresh", "Meena", "Ravi", "Lakshmi", "Amit", "Pooja", "Naveen", "Kavya",
    "Mohit", "Riya", "Shankar", "Deepa", "Aditya", "Neha", "Vineeth", "Sravani",
    "Prasad", "Trisha", "Rakesh", "Anisha", "Manoj", "Keerthi", "Srinivas", "Madhuri",
    "Dinesh", "Swathi", "Ranjith", "Nandini", "Venkat", "Sindhu", "Dheeraj", "Tejaswi",
    "Praveen", "Shruti", "Sanjay", "Lokesh", "Mahesh", "Suraj", "Chandra", "Prem",
    "Bala", "Karthick",
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Reddy", "Singh", "Mehta", "Iyer", "Anand",
    "Murthy", "Kaur", "Joshi", "Banerjee", "Agarwal", "Chaturvedi", "Nair", "Shenoy",
    "Hegde", "Pillai", "Kapoor", "Bahl", "Choudhary", "Trivedi", "Shah", "Dalal",
    "Rao", "Menon", "Kulkarni", "Wagh", "Bhat", "Sastry", "Lakshman", "Mishra",
    "Moorthy", "Nadkarni", "Kamat", "Prabhu", "Gaonkar", "Bhandari", "Thakur", "Verma",
    "Malhotra", "Chadha", "Bedi", "Garg", "Bansal", "Aggarwal", "Deshpande", "Jain",
    "Gupta", "Qureshi",
]

# Demo certifications (generic training labels, no real endorsements).
CERTIFICATIONS = [
    ["Good Clinical Practice (GCP) Foundations (Demo)", "Research Methodology Workshop (Demo)"],
    ["Basic Biostatistics with Spreadsheet Tools (Demo)"],
    ["AYUSH Drug Quality Basics (Demo)", "Laboratory Safety & Good Lab Practices (Demo)"],
    ["Medicinal Plant Identification Workshop (Demo)"],
    ["Panchakarma Assistant Training (Demo)"],
    ["Yoga Therapy Foundation Course (Demo)"],
    ["Research Documentation & Ethics (Demo)"],
]

# Demo student projects.
PROJECTS = [
    {"title": "Panchakarma Outcome Documentation", "description": "Demo student project documenting observed Panchakarma outcomes (prototype data)"},
    {"title": "Medicinal Plant Herbarium Record", "description": "Demo project cataloguing locally available medicinal plants (prototype data)"},
    {"title": "Homoeopathic Case Record Study", "description": "Demo compilation of teaching case records for academic practice"},
    {"title": "Siddha Formulation Literature Review", "description": "Demo literature review of classical Siddha formulations"},
    {"title": "Unani Drug Quality Checklist", "description": "Demo checklist for quality parameters of Unani formulations"},
    {"title": "Sowa-Rigpa Practice Documentation", "description": "Demo documentation of traditional Sowa-Rigpa practice workflows"},
    {"title": "Yoga Therapy Wellness Survey", "description": "Demo survey of yoga therapy and lifestyle practices"},
    {"title": "AYUSH Research Data Dashboard", "description": "Demo spreadsheet dashboard built from a small AYUSH survey dataset"},
]


def _career_areas(system):
    """Full career-area pool (system specific + common) for a system."""
    return SYSTEM_CAREER_AREAS[system] + COMMON_CAREER_AREAS


# ============================================================================
# Demo organisations (all fictional)
# ============================================================================

INDUSTRY_DATA = [
    {
        "name": "Demo AYUSH Pharmaceutical Pvt. Ltd.",
        "email": "hr@demoayushpharma.example.com",
        "company_name": "Demo AYUSH Pharmaceutical Pvt. Ltd.",
        "industry_type": "AYUSH Pharmaceuticals",
        "location": "Pune, Maharashtra (Demo)",
        "size": "Medium",
        "description": "Fictional AYUSH pharmaceutical company used for prototype demonstration. Covers formulations, quality control and regulatory workflows. " + DEMO_ORG_NOTE,
    },
    {
        "name": "Demo Herbal Research Labs",
        "email": "careers@demoherballabs.example.com",
        "company_name": "Demo Herbal Research Labs",
        "industry_type": "Medicinal Plant Research",
        "location": "Coimbatore, Tamil Nadu (Demo)",
        "size": "Small",
        "description": "Fictional herbal research laboratory created for demo purposes. Focus areas include medicinal plant screening and standardization. " + DEMO_ORG_NOTE,
    },
    {
        "name": "Demo Clinical Research Organisation",
        "email": "hr@democro.example.com",
        "company_name": "Demo Clinical Research Organisation",
        "industry_type": "Clinical Research",
        "location": "Hyderabad, Telangana (Demo)",
        "size": "Medium",
        "description": "Fictional contract research organisation used in this prototype. Runs demo AYUSH clinical research and documentation workflows. " + DEMO_ORG_NOTE,
    },
    {
        "name": "Demo AYUSH Hospital",
        "email": "admin@demoayushhospital.example.com",
        "company_name": "Demo AYUSH Hospital",
        "industry_type": "AYUSH Healthcare",
        "location": "Lucknow, Uttar Pradesh (Demo)",
        "size": "Large",
        "description": "Fictional multi-system AYUSH hospital used only for prototype demonstration. " + DEMO_ORG_NOTE,
    },
    {
        "name": "Demo Wellness Institute",
        "email": "contact@demowellness.example.com",
        "company_name": "Demo Wellness Institute",
        "industry_type": "Wellness & Yoga",
        "location": "Rishikesh, Uttarakhand (Demo)",
        "size": "Small",
        "description": "Fictional yoga and naturopathy wellness institute created for demo data. " + DEMO_ORG_NOTE,
    },
    {
        "name": "Demo Digital Health Startup",
        "email": "jobs@demodigitalhealth.example.com",
        "company_name": "Demo Digital Health Startup",
        "industry_type": "Digital Health",
        "location": "Bengaluru, Karnataka (Demo)",
        "size": "Startup",
        "description": "Fictional digital health startup used in this prototype. Demo work on AYUSH health apps and research data dashboards. " + DEMO_ORG_NOTE,
    },
    {
        "name": "Demo Medicinal Plants Organisation",
        "email": "research@demomedplants.example.com",
        "company_name": "Demo Medicinal Plants Organisation",
        "industry_type": "Medicinal Plants",
        "location": "Jodhpur, Rajasthan (Demo)",
        "size": "Medium",
        "description": "Fictional medicinal plants organisation created for prototype data. " + DEMO_ORG_NOTE,
    },
    {
        "name": "Demo Research University",
        "email": "faculty@demoresearchuniv.example.com",
        "company_name": "Demo Research University",
        "industry_type": "AYUSH Research & Academia",
        "location": "New Delhi, Delhi (Demo)",
        "size": "Large",
        "description": "Fictional AYUSH research university used only for demonstration. " + DEMO_ORG_NOTE,
    },
]


def _opp(org_email, title, opp_type, systems, programme, year, career_area,
         skills, level, duration, location, mode, deadline, stipend, description):
    """Build one demo opportunity record in the shape used by the seeder."""
    return {
        "industry_email": org_email,
        "title": title,
        "type": opp_type,
        "skills": skills,
        "eligibility": {
            "ayush_system": systems,
            "programme": programme,
            "year": year,
            "career_area": career_area,
            "skill_level": level,
            "duration": duration,
        },
        "description": description + " (Demo/prototype data - not a real opportunity.)",
        "location": location,
        "mode": mode,
        "deadline": deadline,
        "stipend": stipend,
    }


CRO = "hr@democro.example.com"
PHARMA = "hr@demoayushpharma.example.com"
HERBAL = "careers@demoherballabs.example.com"
HOSPITAL = "admin@demoayushhospital.example.com"
WELLNESS = "contact@demowellness.example.com"
DIGITAL = "jobs@demodigitalhealth.example.com"
PLANTS = "research@demomedplants.example.com"
UNIVERSITY = "faculty@demoresearchuniv.example.com"

ALL_SYSTEMS = list(AYUSH_SYSTEMS)

OPPORTUNITIES_DATA = [
    # ------------------------- Internships (10) -------------------------
    _opp(CRO, "Clinical Research Internship - Ayurveda", "internship",
         ["Ayurveda"], "BAMS / MD (Ayurveda)", "3rd year UG and above", "Clinical Research",
         _skills(DOMAIN_CORE, RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS),
         "Intermediate", "6 months", "Hyderabad, Telangana", "On-site", "2027-01-31", "Rs.15,000/month (demo)",
         "Support a demo AYUSH clinical research team with literature review, case-record documentation and basic data entry. Open only to Ayurveda (BAMS / MD Ayurveda) candidates."),
    _opp(CRO, "Clinical Research Internship - Homoeopathy", "internship",
         ["Homoeopathy"], "BHMS / MD (Homoeopathy)", "3rd year UG and above", "Clinical Research",
         _skills(DOMAIN_CORE, RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS),
         "Intermediate", "6 months", "Hyderabad, Telangana", "Hybrid", "2027-02-15", "Rs.14,000/month (demo)",
         "Demo homoeopathy clinical research internship involving documentation, consent records and basic statistics. Open only to Homoeopathy (BHMS / MD Homoeopathy) candidates."),
    _opp(CRO, "Clinical Research Internship - Unani", "internship",
         ["Unani"], "BUMS / MD (Unani)", "3rd year UG and above", "Clinical Research",
         _skills(DOMAIN_CORE, RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS),
         "Intermediate", "6 months", "Hyderabad, Telangana", "On-site", "2027-02-28", "Rs.14,000/month (demo)",
         "Demo Unani clinical research internship covering protocol support, data collection and documentation. Open only to Unani (BUMS / MD Unani) candidates."),
    _opp(HOSPITAL, "Panchakarma Therapy Internship", "internship",
         ["Ayurveda"], "BAMS", "4th year UG and above", "Panchakarma",
         _skills(DOMAIN_CORE, PROFESSIONAL_SKILLS, [S["tm"]]),
         "Beginner", "3 months", "Lucknow, Uttar Pradesh", "On-site", "2026-12-20", "Rs.10,000/month (demo)",
         "Observe and assist demo Panchakarma procedures under supervision, with patient counselling practice. Open only to Ayurveda (BAMS) candidates."),
    _opp(HERBAL, "Siddha Drug Standardization Internship", "internship",
         ["Siddha"], "BSMS", "Final year UG or PG", "Drug Standardization",
         _skills(DOMAIN_CORE, PHARMACY_SKILLS, PLANT_SKILLS, LAB_SKILLS, QUALITY_SKILLS),
         "Intermediate", "4 months", "Coimbatore, Tamil Nadu", "On-site", "2027-01-15", "Rs.12,000/month (demo)",
         "Demo laboratory internship on standardization parameters of Siddha formulations. Open only to Siddha (BSMS / MD Siddha) candidates."),
    _opp(PLANTS, "Medicinal Plant Documentation Internship", "internship",
         ["Ayurveda", "Siddha", "Unani"], "BAMS / BSMS / BUMS", "Any UG year", "Medicinal Plant Research",
         _skills(PLANT_SKILLS, LAB_SKILLS, RESEARCH_SKILLS, WRITING_SKILLS),
         "Beginner", "3 months", "Jodhpur, Rajasthan", "On-site", "2027-03-10", "Rs.9,000/month (demo)",
         "Field and herbarium documentation of medicinal plants used in Ayurveda, Siddha and Unani practice. Explicitly limited to those three systems."),
    _opp(WELLNESS, "Yoga Therapy Internship", "internship",
         ["Yoga & Naturopathy"], "Yoga & Naturopathy Programme / Certificate in Yoga Therapy", "2nd year and above", "Yoga Therapy",
         _skills(YOGA_SKILLS, DOMAIN_CORE, PROFESSIONAL_SKILLS),
         "Beginner", "4 months", "Rishikesh, Uttarakhand", "On-site", "2027-02-10", "Rs.8,000/month (demo)",
         "Assist with demo yoga therapy and lifestyle counselling sessions for wellness programme participants. Open only to Yoga & Naturopathy candidates."),
    _opp(PHARMA, "Homoeopathic Pharmacy Internship", "internship",
         ["Homoeopathy"], "BHMS", "Final year UG", "Pharmacy",
         _skills(PHARMACY_SKILLS, QUALITY_SKILLS, LAB_SKILLS, PROFESSIONAL_SKILLS),
         "Beginner", "3 months", "Pune, Maharashtra", "On-site", "2027-01-20", "Rs.10,000/month (demo)",
         "Demo internship in homoeopathic pharmacy dispensing, labelling and quality documentation. Open only to Homoeopathy (BHMS) candidates."),
    _opp(DIGITAL, "AYUSH Research Data Internship", "internship",
         ["Ayurveda", "Homoeopathy", "Unani"], "BAMS / BHMS / BUMS", "3rd year UG and above", "Data & Research Analytics",
         _skills(DATA_SKILLS, RESEARCH_SKILLS, PROFESSIONAL_SKILLS),
         "Intermediate", "6 months", "Remote (demo)", "Remote", "2027-03-31", "Rs.12,000/month (demo)",
         "Clean, structure and visualise demo AYUSH research datasets in spreadsheets and dashboards. Explicitly limited to Ayurveda, Homoeopathy and Unani candidates."),
    _opp(HOSPITAL, "Sowa-Rigpa Clinical Documentation Internship", "internship",
         ["Sowa-Rigpa"], "BSRMS", "3rd year UG and above", "Documentation",
         _skills(DOMAIN_CORE, WRITING_SKILLS, RESEARCH_SKILLS),
         "Beginner", "3 months", "Leh, Ladakh (Demo)", "On-site", "2027-02-05", "Rs.9,000/month (demo)",
         "Documentation of demo Sowa-Rigpa clinical workflows and traditional medicine records. Open only to Sowa-Rigpa (BSRMS) candidates."),

    # ---------------------------- Jobs (11) ----------------------------
    _opp(HOSPITAL, "Ayurveda Physician", "job",
         ["Ayurveda"], "BAMS (MD Ayurveda preferred)", "Graduates / PG", "Clinical Practice",
         _skills(DOMAIN_CORE, [S["comm"], S["ct"], S["pe"], S["tm"]]),
         "Intermediate", "Full time", "Lucknow, Uttar Pradesh", "On-site", "2027-04-30", "Rs.5-8 LPA (demo)",
         "Demo clinical practice role in an AYUSH hospital outpatient department. Open only to Ayurveda (BAMS / MD Ayurveda) candidates."),
    _opp(HOSPITAL, "Unani Physician", "job",
         ["Unani"], "BUMS (MD Unani preferred)", "Graduates / PG", "Clinical Practice",
         _skills(DOMAIN_CORE, [S["comm"], S["ct"], S["pe"]]),
         "Intermediate", "Full time", "Lucknow, Uttar Pradesh", "On-site", "2027-04-30", "Rs.5-8 LPA (demo)",
         "Demo Unani clinical practice role covering Moalajat and outpatient care. Open only to Unani (BUMS / MD Unani) candidates."),
    _opp(HOSPITAL, "Siddha Physician", "job",
         ["Siddha"], "BSMS (MD Siddha preferred)", "Graduates / PG", "Clinical Practice",
         _skills(DOMAIN_CORE, [S["comm"], S["ct"], S["pe"]]),
         "Intermediate", "Full time", "Madurai, Tamil Nadu (Demo)", "On-site", "2027-05-15", "Rs.5-8 LPA (demo)",
         "Demo Siddha clinical practice role in an integrated AYUSH hospital setting. Open only to Siddha (BSMS / MD Siddha) candidates."),
    _opp(HOSPITAL, "Homoeopathic Physician", "job",
         ["Homoeopathy"], "BHMS (MD Homoeopathy preferred)", "Graduates / PG", "Clinical Practice",
         _skills(DOMAIN_CORE, [S["materia"], S["comm"], S["ct"], S["pe"]]),
         "Intermediate", "Full time", "Lucknow, Uttar Pradesh", "On-site", "2027-05-15", "Rs.5-8 LPA (demo)",
         "Demo homoeopathic outpatient practice with case taking and Materia Medica reference work. Open only to Homoeopathy (BHMS / MD Homoeopathy) candidates."),
    _opp(HOSPITAL, "Sowa-Rigpa Practitioner", "job",
         ["Sowa-Rigpa"], "BSRMS (MD Sowa-Rigpa preferred)", "Graduates / PG", "Clinical Practice",
         _skills(DOMAIN_CORE, [S["comm"], S["ct"], S["pe"]]),
         "Intermediate", "Full time", "Leh, Ladakh (Demo)", "On-site", "2027-06-15", "Rs.5-7 LPA (demo)",
         "Demo Sowa-Rigpa practice role in a traditional medicine unit. Open only to Sowa-Rigpa (BSRMS / MD Sowa-Rigpa) candidates."),
    _opp(CRO, "Clinical Research Associate - AYUSH", "job",
         ALL_SYSTEMS, "Any AYUSH graduate programme (BAMS/BUMS/BSMS/BSRMS/BHMS/Yoga & Naturopathy)", "Graduates / PG", "Clinical Research",
         _skills(RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS, DATA_SKILLS[:4], PROFESSIONAL_SKILLS),
         "Intermediate", "Full time", "Hyderabad, Telangana", "Hybrid", "2027-05-31", "Rs.4-6 LPA (demo)",
         "Demo CRA role coordinating documentation and monitoring for AYUSH studies. Explicitly open to graduates of all six AYUSH systems listed in eligibility."),
    _opp(PHARMA, "Quality Control Analyst - AYUSH Formulations", "job",
         ["Ayurveda", "Unani", "Homoeopathy", "Siddha"], "BAMS / BUMS / BHMS / BSMS", "Graduates / PG", "Quality Control",
         _skills(QUALITY_SKILLS, LAB_SKILLS, [S["pharm"]]),
         "Intermediate", "Full time", "Pune, Maharashtra", "On-site", "2027-04-20", "Rs.4-7 LPA (demo)",
         "Demo QC role covering sample testing, documentation and specification checks for AYUSH formulations. Open only to the four listed AYUSH systems."),
    _opp(HERBAL, "Laboratory Technician - Drug Standardization", "job",
         ["Siddha", "Ayurveda", "Unani"], "BSMS / BAMS / BUMS", "Graduates", "Laboratory Research",
         _skills(LAB_SKILLS, QUALITY_SKILLS, PLANT_SKILLS),
         "Beginner", "Full time", "Coimbatore, Tamil Nadu", "On-site", "2027-03-25", "Rs.3-5 LPA (demo)",
         "Demo laboratory technician role supporting pharmacopoeial testing of medicinal plant and formulation samples."),
    _opp(HOSPITAL, "AYUSH Hospital Administrator", "job",
         ["Ayurveda", "Homoeopathy", "Yoga & Naturopathy"], "BAMS / BHMS / Yoga & Naturopathy Programme", "Graduates / PG", "Hospital Administration",
         _skills(DOMAIN_CORE, [S["pm"], S["lead"], S["comm"], S["da"], S["spread"], S["pe"]]),
         "Advanced", "Full time", "Lucknow, Uttar Pradesh", "On-site", "2027-05-20", "Rs.6-9 LPA (demo)",
         "Demo hospital administration role covering operations, records and reporting for AYUSH service units."),
    _opp(UNIVERSITY, "Public Health Research Assistant", "job",
         ["Yoga & Naturopathy", "Ayurveda", "Homoeopathy"], "Any listed AYUSH programme", "Graduates / PG", "Public Health",
         _skills(DATA_SKILLS, RESEARCH_SKILLS, PROFESSIONAL_SKILLS),
         "Intermediate", "Full time", "New Delhi, Delhi (Demo)", "Hybrid", "2027-06-10", "Rs.4-6 LPA (demo)",
         "Demo public health research support role for community AYUSH and lifestyle studies."),
    _opp(DIGITAL, "Healthcare Data Analyst - AYUSH", "job",
         ["Ayurveda", "Unani", "Homoeopathy"], "BAMS / BUMS / BHMS", "Graduates / PG", "Data & Research Analytics",
         _skills(DATA_SKILLS, [S["cr"], S["di"], S["comm"], S["ps"]]),
         "Intermediate", "Full time", "Bengaluru, Karnataka", "Hybrid", "2027-06-30", "Rs.5-8 LPA (demo)",
         "Demo analyst role building AYUSH research and wellness dashboards from de-identified demo datasets."),

    # ---------------------- Research Projects (6) ----------------------
    _opp(UNIVERSITY, "Research Project - Panchakarma Outcome Documentation", "skill-program",
         ["Ayurveda"], "BAMS / MD (Ayurveda)", "PG and final year UG", "Clinical Research",
         _skills(RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, WRITING_SKILLS),
         "Intermediate", "9 months", "New Delhi, Delhi (Demo)", "Hybrid", "2027-01-10", "Rs.12,000/month (demo)",
         "Demo research project documenting Panchakarma outcomes using a structured observation sheet. Ayurveda candidates only."),
    _opp(UNIVERSITY, "Research Project - Quality Parameters of Homoeopathic Formulations", "skill-program",
         ["Homoeopathy"], "BHMS / MD (Homoeopathy)", "PG and final year UG", "Drug / Product Quality",
         _skills(QUALITY_SKILLS, LAB_SKILLS, RESEARCH_SKILLS),
         "Intermediate", "9 months", "New Delhi, Delhi (Demo)", "On-site", "2027-01-25", "Rs.12,000/month (demo)",
         "Demo research project on quality parameters and documentation of homoeopathic formulations. Homoeopathy candidates only."),
    _opp(UNIVERSITY, "Research Project - Documentation of Sowa-Rigpa Formulations", "skill-program",
         ["Sowa-Rigpa"], "BSRMS / MD (Sowa-Rigpa)", "PG and final year UG", "Traditional Medicine Research",
         _skills(RESEARCH_SKILLS, WRITING_SKILLS, [S["materia"], S["pe"]]),
         "Intermediate", "9 months", "Leh, Ladakh (Demo)", "Hybrid", "2027-02-20", "Rs.12,000/month (demo)",
         "Demo research project compiling formulation documentation from Sowa-Rigpa literature. Sowa-Rigpa candidates only."),
    _opp(HERBAL, "Research Project - In-vitro Screening of Medicinal Plants", "skill-program",
         ["Ayurveda", "Siddha"], "BAMS / BSMS", "PG and final year UG", "Pharmacological Research",
         _skills(PLANT_SKILLS, LAB_SKILLS, RESEARCH_SKILLS, [S["fr"]], DATA_SKILLS[:3]),
         "Intermediate", "8 months", "Coimbatore, Tamil Nadu", "On-site", "2027-03-15", "Rs.11,000/month (demo)",
         "Demo laboratory screening project for medicinal plant extracts. Explicitly limited to Ayurveda and Siddha candidates."),
    _opp(WELLNESS, "Research Project - Yoga Therapy for Lifestyle Disorders", "skill-program",
         ["Yoga & Naturopathy"], "Yoga & Naturopathy Programme / PG Diploma (Yoga Therapy)", "PG and final year", "Yoga Research",
         _skills(YOGA_SKILLS, RESEARCH_SKILLS, DATA_SKILLS[:4], WRITING_SKILLS),
         "Intermediate", "8 months", "Rishikesh, Uttarakhand", "Hybrid", "2027-02-28", "Rs.10,000/month (demo)",
         "Demo research project evaluating yoga therapy and lifestyle counselling protocols. Yoga & Naturopathy candidates only."),
    _opp(UNIVERSITY, "Research Project - Pharmacopoeial Standards for Unani Drugs", "skill-program",
         ["Unani"], "BUMS / MD (Unani)", "PG and final year UG", "Drug Standardization",
         _skills(QUALITY_SKILLS, LAB_SKILLS, RESEARCH_SKILLS, [S["materia"]]),
         "Advanced", "10 months", "New Delhi, Delhi (Demo)", "On-site", "2027-03-05", "Rs.13,000/month (demo)",
         "Demo research project on pharmacopoeial standards for selected Unani formulations. Unani candidates only."),

    # ---------------------- Training Programmes (6) ----------------------
    _opp(UNIVERSITY, "Training Programme - Medical Statistics for AYUSH Research", "skill-program",
         ALL_SYSTEMS, "Any AYUSH programme (PG preferred)", "PG / early career", "Data & Research Analytics",
         _skills([S["stat"], S["bio"], S["da"], S["dv"], S["si"], S["spread"], S["clean"]]),
         "Beginner", "6 weeks", "Online (Demo)", "Remote", "2026-12-15", "Free (demo)",
         "Demo training programme covering descriptive statistics, spreadsheet analysis and reporting for AYUSH research."),
    _opp(UNIVERSITY, "Training Programme - Research Methodology for AYUSH Postgraduates", "skill-program",
         ["Ayurveda", "Unani", "Siddha", "Homoeopathy", "Sowa-Rigpa"], "MD / PG AYUSH programmes", "PG students", "Research & Development",
         _skills(RESEARCH_SKILLS, [S["sw"], S["doc"], S["pres"]]),
         "Intermediate", "8 weeks", "Online (Demo)", "Remote", "2027-01-05", "Rs.2,000 fee (demo)",
         "Demo programme on study design, literature review and scientific writing for AYUSH postgraduate research."),
    _opp(CRO, "Training Programme - Good Clinical Practice for AYUSH Studies", "skill-program",
         ["Ayurveda", "Homoeopathy", "Unani"], "BAMS / BHMS / BUMS", "Final year UG and PG", "Clinical Research",
         _skills([S["cr"], S["eth"], S["doc"], S["dc"], S["rd"]]),
         "Intermediate", "4 weeks", "Online (Demo)", "Remote", "2027-01-18", "Rs.1,500 fee (demo)",
         "Demo GCP-oriented training programme for AYUSH clinical study teams and coordinators."),
    _opp(HOSPITAL, "Training Programme - Panchakarma Assistant Training", "skill-program",
         ["Ayurveda"], "BAMS / Panchakarma training background", "3rd year UG and above", "Panchakarma",
         _skills(DOMAIN_CORE, [S["tm"], S["comm"], S["pe"], S["prac"]]),
         "Beginner", "6 weeks", "Lucknow, Uttar Pradesh", "On-site", "2027-02-22", "Rs.3,000 fee (demo)",
         "Demo hands-on Panchakarma assistant training programme with supervised practice sessions. Ayurveda candidates only."),
    _opp(HERBAL, "Training Programme - AYUSH Drug Standardization Techniques", "skill-program",
         ["Siddha", "Ayurveda", "Unani", "Homoeopathy"], "BSMS / BAMS / BUMS / BHMS", "Final year UG and PG", "Quality Assurance",
         _skills(LAB_SKILLS, QUALITY_SKILLS, [S["inst"]]),
         "Intermediate", "6 weeks", "Coimbatore, Tamil Nadu", "Hybrid", "2027-03-20", "Rs.2,500 fee (demo)",
         "Demo training on quality testing, instrumentation basics and documentation for AYUSH drug standardization."),
    _opp(DIGITAL, "Training Programme - Research Data Management for AYUSH Studies", "skill-program",
         ALL_SYSTEMS, "Any AYUSH programme", "Any year", "Data & Research Analytics",
         _skills([S["rdb"], S["clean"], S["spread"], S["dc"], S["da"], S["eth"]]),
         "Beginner", "5 weeks", "Online (Demo)", "Remote", "2027-02-01", "Free (demo)",
         "Demo training programme on data cleaning, spreadsheet workflows and research database management for AYUSH studies."),

    # ---------------------- Faculty Development (4) ----------------------
    _opp(UNIVERSITY, "Faculty Development Programme - Research Methodology in AYUSH", "skill-program",
         ["Ayurveda", "Homoeopathy", "Unani"], "AYUSH faculty (MD / PhD)", "Faculty members", "Teaching / Academia",
         _skills(RESEARCH_SKILLS, [S["sw"], S["pres"], S["pm"]]),
         "Advanced", "2 weeks", "New Delhi, Delhi (Demo)", "Hybrid", "2026-12-05", "Free (demo)",
         "Demo FDP supporting AYUSH faculty in designing and supervising research projects and guiding postgraduate dissertations."),
    _opp(UNIVERSITY, "Faculty Development Programme - Biostatistics for AYUSH Faculty", "skill-program",
         ALL_SYSTEMS, "AYUSH faculty (any system)", "Faculty members", "Data & Research Analytics",
         _skills([S["bio"], S["stat"], S["di"], S["si"], S["da"], S["dv"]]),
         "Intermediate", "2 weeks", "Online (Demo)", "Remote", "2027-01-12", "Free (demo)",
         "Demo FDP covering biostatistics fundamentals and interpretation for AYUSH research and teaching."),
    _opp(UNIVERSITY, "Faculty Development Programme - Evidence Synthesis in AYUSH Curriculum", "skill-program",
         ["Ayurveda", "Unani", "Siddha", "Homoeopathy"], "AYUSH faculty (MD / PhD)", "Faculty members", "Teaching / Academia",
         _skills([S["ev"], S["lit"], S["rm"], S["sw"], S["ct"]]),
         "Advanced", "10 days", "New Delhi, Delhi (Demo)", "Hybrid", "2027-02-18", "Free (demo)",
         "Demo FDP on integrating literature review and evidence synthesis into AYUSH teaching and dissertation work."),
    _opp(DIGITAL, "Faculty Development Programme - Digital Tools for AYUSH Research", "skill-program",
         ALL_SYSTEMS, "AYUSH faculty (any system)", "Faculty members", "Digital Health",
         _skills([S["dv"], S["spread"], S["rdb"], S["da"], S["pres"]]),
         "Beginner", "10 days", "Online (Demo)", "Remote", "2027-03-08", "Free (demo)",
         "Demo FDP introducing spreadsheet dashboards, research databases and data visualisation for AYUSH faculty."),

    # ------------------------- Workshops (4) -------------------------
    _opp(PLANTS, "Workshop - Medicinal Plant Identification & Herbarium Records", "event",
         ["Ayurveda", "Siddha", "Unani"], "BAMS / BSMS / BUMS", "Any year", "Medicinal Plant Research",
         _skills(PLANT_SKILLS, [S["sh"], S["ld"], S["comm"]]),
         "Beginner", "3 days", "Jodhpur, Rajasthan", "On-site", "2026-11-28", "Rs.500 fee (demo)",
         "Demo workshop on medicinal plant identification, collection practice and herbarium record keeping."),
    _opp(UNIVERSITY, "Workshop - Scientific Writing for AYUSH Journals", "event",
         ALL_SYSTEMS, "Any AYUSH programme", "PG and faculty", "Research & Development",
         _skills([S["sw"], S["rm"], S["ev"], S["doc"], S["pres"]]),
         "Intermediate", "2 days", "Online (Demo)", "Remote", "2026-12-10", "Free (demo)",
         "Demo workshop on structuring manuscripts, reporting standards and referencing for AYUSH research outputs."),
    _opp(HERBAL, "Workshop - Good Laboratory Practices in AYUSH Labs", "event",
         ["Ayurveda", "Siddha", "Homoeopathy"], "BAMS / BSMS / BHMS", "Final year UG and PG", "Laboratory Research",
         _skills([S["ls"], S["lt"], S["ld"], S["qt"], S["pe"]]),
         "Beginner", "3 days", "Coimbatore, Tamil Nadu", "On-site", "2027-01-08", "Rs.400 fee (demo)",
         "Demo workshop on laboratory safety, sample handling and quality testing documentation in AYUSH laboratories."),
    _opp(WELLNESS, "Workshop - Yoga & Naturopathy for Lifestyle Wellness", "event",
         ["Yoga & Naturopathy"], "Yoga & Naturopathy Programme", "Any year", "Lifestyle & Wellness",
         _skills(YOGA_SKILLS, [S["comm"], S["pres"], S["prac"]]),
         "Beginner", "2 days", "Rishikesh, Uttarakhand", "On-site", "2026-11-20", "Free (demo)",
         "Demo workshop on yoga and naturopathy practices for lifestyle and preventive wellness. Yoga & Naturopathy candidates only."),

    # ------------------------ Mentorship (4) ------------------------
    _opp(CRO, "Mentorship - Clinical Research Career Pathway", "skill-program",
         ["Ayurveda", "Homoeopathy"], "BAMS / BHMS", "3rd year UG and above", "Clinical Research",
         _skills(RESEARCH_SKILLS, CLIN_RESEARCH_SKILLS, [S["comm"], S["pm"]]),
         "Beginner", "4 months", "Online (Demo)", "Remote", "2026-12-31", "Free (demo)",
         "Demo mentorship programme pairing AYUSH students with demo clinical research professionals. Ayurveda and Homoeopathy candidates only."),
    _opp(HERBAL, "Mentorship - AYUSH Drug Standardization Career Pathway", "skill-program",
         ["Siddha", "Unani"], "BSMS / BUMS", "Final year UG and PG", "Drug Standardization",
         _skills(LAB_SKILLS, QUALITY_SKILLS, [S["pm"], S["comm"]]),
         "Intermediate", "4 months", "Hybrid (Demo)", "Hybrid", "2027-01-28", "Free (demo)",
         "Demo mentorship on laboratory careers in AYUSH drug standardization. Siddha and Unani candidates only."),
    _opp(UNIVERSITY, "Mentorship - AYUSH Public Health Career Pathway", "skill-program",
         ["Yoga & Naturopathy", "Homoeopathy"], "Any listed AYUSH programme", "Final year UG and PG", "Public Health",
         _skills([S["rm"], S["dc"], S["da"], S["comm"], S["ev"]]),
         "Beginner", "3 months", "Online (Demo)", "Remote", "2027-02-25", "Free (demo)",
         "Demo mentorship on public health research and community AYUSH programme careers."),
    _opp(DIGITAL, "Mentorship - AYUSH Digital Health Career Pathway", "skill-program",
         ["Ayurveda", "Unani", "Homoeopathy"], "BAMS / BUMS / BHMS", "Any year", "Digital Health",
         _skills(DATA_SKILLS[:5], [S["ps"], S["comm"], S["pm"]]),
         "Beginner", "3 months", "Online (Demo)", "Remote", "2027-03-12", "Free (demo)",
         "Demo mentorship on digital health and health data roles for AYUSH graduates."),

    # ------------------- Faculty Internships (3) -------------------
    _opp(CRO, "Faculty Research Internship - Clinical Trial Documentation", "internship",
         ["Ayurveda", "Homoeopathy"], "AYUSH faculty (MD / PhD)", "Faculty members", "Clinical Research",
         _skills(CLIN_RESEARCH_SKILLS, RESEARCH_SKILLS, [S["sw"], S["rd"]]),
         "Advanced", "3 months", "Hyderabad, Telangana", "Hybrid", "2027-02-12", "Rs.25,000/month (demo)",
         "Demo faculty internship on clinical study documentation and monitoring workflows. Ayurveda and Homoeopathy faculty only."),
    _opp(HERBAL, "Faculty Internship - Herbal Quality Testing", "internship",
         ["Ayurveda", "Siddha", "Unani"], "AYUSH faculty (MD / PhD)", "Faculty members", "Quality Assurance",
         _skills(LAB_SKILLS, QUALITY_SKILLS, [S["inst"], S["ld"]]),
         "Advanced", "2 months", "Coimbatore, Tamil Nadu", "On-site", "2027-03-18", "Rs.20,000/month (demo)",
         "Demo faculty internship in a herbal testing laboratory covering instrumentation and documentation."),
    _opp(DIGITAL, "Faculty Internship - AYUSH Digital Health Analytics", "internship",
         ["Ayurveda", "Homoeopathy", "Yoga & Naturopathy"], "AYUSH faculty (MD / PhD / PG)", "Faculty members", "Digital Health",
         _skills(DATA_SKILLS, [S["dv"], S["rdb"], S["pres"]]),
         "Intermediate", "2 months", "Bengaluru, Karnataka (Demo)", "Hybrid", "2027-03-28", "Rs.20,000/month (demo)",
         "Demo faculty internship building AYUSH research dashboards and digital health reports from demo datasets."),

    # --------------------- Consultancy Projects (3) ---------------------
    _opp(PHARMA, "Consultancy - AYUSH Formulary Standardization", "job",
         ["Ayurveda", "Unani", "Homoeopathy"], "BAMS / BUMS / BHMS or PG", "Graduates / PG / faculty", "Quality Assurance",
         _skills([S["qc"], S["qt"], S["ld"], S["pharm"], S["pm"]]),
         "Advanced", "6 months (project)", "Pune, Maharashtra", "Hybrid", "2027-04-10", "Rs.80,000 project fee (demo)",
         "Demo consultancy project reviewing formulation documentation and standardization checklists. Limited to the three listed AYUSH systems."),
    _opp(WELLNESS, "Consultancy - Wellness Centre Protocol Development", "job",
         ["Yoga & Naturopathy"], "Yoga & Naturopathy Programme / PG Diploma (Yoga Therapy)", "Graduates / PG / faculty", "Wellness Programme Management",
         _skills(YOGA_SKILLS, [S["pm"], S["lc"], S["comm"], S["pres"]]),
         "Intermediate", "4 months (project)", "Rishikesh, Uttarakhand", "Hybrid", "2027-03-30", "Rs.50,000 project fee (demo)",
         "Demo consultancy project drafting yoga and naturopathy wellness centre protocols. Yoga & Naturopathy candidates only."),
    _opp(PLANTS, "Consultancy - Medicinal Plants Data Compilation", "job",
         ["Ayurveda", "Siddha"], "BAMS / BSMS", "Graduates / PG", "Medicinal Plant Research",
         _skills(PLANT_SKILLS, [S["dc"], S["clean"], S["rdb"], S["doc"]]),
         "Intermediate", "5 months (project)", "Jodhpur, Rajasthan", "Hybrid", "2027-04-25", "Rs.60,000 project fee (demo)",
         "Demo consultancy project compiling medicinal plant use data for Ayurveda and Siddha references."),

    # -------------------- Live Industry Projects (3) --------------------
    _opp(CRO, "Live Industry Project - Clinical Research Data Cleaning", "skill-program",
         ["Ayurveda", "Homoeopathy", "Unani"], "BAMS / BHMS / BUMS", "3rd year UG and above", "Data & Research Analytics",
         _skills([S["clean"], S["spread"], S["da"], S["stat"], S["doc"], S["eth"]]),
         "Intermediate", "8 weeks", "Remote (Demo)", "Remote", "2027-02-08", "Rs.8,000 stipend (demo)",
         "Demo live project cleaning and validating a de-identified AYUSH clinical research dataset."),
    _opp(PHARMA, "Live Industry Project - AYUSH Pharmacy Quality Dashboard", "skill-program",
         ["Ayurveda", "Unani", "Homoeopathy", "Siddha"], "BAMS / BUMS / BHMS / BSMS", "Final year UG and PG", "Quality Control",
         _skills([S["qc"], S["qt"], S["dv"], S["spread"], S["da"]]),
         "Intermediate", "8 weeks", "Hybrid (Demo)", "Hybrid", "2027-02-26", "Rs.8,000 stipend (demo)",
         "Demo live project building a quality-testing dashboard for demo AYUSH formulation batches."),
    _opp(WELLNESS, "Live Industry Project - Wellness Programme Analytics", "skill-program",
         ["Yoga & Naturopathy"], "Yoga & Naturopathy Programme", "Any year", "Wellness Programme Management",
         _skills([S["da"], S["dv"], S["spread"], S["dc"], S["pm"]]),
         "Beginner", "6 weeks", "Remote (Demo)", "Remote", "2027-01-22", "Rs.6,000 stipend (demo)",
         "Demo live project analysing participation and wellness outcomes for a demo yoga programme."),
]


# ============================================================================
# Generators
# ============================================================================

# Demo institute account so the institute dashboard can be demoed too.
INSTITUTE_LOGIN = {
    "email": "registrar@demoayush.edu",
    "password": "institute123",
    "name": "Demo Institute of AYUSH Sciences (Admin)",
}


def generate_institute_user(session, institute_id):
    """Create the demo institute account used to view the institute dashboard."""
    existing = session.query(User).filter(User.email == INSTITUTE_LOGIN["email"]).first()
    if existing:
        print("  Skipping demo institute account (already exists)")
        return 0

    user = User(
        email=INSTITUTE_LOGIN["email"],
        password_hash=generate_password_hash(INSTITUTE_LOGIN["password"]),
        name=INSTITUTE_LOGIN["name"],
        role=UserRole.INSTITUTE,
        institute_id=institute_id,
    )
    session.add(user)
    session.commit()
    print("  Created demo institute account")
    return 1


def generate_students(session, institute_id, count=None):
    """Generate demo student profiles spread across the six AYUSH systems."""
    # Build a deterministic plan: each system contributes its focus areas in turn
    # so the very first demo student is an Ayurveda / Clinical Research (BAMS)
    # profile - the primary demo persona for the skill-gap walk-through.
    plan = []
    for system in AYUSH_SYSTEMS:
        focuses = SYSTEM_FOCUS[system]
        for k in range(SYSTEM_STUDENT_COUNTS[system]):
            plan.append((system, focuses[k % len(focuses)]))

    if count:
        plan = plan[:count]

    print(f"Generating {len(plan)} AYUSH students...")

    students_created = 0
    for i, (system, (career_area, focus_skills)) in enumerate(plan):
        first_name = FIRST_NAMES[i % len(FIRST_NAMES)]
        last_name = LAST_NAMES[i % len(LAST_NAMES)]
        name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}@student.demoayush.edu"

        # Handle duplicate emails
        base_email = email
        suffix = 1
        while session.query(User).filter(User.email == email).first():
            email = f"{first_name.lower()}.{last_name.lower()}{suffix}@student.demoayush.edu"
            suffix += 1

        programmes = SYSTEM_PROGRAMMES[system]
        is_pg = (i % 7 == 6)          # every 7th student is a PG student
        is_research = (i % 13 == 12)  # a couple of PhD / research profiles

        if is_research:
            department = "PhD (AYUSH Research)"
            course = "PhD / Research"
            semester = 2 + (i % 3) * 2
            batch = 2028
        elif is_pg:
            department = programmes["pg"]
            course = programmes["pg_name"]
            semester = 2 + (i % 2) * 2
            batch = 2027
        else:
            department = programmes["ug"]
            course = programmes["ug_name"]
            semester = 2 + (i % 4) * 2
            batch = 2027 + (i % 3)

        # Drop a few skills per student so the skill-gap engine finds realistic
        # missing skills (deterministic, not random).
        skills_list = [s for pos, s in enumerate(focus_skills) if (i + pos) % 6 != 5]
        if career_area not in ("Clinical Research",) and i % 3 == 0:
            # keep at least the system/clinical core visible for most students
            skills_list = _skills(DOMAIN_CORE[:2], skills_list)

        # Extra AYUSH skills shown on the skills page (not used for gap analysis).
        extras_pool = _skills(LAB_SKILLS, [S["spread"], S["rdb"], S["dv"], S["pres"]])
        technical_skills = [s for s in extras_pool if s not in skills_list][:3]

        certifications = CERTIFICATIONS[i % len(CERTIFICATIONS)]
        project_idx = i % len(PROJECTS)
        projects = [PROJECTS[project_idx]]
        if i % 2 == 0:
            projects.append(PROJECTS[(project_idx + 1) % len(PROJECTS)])

        areas = _career_areas(system)
        rot = i % len(areas)
        interests = [areas[(rot + offset) % len(areas)] for offset in range(3)]

        # Create user
        user = User(
            email=email,
            password_hash=generate_password_hash("student123"),
            name=name,
            role=UserRole.STUDENT,
            institute_id=institute_id,
        )
        session.add(user)
        session.flush()

        profile = StudentProfile(
            user_id=user.id,
            institute_id=institute_id,
            branch=system,
            department=department,
            batch=batch,
            course=course,
            semester=semester,
            skills=json.dumps(skills_list),
            technical_skills=json.dumps(technical_skills),
            certifications=json.dumps(certifications),
            projects=json.dumps(projects),
            interests=json.dumps(interests),
            career_goal=f"Build a career in {career_area} within the {system} ecosystem (demo profile)",
            preferred_industry=AYUSH_SECTORS[i % len(AYUSH_SECTORS)],
            other_info=DEMO_NOTE,
        )
        session.add(profile)
        students_created += 1

    session.commit()
    print(f"  Created {students_created} AYUSH students")
    return students_created


def generate_faculty(session, institute_id, count=None):
    """Generate demo faculty members across the six AYUSH systems."""
    faculty_data = [
        {
            "name": "Dr. Vikram Singh",
            "email": "vikram.singh@demoayush.edu",
            "department": "Ayurveda - Kayachikitsa",
            "designation": "Professor",
            "subjects": ["Kayachikitsa", "Roga Nidana & Vikriti Vigyana", "Samhita & Siddhanta", "Research Methodology"],
            "expertise": ["Ayurveda Clinical Practice", "Clinical Research", "Research Methodology"],
            "skills": [S["sys"], S["clin"], S["rm"], S["cr"], S["sw"], S["pm"], S["pe"]],
            "experience": 18,
            "certifications": ["Good Clinical Practice (GCP) Foundations (Demo)", "Research Methodology Workshop (Demo)"],
            "projects": [
                {"title": "Panchakarma Outcome Documentation", "funding": "Demo Institute Seed Grant (fictional)", "amount": "Demo only"},
                {"title": "Ayurveda Case Record Registry", "funding": "Demo Research Fund (fictional)", "amount": "Demo only"},
            ],
        },
        {
            "name": "Prof. Anjali Mehta",
            "email": "anjali.mehta@demoayush.edu",
            "department": "Yoga & Naturopathy",
            "designation": "Associate Professor",
            "subjects": ["Yoga Therapy", "Naturopathy Practices", "Lifestyle & Wellness", "Yoga Research"],
            "expertise": ["Yoga Therapy", "Lifestyle & Wellness", "Public Health"],
            "skills": [S["yoga"], S["nat"], S["lc"], S["prac"], S["rm"], S["dc"], S["comm"]],
            "experience": 12,
            "certifications": ["Yoga Therapy Foundation Course (Demo)"],
            "projects": [
                {"title": "Yoga Therapy for Lifestyle Disorders", "funding": "Demo Wellness Grant (fictional)", "amount": "Demo only"},
            ],
        },
        {
            "name": "Dr. Ramesh Iyer",
            "email": "ramesh.iyer@demoayush.edu",
            "department": "Unani - Ilmul Advia",
            "designation": "Professor",
            "subjects": ["Ilmul Advia", "Moalajat", "Saidla / Pharmacy", "Drug Standardization"],
            "expertise": ["Unani Pharmacology", "Drug Standardization", "Quality Control"],
            "skills": [S["sys"], S["pharm"], S["materia"], S["qc"], S["lt"], S["ld"], S["pe"]],
            "experience": 20,
            "certifications": ["AYUSH Drug Quality Basics (Demo)", "Laboratory Safety & Good Lab Practices (Demo)"],
            "projects": [
                {"title": "Pharmacopoeial Standards for Unani Drugs", "funding": "Demo Research Fund (fictional)", "amount": "Demo only"},
            ],
        },
        {
            "name": "Prof. Sneha Kulkarni",
            "email": "sneha.kulkarni@demoayush.edu",
            "department": "Siddha - Gunapadam",
            "designation": "Associate Professor",
            "subjects": ["Gunapadam", "Siddha Pharmacology", "Drug Standardization", "Traditional Medicine Research"],
            "expertise": ["Siddha Pharmacology", "Medicinal Plant Research", "Drug Standardization"],
            "skills": [S["sys"], S["pharm"], S["plant"], S["lt"], S["qt"], S["ev"], S["sw"]],
            "experience": 11,
            "certifications": ["Medicinal Plant Identification Workshop (Demo)"],
            "projects": [
                {"title": "In-vitro Screening of Medicinal Plants", "funding": "Demo Herbal Research Grant (fictional)", "amount": "Demo only"},
            ],
        },
        {
            "name": "Dr. Arjun Sharma",
            "email": "arjun.sharma@demoayush.edu",
            "department": "Homoeopathy - Materia Medica",
            "designation": "Assistant Professor",
            "subjects": ["Materia Medica", "Organon of Medicine", "Homoeopathic Pharmacy", "Clinical Studies"],
            "expertise": ["Materia Medica", "Homoeopathic Case Studies", "Clinical Research"],
            "skills": [S["sys"], S["materia"], S["pharm"], S["rm"], S["doc"], S["comm"]],
            "experience": 9,
            "certifications": ["Research Documentation & Ethics (Demo)"],
            "projects": [
                {"title": "Quality Parameters of Homoeopathic Formulations", "funding": "Demo Institute Seed Grant (fictional)", "amount": "Demo only"},
            ],
        },
        {
            "name": "Dr. Tenzin Norbu",
            "email": "tenzin.norbu@demoayush.edu",
            "department": "Sowa-Rigpa - Traditional Medicine",
            "designation": "Assistant Professor",
            "subjects": ["Sowa-Rigpa Practice", "Traditional Medicine Documentation", "Materia-related Studies", "Public Health"],
            "expertise": ["Sowa-Rigpa Practice", "Traditional Medicine Research", "Documentation"],
            "skills": [S["sys"], S["clin"], S["materia"], S["doc"], S["lit"], S["comm"], S["pe"]],
            "experience": 8,
            "certifications": ["Research Documentation & Ethics (Demo)"],
            "projects": [
                {"title": "Documentation of Sowa-Rigpa Formulations", "funding": "Demo Institute Seed Grant (fictional)", "amount": "Demo only"},
            ],
        },
        {
            "name": "Dr. Kavya Menon",
            "email": "kavya.menon@demoayush.edu",
            "department": "Ayurveda - Panchakarma",
            "designation": "Assistant Professor",
            "subjects": ["Panchakarma", "Swasthavritta & Yoga", "Clinical Practice", "Kaumarabhritya"],
            "expertise": ["Panchakarma", "Ayurveda Clinical Practice", "Public Health"],
            "skills": [S["sys"], S["clin"], S["prac"], S["tm"], S["comm"], S["pres"]],
            "experience": 7,
            "certifications": ["Panchakarma Assistant Training (Demo)"],
            "projects": [
                {"title": "Panchakarma Protocol Notes", "funding": "Demo Institute Seed Grant (fictional)", "amount": "Demo only"},
            ],
        },
        {
            "name": "Dr. Imran Qureshi",
            "email": "imran.qureshi@demoayush.edu",
            "department": "Unani - Moalajat",
            "designation": "Associate Professor",
            "subjects": ["Moalajat", "Tahaffuzi wa Samaji Tib", "Ilmul Qabalat-o-Nauma", "Research Methodology"],
            "expertise": ["Unani Clinical Practice", "Public Health", "Clinical Research"],
            "skills": [S["sys"], S["clin"], S["prac"], S["rm"], S["dc"], S["ct"], S["pe"]],
            "experience": 14,
            "certifications": ["Research Methodology Workshop (Demo)"],
            "projects": [
                {"title": "Unani Public Health Survey Notes", "funding": "Demo Research Fund (fictional)", "amount": "Demo only"},
            ],
        },
    ]

    if count:
        faculty_data = faculty_data[:count]

    print(f"Generating {len(faculty_data)} AYUSH faculty members...")

    faculty_created = 0
    for f_data in faculty_data:
        existing = session.query(User).filter(User.email == f_data["email"]).first()
        if existing:
            print(f"  Skipping {f_data['name']} (already exists)")
            continue

        user = User(
            email=f_data["email"],
            password_hash=generate_password_hash("faculty123"),
            name=f_data["name"],
            role=UserRole.FACULTY,
            institute_id=institute_id,
        )
        session.add(user)
        session.flush()

        profile = FacultyProfile(
            user_id=user.id,
            institute_id=institute_id,
            department=f_data["department"],
            designation=f_data["designation"],
            subjects_teaching=json.dumps(f_data["subjects"]),
            expertise_areas=json.dumps(f_data["expertise"]),
            skills=json.dumps(f_data["skills"]),
            experience_years=f_data["experience"],
            certifications=json.dumps(f_data["certifications"]),
            research_projects=json.dumps(f_data["projects"]),
        )
        session.add(profile)
        faculty_created += 1

    session.commit()
    print(f"  Created {faculty_created} AYUSH faculty members")
    return faculty_created


def generate_industries(session):
    """Generate the fictional 'Demo ...' organisations."""
    print("Generating demo organisations...")

    industries_created = 0
    for i_data in INDUSTRY_DATA:
        existing = session.query(User).filter(User.email == i_data["email"]).first()
        if existing:
            print(f"  Skipping {i_data['company_name']} (already exists)")
            continue

        user = User(
            email=i_data["email"],
            password_hash=generate_password_hash("industry123"),
            name=i_data["name"],
            role=UserRole.INDUSTRY,
        )
        session.add(user)
        session.flush()

        profile = IndustryProfile(
            user_id=user.id,
            company_name=i_data["company_name"],
            industry_type=i_data["industry_type"],
            location=i_data["location"],
            size=i_data["size"],
            description=i_data["description"],
        )
        session.add(profile)
        industries_created += 1

    session.commit()
    print(f"  Created {industries_created} demo organisations")
    return industries_created


def generate_opportunities(session):
    """Generate the AYUSH demo opportunities."""
    print(f"Generating {len(OPPORTUNITIES_DATA)} AYUSH demo opportunities...")

    opportunities_created = 0
    for o_data in OPPORTUNITIES_DATA:
        industry_user = session.query(User).filter(
            User.email == o_data["industry_email"],
            User.role == UserRole.INDUSTRY,
        ).first()

        if not industry_user:
            print(f"  Skipping {o_data['title']} - organisation not found")
            continue

        industry_profile = session.query(IndustryProfile).filter(
            IndustryProfile.user_id == industry_user.id
        ).first()

        if not industry_profile:
            print(f"  Skipping {o_data['title']} - organisation profile not found")
            continue

        opp = Opportunity(
            industry_id=industry_profile.id,
            title=o_data["title"],
            opportunity_type=o_data["type"],
            required_skills=json.dumps(o_data["skills"]),
            eligibility=json.dumps(o_data["eligibility"]),
            description=o_data["description"],
            location=o_data["location"],
            mode=o_data["mode"],
            deadline=o_data["deadline"],
            stipend=o_data["stipend"],
        )
        session.add(opp)
        session.flush()
        opportunities_created += 1

    session.commit()
    print(f"  Created {opportunities_created} opportunities")
    return opportunities_created


def generate_quiz_for_opportunity(session, opportunity_id, questions_data):
    """Generate a quiz for an opportunity."""
    opp = session.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        print(f"  No opportunity found with id {opportunity_id}")
        return None

    existing_quiz = session.query(Quiz).filter(Quiz.opportunity_id == opportunity_id).first()
    if existing_quiz:
        print(f"  Quiz already exists for opportunity {opportunity_id}")
        return existing_quiz

    quiz = Quiz(
        opportunity_id=opportunity_id,
        title=f"Skill Assessment - {opp.title}",
        description=f"Demo skill assessment for the '{opp.title}' opportunity (prototype data)",
        passing_score=60,
        time_limit_minutes=30,
        is_active=True,
    )
    session.add(quiz)
    session.flush()

    for q_data in questions_data:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q_data["question"],
            option_a=q_data["options"][0],
            option_b=q_data["options"][1],
            option_c=q_data["options"][2],
            option_d=q_data["options"][3],
            correct_option=q_data["correct"],
            skill_tag=q_data.get("skill_tag"),
            difficulty=q_data.get("difficulty", "medium"),
        )
        session.add(question)

    session.commit()
    print(f"  Created quiz with {len(questions_data)} questions for opportunity {opportunity_id}")
    return quiz


CLINICAL_RESEARCH_QUIZ = [
    {
        "question": "In AYUSH clinical research, what is the main purpose of a literature review?",
        "options": ["To summarise existing evidence before designing a study", "To replace the need for ethics approval", "To calculate the final sample size only", "To publish results without data"],
        "correct": "A",
        "skill_tag": S["lit"],
        "difficulty": "easy",
    },
    {
        "question": "Which document records each participant's informed consent in a demo clinical study?",
        "options": ["Informed consent form", "Purchase order", "Inventory register", "Attendance sheet"],
        "correct": "A",
        "skill_tag": S["eth"],
        "difficulty": "easy",
    },
    {
        "question": "A study reports a mean and standard deviation. Which branch of statistics does this belong to?",
        "options": ["Descriptive statistics", "Inferential statistics", "Time-series forecasting", "Machine learning"],
        "correct": "A",
        "skill_tag": S["stat"],
        "difficulty": "easy",
    },
    {
        "question": "What does a p-value below the chosen significance level usually indicate?",
        "options": ["The observed result is unlikely under the null hypothesis", "The study is free of bias", "The sample is representative of the population", "The effect size is large"],
        "correct": "A",
        "skill_tag": S["si"],
        "difficulty": "medium",
    },
    {
        "question": "Which of these is the best practice for recording source data in a clinical study?",
        "options": ["Record data contemporaneously with corrections dated and initialled", "Recreate all records at the end of the study", "Store data only in personal notes", "Delete outliers without explanation"],
        "correct": "A",
        "skill_tag": S["doc"],
        "difficulty": "medium",
    },
    {
        "question": "Why is a case record form (CRF) used in clinical research?",
        "options": ["To capture consistent, pre-defined data points per participant", "To advertise the study", "To replace the protocol", "To bill participants"],
        "correct": "A",
        "skill_tag": S["dc"],
        "difficulty": "easy",
    },
    {
        "question": "Which sampling approach is most likely to introduce selection bias?",
        "options": ["Convenience sampling", "Simple random sampling", "Stratified random sampling", "Systematic sampling with a random start"],
        "correct": "A",
        "skill_tag": S["rd"],
        "difficulty": "medium",
    },
    {
        "question": "In scientific writing for an AYUSH journal, what should the 'Methods' section describe?",
        "options": ["How the study was designed and conducted", "Only the final results", "Acknowledgements and funding", "The literature gap alone"],
        "correct": "A",
        "skill_tag": S["sw"],
        "difficulty": "easy",
    },
]

QUALITY_CONTROL_QUIZ = [
    {
        "question": "What is the primary goal of quality control for AYUSH formulations?",
        "options": ["Ensure consistent identity, purity and strength of the product", "Reduce the number of batches produced", "Replace pharmacopoeial standards", "Increase advertisement reach"],
        "correct": "A",
        "skill_tag": S["qc"],
        "difficulty": "easy",
    },
    {
        "question": "Which test helps confirm the identity of a raw medicinal plant material?",
        "options": ["Macroscopic and microscopic examination", "Market price review", "Packaging check", "Batch numbering"],
        "correct": "A",
        "skill_tag": S["qt"],
        "difficulty": "medium",
    },
    {
        "question": "Why is a laboratory notebook important in a quality testing laboratory?",
        "options": ["It provides a traceable record of observations and methods", "It is only needed for audits by competitors", "It replaces instrument calibration", "It stores finished products"],
        "correct": "A",
        "skill_tag": S["ld"],
        "difficulty": "easy",
    },
    {
        "question": "What should be done before using a weighing balance in a QC laboratory?",
        "options": ["Verify calibration and zero the balance", "Increase the room temperature", "Skip the daily check to save time", "Use it for any unrelated material"],
        "correct": "A",
        "skill_tag": S["inst"],
        "difficulty": "easy",
    },
    {
        "question": "Which practice best protects laboratory staff handling formulation samples?",
        "options": ["Following documented safety procedures and using appropriate PPE", "Working without labels to save time", "Storing all samples together", "Ignoring spill procedures"],
        "correct": "A",
        "skill_tag": S["ls"],
        "difficulty": "easy",
    },
    {
        "question": "Which of these is an analytical technique commonly used for herbal sample testing?",
        "options": ["High-performance thin-layer chromatography (HPTLC)", "Word processing", "Static code analysis", "Financial modelling"],
        "correct": "A",
        "skill_tag": S["lt"],
        "difficulty": "medium",
    },
]


# ============================================================================
# Entry point
# ============================================================================

def main():
    """Main seed function."""
    print("=" * 60)
    print("SIH Platform - AYUSH Demo Data Seeder")
    print("All records generated here are FICTIONAL DEMO/PROTOTYPE DATA.")
    print("=" * 60)

    # Create database tables
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        # Check if data already exists
        if session.query(User).first():
            print("\nData already exists in the database.")
            print("To re-seed, delete the database or clear the tables first.")
            print("\nTo force re-seed, run: python -c 'from backend.database import engine; from backend.models import Base; Base.metadata.drop_all(bind=engine)'")
            return

        # Get or create the demo institute
        institute = session.query(Institute).filter(Institute.id == 1).first()
        if not institute:
            institute = Institute(
                name="Demo Institute of AYUSH Sciences",
                location="Pune, Maharashtra (Demo)",
                type="Demo / Fictional",
                established_year=2018,
            )
            session.add(institute)
            session.commit()
            print("\nCreated demo institute: Demo Institute of AYUSH Sciences (id=1)")

        institute_id = institute.id if institute else 1

        # Create the demo institute account (used by the institute dashboard)
        institute_users_count = generate_institute_user(session, institute_id)

        # Generate data
        print("\nGenerating AYUSH demo data...")
        print("-" * 40)

        students_count = generate_students(session, institute_id)
        faculty_count = generate_faculty(session, institute_id)
        industries_count = generate_industries(session)
        opps_count = generate_opportunities(session)

        # Create quizzes for a couple of demo opportunities
        print("\nCreating AYUSH demo quizzes...")
        print("-" * 40)

        clinical_research = session.query(Opportunity).filter(
            Opportunity.title == "Clinical Research Internship - Ayurveda"
        ).first()
        if clinical_research:
            generate_quiz_for_opportunity(session, clinical_research.id, CLINICAL_RESEARCH_QUIZ)

        qc_opportunity = session.query(Opportunity).filter(
            Opportunity.title == "Quality Control Analyst - AYUSH Formulations"
        ).first()
        if qc_opportunity:
            generate_quiz_for_opportunity(session, qc_opportunity.id, QUALITY_CONTROL_QUIZ)

        print("\n" + "=" * 60)
        print("AYUSH Demo Seeding Complete!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  - AYUSH students: {students_count}")
        print(f"  - AYUSH faculty: {faculty_count}")
        print(f"  - Demo organisations: {industries_count}")
        print(f"  - AYUSH opportunities: {opps_count}")
        print(f"  - Institute ID: {institute_id}")
        print("\nDemo Credentials:")
        print("  Student: arjun.sharma@student.demoayush.edu / student123")
        print("  Faculty: vikram.singh@demoayush.edu / faculty123")
        print("  Institute: registrar@demoayush.edu / institute123")
        print("  Industry: hr@demoayushpharma.example.com / industry123")
        print("\nNote: All 50 students and 8 faculty belong to institute_id = 1")
        print("      All organisations and opportunities are fictional demo data.")

    except Exception as e:
        print(f"\nError during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
