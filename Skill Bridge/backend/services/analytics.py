"""Analytics service for institute and industry dashboards."""
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
import json
import base64
from io import BytesIO

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


class AnalyticsService:
    """Service for generating analytics and charts."""

    def __init__(self):
        # Professional color palette
        self.colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#34495e', '#d35400', '#c0392b', '#27ae60'
        ]
        
        # Chart styling
        plt.rcParams.update({
            'figure.figsize': (10, 6),
            'figure.dpi': 100,
            'font.size': 11,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'axes.grid': True,
            'grid.alpha': 0.3,
            'axes.facecolor': '#f8f9fa',
            'figure.facecolor': 'white'
        })

    def _to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', 
                   facecolor=fig.get_facecolor(),
                   edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64

    def _wrap_json(self, data):
        """Safely parse JSON string."""
        if data is None:
            return []
        if isinstance(data, (list, dict)):
            return data
        try:
            return json.loads(data)
        except:
            return []

    # ============== Institute Analytics ==============

    def generate_institute_analytics(
        self,
        students: List[Dict],
        opportunities: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics for institute dashboard."""
        
        df = pd.DataFrame(students)
        
        # Basic counts
        total_students = len(df)
        
        # Students by branch
        branch_counts = df['branch'].value_counts().to_dict() if 'branch' in df else {}
        students_by_branch = [
            {"branch": k, "count": v, "percentage": round(v/total_students*100, 1)}
            for k, v in branch_counts.items()
        ]
        
        # Students by batch
        batch_counts = df['batch'].value_counts().sort_index().to_dict() if 'batch' in df else {}
        students_by_batch = [
            {"batch": int(k), "count": v, "percentage": round(v/total_students*100, 1)}
            for k, v in batch_counts.items()
        ]
        
        # Skill distribution
        all_skills = []
        for skills in df.get('skills', []):
            parsed = self._wrap_json(skills)
            if isinstance(parsed, list):
                all_skills.extend(parsed)
        
        skill_counter = Counter(all_skills)
        skill_distribution = [
            {"skill": k, "count": v, "percentage": round(v/total_students*100, 1)}
            for k, v in skill_counter.most_common(15)
        ]
        
        most_common_skills = skill_distribution[:10]
        
        # Career interests
        career_interests = df['preferred_industry'].value_counts().to_dict() if 'preferred_industry' in df else {}
        career_data = [
            {"industry": k, "count": v, "percentage": round(v/total_students*100, 1)}
            for k, v in career_interests.items()
        ]
        
        # Calculate participations (would need application tracking in full implementation)
        # For now, estimate based on interest alignment
        internship_participation = min(total_students // 4, 50)  # Placeholder
        job_participation = min(total_students // 10, 20)  # Placeholder
        skill_dev_participation = min(total_students // 5, 30)  # Placeholder
        
        return {
            "total_students": total_students,
            "students_by_branch": students_by_branch,
            "students_by_batch": students_by_batch,
            "skill_distribution": skill_distribution,
            "most_common_skills": most_common_skills,
            "skill_gaps": [],  # Would be calculated with industry data
            "industry_demanded_skills": [],
            "career_interests": career_data,
            "internship_participation": internship_participation,
            "job_participation": job_participation,
            "skill_development_participation": skill_dev_participation
        }

    def generate_institute_charts(self, analytics: Dict[str, Any]) -> Dict[str, str]:
        """Generate chart images for institute dashboard."""
        charts = {}
        
        # 1. Students by AYUSH System (Bar Chart)
        if analytics.get('students_by_branch'):
            fig, ax = plt.subplots()
            branches = [x['branch'] for x in analytics['students_by_branch'][:8]]
            counts = [x['count'] for x in analytics['students_by_branch'][:8]]
            bars = ax.bar(branches, counts, color=self.colors[:len(branches)], edgecolor='white', linewidth=1.5)
            ax.set_title('Students by AYUSH System', fontweight='bold', pad=15)
            ax.set_xlabel('AYUSH System')
            ax.set_ylabel('Number of Students')
            ax.tick_params(axis='x', rotation=45)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(height)}', ha='center', va='bottom', fontsize=10)
            plt.tight_layout()
            charts['branch_chart'] = self._to_base64(fig)
        
        # 2. Students by Batch (Bar Chart)
        if analytics.get('students_by_batch'):
            fig, ax = plt.subplots()
            batches = [str(x['batch']) for x in analytics['students_by_batch']]
            counts = [x['count'] for x in analytics['students_by_batch']]
            bars = ax.bar(batches, counts, color='#3498db', edgecolor='white', linewidth=1.5)
            ax.set_title('Students by Graduation Year', fontweight='bold', pad=15)
            ax.set_xlabel('Batch Year')
            ax.set_ylabel('Number of Students')
            ax.tick_params(axis='x', rotation=0)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(height)}', ha='center', va='bottom', fontsize=10)
            plt.tight_layout()
            charts['batch_chart'] = self._to_base64(fig)
        
        # 3. Top Skills (Horizontal Bar Chart)
        if analytics.get('most_common_skills'):
            fig, ax = plt.subplots()
            skills = [x['skill'] for x in analytics['most_common_skills'][:10]]
            counts = [x['count'] for x in analytics['most_common_skills'][:10]]
            y_pos = range(len(skills))
            bars = ax.barh(y_pos, counts, color=self.colors[:len(skills)], edgecolor='white')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(skills)
            ax.set_title('Top 10 Most Common Skills', fontweight='bold', pad=15)
            ax.set_xlabel('Number of Students')
            ax.invert_yaxis()
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 0.3, bar.get_y() + bar.get_height()/2.,
                       f'{int(width)}', ha='left', va='center', fontsize=9)
            plt.tight_layout()
            charts['skills_chart'] = self._to_base64(fig)
        
        # 4. Career Interests (Pie Chart)
        if analytics.get('career_interests') and len(analytics['career_interests']) > 1:
            fig, ax = plt.subplots()
            labels = [x['industry'] for x in analytics['career_interests'][:8]]
            sizes = [x['count'] for x in analytics['career_interests'][:8]]
            
            # Add "Other" category if needed
            if len(analytics['career_interests']) > 8:
                other_count = sum(x['count'] for x in analytics['career_interests'][8:])
                labels.append('Other')
                sizes.append(other_count)
            
            wedges, texts, autotexts = ax.pie(
                sizes, labels=None, autopct='%1.1f%%', 
                colors=self.colors[:len(labels)],
                startangle=90, pctdistance=0.85
            )
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_fontweight('bold')
            
            ax.legend(wedges, labels, title="Industries", loc="center left",
                     bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
            ax.set_title('Student Career Interests', fontweight='bold', pad=15)
            plt.tight_layout()
            charts['career_chart'] = self._to_base64(fig)
        
        # 5. Participation Overview (Donut Chart)
        fig, ax = plt.subplots()
        labels = ['Internships', 'Jobs', 'Skill Development']
        sizes = [
            analytics.get('internship_participation', 0),
            analytics.get('job_participation', 0),
            analytics.get('skill_development_participation', 0)
        ]
        total = sum(sizes)
        
        if total > 0:
            wedges, texts, autotexts = ax.pie(
                sizes, labels=None, autopct='%1.1f%%',
                colors=['#3498db', '#2ecc71', '#f39c12'],
                startangle=90, pctdistance=0.8
            )
            for autotext in autotexts:
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            
            centre_circle = plt.Circle((0, 0), 0.60, fc='white')
            ax.add_artist(centre_circle)
            ax.text(0, 0, f'{total}\nStudents', ha='center', va='center', 
                   fontsize=14, fontweight='bold')
            
            ax.legend(wedges, labels, title="Activities", loc="center left",
                     bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)
            ax.set_title('Student Participation Overview', fontweight='bold', pad=15)
        
        plt.tight_layout()
        charts['participation_chart'] = self._to_base64(fig)
        
        return charts

    # ============== Industry Demand Analysis ==============

    def analyze_industry_demand(
        self,
        opportunities: List[Dict],
        student_skills: List[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze industry skill demand vs student supply."""
        
        # Count skill demand from opportunities
        demand_counter = Counter()
        for opp in opportunities:
            skills = self._wrap_json(opp.get('required_skills', []))
            if isinstance(skills, list):
                for skill in skills:
                    demand_counter[skill.strip()] += 1
        
        # Count skill supply from students
        supply_counter = Counter()
        if student_skills:
            for student in student_skills:
                skills = self._wrap_json(student.get('skills', []))
                if isinstance(skills, list):
                    for skill in skills:
                        supply_counter[skill.strip()] += 1
        
        if not demand_counter and not supply_counter:
            return {"rankings": [], "high_demand_low_supply": [], "charts": {}}
        
        # Create comparison data
        all_skills = set(demand_counter.keys()) | set(supply_counter.keys())
        max_demand = max(demand_counter.values()) if demand_counter else 1
        max_supply = max(supply_counter.values()) if supply_counter else 1
        
        rankings = []
        for skill in all_skills:
            demand_val = demand_counter.get(skill, 0)
            supply_val = supply_counter.get(skill, 0)
            
            demand_pct = (demand_val / max_demand * 100) if max_demand > 0 else 0
            supply_pct = (supply_val / max_supply * 100) if max_supply > 0 else 0
            
            gap = demand_pct - supply_pct
            
            rankings.append({
                "skill": skill,
                "demand_count": demand_val,
                "demand_score": round(demand_pct, 1),
                "supply_count": supply_val,
                "supply_score": round(supply_pct, 1),
                "gap": round(gap, 1),
                "priority": "high" if gap > 30 else ("medium" if gap > 10 else "low")
            })
        
        rankings.sort(key=lambda x: x['demand_score'], reverse=True)
        
        # High demand, low supply skills
        high_demand_low_supply = [r for r in rankings if r['gap'] > 20]
        
        return {
            "rankings": rankings[:20],
            "high_demand_low_supply": high_demand_low_supply[:10],
            "total_skills_analyzed": len(all_skills)
        }

    def generate_demand_charts(
        self,
        analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate charts for industry demand analysis."""
        charts = {}
        
        rankings = analysis.get('rankings', [])
        if not rankings:
            return charts
        
        # 1. Top 10 In-Demand Skills (Bar Chart)
        top_skills = rankings[:10]
        fig, ax = plt.subplots()
        skills = [x['skill'] for x in top_skills]
        demand = [x['demand_score'] for x in top_skills]
        
        bars = ax.barh(range(len(skills)), demand, color='#3498db', edgecolor='white', height=0.6)
        ax.set_yticks(range(len(skills)))
        ax.set_yticklabels(skills)
        ax.set_xlabel('Demand Score (0-100)')
        ax.set_title('Top 10 Most Demanded Skills', fontweight='bold', pad=15)
        ax.invert_yaxis()
        
        for i, (bar, val) in enumerate(zip(bars, demand)):
            ax.text(val + 1, bar.get_y() + bar.get_height()/2., 
                   f'{val:.0f}%', va='center', fontsize=9)
        
        plt.tight_layout()
        charts['demand_chart'] = self._to_base64(fig)
        
        # 2. Demand vs Supply Comparison (Grouped Bar)
        compare_data = rankings[:8]
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(compare_data))
        width = 0.35
        
        demand_vals = [x['demand_score'] for x in compare_data]
        supply_vals = [x['supply_score'] for x in compare_data]
        
        bars1 = ax.bar(x - width/2, demand_vals, width, label='Industry Demand', 
                      color='#e74c3c', edgecolor='white')
        bars2 = ax.bar(x + width/2, supply_vals, width, label='Student Supply', 
                      color='#2ecc71', edgecolor='white')
        
        ax.set_xlabel('Skill')
        ax.set_ylabel('Percentage (%)')
        ax.set_title('Industry Demand vs Student Supply', fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels([x['skill'] for x in compare_data], rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 110)
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.0f}%', ha='center', va='bottom', fontsize=8)
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{height:.0f}%', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        charts['demand_supply_chart'] = self._to_base64(fig)
        
        # 3. Skills Gap Priority (if high demand low supply exists)
        high_gap = analysis.get('high_demand_low_supply', [])
        if high_gap:
            fig, ax = plt.subplots()
            skills = [x['skill'] for x in high_gap[:8]]
            gaps = [x['gap'] for x in high_gap[:8]]
            
            colors = ['#e74c3c' if g > 50 else '#f39c12' if g > 30 else '#3498db' 
                     for g in gaps]
            bars = ax.barh(range(len(skills)), gaps, color=colors, edgecolor='white')
            ax.set_yticks(range(len(skills)))
            ax.set_yticklabels(skills)
            ax.set_xlabel('Gap (Demand % - Supply %)')
            ax.set_title('High Demand - Low Supply Skills', fontweight='bold', pad=15)
            ax.invert_yaxis()
            
            for bar, gap in zip(bars, gaps):
                ax.text(gap + 1, bar.get_y() + bar.get_height()/2., 
                       f'+{gap:.0f}%', va='center', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            charts['gap_chart'] = self._to_base64(fig)
        
        # 4. Demand Distribution (Pie Chart)
        fig, ax = plt.subplots()
        high = sum(1 for x in rankings if x['demand_score'] >= 60)
        medium = sum(1 for x in rankings if 30 <= x['demand_score'] < 60)
        low = sum(1 for x in rankings if x['demand_score'] < 30)
        
        labels = ['High Demand (60%+)', 'Medium Demand (30-60%)', 'Low Demand (<30%)']
        sizes = [high, medium, low]
        colors_pie = ['#e74c3c', '#f39c12', '#3498db']
        
        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct='%1.1f%%',
            colors=colors_pie, startangle=90, pctdistance=0.85
        )
        for autotext in autotexts:
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')
        
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title('Skill Demand Distribution', fontweight='bold', pad=15)
        
        plt.tight_layout()
        charts['demand_distribution'] = self._to_base64(fig)
        
        return charts


# Singleton instance
analytics_service = AnalyticsService()
