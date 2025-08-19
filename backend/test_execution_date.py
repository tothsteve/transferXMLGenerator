#!/usr/bin/env python3

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
sys.path.append('/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend')
django.setup()

from bank_transfers.pdf_processor import PDFTransactionProcessor

# Test the execution date assignment
processor = PDFTransactionProcessor()

print("=== Testing get_default_payment_date ===")
default_date = processor.get_default_payment_date()
print(f"Default payment date: {default_date}")

# Today's date should be 2025-08-14
today = datetime.now().strftime('%Y-%m-%d')
print(f"Today's date: {today}")

if default_date == today:
    print("✓ get_default_payment_date() returns today's date correctly!")
else:
    print("✗ get_default_payment_date() is NOT returning today's date!")

# Test parsing a minimal text that looks like tax PDF but has no due date
print("\n=== Testing tax PDF without due date ===")
minimal_tax_text = """
Adó és járulék befizetések
NAV Személyi jövedelemadó 123 10032000-06055950 50000
"""

result = processor.parse_tax_pdf(minimal_tax_text)
print(f"Parsed result: {result}")

# Check if transactions use today's date
if result['transactions']:
    transaction = result['transactions'][0]
    execution_date = transaction['execution_date']
    print(f"Transaction execution date: {execution_date}")
    if execution_date == today:
        print("✓ Tax PDF without due date uses today's date correctly!")
    else:
        print(f"✗ Tax PDF without due date used {execution_date} instead of today ({today})!")
else:
    print("No transactions found in tax PDF")

print("\n=== Testing salary PDF without due date ===")
minimal_salary_text = """
Banki utalások
1. Tóth István 1234567890 12100011-11409520-00000000 150000
"""

result = processor.parse_salary_pdf(minimal_salary_text)
print(f"Parsed result: {result}")

# Check if transactions use today's date
if result['transactions']:
    transaction = result['transactions'][0]
    execution_date = transaction['execution_date']
    print(f"Transaction execution date: {execution_date}")
    if execution_date == today:
        print("✓ Salary PDF without due date uses today's date correctly!")
    else:
        print(f"✗ Salary PDF without due date used {execution_date} instead of today ({today})!")
else:
    print("No transactions found in salary PDF")