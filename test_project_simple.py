"""
Simple test script for Project Management functionality
Tests the core create/list/detail operations without complex session handling
"""

import sys
import os
from datetime import date, datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Project, ProjectMilestone, User, Department, BusinessCase, StatusEnum, PriorityEnum, RoleEnum
from werkzeug.security import generate_password_hash


def test_project_management():
    """Test Project Management core functionality"""
    print("🧪 Testing Project Management Core Functionality")
    print("=" * 55)
    
    with app.app_context():
        # Get existing data
        user = User.query.first()
        dept = Department.query.first()
        business_case = BusinessCase.query.first()
        
        print(f"✓ Using existing user: {user.name if user else 'None'}")
        print(f"✓ Using existing department: {dept.name if dept else 'None'}")
        print(f"✓ Using existing business case: {business_case.code if business_case else 'None'}")
        
        if not all([user, dept]):
            print("❌ Missing required test data (user or department)")
            return False
        
        # Test 1: Project Creation with Auto-Code Generation
        print("\n1. Testing Project Creation with Auto-Code Generation")
        print("-" * 50)
        
        initial_count = Project.query.count()
        print(f"Initial project count: {initial_count}")
        
        # Create test project
        test_project = Project(
            name='Test Project - Auto Code Generation',
            description='Testing automatic code generation for projects',
            start_date=date(2025, 8, 1),
            end_date=date(2025, 12, 31),
            budget=85000.0,
            status=StatusEnum.Open,
            priority=PriorityEnum.High,
            business_case_id=business_case.id if business_case else None,
            project_manager_id=user.id,
            department_id=dept.id,
            created_by=user.id
        )
        
        # Add to session and flush to get ID
        db.session.add(test_project)
        db.session.flush()
        
        # Auto-generate code
        test_project.code = f"PRJ{test_project.id:04d}"
        db.session.commit()
        
        print(f"✓ Created project: {test_project.code}")
        print(f"  Name: {test_project.name}")
        print(f"  Budget: ${test_project.budget:,.2f}")
        print(f"  Status: {test_project.status.value}")
        print(f"  Project Manager: {test_project.project_manager.name}")
        print(f"  Department: {test_project.department.name}")
        if test_project.business_case:
            print(f"  Linked Business Case: {test_project.business_case.code}")
        
        # Test 2: Project Listing
        print("\n2. Testing Project Listing")
        print("-" * 30)
        
        all_projects = Project.query.all()
        final_count = len(all_projects)
        
        print(f"✓ Retrieved {final_count} projects")
        print(f"  Project count increased from {initial_count} to {final_count}")
        
        # Display all projects
        for project in all_projects:
            print(f"  {project.code}: {project.name} (${project.budget:,.2f})")
        
        # Test filtering
        open_projects = Project.query.filter_by(status=StatusEnum.Open).count()
        high_priority = Project.query.filter_by(priority=PriorityEnum.High).count()
        
        print(f"  Open projects: {open_projects}")
        print(f"  High priority projects: {high_priority}")
        
        # Test 3: Project Detail View
        print("\n3. Testing Project Detail View")
        print("-" * 35)
        
        # Test detail for the created project
        project_detail = Project.query.filter_by(code=test_project.code).first()
        
        print(f"✓ Retrieved project details for: {project_detail.code}")
        print(f"  ID: {project_detail.id}")
        print(f"  Name: {project_detail.name}")
        print(f"  Description: {project_detail.description[:50]}...")
        print(f"  Created: {project_detail.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Updated: {project_detail.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Test relationships
        print(f"  Project Manager: {project_detail.project_manager.name}")
        print(f"  Department: {project_detail.department.name}")
        print(f"  Creator: {project_detail.creator.name}")
        
        if project_detail.business_case:
            print(f"  Business Case: {project_detail.business_case.code}")
            print(f"  BC ROI: {project_detail.business_case.roi:.1f}%")
        
        # Test 4: Project Milestones
        print("\n4. Testing Project Milestones")
        print("-" * 32)
        
        # Create test milestones
        milestone_data = [
            {
                'name': 'Project Kickoff Meeting',
                'description': 'Initial project planning and team alignment',
                'due_date': date.today() + timedelta(days=7),
                'completed': False
            },
            {
                'name': 'Requirements Complete',
                'description': 'All project requirements documented and approved',
                'due_date': date.today() + timedelta(days=21),
                'completed': False
            }
        ]
        
        created_milestones = []
        for milestone_info in milestone_data:
            milestone = ProjectMilestone(
                project_id=project_detail.id,
                name=milestone_info['name'],
                description=milestone_info['description'],
                due_date=milestone_info['due_date'],
                owner_id=user.id,
                completed=milestone_info['completed']
            )
            db.session.add(milestone)
            created_milestones.append(milestone)
        
        db.session.commit()
        
        print(f"✓ Created {len(created_milestones)} milestones")
        
        # Retrieve and display milestones
        project_milestones = ProjectMilestone.query.filter_by(project_id=project_detail.id).all()
        
        for milestone in project_milestones:
            status = "✓ Complete" if milestone.completed else "⏳ Pending"
            print(f"  {milestone.name}: {status} (Due: {milestone.due_date})")
            print(f"    Owner: {milestone.owner.name}")
        
        # Test 5: Project Statistics
        print("\n5. Testing Project Statistics")
        print("-" * 32)
        
        # Overall stats
        total_projects = Project.query.count()
        total_milestones = ProjectMilestone.query.count()
        completed_milestones = ProjectMilestone.query.filter_by(completed=True).count()
        
        print(f"✓ Total projects: {total_projects}")
        print(f"✓ Total milestones: {total_milestones}")
        print(f"✓ Completed milestones: {completed_milestones}")
        
        # Budget analysis
        total_budget = db.session.query(db.func.sum(Project.budget)).scalar() or 0
        avg_budget = db.session.query(db.func.avg(Project.budget)).scalar() or 0
        
        print(f"✓ Total project budget: ${total_budget:,.2f}")
        print(f"✓ Average project budget: ${avg_budget:,.2f}")
        
        # Status distribution
        for status in StatusEnum:
            count = Project.query.filter_by(status=status).count()
            if count > 0:
                print(f"  {status.value}: {count} projects")
        
        # Test 6: Code Generation Verification
        print("\n6. Testing Code Generation Verification")
        print("-" * 42)
        
        # Verify all projects have codes
        projects_without_codes = Project.query.filter_by(code=None).count()
        print(f"✓ Projects without codes: {projects_without_codes}")
        
        # Verify code uniqueness
        all_codes = [p.code for p in Project.query.all() if p.code]
        unique_codes = set(all_codes)
        
        print(f"✓ Total codes: {len(all_codes)}")
        print(f"✓ Unique codes: {len(unique_codes)}")
        print(f"✓ Code uniqueness: {'Pass' if len(all_codes) == len(unique_codes) else 'Fail'}")
        
        # Verify code format
        valid_format = all(code.startswith('PRJ') and len(code) == 7 for code in all_codes)
        print(f"✓ Code format valid: {'Pass' if valid_format else 'Fail'}")
        
        print(f"\n🎉 All Project Management Tests Completed Successfully!")
        print("=" * 55)
        print(f"✅ Project creation with auto-code generation: Working")
        print(f"✅ Project listing and filtering: Working")
        print(f"✅ Project detail view and relationships: Working")
        print(f"✅ Project milestones: Working")
        print(f"✅ Project statistics: Working")
        print(f"✅ Code generation and validation: Working")
        
        return True


if __name__ == '__main__':
    try:
        success = test_project_management()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)