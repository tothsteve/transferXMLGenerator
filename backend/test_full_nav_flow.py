#!/usr/bin/env python3
"""
Test script to query invoices for 2025-08-14 and then call queryInvoiceData for each,
logging all requests and responses to files.
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

def test_full_nav_flow():
    """Test full NAV flow: queryInvoiceDigest -> queryInvoiceData for each invoice."""
    
    print("🔍 Full NAV Invoice Query Flow Test - 2025-08-14")
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
    os.makedirs('nav_logs', exist_ok=True)
    
    try:
        # Step 1: Get token
        print("1. Getting NAV token...")
        token = client.token_exchange()
        print(f"✅ Token received: {token[:20]}...")
        
        # Step 2: Query invoice digest for 2025-08-14
        print("\n2. Querying invoice digest for 2025-08-14...")
        
        # Test both INBOUND and OUTBOUND
        directions = ['INBOUND', 'OUTBOUND']
        
        for direction in directions:
            print(f"\n--- Testing {direction} invoices ---")
            
            # Create the digest query XML
            digest_xml = client._create_query_invoice_digest_xml(
                direction=direction,
                page=1,
                date_from_str='2025-08-14',
                date_to_str='2025-08-14'
            )
            
            # Log digest request
            with open(f'nav_logs/digest_request_{direction}.xml', 'w', encoding='utf-8') as f:
                f.write(format_xml(digest_xml))
            print(f"📝 Digest request saved to: nav_logs/digest_request_{direction}.xml")
            
            # Make digest request
            print(f"Making digest request to NAV...")
            url = f"{client.base_url}/queryInvoiceDigest"
            
            response = client.session.post(
                url,
                data=digest_xml,
                headers={
                    'Content-Type': 'application/xml',
                    'Accept': 'application/xml'
                }
            )
            
            print(f"Status: {response.status_code}, Length: {len(response.text)} chars")
            
            # Log digest response
            with open(f'nav_logs/digest_response_{direction}.xml', 'w', encoding='utf-8') as f:
                f.write(format_xml(response.text))
            print(f"📝 Digest response saved to: nav_logs/digest_response_{direction}.xml")
            
            # Parse digest response
            invoices = client._parse_invoice_digest_response(response.text)
            print(f"Found {len(invoices)} {direction} invoices")
            
            # Step 3: Query detailed data for each invoice
            for i, invoice in enumerate(invoices, 1):
                invoice_number = invoice.get('invoiceNumber')
                supplier_tax = invoice.get('supplierTaxNumber')
                batch_index = invoice.get('batchIndex', 1)
                
                print(f"\n  {i}. Invoice: {invoice_number}")
                print(f"     Supplier: {invoice.get('supplierName', 'N/A')}")
                print(f"     Tax Number: {supplier_tax}")
                print(f"     Net Amount: {invoice.get('invoiceNetAmount', 'N/A')}")
                print(f"     VAT Amount: {invoice.get('invoiceVatAmount', 'N/A')}")
                
                # Create queryInvoiceData request
                detail_xml = client._create_query_invoice_data_xml(
                    invoice_number=invoice_number,
                    direction=direction,
                    supplier_tax_number=supplier_tax,
                    batch_index=batch_index
                )
                
                # Log detail request
                safe_name = invoice_number.replace('/', '_').replace('\\', '_')
                with open(f'nav_logs/detail_request_{direction}_{safe_name}.xml', 'w', encoding='utf-8') as f:
                    f.write(format_xml(detail_xml))
                
                # Make detail request
                print(f"     Querying detailed data...")
                detail_url = f"{client.base_url}/queryInvoiceData"
                
                detail_response = client.session.post(
                    detail_url,
                    data=detail_xml,
                    headers={
                        'Content-Type': 'application/xml',
                        'Accept': 'application/xml'
                    }
                )
                
                print(f"     Detail Status: {detail_response.status_code}, Length: {len(detail_response.text)} chars")
                
                # Log detail response
                with open(f'nav_logs/detail_response_{direction}_{safe_name}.xml', 'w', encoding='utf-8') as f:
                    f.write(format_xml(detail_response.text))
                
                # Try to parse detail response
                try:
                    detail_data = client._parse_invoice_data_response(detail_response.text)
                    if detail_data:
                        print(f"     ✅ Detail data received: {list(detail_data.keys())}")
                    else:
                        print(f"     ⚠️  No detail data returned")
                except Exception as e:
                    print(f"     ❌ Detail parse error: {e}")
        
        print(f"\n📁 All logs saved to: nav_logs/ directory")
        print(f"📊 Summary log:")
        
        # Create summary log
        with open('nav_logs/summary.txt', 'w', encoding='utf-8') as f:
            f.write("NAV Invoice Query Test Summary\n")
            f.write("=" * 40 + "\n")
            f.write(f"Date tested: {datetime.now()}\n")
            f.write(f"Target date: 2025-08-14\n")
            f.write(f"NAV Environment: {nav_config.api_environment}\n")
            f.write(f"Base URL: {client.base_url}\n")
            f.write(f"Technical User: {nav_config.technical_user_login}\n")
            f.write(f"Tax Number: {nav_config.tax_number}\n")
            f.write("\nFiles created:\n")
            
            for file in os.listdir('nav_logs'):
                if file.endswith('.xml') or file.endswith('.txt'):
                    f.write(f"- {file}\n")
        
        print("📝 Summary saved to: nav_logs/summary.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Log error
        with open('nav_logs/error.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error occurred: {e}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    test_full_nav_flow()