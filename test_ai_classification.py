#!/usr/bin/env python3
"""
Test script for AI Problem Classification system
Demonstrates the AI classification functionality with sample problems
"""

from ai.problem_classifier import classify_problem, get_classification_explanation
import json

def test_classification():
    """Test the AI problem classification with various problem types"""
    
    # Test cases with expected classifications
    test_cases = [
        {
            "title": "Server crashes during peak hours",
            "description": "Our main web server experiences frequent crashes when user traffic is high, causing downtime and impacting customer experience",
            "expected": "SYSTEM"
        },
        {
            "title": "Employee onboarding process is too slow",
            "description": "New employees are waiting weeks to get proper access and training, which delays their productivity and creates frustration",
            "expected": "PROCESS"
        },
        {
            "title": "Database performance is degrading",
            "description": "Query response times have increased significantly, and the database server is showing high CPU usage during normal operations",
            "expected": "SYSTEM"
        },
        {
            "title": "Approval workflow takes too long",
            "description": "Purchase requests are stuck in approval chains for weeks, causing delays in project delivery and vendor payments",
            "expected": "PROCESS"
        }
    ]
    
    print("🤖 Testing AI Problem Classification System")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['title']}")
        print(f"Description: {test_case['description'][:60]}...")
        print(f"Expected: {test_case['expected']}")
        
        try:
            # Get AI classification
            issue_type, confidence = classify_problem(test_case['title'], test_case['description'])
            explanation = get_classification_explanation(issue_type)
            
            print(f"AI Result: {issue_type} (confidence: {confidence:.2f})")
            print(f"Explanation: {explanation}")
            
            # Check if classification matches expectation
            if issue_type == test_case['expected']:
                print("✅ Classification CORRECT")
            else:
                print("⚠️  Classification differs from expected")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 30)
    
    print("\n🎯 AI Problem Classification Test Complete")

if __name__ == "__main__":
    test_classification()