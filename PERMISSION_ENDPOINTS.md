# Permission Endpoints Documentation

This document describes the newly implemented permission endpoints for retrieving user and role permissions.

## Overview

The following endpoints have been added to the `/permissions` router:

1. **Get User Permissions** - Retrieve all permissions for a specific user
2. **Get Role Permissions** - Retrieve all permissions for a specific role  
3. **Get Current User Permissions** - Retrieve permissions for the authenticated user
4. **Get Detailed User Permissions** - Get user permissions with role information
5. **Check User Permissions** - Verify if a user has specific permissions

## Endpoints

### 1. Get User Permissions

**Endpoint:** `GET /permissions/users/{user_id}/permissions`

**Description:** Get all permissions assigned to a user through their role.

**Parameters:**
- `user_id` (path): The ID of the user

**Authentication:** Required (JWT token)

**Authorization:** 
- Users can view their own permissions
- Admins and superadmins can view any user's permissions

**Response:** `List[PermissionResponseDTO]`

**Example:**
```bash
curl -X GET "{{api_base_url}}/permissions/users/user123/permissions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response Example:**
```json
[
  {
    "id": "perm_001",
    "name": "venue.read",
    "description": "Permission to read venue information",
    "resource": "venue",
    "action": "read",
    "scope": "workspace",
    "roles_count": 3,
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "perm_002", 
    "name": "menu.create",
    "description": "Permission to create menu items",
    "resource": "menu",
    "action": "create", 
    "scope": "venue",
    "roles_count": 2,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### 2. Get Role Permissions

**Endpoint:** `GET /permissions/roles/{role_id}/permissions`

**Description:** Get all permissions assigned to a specific role.

**Parameters:**
- `role_id` (path): The ID of the role

**Authentication:** Required (JWT token)

**Authorization:** Only admins and superadmins can view role permissions

**Response:** `List[PermissionResponseDTO]`

**Example:**
```bash
curl -X GET "{{api_base_url}}/permissions/roles/role456/permissions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Get Current User Permissions

**Endpoint:** `GET /permissions/me/permissions`

**Description:** Get all permissions for the currently authenticated user.

**Authentication:** Required (JWT token)

**Authorization:** Any authenticated user can view their own permissions

**Response:** `List[PermissionResponseDTO]`

**Example:**
```bash
curl -X GET "{{api_base_url}}/permissions/me/permissions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Get Detailed User Permissions

**Endpoint:** `GET /permissions/users/{user_id}/permissions/detailed`

**Description:** Get user permissions along with detailed role information.

**Parameters:**
- `user_id` (path): The ID of the user

**Authentication:** Required (JWT token)

**Authorization:**
- Users can view their own detailed permissions
- Admins and superadmins can view any user's detailed permissions

**Response:** `Dict[str, Any]`

**Example:**
```bash
curl -X GET "{{api_base_url}}/permissions/users/user123/permissions/detailed" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response Example:**
```json
{
  "user_id": "user123",
  "role": {
    "id": "role456",
    "name": "admin",
    "display_name": "Administrator",
    "description": "Full administrative access",
    "exists": true
  },
  "permissions": [
    {
      "id": "perm_001",
      "name": "venue.read",
      "description": "Permission to read venue information",
      "resource": "venue",
      "action": "read",
      "scope": "workspace",
      "roles_count": 3,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total_permissions": 15
}
```

### 5. Check User Permissions

**Endpoint:** `POST /permissions/users/{user_id}/permissions/check`

**Description:** Check if a user has specific permissions.

**Parameters:**
- `user_id` (path): The ID of the user

**Request Body:** `List[str]` - List of permission names to check

**Authentication:** Required (JWT token)

**Authorization:**
- Users can check their own permissions
- Admins and superadmins can check any user's permissions

**Response:** `Dict[str, Any]`

**Example:**
```bash
curl -X POST "{{api_base_url}}/permissions/users/user123/permissions/check" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '["venue.read", "menu.create", "order.manage"]'
```

**Response Example:**
```json
{
  "user_id": "user123",
  "permissions": {
    "venue.read": true,
    "menu.create": true,
    "order.manage": false
  },
  "has_all": false,
  "has_any": true
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to view this user's permissions"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to get user permissions"
}
```

## Usage Examples

### Frontend Integration

```javascript
// Get current user permissions
const getUserPermissions = async () => {
  try {
    const response = await fetch('/api/v1/permissions/me/permissions', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const permissions = await response.json();
    return permissions;
  } catch (error) {
    console.error('Failed to get permissions:', error);
  }
};

// Check if user has specific permission
const checkPermission = async (userId, permissionNames) => {
  try {
    const response = await fetch(`/api/v1/permissions/users/${userId}/permissions/check`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(permissionNames)
    });
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Failed to check permissions:', error);
  }
};
```

### Python Client

```python
import requests

def get_user_permissions(user_id, token):
    """Get permissions for a specific user"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'/api/v1/permissions/users/{user_id}/permissions',
        headers=headers
    )
    return response.json()

def check_user_permissions(user_id, permission_names, token):
    """Check if user has specific permissions"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        f'/api/v1/permissions/users/{user_id}/permissions/check',
        headers=headers,
        json=permission_names
    )
    return response.json()
```

## Database Schema Requirements

These endpoints assume the following database structure:

### Users Collection
```json
{
  "id": "user123",
  "email": "user@example.com",
  "role_id": "role456",
  // ... other user fields
}
```

### Roles Collection
```json
{
  "id": "role456",
  "name": "admin",
  "description": "Administrator role",
  "permission_ids": ["perm_001", "perm_002", "perm_003"],
  // ... other role fields
}
```

### Permissions Collection
```json
{
  "id": "perm_001",
  "name": "venue.read",
  "description": "Permission to read venue information",
  "resource": "venue",
  "action": "read",
  "scope": "workspace",
  // ... other permission fields
}
```

## Security Considerations

1. **Authentication Required**: All endpoints require valid JWT authentication
2. **Authorization Checks**: Users can only view their own permissions unless they are admins
3. **Role Validation**: Invalid role IDs are handled gracefully
4. **Permission Validation**: Missing permissions are logged but don't cause failures
5. **Input Validation**: All inputs are validated for proper format and content

## Performance Notes

1. **Caching**: Consider implementing caching for frequently accessed permissions
2. **Batch Operations**: The check permissions endpoint allows checking multiple permissions at once
3. **Database Queries**: Permissions are fetched individually - consider batch fetching for optimization
4. **Role Lookup**: Role information is cached within the request scope

## Testing

Use the provided test script `test_permission_endpoints.py` to verify the endpoints work correctly:

```bash
python test_permission_endpoints.py
```

Note: The test script requires the API server to be running and will need proper authentication tokens for full testing.