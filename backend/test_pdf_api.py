#!/usr/bin/env python3
"""
Test the PDF processing API endpoint
"""
import requests
import json

def test_pdf_processing_api():
    """Test the PDF processing API"""
    
    print("="*60)
    print("TESTING PDF PROCESSING API")
    print("="*60)
    
    # Test data that simulates what we'd extract from PDF
    # This bypasses the actual PDF reading and tests the processing logic
    url = "http://localhost:8000/api/templates/process_pdf/"
    
    # We'll test with a small dummy file since we're mainly testing the matching logic
    test_data = {
        'template_name': 'Test Template NAV 2025-08'
    }
    
    # Create a minimal test file (simulating PDF)
    files = {
        'pdf_files': ('test.pdf', b'%PDF-1.4 test content', 'application/pdf')
    }
    
    try:
        print("📤 Making API request to process PDF...")
        response = requests.post(url, data=test_data, files=files)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Processing results:")
            print(f"   Template: {data['template']['name']} (ID: {data['template']['id']})")
            print(f"   Beneficiaries: {data['template']['beneficiary_count']}")
            print(f"   Transactions: {data['transactions_processed']}")
            print(f"   Matched: {data['beneficiaries_matched']}")
            print(f"   Created: {data['beneficiaries_created']}")
            print(f"   Total Amount: {data['total_amount']:,.0f} HUF")
            
            if data['consolidations']:
                print("\n🔄 Consolidations:")
                for consolidation in data['consolidations']:
                    print(f"   • {consolidation}")
            
            if data['preview']:
                print(f"\n📋 Preview (first 3 transactions):")
                for i, trans in enumerate(data['preview'][:3]):
                    print(f"   {i+1}. {trans['beneficiary_name']}")
                    print(f"      Account: {trans['account_number']}")
                    print(f"      Amount: {trans['amount']:,.0f} HUF")
                    print(f"      Matched: {'✅' if trans['beneficiary_id'] else '❌ (new)'}")
                    print()
                    
        elif response.status_code == 400:
            error_data = response.json()
            print("❌ Bad Request Error:")
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
            if 'details' in error_data:
                print(f"   Details: {error_data['details']}")
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pdf_processing_api()