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
import pdfplumber

# Test the MEDKA PDF
pdf_path = "/Users/tothi/Downloads/Berosszesito_Medka_2025-07ho.pdf"

processor = PDFTransactionProcessor()

print("=== Testing MEDKA PDF Processing ===")

# Extract raw text first
try:
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    print("=== PDF TEXT SAMPLE ===")
    print(text[:500] + "..." if len(text) > 500 else text)
    
    print("\n=== TESTING PDF DETECTION ===")
    # Check what type is detected
    if "Adó és járulék befizetések" in text:
        pdf_type = "TAX"
        result = processor.parse_tax_pdf(text)
    elif "Bérösszesítő" in text or "Megnevezés" in text and "Bankszámlaszám" in text and "Összeg" in text:
        pdf_type = "WAGE_TAX_SUMMARY"
        result = processor.parse_wage_tax_summary_pdf(text)
    elif "Banki utalások" in text or "utalások" in text.lower():
        pdf_type = "SALARY"
        result = processor.parse_salary_pdf(text)
    else:
        pdf_type = "UNKNOWN"
        result = None
    
    print(f"Detected PDF type: {pdf_type}")
    
    if result:
        print(f"Due date found in PDF: {result.get('due_date')}")
        print(f"Number of transactions: {len(result.get('transactions', []))}")
        
        for i, transaction in enumerate(result.get('transactions', [])[:3]):  # Show first 3
            print(f"Transaction {i+1}:")
            print(f"  - Beneficiary: {transaction.get('beneficiary_name')}")
            print(f"  - Account: {transaction.get('account_number')}")
            print(f"  - Amount: {transaction.get('amount')}")
            print(f"  - Execution Date: {transaction.get('execution_date')}")
        
        # Check if today's date is being used
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\nToday's date: {today}")
        
        # Check if any transaction uses today's date
        using_today = any(t.get('execution_date') == today for t in result.get('transactions', []))
        print(f"Any transaction using today's date: {using_today}")
        
        if not using_today and result.get('transactions'):
            execution_dates = [t.get('execution_date') for t in result.get('transactions', [])]
            unique_dates = list(set(execution_dates))
            print(f"Execution dates being used: {unique_dates}")
    else:
        print("Failed to parse PDF")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()