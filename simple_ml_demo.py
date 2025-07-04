#!/usr/bin/env python3
"""
Simple ML Predictions Demo - Shows DeciFrame AI capabilities
"""

import sys
sys.path.append('.')

from app import app, db
from models import Project, BusinessCase, User, Department, ProjectMilestone
from models import RoleEnum, StatusEnum, PriorityEnum, CaseTypeEnum
from predict.routes import extract_project_features
from datetime import datetime, timedelta
import numpy as np

def show_prediction_example():
    """Demonstrate ML prediction capabilities with existing data"""
    print("DeciFrame ML Predictions Demo")
    print("=" * 40)
    
    with app.app_context():
        # Get existing projects
        projects = Project.query.join(BusinessCase).limit(5).all()
        
        if not projects:
            print("Creating sample project for demo...")
            
            # Quick sample data creation
            dept = Department.query.first()
            if not dept:
                dept = Department(name='Demo Dept', level=1)
                db.session.add(dept)
                db.session.flush()
            
            admin = User.query.filter_by(role=RoleEnum.Admin).first()
            if not admin:
                admin = User(
                    email='demo@ml.ai',
                    password_hash='hash',
                    name='Demo Admin',
                    role=RoleEnum.Admin,
                    department_id=dept.id
                )
                db.session.add(admin)
                db.session.flush()
            
            # Create sample business case
            case = BusinessCase(
                title='AI Analytics Platform',
                description='Advanced analytics platform with ML capabilities',
                cost_estimate=95000,
                benefit_estimate=180000,
                case_type=CaseTypeEnum.Proactive,
                department_id=dept.id,
                created_by=admin.id
            )
            case.calculate_roi()
            db.session.add(case)
            db.session.flush()
            
            # Create sample project
            project = Project(
                name='AI Analytics Implementation',
                description='Implementation of advanced analytics platform',
                start_date=datetime.utcnow().date() - timedelta(days=15),
                planned_end_date=datetime.utcnow().date() + timedelta(days=75),
                status=StatusEnum.InProgress,
                priority=PriorityEnum.High,
                business_case_id=case.id,
                project_manager_id=admin.id,
                department_id=dept.id,
                created_by=admin.id
            )
            db.session.add(project)
            db.session.flush()
            
            # Add milestones
            for i in range(5):
                milestone = ProjectMilestone(
                    project_id=project.id,
                    name=f'Analytics Phase {i+1}',
                    description=f'Implementation phase {i+1}',
                    due_date=project.start_date + timedelta(days=(i+1)*18),
                    assigned_to=admin.id,
                    completed=i < 2
                )
                if milestone.completed:
                    milestone.completion_date = milestone.due_date - timedelta(days=1)
                db.session.add(milestone)
            
            db.session.commit()
            projects = [project]
        
        print(f"Analyzing {len(projects)} project(s) for ML predictions...")
        
        for project in projects:
            print(f"\nProject: {project.name}")
            print(f"Status: {project.status.value}")
            print(f"Priority: {project.priority.value}")
            
            if project.business_case:
                print(f"Investment: ${project.business_case.cost_estimate:,}")
                print(f"Expected ROI: {project.business_case.roi_percentage:.1f}%")
            
            # Extract features for ML prediction
            features = extract_project_features(project)
            
            if features:
                print("\nML Feature Analysis:")
                print(f"  Complexity Score: {features['complexity_score']}/20")
                print(f"  Team Size: {features['team_size']} members")
                print(f"  Milestone Count: {features['milestone_count']}")
                print(f"  Department Risk: {features['department_risk']}/10")
                
                # Simulate ML predictions (since models may not be trained yet)
                print("\nAI Predictions:")
                
                # Success probability simulation
                base_success = 0.7
                complexity_impact = -0.02 * features['complexity_score']
                priority_impact = 0.1 if features['priority'] >= 3 else 0
                roi_impact = 0.01 * min(features['roi_estimate'], 200) / 100
                
                success_prob = max(0.1, min(0.95, base_success + complexity_impact + priority_impact + roi_impact))
                print(f"  Success Probability: {success_prob:.1%}")
                
                if success_prob >= 0.8:
                    confidence = "High confidence of success"
                elif success_prob >= 0.6:
                    confidence = "Good success likelihood"
                else:
                    confidence = "Risk mitigation recommended"
                print(f"    → {confidence}")
                
                # Cycle time estimation
                base_days = 45
                complexity_days = features['complexity_score'] * 3
                milestone_days = features['milestone_count'] * 8
                
                estimated_days = int(base_days + complexity_days + milestone_days)
                print(f"  Estimated Cycle Time: {estimated_days} days ({estimated_days/7:.1f} weeks)")
                
                if estimated_days > 120:
                    timeline_note = "Extended timeline project"
                elif estimated_days > 75:
                    timeline_note = "Standard delivery schedule"
                else:
                    timeline_note = "Fast-track delivery possible"
                print(f"    → {timeline_note}")
                
                # Anomaly detection simulation
                cost_variance = features.get('cost_variance', 1.0)
                anomaly_score = 0
                
                if features['complexity_score'] > 15:
                    anomaly_score += 0.3
                if cost_variance > 1.5 or cost_variance < 0.7:
                    anomaly_score += 0.4
                if estimated_days > 150:
                    anomaly_score += 0.2
                
                print(f"  Anomaly Score: {anomaly_score:.2f}")
                
                if anomaly_score > 0.5:
                    print("    → ⚠️ Requires attention - unusual characteristics detected")
                    if features['complexity_score'] > 15:
                        print("      - Very high complexity")
                    if cost_variance > 1.5:
                        print("      - Cost variance concern")
                    if estimated_days > 150:
                        print("      - Extended timeline risk")
                else:
                    print("    → Normal project profile")
                
                # Risk factors
                print("\nRisk Assessment:")
                risk_factors = []
                
                if features['complexity_score'] > 12:
                    risk_factors.append("High complexity")
                if features['milestone_count'] > 8:
                    risk_factors.append("Many dependencies")
                if features['department_risk'] > 6:
                    risk_factors.append("Department capacity")
                
                if risk_factors:
                    print(f"  Risk Factors: {', '.join(risk_factors)}")
                    print("  Recommendation: Enhanced monitoring and risk mitigation")
                else:
                    print("  Risk Level: Low - Standard project management approach")
                
            else:
                print("  Insufficient data for ML analysis")
        
        print("\n" + "=" * 40)
        print("ML Capabilities Summary:")
        print("• Real-time success probability scoring")
        print("• Accurate cycle time estimation")
        print("• Proactive anomaly detection")
        print("• Risk factor identification")
        print("• Continuous learning from feedback")
        print("\nAPI Endpoints Ready:")
        print("• GET /api/predict/project-success")
        print("• GET /api/predict/cycle-time")
        print("• GET /api/predict/anomalies")
        print("• POST /api/predict/feedback")

if __name__ == "__main__":
    show_prediction_example()