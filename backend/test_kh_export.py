#!/usr/bin/env python3

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
sys.path.append('/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend')
django.setup()

from bank_transfers.models import BankAccount, Beneficiary, Transfer
from bank_transfers.kh_export import KHBankExporter

print("=== Testing KH Bank Export Functionality ===")

# Create test data if needed
try:
    # Get or create a bank account
    bank_account, created = BankAccount.objects.get_or_create(
        account_number="12100011-19014874-00000000",
        defaults={
            'name': 'Test Account',
            'is_default': True
        }
    )
    print(f"Bank account: {bank_account.name} ({'created' if created else 'found'})")
    
    # Get or create test beneficiaries
    beneficiary1, created = Beneficiary.objects.get_or_create(
        account_number="10032000-06055950",
        defaults={
            'name': 'NAV Személyi jövedelemadó',
            'is_active': True
        }
    )
    
    beneficiary2, created = Beneficiary.objects.get_or_create(
        account_number="66000169-11088406-00000000",
        defaults={
            'name': 'IT Cardigan Kft.',
            'is_active': True
        }
    )
    
    print(f"Test beneficiaries: {beneficiary1.name}, {beneficiary2.name}")
    
    # Create test transfers
    transfers = []
    
    transfer1 = Transfer.objects.create(
        originator_account=bank_account,
        beneficiary=beneficiary1,
        amount=Decimal('150000.00'),
        currency='HUF',
        execution_date=date.today(),
        remittance_info='Test transfer 1',
        order=1
    )
    transfers.append(transfer1)
    
    transfer2 = Transfer.objects.create(
        originator_account=bank_account,
        beneficiary=beneficiary2,
        amount=Decimal('61976.00'),
        currency='HUF',
        execution_date=date.today(),
        remittance_info='Invoice payment KI25/00842',
        order=2
    )
    transfers.append(transfer2)
    
    print(f"Created {len(transfers)} test transfers")
    
    # Test KH Bank export
    exporter = KHBankExporter()
    
    print("\n=== Testing KH Export Generation ===")
    kh_content = exporter.generate_kh_export(transfers)
    filename = exporter.get_filename("Test Batch")
    
    print(f"Generated filename: {filename}")
    print(f"Content length: {len(kh_content)} characters")
    
    print("\n=== KH Export Content ===")
    print(kh_content)
    
    print("\n=== Content Analysis ===")
    lines = kh_content.split('\n')
    print(f"Total lines: {len(lines)}")
    print(f"Header line: {lines[0]}")
    
    for i, line in enumerate(lines[1:], 1):
        if line.strip():
            fields = line.split(';')
            print(f"\nTransfer {i}:")
            print(f"  Source Account: {fields[0]}")
            print(f"  Partner Account: {fields[1]}")
            print(f"  Partner Name: {fields[2]}")
            print(f"  Amount: {fields[3]}")
            print(f"  Currency: {fields[4]}")
            print(f"  Remittance: {fields[5]}")
            print(f"  Unique ID: {fields[6]}")
            print(f"  Value Date: {fields[7]}")
    
    # Test validation
    print("\n=== Testing Validation ===")
    
    # Test with invalid currency
    try:
        invalid_transfer = Transfer.objects.create(
            originator_account=bank_account,
            beneficiary=beneficiary1,
            amount=Decimal('1000.00'),
            currency='EUR',  # Invalid for KH format
            execution_date=date.today(),
            remittance_info='Invalid currency test'
        )
        exporter.generate_kh_export([invalid_transfer])
        print("❌ Should have failed with EUR currency")
    except ValueError as e:
        print(f"✅ Correctly rejected EUR currency: {e}")
        invalid_transfer.delete()
    
    # Test with too many transfers
    try:
        many_transfers = transfers * 21  # 42 transfers (over limit of 40)
        exporter.generate_kh_export(many_transfers)
        print("❌ Should have failed with too many transfers")
    except ValueError as e:
        print(f"✅ Correctly rejected too many transfers: {e}")
    
    print("\n✅ KH Bank export test completed successfully!")
    
    # Clean up test data
    print("\n=== Cleaning up test data ===")
    for transfer in transfers:
        transfer.delete()
    print("Test transfers deleted")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()