#!/usr/bin/env python3
"""
Debug script to test the middleware logic with the actual user data
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from django.contrib.auth.models import User
from bank_transfers.models import Company, CompanyUser, UserProfile

def debug_middleware_logic():
    """Test the middleware logic with the tothi user"""
    
    try:
        user = User.objects.get(username='tothi')
        print(f"✅ User found: {user.username} (ID: {user.id})")
        print(f"   Authenticated: {user.is_authenticated}")
        
        # Simulate the middleware logic
        company_id = 4  # X-Company-ID header value
        print(f"\n🔍 Testing middleware logic with X-Company-ID: {company_id}")
        
        # Step 1: Convert to int
        try:
            company_id = int(company_id)
            print(f"✅ Company ID converted to int: {company_id}")
        except (ValueError, TypeError) as e:
            print(f"❌ Company ID conversion failed: {e}")
            return
        
        # Step 2: Check CompanyUser membership
        print(f"\n🔍 Looking for CompanyUser membership...")
        membership = CompanyUser.objects.filter(
            user=user,
            company_id=company_id,
            is_active=True
        ).select_related('company').first()
        
        if membership:
            print(f"✅ Membership found:")
            print(f"   Company: {membership.company.name} (ID: {membership.company.id})")
            print(f"   Role: {membership.role}")
            print(f"   Active: {membership.is_active}")
            # print(f"   Created: {membership.created_at}")  # Field might not exist
            
            # Step 3: Check UserProfile update
            print(f"\n🔍 Checking UserProfile...")
            profile, created = UserProfile.objects.get_or_create(user=user)
            print(f"Profile exists: {not created}")
            print(f"Current last_active_company: {profile.last_active_company}")
            
            if profile.last_active_company != membership.company:
                print(f"⚠️  Would update last_active_company from {profile.last_active_company} to {membership.company}")
            else:
                print(f"✅ last_active_company already correct")
                
            print(f"\n🎉 Middleware should succeed and set request.company = {membership.company}")
            
        else:
            print(f"❌ No membership found!")
            print(f"   This would return 403 Forbidden: 'Nincs jogosultság ehhez a céghez'")
            
            # Debug: Show all memberships for this user
            all_memberships = CompanyUser.objects.filter(user=user)
            print(f"\n📋 All memberships for user {user.username}:")
            for m in all_memberships:
                print(f"   - Company: {m.company.name} (ID: {m.company.id}) - Active: {m.is_active}")
                
    except User.DoesNotExist:
        print("❌ User 'tothi' not found")

if __name__ == "__main__":
    debug_middleware_logic()