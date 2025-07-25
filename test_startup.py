#!/usr/bin/env python3
"""
Test script to verify the application can start without errors
"""
import os
import sys

# Set minimal environment variables for testing
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('GCP_PROJECT_ID', 'test-project')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-startup-testing-only')
os.environ.setdefault('FIRESTORE_DATABASE_ID', '(default)')
os.environ.setdefault('GCS_BUCKET_NAME', 'test-bucket')
os.environ.setdefault('CORS_ORIGINS', '*')

print("🧪 Testing application startup...")

try:
    # Test importing the main application
    print("📦 Testing imports...")
    from app.main import app
    print("✅ Main app imported successfully")
    
    # Test basic configuration
    from app.core.config import settings
    print(f"✅ Settings loaded - Environment: {settings.ENVIRONMENT}")
    
    # Test schemas
    from app.models.schemas import User, Cafe, Order
    print("✅ Schemas imported successfully")
    
    # Test database connections (without actually connecting)
    from app.database.firestore import get_user_repo
    print("✅ Database modules imported successfully")
    
    print("🎉 All imports successful! Application should start correctly.")
    
except Exception as e:
    print(f"❌ Error during startup test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)