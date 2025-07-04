"""
Verification script for Data Export & Retention System
"""
from app import app, db
from models import User, Problem, BusinessCase, Project, AuditLog, Department
from admin.data_management import DataManagementService
from datetime import datetime, timedelta
import csv
import io

def verify_data_management():
    """Verify Data Export & Retention functionality"""
    print("🧪 Verifying Data Export & Retention System")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Test 1: Verify export functionality
            print("\n1. Testing CSV Export Service...")
            
            # Test problems export
            problems_csv = DataManagementService.export_to_csv('problems')
            if problems_csv and len(problems_csv) > 0:
                # Parse CSV to verify structure
                csv_reader = csv.DictReader(io.StringIO(problems_csv))
                headers = csv_reader.fieldnames
                if headers and 'title' in headers:
                    print("✅ Problems CSV export working correctly")
                else:
                    print("❌ Problems CSV missing expected headers")
            else:
                print("❌ Problems CSV export failed")
            
            # Test business cases export
            cases_csv = DataManagementService.export_to_csv('business_cases')
            if cases_csv and len(cases_csv) > 0:
                csv_reader = csv.DictReader(io.StringIO(cases_csv))
                headers = csv_reader.fieldnames
                if headers and 'title' in headers:
                    print("✅ Business Cases CSV export working correctly")
                else:
                    print("❌ Business Cases CSV missing expected headers")
            else:
                print("❌ Business Cases CSV export failed")
            
            # Test projects export
            projects_csv = DataManagementService.export_to_csv('projects')
            if projects_csv and len(projects_csv) > 0:
                csv_reader = csv.DictReader(io.StringIO(projects_csv))
                headers = csv_reader.fieldnames
                if headers and 'name' in headers:
                    print("✅ Projects CSV export working correctly")
                else:
                    print("❌ Projects CSV missing expected headers")
            else:
                print("❌ Projects CSV export failed")
            
            # Test audit logs export
            audit_csv = DataManagementService.export_to_csv('audit_logs')
            if audit_csv and len(audit_csv) > 0:
                csv_reader = csv.DictReader(io.StringIO(audit_csv))
                headers = csv_reader.fieldnames
                if headers and 'action' in headers:
                    print("✅ Audit Logs CSV export working correctly")
                else:
                    print("❌ Audit Logs CSV missing expected headers")
            else:
                print("❌ Audit Logs CSV export failed")
            
            # Test 2: Verify date filtering
            print("\n2. Testing Date Range Filtering...")
            
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            
            filtered_csv = DataManagementService.export_to_csv('problems', start_date=start_date, end_date=end_date)
            if filtered_csv:
                print("✅ Date range filtering working")
            else:
                print("❌ Date range filtering failed")
            
            # Test 3: Verify table statistics
            print("\n3. Testing Table Statistics...")
            
            stats = DataManagementService.get_table_statistics()
            if stats and isinstance(stats, dict):
                expected_keys = ['problems', 'business_cases', 'projects', 'total_records']
                if all(key in stats for key in expected_keys):
                    print("✅ Table statistics working correctly")
                    print(f"   - Problems: {stats.get('problems', 0)}")
                    print(f"   - Business Cases: {stats.get('business_cases', 0)}")
                    print(f"   - Projects: {stats.get('projects', 0)}")
                else:
                    print("❌ Table statistics missing expected keys")
            else:
                print("❌ Table statistics failed")
            
            # Test 4: Verify archive models exist
            print("\n4. Testing Archive Models...")
            
            from models import ArchivedProblem, ArchivedBusinessCase, ArchivedProject
            
            # Check if archive tables exist in database
            try:
                db.session.execute(db.text("SELECT COUNT(*) FROM archived_problems")).fetchone()
                print("✅ ArchivedProblem table exists")
            except Exception:
                print("❌ ArchivedProblem table missing")
            
            try:
                db.session.execute(db.text("SELECT COUNT(*) FROM archived_business_cases")).fetchone()
                print("✅ ArchivedBusinessCase table exists")
            except Exception:
                print("❌ ArchivedBusinessCase table missing")
            
            try:
                db.session.execute(db.text("SELECT COUNT(*) FROM archived_projects")).fetchone()
                print("✅ ArchivedProject table exists")
            except Exception:
                print("❌ ArchivedProject table missing")
            
            # Test 5: Verify retention policies
            print("\n5. Testing Retention Policies...")
            
            policies = DataManagementService.get_retention_policies()
            if policies is not None:
                print("✅ Retention policies service working")
            else:
                print("❌ Retention policies service failed")
            
            print("\n" + "=" * 50)
            print("🏁 Data Management Verification Complete")
            
        except Exception as e:
            print(f"❌ Verification failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    verify_data_management()