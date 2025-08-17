#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
sys.path.append('/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend')
django.setup()

from bank_transfers.pdf_processor import PDFTransactionProcessor
import pdfplumber

# Test the invoice parsing with the actual PDF
pdf_path = "/Users/tothi/Library/CloudStorage/Dropbox/ITCardigan/2025/Bejövő/20250703_KI2500842_ITCardiganKft.pdf"

processor = PDFTransactionProcessor()

print("=== Testing Invoice Parsing ===")

# Extract raw text first
try:
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    print("\n=== RAW TEXT ===")
    print(text[:1000] + "..." if len(text) > 1000 else text)
    
    print("\n=== TESTING INVOICE DETECTION ===")
    is_invoice = processor.is_invoice_pdf(text)
    print(f"Is invoice: {is_invoice}")
    
    print("\n=== TESTING INVOICE INFO EXTRACTION ===")
    invoice_info = processor.extract_invoice_info(text)
    print(f"Invoice info: {invoice_info}")
    
    print("\n=== TESTING PAYMENT DETAILS EXTRACTION ===")
    payment_info = processor.extract_invoice_payment_details(text)
    print(f"Payment info: {payment_info}")
    
    print("\n=== TESTING FULL INVOICE PARSING ===")
    result = processor.parse_invoice_pdf(text)
    print(f"Full result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()