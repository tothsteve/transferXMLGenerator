#!/usr/bin/env python3
"""
Show all XML request types we're making to NAV API
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

def show_all_xml_requests():
    """Show all types of XML requests we make to NAV."""
    
    print("📋 All NAV API XML Requests - Complete Overview")
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
    os.makedirs('nav_xml_requests', exist_ok=True)
    
    print("\n1️⃣ TOKEN EXCHANGE REQUEST")
    print("-" * 40)
    
    # Create token exchange request
    credentials = client._get_decrypted_credentials()
    request_id = client._generate_request_id()
    timestamp = client._generate_timestamp()
    
    token_request = {
        'header': {
            'requestId': request_id,
            'timestamp': timestamp,
            'requestVersion': '3.0',
            'headerVersion': '1.0'
        },
        'user': {
            'login': credentials['technical_user_login'],
            'passwordHash': client._hash_password(credentials['technical_user_password']),
            'taxNumber': credentials['tax_number'],
            'requestSignature': client._generate_request_signature({
                'requestId': request_id,
                'timestamp': timestamp
            })
        },
        'software': {
            'softwareId': '28778367-TXMLGEN01',
            'softwareName': 'Transfer XML Generator',
            'softwareOperation': 'LOCAL_SOFTWARE', 
            'softwareMainVersion': '1.0',
            'softwareDevName': 'IT Cardigan Kft.',
            'softwareDevContact': 'info@itcardigan.hu',
            'softwareDevTaxNumber': credentials['tax_number']
        }
    }
    
    token_xml = client._create_token_exchange_xml(token_request)
    with open('nav_xml_requests/1_token_exchange.xml', 'w', encoding='utf-8') as f:
        f.write(format_xml(token_xml.decode('utf-8')))
    
    print(f"📄 Endpoint: /tokenExchange")
    print(f"📝 File: nav_xml_requests/1_token_exchange.xml")
    print(format_xml(token_xml.decode('utf-8'))[:500] + "...")
    
    print("\n2️⃣ QUERY INVOICE DIGEST REQUEST (INBOUND)")
    print("-" * 40)
    
    digest_xml = client._create_query_invoice_digest_xml(
        direction='INBOUND',
        page=1,
        date_from_str='2025-08-14',
        date_to_str='2025-08-14'
    )
    
    with open('nav_xml_requests/2_query_invoice_digest_inbound.xml', 'w', encoding='utf-8') as f:
        f.write(format_xml(digest_xml))
    
    print(f"📄 Endpoint: /queryInvoiceDigest")
    print(f"📝 File: nav_xml_requests/2_query_invoice_digest_inbound.xml")
    print(format_xml(digest_xml)[:500] + "...")
    
    print("\n3️⃣ QUERY INVOICE DIGEST REQUEST (OUTBOUND)")
    print("-" * 40)
    
    digest_xml_out = client._create_query_invoice_digest_xml(
        direction='OUTBOUND',
        page=1,
        date_from_str='2025-08-14',
        date_to_str='2025-08-14'
    )
    
    with open('nav_xml_requests/3_query_invoice_digest_outbound.xml', 'w', encoding='utf-8') as f:
        f.write(format_xml(digest_xml_out))
    
    print(f"📄 Endpoint: /queryInvoiceDigest")
    print(f"📝 File: nav_xml_requests/3_query_invoice_digest_outbound.xml")
    print(format_xml(digest_xml_out)[:500] + "...")
    
    print("\n4️⃣ QUERY INVOICE CHAIN DIGEST REQUEST")
    print("-" * 40)
    
    chain_xml = client._create_query_invoice_chain_digest_xml(
        tax_number='10891810',
        invoice_number='A/A28700200/1180/00013',
        direction='INBOUND'
    )
    
    with open('nav_xml_requests/4_query_invoice_chain_digest.xml', 'w', encoding='utf-8') as f:
        f.write(format_xml(chain_xml))
    
    print(f"📄 Endpoint: /queryInvoiceChainDigest")
    print(f"📝 File: nav_xml_requests/4_query_invoice_chain_digest.xml")
    print(format_xml(chain_xml)[:500] + "...")
    
    print("\n5️⃣ QUERY INVOICE DATA REQUEST")
    print("-" * 40)
    
    data_xml = client._create_query_invoice_data_xml(
        invoice_number='A/A28700200/1180/00013',
        direction='INBOUND',
        supplier_tax_number='10891810',
        batch_index=1
    )
    
    with open('nav_xml_requests/5_query_invoice_data.xml', 'w', encoding='utf-8') as f:
        f.write(format_xml(data_xml))
    
    print(f"📄 Endpoint: /queryInvoiceData")
    print(f"📝 File: nav_xml_requests/5_query_invoice_data.xml")
    print(format_xml(data_xml)[:500] + "...")
    
    print("\n6️⃣ QUERY INVOICE DATA REQUEST (Different BatchIndex)")
    print("-" * 40)
    
    data_xml_batch2 = client._create_query_invoice_data_xml(
        invoice_number='A/A28700200/1180/00013',
        direction='INBOUND',
        supplier_tax_number='10891810',
        batch_index=2
    )
    
    with open('nav_xml_requests/6_query_invoice_data_batch2.xml', 'w', encoding='utf-8') as f:
        f.write(format_xml(data_xml_batch2))
    
    print(f"📄 Endpoint: /queryInvoiceData")
    print(f"📝 File: nav_xml_requests/6_query_invoice_data_batch2.xml")
    print(format_xml(data_xml_batch2)[:500] + "...")
    
    print("\n📁 All XML requests saved to: nav_xml_requests/ directory")
    
    # Create summary
    with open('nav_xml_requests/README.txt', 'w', encoding='utf-8') as f:
        f.write("NAV API XML Requests Overview\n")
        f.write("=" * 40 + "\n\n")
        f.write("1. tokenExchange - Get authentication token\n")
        f.write("2. queryInvoiceDigest (INBOUND) - Get invoice list for incoming invoices\n")
        f.write("3. queryInvoiceDigest (OUTBOUND) - Get invoice list for outgoing invoices\n")
        f.write("4. queryInvoiceChainDigest - Get chain metadata for specific invoice\n")
        f.write("5. queryInvoiceData - Get detailed invoice data (batch index 1)\n")
        f.write("6. queryInvoiceData - Get detailed invoice data (batch index 2)\n\n")
        f.write("All requests use NAV API v3.0 specification.\n")
        f.write("Authentication: SHA3-512 signatures with technical user credentials.\n")
        f.write("Environment: Production NAV API endpoint.\n")

if __name__ == "__main__":
    show_all_xml_requests()