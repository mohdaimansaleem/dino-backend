# Comprehensive Validation System

## Overview

The Dino Multi-Venue Platform now includes a comprehensive validation system that ensures data consistency, integrity, and security across all collections. This system provides:

- **Strict Data Validation**: All data is validated before being stored in the database
- **Detailed Error Messages**: Clear, actionable error messages for validation failures
- **Reference Integrity**: Ensures foreign key relationships are valid
- **Uniqueness Constraints**: Prevents duplicate emails, phone numbers, etc.
- **Business Logic Validation**: Enforces business rules and constraints
- **Real-time Validation**: Test validation without creating data

## Key Features

### 1. Automatic Validation
All API endpoints now automatically validate data before database operations:
- **Create Operations**: Full validation of all required fields and constraints
- **Update Operations**: Validation of changed fields with existing data context
- **Reference Validation**: Ensures related entities exist and are active

### 2. Comprehensive Error Reporting
Validation errors include:
- **Field Name**: Which field failed validation
- **Current Value**: The invalid value provided
- **Expected Format**: What was expected
- **Detailed Message**: Human-readable explanation

### 3. Collection-Specific Validation

#### Users Collection
```json
{
  "required_fields": ["email", "phone", "first_name", "last_name", "password"],
  "validations": {
    "email": "Valid email format, must be unique",
    "phone": "7-15 digits with optional + prefix, must be unique",
    "password": "Minimum 8 characters with uppercase, lowercase, and digit",
    "role_id": "Must reference existing role",
    "workspace_id": "Must reference active workspace",
    "venue_id": "Must reference active venue"
  }
}
```

#### Workspaces Collection
```json
{
  "required_fields": ["display_name", "business_type"],
  "validations": {
    "display_name": "1-100 characters, generates unique internal name",
    "business_type": "Must be: venue, restaurant, or both",
    "owner_id": "Must reference active user"
  }
}
```

#### Venues Collection
```json
{
  "required_fields": ["name", "description", "location", "phone", "email", "price_range", "workspace_id"],
  "validations": {
    "name": "1-100 characters",
    "phone": "Valid phone format",
    "email": "Valid email format",
    "price_range": "Must be: budget, mid_range, premium, or luxury",
    "workspace_id": "Must reference active workspace",
    "location": "Complete address with required fields"
  }
}
```

#### Orders Collection
```json
{
  "required_fields": ["venue_id", "customer_id", "order_type", "items"],
  "validations": {
    "venue_id": "Must reference active venue",
    "customer_id": "Must reference existing customer",
    "order_type": "Must be: dine_in, takeaway, or delivery",
    "items": "1-50 items with valid menu_item_ids",
    "table_id": "Must reference table in the same venue"
  }
}
```

## API Endpoints

### Validation Testing Endpoints

#### Test User Data Validation
```http
POST /api/v1/validation/validate-user
Content-Type: application/json

{
  "email": "test@example.com",
  "phone": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123"
}
```

#### Test Workspace Registration
```http
POST /api/v1/validation/validate-workspace
Content-Type: application/json

{
  "display_name": "My Restaurant",
  "business_type": "restaurant",
  "description": "A family restaurant"
}
```

#### Generic Collection Validation
```http
POST /api/v1/validation/validate-collection/users?is_update=false
Content-Type: application/json

{
  "email": "user@example.com",
  "phone": "+1234567890",
  "first_name": "Jane",
  "last_name": "Smith",
  "password": "StrongPass123"
}
```

### Get Validation Rules
```http
GET /api/v1/validation/validation-rules/users
```

### Get Validation Examples
```http
GET /api/v1/validation/validation-examples/users
```

## Enhanced API Endpoints

### User Registration with Validation
```http
POST /api/v1/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "phone": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123"
}
```

**Enhanced Response on Validation Error:**
```json
{
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
```

### Workspace Registration with Validation
```http
POST /api/v1/auth/register-workspace
Content-Type: application/json

{
  "workspace_display_name": "My Restaurant Chain",
  "workspace_description": "A chain of family restaurants",
  "business_type": "restaurant",
  "venue_name": "Main Branch",
  "venue_description": "Our flagship restaurant",
  "venue_location": {
    "address": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "postal_code": "10001"
  },
  "venue_phone": "+1234567890",
  "venue_email": "main@restaurant.com",
  "cuisine_types": ["italian", "american"],
  "price_range": "mid_range",
  "owner_email": "owner@restaurant.com",
  "owner_phone": "+1234567891",
  "owner_first_name": "John",
  "owner_last_name": "Doe",
  "owner_password": "SecurePass123",
  "confirm_password": "SecurePass123"
}
```

## Validation Rules by Collection

### Password Validation
- Minimum 8 characters
- Maximum 128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### Email Validation
- Valid email format (RFC compliant)
- Must be unique across users
- Case-insensitive comparison

### Phone Validation
- 7-15 digits
- Optional + prefix
- Must be unique across users
- International format supported

### Reference Validation
- **role_id**: Must exist in roles collection
- **workspace_id**: Must exist and be active in workspaces collection
- **venue_id**: Must exist and be active in venues collection
- **customer_id**: Must exist in customers collection
- **table_id**: Must exist and belong to the specified venue

### Business Logic Validation
- **Workspace Names**: Auto-generated unique internal names
- **Operating Hours**: Valid time ranges and day-of-week values
- **Order Items**: Valid quantities (1-50) and menu item references
- **Location Data**: Complete address information required
- **Enum Fields**: Strict validation against predefined values

## Error Response Format

All validation errors follow a consistent format:

```json
{
  "detail": {
    "message": "Validation failed",
    "validation_errors": [
      {
        "field": "field_name",
        "value": "provided_value",
        "expected": "expected_format",
        "message": "Human readable error message"
      }
    ],
    "error_count": 1
  }
}
```

## Implementation Details

### Validation Service
- **Location**: `app/services/validation_service.py`
- **Purpose**: Centralized validation logic for all collections
- **Features**: Field validation, reference checking, uniqueness validation

### Validated Repositories
- **Location**: `app/database/validated_repository.py`
- **Purpose**: Database repositories with automatic validation
- **Features**: Pre-save validation, error handling, logging

### Validation Middleware
- **Location**: `app/core/validation_middleware.py`
- **Purpose**: Automatic validation decorators
- **Features**: Create/update validation, error formatting

## Usage Examples

### Testing Validation Before Creating Data

```python
# Test user data validation
validation_service = get_validation_service()
user_data = {
    "email": "test@example.com",
    "phone": "+1234567890",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123"
}

errors = await validation_service.validate_user_data(user_data, is_update=False)
if errors:
    # Handle validation errors
    formatted_errors = validation_service.format_validation_errors(errors)
    print(f"Validation failed: {formatted_errors}")
else:
    # Data is valid, proceed with creation
    user_repo = get_validated_user_repo()
    user_id = await user_repo.create(user_data)
```

### Using Validated Repositories

```python
# Repositories automatically validate data
user_repo = get_validated_user_repo()

try:
    user_id = await user_repo.create({
        "email": "user@example.com",
        "phone": "+1234567890",
        "first_name": "Jane",
        "last_name": "Smith",
        "password": "StrongPass123"
    })
    print(f"User created: {user_id}")
except HTTPException as e:
    # Validation failed
    print(f"Validation error: {e.detail}")
```

## Benefits

1. **Data Consistency**: All data follows strict validation rules
2. **Better User Experience**: Clear, actionable error messages
3. **Security**: Prevents injection attacks and malformed data
4. **Maintainability**: Centralized validation logic
5. **Testing**: Easy to test validation without creating data
6. **Documentation**: Self-documenting validation rules
7. **Scalability**: Easy to add new validation rules

## Migration Notes

- All existing endpoints now include automatic validation
- Validation can be tested without creating data
- Error responses include detailed validation information
- Reference integrity is enforced across all collections
- Uniqueness constraints prevent duplicate data

This validation system ensures that the Dino Multi-Venue Platform maintains high data quality and provides excellent developer experience with clear, actionable error messages.