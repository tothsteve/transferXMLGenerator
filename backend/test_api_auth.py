#!/usr/bin/env python3
"""
Test API authentication by making actual API calls
"""

import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def get_auth_token(username):
    """Get JWT token for a user"""
    try:
        user = User.objects.get(username=username)
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    except User.DoesNotExist:
        print(f"User {username} not found")
        return None

def test_api_call():
    """Test authenticated API call"""
    
    # Get token for tothi user
    token = get_auth_token('tothi')
    if not token:
        return
    
    print(f"🔑 Got JWT token for user 'tothi': {token[:20]}...")
    print(f"Full token: {token}")
    
    # Test API call to beneficiaries endpoint
    url = "http://localhost:8000/api/beneficiaries/"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": "4",
        "Content-Type": "application/json"
    }
    
    print(f"\n📡 Making API call to: {url}")
    print(f"Headers:")
    for key, value in headers.items():
        if key == "Authorization":
            print(f"  {key}: Bearer {value[:20]}...")
        else:
            print(f"  {key}: {value}")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"\n📊 Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ Success! Response: {response.json()}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_debug_endpoint():
    """Test the debug auth endpoint"""
    
    # Get token for tothi user
    token = get_auth_token('tothi')
    if not token:
        return
    
    print(f"\n🐛 Testing debug auth endpoint...")
    
    # Test API call to debug endpoint
    url = "http://localhost:8000/api/debug/auth/"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": "4",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug info:")
            print(f"  User: {data.get('user', {}).get('username')} (authenticated: {data.get('user', {}).get('is_authenticated')})")
            company = data.get('company')
            if company:
                print(f"  Company: {company.get('name')} (ID: {company.get('id')})")
            else:
                print(f"  Company: None")
        else:
            print(f"❌ Debug endpoint error: {response.text}")
            
    except Exception as e:
        print(f"❌ Debug request failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing API authentication...")
    test_debug_endpoint()
    test_api_call()