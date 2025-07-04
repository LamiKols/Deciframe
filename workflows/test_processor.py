"""
Test script to demonstrate workflow processor functionality
"""

from workflows.processor import dispatch_event
from workflows.events import trigger_problem_created, trigger_case_submitted

def test_workflow_processor():
    """Test the workflow processor with sample data"""
    
    print("🧪 Testing Workflow Processor")
    
    # Test problem creation workflow
    problem_data = {
        'id': 999,
        'code': 'TEST001',
        'title': 'Test High Priority Problem',
        'description': 'This is a test problem for workflow testing',
        'priority': 'High',
        'impact': 'Critical',
        'status': 'Open',
        'created_by': 1,
        'dept_id': 1,
        'estimated_cost': 15000
    }
    
    print("\n📋 Testing problem_created event...")
    results = trigger_problem_created(problem_data)
    print(f"Triggered {len(results)} workflows")
    for result in results:
        print(f"  - {result.get('workflow_name')}: {result.get('status')}")
    
    # Test case submission workflow
    case_data = {
        'id': 999,
        'code': 'TEST-C001',
        'title': 'Test Business Case',
        'summary': 'Test case for workflow processing',
        'case_type': 'Reactive',
        'status': 'Draft',
        'priority': 'High',
        'estimated_cost': 3000,  # Low cost for auto-approval
        'expected_benefit': 5000,
        'created_by': 1,
        'dept_id': 1,
        'risk_level': 'Low'
    }
    
    print("\n📊 Testing case_submitted event...")
    results = trigger_case_submitted(case_data)
    print(f"Triggered {len(results)} workflows")
    for result in results:
        print(f"  - {result.get('workflow_name')}: {result.get('status')}")
    
    # Test direct event dispatch
    print("\n🔧 Testing direct event dispatch...")
    context = {'test': True, 'user_id': 1}
    results = dispatch_event('daily_review', context)
    print(f"Triggered {len(results)} workflows for daily_review")
    
    print("\n✅ Workflow processor testing completed")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        test_workflow_processor()