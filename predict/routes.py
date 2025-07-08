"""
Predictive Analytics API Routes for DeciFrame
Provides ML-powered forecasting for project success, cycle time, and anomaly detection
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import joblib
import numpy as np
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import Project, BusinessCase, PredictionFeedback, User, RoleEnum, StatusEnum, PriorityEnum

predict_bp = Blueprint('predict', __name__, url_prefix='/api/predict')

# Global model cache
MODEL_CACHE = {}

def load_model(model_type):
    """Load ML model from disk with caching"""
    if model_type in MODEL_CACHE:
        return MODEL_CACHE[model_type]
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'analytics', 'models')
    
    try:
        model_path = os.path.join(models_dir, f'{model_type}_model.pkl')
        scaler_path = os.path.join(models_dir, f'{model_type}_scaler.pkl')
        features_path = os.path.join(models_dir, f'{model_type}_features.pkl')
        
        if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
            return None
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        features = joblib.load(features_path)
        
        MODEL_CACHE[model_type] = {
            'model': model,
            'scaler': scaler,
            'features': features
        }
        
        return MODEL_CACHE[model_type]
        
    except Exception as e:
        logging.error(f"Error loading {model_type} model: {str(e)}")
        return None

def extract_project_features(project):
    """Extract features from a project for ML prediction"""
    if not project.business_case:
        return None
    
    # Calculate complexity score
    complexity = len(project.milestones) * 2
    if project.business_case.cost_estimate and project.business_case.cost_estimate > 50000:
        complexity += 3
    if project.business_case.roi_percentage and project.business_case.roi_percentage > 100:
        complexity += 2
    if project.status == StatusEnum.OnHold:
        complexity += 5
    complexity = min(complexity, 20)
    
    # Calculate team size
    team_members = set()
    if project.project_manager_id:
        team_members.add(project.project_manager_id)
    if project.business_case.business_analyst_id:
        team_members.add(project.business_case.business_analyst_id)
    for milestone in project.milestones:
        if milestone.assigned_to:
            team_members.add(milestone.assigned_to)
    team_size = max(len(team_members), 1)
    
    # Priority encoding
    priority_map = {PriorityEnum.Low: 1, PriorityEnum.Medium: 2, PriorityEnum.High: 3}
    priority = priority_map.get(project.priority, 2)
    
    # Department risk
    dept_risk_scores = {1: 3, 2: 4, 3: 6, 4: 5, 5: 7}
    dept_risk = dept_risk_scores.get(project.business_case.department_id, 5)
    
    return {
        'cost_estimate': project.business_case.cost_estimate or 0,
        'actual_cost': project.business_case.actual_cost or project.business_case.cost_estimate or 0,
        'priority': priority,
        'complexity_score': complexity,
        'team_size': team_size,
        'milestone_count': len(project.milestones),
        'department_risk': dept_risk,
        'roi_estimate': project.business_case.roi_percentage or 0,
        'cycle_time': calculate_cycle_time(project),
        'cost_variance': calculate_cost_variance(project)
    }

def calculate_cycle_time(project):
    """Calculate or estimate cycle time"""
    if project.business_case and project.business_case.approval_date and project.start_date:
        return (project.start_date - project.business_case.approval_date).days
    
    # Estimate based on complexity and priority
    base_days = 30
    complexity = len(project.milestones) * 2
    priority_map = {PriorityEnum.Low: 1, PriorityEnum.Medium: 2, PriorityEnum.High: 3}
    priority = priority_map.get(project.priority, 2)
    complexity_factor = complexity / 10
    priority_factor = 2.0 - (priority / 3.0)
    
    return int(base_days * complexity_factor * priority_factor)

def calculate_cost_variance(project):
    """Calculate cost variance ratio"""
    if not project.business_case:
        return 1.0
    
    actual = project.business_case.actual_cost
    estimated = project.business_case.cost_estimate
    
    if actual and estimated and estimated > 0:
        return actual / estimated
    
    return 1.0

@predict_bp.route('/project-success')
@login_required
def predict_project_success():
    """Predict project success probability"""
    project_id = request.args.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'project_id parameter required'}), 400
    
    try:
        project = Project.query.get(int(project_id))
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Load success model
        model_data = load_model('success')
        if not model_data:
            return jsonify({'error': 'Success prediction model not available'}), 503
        
        # Extract features
        features_dict = extract_project_features(project)
        if not features_dict:
            return jsonify({'error': 'Insufficient project data for prediction'}), 400
        
        # Prepare feature vector
        feature_names = model_data['features']
        feature_vector = []
        for feature in feature_names:
            feature_vector.append(features_dict.get(feature, 0))
        
        # Scale features and predict
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = model_data['scaler'].transform(X)
        
        # Get probability prediction
        try:
            probability = model_data['model'].predict_proba(X_scaled)[0][1]  # Probability of success
        except:
            # Fallback to binary prediction if predict_proba fails
            prediction = model_data['model'].predict(X_scaled)[0]
            probability = float(prediction)
        
        # Store prediction for feedback
        feedback = PredictionFeedback()
        feedback.prediction_type = 'project-success'
        feedback.entity_id = project.id
        feedback.predicted_value = probability
        feedback.user_id = current_user.id if current_user.is_authenticated else None
        db.session.add(feedback)
        db.session.commit()
        
        # Trigger AI workflow actions
        from analytics.ai_workflows import AIWorkflowEngine
        workflow_engine = AIWorkflowEngine()
        workflow_engine.check_project_risk_escalation(project.id, probability)
        
        return jsonify({
            'probability': round(probability, 3),
            'confidence': 'high' if abs(probability - 0.5) > 0.3 else 'medium',
            'factors': {
                'complexity': features_dict['complexity_score'],
                'team_size': features_dict['team_size'],
                'cost_estimate': features_dict['cost_estimate'],
                'priority': features_dict['priority']
            }
        })
        
    except Exception as e:
        logging.error(f"Error in project success prediction: {str(e)}")
        return jsonify({'error': 'Prediction service error'}), 500

@predict_bp.route('/cycle-time')
@login_required
def predict_cycle_time():
    """Predict project cycle time in days"""
    case_id = request.args.get('case_id')
    project_id = request.args.get('project_id')
    
    if not case_id and not project_id:
        return jsonify({'error': 'case_id or project_id parameter required'}), 400
    
    try:
        if project_id:
            project = Project.query.get(int(project_id))
            if not project:
                return jsonify({'error': 'Project not found'}), 404
        else:
            case = BusinessCase.query.get(int(case_id))
            if not case:
                return jsonify({'error': 'Business case not found'}), 404
            project = case.project
            if not project:
                return jsonify({'error': 'No project associated with business case'}), 404
        
        # Load cycle time model
        model_data = load_model('cycle_time')
        if not model_data:
            return jsonify({'error': 'Cycle time prediction model not available'}), 503
        
        # Extract features
        features_dict = extract_project_features(project)
        if not features_dict:
            return jsonify({'error': 'Insufficient project data for prediction'}), 400
        
        # Prepare feature vector
        feature_names = model_data['features']
        feature_vector = []
        for feature in feature_names:
            feature_vector.append(features_dict.get(feature, 0))
        
        # Scale features and predict
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = model_data['scaler'].transform(X)
        estimated_days = model_data['model'].predict(X_scaled)[0]
        
        # Ensure reasonable bounds
        estimated_days = max(1, min(int(estimated_days), 365))
        
        # Store prediction for feedback
        feedback = PredictionFeedback()
        feedback.prediction_type = 'cycle-time'
        feedback.entity_id = project.id
        feedback.predicted_value = estimated_days
        feedback.user_id = current_user.id if current_user.is_authenticated else None
        db.session.add(feedback)
        db.session.commit()
        
        # Trigger AI milestone rescheduling workflow
        from analytics.ai_workflows import AIWorkflowEngine
        workflow_engine = AIWorkflowEngine()
        workflow_engine.smart_milestone_reschedule(project.id, estimated_days)
        
        return jsonify({
            'estimated_days': estimated_days,
            'estimated_weeks': round(estimated_days / 7, 1),
            'confidence': 'high' if features_dict['milestone_count'] > 2 else 'medium',
            'factors': {
                'complexity': features_dict['complexity_score'],
                'priority': features_dict['priority'],
                'milestone_count': features_dict['milestone_count']
            }
        })
        
    except Exception as e:
        logging.error(f"Error in cycle time prediction: {str(e)}")
        return jsonify({'error': 'Prediction service error'}), 500

@predict_bp.route('/anomalies')
@login_required
def detect_anomalies():
    """Detect anomalous projects or business cases"""
    module = request.args.get('module', 'project')
    since_str = request.args.get('since')
    
    try:
        # Parse date filter
        since_date = None
        if since_str:
            since_date = datetime.strptime(since_str, '%Y-%m-%d').date()
        else:
            since_date = (datetime.utcnow() - timedelta(days=30)).date()
        
        # Load anomaly model
        model_data = load_model('anomaly')
        if not model_data:
            return jsonify({'error': 'Anomaly detection model not available'}), 503
        
        # Get projects to analyze
        query = Project.query.join(BusinessCase)
        if since_date:
            query = query.filter(Project.created_at >= since_date)
        
        projects = query.all()
        
        anomalies = []
        for project in projects:
            features_dict = extract_project_features(project)
            if not features_dict:
                continue
            
            # Prepare feature vector
            feature_names = model_data['features']
            feature_vector = []
            for feature in feature_names:
                feature_vector.append(features_dict.get(feature, 0))
            
            # Scale features and detect anomaly
            X = np.array(feature_vector).reshape(1, -1)
            X_scaled = model_data['scaler'].transform(X)
            
            # Get anomaly score and prediction
            anomaly_score = model_data['model'].decision_function(X_scaled)[0]
            is_anomaly = model_data['model'].predict(X_scaled)[0] == -1
            
            if is_anomaly:
                anomalies.append({
                    'id': project.id,
                    'name': project.name,
                    'type': 'project',
                    'anomaly_score': round(anomaly_score, 3),
                    'reasons': analyze_anomaly_reasons(features_dict),
                    'created_at': project.created_at.isoformat()
                })
        
        return jsonify({
            'anomalies': anomalies,
            'total_analyzed': len(projects),
            'anomaly_count': len(anomalies),
            'analysis_date': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in anomaly detection: {str(e)}")
        return jsonify({'error': 'Anomaly detection service error'}), 500

def analyze_anomaly_reasons(features_dict):
    """Analyze why a project might be flagged as anomalous"""
    reasons = []
    
    if features_dict['cost_variance'] > 2.0:
        reasons.append('High cost overrun')
    elif features_dict['cost_variance'] < 0.5:
        reasons.append('Unusually low cost')
    
    if features_dict['cycle_time'] > 180:
        reasons.append('Extended cycle time')
    
    if features_dict['complexity_score'] > 15:
        reasons.append('Very high complexity')
    
    if features_dict['cost_estimate'] > 100000:
        reasons.append('High-value project')
    
    if not reasons:
        reasons.append('Unusual feature combination')
    
    return reasons

@predict_bp.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Submit prediction feedback for model improvement"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        prediction_type = data.get('type')
        entity_id = data.get('id')
        actual_value = data.get('actual')
        
        if not all([prediction_type, entity_id, actual_value is not None]):
            return jsonify({'error': 'Missing required fields: type, id, actual'}), 400
        
        # Validate prediction type
        valid_types = ['project-success', 'cycle-time', 'anomaly']
        if prediction_type not in valid_types:
            return jsonify({'error': f'Invalid prediction type. Must be one of: {valid_types}'}), 400
        
        # Create feedback record
        feedback = PredictionFeedback()
        feedback.prediction_type = prediction_type
        feedback.entity_id = int(entity_id)
        feedback.actual_value = float(actual_value)
        feedback.user_id = current_user.id
        
        # Find the original prediction if it exists
        existing_feedback = PredictionFeedback.query.filter_by(
            prediction_type=prediction_type,
            entity_id=int(entity_id)
        ).order_by(PredictionFeedback.feedback_date.desc()).first()
        
        if existing_feedback:
            feedback.predicted_value = existing_feedback.predicted_value
        
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'feedback_id': feedback.id,
            'message': 'Feedback recorded successfully'
        })
        
    except Exception as e:
        logging.error(f"Error submitting prediction feedback: {str(e)}")
        return jsonify({'error': 'Feedback submission failed'}), 500

@predict_bp.route('/model-stats')
@login_required
def get_model_stats():
    """Get statistics about model performance and feedback"""
    if current_user.role not in [RoleEnum.Admin, RoleEnum.Director, RoleEnum.CEO]:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        stats = {}
        
        # Model availability
        models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'analytics', 'models')
        stats['models_available'] = {
            'success': os.path.exists(os.path.join(models_dir, 'success_model.pkl')),
            'cycle_time': os.path.exists(os.path.join(models_dir, 'cycle_time_model.pkl')),
            'anomaly': os.path.exists(os.path.join(models_dir, 'anomaly_model.pkl'))
        }
        
        # Feedback statistics
        feedback_counts = db.session.query(
            PredictionFeedback.prediction_type,
            db.func.count(PredictionFeedback.id)
        ).group_by(PredictionFeedback.prediction_type).all()
        
        stats['feedback_counts'] = {ptype: count for ptype, count in feedback_counts}
        
        # Recent predictions
        recent_predictions = PredictionFeedback.query.filter(
            PredictionFeedback.feedback_date >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        stats['recent_predictions'] = recent_predictions
        
        # Training metadata
        try:
            metadata_path = os.path.join(models_dir, 'training_metadata.pkl')
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                stats['last_training'] = metadata
        except:
            stats['last_training'] = None
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error getting model stats: {str(e)}")
        return jsonify({'error': 'Stats retrieval failed'}), 500

def register_predict_blueprint(app):
    """Register predict blueprint with the Flask app"""
    app.register_blueprint(predict_bp)
    logging.info("✓ Predict blueprint registered")