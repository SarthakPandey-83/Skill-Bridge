"""Skill gap analysis service."""
from typing import List, Dict, Any, Tuple
from collections import Counter
import json


class SkillGapEngine:
    """
    Engine for calculating skill gaps between student skills
    and industry requirements.
    
    Can be extended/replaced with ML-based analysis later.
    """

    def __init__(self):
        # AYUSH-relevant skill taxonomy used across the prototype demo data.
        self.skill_categories = {
            "domain": [
                "AYUSH System Knowledge", "Clinical Knowledge", "Pharmacology",
                "Materia Medica", "Medicinal Plant Knowledge", "Healthcare Practices",
                "Pharmacy", "Quality Control", "Yoga Therapy", "Naturopathy Practices",
                "Lifestyle Counselling"
            ],
            "research": [
                "Research Methodology", "Research Design", "Literature Review",
                "Evidence Synthesis", "Clinical Research", "Fundamental Research",
                "Research Ethics", "Scientific Writing", "Research Documentation",
                "Data Collection", "Data Interpretation"
            ],
            "data": [
                "Basic Statistics", "Biostatistics", "Data Cleaning", "Data Analysis",
                "Data Visualization", "Spreadsheet Analysis", "Statistical Interpretation",
                "Research Database Management"
            ],
            "laboratory": [
                "Laboratory Techniques", "Molecular Biology", "Sample Handling",
                "Laboratory Documentation", "Quality Testing", "Laboratory Safety",
                "Instrumentation"
            ],
            "professional": [
                "Communication", "Teamwork", "Problem Solving", "Critical Thinking",
                "Time Management", "Presentation", "Leadership", "Project Management",
                "Professional Ethics"
            ]
        }

        # Quick lookup
        self.all_skills = set()
        for category_skills in self.skill_categories.values():
            self.all_skills.update(category_skills)

    def categorize_skill(self, skill: str) -> str:
        """Categorize a skill into its domain."""
        skill_lower = skill.lower().strip()
        for category, skills in self.skill_categories.items():
            for s in skills:
                if s.lower() == skill_lower:
                    return category
        return "other"

    def calculate_skill_level(self, skills: List[str], weights: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculate current skill levels for a student.
        Default: all listed skills at level 3 (intermediate)
        Can be enhanced with proficiency ratings.
        """
        if weights is None:
            weights = {}
        
        levels = {}
        for skill in skills:
            skill_normalized = skill.strip()
            if skill_normalized:
                levels[skill_normalized] = weights.get(skill_normalized, 3.0)
        return levels

    def calculate_industry_demand(self, opportunities: List[Dict]) -> Dict[str, float]:
        """
        Calculate industry demand for each skill based on opportunity frequency.
        Returns normalized demand scores (0-5 scale).
        """
        skill_counter = Counter()
        
        for opp in opportunities:
            required_skills = opp.get("required_skills", [])
            if isinstance(required_skills, str):
                try:
                    required_skills = json.loads(required_skills)
                except:
                    required_skills = []
            
            for skill in required_skills:
                skill_normalized = skill.strip()
                if skill_normalized:
                    skill_counter[skill_normalized] += 1
        
        if not skill_counter:
            return {}
        
        max_count = max(skill_counter.values())
        
        # Normalize to 0-5 scale
        demand_scores = {}
        for skill, count in skill_counter.items():
            normalized = (count / max_count) * 5.0 if max_count > 0 else 0
            demand_scores[skill] = round(normalized, 2)
        
        return demand_scores

    def analyze_skill_gap(
        self,
        student_skills: List[str],
        industry_skills: Dict[str, float],
        student_levels: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Analyze skill gap for a student against industry requirements.
        
        Returns:
        - current_skills: Skills student already has
        - missing_skills: Industry-required skills student lacks
        - weak_skills: Skills present but below industry demand
        - recommended_skills: Priority skills to learn
        - skill_gaps: Detailed gap analysis for each skill
        """
        if student_levels is None:
            student_levels = self.calculate_skill_level(student_skills)
        
        student_skill_set = set(student_levels.keys())
        industry_skill_set = set(industry_skills.keys())
        
        # Categorize skills
        current_skills = list(student_skill_set & industry_skill_set)
        missing_skills = list(industry_skill_set - student_skill_set)
        
        # Weak skills: present but below demand threshold
        weak_skills = []
        for skill in current_skills:
            current = student_levels.get(skill, 0)
            demand = industry_skills.get(skill, 0)
            if current < demand and demand > 2.0:
                weak_skills.append(skill)
        
        # Recommended skills: missing + weak, sorted by demand
        recommendations = []
        for skill in missing_skills:
            recommendations.append({
                "skill": skill,
                "reason": "missing",
                "priority": industry_skills.get(skill, 0),
                "category": self.categorize_skill(skill)
            })
        
        for skill in weak_skills:
            recommendations.append({
                "skill": skill,
                "reason": "weak",
                "priority": industry_skills.get(skill, 0) - student_levels.get(skill, 0),
                "category": self.categorize_skill(skill)
            })
        
        # Sort by priority (highest first)
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        
        # Build detailed skill gap records
        skill_gaps = []
        all_relevant_skills = industry_skill_set | student_skill_set
        
        for skill in all_relevant_skills:
            current = student_levels.get(skill, 0)
            demand = industry_skills.get(skill, 0)
            gap = demand - current
            
            if current >= demand or demand == 0:
                status = "matched"
            elif current > 0:
                status = "weak"
            else:
                status = "missing"
            
            skill_gaps.append({
                "skill_name": skill,
                "current_level": round(current, 2),
                "industry_demand": round(demand, 2),
                "gap": round(gap, 2),
                "status": status
            })
        
        # Sort gaps by severity (largest gap first)
        skill_gaps.sort(key=lambda x: x["gap"], reverse=True)
        
        return {
            "current_skills": list(current_skills),
            "missing_skills": missing_skills,
            "weak_skills": weak_skills,
            "industry_demanded_skills": list(industry_skill_set),
            "recommended_skills": recommendations[:10],  # Top 10 recommendations
            "skill_gaps": skill_gaps
        }

    def calculate_skill_demand_rankings(
        self,
        all_opportunities: List[Dict],
        student_skills_available: Dict[str, int] = None
    ) -> List[Dict]:
        """
        Calculate and rank skills by industry demand.
        Optionally compare against student skill availability.
        
        Returns list of {skill, demand_count, demand_score, supply_count, supply_score, gap}
        """
        demand = self.calculate_industry_demand(all_opportunities)
        
        # Count students having each skill
        supply = {}
        if student_skills_available:
            for skill, count in student_skills_available.items():
                supply[skill] = count
        
        if not demand and not supply:
            return []
        
        all_skills = set(demand.keys()) | set(supply.keys())
        max_demand = max(demand.values()) if demand else 1
        max_supply = max(supply.values()) if supply else 1
        
        rankings = []
        for skill in all_skills:
            demand_count = sum(1 for opp in all_opportunities 
                             if skill in (opp.get("required_skills", []) or []))
            demand_score = (demand.get(skill, 0) / 5.0) * 100  # Convert to percentage
            
            supply_count = supply.get(skill, 0)
            supply_score = (supply.get(skill, 0) / max_supply * 100) if max_supply > 0 else 0
            
            # Gap: how much demand exceeds supply
            gap = demand_score - supply_score
            
            rankings.append({
                "skill": skill,
                "demand_count": demand_count,
                "demand_percentage": round(demand_score, 2),
                "supply_count": supply_count,
                "supply_percentage": round(supply_score, 2),
                "gap": round(gap, 2),
                "category": self.categorize_skill(skill),
                "high_demand_low_supply": gap > 20  # Flag significant gaps
            })
        
        # Sort by demand percentage (highest first)
        rankings.sort(key=lambda x: x["demand_percentage"], reverse=True)
        
        return rankings

    def get_skills_by_demand_tier(
        self,
        rankings: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """Categorize skills into demand tiers."""
        high_demand = []
        medium_demand = []
        low_demand = []
        
        for r in rankings:
            if r["demand_percentage"] >= 60:
                high_demand.append(r)
            elif r["demand_percentage"] >= 30:
                medium_demand.append(r)
            else:
                low_demand.append(r)
        
        return {
            "high_demand": high_demand,
            "medium_demand": medium_demand,
            "low_demand": low_demand
        }


# Singleton instance
skill_engine = SkillGapEngine()
