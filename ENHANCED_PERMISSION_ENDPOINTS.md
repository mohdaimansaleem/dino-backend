# Enhanced Permission Endpoints

This document describes the enhanced permission management endpoints that provide comprehensive access control and permission validation for the Dino platform.

## Overview

The enhanced permission system provides:
- **User Permission Management**: View and validate permissions for specific users
- **Role Permission Management**: Manage permissions at the role level
- **Access Validation**: Validate user access to specific resources and actions
- **Authorization Control**: Proper authorization with detailed error messages
- **Permission Summaries**: Grouped views of permissions by resource

## Endpoints

### User Permission Endpoints

#### 1. Get User Permissions
```http
GET /permissions/users/{user_id}/permissions
```

**Description**: Get all permissions assigned to a specific user through their role.

**Authorization**: 
- Users can view their own permissions
- Admins and superadmins can view any user's permissions

**Response Format**:
```json
{
  "success": true,
  "message": "User permissions retrieved successfully",
  "data": {
    "user_id": "user123",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "role": {
      "id": "role123",
      "name": "admin",
      "display_name": "Administrator",
      "description": "System administrator role",
      "exists": true
    },
    "permissions": [
      {
        "id": "perm123",
        "name": "venue.read",
        "description": "Read venue information",
        "resource": "venue",
        "action": "read",
        "scope": "workspace",
        "roles_count": 2
      }
    ],
    "total_permissions": 15
  }
}
```

**Error Responses**:
- `401 Unauthorized`: No authentication token provided
- `403 Forbidden`: "Not authorized to view this user's permissions"
- `404 Not Found`: User not found

#### 2. Get User Permissions Summary
```http
GET /permissions/users/{user_id}/permissions/summary
```

**Description**: Get user permissions grouped by resource for easier understanding.

**Response Format**:
```json
{
  "success": true,
  "message": "User permissions summary retrieved successfully",
  "data": {
    "user_id": "user123",
    "user_name": "John Doe",
    "role": { /* role info */ },
    "total_permissions": 15,
    "resources_count": 5,
    "permissions_by_resource": [
      {
        "resource": "venue",
        "permissions": [/* permission objects */],
        "actions": ["read", "update", "create"]
      },
      {
        "resource": "order",
        "permissions": [/* permission objects */],
        "actions": ["read", "create", "update"]
      }
    ]
  }
}
```

#### 3. Check User Permissions
```http
POST /permissions/users/{user_id}/permissions/check
```

**Description**: Check if a user has specific permissions.

**Request Body**:
```json
[
  "venue.read",
  "order.create",
  "user.update",
  "nonexistent.permission"
]
```

**Response Format**:
```json
{
  "success": true,
  "message": "Permission check completed successfully",
  "data": {
    "user_id": "user123",
    "user_name": "John Doe",
    "role": { /* role info */ },
    "requested_permissions": ["venue.read", "order.create", "user.update", "nonexistent.permission"],
    "permission_results": {
      "venue.read": true,
      "order.create": true,
      "user.update": false,
      "nonexistent.permission": false
    },
    "has_all_permissions": false,
    "has_any_permissions": true,
    "missing_permissions": ["user.update", "nonexistent.permission"]
  }
}
```

### Role Permission Endpoints

#### 4. Get Role Permissions
```http
GET /permissions/roles/{role_id}/permissions
```

**Description**: Get all permissions assigned to a specific role.

**Authorization**: Only admins and superadmins can view role permissions.

**Response Format**:
```json
{
  "success": true,
  "message": "Role permissions retrieved successfully",
  "data": {
    "role_id": "role123",
    "role_name": "admin",
    "role_display_name": "Administrator",
    "role_description": "System administrator role",
    "permissions": [/* permission objects */],
    "total_permissions": 25,
    "users_with_role": 3,
    "missing_permissions": null
  }
}
```

#### 5. Get Role Permissions Summary
```http
GET /permissions/roles/{role_id}/permissions/summary
```

**Description**: Get role permissions grouped by resource.

**Response Format**: Similar to user permissions summary but for roles.

### Access Validation Endpoints

#### 6. Validate User Access
```http
POST /permissions/validate-access
```

**Description**: Validate if a user has access to perform a specific action on a resource.

**Request Body**:
```json
{
  "user_id": "user123",
  "resource": "venue",
  "action": "read"
}
```

**Response Format**:
```json
{
  "success": true,
  "message": "Access validation completed successfully",
  "data": {
    "user_id": "user123",
    "user_name": "John Doe",
    "role": { /* role info */ },
    "resource": "venue",
    "action": "read",
    "permission_name": "venue.read",
    "has_access": true,
    "access_type": "direct",
    "matching_permissions": [
      {
        "id": "perm123",
        "name": "venue.read",
        "description": "Read venue information"
      }
    ]
  }
}
```

**Access Types**:
- `direct`: User has the exact permission
- `wildcard`: User has a wildcard permission (e.g., `venue.*`, `*.read`, `*.*`)
- `none`: User has no matching permissions

## Authorization Rules

### User Permission Access
1. **Own Permissions**: Users can always view their own permissions
2. **Other Users**: Only admins and superadmins can view other users' permissions
3. **Error Message**: "Not authorized to view this user's permissions"

### Role Permission Access
1. **Role Viewing**: Only admins and superadmins can view role permissions
2. **Error Message**: "Not authorized to view role permissions"

### Access Validation
1. **Own Access**: Users can validate their own access
2. **Other Users**: Only admins and superadmins can validate other users' access
3. **Error Message**: "Not authorized to validate this user's access"

## Testing

### Using the Test Script
```bash
# Run the comprehensive test suite
python test_enhanced_permission_endpoints.py <your_auth_token>
```

### Using Postman
1. Import the `enhanced_permission_endpoints.postman_collection.json` file
2. Set the `auth_token` variable with your JWT token
3. Run the "Get Current User Profile" request to auto-populate test variables
4. Execute the test requests

### Manual Testing with cURL

#### Get your own permissions:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/permissions/users/YOUR_USER_ID/permissions
```

#### Check specific permissions:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '["venue.read", "order.create"]' \
     http://localhost:8000/api/v1/permissions/users/YOUR_USER_ID/permissions/check
```

#### Validate access:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "YOUR_USER_ID", "resource": "venue", "action": "read"}' \
     http://localhost:8000/api/v1/permissions/validate-access
```

## Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 403 Forbidden
```json
{
  "detail": "Not authorized to view this user's permissions"
}
```

#### 404 Not Found
```json
{
  "detail": "User not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to get user permissions"
}
```

## Implementation Details

### Key Improvements Made

1. **Enhanced Authorization Logic**:
   - Clear separation between own vs. other user access
   - Proper role-based access control
   - Detailed error messages

2. **Improved Response Format**:
   - Consistent API response structure
   - Rich metadata (user info, role info, counts)
   - Better error handling

3. **Additional Utility Endpoints**:
   - Permission summaries grouped by resource
   - Access validation with wildcard support
   - Comprehensive permission checking

4. **Better Error Messages**:
   - Specific authorization error messages
   - Proper HTTP status codes
   - Detailed validation feedback

### Security Considerations

1. **Authentication Required**: All endpoints require valid JWT token
2. **Authorization Checks**: Proper permission validation before data access
3. **Data Isolation**: Users can only see their own data unless they have admin privileges
4. **Error Information**: Error messages don't leak sensitive information

### Performance Considerations

1. **Efficient Queries**: Optimized database queries for permission retrieval
2. **Caching Opportunities**: Role and permission data can be cached
3. **Pagination Support**: Large permission sets are handled efficiently
4. **Minimal Data Transfer**: Only necessary data is returned

## Integration Examples

### Frontend Integration
```javascript
// Check if user can create orders
const checkPermission = async (userId, permissions) => {
  const response = await fetch(`/api/v1/permissions/users/${userId}/permissions/check`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(permissions)
  });
  
  const result = await response.json();
  return result.data.permission_results;
};

// Usage
const canCreateOrder = await checkPermission(userId, ['order.create']);
if (canCreateOrder['order.create']) {
  // Show create order button
}
```

### Backend Integration
```python
# Validate user access in middleware
async def validate_user_access(user_id: str, resource: str, action: str):
    # Call the validate-access endpoint
    # This can be used in other services or middleware
    pass
```

## Future Enhancements

1. **Permission Caching**: Implement Redis caching for frequently accessed permissions
2. **Audit Logging**: Log all permission checks for security auditing
3. **Dynamic Permissions**: Support for context-based permissions (e.g., venue-specific)
4. **Permission Templates**: Pre-defined permission sets for common roles
5. **Bulk Operations**: Batch permission checks for multiple users/resources

## Troubleshooting

### Common Issues

1. **"Not authorized" errors**: Check if the user has admin privileges
2. **"User not found" errors**: Verify the user ID exists in the system
3. **"Role not found" errors**: Check if the user has a valid role assigned
4. **Empty permissions**: User might not have a role or role has no permissions

### Debug Steps

1. Check authentication token validity
2. Verify user exists and is active
3. Confirm user has a role assigned
4. Validate role has permissions assigned
5. Check permission names match exactly

This enhanced permission system provides a robust foundation for access control in the Dino platform, with clear authorization rules, comprehensive error handling, and extensive testing capabilities.