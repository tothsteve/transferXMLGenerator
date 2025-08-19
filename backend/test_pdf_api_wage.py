#!/usr/bin/env python3
"""
Test the wage tax PDF through the actual API endpoint
"""

import requests
import os

def test_api_upload():
    """Test PDF upload through API"""
    pdf_path = "/Users/tothi/Downloads/Berosszesito_Medka_2025-07ho.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # API endpoint
    url = "http://localhost:8000/api/templates/process_pdf/"
    
    try:
        # Prepare files and data
        with open(pdf_path, 'rb') as f:
            files = {
                'pdf_files': ('Berosszesito_Medka_2025-07ho.pdf', f, 'application/pdf')
            }
            data = {
                'template_name': 'Medka Wage Tax July 2025'
            }
            
            print("🚀 Uploading PDF to API...")
            response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API upload successful!")
            print(f"Template: {result['template']['name']}")
            print(f"ID: {result['template']['id']}")
            print(f"Transactions: {result['transactions_processed']}")
            print(f"Total Amount: {result['total_amount']:,.0f} HUF")
            
            print(f"\n📋 Transactions:")
            for i, t in enumerate(result['preview'], 1):
                status = "Existing" if t['beneficiary_id'] else "New"
                print(f"{i}. {t['beneficiary_name']} - {t['amount']:,.0f} HUF ({status})")
            
            if result['consolidations']:
                print(f"\n📄 Notes:")
                for msg in result['consolidations']:
                    print(f"  • {msg}")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the Django server running on localhost:8000?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_upload()