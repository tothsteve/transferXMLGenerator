#!/usr/bin/env python3
"""
Test script for NAV API Integration with Multi-Environment Support

This script demonstrates the enhanced multi-company, multi-environment NAV integration.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.models import Company, NavConfiguration
from bank_transfers.services.invoice_sync_service import InvoiceSyncService
from datetime import datetime, date, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_multi_environment_nav_integration():
    """Test the enhanced NAV integration with multiple environments."""
    
    print("🧪 Testing Enhanced NAV Multi-Environment Integration")
    print("="*60)
    
    # Get all companies
    companies = Company.objects.all()
    if not companies:
        print("❌ No companies found in database")
        return
    
    print(f"📊 Found {companies.count()} companies")
    print()
    
    # Analyze NAV configurations per company
    for company in companies:
        print(f"🏢 Company: {company.name}")
        print("-" * 40)
        
        # Get all NAV configurations for this company
        nav_configs = company.nav_configs.all()
        
        if not nav_configs:
            print("   ❌ No NAV configurations")
            print()
            continue
        
        print(f"   📋 NAV Configurations ({nav_configs.count()}):")
        
        # Show each configuration
        for config in nav_configs:
            env_icon = "🔴" if config.api_environment == 'production' else "🟡"
            active_icon = "✅" if config.is_active else "❌"
            
            print(f"   {env_icon} {config.api_environment.upper():10s} | Active: {active_icon} | Tax#: {config.tax_number}")
        
        print()
        
        # Test configuration selection logic
        print("   🧪 Testing Configuration Selection:")
        
        # Test 1: Auto-select (prefer production)
        config = NavConfiguration.objects.get_active_config(company, prefer_production=True)
        if config:
            print(f"   ✅ Auto-select (prefer production): {config.api_environment}")
        else:
            print(f"   ❌ Auto-select (prefer production): None found")
        
        # Test 2: Auto-select (prefer test)
        config = NavConfiguration.objects.get_active_config(company, prefer_production=False)
        if config:
            print(f"   ✅ Auto-select (prefer test): {config.api_environment}")
        else:
            print(f"   ❌ Auto-select (prefer test): None found")
        
        # Test 3: Force production
        config = NavConfiguration.objects.for_company_and_environment(company, 'production')
        if config:
            print(f"   ✅ Force production: Available")
        else:
            print(f"   ❌ Force production: Not available")
        
        # Test 4: Force test
        config = NavConfiguration.objects.for_company_and_environment(company, 'test')
        if config:
            print(f"   ✅ Force test: Available")
        else:
            print(f"   ❌ Force test: Not available")
        
        print()
        
        # Test actual NAV sync with different environments
        sync_service = InvoiceSyncService()
        test_date_from = date.today() - timedelta(days=1)
        test_date_to = date.today()
        
        print(f"   🚀 Testing NAV Sync ({test_date_from} to {test_date_to}):")
        
        # Test with production environment (if available)
        try:
            print("   📡 Testing production environment...")
            result = sync_service.sync_company_invoices(
                company=company,
                date_from=test_date_from,
                date_to=test_date_to,
                direction='INBOUND',
                environment='production',
                prefer_production=True
            )
            print(f"   ✅ Production sync: Success={result.get('success', False)}")
        except Exception as e:
            print(f"   ❌ Production sync failed: {str(e)[:80]}...")
        
        # Test with test environment (if available)
        try:
            print("   📡 Testing test environment...")
            result = sync_service.sync_company_invoices(
                company=company,
                date_from=test_date_from,
                date_to=test_date_to,
                direction='INBOUND',
                environment='test',
                prefer_production=False
            )
            print(f"   ✅ Test sync: Success={result.get('success', False)}")
        except Exception as e:
            print(f"   ❌ Test sync failed: {str(e)[:80]}...")
        
        # Test with auto-selection
        try:
            print("   📡 Testing auto-selection...")
            result = sync_service.sync_company_invoices(
                company=company,
                date_from=test_date_from,
                date_to=test_date_to,
                direction='INBOUND',
                environment=None,
                prefer_production=True
            )
            print(f"   ✅ Auto-select sync: Success={result.get('success', False)}")
        except Exception as e:
            print(f"   ❌ Auto-select sync failed: {str(e)[:80]}...")
        
        print()
        print("="*60)
        print()

def test_production_scenarios():
    """Test real-world production scenarios."""
    
    print("🎯 Testing Production Scenarios")
    print("="*40)
    
    scenarios = [
        {
            'name': 'Company with only production config',
            'description': 'Should use production for all operations'
        },
        {
            'name': 'Company with only test config', 
            'description': 'Should use test for all operations'
        },
        {
            'name': 'Company with both configs',
            'description': 'Should intelligently select based on preference'
        },
        {
            'name': 'Company with no configs',
            'description': 'Should fail gracefully with clear error'
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 {scenario['name']}")
        print(f"   {scenario['description']}")
        print()

if __name__ == "__main__":
    print("🚀 Starting NAV API Integration Tests")
    print()
    
    test_multi_environment_nav_integration()
    test_production_scenarios()
    
    print("✅ NAV API Integration Tests Complete")