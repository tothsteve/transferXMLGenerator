#!/usr/bin/env python3
"""
Test beneficiary matching and full PDF processing
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.pdf_processor import PDFTransactionProcessor
from bank_transfers.models import Beneficiary
from django.core.files.uploadedfile import SimpleUploadedFile

def test_beneficiary_matching():
    """Test beneficiary matching with actual database"""
    
    print("="*60)
    print("TESTING BENEFICIARY MATCHING")
    print("="*60)
    
    # Show existing beneficiaries
    beneficiaries = Beneficiary.objects.all()
    print(f"\n📋 Found {beneficiaries.count()} existing beneficiaries:")
    for b in beneficiaries:
        print(f"  • {b.name} ({b.account_number})")
    
    processor = PDFTransactionProcessor()
    
    # Test data based on our PDF analysis
    test_transactions = [
        {
            'beneficiary_name': 'NAV Egyszerűsített foglalkoztatás',
            'account_number': '10032000-06057763',
            'amount': 30800,
            'remittance_info': '28778367-2-16',
            'execution_date': '2025-08-12'
        },
        {
            'beneficiary_name': 'NAV Személyi jövedelemadó',
            'account_number': '10032000-06055950',
            'amount': 271000,
            'remittance_info': '28778367-2-16',
            'execution_date': '2025-08-12'
        },
        {
            'beneficiary_name': 'Tóth István',
            'account_number': '12100011-11409520-00000000',
            'amount': 1160250,
            'remittance_info': 'jövedelem',
            'execution_date': '2025-08-15'
        },
        {
            'beneficiary_name': 'Tóth István',
            'account_number': '11600006-00000000-79306874',
            'amount': 231952,
            'remittance_info': 'jövedelem',
            'execution_date': '2025-08-15'
        },
        {
            'beneficiary_name': 'Tóth István',
            'account_number': '11600006-00000000-79306874',
            'amount': 86500,
            'remittance_info': 'jövedelem',
            'execution_date': '2025-08-15'
        }
    ]
    
    print(f"\n🔍 Testing matching for {len(test_transactions)} transactions:")
    
    # Test beneficiary matching
    matched_transactions, consolidations = processor.match_and_consolidate_beneficiaries(test_transactions)
    
    print(f"\n✅ Matching Results:")
    print(f"Original transactions: {len(test_transactions)}")
    print(f"After consolidation: {len(matched_transactions)}")
    print(f"Consolidation messages: {len(consolidations)}")
    
    print(f"\n🔄 Consolidations:")
    for msg in consolidations:
        print(f"  • {msg}")
    
    print(f"\n💰 Final Transactions:")
    total_amount = 0
    for t in matched_transactions:
        status = "✅ MATCHED" if t['beneficiary_id'] else "❌ NEW"
        print(f"  • {t['beneficiary_name']}: {t['amount']:,.0f} HUF ({status})")
        print(f"    Account: {t['account_number'][:12]}...")
        print(f"    Remittance: {t['remittance_info']}")
        total_amount += t['amount']
    
    print(f"\n💵 Total Amount: {total_amount:,.0f} HUF")
    
    # Test template creation
    print(f"\n📄 Testing Template Creation:")
    try:
        template = processor.create_template(matched_transactions, "Test Monthly Payments July 2025")
        print(f"✅ Template created: '{template.name}' (ID: {template.id})")
        
        # Test template beneficiary update
        processor.update_template_beneficiaries(template, matched_transactions)
        print(f"✅ Template updated with {len(matched_transactions)} beneficiaries")
        
        # Show template summary
        from bank_transfers.models import TemplateBeneficiary
        template_beneficiaries = TemplateBeneficiary.objects.filter(template=template)
        print(f"\n📊 Template Summary:")
        for tb in template_beneficiaries:
            print(f"  • {tb.beneficiary.name}: {tb.default_amount:,.0f} HUF")
            print(f"    Remittance: {tb.default_remittance}")
        
        # Cleanup - delete test template
        template.delete()
        print(f"\n🧹 Test template deleted")
        
    except Exception as e:
        print(f"❌ Template creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_beneficiary_matching()