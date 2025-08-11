#!/usr/bin/env python3
"""
Test script to verify table endpoint configuration
"""
import requests
import json
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_table_endpoint():
    """Test the table endpoint for 307 redirect issues"""
    
    base_url = "https://dino-backend-api-867506203789.us-central1.run.app"
    
    # Test different URL variations
    test_urls = [
        f"{base_url}/api/v1/tables",      # Without trailing slash
        f"{base_url}/api/v1/tables/",     # With trailing slash
    ]
    
    test_data = {
        "venue_id": "test-venue-id",
        "table_number": 1,
        "capacity": 4,
        "location": "Main dining area"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"  # This will fail auth but should not cause 307
    }
    
    for url in test_urls:
        print(f"\n🧪 Testing: {url}")
        try:
            response = requests.post(
                url, 
                json=test_data, 
                headers=headers,
                allow_redirects=False,  # Don't follow redirects
                verify=False  # Skip SSL verification for testing
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 307:
                print(f"❌ 307 Redirect detected!")
                print(f"Location: {response.headers.get('location', 'Not provided')}")
            elif response.status_code == 401:
                print(f"✅ Expected 401 (auth required) - endpoint working correctly")
            elif response.status_code == 422:
                print(f"✅ Expected 422 (validation error) - endpoint working correctly")
            else:
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_table_endpoint()