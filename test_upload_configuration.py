"""
Test upload folder configuration and file handling
"""

import sys
import os
sys.path.append('.')

from app import app

def test_upload_config():
    with app.app_context():
        print("Testing upload configuration...")
        
        # Check upload folder configuration
        upload_folder = app.config.get('UPLOAD_FOLDER')
        print(f"Upload folder configured: {upload_folder}")
        
        # Check if directory exists
        if upload_folder and os.path.exists(upload_folder):
            print(f"✓ Upload directory exists: {upload_folder}")
            
            # Check if writable
            test_file = os.path.join(upload_folder, 'test_write.txt')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print("✓ Upload directory is writable")
            except Exception as e:
                print(f"✗ Upload directory not writable: {e}")
                return False
        else:
            print(f"✗ Upload directory does not exist: {upload_folder}")
            return False
        
        # Check max content length
        max_size = app.config.get('MAX_CONTENT_LENGTH')
        print(f"Max file size: {max_size} bytes ({max_size / (1024*1024)}MB)")
        
        # Test pandas and openpyxl
        try:
            import pandas as pd
            import openpyxl
            print("✓ pandas and openpyxl are available")
        except ImportError as e:
            print(f"✗ Missing dependencies: {e}")
            return False
        
        return True

if __name__ == "__main__":
    success = test_upload_config()
    print(f"\nUpload configuration test: {'SUCCESS' if success else 'FAILED'}")