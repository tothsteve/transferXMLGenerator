#!/usr/bin/env python3
"""
Test the PDF processing API endpoint
"""
import os
import django
import requests
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()

def test_pdf_api_endpoint():
    """Test the PDF processing API endpoint"""
    
    # Start Django server first (should be running)
    api_url = "http://localhost:8000/api/templates/process_pdf/"
    
    # PDF files to test
    pdf_files = [
        '/Users/tothi/Library/CloudStorage/Dropbox/ITCardigan/Cégiratok/Berpapirok/2025/07/Adoesjarulekbefizetesek(2508)2025Julius ITC.pdf',
        '/Users/tothi/Library/CloudStorage/Dropbox/ITCardigan/Cégiratok/Berpapirok/2025/07/Bankiutalasok2025Julius ITC.pdf'
    ]
    
    print("="*60)
    print("TESTING PDF PROCESSING API ENDPOINT")
    print("="*60)
    
    # Check if files exist
    for file_path in pdf_files:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return
        else:
            print(f"✅ File found: {Path(file_path).name}")
    
    # Prepare files for upload
    files = []
    try:
        for file_path in pdf_files:
            files.append(('pdf_files', (Path(file_path).name, open(file_path, 'rb'), 'application/pdf')))
        
        # Prepare data
        data = {
            'template_name': 'API Test Monthly Payments July 2025'
        }
        
        print(f"\n📡 Sending POST request to: {api_url}")
        print(f"Files: {[f[1][0] for f in files]}")
        print(f"Data: {data}")
        
        # Make API request
        response = requests.post(api_url, files=files, data=data, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS! API Response:")
            print(f"📄 Template Created: {result['template']['name']} (ID: {result['template']['id']})")
            print(f"🔢 Transactions Processed: {result['transactions_processed']}")
            print(f"✅ Beneficiaries Matched: {result['beneficiaries_matched']}")
            print(f"🆕 Beneficiaries Created: {result['beneficiaries_created']}")
            print(f"💰 Total Amount: {result['total_amount']:,.0f} HUF")
            
            if result['consolidations']:
                print(f"\n🔄 Consolidations:")
                for msg in result['consolidations']:
                    print(f"  • {msg}")
            
            print(f"\n📋 Preview Transactions:")
            for t in result['preview']:
                status_icon = "✅" if t['beneficiary_id'] else "🆕"
                print(f"  {status_icon} {t['beneficiary_name']}: {t['amount']:,.0f} HUF")
                
            # Cleanup - delete test template
            template_id = result['template']['id']
            delete_url = f"http://localhost:8000/api/templates/{template_id}/"
            delete_response = requests.delete(delete_url)
            if delete_response.status_code == 204:
                print(f"\n🧹 Test template deleted (ID: {template_id})")
            else:
                print(f"\n⚠️ Failed to delete test template: {delete_response.status_code}")
        
        else:
            print(f"\n❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Details: {error_data}")
            except:
                print(f"Error Text: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure Django server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close file handles
        for file_tuple in files:
            file_tuple[1][1].close()

if __name__ == "__main__":
    test_pdf_api_endpoint()