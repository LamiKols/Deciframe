"""
ML Model Training Pipeline for DeciFrame Predictive Analytics
Trains models for project success forecasting, cycle-time estimation, and anomaly detection
"""

import os
import sys
import pandas as pd
from datetime import datetime
import joblib
import logging
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Project, BusinessCase, StatusEnum, PriorityEnum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLModelTrainer:
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        
    def extract_project_features(self):
        """Extract features and targets from historical project data"""
        logger.info("Extracting project features from database...")
        
        with app.app_context():
            # Query all completed or active projects with sufficient data
            projects = db.session.query(Project).join(BusinessCase).all()
            
            data = []
            for project in projects:
                if not project.business_case:
                    continue
                    
                # Calculate project metrics
                record = {
                    'project_id': project.id,
                    'business_case_id': project.business_case.id,
                    'cost_estimate': project.business_case.cost_estimate or 0,
                    'actual_cost': project.business_case.actual_cost or project.business_case.cost_estimate or 0,
                    'priority': self._encode_priority(project.priority),
                    'complexity_score': self._calculate_complexity(project),
                    'team_size': self._get_team_size(project),
                    'milestone_count': len(project.milestones),
                    'days_since_start': self._days_since_start(project),
                    'department_risk': self._get_department_risk(project.business_case.department_id),
                    'roi_estimate': project.business_case.roi_percentage or 0,
                }
                
                # Target variables
                record['success_probability'] = self._calculate_success_probability(project)
                record['cycle_time'] = self._calculate_cycle_time(project)
                record['cost_variance'] = self._calculate_cost_variance(project)
                record['is_anomaly'] = self._detect_manual_anomaly(project)
                
                data.append(record)
            
            if not data:
                logger.warning("No project data found for training")
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            logger.info(f"Extracted {len(df)} project records for training")
            return df
    
    def _encode_priority(self, priority):
        """Convert priority enum to numeric value"""
        priority_map = {
            PriorityEnum.Low: 1,
            PriorityEnum.Medium: 2,
            PriorityEnum.High: 3
        }
        return priority_map.get(priority, 2)
    
    def _calculate_complexity(self, project):
        """Calculate project complexity score based on multiple factors"""
        complexity = 0
        
        # Base complexity from milestone count
        complexity += len(project.milestones) * 2
        
        # Business case complexity
        if project.business_case:
            if project.business_case.cost_estimate and project.business_case.cost_estimate > 50000:
                complexity += 3
            if project.business_case.roi_percentage and project.business_case.roi_percentage > 100:
                complexity += 2
        
        # Status complexity
        if project.status == StatusEnum.OnHold:
            complexity += 5
            
        return min(complexity, 20)  # Cap at 20
    
    def _get_team_size(self, project):
        """Estimate team size based on project assignments"""
        team_members = set()
        if project.project_manager_id:
            team_members.add(project.project_manager_id)
        if project.business_case and project.business_case.business_analyst_id:
            team_members.add(project.business_case.business_analyst_id)
        
        # Add milestone owners
        for milestone in project.milestones:
            if milestone.assigned_to:
                team_members.add(milestone.assigned_to)
        
        return max(len(team_members), 1)
    
    def _days_since_start(self, project):
        """Calculate days since project start"""
        if not project.start_date:
            return 0
        return (datetime.utcnow().date() - project.start_date).days
    
    def _get_department_risk(self, department_id):
        """Calculate department risk factor based on historical performance"""
        if not department_id:
            return 5  # Default medium risk
            
        # Simple risk scoring based on department ID
        # In practice, this would be based on historical success rates
        risk_scores = {1: 3, 2: 4, 3: 6, 4: 5, 5: 7}
        return risk_scores.get(department_id, 5)
    
    def _calculate_success_probability(self, project):
        """Calculate target success probability (1 = success, 0 = failure)"""
        if project.status == StatusEnum.Completed:
            # Check if completed on time and within budget
            on_time = True
            if project.end_date and project.planned_end_date:
                on_time = project.end_date <= project.planned_end_date
            
            within_budget = True
            if project.business_case:
                actual = project.business_case.actual_cost or project.business_case.cost_estimate
                estimated = project.business_case.cost_estimate
                if actual and estimated:
                    within_budget = actual <= estimated * 1.1  # 10% tolerance
            
            return 1.0 if (on_time and within_budget) else 0.0
        
        # For active projects, estimate based on current performance
        elif project.status in [StatusEnum.InProgress, StatusEnum.Open]:
            score = 0.7  # Base optimistic score
            
            # Adjust based on overdue milestones
            overdue_count = sum(1 for m in project.milestones 
                              if m.due_date and m.due_date < datetime.utcnow().date() and not m.completed)
            score -= overdue_count * 0.1
            
            # Adjust based on progress
            completed_milestones = sum(1 for m in project.milestones if m.completed)
            total_milestones = len(project.milestones)
            if total_milestones > 0:
                progress = completed_milestones / total_milestones
                score = score * 0.5 + progress * 0.5
            
            return max(0.0, min(1.0, score))
        
        return 0.3  # Default for on-hold or unknown status
    
    def _calculate_cycle_time(self, project):
        """Calculate actual or estimated cycle time in days"""
        if project.business_case and project.business_case.approval_date and project.start_date:
            return (project.start_date - project.business_case.approval_date).days
        
        # Estimate based on complexity and priority
        base_days = 30
        complexity_factor = self._calculate_complexity(project) / 10
        priority_factor = 2.0 - (self._encode_priority(project.priority) / 3.0)
        
        return int(base_days * complexity_factor * priority_factor)
    
    def _calculate_cost_variance(self, project):
        """Calculate cost variance ratio (actual/estimated)"""
        if not project.business_case:
            return 1.0
            
        actual = project.business_case.actual_cost
        estimated = project.business_case.cost_estimate
        
        if actual and estimated and estimated > 0:
            return actual / estimated
        
        return 1.0
    
    def _detect_manual_anomaly(self, project):
        """Manual anomaly detection based on business rules"""
        if not project.business_case:
            return False
            
        # High cost variance
        cost_variance = self._calculate_cost_variance(project)
        if cost_variance > 2.0 or cost_variance < 0.5:
            return True
            
        # Very long cycle time
        cycle_time = self._calculate_cycle_time(project)
        if cycle_time > 180:  # More than 6 months
            return True
            
        # Too many overdue milestones
        overdue_count = sum(1 for m in project.milestones 
                          if m.due_date and m.due_date < datetime.utcnow().date() and not m.completed)
        if overdue_count > 3:
            return True
            
        return False
    
    def train_success_model(self, df):
        """Train project success prediction model"""
        logger.info("Training project success prediction model...")
        
        # Features for success prediction
        feature_cols = ['cost_estimate', 'priority', 'complexity_score', 'team_size', 
                       'milestone_count', 'department_risk', 'roi_estimate']
        
        X = df[feature_cols].fillna(0)
        y = df['success_probability']
        
        if len(X) < 10:
            logger.warning("Insufficient data for success model training")
            return None
            
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Convert to binary classification
        y_train_binary = (y_train > 0.5).astype(int)
        y_test_binary = (y_test > 0.5).astype(int)
        
        model.fit(X_train_scaled, y_train_binary)
        
        # Evaluate
        if len(X_test) > 0:
            y_pred = model.predict(X_test_scaled)
            accuracy = (y_pred == y_test_binary).mean()
            logger.info(f"Success model accuracy: {accuracy:.3f}")
        
        # Save model and scaler
        joblib.dump(model, os.path.join(self.models_dir, 'success_model.pkl'))
        joblib.dump(scaler, os.path.join(self.models_dir, 'success_scaler.pkl'))
        joblib.dump(feature_cols, os.path.join(self.models_dir, 'success_features.pkl'))
        
        logger.info("Success model saved successfully")
        return model
    
    def train_cycle_time_model(self, df):
        """Train cycle time estimation model"""
        logger.info("Training cycle time estimation model...")
        
        feature_cols = ['cost_estimate', 'priority', 'complexity_score', 'team_size', 
                       'milestone_count', 'department_risk']
        
        X = df[feature_cols].fillna(0)
        y = df['cycle_time']
        
        if len(X) < 10:
            logger.warning("Insufficient data for cycle time model training")
            return None
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        if len(X_test) > 0:
            y_pred = model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            logger.info(f"Cycle time model MAE: {mae:.2f} days, R²: {r2:.3f}")
        
        # Save model and scaler
        joblib.dump(model, os.path.join(self.models_dir, 'cycle_time_model.pkl'))
        joblib.dump(scaler, os.path.join(self.models_dir, 'cycle_time_scaler.pkl'))
        joblib.dump(feature_cols, os.path.join(self.models_dir, 'cycle_time_features.pkl'))
        
        logger.info("Cycle time model saved successfully")
        return model
    
    def train_anomaly_model(self, df):
        """Train anomaly detection model"""
        logger.info("Training anomaly detection model...")
        
        feature_cols = ['cost_estimate', 'actual_cost', 'priority', 'complexity_score', 
                       'team_size', 'milestone_count', 'cycle_time', 'cost_variance']
        
        X = df[feature_cols].fillna(0)
        
        if len(X) < 10:
            logger.warning("Insufficient data for anomaly model training")
            return None
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train isolation forest
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X_scaled)
        
        # Evaluate on known anomalies
        anomaly_predictions = model.predict(X_scaled)
        anomaly_score = model.decision_function(X_scaled)
        
        logger.info(f"Anomaly model trained with {len(X)} samples")
        logger.info(f"Detected {sum(anomaly_predictions == -1)} anomalies")
        
        # Save model and scaler
        joblib.dump(model, os.path.join(self.models_dir, 'anomaly_model.pkl'))
        joblib.dump(scaler, os.path.join(self.models_dir, 'anomaly_scaler.pkl'))
        joblib.dump(feature_cols, os.path.join(self.models_dir, 'anomaly_features.pkl'))
        
        logger.info("Anomaly model saved successfully")
        return model
    
    def train_all_models(self):
        """Train all ML models"""
        logger.info("Starting ML model training pipeline...")
        
        # Extract data
        df = self.extract_project_features()
        
        if df.empty:
            logger.error("No data available for training")
            return False
        
        logger.info(f"Training on {len(df)} records")
        
        # Train models
        success_model = self.train_success_model(df)
        cycle_time_model = self.train_cycle_time_model(df)
        anomaly_model = self.train_anomaly_model(df)
        
        # Save metadata
        metadata = {
            'training_date': datetime.utcnow().isoformat(),
            'data_size': len(df),
            'models_trained': {
                'success': success_model is not None,
                'cycle_time': cycle_time_model is not None,
                'anomaly': anomaly_model is not None
            }
        }
        
        joblib.dump(metadata, os.path.join(self.models_dir, 'training_metadata.pkl'))
        
        logger.info("ML model training pipeline completed successfully")
        return True

def main():
    """Main training script entry point"""
    trainer = MLModelTrainer()
    success = trainer.train_all_models()
    
    if success:
        print("✓ ML models trained successfully")
    else:
        print("❌ ML model training failed")
        sys.exit(1)

if __name__ == "__main__":
    main()