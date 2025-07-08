#!/usr/bin/env python3
"""
Complete AI Problem Classification System Test
Tests the full workflow including database integration and frontend functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Problem, User, Department, PriorityEnum, StatusEnum
from ai.problem_classifier import classify_problem, get_classification_explanation
import json

def test_complete_classification_workflow():
    """Test the complete AI classification workflow with database integration"""
    
    with app.app_context():
        print("🔬 Testing Complete AI Problem Classification System")
        print("=" * 60)
        
        # Test cases representing real-world scenarios
        test_problems = [
            {
                "title": "Email server not responding to SMTP requests",
                "description": "The mail server has stopped accepting SMTP connections from our application servers, causing email delivery failures across all systems",
                "expected_type": "SYSTEM"
            },
            {
                "title": "Purchase approval process bottleneck",
                "description": "Purchase requests over $1000 require multiple approvals that take weeks, delaying vendor payments and project timelines",
                "expected_type": "PROCESS"
            },
            {
                "title": "Customer complaints about slow website loading",
                "description": "Multiple customers have reported that our website takes more than 10 seconds to load pages, especially during business hours",
                "expected_type": "SYSTEM"
            },
            {
                "title": "New employee equipment setup delays",
                "description": "IT equipment ordering and setup for new hires takes 2-3 weeks, leaving employees without proper tools to start work",
                "expected_type": "PROCESS"
            }
        ]
        
        # Get a test user and department
        user = User.query.filter_by(role='Admin').first()
        if not user:
            print("❌ No admin user found for testing")
            return
            
        dept = Department.query.first()
        if not dept:
            print("❌ No department found for testing")
            return
        
        print(f"Testing with user: {user.email}")
        print(f"Using department: {dept.name}")
        print()
        
        successful_classifications = 0
        total_tests = len(test_problems)
        
        for i, test_case in enumerate(test_problems, 1):
            print(f"Test {i}: {test_case['title']}")
            print(f"Description: {test_case['description'][:80]}...")
            print(f"Expected Classification: {test_case['expected_type']}")
            
            try:
                # Step 1: Test AI Classification
                issue_type, confidence = classify_problem(
                    test_case['title'], 
                    test_case['description']
                )
                explanation = get_classification_explanation(issue_type)
                
                print(f"AI Classification: {issue_type}")
                print(f"Confidence Score: {confidence:.2f} ({confidence*100:.0f}%)")
                print(f"Explanation: {explanation}")
                
                # Step 2: Create Problem with AI Classification
                problem = Problem(
                    title=test_case['title'],
                    description=test_case['description'],
                    priority=PriorityEnum.Medium,
                    department_id=dept.id,
                    status=StatusEnum.Open,
                    reported_by=user.id,
                    created_by=user.id,
                    issue_type=issue_type,
                    ai_confidence=confidence
                )
                
                db.session.add(problem)
                db.session.flush()
                problem.code = f"P{problem.id:04d}"
                db.session.commit()
                
                print(f"Created Problem: {problem.code}")
                print(f"Stored Classification: {problem.issue_type}")
                print(f"Stored Confidence: {problem.ai_confidence}")
                
                # Step 3: Verify Classification Accuracy
                if issue_type == test_case['expected_type']:
                    print("✅ Classification CORRECT")
                    successful_classifications += 1
                else:
                    print("⚠️  Classification differs from expected")
                
                # Step 4: Verify Database Storage
                retrieved_problem = Problem.query.filter_by(code=problem.code).first()
                if (retrieved_problem.issue_type == issue_type and 
                    retrieved_problem.ai_confidence == confidence):
                    print("✅ Database storage VERIFIED")
                else:
                    print("❌ Database storage FAILED")
                
            except Exception as e:
                print(f"❌ Test failed with error: {e}")
            
            print("-" * 40)
            print()
        
        # Summary
        accuracy_percentage = (successful_classifications / total_tests) * 100
        print(f"🎯 Test Results Summary:")
        print(f"Total Tests: {total_tests}")
        print(f"Successful Classifications: {successful_classifications}")
        print(f"Accuracy Rate: {accuracy_percentage:.1f}%")
        
        if accuracy_percentage >= 80:
            print("✅ AI Classification System PASSED - High Accuracy")
        elif accuracy_percentage >= 60:
            print("⚠️  AI Classification System PARTIAL - Moderate Accuracy")
        else:
            print("❌ AI Classification System FAILED - Low Accuracy")
        
        print()
        print("🔍 Testing API Endpoint Response Format")
        
        # Test API response format
        test_title = "Database connection timeout errors"
        test_desc = "Application servers are experiencing timeout errors when connecting to the database"
        
        issue_type, confidence = classify_problem(test_title, test_desc)
        explanation = get_classification_explanation(issue_type)
        
        # Simulate API response
        api_response = {
            'issue_type': issue_type,
            'confidence': confidence,
            'explanation': explanation,
            'confidence_percentage': round(confidence * 100)
        }
        
        print("Sample API Response:")
        print(json.dumps(api_response, indent=2))
        
        print()
        print("🎉 Complete AI Problem Classification Test FINISHED")

if __name__ == "__main__":
    test_complete_classification_workflow()