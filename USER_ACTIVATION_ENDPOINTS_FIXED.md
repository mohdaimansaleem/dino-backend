# User Activation/Deactivation Endpoints - Fixed

## Summary of Changes

I've fixed the user activation/deactivation endpoints to match your requirements:

### ✅ **Fixed Endpoints:**

1. **Deactivate User**
   - **OLD:** `DELETE /users/{user_id}` 
   - **NEW:** `PUT /users/{user_id}/deactivate` ✅
   - **Action:** Sets `is_active = False`

2. **Activate User** 
   - **OLD:** `POST /users/{user_id}/activate`
   - **NEW:** `PUT /users/{user_id}/activate` ✅
   - **Action:** Sets `is_active = True`

## Endpoint Details

### 1. Deactivate User

**Endpoint:** `PUT /users/{user_id}/deactivate`

**Method:** PUT

**Description:** Deactivate a user by setting `is_active` to `False`

**Parameters:**
- `user_id` (path): The ID of the user to deactivate

**Authentication:** Required (Admin only)

**Request:**
```bash
curl -X PUT "{{api_base_url}}/users/{{user_id}}/deactivate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "User deactivated successfully",
  "timestamp": "2025-08-06T14:47:24.756930"
}
```

### 2. Activate User

**Endpoint:** `PUT /users/{user_id}/activate`

**Method:** PUT

**Description:** Activate a user by setting `is_active` to `True`

**Parameters:**
- `user_id` (path): The ID of the user to activate

**Authentication:** Required (Admin only)

**Request:**
```bash
curl -X PUT "{{api_base_url}}/users/{{user_id}}/activate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "User activated successfully",
  "timestamp": "2025-08-06T14:47:24.756930"
}
```

## Implementation Details

### What the endpoints do:

1. **Deactivate (`PUT /users/{user_id}/deactivate`)**:
   - Validates user exists
   - Checks admin permissions
   - Updates user record: `{"is_active": False}`
   - Returns success message

2. **Activate (`PUT /users/{user_id}/activate`)**:
   - Validates user exists  
   - Checks admin permissions
   - Updates user record: `{"is_active": True}`
   - Returns success message

### Security & Validation:

- ✅ **Authentication Required:** Both endpoints require JWT token
- ✅ **Admin Only:** Only admin/superadmin users can activate/deactivate
- ✅ **User Validation:** Checks if user exists before operation
- ✅ **Permission Validation:** Uses existing permission validation logic
- ✅ **Error Handling:** Proper HTTP status codes and error messages
- ✅ **Logging:** All operations are logged for audit trail

### Database Changes:

Both endpoints simply update the `is_active` field in the user document:

```javascript
// Deactivate
{ "is_active": false, "updated_at": "2024-01-01T00:00:00Z" }

// Activate  
{ "is_active": true, "updated_at": "2024-01-01T00:00:00Z" }
```

## Files Modified

1. **`app/api/v1/endpoints/user.py`**
   - Changed `DELETE /{user_id}` to `PUT /{user_id}/deactivate`
   - Changed `POST /{user_id}/activate` to `PUT /{user_id}/activate`
   
2. **`app/api/v1/endpoints/user_management.py`**
   - Changed `DELETE /users/{user_id}` to `PUT /users/{user_id}/deactivate`
   - Changed `POST /users/{user_id}/activate` to `PUT /users/{user_id}/activate`

## Testing

### Postman Collection

```json
{
  "name": "User Activation/Deactivation",
  "requests": [
    {
      "name": "Deactivate User",
      "method": "PUT",
      "url": "{{api_base_url}}/users/{{user_id}}/deactivate",
      "headers": {
        "Authorization": "Bearer {{jwt_token}}"
      }
    },
    {
      "name": "Activate User", 
      "method": "PUT",
      "url": "{{api_base_url}}/users/{{user_id}}/activate",
      "headers": {
        "Authorization": "Bearer {{jwt_token}}"
      }
    }
  ]
}
```

### Test Script

```bash
# Test deactivation
curl -X PUT "http://localhost:8000/api/v1/users/user123/deactivate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Test activation
curl -X PUT "http://localhost:8000/api/v1/users/user123/activate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
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
  "detail": "Not authorized to update this user"
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
  "detail": "Failed to deactivate user"
}
```

## Summary

✅ **Fixed the endpoint methods and paths as requested:**
- Deactivate: `PUT /users/{user_id}/deactivate` (was `DELETE /users/{user_id}`)
- Activate: `PUT /users/{user_id}/activate` (was `POST /users/{user_id}/activate`)

✅ **Both endpoints now simply update the `is_active` field**

✅ **Proper authentication and authorization maintained**

✅ **Clean, consistent implementation across both user endpoint files**

The endpoints are now correctly implemented according to your specifications!