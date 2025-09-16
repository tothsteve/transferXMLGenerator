#!/usr/bin/env python
"""
End-to-end test for VAT-based PDF processing
"""
import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.pdf_processor import PDFTransactionProcessor
from bank_transfers.models import Company, Beneficiary

def test_vat_pdf_processing():
    """Test complete VAT-based PDF processing workflow"""
    print("=== VAT PDF PROCESSING END-TO-END TEST ===\n")
    
    # Get first existing company or create one with unique tax ID
    import uuid
    company = Company.objects.first()
    if not company:
        unique_tax_id = f"99999999-1-{str(uuid.uuid4())[:2]}"
        company = Company.objects.create(
            name="Test Company for VAT",
            tax_id=unique_tax_id,
            is_active=True
        )
        created = True
    else:
        created = False
    print(f"Using test company: {company.name} (Created: {created})")
    
    # Initialize processor
    processor = PDFTransactionProcessor()
    
    # Test both PDFs
    pdf_files = [
        '/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/temp/Berjegyzek_Medka_2025-07ho.pdf',
        '/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/temp/08 bérlapok.pdf'
    ]
    
    expected_results = {
        'Berjegyzek_Medka_2025-07ho.pdf': {
            'company_tax_id': '32560682-2-43',
            'employees': [
                ('Fekete Dávid', '8450782546', 1095986),
                ('Kövesi Dániel', '8422463822', 1330000)  # Kövesi András skipped (0 amount)
            ]
        },
        '08 bérlapok.pdf': {
            'company_tax_id': '26753502-2-13', 
            'employees': [
                ('Cserháti Tamás', '8413562422', 267917),
                ('Galgóczi Ferenc Attila', '8329552896', 1500000)
            ]
        }
    }
    
    for pdf_path in pdf_files:
        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            continue
            
        pdf_name = os.path.basename(pdf_path)
        print(f"\n--- Testing {pdf_name} ---")
        
        # Create Django uploaded file
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        uploaded_file = SimpleUploadedFile(
            name=pdf_name,
            content=pdf_data,
            content_type='application/pdf'
        )
        
        try:
            # Process the PDF
            result = processor.process_pdf_files([uploaded_file], company=company)
            
            print(f"✅ PDF processed successfully")
            print(f"   Template: {result['template']['name']}")
            print(f"   Transactions: {result['transactions_processed']}")
            print(f"   Created beneficiaries: {result['beneficiaries_created']}")
            print(f"   Matched beneficiaries: {result['beneficiaries_matched']}")
            
            # Verify against expected results
            expected = expected_results.get(pdf_name, {})
            if expected:
                print(f"\n   Expected company tax ID: {expected['company_tax_id']}")
                print(f"   Expected employees: {len(expected['employees'])}")
                
                # Check each expected employee
                for exp_name, exp_vat, exp_amount in expected['employees']:
                    found = False
                    for transaction in result['preview']:
                        if (transaction['beneficiary_name'] == exp_name and 
                            transaction.get('vat_number') == exp_vat and
                            transaction['amount'] == exp_amount):
                            print(f"   ✅ {exp_name} ({exp_vat}) - {exp_amount}")
                            found = True
                            break
                    if not found:
                        print(f"   ❌ {exp_name} ({exp_vat}) - {exp_amount} NOT FOUND")
            
            # Show actual extracted data
            print(f"\n   Actual extracted data:")
            for transaction in result['preview']:
                vat = transaction.get('vat_number', 'No VAT')
                print(f"   - {transaction['beneficiary_name']} ({vat}) - {transaction['amount']}")
                
        except Exception as e:
            print(f"❌ Error processing {pdf_name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Check created beneficiaries in database
    print(f"\n--- Database State ---")
    beneficiaries = Beneficiary.objects.filter(company=company).exclude(vat_number__isnull=True)
    print(f"Beneficiaries with VAT numbers: {beneficiaries.count()}")
    for b in beneficiaries:
        print(f"  - {b.name} (VAT: {b.vat_number}, Account: {b.account_number or 'None'})")
    
    print(f"\n=== TEST COMPLETE ===")

if __name__ == '__main__':
    test_vat_pdf_processing()