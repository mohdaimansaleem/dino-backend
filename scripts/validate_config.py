#!/usr/bin/env python3
"""
Configuration Validation Script for Dino Backend
Validates environment configuration and identifies issues
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.core.config import Settings, validate_configuration
    from pydantic import ValidationError
except ImportError as e:
    print(f"❌ Error importing configuration: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def print_colored(message: str, color: str = "white"):
    """Print colored output"""
    colors = {
        "red": "\033[0;31m",
        "green": "\033[0;32m", 
        "yellow": "\033[1;33m",
        "blue": "\033[0;34m",
        "white": "\033[0;37m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")

def validate_environment():
    """Validate the current environment configuration"""
    print_colored("🔍 Dino Backend Configuration Validation", "blue")
    print_colored("=" * 50, "blue")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print_colored(f"✅ Found .env file: {env_file.absolute()}", "green")
    else:
        print_colored("⚠️ No .env file found - using environment variables only", "yellow")
    
    try:
        # Try to load settings
        print_colored("\n📋 Loading configuration...", "blue")
        settings = Settings()
        print_colored("✅ Configuration loaded successfully", "green")
        
        # Display environment info
        env_info = settings.get_env_info()
        print_colored(f"\n🌍 Environment: {env_info['environment']}", "blue")
        print_colored(f"🐛 Debug Mode: {env_info['debug']}", "blue")
        print_colored(f"📊 Log Level: {env_info['log_level']}", "blue")
        print_colored(f"🏗️ GCP Project: {env_info['gcp_project_id']}", "blue")
        print_colored(f"🗄️ Firestore DB: {env_info['firestore_db']}", "blue")
        print_colored(f"🪣 GCS Bucket: {env_info['gcs_bucket']}", "blue")
        print_colored(f"🔗 QR Base URL: {env_info['qr_base_url']}", "blue")
        print_colored(f"🌐 CORS Origins: {env_info['cors_origins']}", "blue")
        
        # Validate configuration
        print_colored("\n🔍 Running validation checks...", "blue")
        validation_result = validate_configuration()
        
        if validation_result["valid"]:
            print_colored("✅ Configuration validation passed!", "green")
        else:
            print_colored("❌ Configuration validation failed!", "red")
        
        # Display warnings
        if validation_result["warnings"]:
            print_colored("\n⚠️ Warnings:", "yellow")
            for warning in validation_result["warnings"]:
                print_colored(f"  • {warning}", "yellow")
        
        # Display errors
        if validation_result["errors"]:
            print_colored("\n❌ Errors:", "red")
            for error in validation_result["errors"]:
                print_colored(f"  • {error}", "red")
        
        # Security checks
        print_colored("\n🔒 Security Checks:", "blue")
        
        # Check SECRET_KEY
        if hasattr(settings, 'SECRET_KEY'):
            if len(settings.SECRET_KEY) >= 32:
                print_colored("✅ SECRET_KEY length is adequate", "green")
            else:
                print_colored(f"❌ SECRET_KEY too short ({len(settings.SECRET_KEY)} chars, need 32+)", "red")
            
            if settings.SECRET_KEY.startswith("your-") or "change" in settings.SECRET_KEY.lower():
                print_colored("❌ SECRET_KEY appears to be a default value", "red")
            else:
                print_colored("✅ SECRET_KEY appears to be customized", "green")
        else:
            print_colored("❌ SECRET_KEY not found", "red")
        
        # Check CORS
        if settings.is_production:
            if '*' in settings.CORS_ORIGINS:
                print_colored("❌ CORS wildcard '*' detected in production", "red")
            else:
                print_colored("✅ CORS origins properly configured for production", "green")
        else:
            print_colored("ℹ️ Development environment - CORS validation skipped", "blue")
        
        # Check GCP configuration
        if settings.GCP_PROJECT_ID == "your-gcp-project-id":
            print_colored("❌ GCP_PROJECT_ID not configured", "red")
        else:
            print_colored("✅ GCP_PROJECT_ID configured", "green")
        
        # Production-specific checks
        if settings.is_production:
            print_colored("\n🏭 Production Environment Checks:", "blue")
            
            if settings.DEBUG:
                print_colored("⚠️ DEBUG is enabled in production", "yellow")
            else:
                print_colored("✅ DEBUG is disabled in production", "green")
            
            if settings.LOG_LEVEL == "DEBUG":
                print_colored("⚠️ LOG_LEVEL is DEBUG in production", "yellow")
            else:
                print_colored("✅ LOG_LEVEL is appropriate for production", "green")
        
        # Summary
        print_colored("\n📊 Summary:", "blue")
        if validation_result["valid"] and not validation_result["errors"]:
            if validation_result["warnings"]:
                print_colored("⚠️ Configuration is valid but has warnings", "yellow")
                return 1  # Exit code 1 for warnings
            else:
                print_colored("✅ Configuration is fully valid", "green")
                return 0  # Exit code 0 for success
        else:
            print_colored("❌ Configuration has errors that must be fixed", "red")
            return 2  # Exit code 2 for errors
            
    except ValidationError as e:
        print_colored(f"\n❌ Configuration validation failed:", "red")
        for error in e.errors():
            field = error.get('loc', ['unknown'])[0]
            message = error.get('msg', 'Unknown error')
            print_colored(f"  • {field}: {message}", "red")
        return 2
        
    except Exception as e:
        print_colored(f"\n❌ Unexpected error during validation: {e}", "red")
        return 2

def main():
    """Main function"""
    exit_code = validate_environment()
    
    if exit_code == 0:
        print_colored("\n🎉 All checks passed! Ready for deployment.", "green")
    elif exit_code == 1:
        print_colored("\n⚠️ Configuration has warnings. Review before deployment.", "yellow")
    else:
        print_colored("\n❌ Configuration has errors. Fix before deployment.", "red")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()