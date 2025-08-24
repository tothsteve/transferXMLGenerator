#!/usr/bin/env python3
"""
Test script to try different batchIndex values for A/A28700200/1180/00013
"""

import os
import django
from datetime import datetime, timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.models import NavConfiguration, Company
from bank_transfers.services.nav_client import NavApiClient
import xml.etree.ElementTree as ET

def format_xml(xml_string):
    """Format XML string with proper indentation."""
    try:
        root = ET.fromstring(xml_string)
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding='unicode')
    except:
        return xml_string

def test_different_batch_indexes():
    """Test different batchIndex values for Shell invoice."""
    
    print("🔍 Testing Different BatchIndex Values for Shell Invoice")
    print("=" * 60)
    
    # Get the NavConfiguration
    company = Company.objects.get(name='IT Cardigan Kft.')
    nav_config = NavConfiguration.objects.filter(company=company, is_active=True).first()
    
    if not nav_config:
        print("❌ No active NAV configuration found")
        return
    
    # Initialize client
    client = NavApiClient(nav_config)
    
    # Create log files
    os.makedirs('nav_logs_batch', exist_ok=True)
    
    try:
        # Step 1: Get token
        print("1. Getting NAV token...")
        token = client.token_exchange()
        print(f"✅ Token received: {token[:20]}...")
        
        # Test Shell invoice with different batch indexes
        test_invoice = {
            'invoice_number': 'A/A28700200/1180/00013',
            'direction': 'INBOUND',
            'supplier_tax_number': '10891810'
        }
        
        print(f"\n2. Testing BatchIndex Values for: {test_invoice['invoice_number']}")
        print("-" * 50)
        
        # Try batch indexes 1-5
        for batch_index in range(1, 6):
            print(f"\n🔢 Testing BatchIndex: {batch_index}")
            
            # Create queryInvoiceData request with specific batch index
            detail_xml = client._create_query_invoice_data_xml(
                invoice_number=test_invoice['invoice_number'],
                direction=test_invoice['direction'],
                supplier_tax_number=test_invoice['supplier_tax_number'],
                batch_index=batch_index
            )
            
            # Log detail request
            with open(f'nav_logs_batch/detail_request_batch_{batch_index}.xml', 'w', encoding='utf-8') as f:
                f.write(format_xml(detail_xml))
            
            # Make detail request
            detail_url = f"{client.base_url}/queryInvoiceData"
            
            detail_response = client.session.post(
                detail_url,
                data=detail_xml,
                headers={
                    'Content-Type': 'application/xml',
                    'Accept': 'application/xml'
                }
            )
            
            print(f"   Status: {detail_response.status_code}, Length: {len(detail_response.text)} chars")
            
            # Log detail response
            with open(f'nav_logs_batch/detail_response_batch_{batch_index}.xml', 'w', encoding='utf-8') as f:
                f.write(format_xml(detail_response.text))
            
            # Check if this batch has data
            if detail_response.status_code == 200:
                # Look for invoiceDataResult in response
                if 'invoiceDataResult' in detail_response.text:
                    print(f"   🎉 FOUND DATA in batch {batch_index}!")
                    
                    # Try to parse detail response
                    try:
                        detail_data = client._parse_invoice_data_response(detail_response.text)
                        if detail_data:
                            print(f"   ✅ Parsed data: {list(detail_data.keys())}")
                        else:
                            print(f"   ⚠️  Data found but parsing returned None")
                    except Exception as e:
                        print(f"   ❌ Parse error: {e}")
                        
                elif 'invoiceData' in detail_response.text:
                    print(f"   🔍 Found invoiceData element in batch {batch_index}")
                else:
                    print(f"   ⚪ Empty response (standard NAV response structure)")
            else:
                print(f"   ❌ HTTP Error: {detail_response.status_code}")
        
        print(f"\n📁 Batch test logs saved to: nav_logs_batch/ directory")
        
        # Create summary
        with open('nav_logs_batch/summary.txt', 'w', encoding='utf-8') as f:
            f.write("NAV BatchIndex Test Summary\n")
            f.write("=" * 40 + "\n")
            f.write(f"Date tested: {datetime.now()}\n")
            f.write(f"Invoice tested: {test_invoice['invoice_number']}\n")
            f.write("Batch indexes tested: 1-5\n")
            f.write("\nCheck individual response files for detailed results.\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_different_batch_indexes()