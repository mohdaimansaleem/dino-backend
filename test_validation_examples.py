#!/usr/bin/env python3
"""
Validation System Test Examples
Demonstrates the comprehensive validation system
"""
import asyncio
import json
from typing import Dict, Any

# Mock the validation service for demonstration
class MockValidationService:
    """Mock validation service for demonstration"""
    
    async def validate_user_data(self, data: Dict[str, Any], is_update: bool = False, user_id: str = None):
        """Mock user validation"""
        errors = []
        
        # Email validation
        if 'email' in data:
            email = data['email']
            if '@' not in email or '.' not in email:
                errors.append({
                    "field": "email",
                    "value": email,
                    "expected": "valid email format",
                    "message": f"Field email must be a valid email address"
                })
        
        # Password validation
        if 'password' in data:
            password = data['password']
            if len(password) < 8:
                errors.append({
                    "field": "password",
                    "value": password,
                    "expected": "minimum 8 characters",
                    "message": "Password must be at least 8 characters long"
                })
            if not any(c.isupper() for c in password):
                errors.append({
                    "field": "password",
                    "value": password,
                    "expected": "uppercase letter",
                    "message": "Password must contain at least one uppercase letter"
                })
            if not any(c.islower() for c in password):
                errors.append({
                    "field": "password",
                    "value": password,
                    "expected": "lowercase letter",
                    "message": "Password must contain at least one lowercase letter"
                })
            if not any(c.isdigit() for c in password):
                errors.append({
                    "field": "password",
                    "value": password,
                    "expected": "digit",
                    "message": "Password must contain at least one digit"
                })
        
        # Phone validation
        if 'phone' in data:
            phone = data['phone']
            if len(phone.replace('+', '').replace('-', '').replace(' ', '')) < 7:
                errors.append({
                    "field": "phone",
                    "value": phone,
                    "expected": "7-15 digits",
                    "message": "Phone number must have 7-15 digits"
                })
        
        # Required fields
        required_fields = ['email', 'phone', 'first_name', 'last_name', 'password']
        if not is_update:
            for field in required_fields:
                if field not in data or not data[field]:
                    errors.append({
                        "field": field,
                        "value": None,
                        "expected": "required field",
                        "message": f"Missing required field: {field}"
                    })
        
        return errors
    
    def format_validation_errors(self, errors):
        """Format validation errors"""
        if not errors:
            return {"valid": True, "errors": []}
        
        return {
            "valid": False,
            "errors": errors,
            "error_count": len(errors)
        }


async def test_user_validation():
    """Test user data validation"""
    print("=" * 60)
    print("USER DATA VALIDATION TESTS")
    print("=" * 60)
    
    validation_service = MockValidationService()
    
    # Test 1: Valid user data
    print("\n1. Testing VALID user data:")
    valid_user = {
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecurePass123"
    }
    print(f"Data: {json.dumps(valid_user, indent=2)}")
    
    errors = await validation_service.validate_user_data(valid_user)
    result = validation_service.format_validation_errors(errors)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Invalid user data
    print("\n2. Testing INVALID user data:")
    invalid_user = {
        "email": "invalid-email",
        "phone": "123",
        "first_name": "",
        "password": "weak"
    }
    print(f"Data: {json.dumps(invalid_user, indent=2)}")
    
    errors = await validation_service.validate_user_data(invalid_user)
    result = validation_service.format_validation_errors(errors)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Missing required fields
    print("\n3. Testing MISSING required fields:")
    incomplete_user = {
        "email": "test@example.com"
    }
    print(f"Data: {json.dumps(incomplete_user, indent=2)}")
    
    errors = await validation_service.validate_user_data(incomplete_user)
    result = validation_service.format_validation_errors(errors)
    print(f"Result: {json.dumps(result, indent=2)}")


def test_api_examples():
    """Show API request/response examples"""
    print("\n" + "=" * 60)
    print("API REQUEST/RESPONSE EXAMPLES")
    print("=" * 60)
    
    print("\n1. User Registration with Validation:")
    print("POST /api/v1/users/register")
    print("Content-Type: application/json")
    print()
    
    valid_request = {
        "email": "user@example.com",
        "phone": "+1234567890",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123"
    }
    print("Request Body:")
    print(json.dumps(valid_request, indent=2))
    
    print("\nSuccess Response (201):")
    success_response = {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": "user_123",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True
        }
    }
    print(json.dumps(success_response, indent=2))
    
    print("\nValidation Error Response (422):")
    error_response = {
        "detail": {
            "message": "Validation failed",
            "validation_errors": [
                {
                    "field": "email",
                    "value": "invalid-email",
                    "expected": "valid email format",
                    "message": "Field email must be a valid email address"
                },
                {
                    "field": "password",
                    "value": "weak",
                    "expected": "minimum 8 characters with uppercase, lowercase, and digit",
                    "message": "Password must contain at least one uppercase letter"
                }
            ],
            "error_count": 2
        }
    }
    print(json.dumps(error_response, indent=2))
    
    print("\n2. Validation Testing Endpoint:")
    print("POST /api/v1/validation/validate-user")
    print("Content-Type: application/json")
    print()
    
    test_request = {
        "email": "test@example.com",
        "phone": "+1234567890",
        "first_name": "Jane",
        "last_name": "Smith",
        "password": "TestPass123"
    }
    print("Request Body:")
    print(json.dumps(test_request, indent=2))
    
    print("\nValidation Response:")
    validation_response = {
        "valid": True,
        "errors": [],
        "error_count": 0
    }
    print(json.dumps(validation_response, indent=2))


def show_validation_rules():
    """Show validation rules for different collections"""
    print("\n" + "=" * 60)
    print("VALIDATION RULES BY COLLECTION")
    print("=" * 60)
    
    rules = {
        "users": {
            "required_fields": ["email", "phone", "first_name", "last_name", "password"],
            "field_rules": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "unique": True,
                    "description": "Valid email address, must be unique"
                },
                "phone": {
                    "type": "string",
                    "pattern": "^[+]?[1-9]?[0-9]{7,15}$",
                    "unique": True,
                    "description": "Phone number with 7-15 digits, optional + prefix, must be unique"
                },
                "password": {
                    "type": "string",
                    "min_length": 8,
                    "max_length": 128,
                    "requirements": [
                        "At least one uppercase letter",
                        "At least one lowercase letter",
                        "At least one digit"
                    ]
                },
                "role_id": {
                    "type": "string",
                    "reference": "roles",
                    "description": "Must reference an existing role"
                }
            }
        },
        "workspaces": {
            "required_fields": ["display_name", "business_type"],
            "field_rules": {
                "display_name": {
                    "type": "string",
                    "min_length": 1,
                    "max_length": 100,
                    "description": "Workspace display name"
                },
                "business_type": {
                    "type": "enum",
                    "values": ["venue", "restaurant", "both"],
                    "description": "Type of business"
                }
            }
        },
        "venues": {
            "required_fields": ["name", "description", "location", "phone", "email", "price_range", "workspace_id"],
            "field_rules": {
                "price_range": {
                    "type": "enum",
                    "values": ["budget", "mid_range", "premium", "luxury"],
                    "description": "Price range category"
                },
                "location": {
                    "type": "object",
                    "required_fields": ["address", "city", "state", "country", "postal_code"],
                    "description": "Complete address information"
                }
            }
        }
    }
    
    for collection, rule_set in rules.items():
        print(f"\n{collection.upper()} Collection:")
        print(f"Required Fields: {', '.join(rule_set['required_fields'])}")
        print("Field Rules:")
        for field, rule in rule_set['field_rules'].items():
            print(f"  {field}: {rule.get('description', 'No description')}")
            if 'type' in rule:
                print(f"    Type: {rule['type']}")
            if 'values' in rule:
                print(f"    Values: {', '.join(rule['values'])}")
            if 'unique' in rule:
                print(f"    Unique: {rule['unique']}")
            if 'reference' in rule:
                print(f"    References: {rule['reference']} collection")


def show_benefits():
    """Show benefits of the validation system"""
    print("\n" + "=" * 60)
    print("VALIDATION SYSTEM BENEFITS")
    print("=" * 60)
    
    benefits = [
        "✅ Data Consistency: All data follows strict validation rules",
        "✅ Better User Experience: Clear, actionable error messages",
        "✅ Security: Prevents injection attacks and malformed data",
        "✅ Maintainability: Centralized validation logic",
        "✅ Testing: Easy to test validation without creating data",
        "✅ Documentation: Self-documenting validation rules",
        "✅ Scalability: Easy to add new validation rules",
        "✅ Reference Integrity: Ensures foreign key relationships are valid",
        "✅ Uniqueness Constraints: Prevents duplicate emails, phone numbers",
        "✅ Real-time Validation: Test validation before data creation"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    print("\nKey Features:")
    features = [
        "• Automatic validation on all create/update operations",
        "• Detailed field-level error messages",
        "• Reference integrity enforcement",
        "• Uniqueness constraint validation",
        "• Business logic validation",
        "• Real-time validation testing endpoints",
        "• Comprehensive error reporting",
        "• Collection-specific validation rules"
    ]
    
    for feature in features:
        print(f"  {feature}")


async def main():
    """Run all validation examples"""
    print("DINO MULTI-VENUE PLATFORM")
    print("Comprehensive Validation System Demo")
    print("=" * 60)
    
    await test_user_validation()
    test_api_examples()
    show_validation_rules()
    show_benefits()
    
    print("\n" + "=" * 60)
    print("VALIDATION SYSTEM IMPLEMENTATION COMPLETE")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Test the validation endpoints using the API")
    print("2. Try creating users with invalid data to see validation in action")
    print("3. Use the validation testing endpoints to test data before creation")
    print("4. Review the VALIDATION_SYSTEM.md documentation for complete details")


if __name__ == "__main__":
    asyncio.run(main())