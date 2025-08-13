"""
PDF Transaction Processor
Extracts transaction data from Hungarian payment PDFs (NAV tax and salary documents)
"""

import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Tuple
from django.core.files.uploadedfile import UploadedFile

from .models import Beneficiary, TransferTemplate, TemplateBeneficiary


class PDFTransactionProcessor:
    """Process Hungarian payment PDFs and extract transaction data"""
    
    def __init__(self):
        self.supported_formats = ['tax_payments', 'salary_payments']
    
    def process_pdf_files(self, pdf_files: List[UploadedFile], template_name: str = None, template_id: int = None) -> Dict[str, Any]:
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
        
        # Step 1: Extract data from all PDFs
        for pdf_file in pdf_files:
            try:
                pdf_data = self.extract_pdf_data(pdf_file)
                transactions = pdf_data['transactions']  # transactions are already parsed in extract_pdf_data
                all_transactions.extend(transactions)
            except Exception as e:
                raise ValueError(f"Failed to process {pdf_file.name}: {str(e)}")
        
        # Step 2: Match beneficiaries and consolidate transactions
        all_transactions, consolidation_msgs = self.match_and_consolidate_beneficiaries(all_transactions)
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
            existing_template = self.find_matching_template(all_transactions)
            
            if existing_template:
                template = existing_template
                template_created = False
                consolidations.append(f"Meglévő sablon frissítése: '{template.name}'")
            else:
                template = self.create_template(all_transactions, template_name)
                template_created = True
        
        # Step 4: Update template with transactions
        self.update_template_beneficiaries(template, all_transactions)
        
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
            'template_updated': existing_template is not None,
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
            
            # Detect PDF type based on content
            if "Adó és járulék befizetések" in text:
                return self.parse_tax_pdf(text)
            elif "Banki utalások" in text or "utalások" in text.lower():
                return self.parse_salary_pdf(text)
            else:
                raise ValueError(f"Unknown PDF format in {pdf_file.name}")
                
        except Exception as e:
            raise ValueError(f"Failed to read PDF {pdf_file.name}: {str(e)}")
    
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
            # Default to next month 12th
            due_date = "2025-08-12"
        
        # Extract NAV transactions using table structure
        # Look for the table with Adónem kód, Számlaszám, Befizetendő forint
        # NAV accounts use 2x8 format (10032000-06055950)
        table_pattern = r'(.+?)\s+(\d{3})\s+(\d{8}-\d{8})\s+([\d\s]+)'
        matches = re.findall(table_pattern, text)
        
        seen_transactions = set()  # Prevent duplicates
        
        for match in matches:
            description, code, account, amount_str = match
            
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
                            
                            transactions.append({
                                'beneficiary_name': beneficiary_name,
                                'account_number': account,
                                'amount': amount,
                                'remittance_info': company_tax_id,
                                'execution_date': due_date
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
        
        # Extract execution date (default to current month 15th)
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', text)
        if date_match:
            year, month, day = date_match.groups()
            due_date = f"{year}-{month}-15"  # Mid-month for salaries
        else:
            due_date = "2025-08-15"
        
        # Pattern for salary lines: [number]. [name] [tax_id] [account] [amount]
        # Bank accounts use 3x8 format (12100011-11409520-00000000)
        salary_pattern = r'\d+\.\s+(.+?)\s+(\d{10})\s+(\d{8}-\d{8}-\d{8})\s+([\d,]+)'
        matches = re.findall(salary_pattern, text)
        
        for match in matches:
            name, tax_id, account, amount_str = match
            amount = float(amount_str.replace(',', '').replace(' ', ''))
            
            if amount > 0:
                transactions.append({
                    'beneficiary_name': name.strip(),
                    'account_number': account,
                    'amount': amount,
                    'remittance_info': 'jövedelem',  # Default for salary
                    'execution_date': due_date
                })
        
        return {
            'pdf_type': 'salary_payments',
            'transactions': transactions,
            'due_date': due_date
        }
    
    def match_and_consolidate_beneficiaries(self, transactions: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Match transactions to existing beneficiaries and consolidate duplicates"""
        consolidations = []
        matched_transactions = []
        
        # Group transactions by beneficiary name and account
        grouped = {}
        for transaction in transactions:
            key = (transaction['beneficiary_name'], transaction['account_number'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(transaction)
        
        for (name, account), trans_group in grouped.items():
            # Try to match existing beneficiary
            beneficiary = self.find_matching_beneficiary(account, name)
            
            if len(trans_group) > 1:
                # Consolidate multiple transactions to same beneficiary
                total_amount = sum(t['amount'] for t in trans_group)
                
                # Special handling for Tóth István 116 account
                if '116' in account and 'tóth' in name.lower():
                    remittance_info = 'jövedelem + bérleti díj'
                else:
                    remittance_info = trans_group[0]['remittance_info']
                
                consolidations.append(f"{name} ({account[:8]}...): {len(trans_group)} transfers merged into {total_amount:,.0f} HUF")
                
                matched_transactions.append({
                    'beneficiary_id': beneficiary.id if beneficiary else None,
                    'beneficiary_name': beneficiary.name if beneficiary else name,
                    'account_number': account,
                    'amount': total_amount,
                    'remittance_info': remittance_info,
                    'execution_date': trans_group[0]['execution_date'],
                    'created_beneficiary': beneficiary is None
                })
            else:
                # Single transaction
                transaction = trans_group[0]
                matched_transactions.append({
                    'beneficiary_id': beneficiary.id if beneficiary else None,
                    'beneficiary_name': beneficiary.name if beneficiary else transaction['beneficiary_name'],
                    'account_number': transaction['account_number'],
                    'amount': transaction['amount'],
                    'remittance_info': transaction['remittance_info'],
                    'execution_date': transaction['execution_date'],
                    'created_beneficiary': beneficiary is None
                })
        
        return matched_transactions, consolidations
    
    def find_matching_beneficiary(self, account_number: str, name: str = None) -> Beneficiary:
        """Find existing beneficiary by account number or name"""
        # Clean account number for matching (remove dashes and spaces)
        clean_account = account_number.replace('-', '').replace(' ', '')
        
        # Try exact full account match first (most reliable)
        beneficiary = Beneficiary.objects.filter(
            account_number=clean_account
        ).first()
        
        # Try with original format (with dashes)
        if not beneficiary:
            beneficiary = Beneficiary.objects.filter(
                account_number=account_number
            ).first()
        
        # Try to match by cleaning both sides for comparison
        if not beneficiary:
            for b in Beneficiary.objects.all():
                db_clean = b.account_number.replace('-', '').replace(' ', '')
                if db_clean == clean_account:
                    beneficiary = b
                    break
        
        # Only match by exact account number - no name-based fallback
        # This prevents different people with same names from being consolidated
        return beneficiary
    
    def create_template(self, transactions: List[Dict], template_name: str = None) -> TransferTemplate:
        """Create new transfer template"""
        if not template_name:
            # Auto-generate name based on current date
            current_date = datetime.now()
            template_name = f"Monthly Payments {current_date.strftime('%Y-%m')}"
        
        template = TransferTemplate.objects.create(
            name=template_name,
            description=f"Generated from PDF import - {len(transactions)} beneficiaries",
            is_active=True
        )
        
        return template
    
    def find_matching_template(self, transactions: List[Dict]) -> TransferTemplate:
        """
        Find existing template that matches the beneficiaries from PDF transactions
        
        Args:
            transactions: List of transaction dictionaries with beneficiary info
            
        Returns:
            TransferTemplate instance if match found, None otherwise
        """
        # Get unique account numbers from transactions
        pdf_account_numbers = set()
        for transaction in transactions:
            account_number = transaction['account_number'].replace('-', '').replace(' ', '')
            pdf_account_numbers.add(account_number)
        
        # Find templates that have exactly the same beneficiaries
        templates = TransferTemplate.objects.filter(is_active=True).prefetch_related(
            'template_beneficiaries__beneficiary'
        )
        
        for template in templates:
            # Get account numbers from template beneficiaries
            template_account_numbers = set()
            for tb in template.template_beneficiaries.all():
                account_number = tb.beneficiary.account_number.replace('-', '').replace(' ', '')
                template_account_numbers.add(account_number)
            
            # Check if sets match exactly
            if pdf_account_numbers == template_account_numbers:
                return template
        
        return None
    
    def update_template_beneficiaries(self, template: TransferTemplate, transactions: List[Dict]):
        """Update template with beneficiaries from transactions"""
        # Clear existing template beneficiaries
        TemplateBeneficiary.objects.filter(template=template).delete()
        
        # Group transactions by beneficiary to handle duplicates
        beneficiary_data = {}
        
        for transaction in transactions:
            # Create beneficiary if doesn't exist
            if transaction.get('created_beneficiary', False):
                beneficiary = Beneficiary.objects.create(
                    name=transaction['beneficiary_name'],
                    account_number=transaction['account_number'].replace('-', ''),
                    is_frequent=True,
                    is_active=True
                )
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
        
        # Create template beneficiaries
        for beneficiary_id, data in beneficiary_data.items():
            TemplateBeneficiary.objects.create(
                template=template,
                beneficiary_id=beneficiary_id,
                default_amount=data['amount'],
                default_remittance=data['remittance']
            )