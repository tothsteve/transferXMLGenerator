#!/usr/bin/env python3
"""
Test script for the new wage tax summary PDF processing
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from bank_transfers.pdf_processor import PDFTransactionProcessor

def test_wage_tax_pdf():
    """Test the wage tax summary PDF processing"""
    pdf_path = "/Users/tothi/Downloads/Berosszesito_Medka_2025-07ho.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    # Read the PDF file
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Create uploaded file object
    uploaded_file = SimpleUploadedFile(
        name="Berosszesito_Medka_2025-07ho.pdf",
        content=pdf_content,
        content_type="application/pdf"
    )
    
    # Initialize processor
    processor = PDFTransactionProcessor()
    
    try:
        # Process the PDF
        print("Processing wage tax summary PDF...")
        result = processor.process_pdf_files([uploaded_file], "Test Wage Tax July 2025")
        
        print(f"\n✅ Processing successful!")
        print(f"Template: {result['template']['name']}")
        print(f"Transactions processed: {result['transactions_processed']}")
        print(f"Beneficiaries matched: {result['beneficiaries_matched']}")
        print(f"Beneficiaries created: {result['beneficiaries_created']}")
        print(f"Total amount: {result['total_amount']:,.0f} HUF")
        
        print(f"\n📋 Preview transactions:")
        for i, transaction in enumerate(result['preview'], 1):
            status = "Existing" if transaction['beneficiary_id'] else "New"
            print(f"{i}. {transaction['beneficiary_name']}")
            print(f"   Account: {transaction['account_number']}")
            print(f"   Amount: {transaction['amount']:,.0f} HUF")
            print(f"   Remittance: {transaction['remittance_info']}")
            print(f"   Status: {status}")
            print()
        
        if result['consolidations']:
            print(f"📄 Consolidations:")
            for msg in result['consolidations']:
                print(f"  • {msg}")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wage_tax_pdf()