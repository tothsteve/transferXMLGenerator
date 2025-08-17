#!/usr/bin/env python3

import os
import sys
import django
import re
import pdfplumber

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
sys.path.append('/Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend')
django.setup()

# Test the MEDKA PDF to see what dates are found
pdf_path = "/Users/tothi/Downloads/Berosszesito_Medka_2025-07ho.pdf"

print("=== Analyzing MEDKA PDF Date Extraction ===")

try:
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    print("=== FULL PDF TEXT ===")
    print(text)
    print("\n" + "="*50 + "\n")
    
    # Check for explicit payment deadline
    print("=== SEARCHING FOR PAYMENT DEADLINE ===")
    deadline_patterns = [
        r'fizetési\s*határidő[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})',
        r'befizetési\s*határidő[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})',
        r'határidő[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})'
    ]
    
    explicit_deadline_found = False
    for pattern in deadline_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"Found explicit deadline with pattern '{pattern}': {matches}")
            explicit_deadline_found = True
    
    if not explicit_deadline_found:
        print("❌ NO explicit payment deadline found in PDF")
        print("This means we should use TODAY'S DATE, not calculated next month 12th")
    
    # Check what date extraction logic finds
    print("\n=== CURRENT DATE EXTRACTION LOGIC ===")
    date_match = re.search(r'(\d{4})\s+(január|február|március|április|május|június|július|augusztus|szeptember|október|november|december)', text)
    if date_match:
        year = date_match.group(1)
        month_name = date_match.group(2)
        print(f"Found year: {year}, month: {month_name}")
        
        month_map = {
            'január': '01', 'február': '02', 'március': '03', 'április': '04',
            'május': '05', 'június': '06', 'július': '07', 'augusztus': '08',
            'szeptember': '09', 'október': '10', 'november': '11', 'december': '12'
        }
        month = month_map.get(month_name, '08')
        print(f"Mapped to month number: {month}")
        
        # Due date is typically 12th of the following month
        next_month = str(int(month) + 1).zfill(2) if int(month) < 12 else '01'
        due_year = year if int(month) < 12 else str(int(year) + 1)
        calculated_due_date = f"{due_year}-{next_month}-12"
        print(f"Calculated due date: {calculated_due_date}")
        print("⚠️  This is using CALCULATED date, not explicit deadline from PDF")
        print("⚠️  Since no explicit deadline exists, should use TODAY'S DATE instead")
    
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\nToday's date: {today}")
    print("✅ This is what should be used for execution_date")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()