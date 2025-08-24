#!/usr/bin/env python3
"""
Test script for the new sophisticated NAV flow with invoice chain digest.
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

def test_advanced_nav_flow():
    """Test the new advanced NAV flow: digest -> chain -> data"""
    
    print("🚀 Advanced NAV Flow Test - Chain Query First")
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
    os.makedirs('nav_logs_advanced', exist_ok=True)
    
    try:
        # Step 1: Get token
        print("1. Getting NAV token...")
        token = client.token_exchange()
        print(f"✅ Token received: {token[:20]}...")
        
        # Test with Shell invoice from our previous test
        test_invoice = {
            'invoice_number': 'A/A28700200/1180/00013',
            'direction': 'INBOUND',
            'supplier_tax_number': '10891810'
        }
        
        print(f"\n2. Testing Advanced Flow for: {test_invoice['invoice_number']}")
        print("-" * 50)
        
        # Step 2: Query invoice chain digest FIRST
        print(f"Step 2a: Querying invoice chain digest...")
        
        chain_xml = client._create_query_invoice_chain_digest_xml(
            tax_number=test_invoice['supplier_tax_number'],
            invoice_number=test_invoice['invoice_number'],
            direction=test_invoice['direction']
        )
        
        # Log chain request
        with open('nav_logs_advanced/chain_request.xml', 'w', encoding='utf-8') as f:
            f.write(format_xml(chain_xml))
        print(f"📝 Chain request saved to: nav_logs_advanced/chain_request.xml")
        
        # Make chain request
        url = f"{client.base_url}/queryInvoiceChainDigest"
        
        response = client.session.post(
            url,
            data=chain_xml,
            headers={
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
        )
        
        print(f"Chain Status: {response.status_code}, Length: {len(response.text)} chars")
        
        # Log chain response
        with open('nav_logs_advanced/chain_response.xml', 'w', encoding='utf-8') as f:
            f.write(format_xml(response.text))
        print(f"📝 Chain response saved to: nav_logs_advanced/chain_response.xml")
        
        # Parse chain response
        try:
            chain_data = client._parse_invoice_chain_digest_response(response.text)
            print(f"✅ Chain elements found: {len(chain_data.get('chainElements', []))}")
            
            # Extract metadata
            version = None
            operation = None
            transaction_id = None
            
            for element in chain_data.get('chainElements', []):
                if element.get('invoiceNumber') == test_invoice['invoice_number']:
                    version = element.get('originalRequestVersion')
                    operation = element.get('invoiceOperation') 
                    transaction_id = element.get('transactionId')
                    print(f"📊 Metadata: version={version}, operation={operation}, transactionId={transaction_id}")
                    break
                    
        except Exception as e:
            print(f"❌ Chain parse error: {e}")
            chain_data = None
            version = operation = transaction_id = None
        
        # Step 3: Query detailed data with metadata
        print(f"\nStep 2b: Querying detailed invoice data with chain metadata...")
        
        detail_xml = client._create_query_invoice_data_xml(
            invoice_number=test_invoice['invoice_number'],
            direction=test_invoice['direction'],
            supplier_tax_number=test_invoice['supplier_tax_number'],
            batch_index=1
        )
        
        # Log detail request
        with open('nav_logs_advanced/detail_request.xml', 'w', encoding='utf-8') as f:
            f.write(format_xml(detail_xml))
        
        # Make detail request
        print(f"Making detailed data request...")
        detail_url = f"{client.base_url}/queryInvoiceData"
        
        detail_response = client.session.post(
            detail_url,
            data=detail_xml,
            headers={
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
        )
        
        print(f"Detail Status: {detail_response.status_code}, Length: {len(detail_response.text)} chars")
        
        # Log detail response
        with open('nav_logs_advanced/detail_response.xml', 'w', encoding='utf-8') as f:
            f.write(format_xml(detail_response.text))
        
        # Try to parse detail response
        try:
            detail_data = client._parse_invoice_data_response(detail_response.text)
            if detail_data:
                print(f"✅ Detail data received: {list(detail_data.keys())}")
            else:
                print(f"⚠️  Still no detail data returned")
        except Exception as e:
            print(f"❌ Detail parse error: {e}")
        
        print(f"\n📁 Advanced flow logs saved to: nav_logs_advanced/ directory")
        
        # Create summary
        with open('nav_logs_advanced/summary.txt', 'w', encoding='utf-8') as f:
            f.write("Advanced NAV Flow Test Summary\n")
            f.write("=" * 40 + "\n")
            f.write(f"Date tested: {datetime.now()}\n")
            f.write(f"Invoice tested: {test_invoice['invoice_number']}\n")
            f.write(f"Chain status: {response.status_code}\n")
            f.write(f"Detail status: {detail_response.status_code}\n")
            f.write(f"Chain elements: {len(chain_data.get('chainElements', [])) if chain_data else 0}\n")
            f.write(f"Metadata found: version={version}, operation={operation}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_advanced_nav_flow()