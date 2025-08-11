#!/usr/bin/env python3
"""
Check if the users endpoint is properly registered
"""

def check_endpoint_registration():
    """Check if the users endpoint is registered in the FastAPI app"""
    try:
        from app.main import app
        
        print("🔍 Checking endpoint registration...")
        print("=" * 50)
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if route.methods else [],
                    'name': getattr(route, 'name', 'unnamed')
                })
        
        # Filter for users endpoints
        users_routes = [r for r in routes if '/users' in r['path']]
        
        print(f"📊 Total routes found: {len(routes)}")
        print(f"👥 Users routes found: {len(users_routes)}")
        
        if users_routes:
            print("\n✅ Users endpoints found:")
            for route in users_routes:
                methods_str = ', '.join(route['methods'])
                print(f"   {methods_str:15} {route['path']}")
        else:
            print("\n❌ No users endpoints found!")
            
        # Check specifically for GET /users
        get_users_route = None
        for route in users_routes:
            if route['path'] == '/api/v1/users' and 'GET' in route['methods']:
                get_users_route = route
                break
        
        if get_users_route:
            print(f"\n✅ GET /api/v1/users endpoint is registered!")
            return True
        else:
            print(f"\n❌ GET /api/v1/users endpoint is NOT registered!")
            
            # Show what we do have
            print("\n🔍 Available users endpoints:")
            for route in users_routes:
                if 'GET' in route['methods']:
                    print(f"   GET {route['path']}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error checking registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_router_import():
    """Check if the user router can be imported"""
    try:
        print("\n🔍 Checking router import...")
        from app.api.v1.endpoints.user import router
        
        # Check routes in the router
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if route.methods else [],
                    'name': getattr(route, 'name', 'unnamed')
                })
        
        print(f"📊 Routes in user router: {len(routes)}")
        
        # Look for the GET / route
        get_root_route = None
        for route in routes:
            if route['path'] == '/' and 'GET' in route['methods']:
                get_root_route = route
                break
        
        if get_root_route:
            print("✅ GET / route found in user router")
            return True
        else:
            print("❌ GET / route NOT found in user router")
            print("Available routes:")
            for route in routes:
                methods_str = ', '.join(route['methods'])
                print(f"   {methods_str:15} {route['path']}")
            return False
            
    except Exception as e:
        print(f"❌ Error importing user router: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 ENDPOINT REGISTRATION CHECK")
    print("=" * 60)
    
    # Check 1: Router import
    router_ok = check_router_import()
    
    # Check 2: App registration
    app_ok = check_endpoint_registration()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if router_ok and app_ok:
        print("✅ Everything looks good! The endpoint should work.")
        print("\n💡 If you're still getting 404, try:")
        print("1. Restart the server")
        print("2. Check if you're using the correct URL")
        print("3. Check server logs for errors")
    elif router_ok and not app_ok:
        print("⚠️  Router is OK but not registered in main app")
        print("Check app/main.py and app/api/v1/api.py")
    elif not router_ok:
        print("❌ Issue with the user router itself")
        print("Check app/api/v1/endpoints/user.py for syntax errors")
    
    return router_ok and app_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)