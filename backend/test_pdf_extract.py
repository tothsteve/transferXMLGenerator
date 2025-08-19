#!/usr/bin/env python3
"""
Test PDF extraction functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

from bank_transfers.pdf_processor import PDFTransactionProcessor
import pdfplumber

def test_pdf_extraction():
    """Test PDF text extraction with actual files"""
    
    test_files = [
        '/Users/tothi/Library/CloudStorage/Dropbox/ITCardigan/Cégiratok/Berpapirok/2025/07/Adoesjarulekbefizetesek(2508)2025Julius ITC.pdf',
        '/Users/tothi/Library/CloudStorage/Dropbox/ITCardigan/Cégiratok/Berpapirok/2025/07/Bankiutalasok2025Julius ITC.pdf'
    ]
    
    processor = PDFTransactionProcessor()
    
    for file_path in test_files:
        print(f"\n{'='*60}")
        print(f"Testing: {file_path.split('/')[-1]}")
        print('='*60)
        
        try:
            # Test basic text extraction
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                print(f"✅ Text extracted: {len(text)} characters")
                print("First 200 chars:")
                print(text[:200])
                print("...")
                
                # Test PDF type detection
                if "Adó és járulék befizetések" in text:
                    print("🔍 Detected: TAX PAYMENT PDF")
                    result = processor.parse_tax_pdf(text)
                    print(f"📊 Extracted {len(result['transactions'])} transactions")
                    for t in result['transactions']:
                        print(f"  • {t['beneficiary_name']}: {t['amount']:,.0f} HUF")
                        
                elif "Banki utalások" in text or "utalások" in text.lower():
                    print("🔍 Detected: SALARY PAYMENT PDF")
                    result = processor.parse_salary_pdf(text)
                    print(f"📊 Extracted {len(result['transactions'])} transactions")
                    for t in result['transactions']:
                        print(f"  • {t['beneficiary_name']}: {t['amount']:,.0f} HUF")
                else:
                    print("❌ Unknown PDF format")
                    
        except Exception as e:
            print(f"❌ Error processing {file_path.split('/')[-1]}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_pdf_extraction()