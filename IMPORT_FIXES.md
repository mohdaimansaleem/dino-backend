# Import Fixes Applied

## Issue
The application was failing to start with the error:
```
ImportError: cannot import name 'VenueHours' from 'app.models.schemas'
```

## Root Cause
Multiple missing or incorrectly named schema imports across the application.

## Fixes Applied

### 1. Fixed VenueHours Import in venue.py
**File:** `app/api/v1/endpoints/venue.py`
**Issue:** Importing `VenueHours` which doesn't exist
**Fix:** Changed to `VenueOperatingHours` (the actual class name)

```python
# Before
from app.models.schemas import (
    VenueCreate, VenueUpdate, Venue, ApiResponse, PaginatedResponse,
    VenueHours, SubscriptionPlan, SubscriptionStatus
)

# After  
from app.models.schemas import (
    VenueCreate, VenueUpdate, Venue, ApiResponse, PaginatedResponse,
    VenueOperatingHours, SubscriptionPlan, SubscriptionStatus
)
```

### 2. Fixed VenueRepository Import in venue.py
**File:** `app/api/v1/endpoints/venue.py`