#!/usr/bin/env python3
"""
Debug beneficiary matching with NAV accounts
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.models import Beneficiary
from bank_transfers.pdf_processor import PDFTransactionProcessor

def debug_nav_matching():
    """Debug NAV beneficiary matching"""
    
    print("="*60)
    print("DEBUGGING NAV BENEFICIARY MATCHING")
    print("="*60)
    
    # Show all NAV beneficiaries in database
    nav_beneficiaries = Beneficiary.objects.filter(name__icontains='NAV').order_by('name')
    print(f"\n📋 Found {nav_beneficiaries.count()} NAV beneficiaries in database:")
    for b in nav_beneficiaries:
        print(f"  • ID {b.id}: {b.name}")
        print(f"    Account: {b.account_number}")
        print()
    
    # Test the PDF extracted transactions
    test_accounts = [
        ('10032000-06057763', 'NAV Egyszerűsített foglalkoztatásból eredő szociális hozzájárulási adó beszedési számla'),
        ('10032000-06055912', 'NAV Szociális hozzájárulási adó beszedési számla'), 
        ('10032000-06055950', 'NAV Személyi jövedelemadó magánszemélyektől levont adó, adóelőleg beszedési számla'),
        ('10032000-06055819', 'NAV Biztosítottaktól levont társadalombiztosítási járulék beszedési számla')
    ]
    
    processor = PDFTransactionProcessor()
    
    print("🔍 Testing beneficiary matching:")
    for account, pdf_name in test_accounts:
        print(f"\n--- Testing: {pdf_name[:50]}...")
        print(f"PDF Account: {account}")
        
        # Test the matching function
        matched = processor.find_matching_beneficiary(account, pdf_name)
        
        if matched:
            print(f"✅ MATCHED: {matched.name} (ID: {matched.id})")
            print(f"   DB Account: {matched.account_number}")
            
            # Test the account cleaning and matching logic
            clean_pdf = account.replace('-', '').replace(' ', '')
            clean_db = matched.account_number.replace('-', '').replace(' ', '')
            print(f"   Clean PDF: {clean_pdf}")
            print(f"   Clean DB:  {clean_db}")
            print(f"   Match: {'✅' if clean_pdf == clean_db else '❌'}")
        else:
            print(f"❌ NOT MATCHED")
            
            # Try manual search
            clean_account = account.replace('-', '')
            possible_matches = Beneficiary.objects.filter(
                account_number__icontains=clean_account[:8]
            )
            print(f"   Possible matches with {clean_account[:8]}:")
            for m in possible_matches:
                print(f"     • {m.name} ({m.account_number})")

if __name__ == "__main__":
    debug_nav_matching()