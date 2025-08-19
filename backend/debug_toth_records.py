#!/usr/bin/env python3
"""
Debug Tóth István beneficiary consolidation issue
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.models import Beneficiary
from bank_transfers.pdf_processor import PDFTransactionProcessor

def debug_toth_records():
    """Debug Tóth István beneficiary matching and consolidation"""
    
    print("="*60)
    print("DEBUGGING TÓTH ISTVÁN RECORDS")
    print("="*60)
    
    # Check all Tóth beneficiaries in database
    toth_beneficiaries = Beneficiary.objects.filter(name__icontains='Tóth').order_by('name')
    print(f"\n📋 Found {toth_beneficiaries.count()} Tóth beneficiaries in database:")
    for b in toth_beneficiaries:
        print(f"  • ID {b.id}: {b.name}")
        print(f"    Account: {b.account_number}")
        print()
    
    # Test with sample Tóth István transactions (simulating PDF extract)
    processor = PDFTransactionProcessor()
    
    # Sample transactions that might come from PDF - using real account numbers
    test_transactions = [
        {
            'beneficiary_name': 'Tóth István',
            'account_number': '11600006-00000000-79306874',  # Your account ending in 116 (matches DB)
            'amount': 150000.0,
            'remittance_info': 'jövedelem',
            'execution_date': '2025-08-15'
        },
        {
            'beneficiary_name': 'Tóth István',
            'account_number': '11600006-00000000-79306874',  # Same account - should consolidate
            'amount': 50000.0,
            'remittance_info': 'bérleti díj',
            'execution_date': '2025-08-15'
        },
        {
            'beneficiary_name': 'Tóth István',
            'account_number': '12100011-11409520-00000000',  # Father's account (matches DB)
            'amount': 80000.0,
            'remittance_info': 'jövedelem',
            'execution_date': '2025-08-15'
        }
    ]
    
    print("🧪 Testing consolidation with sample transactions:")
    for i, trans in enumerate(test_transactions, 1):
        print(f"  {i}. {trans['beneficiary_name']}")
        print(f"     Account: {trans['account_number']}")
        print(f"     Amount: {trans['amount']:,.0f} HUF")
        print(f"     Remittance: {trans['remittance_info']}")
        print()
    
    # Test the consolidation logic
    consolidated, consolidation_msgs = processor.match_and_consolidate_beneficiaries(test_transactions)
    
    print("🔄 Consolidation results:")
    if consolidation_msgs:
        for msg in consolidation_msgs:
            print(f"   • {msg}")
    else:
        print("   • No consolidations performed")
    print()
    
    print("📊 Final consolidated transactions:")
    for i, trans in enumerate(consolidated, 1):
        print(f"  {i}. {trans['beneficiary_name']}")
        print(f"     Account: {trans['account_number']}")
        print(f"     Amount: {trans['amount']:,.0f} HUF")
        print(f"     Remittance: {trans['remittance_info']}")
        print(f"     Beneficiary ID: {trans['beneficiary_id']}")
        print(f"     Created new: {trans['created_beneficiary']}")
        print()
    
    # Test individual beneficiary matching
    print("🔍 Testing individual beneficiary matching:")
    for trans in test_transactions:
        matched = processor.find_matching_beneficiary(trans['account_number'], trans['beneficiary_name'])
        print(f"  Account {trans['account_number'][:8]}...")
        if matched:
            print(f"    ✅ Matched: {matched.name} (ID: {matched.id})")
            print(f"    DB Account: {matched.account_number}")
        else:
            print(f"    ❌ No match found")
        print()

if __name__ == "__main__":
    debug_toth_records()