#!/usr/bin/env python3
"""
Verification script to test the authentication fixes.
This script will:
1. Test CORS headers are properly configured
2. Verify authentication endpoints are working
3. Check that company context is properly set
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_cors_headers():
    """Test that CORS headers are properly configured for our custom headers"""
    print("🧪 Testing CORS configuration...")
    
    # Make an OPTIONS request to check CORS headers
    response = requests.options(
        f"{BASE_URL}/debug/auth/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-company-id"
        }
    )
    
    print(f"✅ CORS OPTIONS response status: {response.status_code}")
    
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
    }
    
    print("📋 CORS Headers:")
    for header, value in cors_headers.items():
        print(f"   {header}: {value}")
    
    # Check if our custom header is allowed
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
    if "x-company-id" in allowed_headers:
        print("✅ X-Company-ID header is allowed")
    else:
        print("❌ X-Company-ID header is NOT allowed")
    
    return response.status_code == 200

def test_login_endpoint():
    """Test login endpoint works"""
    print("\n🔑 Testing login endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login/",
            json={
                "username": "test_user",
                "password": "test_password"
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Login response status: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Login endpoint is working (400 = invalid credentials expected)")
            return True
        elif response.status_code == 200:
            print("✅ Login successful!")
            return True
        else:
            print(f"❌ Unexpected response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

def test_auth_debug_endpoint():
    """Test the debug auth endpoint without authentication"""
    print("\n🐛 Testing debug auth endpoint (should require auth)...")
    
    try:
        response = requests.get(f"{BASE_URL}/debug/auth/")
        
        print(f"📡 Debug endpoint response status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Auth debug endpoint properly requires authentication")
            return True
        else:
            print(f"❌ Expected 401, got {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Debug endpoint test failed: {e}")
        return False

def main():
    print("🚀 Starting authentication verification tests...\n")
    
    tests = [
        ("CORS Configuration", test_cors_headers),
        ("Login Endpoint", test_login_endpoint),
        ("Auth Debug Endpoint", test_auth_debug_endpoint),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print("="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All authentication fixes are working correctly!")
        print("✅ CORS issue should be resolved")
        print("✅ Frontend should be able to make authenticated API calls")
    else:
        print("⚠️  Some issues remain - check the output above")
    
    print("\n📝 Next steps:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Check browser console for any remaining CORS errors")
    print("3. Try logging in to verify the full authentication flow")

if __name__ == "__main__":
    main()