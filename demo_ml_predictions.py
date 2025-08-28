#!/usr/bin/env python3
"""
ML Predictions Demo Script for DeciFrame
Demonstrates project success forecasting, cycle-time estimation, and anomaly detection
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append('.')

from app import app, db
from models import User, Department, Project, BusinessCase, ProjectMilestone
from models import RoleEnum, StatusEnum, PriorityEnum, CaseTypeEnum
from analytics.train_models import MLModelTrainer
from predict.routes import extract_project_features

def create_demo_data():
    """Create comprehensive demo data for ML predictions"""
    print("Creating demo data for ML predictions...")
    
    with app.app_context():
        # Create demo department
        dept = Department.query.filter_by(name='ML Demo Dept').first()
        if not dept:
            dept = Department(name='ML Demo Dept', level=1)
            db.session.add(dept)
            db.session.flush()
        
        # Create demo users
        admin = User.query.filter_by(email='ml.demo@deciframe.com').first()
        if not admin:
            admin = User(
                email='ml.demo@deciframe.com',
                password_hash='demo_hash',
                name='ML Demo Admin',
                role=RoleEnum.Admin,
                department_id=dept.id
            )
            db.session.add(admin)
            db.session.flush()
        
        pm = User.query.filter_by(email='pm.ml.demo@deciframe.com').first()
        if not pm:
            pm = User(
                email='pm.ml.demo@deciframe.com',
                password_hash='demo_hash',
                name='ML Demo PM',
                role=RoleEnum.PM,
                department_id=dept.id
            )
            db.session.add(pm)
            db.session.flush()
        
        # Create demo projects with varied characteristics
        demo_projects = [
            {
                'name': 'E-commerce Platform Upgrade',
                'cost': 85000, 'benefit': 150000,
                'priority': PriorityEnum.High,
                'status': StatusEnum.InProgress,
                'milestones': 6,
                'complexity': 'high'
            },
            {
                'name': 'Customer Support Portal',
                'cost': 45000, 'benefit': 75000,
                'priority': PriorityEnum.Medium,
                'status': StatusEnum.Open,
                'milestones': 4,
                'complexity': 'medium'
            },
            {
                'name': 'Data Migration Project',
                'cost': 120000, 'benefit': 200000,
                'priority': PriorityEnum.High,
                'status': StatusEnum.InProgress,
                'milestones': 8,
                'complexity': 'high'
            }
        ]
        
        created_projects = []
        
        for proj_data in demo_projects:
            # Check if project exists
            existing = Project.query.filter_by(name=proj_data['name']).first()
            if existing:
                created_projects.append(existing)
                continue
            
            # Create business case
            case = BusinessCase(
                title=f"Business Case: {proj_data['name']}",
                description=f"Demo business case for {proj_data['name']}",
                cost_estimate=proj_data['cost'],
                benefit_estimate=proj_data['benefit'],
                case_type=CaseTypeEnum.Reactive,
                department_id=dept.id,
                created_by=admin.id
            )
            case.calculate_roi()
            case.approval_date = datetime.utcnow().date() - timedelta(days=30)
            db.session.add(case)
            db.session.flush()
            
            # Create project
            project = Project(
                name=proj_data['name'],
                description=f"Demo project: {proj_data['name']}",
                start_date=case.approval_date + timedelta(days=14),
                planned_end_date=case.approval_date + timedelta(days=90),
                status=proj_data['status'],
                priority=proj_data['priority'],
                business_case_id=case.id,
                project_manager_id=pm.id,
                department_id=dept.id,
                created_by=admin.id
            )
            db.session.add(project)
            db.session.flush()
            
            # Create milestones
            for i in range(proj_data['milestones']):
                milestone = ProjectMilestone(
                    project_id=project.id,
                    name=f"Phase {i+1}",
                    description=f"Milestone {i+1} for {proj_data['name']}",
                    due_date=project.start_date + timedelta(days=(i+1)*15),
                    assigned_to=pm.id,
                    completed=i < proj_data['milestones']//2
                )
                if milestone.completed:
                    milestone.completion_date = milestone.due_date - timedelta(days=2)
                db.session.add(milestone)
            
            created_projects.append(project)
        
        db.session.commit()
        print(f"Created {len(created_projects)} demo projects")
        return created_projects

def demonstrate_feature_extraction(projects):
    """Show feature extraction for ML models"""
    print("\n=== FEATURE EXTRACTION DEMO ===")
    
    with app.app_context():
        for project in projects[:2]:  # Show first 2 projects
            print(f"\nProject: {project.name}")
            print(f"Status: {project.status.value}")
            print(f"Priority: {project.priority.value}")
            
            features = extract_project_features(project)
            if features:
                print("Extracted Features:")
                for key, value in features.items():
                    print(f"  {key}: {value}")
            else:
                print("  Could not extract features (insufficient data)")

def demonstrate_ml_training():
    """Show ML model training process"""
    print("\n=== ML MODEL TRAINING DEMO ===")
    
    trainer = MLModelTrainer()
    
    with app.app_context():
        # Extract features
        df = trainer.extract_project_features()
        print(f"Extracted data for training: {len(df)} records")
        
        if not df.empty:
            print(f"Feature columns: {list(df.columns)}")
            print(f"Sample data shape: {df.shape}")
            
            # Show sample statistics
            if 'success_probability' in df.columns:
                print(f"Success probability range: {df['success_probability'].min():.2f} - {df['success_probability'].max():.2f}")
            
            if 'cycle_time' in df.columns:
                print(f"Cycle time range: {df['cycle_time'].min():.0f} - {df['cycle_time'].max():.0f} days")
            
            # Attempt training
            print("\nTraining ML models...")
            success = trainer.train_all_models()
            
            if success:
                print("✓ Models trained successfully")
                
                # Check model files
                models_dir = trainer.models_dir
                model_files = ['success_model.pkl', 'cycle_time_model.pkl', 'anomaly_model.pkl']
                
                for model_file in model_files:
                    filepath = os.path.join(models_dir, model_file)
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        print(f"  ✓ {model_file} ({size} bytes)")
                    else:
                        print(f"  ✗ {model_file} missing")
            else:
                print("✗ Model training failed")
        else:
            print("No data available for training")

def demonstrate_predictions(projects):
    """Show prediction examples using trained models"""
    print("\n=== PREDICTION EXAMPLES ===")
    
    from predict.routes import load_model
    
    with app.app_context():
        # Check if models are available
        success_model = load_model('success')
        cycle_model = load_model('cycle_time')
        anomaly_model = load_model('anomaly')
        
        if not any([success_model, cycle_model, anomaly_model]):
            print("No trained models available for predictions")
            print("Models need to be trained first with sufficient data")
            return
        
        for project in projects:
            print(f"\nProject: {project.name}")
            print(f"Cost Estimate: ${project.business_case.cost_estimate:,}")
            print(f"Expected ROI: {project.business_case.roi_percentage:.1f}%")
            
            features = extract_project_features(project)
            if not features:
                print("  Cannot make predictions - insufficient data")
                continue
            
            # Success prediction
            if success_model:
                try:
                    feature_vector = [features.get(f, 0) for f in success_model['features']]
                    X_scaled = success_model['scaler'].transform([feature_vector])
                    prob = success_model['model'].predict_proba(X_scaled)[0][1]
                    print(f"  Success Probability: {prob:.1%}")
                    
                    if prob >= 0.8:
                        print("    → High confidence of success")
                    elif prob >= 0.5:
                        print("    → Moderate success likelihood")
                    else:
                        print("    → Risk of project challenges")
                except Exception as e:
                    print(f"  Success prediction error: {e}")
            
            # Cycle time prediction
            if cycle_model:
                try:
                    feature_vector = [features.get(f, 0) for f in cycle_model['features']]
                    X_scaled = cycle_model['scaler'].transform([feature_vector])
                    days = cycle_model['model'].predict(X_scaled)[0]
                    print(f"  Estimated Cycle Time: {max(1, int(days))} days ({days/7:.1f} weeks)")
                    
                    if days > 120:
                        print("    → Long-duration project")
                    elif days > 60:
                        print("    → Standard timeline")
                    else:
                        print("    → Fast-track delivery")
                except Exception as e:
                    print(f"  Cycle time prediction error: {e}")
            
            # Anomaly detection
            if anomaly_model:
                try:
                    feature_vector = [features.get(f, 0) for f in anomaly_model['features']]
                    X_scaled = anomaly_model['scaler'].transform([feature_vector])
                    anomaly_score = anomaly_model['model'].decision_function(X_scaled)[0]
                    is_anomaly = anomaly_model['model'].predict(X_scaled)[0] == -1
                    
                    print(f"  Anomaly Score: {anomaly_score:.3f}")
                    if is_anomaly:
                        print("    → ⚠️  Flagged as anomalous - requires attention")
                        
                        # Analyze reasons
                        if features['cost_variance'] > 1.5:
                            print("      - High cost variance detected")
                        if features['complexity_score'] > 15:
                            print("      - Very high complexity")
                        if features['cycle_time'] > 120:
                            print("      - Extended timeline")
                    else:
                        print("    → Normal project characteristics")
                except Exception as e:
                    print(f"  Anomaly detection error: {e}")

def main():
    """Run complete ML predictions demonstration"""
    print("🤖 DeciFrame ML Predictions Demonstration")
    print("=" * 50)
    
    try:
        # Create demo data
        projects = create_demo_data()
        
        # Demonstrate feature extraction
        demonstrate_feature_extraction(projects)
        
        # Show ML training process
        demonstrate_ml_training()
        
        # Show prediction examples
        demonstrate_predictions(projects)
        
        print("\n" + "=" * 50)
        print("🎯 ML Demonstration Complete!")
        print("\nThe predictive analytics system provides:")
        print("• Project success probability scoring")
        print("• Accurate cycle time estimation") 
        print("• Anomaly detection with reasoning")
        print("• Continuous learning through feedback")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()