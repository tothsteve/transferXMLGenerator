"""
PDF Transaction Processor
Extracts transaction data from Hungarian payment PDFs (NAV tax and salary documents)
"""

import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from django.core.files.uploadedfile import UploadedFile

from .models import Beneficiary, TransferTemplate, TemplateBeneficiary
from .hungarian_account_validator import (
    validate_and_format_hungarian_account_number,
    clean_account_number,
    format_account_number_for_display
)


class PDFTransactionProcessor:
    """Process Hungarian payment PDFs and extract transaction data"""
    
    def __init__(self):
        self.supported_formats = ['tax_payments', 'salary_payments', 'wage_tax_summary', 'invoice']
    
    def normalize_tax_number(self, tax_number: str) -> str:
        """
        Normalize Hungarian tax number by removing dashes and spaces
        
        Args:
            tax_number: Raw tax number (e.g., "12345678-2-16" or "12345678216")
            
        Returns:
            Normalized tax number with only digits
        """
        if not tax_number:
            return ""
        return re.sub(r'[-\s]', '', tax_number.strip())
    
    def validate_company_tax_number(self, pdf_tax_id: str, company) -> Dict[str, Any]:
        """
        Validate that the extracted company tax ID from PDF matches the user's company
        
        Args:
            pdf_tax_id: Tax ID extracted from PDF
            company: User's company object
            
        Returns:
            Dict with validation result and error message if invalid
        """
        if not company:
            return {
                'is_valid': False,
                'error': 'Nincs cég megadva a validációhoz'
            }
        
        if not pdf_tax_id or pdf_tax_id == "Unknown":
            return {
                'is_valid': False,
                'error': 'Nem sikerült kinyerni az adószámot a PDF-ből'
            }
        
        # Normalize both tax numbers for comparison
        normalized_pdf_tax = self.normalize_tax_number(pdf_tax_id)
        normalized_company_tax = self.normalize_tax_number(company.tax_id)
        
        if normalized_pdf_tax != normalized_company_tax:
            return {
                'is_valid': False,
                'error': f'A PDF adószáma ({pdf_tax_id}) nem egyezik a cég adószámával ({company.tax_id}). Kérjük ellenőrizze, hogy a megfelelő cég PDF-jét tölti-e fel.'
            }
        
        return {
            'is_valid': True,
            'error': None
        }
    
    def validate_and_format_account_number(self, account_number: str) -> Dict[str, Any]:
        """
        Validate and format Hungarian account number using proper validation logic
        
        Args:
            account_number: Raw account number from PDF
            
        Returns:
            Dict with validation result, formatted number, and error if any
        """
        if not account_number:
            return {
                'is_valid': False,
                'formatted': '',
                'clean': '',
                'error': 'Empty account number'
            }
        
        # Clean the account number first
        clean_account = clean_account_number(account_number)
        
        # Validate and format using Hungarian bank account rules
        # We skip checksum validation for PDF imports to be more lenient
        result = validate_and_format_hungarian_account_number(clean_account, validate_checksum=False)
        
        return {
            'is_valid': result.is_valid,
            'formatted': result.formatted,
            'clean': clean_account,
            'error': result.error
        }
    
    def process_pdf_files(self, pdf_files: List[UploadedFile], template_name: str = None, template_id: int = None, company=None) -> Dict[str, Any]:
        """
        Main entry point - process multiple PDF files and create/update template
        
        Args:
            pdf_files: List of uploaded PDF files
            template_name: Optional template name (auto-generated if None)
            template_id: Optional template ID to update existing template
            
        Returns:
            Dictionary with processing results
        """
        all_transactions = []
        consolidations = []
        company_names = []
        company_tax_ids = []
        
        # Step 1: Extract data from all PDFs
        for pdf_file in pdf_files:
            try:
                # First extract raw text to get company name
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                # Extract company name from text
                company_name = self.extract_company_name_from_text(text)
                if company_name and company_name != "Ismeretlen cég":
                    company_names.append(company_name)
                
                pdf_data = self.extract_pdf_data(pdf_file)
                transactions = pdf_data['transactions']  # transactions are already parsed in extract_pdf_data
                all_transactions.extend(transactions)
                
                # Collect company tax ID for validation
                pdf_tax_id = pdf_data.get('company_tax_id')
                if pdf_tax_id and pdf_tax_id != "Unknown":
                    company_tax_ids.append(pdf_tax_id)
                    
            except Exception as e:
                raise ValueError(f"Failed to process {pdf_file.name}: {str(e)}")
        
        # Step 1.5: Validate company tax numbers if company is provided
        if company and company_tax_ids:
            # Get unique tax IDs from all PDFs
            unique_tax_ids = list(set(company_tax_ids))
            
            # Validate each unique tax ID
            for pdf_tax_id in unique_tax_ids:
                validation_result = self.validate_company_tax_number(pdf_tax_id, company)
                if not validation_result['is_valid']:
                    raise ValueError(validation_result['error'])
        
        # Determine the best company name to use
        if company_names:
            # Use the most common company name, or the first one if all are unique
            from collections import Counter
            company_counter = Counter(company_names)
            most_common_company = company_counter.most_common(1)[0][0]
        else:
            most_common_company = None
        
        # Step 2: Match beneficiaries and consolidate transactions
        all_transactions, consolidation_msgs = self.match_and_consolidate_beneficiaries(all_transactions, company)
        consolidations.extend(consolidation_msgs)
        
        # Step 3: Try to find existing template with matching beneficiaries (if not explicitly updating one)
        existing_template = None
        template_created = True
        
        if template_id:
            # Explicitly updating a specific template
            template = TransferTemplate.objects.get(id=template_id)
            template_created = False
        else:
            # Check if there's an existing template with the same beneficiaries
            existing_template = self.find_matching_template(all_transactions, company)
            
            if existing_template:
                template = existing_template
                template_created = False
                consolidations.append(f"Meglévő sablon frissítése: '{template.name}'")
            else:
                template = self.create_template(all_transactions, template_name, most_common_company, company)
                template_created = True
        
        # Step 4: Update template with transactions
        self.update_template_beneficiaries(template, all_transactions, company)
        
        return {
            'template': {
                'id': template.id,
                'name': template.name,
                'beneficiary_count': len(all_transactions)
            },
            'transactions_processed': len(all_transactions),
            'beneficiaries_matched': len([t for t in all_transactions if not t.get('created_beneficiary', False)]),
            'beneficiaries_created': len([t for t in all_transactions if t.get('created_beneficiary', False)]),
            'consolidations': consolidations,
            'template_created': template_created,
            'template_updated': not template_created,
            'preview': all_transactions,
            'total_amount': sum(t['amount'] for t in all_transactions)
        }
    
    def extract_pdf_data(self, pdf_file: UploadedFile) -> Dict[str, Any]:
        """Extract raw text and identify PDF type"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Detect PDF type based on content - order matters (most specific first)
            if "Adó és járulék befizetések" in text:
                print(f"DEBUG: Detected as TAX PDF: {pdf_file.name}")
                return self.parse_tax_pdf(text)
            elif ("BÉRJEGYZÉK" in text or "B É R J E G Y Z É K" in text) and "Átutalt összeg:" in text and re.search(r'\(\d{10}\)', text):
                print(f"DEBUG: Detected as SALARY WITH VAT PDF: {pdf_file.name}")
                return self.parse_salary_with_vat_pdf(text)
            elif "Bérösszesítő" in text or "Megnevezés" in text and "Bankszámlaszám" in text and "Összeg" in text:
                print(f"DEBUG: Detected as WAGE TAX SUMMARY PDF: {pdf_file.name}")
                return self.parse_wage_tax_summary_pdf(text)
            elif "Banki utalások" in text or "utalások" in text.lower():
                print(f"DEBUG: Detected as SALARY PDF: {pdf_file.name}")
                return self.parse_salary_pdf(text)
            elif self.is_invoice_pdf(text):
                print(f"DEBUG: Detected as INVOICE PDF: {pdf_file.name}")
                return self.parse_invoice_pdf(text)
            else:
                raise ValueError(f"Unknown PDF format in {pdf_file.name}")
                
        except Exception as e:
            raise ValueError(f"Failed to read PDF {pdf_file.name}: {str(e)}")
    
    def extract_company_name_from_text(self, text: str) -> str:
        """
        Extract company name from PDF text for automatic template naming
        
        Args:
            text: Raw PDF text
            
        Returns:
            Company name or default fallback
        """
        # Clean up text - remove extra whitespace and line breaks
        cleaned_text = re.sub(r'\s+', ' ', text.replace('\n', ' '))
        
        # Try to find company name patterns
        
        # Pattern 1: "COMPANY NAME Kft. (tax-id)" format - prioritize uppercase starting companies
        company_match = re.search(r'([A-ZÁÉÍÓÖŐÜŰ]{2,}[A-Za-záéíóöőüű\s]*(?:Kft|Bt|Zrt|Nyrt)\.?)\s*\(\d{8}-\d-\d{2}\)', cleaned_text)
        if company_match:
            company_name = company_match.group(1).strip()
            # Clean up any remaining formatting issues
            company_name = re.sub(r'\s+', ' ', company_name)
            return company_name
        
        # Pattern 2: Look for line with company name and tax ID together
        # "MEDKA Kft. (32560682-2-43) - 2025"
        company_line_match = re.search(r'([A-ZÁÉÍÓÖŐÜŰ][A-Za-záéíóöőüű\s]+(?:Kft|Bt|Zrt|Nyrt)\.?)\s*\(\d{8}-\d-\d{2}\)', cleaned_text)
        if company_line_match:
            company_name = company_line_match.group(1).strip()
            company_name = re.sub(r'\s+', ' ', company_name)
            return company_name
        
        # Pattern 3: Look for "Bérösszesítő COMPANY NAME" format (handle broken formatting)
        wage_summary_match = re.search(r'Bérösszesít[őo]*\s*([A-ZÁÉÍÓÖŐÜŰ][A-Za-záéíóöőüű\s]+(?:Kft|Bt|Zrt|Nyrt)\.?)', cleaned_text)
        if wage_summary_match:
            company_name = wage_summary_match.group(1).strip()
            company_name = re.sub(r'\s+', ' ', company_name)
            # Remove "Bérösszesít" prefix if it got included
            company_name = re.sub(r'^Bérösszesít[őo]*\s*', '', company_name)
            return company_name
        
        # Pattern 4: Look for standalone company names with Kft/Bt/Zrt (more specific)
        standalone_company = re.search(r'\b([A-ZÁÉÍÓÖŐÜŰ][A-Za-záéíóöőüű\s]{3,25}(?:Kft|Bt|Zrt|Nyrt)\.?)\b', cleaned_text)
        if standalone_company:
            company_name = standalone_company.group(1).strip()
            company_name = re.sub(r'\s+', ' ', company_name)
            # Exclude common false positives
            if not any(exclude in company_name.lower() for exclude in ['bérösszesítő', 'program', 'felhasználó']):
                return company_name
        
        # Pattern 5: Extract from lines that contain both company type and tax ID
        tax_context_match = re.search(r'([A-ZÁÉÍÓÖŐÜŰ][A-Za-záéíóöőüű\s]+(?:Kft|Bt|Zrt|Nyrt)\.?)[^(]*\(\d{8}-\d-\d{2}\)', cleaned_text)
        if tax_context_match:
            company_name = tax_context_match.group(1).strip()
            company_name = re.sub(r'\s+', ' ', company_name)
            return company_name
        
        # Fallback: return default
        return "Ismeretlen cég"
    
    def parse_tax_pdf(self, text: str) -> Dict[str, Any]:
        """Parse NAV tax payment PDF"""
        transactions = []
        
        # Extract company tax ID (remittance info for NAV payments)
        tax_id_match = re.search(r'(\d{8}-\d-\d{2})', text)
        company_tax_id = tax_id_match.group(1) if tax_id_match else "28778367-2-16"
        
        # Extract due date
        date_match = re.search(r'Befizetési határidő:\s*(\d{4})\.(\d{2})\.(\d{2})', text)
        if date_match:
            year, month, day = date_match.groups()
            due_date = f"{year}-{month}-{day}"
        else:
            # Default to today's date
            due_date = self.get_default_payment_date()
        
        # Extract NAV transactions using table structure
        # Look for the table with Adónem kód, Számlaszám, Befizetendő forint
        # NAV accounts use 2x8 format (10032000-06055950)
        table_pattern = r'(.+?)\s+(\d{3})\s+(\d{8}-?\d{8})\s+([\d\s]+)'
        matches = re.findall(table_pattern, text)
        
        seen_transactions = set()  # Prevent duplicates
        
        for match in matches:
            description, code, raw_account, amount_str = match
            
            # Validate and format the account number
            account_validation = self.validate_and_format_account_number(raw_account)
            if not account_validation['is_valid']:
                print(f"Warning: Invalid account number in tax PDF: {raw_account} - {account_validation['error']}")
                continue
                
            account = account_validation['formatted']
            
            # Clean description and validate it's a NAV transaction
            clean_desc = description.strip()
            if any(keyword in clean_desc.lower() for keyword in ['nav', 'adó', 'járulék', 'hozzájárulás']):
                try:
                    amount = float(amount_str.replace(' ', ''))
                    if amount > 0:
                        # Create unique key to prevent duplicates
                        unique_key = (clean_desc, account, amount)
                        if unique_key not in seen_transactions:
                            seen_transactions.add(unique_key)
                            
                            # Clean up beneficiary name
                            if clean_desc.startswith('NAV'):
                                beneficiary_name = clean_desc
                            else:
                                beneficiary_name = f"NAV {clean_desc}"
                            
                            # If due_date is None, use today's date
                            final_execution_date = due_date if due_date else self.get_default_payment_date()
                            print(f"DEBUG: Tax PDF transaction - due_date: {due_date}, final_execution_date: {final_execution_date}")
                            transactions.append({
                                'beneficiary_name': beneficiary_name,
                                'account_number': account,
                                'amount': amount,
                                'remittance_info': company_tax_id,
                                'execution_date': final_execution_date
                            })
                except ValueError:
                    continue
        
        return {
            'pdf_type': 'tax_payments',
            'transactions': transactions,
            'due_date': due_date,
            'company_tax_id': company_tax_id
        }
    
    def parse_salary_pdf(self, text: str) -> Dict[str, Any]:
        """Parse salary/bank transfer PDF"""
        transactions = []
        
        # Extract execution date (default to today's date)
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', text)
        if date_match:
            year, month, day = date_match.groups()
            due_date = f"{year}-{month}-{day}"  # Use actual date from PDF
        else:
            due_date = self.get_default_payment_date()  # Use today's date
        
        # Pattern for salary lines: [number]. [name] [tax_id] [account] [amount]
        # Bank accounts use 3x8 format (12100011-11409520-00000000)
        salary_pattern = r'\d+\.\s+(.+?)\s+(\d{10})\s+(\d{8}-?\d{8}-?\d{8})\s+([\d,]+)'
        matches = re.findall(salary_pattern, text)
        
        for match in matches:
            name, tax_id, raw_account, amount_str = match
            
            # Validate and format the account number
            account_validation = self.validate_and_format_account_number(raw_account)
            if not account_validation['is_valid']:
                print(f"Warning: Invalid account number in salary PDF: {raw_account} - {account_validation['error']}")
                continue
                
            account = account_validation['formatted']
            amount = float(amount_str.replace(',', '').replace(' ', ''))
            
            if amount > 0:
                # If due_date is None, use today's date
                final_execution_date = due_date if due_date else self.get_default_payment_date()
                print(f"DEBUG: Salary PDF transaction - due_date: {due_date}, final_execution_date: {final_execution_date}")
                transactions.append({
                    'beneficiary_name': name.strip(),
                    'account_number': account,
                    'amount': amount,
                    'remittance_info': 'jövedelem',  # Default for salary
                    'execution_date': final_execution_date
                })
        
        return {
            'pdf_type': 'salary_payments',
            'transactions': transactions,
            'due_date': due_date
        }
    
    def parse_salary_with_vat_pdf(self, text: str) -> Dict[str, Any]:
        """Parse salary PDF that uses VAT numbers instead of account numbers for employee matching"""
        transactions = []
        
        # Extract company tax ID (remittance info)
        company_tax_id_match = re.search(r'(\d{8}-\d-\d{2})', text)
        company_tax_id = company_tax_id_match.group(1) if company_tax_id_match else "Unknown"
        
        # Extract execution date from header
        date_match = re.search(r'(\d{4})\.\s*(január|február|március|április|május|június|július|augusztus|szeptember|október|november|december)', text)
        if date_match:
            year = date_match.group(1)
            month_name = date_match.group(2)
            
            # Convert Hungarian month names to numbers
            month_map = {
                'január': '01', 'február': '02', 'március': '03', 'április': '04',
                'május': '05', 'június': '06', 'július': '07', 'augusztus': '08',
                'szeptember': '09', 'október': '10', 'november': '11', 'december': '12'
            }
            month = month_map.get(month_name, '01')
            due_date = f"{year}-{month}-15"  # Use 15th of the month as default
        else:
            due_date = self.get_default_payment_date()
        
        # Process per-page to handle complex layout
        # Split text by page indicators and process each section
        page_sections = re.split(r'B É R J E G Y Z É K', text)[1:]  # Split by page headers, skip first empty
        
        for page_text in page_sections:
            if not page_text.strip():
                continue
                
            # Extract employee name and VAT number from header
            name_vat_pattern = r'^([A-ZÁÉÍÓÖŐÜŰa-záéíóöőüű\s]+?)\s*\((\d{10})\)'
            name_vat_match = re.search(name_vat_pattern, page_text, re.MULTILINE)
            
            # Extract amount
            amount_pattern = r'Átutalt összeg:\s*([\d\s]+)'
            amount_match = re.search(amount_pattern, page_text)
            
            if name_vat_match and amount_match:
                name = name_vat_match.group(1).strip()
                vat_number = name_vat_match.group(2)
                amount_str = amount_match.group(1).strip()
                
                # Validate VAT number format (10 digits)
                if not vat_number.isdigit() or len(vat_number) != 10:
                    print(f"Warning: Invalid VAT number format: {vat_number}")
                    continue
                    
                # Clean and parse amount
                try:
                    amount = float(amount_str.replace(' ', '').replace(',', ''))
                    
                    # Skip zero amounts
                    if amount <= 0:
                        print(f"Info: Skipping {name} - zero amount")
                        continue
                        
                    transactions.append({
                        'beneficiary_name': name,
                        'vat_number': vat_number,
                        'amount': amount,
                        'remittance_info': f'{company_tax_id} - jövedelem',
                        'execution_date': due_date
                    })
                    print(f"DEBUG: Added salary transaction: {name} ({vat_number}) - {amount}")
                    
                except ValueError:
                    print(f"Warning: Could not parse amount: {amount_str}")
                    continue
        
        return {
            'pdf_type': 'salary_with_vat',
            'transactions': transactions,
            'due_date': due_date,
            'company_tax_id': company_tax_id
        }
    
    def parse_wage_tax_summary_pdf(self, text: str) -> Dict[str, Any]:
        """Parse wage tax summary PDF (Bérösszesítő)"""
        transactions = []
        
        # Extract company tax ID from the document
        # Look for pattern like "MEDKA Kft. (32560682-2-43)"
        tax_id_match = re.search(r'\((\d{8}-\d-\d{2})\)', text)
        company_tax_id = tax_id_match.group(1) if tax_id_match else "Unknown"
        
        # Check for explicit payment deadline first
        deadline_patterns = [
            r'fizetési\s*határidő[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})',
            r'befizetési\s*határidő[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})',
            r'határidő[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})'
        ]
        
        explicit_deadline = None
        for pattern in deadline_patterns:
            deadline_match = re.search(pattern, text, re.IGNORECASE)
            if deadline_match:
                date_str = deadline_match.group(1).replace('/', '-').replace('.', '-')
                explicit_deadline = date_str
                break
        
        if explicit_deadline:
            # Use explicit deadline from PDF
            due_date = explicit_deadline
            print(f"DEBUG: Found explicit payment deadline in wage tax summary: {due_date}")
        else:
            # No explicit deadline - check if this is just a summary document
            # Extract year and month from title for reference only
            date_match = re.search(r'(\d{4})\s+(január|február|március|április|május|június|július|augusztus|szeptember|október|november|december)', text)
            if date_match:
                year = date_match.group(1)
                month_name = date_match.group(2)
                print(f"DEBUG: Wage tax summary for {month_name} {year} but no explicit deadline - using today's date")
            
            # Use today's date since no explicit deadline exists
            due_date = self.get_default_payment_date()
            print(f"DEBUG: No explicit deadline in wage tax summary - using today's date: {due_date}")
        
        # Parse the wage tax summary table
        # Look for lines with: Tax description + Tax code + Account number + Amount
        # Pattern: Megnevezés [Code] [Percentage] Account Amount
        
        # Split text into lines for better parsing
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for lines that contain NAV tax account numbers (starting with 10032000)
            if '10032000' in line:
                # Try to extract: description, code, account, amount
                # Pattern variations we need to handle:
                # "Magánszemélytől levont SZJA 15,00% 10032000-06055950 547 00 290 0"
                # "Társ.bizt. járulék (biztosítottaktól levont) 18,50% 407 10032000-06055819 675 000"
                
                # Find the account number in the line
                account_match = re.search(r'(10032000-?\d{8})', line)
                if not account_match:
                    continue
                    
                raw_account_number = account_match.group(1)
                
                # Validate and format the account number properly
                account_validation = self.validate_and_format_account_number(raw_account_number)
                if not account_validation['is_valid']:
                    print(f"Warning: Invalid account number format: {raw_account_number} - {account_validation['error']}")
                    continue
                    
                account_number = account_validation['formatted']
                
                # Extract everything before the account number as description
                account_pos = line.find(account_number)
                description_part = line[:account_pos].strip()
                
                # Extract everything after the account number as amount
                amount_part = line[account_pos + len(account_number):].strip()
                
                # Clean up description - remove percentages and tax codes
                description = re.sub(r'\d+,\d+%', '', description_part)  # Remove percentages
                description = re.sub(r'\b\d{3}\b', '', description)      # Remove 3-digit tax codes
                description = re.sub(r'\s+', ' ', description).strip()   # Clean whitespace
                
                # Parse amount (remove spaces and convert to float)
                try:
                    # Handle amounts like "547 00", "675 000", "0 103"
                    amount_clean = re.sub(r'\s+', '', amount_part)
                    # If it ends with digits, it's the amount
                    amount_match = re.search(r'^(\d+)', amount_clean)
                    if amount_match:
                        amount = float(amount_match.group(1))
                        
                        # Skip if amount is 0
                        if amount == 0:
                            continue
                            
                        # Create appropriate beneficiary name
                        if description:
                            beneficiary_name = f"NAV {description}"
                        else:
                            beneficiary_name = "NAV Adó és járulék"
                            
                        transactions.append({
                            'beneficiary_name': beneficiary_name,
                            'account_number': account_number,
                            'amount': amount,
                            'remittance_info': company_tax_id,
                            'execution_date': due_date if due_date else self.get_default_payment_date()
                        })
                        
                except (ValueError, AttributeError):
                    # Skip lines where amount parsing fails
                    continue
        
        return {
            'pdf_type': 'wage_tax_summary',
            'transactions': transactions,
            'due_date': due_date,
            'company_tax_id': company_tax_id
        }
    
    def match_and_consolidate_beneficiaries(self, transactions: List[Dict], company=None) -> Tuple[List[Dict], List[str]]:
        """Match transactions to existing beneficiaries and consolidate duplicates"""
        consolidations = []
        matched_transactions = []
        
        # Group transactions by beneficiary identifier (account_number OR vat_number)
        grouped = {}
        for transaction in transactions:
            if 'vat_number' in transaction:
                # VAT-based transaction - group by name and VAT number
                key = (transaction['beneficiary_name'], transaction.get('vat_number', ''))
            else:
                # Account-based transaction - group by name and account
                key = (transaction['beneficiary_name'], transaction.get('account_number', ''))
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(transaction)
        
        for (name, identifier), trans_group in grouped.items():
            # Try to match existing beneficiary
            if 'vat_number' in trans_group[0]:
                # VAT-based matching
                beneficiary = self.find_matching_beneficiary_by_vat(identifier, name, company)
            else:
                # Account-based matching (existing logic)
                beneficiary = self.find_matching_beneficiary(identifier, name, company)
            
            if len(trans_group) > 1:
                # Consolidate multiple transactions to same beneficiary
                total_amount = sum(t['amount'] for t in trans_group)
                
                # Determine remittance info based on beneficiary and transaction type
                if 'vat_number' in trans_group[0]:
                    # VAT-based transaction: Use beneficiary's stored remittance info or default to 'jövedelem'
                    if beneficiary and beneficiary.remittance_information:
                        remittance_info = beneficiary.remittance_information
                    else:
                        remittance_info = 'jövedelem'
                elif 'account_number' in trans_group[0] and '116' in identifier and 'tóth' in name.lower():
                    # Special handling for specific account-based transactions
                    remittance_info = 'jövedelem + bérleti díj'
                else:
                    # Other account-based transactions: use original remittance info
                    remittance_info = trans_group[0]['remittance_info']
                
                # Format consolidation message based on transaction type
                if 'vat_number' in trans_group[0]:
                    identifier_display = f"VAT:{identifier}"
                else:
                    identifier_display = f"{identifier[:8]}..." if len(identifier) > 8 else identifier
                
                consolidations.append(f"{name} ({identifier_display}): {len(trans_group)} transfers merged into {total_amount:,.0f} HUF")
                
                # Create consolidated transaction
                consolidated_transaction = {
                    'beneficiary_id': beneficiary.id if beneficiary else None,
                    'beneficiary_name': beneficiary.name if beneficiary else name,
                    'amount': total_amount,
                    'remittance_info': remittance_info,
                    'execution_date': trans_group[0]['execution_date'],
                    'created_beneficiary': beneficiary is None
                }
                
                # Add either account_number or vat_number based on transaction type
                if 'vat_number' in trans_group[0]:
                    consolidated_transaction['vat_number'] = identifier
                    # For VAT-based transactions, use beneficiary's account if found
                    if beneficiary and beneficiary.account_number:
                        consolidated_transaction['account_number'] = beneficiary.account_number
                else:
                    consolidated_transaction['account_number'] = identifier
                
                matched_transactions.append(consolidated_transaction)
            else:
                # Single transaction
                transaction = trans_group[0]
                
                # Determine remittance info for single transaction
                if 'vat_number' in transaction:
                    # VAT-based transaction: Use beneficiary's stored remittance info or default to 'jövedelem'
                    if beneficiary and beneficiary.remittance_information:
                        remittance_info = beneficiary.remittance_information
                    else:
                        remittance_info = 'jövedelem'
                else:
                    # Account-based transaction: use original remittance info
                    remittance_info = transaction['remittance_info']
                
                matched_transaction = {
                    'beneficiary_id': beneficiary.id if beneficiary else None,
                    'beneficiary_name': beneficiary.name if beneficiary else transaction['beneficiary_name'],
                    'amount': transaction['amount'],
                    'remittance_info': remittance_info,
                    'execution_date': transaction['execution_date'],
                    'created_beneficiary': beneficiary is None
                }
                
                # Add either account_number or vat_number based on transaction type
                if 'vat_number' in transaction:
                    matched_transaction['vat_number'] = transaction['vat_number']
                    # For VAT-based transactions, use beneficiary's account if found
                    if beneficiary and beneficiary.account_number:
                        matched_transaction['account_number'] = beneficiary.account_number
                else:
                    matched_transaction['account_number'] = transaction['account_number']
                
                matched_transactions.append(matched_transaction)
        
        return matched_transactions, consolidations
    
    def find_matching_beneficiary(self, account_number: str, name: str = None, company=None) -> Optional[Beneficiary]:
        """Find existing beneficiary by account number or name"""
        # Clean account number for matching (remove dashes and spaces)
        clean_account = account_number.replace('-', '').replace(' ', '')
        
        # Try exact full account match first (most reliable)
        beneficiary = Beneficiary.objects.filter(
            account_number=clean_account,
            company=company
        ).first()
        
        # Try with original format (with dashes)
        if not beneficiary:
            beneficiary = Beneficiary.objects.filter(
                account_number=account_number,
                company=company
            ).first()
        
        # Try to match by cleaning both sides for comparison
        if not beneficiary:
            for b in Beneficiary.objects.filter(company=company):
                db_clean = b.account_number.replace('-', '').replace(' ', '')
                if db_clean == clean_account:
                    beneficiary = b
                    break
        
        # Hungarian banking rule: 3x8 format with trailing zeros = 2x8 format
        # Example: 66000169-11088406-00000000 = 66000169-11088406
        if not beneficiary and len(clean_account) == 24:
            # Check if third block is all zeros
            if clean_account[16:24] == '00000000':
                short_account = clean_account[:16]  # First 16 digits (2x8 format)
                
                # Try to find beneficiary with 2x8 format
                for b in Beneficiary.objects.filter(company=company):
                    db_clean = b.account_number.replace('-', '').replace(' ', '')
                    if db_clean == short_account:
                        beneficiary = b
                        break
                        
                # Also try formatted versions
                if not beneficiary:
                    formatted_short = f"{short_account[:8]}-{short_account[8:16]}"
                    beneficiary = Beneficiary.objects.filter(
                        account_number=formatted_short,
                        company=company
                    ).first()
        
        # Reverse check: if we have 2x8 format, check for 3x8 with trailing zeros
        elif not beneficiary and len(clean_account) == 16:
            extended_account = clean_account + '00000000'  # Add trailing zeros
            
            for b in Beneficiary.objects.filter(company=company):
                db_clean = b.account_number.replace('-', '').replace(' ', '')
                if db_clean == extended_account:
                    beneficiary = b
                    break
                    
            # Also try formatted version
            if not beneficiary:
                formatted_extended = f"{clean_account[:8]}-{clean_account[8:16]}-00000000"
                beneficiary = Beneficiary.objects.filter(
                    account_number=formatted_extended,
                    company=company
                ).first()
        
        # Only match by exact account number - no name-based fallback
        # This prevents different people with same names from being consolidated
        return beneficiary  # Returns None if no match found
    
    def find_matching_beneficiary_by_vat(self, vat_number: str, name: str = None, company=None) -> Optional[Beneficiary]:
        """Find existing beneficiary by VAT number"""
        if not vat_number or not company:
            return None
        
        # Clean VAT number for matching (remove spaces and dashes)
        clean_vat = vat_number.replace('-', '').replace(' ', '')
        
        # Try exact VAT number match first
        beneficiary = Beneficiary.objects.filter(
            vat_number=clean_vat,
            company=company
        ).first()
        
        # Try with original format (in case it's stored with dashes)
        if not beneficiary:
            beneficiary = Beneficiary.objects.filter(
                vat_number=vat_number,
                company=company
            ).first()
        
        # Try to match by cleaning both sides for comparison
        if not beneficiary:
            for b in Beneficiary.objects.filter(company=company).exclude(vat_number__isnull=True).exclude(vat_number=''):
                db_clean_vat = b.vat_number.replace('-', '').replace(' ', '') if b.vat_number else ''
                if db_clean_vat == clean_vat:
                    beneficiary = b
                    break
        
        # Log the match result for debugging
        if beneficiary:
            print(f"DEBUG: Found beneficiary match by VAT: {beneficiary.name} (VAT: {beneficiary.vat_number}) for PDF VAT: {vat_number}")
        else:
            print(f"DEBUG: No beneficiary found for VAT number: {vat_number}")
        
        return beneficiary
    
    def create_template(self, transactions: List[Dict], template_name: str = None, company_name: str = None, company=None) -> TransferTemplate:
        """Create new transfer template"""
        if not template_name:
            # Auto-generate name based on company name and current date
            current_date = datetime.now()
            if company_name and company_name != "Ismeretlen cég":
                template_name = f"{company_name} - {current_date.strftime('%Y-%m')}"
            else:
                template_name = f"Monthly Payments {current_date.strftime('%Y-%m')}"
        
        template = TransferTemplate.objects.create(
            name=template_name,
            description=f"Generated from PDF import - {len(transactions)} beneficiaries",
            is_active=True,
            company=company
        )
        
        return template
    
    def find_matching_template(self, transactions: List[Dict], company=None) -> TransferTemplate:
        """
        Find existing template that has EXACTLY the same beneficiaries as PDF transactions
        
        Args:
            transactions: List of transaction dictionaries with beneficiary info
            
        Returns:
            TransferTemplate instance if exact match found, None otherwise
        """
        # Get unique identifiers from transactions (account numbers OR VAT numbers)
        pdf_identifiers = set()
        for transaction in transactions:
            if 'account_number' in transaction:
                # Account-based transaction
                account_number = transaction['account_number'].replace('-', '').replace(' ', '')
                # Normalize account number - remove trailing zeros for comparison
                normalized_account = self._normalize_account_number(account_number)
                pdf_identifiers.add(f"account:{normalized_account}")
            elif 'vat_number' in transaction:
                # VAT-based transaction
                vat_number = transaction['vat_number'].replace('-', '').replace(' ', '')
                pdf_identifiers.add(f"vat:{vat_number}")
            else:
                # Skip transactions without identifiers
                continue
        
        print(f"DEBUG: PDF has {len(pdf_identifiers)} unique identifiers: {sorted(list(pdf_identifiers))}")
        
        # Find templates with EXACTLY the same beneficiaries (filtered by company)
        templates = TransferTemplate.objects.filter(is_active=True, company=company).prefetch_related(
            'template_beneficiaries__beneficiary'
        ).order_by('-created_at')  # Check newest templates first
        
        for template in templates:
            # Get identifiers from template beneficiaries  
            template_identifiers = set()
            for tb in template.template_beneficiaries.filter(is_active=True):
                # Add account identifier if present
                if tb.beneficiary.account_number:
                    account_number = tb.beneficiary.account_number.replace('-', '').replace(' ', '')
                    normalized_account = self._normalize_account_number(account_number)
                    template_identifiers.add(f"account:{normalized_account}")
                
                # Add VAT identifier if present
                if tb.beneficiary.vat_number:
                    vat_number = tb.beneficiary.vat_number.replace('-', '').replace(' ', '')
                    template_identifiers.add(f"vat:{vat_number}")
            
            print(f"DEBUG: Template '{template.name}' has {len(template_identifiers)} identifiers: {sorted(list(template_identifiers))}")
            
            # EXACT match only - same number of identifiers AND same identifiers
            if (len(pdf_identifiers) == len(template_identifiers) and 
                pdf_identifiers == template_identifiers):
                print(f"DEBUG: Found EXACT template match: '{template.name}' - same {len(pdf_identifiers)} identifiers")
                return template
            else:
                print(f"DEBUG: Template '{template.name}' does not match - different identifiers or count")
        
        print("DEBUG: No exact matching template found - will create new one")
        return None
    
    def _normalize_account_number(self, account_number: str) -> str:
        """
        Normalize Hungarian account number for comparison
        
        Hungarian account numbers can be in:
        - 16 digit format: 1210001111409520 (bank + account)
        - 24 digit format: 121000111140952000000000 (bank + account + padding zeros)
        
        This normalizes to 16-digit format by removing trailing zeros
        """
        clean_account = account_number.replace('-', '').replace(' ', '')
        
        if len(clean_account) == 24:
            # Remove trailing zeros from 24-digit format to get 16-digit format
            # Find the position where trailing zeros start
            i = 23  # Start from the end
            while i >= 16 and clean_account[i] == '0':
                i -= 1
            # Keep everything up to the last non-zero digit, but at least 16 digits
            normalized = clean_account[:max(16, i + 1)]
        else:
            # Already in correct format or other format
            normalized = clean_account
        
        return normalized
    
    def update_template_beneficiaries(self, template: TransferTemplate, transactions: List[Dict], company=None):
        """Update template with beneficiaries from transactions - merge with existing, support VAT-based matching"""
        # Don't clear existing beneficiaries - merge instead
        # Get existing beneficiaries in the template
        existing_beneficiaries = {}
        for tb in template.template_beneficiaries.all():
            # Create keys based on available identifiers
            if tb.beneficiary.account_number:
                clean_account = tb.beneficiary.account_number.replace('-', '').replace(' ', '')
                existing_beneficiaries[f"account:{clean_account}"] = tb
            if tb.beneficiary.vat_number:
                clean_vat = tb.beneficiary.vat_number.replace('-', '').replace(' ', '')
                existing_beneficiaries[f"vat:{clean_vat}"] = tb
        
        # Group transactions by beneficiary to handle duplicates
        beneficiary_data = {}
        
        for transaction in transactions:
            # Create beneficiary if doesn't exist
            if transaction.get('created_beneficiary', False):
                # Create beneficiary with appropriate fields based on transaction type
                create_data = {
                    'name': transaction['beneficiary_name'],
                    'is_frequent': True,
                    'is_active': True,
                    'company': company
                }
                
                # Add account number if provided
                if 'account_number' in transaction:
                    clean_account = clean_account_number(transaction['account_number'])
                    create_data['account_number'] = clean_account
                
                # Add VAT number if provided
                if 'vat_number' in transaction:
                    create_data['vat_number'] = transaction['vat_number']
                
                # For VAT-based transactions without account, we need to get account from somewhere
                # This is a limitation - VAT-only beneficiaries need account numbers for transfers
                if 'vat_number' in transaction and 'account_number' not in transaction:
                    # This will be handled later - beneficiary created without account number
                    # User will need to add account number before generating transfers
                    print(f"DEBUG: Creating VAT-only beneficiary '{transaction['beneficiary_name']}' - account number required for transfers")
                
                beneficiary = Beneficiary.objects.create(**create_data)
                beneficiary_id = beneficiary.id
            else:
                beneficiary_id = transaction['beneficiary_id']
            
            # If beneficiary already exists in our template, sum the amounts
            if beneficiary_id in beneficiary_data:
                beneficiary_data[beneficiary_id]['amount'] += Decimal(str(transaction['amount']))
                # Keep longest remittance info
                if len(transaction['remittance_info']) > len(beneficiary_data[beneficiary_id]['remittance']):
                    beneficiary_data[beneficiary_id]['remittance'] = transaction['remittance_info']
            else:
                beneficiary_data[beneficiary_id] = {
                    'amount': Decimal(str(transaction['amount'])),
                    'remittance': transaction['remittance_info']
                }
        
        # Create or update template beneficiaries
        for beneficiary_id, data in beneficiary_data.items():
            # Get the execution date from the first transaction for this beneficiary
            execution_date = None
            for transaction in transactions:
                if (transaction.get('beneficiary_id') == beneficiary_id or 
                    (not transaction.get('beneficiary_id') and 
                     transaction.get('beneficiary_name') == data.get('beneficiary_name'))):
                    execution_date = transaction.get('execution_date')
                    print(f"DEBUG: Found transaction execution_date for beneficiary {beneficiary_id}: {execution_date}")
                    break
            
            # Convert string date to date object for database storage
            from datetime import datetime
            if execution_date:
                try:
                    if isinstance(execution_date, str):
                        execution_date = datetime.strptime(execution_date, '%Y-%m-%d').date()
                        print(f"DEBUG: Converted execution_date string to date object: {execution_date}")
                except ValueError as e:
                    print(f"DEBUG: Error converting execution_date '{execution_date}': {e}")
                    execution_date = datetime.now().date()  # Fallback to today
            else:
                # No execution date found in PDF - use today's date
                execution_date = datetime.now().date()
                print(f"DEBUG: No execution_date in PDF - using today's date: {execution_date}")
            
            # Check if this beneficiary already exists in template
            beneficiary = Beneficiary.objects.get(id=beneficiary_id)
            
            # Try to find existing template beneficiary by account or VAT number
            existing_tb = None
            if beneficiary.account_number:
                clean_account = beneficiary.account_number.replace('-', '').replace(' ', '')
                existing_tb = existing_beneficiaries.get(f"account:{clean_account}")
            if not existing_tb and beneficiary.vat_number:
                clean_vat = beneficiary.vat_number.replace('-', '').replace(' ', '')
                existing_tb = existing_beneficiaries.get(f"vat:{clean_vat}")
            
            if existing_tb:
                # Update existing template beneficiary
                existing_tb.default_amount = data['amount']
                existing_tb.default_remittance = data['remittance']
                # Always update execution date - use new date or today if no date in PDF
                existing_tb.default_execution_date = execution_date
                existing_tb.save()
                print(f"DEBUG: Updated existing beneficiary '{beneficiary.name}' in template with execution date: {execution_date}")
            else:
                # Create new template beneficiary
                TemplateBeneficiary.objects.create(
                    template=template,
                    beneficiary_id=beneficiary_id,
                    default_amount=data['amount'],
                    default_remittance=data['remittance'],
                    default_execution_date=execution_date
                )
                print(f"DEBUG: Added new beneficiary '{beneficiary.name}' to template")
    
    def is_invoice_pdf(self, text: str) -> bool:
        """
        Detect if PDF is an invoice based on common Hungarian invoice keywords
        
        Args:
            text: Raw PDF text
            
        Returns:
            True if PDF appears to be an invoice
        """
        # Clean up text for better matching
        lower_text = text.lower()
        
        # Hungarian invoice keywords
        invoice_keywords = [
            'számla',           # Invoice
            'számlaszám',       # Invoice number
            'teljesítés dátuma',# Performance date
            'fizetési határidő', # Payment deadline
            'bruttó összeg',    # Gross amount
            'nettó összeg',     # Net amount
            'áfa',              # VAT
            'kedvezményezett',  # Beneficiary
            'számla kiállítója',# Invoice issuer
            'számla címzettje', # Invoice recipient
            'összesen fizetendő',# Total payable
            'fizetési mód',     # Payment method
            'bankszámla',       # Bank account
            'swift',            # SWIFT code
            'iban'              # IBAN
        ]
        
        # Check for invoice-specific patterns
        invoice_patterns = [
            r'számla\s*sz[áa]m[:\s]',     # Invoice number pattern
            r'\d{4}[-/]\d{2}[-/]\d{2}',   # Date patterns
            r'ft\b|huf\b',                 # Currency indicators
            r'áfa\s*\d+%',                # VAT percentage
            r'bruttó|netto',              # Gross/Net
            r'kedvezmény[a-zA-ZáéíóöőüűÁÉÍÓÖŐÜŰ]*', # Discount variations
        ]
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in invoice_keywords if keyword in lower_text)
        pattern_matches = sum(1 for pattern in invoice_patterns if re.search(pattern, lower_text))
        
        # Invoice if we have enough indicators (at least 3 keywords or 2 patterns)
        return keyword_matches >= 3 or pattern_matches >= 2
    
    def parse_invoice_pdf(self, text: str) -> Dict[str, Any]:
        """
        Parse invoice PDF and extract payment information
        
        Args:
            text: Raw PDF text from invoice
            
        Returns:
            Dictionary with invoice transaction data
        """
        transactions = []
        
        # Extract invoice basic info
        invoice_info = self.extract_invoice_info(text)
        
        # Try to extract payment details
        payment_info = self.extract_invoice_payment_details(text)
        
        if payment_info:
            # Create transaction from invoice data
            # Use invoice number as remittance info (priority: extracted from invoice_info)
            remittance_info = invoice_info.get('invoice_number', 'Számla')
            if not remittance_info or remittance_info == 'Számla':
                remittance_info = payment_info.get('invoice_number', 'Számla')
            
            execution_date = payment_info.get('due_date') or invoice_info.get('due_date') or self.get_default_payment_date()
            print(f"DEBUG: Final execution_date for transaction: {execution_date}")
            print(f"DEBUG: payment_info due_date: {payment_info.get('due_date')}")
            print(f"DEBUG: invoice_info due_date: {invoice_info.get('due_date')}")
            
            transaction = {
                'beneficiary_name': payment_info.get('beneficiary_name', 'Számla kedvezményezett'),
                'account_number': payment_info.get('account_number', ''),
                'amount': payment_info.get('amount', 0),
                'remittance_info': remittance_info,
                'execution_date': execution_date
            }
            
            # Only add if we have essential info
            if transaction['amount'] > 0 and transaction['account_number']:
                transactions.append(transaction)
        
        return {
            'pdf_type': 'invoice',
            'transactions': transactions,
            'invoice_info': invoice_info,
            'due_date': invoice_info.get('due_date')
        }
    
    def extract_invoice_info(self, text: str) -> Dict[str, Any]:
        """Extract basic invoice information"""
        info = {}
        
        # Extract invoice number - based on actual PDF structure
        # In the PDF: "Számlaszám Fizetési mód\nKI25/00842 Átutalás"
        
        # First try the simplest approach - just look for the KI25/00842 pattern anywhere
        simple_invoice_pattern = re.search(r'([A-Z]{2}\d{2}/\d{5})', text)
        if simple_invoice_pattern:
            info['invoice_number'] = simple_invoice_pattern.group(1)
            print(f"DEBUG: Found invoice number '{simple_invoice_pattern.group(1)}' with simple pattern")
        else:
            # More complex patterns as fallback
            invoice_num_patterns = [
                r'számlaszám[:\s]*([A-Z0-9\-/]+)',                    # "Számlaszám KI25/00842"
                r'számlaszám[:\s\n\r]*([A-Z0-9\-/]+)',               # "Számlaszám\nKI25/00842" (table format)
                r'számla\s*sz[áa]m[:\s]*([A-Z0-9\-/]+)',             # "Számla szám: KI25/00842"  
                r'([A-Z]{1,4}\d{1,4}/\d{4,6})',                     # Pattern like "KI25/00842" 
                r'([A-Z]{1,3}-\d{2,4}-\d{5,6})'                     # Pattern like "KI-25-00842"
            ]
            
            for pattern in invoice_num_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['invoice_number'] = match.group(1).strip()
                    print(f"DEBUG: Found invoice number '{match.group(1).strip()}' with pattern: {pattern}")
                    break
        
        # If no invoice number found yet, try a more aggressive search
        if 'invoice_number' not in info:
            # Look for any pattern that looks like an invoice number near "Számlaszám"
            # Split text into lines and look for the line after "Számlaszám"
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'számlaszám' in line.lower():
                    # Look at current line and next few lines for invoice number
                    for j in range(max(0, i), min(len(lines), i+3)):
                        check_line = lines[j].strip()
                        # Look for invoice number patterns in this line
                        invoice_match = re.search(r'([A-Z]{1,4}\d{1,4}/\d{4,6})', check_line)
                        if invoice_match and invoice_match.group(1).lower() != 'számlaszám':
                            info['invoice_number'] = invoice_match.group(1).strip()
                            print(f"DEBUG: Found invoice number '{invoice_match.group(1).strip()}' in line: {check_line}")
                            break
                    if 'invoice_number' in info:
                        break
        
        # Extract dates - based on table structure: "Számla kelte Teljesítés kelte Fizetési határidő"
        # followed by: "2025.07.02 2025.07.12 2025.07.12"
        
        # Look for lines with "Fizetési határidő" and get the third date in the next line
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'fizetési határidő' in line.lower():
                # Check the next line for dates
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Look for pattern: date date date (third one is payment deadline)
                    date_matches = re.findall(r'(\d{4}[-./]\d{2}[-./]\d{2})', next_line)
                    if len(date_matches) >= 3:
                        # Third date is payment deadline
                        date_str = date_matches[2].replace('/', '-').replace('.', '-')
                        info['due_date'] = date_str
                        print(f"DEBUG: Found payment deadline '{date_str}' in table format")
                        break
                    elif len(date_matches) >= 1:
                        # If only one date, use it
                        date_str = date_matches[-1].replace('/', '-').replace('.', '-')
                        info['due_date'] = date_str
                        print(f"DEBUG: Found single date '{date_str}' near Fizetési határidő")
                        break
        
        # Fallback to simple pattern matching if table format didn't work
        if 'due_date' not in info:
            date_patterns = [
                r'fizetési\s*határidő[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})',  
                r'(\d{4}[-./]\d{2}[-./]\d{2})'  # Any date pattern as last resort
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    date_str = matches[-1].replace('/', '-').replace('.', '-')  # Take last date found
                    info['due_date'] = date_str
                    print(f"DEBUG: Found fallback due date '{date_str}'")
                    break
        
        # Default due date if not found
        if 'due_date' not in info:
            info['due_date'] = self.get_default_payment_date()
        
        return info
    
    def extract_invoice_payment_details(self, text: str) -> Dict[str, Any]:
        """Extract payment details from invoice"""
        payment_info = {}
        
        # Extract total amount - look for "Fizetendő:" or "Bruttó" patterns
        amount_patterns = [
            r'fizetendő[:\s]*([0-9\s,.]+)\s*ft',        # "Fizetendő: 61.976 Ft"
            r'([0-9\s,.]+)\s*ft\s*$',                    # "61.976 Ft" at end of line
            r'bruttó[:\s]*([0-9\s,.]+)',                 # "Bruttó 61.976"
            r'összesen\s*fizetendő[:\s]*([0-9\s,.]+)',   # "Összesen fizetendő 61.976"
            r'végösszeg[:\s]*([0-9\s,.]+)\s*ft'          # "Végösszeg: 61.976 Ft"
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                amount_str = match.replace(' ', '').replace(',', '').replace('.', '')
                try:
                    amount = float(amount_str)
                    if amount > 0:  # Only accept positive amounts
                        payment_info['amount'] = amount
                        break
                except ValueError:
                    continue
            if 'amount' in payment_info:
                break
        
        # Extract beneficiary name from "Eladó neve és címe:" section
        # Look for company name patterns in the seller section
        beneficiary_patterns = [
            # Pattern 1: Look for lines after "Eladó neve és címe:" 
            r'eladó\s+neve\s+és\s+címe[:\s]*[\r\n]+([A-ZÁÉÍÓÖŐÜŰa-záéíóöőüű\s]+(?:Kft|Bt|Zrt|Nyrt)\.?)',
            # Pattern 2: Look for company names with Kft/Zrt/Bt before an address
            r'([A-ZÁÉÍÓÖŐÜŰa-záéíóöőüű\s]+(?:Kft|Bt|Zrt|Nyrt)\.?)\s*[\r\n]+\d{4}',  # Company followed by postal code
            # Pattern 3: Direct match for common company patterns
            r'^([A-ZÁÉÍÓÖŐÜŰa-záéíóöőüű][A-Za-záéíóöőüű\s]+(?:Kft|Bt|Zrt|Nyrt)\.?)$'
        ]
        
        for pattern in beneficiary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                company_name = match.group(1).strip()
                # Clean up any extra whitespace
                company_name = re.sub(r'\s+', ' ', company_name)
                if len(company_name) > 5:  # Ensure it's a meaningful name
                    payment_info['beneficiary_name'] = company_name
                    break
        
        # Extract account number from "Bank:" line
        # Look for patterns like "Bank: 66000169-11088406-00000000"
        account_patterns = [
            r'bank[:\s]+([0-9]{8}-[0-9]{8}-[0-9]{8})',           # 3x8 format with dashes
            r'bank[:\s]+([0-9]{8}-[0-9]{8})',                    # 2x8 format with dashes  
            r'bank[:\s]+([0-9]{24})',                            # 24 digits no dashes
            r'bank[:\s]+([0-9]{16})',                            # 16 digits no dashes
            r'([0-9]{8}-[0-9]{8}-[0-9]{8})',                    # Any 3x8 format in text
            r'([0-9]{8}-[0-9]{8})'                              # Any 2x8 format in text
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_account = match.group(1).strip()
                # Validate and format the account number
                account_validation = self.validate_and_format_account_number(raw_account)
                if account_validation['is_valid']:
                    payment_info['account_number'] = account_validation['formatted']
                    break
        
        return payment_info
    
    def get_default_payment_date(self) -> str:
        """Get default payment date (today)"""
        from datetime import datetime
        default_date = datetime.now()
        return default_date.strftime('%Y-%m-%d')