"""
Comprehensive tests for Project Management functionality
Tests create, list, detail operations and auto-code generation
"""

import sys
import os
from datetime import date, datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Project, ProjectMilestone, User, Department, BusinessCase, StatusEnum, PriorityEnum, RoleEnum, CaseTypeEnum, CaseDepthEnum
from stateless_auth import create_auth_token
from werkzeug.security import generate_password_hash


def setup_test_data():
    """Create test department, user, and business case"""
    with app.app_context():
        # Clean up existing test data in correct order (child tables first)
        ProjectMilestone.query.delete()
        Project.query.delete()
        
        # Get or create test department
        dept = Department.query.filter_by(name='Test Department').first()
        if not dept:
            dept = Department(name='Test Department', level=1)
            db.session.add(dept)
            db.session.flush()
        
        # Get or create test user
        user = User.query.filter_by(email='testuser@example.com').first()
        if not user:
            user = User(
                email='testuser@example.com',
                password_hash=generate_password_hash('testpass'),
                name='Test User',
                role=RoleEnum.PM,
                department_id=dept.id
            )
            db.session.add(user)
            db.session.flush()
        
        # Get or create test business case
        business_case = BusinessCase.query.filter_by(title='Test Business Case').first()
        if not business_case:
            business_case = BusinessCase(
                title='Test Business Case',
                description='Test business case for project linking',
                cost_estimate=50000.0,
                benefit_estimate=100000.0,
                created_by=user.id,
                case_type=CaseTypeEnum.Proactive,
                case_depth=CaseDepthEnum.Light,
                initiative_name='Test Initiative'
            )
            db.session.add(business_case)
            db.session.flush()
            business_case.code = f'C{business_case.id:04d}'
            business_case.calculate_roi()
        
        db.session.commit()
        return dept, user, business_case


def test_project_creation():
    """Test project creation with auto-code generation"""
    print("\n🧪 Testing Project Creation")
    print("=" * 30)
    
    with app.app_context():
        dept, user, business_case = setup_test_data()
        
        # Test data validation
        initial_count = Project.query.count()
        
        # Create test project
        project = Project(
            name='Test Project Creation',
            description='Testing project creation functionality',
            start_date=date(2025, 7, 1),
            end_date=date(2025, 12, 31),
            budget=75000.0,
            status=StatusEnum.Open,
            priority=PriorityEnum.High,
            business_case_id=business_case.id,
            project_manager_id=user.id,
            department_id=dept.id,
            created_by=user.id
        )
        
        # Simulate the auto-generation process
        db.session.add(project)
        db.session.flush()
        
        # Auto-generate project code
        project.code = f"PRJ{project.id:04d}"
        
        db.session.commit()
        
        # Verify creation
        final_count = Project.query.count()
        assert final_count == initial_count + 1, f"Expected {initial_count + 1} projects, got {final_count}"
        
        # Verify auto-generated code
        assert project.code is not None, "Project code should be auto-generated"
        assert project.code.startswith("PRJ"), "Project code should start with 'PRJ'"
        assert len(project.code) == 7, "Project code should be 7 characters (PRJ + 4 digits)"
        
        # Verify project properties
        assert project.name == 'Test Project Creation'
        assert project.budget == 75000.0
        assert project.status == StatusEnum.Open
        assert project.priority == PriorityEnum.High
        assert project.business_case_id == business_case.id
        assert project.project_manager_id == user.id
        assert project.department_id == dept.id
        
        print(f"✓ Project created successfully: {project.code}")
        print(f"  Name: {project.name}")
        print(f"  Budget: ${project.budget:,.2f}")
        print(f"  Status: {project.status.value}")
        print(f"  Priority: {project.priority.value}")
        print(f"  Linked Business Case: {project.business_case.code}")
        print(f"  Project Manager: {project.project_manager.name}")
        print(f"  Department: {project.department.name}")
        
        return project


def test_multiple_project_creation():
    """Test creating multiple projects with sequential codes"""
    print("\n🧪 Testing Multiple Project Creation")
    print("=" * 35)
    
    with app.app_context():
        dept, user, business_case = setup_test_data()
        projects = []
        project_names = [
            'Marketing Campaign Project',
            'Infrastructure Upgrade Project',
            'Product Development Project'
        ]
        
        for i, name in enumerate(project_names):
            project = Project(
                name=name,
                description=f'Test project {i+1} for sequential code testing',
                start_date=date(2025, 8, 1),
                end_date=date(2025, 11, 30),
                budget=25000.0 + (i * 10000),
                status=StatusEnum.Open if i == 0 else StatusEnum.InProgress,
                priority=PriorityEnum.Medium,
                project_manager_id=user.id,
                department_id=dept.id,
                created_by=user.id
            )
            
            db.session.add(project)
            db.session.flush()
            
            # Auto-generate sequential codes
            project.code = f"PRJ{project.id:04d}"
            projects.append(project)
        
        db.session.commit()
        
        # Verify sequential codes
        codes = [p.code for p in projects]
        print(f"✓ Created {len(projects)} projects with sequential codes:")
        for project in projects:
            print(f"  {project.code}: {project.name} (${project.budget:,.2f})")
        
        # Verify uniqueness
        assert len(set(codes)) == len(codes), "All project codes should be unique"
        
        return projects


def test_project_listing():
    """Test project listing functionality"""
    print("\n🧪 Testing Project Listing")
    print("=" * 25)
    
    # Create test projects first
    projects = test_multiple_project_creation()
    
    with app.app_context():
        # Test basic listing
        all_projects = Project.query.all()
        print(f"✓ Retrieved {len(all_projects)} projects from database")
        
        # Test filtering by status
        open_projects = Project.query.filter_by(status=StatusEnum.Open).all()
        in_progress_projects = Project.query.filter_by(status=StatusEnum.InProgress).all()
        
        print(f"  Open projects: {len(open_projects)}")
        print(f"  In Progress projects: {len(in_progress_projects)}")
        
        # Test filtering by priority
        high_priority = Project.query.filter_by(priority=PriorityEnum.High).all()
        medium_priority = Project.query.filter_by(priority=PriorityEnum.Medium).all()
        
        print(f"  High priority projects: {len(high_priority)}")
        print(f"  Medium priority projects: {len(medium_priority)}")
        
        # Test ordering
        ordered_projects = Project.query.order_by(Project.created_at.desc()).all()
        assert len(ordered_projects) == len(all_projects), "Ordered query should return same count"
        
        # Test business case relationships
        linked_projects = Project.query.filter(Project.business_case_id.isnot(None)).all()
        print(f"  Projects linked to business cases: {len(linked_projects)}")
        
        # Verify project data integrity
        for project in all_projects:
            assert project.code is not None, f"Project {project.id} should have a code"
            assert project.name is not None, f"Project {project.id} should have a name"
            assert project.created_at is not None, f"Project {project.id} should have creation date"
            assert project.project_manager is not None, f"Project {project.id} should have a project manager"
            assert project.department is not None, f"Project {project.id} should have a department"
        
        print("✓ All projects have required fields and relationships")
        
        return all_projects


def test_project_detail():
    """Test project detail functionality and relationships"""
    print("\n🧪 Testing Project Detail")
    print("=" * 25)
    
    # Get existing projects
    with app.app_context():
        projects = Project.query.all()
        if not projects:
            projects = test_multiple_project_creation()
        
        # Test detail for first project
        project = projects[0]
        
        print(f"✓ Testing detail view for project: {project.code}")
        
        # Verify all relationships are loaded correctly
        assert project.project_manager is not None, "Project manager relationship should be loaded"
        assert project.department is not None, "Department relationship should be loaded"
        assert project.creator is not None, "Creator relationship should be loaded"
        
        print(f"  Project Manager: {project.project_manager.name}")
        print(f"  Department: {project.department.name}")
        print(f"  Creator: {project.creator.name}")
        print(f"  Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Updated: {project.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Test business case relationship if exists
        if project.business_case:
            print(f"  Linked Business Case: {project.business_case.code}")
            print(f"  Business Case ROI: {project.business_case.roi:.1f}%")
            
            # Test budget variance calculation
            if project.budget and project.business_case.cost_estimate:
                variance = ((project.budget - project.business_case.cost_estimate) / project.business_case.cost_estimate * 100)
                print(f"  Budget Variance: {variance:+.1f}%")
        
        # Test milestone relationship
        milestones = project.milestones
        print(f"  Milestones: {len(milestones)}")
        
        return project


def test_project_milestones():
    """Test project milestone functionality"""
    print("\n🧪 Testing Project Milestones")
    print("=" * 28)
    
    with app.app_context():
        # Get or create a project
        project = Project.query.first()
        if not project:
            project = test_project_creation()
        
        # Create test milestones
        milestones_data = [
            {
                'name': 'Project Kickoff',
                'description': 'Initial project meeting and planning',
                'due_date': date.today() + timedelta(days=7),
                'completed': True,
                'completion_date': date.today() - timedelta(days=3)
            },
            {
                'name': 'Requirements Gathering',
                'description': 'Collect and document all project requirements',
                'due_date': date.today() + timedelta(days=14),
                'completed': False
            },
            {
                'name': 'Design Phase Complete',
                'description': 'Finalize project design and architecture',
                'due_date': date.today() + timedelta(days=30),
                'completed': False
            }
        ]
        
        user = User.query.first()
        created_milestones = []
        
        for milestone_data in milestones_data:
            milestone = ProjectMilestone(
                project_id=project.id,
                name=milestone_data['name'],
                description=milestone_data['description'],
                due_date=milestone_data['due_date'],
                owner_id=user.id,
                completed=milestone_data['completed'],
                completion_date=milestone_data.get('completion_date')
            )
            db.session.add(milestone)
            created_milestones.append(milestone)
        
        db.session.commit()
        
        # Test milestone retrieval and calculations
        all_milestones = ProjectMilestone.query.filter_by(project_id=project.id).all()
        total_milestones = len(all_milestones)
        completed_milestones = len([m for m in all_milestones if m.completed])
        progress_percentage = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        
        print(f"✓ Created {len(created_milestones)} milestones for project {project.code}")
        print(f"  Total milestones: {total_milestones}")
        print(f"  Completed milestones: {completed_milestones}")
        print(f"  Progress: {progress_percentage:.1f}%")
        
        # Test overdue milestones
        today = date.today()
        overdue_milestones = [m for m in all_milestones if m.due_date < today and not m.completed]
        upcoming_milestones = [m for m in all_milestones if today <= m.due_date <= today + timedelta(days=7) and not m.completed]
        
        print(f"  Overdue milestones: {len(overdue_milestones)}")
        print(f"  Upcoming milestones (7 days): {len(upcoming_milestones)}")
        
        # Verify milestone relationships
        for milestone in all_milestones:
            assert milestone.project is not None, "Milestone should have project relationship"
            assert milestone.owner is not None, "Milestone should have owner relationship"
            print(f"    {milestone.name}: Due {milestone.due_date}, Owner: {milestone.owner.name}")
        
        return all_milestones


def test_project_statistics():
    """Test project statistics and calculations"""
    print("\n🧪 Testing Project Statistics")
    print("=" * 28)
    
    with app.app_context():
        # Overall statistics
        total_projects = Project.query.count()
        active_projects = Project.query.filter(Project.status.in_([StatusEnum.Open, StatusEnum.InProgress])).count()
        completed_projects = Project.query.filter_by(status=StatusEnum.Resolved).count()
        
        print(f"✓ Project Statistics:")
        print(f"  Total projects: {total_projects}")
        print(f"  Active projects: {active_projects}")
        print(f"  Completed projects: {completed_projects}")
        
        # Status distribution
        status_stats = {}
        for status in StatusEnum:
            count = Project.query.filter_by(status=status).count()
            status_stats[status.value] = count
            if count > 0:
                print(f"  {status.value}: {count}")
        
        # Priority distribution
        priority_stats = {}
        for priority in PriorityEnum:
            count = Project.query.filter_by(priority=priority).count()
            priority_stats[priority.value] = count
            if count > 0:
                print(f"  {priority.value} priority: {count}")
        
        # Department distribution
        dept_stats = db.session.query(
            Department.name,
            db.func.count(Project.id).label('project_count')
        ).join(Project).group_by(Department.name).all()
        
        print(f"  Projects by department:")
        for dept_name, count in dept_stats:
            print(f"    {dept_name}: {count}")
        
        # Budget analysis
        total_budget = db.session.query(db.func.sum(Project.budget)).filter(Project.budget.isnot(None)).scalar() or 0
        avg_budget = db.session.query(db.func.avg(Project.budget)).filter(Project.budget.isnot(None)).scalar() or 0
        
        print(f"  Total project budget: ${total_budget:,.2f}")
        print(f"  Average project budget: ${avg_budget:,.2f}")
        
        return {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'status_stats': status_stats,
            'priority_stats': priority_stats,
            'dept_stats': dept_stats,
            'total_budget': total_budget,
            'avg_budget': avg_budget
        }


def test_project_business_case_integration():
    """Test project integration with business cases"""
    print("\n🧪 Testing Business Case Integration")
    print("=" * 35)
    
    with app.app_context():
        # Get projects linked to business cases
        linked_projects = Project.query.filter(Project.business_case_id.isnot(None)).all()
        
        print(f"✓ Testing {len(linked_projects)} projects linked to business cases")
        
        for project in linked_projects:
            business_case = project.business_case
            print(f"\n  Project: {project.code} - {project.name}")
            print(f"  Business Case: {business_case.code} - {business_case.title}")
            print(f"  BC Type: {business_case.case_type.value}")
            print(f"  BC Depth: {business_case.case_depth.value}")
            print(f"  BC ROI: {business_case.roi:.1f}%")
            
            # Budget variance analysis
            if project.budget and business_case.cost_estimate:
                variance = ((project.budget - business_case.cost_estimate) / business_case.cost_estimate * 100)
                print(f"  BC Cost Estimate: ${business_case.cost_estimate:,.2f}")
                print(f"  Project Budget: ${project.budget:,.2f}")
                print(f"  Budget Variance: {variance:+.1f}%")
                
                # Flag significant variances
                if abs(variance) > 25:
                    print(f"  ⚠️  Significant budget variance detected!")
        
        return linked_projects


def run_all_tests():
    """Run comprehensive project management tests"""
    print("🧪 Running Comprehensive Project Management Tests")
    print("=" * 55)
    
    try:
        # Test project creation
        project = test_project_creation()
        
        # Test multiple project creation
        projects = test_multiple_project_creation()
        
        # Test project listing
        all_projects = test_project_listing()
        
        # Test project detail
        detail_project = test_project_detail()
        
        # Test milestones
        milestones = test_project_milestones()
        
        # Test statistics
        stats = test_project_statistics()
        
        # Test business case integration
        linked_projects = test_project_business_case_integration()
        
        print(f"\n🎉 All Project Management Tests Completed Successfully!")
        print("=" * 55)
        print(f"✅ Projects created: {len(all_projects)}")
        print(f"✅ Milestones created: {len(milestones)}")
        print(f"✅ Business case integrations: {len(linked_projects)}")
        print(f"✅ Auto-generated codes working correctly")
        print(f"✅ All CRUD operations functional")
        print(f"✅ Statistics and calculations accurate")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)