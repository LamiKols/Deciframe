#!/usr/bin/env python3
"""
Sample Data Creation Script for DeciFrame
Creates realistic sample data for new user testing and demonstrations
"""

import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    User, Department, Problem, BusinessCase, Project, ProjectMilestone,
    NotificationTemplate, Epic, UserStory, AuditLog, OrganizationSettings
)

def create_sample_data():
    """Create comprehensive sample data for DeciFrame"""
    
    with app.app_context():
        print("🔄 Creating sample data for DeciFrame...")
        
        # Create organization settings
        org_settings = OrganizationSettings.query.first()
        if not org_settings:
            org_settings = OrganizationSettings(
                name="DeciFrame Demo Corp",
                currency="USD",
                timezone="America/New_York",
                date_format="%Y-%m-%d",
                theme="light"
            )
            db.session.add(org_settings)
            print("✓ Created organization settings")
        
        # Create departments with hierarchy
        departments_data = [
            {"name": "Executive", "code": "EXEC", "level": 1, "parent": None},
            {"name": "Information Technology", "code": "IT", "level": 1, "parent": None},
            {"name": "Human Resources", "code": "HR", "level": 1, "parent": None},
            {"name": "Finance", "code": "FIN", "level": 1, "parent": None},
            {"name": "Operations", "code": "OPS", "level": 1, "parent": None},
            {"name": "Marketing", "code": "MKT", "level": 1, "parent": None},
            {"name": "Software Development", "code": "DEV", "level": 2, "parent": "IT"},
            {"name": "Infrastructure", "code": "INFRA", "level": 2, "parent": "IT"},
            {"name": "Quality Assurance", "code": "QA", "level": 2, "parent": "IT"},
            {"name": "Business Analysis", "code": "BA", "level": 2, "parent": "IT"},
            {"name": "Frontend Team", "code": "FE", "level": 3, "parent": "DEV"},
            {"name": "Backend Team", "code": "BE", "level": 3, "parent": "DEV"},
        ]
        
        dept_map = {}
        for dept_data in departments_data:
            dept = Department.query.filter_by(code=dept_data["code"]).first()
            if not dept:
                parent_dept = None
                if dept_data["parent"]:
                    parent_dept = dept_map.get(dept_data["parent"])
                
                dept = Department(
                    name=dept_data["name"],
                    code=dept_data["code"],
                    level=dept_data["level"],
                    parent=parent_dept
                )
                db.session.add(dept)
                dept_map[dept_data["code"]] = dept
                print(f"✓ Created department: {dept.name}")
        
        db.session.commit()
        
        # Refresh department map after commit
        for dept_data in departments_data:
            dept_map[dept_data["code"]] = Department.query.filter_by(code=dept_data["code"]).first()
        
        # Create sample users
        users_data = [
            {"name": "Sarah Chen", "email": "sarah.chen@democorp.com", "role": "CEO", "dept": "EXEC"},
            {"name": "Michael Rodriguez", "email": "michael.rodriguez@democorp.com", "role": "Director", "dept": "IT"},
            {"name": "Jennifer Park", "email": "jennifer.park@democorp.com", "role": "Manager", "dept": "DEV"},
            {"name": "David Thompson", "email": "david.thompson@democorp.com", "role": "BA", "dept": "BA"},
            {"name": "Lisa Wang", "email": "lisa.wang@democorp.com", "role": "PM", "dept": "IT"},
            {"name": "Robert Johnson", "email": "robert.johnson@democorp.com", "role": "Staff", "dept": "FE"},
            {"name": "Emily Davis", "email": "emily.davis@democorp.com", "role": "Staff", "dept": "BE"},
            {"name": "James Wilson", "email": "james.wilson@democorp.com", "role": "Manager", "dept": "QA"},
            {"name": "Amanda Brown", "email": "amanda.brown@democorp.com", "role": "Director", "dept": "HR"},
            {"name": "Kevin Lee", "email": "kevin.lee@democorp.com", "role": "Staff", "dept": "INFRA"},
        ]
        
        user_map = {}
        for user_data in users_data:
            user = User.query.filter_by(email=user_data["email"]).first()
            if not user:
                dept = dept_map.get(user_data["dept"])
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    role=user_data["role"],
                    department=dept,
                    password_hash=generate_password_hash("demo123"),
                    is_active=True,
                    theme="light"
                )
                db.session.add(user)
                user_map[user_data["email"]] = user
                print(f"✓ Created user: {user.name} ({user.role})")
        
        db.session.commit()
        
        # Refresh user map after commit
        for user_data in users_data:
            user_map[user_data["email"]] = User.query.filter_by(email=user_data["email"]).first()
        
        # Create sample problems
        problems_data = [
            {
                "title": "Customer Portal Performance Issues",
                "description": "Users are experiencing slow load times on the customer portal, especially during peak hours. Response times exceed 5 seconds for dashboard loading.",
                "category": "technical",
                "priority": "high",
                "impact": "high",
                "urgency": "high",
                "reporter": "sarah.chen@democorp.com",
                "dept": "IT"
            },
            {
                "title": "Manual Invoice Processing Bottleneck",
                "description": "Finance team is spending 40+ hours per week manually processing invoices. This creates delays in vendor payments and increases error rates.",
                "category": "process",
                "priority": "medium",
                "impact": "medium", 
                "urgency": "medium",
                "reporter": "michael.rodriguez@democorp.com",
                "dept": "FIN"
            },
            {
                "title": "Employee Onboarding Delays",
                "description": "New employee onboarding process takes 3-4 weeks due to manual paperwork and multiple system access requests. This delays productivity and affects new hire experience.",
                "category": "process",
                "priority": "medium",
                "impact": "medium",
                "urgency": "low",
                "reporter": "amanda.brown@democorp.com",
                "dept": "HR"
            },
            {
                "title": "Mobile App Crash Reports",
                "description": "iOS mobile app is crashing for users on iOS 17+. Crash reports show memory allocation issues in the image processing module.",
                "category": "technical",
                "priority": "high",
                "impact": "high",
                "urgency": "high",
                "reporter": "jennifer.park@democorp.com",
                "dept": "DEV"
            },
            {
                "title": "Data Backup Recovery Time",
                "description": "Current backup system takes 8+ hours for full recovery. We need to reduce RTO to under 2 hours to meet business continuity requirements.",
                "category": "technical",
                "priority": "medium",
                "impact": "high",
                "urgency": "low",
                "reporter": "kevin.lee@democorp.com",
                "dept": "INFRA"
            }
        ]
        
        problem_map = {}
        for i, prob_data in enumerate(problems_data, 1):
            problem = Problem.query.filter_by(title=prob_data["title"]).first()
            if not problem:
                reporter = user_map.get(prob_data["reporter"])
                dept = dept_map.get(prob_data["dept"])
                
                problem = Problem(
                    title=prob_data["title"],
                    description=prob_data["description"],
                    category=prob_data["category"],
                    priority=prob_data["priority"],
                    impact=prob_data["impact"],
                    urgency=prob_data["urgency"],
                    status="submitted",
                    reporter=reporter,
                    department=dept,
                    created_at=datetime.utcnow() - timedelta(days=30-i*5)
                )
                db.session.add(problem)
                problem_map[prob_data["title"]] = problem
                print(f"✓ Created problem: {problem.title}")
        
        db.session.commit()
        
        # Create sample business cases
        business_cases_data = [
            {
                "title": "Customer Portal Performance Optimization",
                "description": "Implement CDN, database optimization, and caching layer to improve customer portal performance",
                "problem": "Customer Portal Performance Issues",
                "business_value": 250000,
                "implementation_cost": 75000,
                "timeline_months": 4,
                "roi_percentage": 233.33,
                "case_type": "reactive",
                "depth": "full",
                "status": "approved"
            },
            {
                "title": "Invoice Processing Automation System",
                "description": "Deploy RPA solution for automated invoice processing with OCR and approval workflows",
                "problem": "Manual Invoice Processing Bottleneck",
                "business_value": 180000,
                "implementation_cost": 45000,
                "timeline_months": 3,
                "roi_percentage": 300.0,
                "case_type": "reactive",
                "depth": "full",
                "status": "submitted"
            },
            {
                "title": "Digital Employee Onboarding Platform",
                "description": "Build comprehensive digital onboarding platform with automated workflows and integration",
                "problem": "Employee Onboarding Delays",
                "business_value": 120000,
                "implementation_cost": 35000,
                "timeline_months": 6,
                "roi_percentage": 242.86,
                "case_type": "reactive",
                "depth": "light",
                "status": "draft"
            },
            {
                "title": "Mobile App Stability Enhancement",
                "description": "Comprehensive mobile app refactoring with memory management improvements and iOS 17+ compatibility",
                "problem": "Mobile App Crash Reports",
                "business_value": 320000,
                "implementation_cost": 85000,
                "timeline_months": 5,
                "roi_percentage": 276.47,
                "case_type": "reactive",
                "depth": "full",
                "status": "approved"
            }
        ]
        
        business_case_map = {}
        for i, bc_data in enumerate(business_cases_data, 1):
            bc = BusinessCase.query.filter_by(title=bc_data["title"]).first()
            if not bc:
                problem = problem_map.get(bc_data["problem"])
                author = user_map.get("david.thompson@democorp.com")  # BA creates business cases
                
                bc = BusinessCase(
                    title=bc_data["title"],
                    description=bc_data["description"],
                    problem=problem,
                    business_value=bc_data["business_value"],
                    implementation_cost=bc_data["implementation_cost"],
                    timeline_months=bc_data["timeline_months"],
                    roi_percentage=bc_data["roi_percentage"],
                    case_type=bc_data["case_type"],
                    depth=bc_data["depth"],
                    status=bc_data["status"],
                    author=author,
                    created_at=datetime.utcnow() - timedelta(days=25-i*4)
                )
                db.session.add(bc)
                business_case_map[bc_data["title"]] = bc
                print(f"✓ Created business case: {bc.title}")
        
        db.session.commit()
        
        # Create sample projects for approved business cases
        projects_data = [
            {
                "title": "Portal Performance Enhancement Project",
                "description": "Multi-phase project to optimize customer portal performance through infrastructure and code improvements",
                "business_case": "Customer Portal Performance Optimization",
                "budget": 75000,
                "status": "active",
                "manager": "lisa.wang@democorp.com",
                "start_date": datetime.utcnow() - timedelta(days=15),
                "target_end_date": datetime.utcnow() + timedelta(days=105)
            },
            {
                "title": "Mobile App iOS 17 Compatibility",
                "description": "Technical project to resolve iOS 17+ compatibility issues and improve app stability",
                "business_case": "Mobile App Stability Enhancement",
                "budget": 85000,
                "status": "planning",
                "manager": "jennifer.park@democorp.com",
                "start_date": datetime.utcnow() + timedelta(days=7),
                "target_end_date": datetime.utcnow() + timedelta(days=150)
            }
        ]
        
        project_map = {}
        for proj_data in projects_data:
            project = Project.query.filter_by(title=proj_data["title"]).first()
            if not project:
                bc = business_case_map.get(proj_data["business_case"])
                manager = user_map.get(proj_data["manager"])
                
                project = Project(
                    title=proj_data["title"],
                    description=proj_data["description"],
                    business_case=bc,
                    budget=proj_data["budget"],
                    status=proj_data["status"],
                    project_manager=manager,
                    start_date=proj_data["start_date"],
                    target_end_date=proj_data["target_end_date"]
                )
                db.session.add(project)
                project_map[proj_data["title"]] = project
                print(f"✓ Created project: {project.title}")
        
        db.session.commit()
        
        # Create sample milestones
        milestones_data = [
            {
                "project": "Portal Performance Enhancement Project",
                "title": "Infrastructure Assessment Complete",
                "description": "Complete assessment of current infrastructure and identify bottlenecks",
                "due_date": datetime.utcnow() - timedelta(days=5),
                "is_completed": True,
                "completion_date": datetime.utcnow() - timedelta(days=3)
            },
            {
                "project": "Portal Performance Enhancement Project", 
                "title": "CDN Implementation",
                "description": "Deploy and configure CDN for static asset delivery",
                "due_date": datetime.utcnow() + timedelta(days=15),
                "is_completed": False
            },
            {
                "project": "Portal Performance Enhancement Project",
                "title": "Database Optimization",
                "description": "Optimize database queries and implement indexing improvements",
                "due_date": datetime.utcnow() + timedelta(days=30),
                "is_completed": False
            },
            {
                "project": "Mobile App iOS 17 Compatibility",
                "title": "iOS 17 Testing Environment Setup",
                "description": "Set up comprehensive testing environment for iOS 17+ devices",
                "due_date": datetime.utcnow() + timedelta(days=10),
                "is_completed": False
            }
        ]
        
        for milestone_data in milestones_data:
            milestone = ProjectMilestone.query.filter_by(title=milestone_data["title"]).first()
            if not milestone:
                project = project_map.get(milestone_data["project"])
                
                milestone = ProjectMilestone(
                    project=project,
                    title=milestone_data["title"],
                    description=milestone_data["description"],
                    due_date=milestone_data["due_date"],
                    is_completed=milestone_data["is_completed"],
                    completion_date=milestone_data.get("completion_date")
                )
                db.session.add(milestone)
                print(f"✓ Created milestone: {milestone.title}")
        
        # Create sample epics and user stories
        epics_data = [
            {
                "title": "Performance Monitoring Dashboard",
                "description": "Create comprehensive dashboard for monitoring portal performance metrics in real-time",
                "business_case": "Customer Portal Performance Optimization",
                "status": "approved",
                "workflow_status": "approved"
            },
            {
                "title": "User Experience Optimization",
                "description": "Enhance user interface and user experience for better customer engagement",
                "business_case": "Customer Portal Performance Optimization", 
                "status": "submitted",
                "workflow_status": "submitted"
            }
        ]
        
        epic_map = {}
        for epic_data in epics_data:
            epic = Epic.query.filter_by(title=epic_data["title"]).first()
            if not epic:
                bc = business_case_map.get(epic_data["business_case"])
                author = user_map.get("david.thompson@democorp.com")
                
                epic = Epic(
                    title=epic_data["title"],
                    description=epic_data["description"],
                    business_case=bc,
                    status=epic_data["status"],
                    workflow_status=epic_data["workflow_status"],
                    author=author
                )
                db.session.add(epic)
                epic_map[epic_data["title"]] = epic
                print(f"✓ Created epic: {epic.title}")
        
        db.session.commit()
        
        # Create sample user stories
        stories_data = [
            {
                "epic": "Performance Monitoring Dashboard",
                "title": "Real-time Performance Metrics Display",
                "description": "As an admin, I want to see real-time performance metrics so that I can monitor system health",
                "acceptance_criteria": "Given I am on the dashboard, when I view performance metrics, then I see current response times, error rates, and throughput",
                "story_points": 8,
                "priority": "high"
            },
            {
                "epic": "Performance Monitoring Dashboard",
                "title": "Performance Alert Configuration",
                "description": "As an admin, I want to configure performance alerts so that I'm notified of issues immediately",
                "acceptance_criteria": "Given I am configuring alerts, when I set thresholds, then I receive notifications when limits are exceeded",
                "story_points": 5,
                "priority": "medium"
            },
            {
                "epic": "User Experience Optimization",
                "title": "Responsive Navigation Menu",
                "description": "As a user, I want a responsive navigation menu so that I can easily navigate on mobile devices",
                "acceptance_criteria": "Given I am on a mobile device, when I access the navigation, then it displays properly and is fully functional",
                "story_points": 3,
                "priority": "medium"
            }
        ]
        
        for story_data in stories_data:
            story = UserStory.query.filter_by(title=story_data["title"]).first()
            if not story:
                epic = epic_map.get(story_data["epic"])
                author = user_map.get("david.thompson@democorp.com")
                
                story = UserStory(
                    epic=epic,
                    title=story_data["title"],
                    description=story_data["description"],
                    acceptance_criteria=story_data["acceptance_criteria"],
                    story_points=story_data["story_points"],
                    priority=story_data["priority"],
                    status="draft",
                    author=author
                )
                db.session.add(story)
                print(f"✓ Created user story: {story.title}")
        
        db.session.commit()
        
        # Create audit log entries for realistic activity
        audit_entries = [
            {
                "user": "david.thompson@democorp.com",
                "action": "create_business_case",
                "module": "Business Cases",
                "target": "Customer Portal Performance Optimization",
                "details": "Created comprehensive business case for portal performance improvements",
                "timestamp": datetime.utcnow() - timedelta(days=20)
            },
            {
                "user": "michael.rodriguez@democorp.com",
                "action": "approve_business_case", 
                "module": "Business Cases",
                "target": "Customer Portal Performance Optimization",
                "details": "Approved business case after technical review",
                "timestamp": datetime.utcnow() - timedelta(days=18)
            },
            {
                "user": "lisa.wang@democorp.com",
                "action": "create_project",
                "module": "Projects",
                "target": "Portal Performance Enhancement Project",
                "details": "Created project from approved business case",
                "timestamp": datetime.utcnow() - timedelta(days=15)
            }
        ]
        
        for audit_data in audit_entries:
            user = user_map.get(audit_data["user"])
            audit = AuditLog(
                user=user,
                action=audit_data["action"],
                module=audit_data["module"],
                target=audit_data["target"],
                details=audit_data["details"],
                timestamp=audit_data["timestamp"]
            )
            db.session.add(audit)
        
        db.session.commit()
        
        print("\n🎉 Sample data creation completed successfully!")
        print("\n📊 Created:")
        print(f"   • {len(departments_data)} departments with hierarchy")
        print(f"   • {len(users_data)} users across different roles")
        print(f"   • {len(problems_data)} realistic problems")
        print(f"   • {len(business_cases_data)} business cases")
        print(f"   • {len(projects_data)} active projects")
        print(f"   • {len(milestones_data)} project milestones")
        print(f"   • {len(epics_data)} epics with user stories")
        print(f"   • {len(audit_entries)} audit log entries")
        
        print("\n👥 Sample Login Credentials:")
        print("   • CEO: sarah.chen@democorp.com / demo123")
        print("   • IT Director: michael.rodriguez@democorp.com / demo123")
        print("   • Dev Manager: jennifer.park@democorp.com / demo123")
        print("   • Business Analyst: david.thompson@democorp.com / demo123")
        print("   • Project Manager: lisa.wang@democorp.com / demo123")
        
        print("\n✨ New users can now explore a fully populated system!")

if __name__ == "__main__":
    create_sample_data()