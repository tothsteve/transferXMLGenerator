#!/usr/bin/env python3

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
sys.path.append('/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from bank_transfers.pdf_processor import PDFTransactionProcessor
from bank_transfers.models import TransferTemplate, TemplateBeneficiary

print("=== Testing Full Template Update Flow ===")

# Simulate uploading the MEDKA PDF file
pdf_path = "/Users/tothi/Downloads/Berosszesito_Medka_2025-07ho.pdf"

try:
    # Read the PDF file
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Create uploaded file object
    uploaded_file = SimpleUploadedFile(
        name="Berosszesito_Medka_2025-07ho.pdf",
        content=pdf_content,
        content_type="application/pdf"
    )
    
    processor = PDFTransactionProcessor()
    
    print("=== Step 1: Process PDF (should find or create template) ===")
    result = processor.process_pdf_files(
        pdf_files=[uploaded_file],
        template_name=None,  # Let it auto-detect or create
        template_id=None
    )
    
    print(f"Processing result:")
    print(f"  - Template ID: {result['template']['id']}")
    print(f"  - Template Name: {result['template']['name']}")
    print(f"  - Transactions processed: {result['transactions_processed']}")
    print(f"  - Template created: {result['template_created']}")
    print(f"  - Template updated: {result['template_updated']}")
    
    template_id = result['template']['id']
    
    print(f"\n=== Step 2: Check template beneficiaries execution dates ===")
    template = TransferTemplate.objects.get(id=template_id)
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"Today's date: {today}")
    
    for tb in template.template_beneficiaries.filter(is_active=True):
        execution_date_str = tb.default_execution_date.strftime('%Y-%m-%d') if tb.default_execution_date else 'None'
        print(f"  - {tb.beneficiary.name}: {execution_date_str}")
        
        if execution_date_str == today:
            print(f"    ✓ Using today's date correctly")
        else:
            print(f"    ✗ Using {execution_date_str} instead of today ({today})")
    
    print(f"\n=== Step 3: Simulate template loading (API call) ===")
    # This simulates what happens when user clicks "Sablon Frissítése" 
    from bank_transfers.api_views import TransferTemplateViewSet
    from rest_framework.request import Request
    from django.test import RequestFactory
    from rest_framework.test import APIRequestFactory
    
    # Create a mock request
    factory = APIRequestFactory()
    request = factory.post(f'/api/templates/{template_id}/load_transfers/', {
        'originator_account_id': 1,  # Assuming account ID 1 exists
        'execution_date': today
    })
    
    # Get the template data that would be returned to frontend
    from bank_transfers.serializers import TransferTemplateSerializer
    template_data = TransferTemplateSerializer(template).data
    
    print(f"Template loading simulation:")
    print(f"  - Template: {template_data['name']}")
    print(f"  - Beneficiary count: {template_data['beneficiary_count']}")
    
    print(f"\n  Template beneficiaries execution dates:")
    for tb_data in template_data['template_beneficiaries']:
        exec_date = tb_data.get('default_execution_date')
        beneficiary_name = tb_data['beneficiary']['name']
        print(f"    - {beneficiary_name}: {exec_date}")
        
        if exec_date == today:
            print(f"      ✓ Template shows today's date correctly")
        else:
            print(f"      ✗ Template shows {exec_date} instead of today ({today})")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()