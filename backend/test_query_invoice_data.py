#!/usr/bin/env python3
"""
Test script to show the exact queryInvoiceData XML request being sent to NAV.
"""

import os
import django
from datetime import datetime, timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.models import NavConfiguration, Company
from bank_transfers.services.nav_client import NavApiClient

def show_query_invoice_data_xml():
    """Show the exact XML being sent for queryInvoiceData requests and NAV response."""
    
    print("🔍 NAV queryInvoiceData Request & Response")
    print("=" * 60)
    
    # Get the NavConfiguration
    company = Company.objects.get(name='IT Cardigan Kft.')
    nav_config = NavConfiguration.objects.filter(company=company, is_active=True).first()
    
    if not nav_config:
        print("❌ No active NAV configuration found")
        return
    
    # Initialize client
    client = NavApiClient(nav_config)
    
    # Test the first case: Yettel invoice that should have amounts
    test_case = {
        'invoice_number': '100334130700',
        'direction': 'INBOUND', 
        'supplier_tax_number': '11107792',
        'batch_index': 1
    }
    
    print(f"📄 Testing Invoice: {test_case['invoice_number']}")
    print("-" * 40)
    
    try:
        # First, get token
        print("1. Getting NAV token...")
        token = client.token_exchange()
        print(f"✅ Token received: {token[:20]}...")
        
        # Generate the XML request
        xml_request = client._create_query_invoice_data_xml(
            invoice_number=test_case['invoice_number'],
            direction=test_case['direction'],
            supplier_tax_number=test_case['supplier_tax_number'],
            batch_index=test_case['batch_index']
        )
        
        print("\n2. XML Request to be sent:")
        print(xml_request)
        
        # Make actual request to NAV
        print("\n3. Making request to NAV...")
        url = f"{client.base_url}/queryInvoiceData"
        print(f"URL: {url}")
        
        response = client.session.post(
            url,
            data=xml_request,
            headers={
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
        )
        
        print(f"\n4. NAV Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Response Length: {len(response.text)} characters")
        print("\n5. Response Body:")
        print("-" * 40)
        print(response.text)
        print("-" * 40)
        
        # Try to parse the response
        print("\n6. Parsed Response:")
        try:
            parsed_data = client._parse_invoice_data_response(response.text)
            if parsed_data:
                print(f"✅ Parsed data: {parsed_data}")
            else:
                print("⚠️  No parsed data (returned None)")
        except Exception as parse_error:
            print(f"❌ Parse error: {parse_error}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_query_invoice_data_xml()