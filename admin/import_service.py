"""
Bulk Data Import Service for DeciFrame
Handles CSV/Excel file processing and data import
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from werkzeug.datastructures import FileStorage

from app import db
from models import ImportJob, Problem, BusinessCase, Project, User, Department, RoleEnum


class ImportService:
    """Service for handling bulk data imports"""
    
    # Define required and optional fields for each data type
    FIELD_MAPPINGS = {
        'Problem': {
            'required': ['title', 'description'],
            'optional': ['priority', 'reporter_email', 'department_name', 'status', 'impact', 'urgency'],
            'model_fields': {
                'title': 'title',
                'description': 'description', 
                'priority': 'priority',
                'reporter_email': 'reporter_id',  # Will lookup user by email
                'department_name': 'dept_id',     # Will lookup department by name
                'status': 'status',
                'impact': 'impact',
                'urgency': 'urgency'
            }
        },
        'BusinessCase': {
            'required': ['title', 'summary'],
            'optional': ['case_type', 'cost_estimate', 'benefit_estimate', 'submitter_email', 'department_name', 'status'],
            'model_fields': {
                'title': 'title',
                'summary': 'summary',
                'case_type': 'case_type',
                'cost_estimate': 'cost_estimate',
                'benefit_estimate': 'benefit_estimate',
                'submitter_email': 'submitter_id',  # Will lookup user by email
                'department_name': 'dept_id',       # Will lookup department by name
                'status': 'status'
            }
        },
        'Project': {
            'required': ['name', 'description'],
            'optional': ['project_manager_email', 'department_name', 'status', 'budget', 'start_date', 'target_end_date'],
            'model_fields': {
                'name': 'name',
                'description': 'description',
                'project_manager_email': 'project_manager_id',  # Will lookup user by email
                'department_name': 'dept_id',                   # Will lookup department by name
                'status': 'status',
                'budget': 'budget',
                'start_date': 'start_date',
                'target_end_date': 'target_end_date'
            }
        }
    }
    
    @staticmethod
    def validate_file(file: FileStorage) -> Tuple[bool, str]:
        """Validate uploaded file format and size"""
        if not file or not file.filename:
            return False, "No file selected"
        
        allowed_extensions = {'.csv', '.xlsx', '.xls'}
        file_ext = '.' + file.filename.rsplit('.', 1)[-1].lower()
        
        if file_ext not in allowed_extensions:
            return False, f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        
        # Check file size (max 10MB)
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)     # Reset to beginning
        
        if size > 10 * 1024 * 1024:  # 10MB
            return False, "File size exceeds 10MB limit"
        
        return True, "File validation passed"
    
    @staticmethod
    def read_file_preview(file: FileStorage, max_rows: int = 10) -> Tuple[bool, Any]:
        """Read file and return preview data"""
        try:
            file_ext = '.' + file.filename.rsplit('.', 1)[-1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file, nrows=max_rows)
            else:  # Excel files
                df = pd.read_excel(file, nrows=max_rows)
            
            file.seek(0)  # Reset file pointer
            
            return True, {
                'columns': df.columns.tolist(),
                'preview_data': df.to_dict('records'),
                'total_rows': len(df)
            }
        
        except Exception as e:
            file.seek(0)  # Reset file pointer
            return False, f"Error reading file: {str(e)}"
    
    @staticmethod
    def create_import_job(user_id: int, data_type: str, filename: str) -> ImportJob:
        """Create new import job record"""
        job = ImportJob(
            user_id=user_id,
            data_type=data_type,
            filename=filename,
            status='Pending'
        )
        db.session.add(job)
        db.session.commit()
        return job
    
    @staticmethod
    def save_column_mapping(job_id: int, mapping: Dict[str, str]) -> bool:
        """Save column mapping configuration"""
        try:
            job = ImportJob.query.get(job_id)
            if not job:
                return False
            
            job.mapping = mapping
            job.status = 'Mapping'
            db.session.commit()
            return True
        
        except Exception:
            db.session.rollback()
            return False
    
    @staticmethod
    def process_import(job_id: int, file_data: Any) -> Tuple[bool, str]:
        """Process the actual data import"""
        job = ImportJob.query.get(job_id)
        if not job or not job.mapping:
            return False, "Invalid job or missing mapping"
        
        try:
            job.status = 'Importing'
            db.session.commit()
            
            # Read full file
            file_ext = '.' + job.filename.rsplit('.', 1)[-1].lower()
            if file_ext == '.csv':
                df = pd.read_csv(file_data)
            else:
                df = pd.read_excel(file_data)
            
            success_count = 0
            error_count = 0
            errors = []
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    if ImportService._import_single_row(job.data_type, job.mapping, row, index + 1):
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append({
                            'row': index + 1,
                            'error': 'Failed to create record'
                        })
                
                except Exception as e:
                    error_count += 1
                    errors.append({
                        'row': index + 1,
                        'error': str(e)
                    })
            
            # Update job status
            job.rows_success = success_count
            job.rows_failed = error_count
            job.error_details = errors
            job.status = 'Complete' if error_count == 0 else 'Failed'
            db.session.commit()
            
            return True, f"Import completed: {success_count} success, {error_count} failed"
        
        except Exception as e:
            job.status = 'Failed'
            job.error_details = [{'error': f"Import failed: {str(e)}"}]
            db.session.commit()
            return False, f"Import failed: {str(e)}"
    
    @staticmethod
    def _import_single_row(data_type: str, mapping: Dict[str, str], row: pd.Series, row_number: int) -> bool:
        """Import a single row of data"""
        try:
            # Prepare data based on mapping
            data = {}
            field_config = ImportService.FIELD_MAPPINGS[data_type]['model_fields']
            
            for csv_field, model_field in mapping.items():
                if csv_field in row and pd.notna(row[csv_field]):
                    value = row[csv_field]
                    
                    # Handle special field mappings
                    if model_field.endswith('_id') and model_field != 'id':
                        # Lookup foreign key relationships
                        if 'email' in csv_field:
                            user = User.query.filter_by(email=value).first()
                            if user:
                                data[model_field] = user.id
                        elif 'department_name' in csv_field:
                            dept = Department.query.filter_by(name=value).first()
                            if dept:
                                data[model_field] = dept.id
                    else:
                        # Direct field mapping
                        data[model_field] = value
            
            # Create record based on data type
            if data_type == 'Problem':
                record = Problem(**data)
            elif data_type == 'BusinessCase':
                record = BusinessCase(**data)
            elif data_type == 'Project':
                record = Project(**data)
            else:
                return False
            
            db.session.add(record)
            db.session.commit()
            return True
        
        except Exception as e:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_import_jobs(user_id: int = None) -> List[ImportJob]:
        """Get import jobs, optionally filtered by user"""
        query = ImportJob.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(ImportJob.created_at.desc()).all()
    
    @staticmethod
    def get_field_requirements(data_type: str) -> Dict[str, List[str]]:
        """Get required and optional fields for a data type"""
        if data_type in ImportService.FIELD_MAPPINGS:
            return {
                'required': ImportService.FIELD_MAPPINGS[data_type]['required'],
                'optional': ImportService.FIELD_MAPPINGS[data_type]['optional']
            }
        return {'required': [], 'optional': []}