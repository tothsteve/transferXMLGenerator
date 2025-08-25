"""
NAV Invoice Synchronization Service

This service provides READ-ONLY synchronization of invoice data from the Hungarian NAV system.
It queries invoice information but NEVER creates, modifies, or deletes anything in NAV.

Key Features:
- READ-ONLY operations only
- Multi-tenant support with company isolation
- Comprehensive error handling and logging
- Batch processing with progress tracking
- Data transformation from NAV XML to Django models

CRITICAL: This service only QUERIES data from NAV. It does not and must not
          perform any write operations (create, update, delete) to NAV system.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from django.utils import timezone as django_timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import (
    Company, NavConfiguration, Invoice, InvoiceLineItem, 
    InvoiceSyncLog
)
from .nav_client import NavApiClient
from .credential_manager import CredentialManager

logger = logging.getLogger(__name__)


class InvoiceSyncService:
    """
    READ-ONLY invoice synchronization service for NAV data.
    
    This service handles the business logic for querying invoice data from NAV
    and storing it locally. It maintains strict READ-ONLY operations and never
    modifies anything in the NAV system.
    """
    
    def __init__(self):
        self.credential_manager = CredentialManager()
        
    def sync_company_invoices(
        self, 
        company: Company, 
        date_from: datetime = None, 
        date_to: datetime = None,
        direction: str = 'OUTBOUND',
        environment: str = None,
        prefer_production: bool = True
    ) -> Dict:
        """
        Synchronize invoices for a specific company with environment selection.
        
        READ-ONLY OPERATION: Only queries data from NAV, never modifies NAV.
        
        Args:
            company: Company to sync invoices for
            date_from: Start date for invoice query (defaults to 30 days ago)
            date_to: End date for invoice query (defaults to today)
            direction: Invoice direction ('OUTBOUND' or 'INBOUND')
            environment: Specific environment ('production'/'test') or None for auto-select
            prefer_production: If True and environment=None, prefer production over test
            
        Returns:
            Dict with sync results: {
                'success': bool,
                'invoices_processed': int,
                'invoices_created': int,
                'invoices_updated': int,
                'errors': list,
                'sync_log_id': int
            }
        """
        
        # Default date range: last 30 days
        if not date_from:
            date_from = django_timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = django_timezone.now()
            
        # Initialize sync log
        sync_log = InvoiceSyncLog.objects.create(
            company=company,
            sync_start_time=django_timezone.now(),
            direction_synced=direction,
            sync_status='RUNNING',
            invoices_processed=0,
            invoices_created=0,
            invoices_updated=0
        )
        
        try:
            # Smart NAV configuration selection with environment awareness
            nav_config = self._get_nav_configuration(company, environment, prefer_production)
            if not nav_config:
                env_msg = f" in {environment} environment" if environment else ""
                raise ValueError(f"Nincs aktív NAV konfiguráció a {company.name} céghez{env_msg}")
            
            logger.info(f"🌍 Using {nav_config.api_environment} environment for {company.name}")
            
            # Initialize NAV client
            nav_client = self._initialize_nav_client(nav_config)
            
            # Test connection first
            if not nav_client.test_connection():
                raise Exception("NAV kapcsolat teszt sikertelen")
            
            # Query invoice digest from NAV (READ-ONLY)
            logger.info(f"NAV számla lekérdezés indítása: {company.name}, {date_from} - {date_to}")
            invoice_digest = nav_client.query_invoice_digest(
                date_from=date_from,
                date_to=date_to,
                direction=direction
            )
            
            # Process each invoice in the digest
            results = self._process_invoice_digest(
                nav_client=nav_client,
                company=company,
                invoice_digest=invoice_digest,
                sync_log=sync_log,
                direction=direction
            )
            
            # Update sync log with results
            sync_log.sync_end_time = django_timezone.now()
            sync_log.sync_status = 'COMPLETED'
            sync_log.invoices_processed = results['invoices_processed']
            sync_log.invoices_created = results['invoices_created']
            sync_log.invoices_updated = results['invoices_updated']
            sync_log.save()
            
            logger.info(f"NAV szinkronizáció befejezve: {company.name} - {results}")
            
            return {
                'success': True,
                'sync_log_id': sync_log.id,
                **results
            }
            
        except Exception as e:
            # Log error and update sync status
            error_message = str(e)
            logger.error(f"NAV szinkronizáció hiba: {company.name} - {error_message}")
            
            sync_log.sync_end_time = django_timezone.now()
            sync_log.sync_status = 'ERROR'
            sync_log.last_error_message = error_message
            sync_log.save()
            
            return {
                'success': False,
                'sync_log_id': sync_log.id,
                'invoices_processed': 0,
                'invoices_created': 0,
                'invoices_updated': 0,
                'errors': [error_message]
            }
    
    def _get_nav_configuration(self, company: Company) -> Optional[NavConfiguration]:
        """Get active NAV configuration for company."""
        return NavConfiguration.objects.filter(
            company=company,
            is_active=True,
            sync_enabled=True
        ).first()
    
    def _initialize_nav_client(self, nav_config: NavConfiguration) -> NavApiClient:
        """Initialize NAV client with configuration."""
        return NavApiClient(nav_config)
    
    def _process_invoice_digest(
        self, 
        nav_client: NavApiClient, 
        company: Company, 
        invoice_digest: List[Dict], 
        sync_log: InvoiceSyncLog,
        direction: str = 'INBOUND'
    ) -> Dict:
        """
        Process invoice digest and fetch detailed invoice data.
        
        READ-ONLY OPERATION: Only queries invoice details from NAV.
        """
        
        invoices_processed = 0
        invoices_created = 0
        invoices_updated = 0
        
        for digest_entry in invoice_digest:
            try:
                nav_invoice_number = digest_entry.get('invoiceNumber')
                if not nav_invoice_number:
                    continue
                
                # Extract supplier tax number and batch index from digest
                supplier_tax_number = digest_entry.get('supplierTaxNumber')
                batch_index = digest_entry.get('batchIndex', 1)
                
                # Debug: Log what data is available in the digest
                logger.info(f"📊 Digest data for {nav_invoice_number}: net={digest_entry.get('invoiceNetAmount', 'MISSING')}, vat={digest_entry.get('invoiceVatAmount', 'MISSING')}, gross={digest_entry.get('invoiceGrossAmount', 'MISSING')}, currency={digest_entry.get('currency', 'MISSING')}")
                logger.info(f"📊 All digest keys: {list(digest_entry.keys())}")
                
                # Check if invoice already exists
                existing_invoice = Invoice.objects.filter(
                    company=company,
                    nav_invoice_number=nav_invoice_number
                ).first()
                
                # Modern NAV approach: Query invoice chain FIRST, then detailed data
                # This follows the BIP pattern for proper invoice data retrieval
                try:
                    # Skip chain digest and query invoice data directly
                    # This avoids the chain metadata complexity that was causing 400 errors
                    logger.info(f"Querying detailed data directly for invoice: {nav_invoice_number}")
                    
                    version = None
                    operation = None
                    transaction_id = None
                    
                    detailed_invoice_data = nav_client.query_invoice_data(
                        nav_invoice_number, 
                        direction=direction, 
                        supplier_tax_number=supplier_tax_number,
                        batch_index=batch_index,
                        version=version,
                        operation=operation
                    )
                    
                    if detailed_invoice_data:
                        logger.info(f"✅ Detailed data received for {nav_invoice_number}: {list(detailed_invoice_data.keys()) if isinstance(detailed_invoice_data, dict) else type(detailed_invoice_data)}")
                        # Add chain metadata to detailed data
                        if transaction_id:
                            detailed_invoice_data['transaction_id'] = transaction_id
                        if version:
                            detailed_invoice_data['original_request_version'] = version
                        if operation:
                            detailed_invoice_data['invoice_operation'] = operation
                            
                        # Check if we got XML data
                        if 'nav_invoice_xml' in detailed_invoice_data:
                            logger.info(f"📄 XML data received for {nav_invoice_number} ({len(detailed_invoice_data['nav_invoice_xml'])} characters)")
                        if 'gross_amount' in detailed_invoice_data:
                            logger.info(f"💰 Gross amount from XML: {detailed_invoice_data['gross_amount']} {detailed_invoice_data.get('currency', 'HUF')}")
                    else:
                        logger.info(f"⚠️  No detailed data returned for {nav_invoice_number}")
                        
                except Exception as e:
                    # If chain or detailed query fails, continue with digest data only
                    logger.warning(f"❌ Advanced query failed for {nav_invoice_number}: {str(e)}")
                    detailed_invoice_data = None
                
                # Create invoice data from available information
                invoice_data = self._create_invoice_data_from_digest(
                    digest_entry, direction, detailed_invoice_data
                )
                
                if existing_invoice:
                    # Update existing invoice
                    self._update_invoice_from_nav_data(existing_invoice, invoice_data)
                    invoices_updated += 1
                    # Extract and save line items if we have XML data
                    if detailed_invoice_data and 'nav_invoice_xml' in detailed_invoice_data:
                        self._extract_and_save_line_items(existing_invoice, detailed_invoice_data['nav_invoice_xml'])
                else:
                    # Create new invoice
                    new_invoice = self._create_invoice_from_nav_data(company, invoice_data)
                    invoices_created += 1
                    # Extract and save line items if we have XML data
                    if detailed_invoice_data and 'nav_invoice_xml' in detailed_invoice_data:
                        self._extract_and_save_line_items(new_invoice, detailed_invoice_data['nav_invoice_xml'])
                
                invoices_processed += 1
                
                # Update progress in sync log periodically
                if invoices_processed % 10 == 0:
                    sync_log.invoices_processed = invoices_processed
                    sync_log.invoices_created = invoices_created
                    sync_log.invoices_updated = invoices_updated
                    sync_log.save()
                
            except Exception as e:
                logger.error(f"Hiba a számla feldolgozásában: {nav_invoice_number} - {str(e)}")
                continue
        
        return {
            'invoices_processed': invoices_processed,
            'invoices_created': invoices_created,
            'invoices_updated': invoices_updated,
            'errors': []
        }
    
    def _extract_and_save_line_items(self, invoice: Invoice, nav_invoice_xml: str):
        """
        Extract line items from NAV invoice XML and save to database.
        
        Args:
            invoice: Invoice instance to attach line items to
            nav_invoice_xml: Decoded NAV invoice XML string
        """
        try:
            import xml.etree.ElementTree as ET
            
            # Parse the XML
            root = ET.fromstring(nav_invoice_xml)
            
            # Clear existing line items for this invoice
            invoice.line_items.all().delete()
            
            # Find all line elements
            line_elements = root.findall('.//{http://schemas.nav.gov.hu/OSA/3.0/data}line')
            
            for line_elem in line_elements:
                line_data = {}
                
                # Helper function to get text from element
                def get_line_text(tag_name):
                    namespace = "http://schemas.nav.gov.hu/OSA/3.0/data"
                    elem = line_elem.find(f'.//{{{namespace}}}{tag_name}')
                    return elem.text if elem is not None else None
                
                # Extract line information
                line_number = get_line_text('lineNumber')
                if line_number:
                    line_data['line_number'] = int(line_number)
                else:
                    continue  # Skip if no line number
                
                line_data['line_description'] = get_line_text('lineDescription') or ''
                
                # Extract quantity and unit info
                quantity_text = get_line_text('quantity')
                if quantity_text:
                    try:
                        line_data['quantity'] = Decimal(quantity_text)
                    except:
                        line_data['quantity'] = None
                else:
                    line_data['quantity'] = None
                
                line_data['unit_of_measure'] = get_line_text('unitOfMeasure') or ''
                
                # Extract unit price
                unit_price_text = get_line_text('unitPrice')
                if unit_price_text:
                    try:
                        line_data['unit_price'] = Decimal(unit_price_text)
                    except:
                        line_data['unit_price'] = None
                else:
                    line_data['unit_price'] = None
                
                # Extract line net amount (required field)
                line_net_text = get_line_text('lineNetAmount')
                if line_net_text:
                    try:
                        line_data['line_net_amount'] = Decimal(line_net_text)
                    except:
                        line_data['line_net_amount'] = Decimal('0.00')
                else:
                    # Try to get from simplified amount structure
                    line_gross_text = get_line_text('lineGrossAmountSimplified')
                    if line_gross_text:
                        try:
                            # For simplified invoices, use gross amount as approximation
                            line_data['line_net_amount'] = Decimal(line_gross_text)
                        except:
                            line_data['line_net_amount'] = Decimal('0.00')
                    else:
                        line_data['line_net_amount'] = Decimal('0.00')
                
                # Extract line VAT amount
                line_vat_text = get_line_text('lineVatAmount')
                if line_vat_text:
                    try:
                        line_data['line_vat_amount'] = Decimal(line_vat_text)
                    except:
                        line_data['line_vat_amount'] = Decimal('0.00')
                else:
                    line_data['line_vat_amount'] = Decimal('0.00')
                
                # Extract line gross amount
                line_gross_text = get_line_text('lineGrossAmount') or get_line_text('lineGrossAmountSimplified')
                if line_gross_text:
                    try:
                        line_data['line_gross_amount'] = Decimal(line_gross_text)
                    except:
                        line_data['line_gross_amount'] = Decimal('0.00')
                else:
                    line_data['line_gross_amount'] = Decimal('0.00')
                
                # Create the line item
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    line_number=line_data['line_number'],
                    line_description=line_data['line_description'],
                    quantity=line_data['quantity'],
                    unit_of_measure=line_data['unit_of_measure'],
                    unit_price=line_data['unit_price'],
                    line_net_amount=line_data['line_net_amount'],
                    line_vat_amount=line_data['line_vat_amount'],
                    line_gross_amount=line_data['line_gross_amount']
                )
            
            # Log line items created
            line_count = invoice.line_items.count()
            logger.info(f"📝 Extracted {line_count} line items for invoice {invoice.nav_invoice_number}")
            
        except Exception as e:
            logger.error(f"❌ Failed to extract line items for invoice {invoice.nav_invoice_number}: {str(e)}")
    
    def _create_invoice_data_from_digest(self, digest_entry: Dict, direction: str, detailed_data: Dict = None) -> Dict:
        """Create comprehensive invoice data from digest and detailed information."""
        from django.utils import timezone
        from decimal import Decimal
        
        # Extract ALL available data from digest (NAV provides complete business data here!)
        invoice_data = {
            'invoice_number': digest_entry.get('invoiceNumber', ''),
            'invoice_direction': direction,
            'supplier_name': digest_entry.get('supplierName', ''),
            'supplier_tax_number': digest_entry.get('supplierTaxNumber', ''),
            'customer_name': digest_entry.get('customerName', ''),
            'customer_tax_number': digest_entry.get('customerTaxNumber', ''),
            'batch_index': digest_entry.get('batchIndex', 1),
            
            # Real dates from NAV
            'issue_date': digest_entry.get('invoiceIssueDate', ''),  # Real issue date
            'payment_due_date': digest_entry.get('paymentDate', ''),
            'fulfillment_date': digest_entry.get('invoiceDeliveryDate', ''),
            'nav_creation_date': digest_entry.get('insDate', ''),  # When created in NAV
            
            # Real amounts from NAV
            'currency': digest_entry.get('currency', 'HUF'),
            'net_amount': self._safe_decimal(digest_entry.get('invoiceNetAmount', '0')),
            'vat_amount': self._safe_decimal(digest_entry.get('invoiceVatAmount', '0')),
            'gross_amount': self._calculate_gross_amount(digest_entry),
            
            # Additional NAV metadata (now stored in database!)
            'invoice_operation': digest_entry.get('invoiceOperation', ''),
            'invoice_category': digest_entry.get('invoiceCategory', ''),
            'payment_method': digest_entry.get('paymentMethod', ''),
            'payment_date': digest_entry.get('paymentDate', ''),
            'invoice_appearance': digest_entry.get('invoiceAppearance', ''),
            'nav_source': digest_entry.get('source', ''),
            'completeness_indicator': self._parse_boolean(digest_entry.get('completenessIndicator', '')),
            'modification_index': self._safe_integer(digest_entry.get('modificationIndex', '')),
            'original_invoice_number': digest_entry.get('originalInvoiceNumber', ''),
            'invoice_index': self._safe_integer(digest_entry.get('index', '')),
            'nav_creation_date': digest_entry.get('insDate', ''),
            'transaction_id': digest_entry.get('transactionId', ''),
            
            # HUF amounts for foreign currency invoices
            'net_amount_huf': self._safe_decimal(digest_entry.get('invoiceNetAmountHUF', '')),
            'vat_amount_huf': self._safe_decimal(digest_entry.get('invoiceVatAmountHUF', '')),
            
            # Default for required field
            'last_modified_date': timezone.now().isoformat(),
        }
        
        # Override with detailed data if available (but digest has everything we need!)
        if detailed_data:
            invoice_data.update(detailed_data)
        
        return invoice_data
    
    def _safe_decimal(self, value: str) -> float:
        """Safely convert string to decimal/float."""
        if not value:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_gross_amount(self, digest_entry: Dict) -> float:
        """Calculate gross amount from net + VAT amounts."""
        net = self._safe_decimal(digest_entry.get('invoiceNetAmount', '0'))
        vat = self._safe_decimal(digest_entry.get('invoiceVatAmount', '0'))
        return net + vat
    
    def _safe_integer(self, value: str) -> int:
        """Safely convert string to integer."""
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_boolean(self, value: str) -> bool:
        """Parse string to boolean."""
        if not value:
            return None
        return str(value).lower() in ('true', '1', 'yes')
    
    @transaction.atomic
    def _create_invoice_from_nav_data(self, company: Company, nav_data: Dict) -> Invoice:
        """Create new invoice from NAV data."""
        
        invoice = Invoice.objects.create(
            company=company,
            nav_invoice_number=nav_data.get('invoice_number', ''),
            invoice_direction=nav_data.get('invoice_direction', 'INBOUND'),
            supplier_name=nav_data.get('supplier_name', ''),
            supplier_tax_number=nav_data.get('supplier_tax_number', ''),
            customer_name=nav_data.get('customer_name', ''),
            customer_tax_number=nav_data.get('customer_tax_number', ''),
            issue_date=self._parse_nav_date(nav_data.get('issue_date')),
            fulfillment_date=self._parse_nav_date(nav_data.get('fulfillment_date')),
            payment_due_date=self._parse_nav_date(nav_data.get('payment_due_date')),
            currency_code=nav_data.get('currency', 'HUF'),
            invoice_net_amount=self._parse_decimal(nav_data.get('net_amount', '0')),
            invoice_vat_amount=self._parse_decimal(nav_data.get('vat_amount', '0')),
            invoice_gross_amount=self._parse_decimal(nav_data.get('gross_amount', '0')),
            original_request_version=nav_data.get('original_request_version', ''),
            completion_date=self._parse_nav_date(nav_data.get('completion_date')),
            source='NAV_SYNC',
            nav_transaction_id=nav_data.get('transaction_id', ''),
            last_modified_date=self._parse_nav_date(nav_data.get('last_modified_date')) or django_timezone.now(),
            
            # New NAV business fields
            invoice_operation=nav_data.get('invoice_operation') or None,
            invoice_category=nav_data.get('invoice_category') or None,
            payment_method=nav_data.get('payment_method') or None,
            payment_date=self._parse_nav_date(nav_data.get('payment_date')),
            invoice_appearance=nav_data.get('invoice_appearance') or None,
            nav_source=nav_data.get('nav_source') or None,
            completeness_indicator=nav_data.get('completeness_indicator'),
            modification_index=nav_data.get('modification_index'),
            original_invoice_number=nav_data.get('original_invoice_number') or None,
            invoice_index=nav_data.get('invoice_index'),
            batch_index=nav_data.get('batch_index'),
            nav_creation_date=self._parse_nav_date(nav_data.get('nav_creation_date')),
            
            # HUF amounts for foreign currency invoices
            invoice_net_amount_huf=self._parse_decimal(nav_data.get('net_amount_huf', '0')) if nav_data.get('net_amount_huf') else None,
            invoice_vat_amount_huf=self._parse_decimal(nav_data.get('vat_amount_huf', '0')) if nav_data.get('vat_amount_huf') else None,
            invoice_gross_amount_huf=(
                self._parse_decimal(nav_data.get('net_amount_huf', '0')) + 
                self._parse_decimal(nav_data.get('vat_amount_huf', '0'))
            ) if nav_data.get('net_amount_huf') and nav_data.get('vat_amount_huf') else None,
            
            # XML Data Storage
            nav_invoice_xml=nav_data.get('nav_invoice_xml'),
            nav_invoice_hash=nav_data.get('nav_invoice_hash'),
            
            sync_status='SYNCED'
        )
        
        # Create line items if available
        line_items = nav_data.get('lineItems', [])
        for line_data in line_items:
            self._create_line_item_from_nav_data(invoice, line_data)
        
        logger.info(f"Új számla létrehozva: {invoice.nav_invoice_number}")
        return invoice
    
    def _update_invoice_from_nav_data(self, invoice: Invoice, nav_data: Dict):
        """Update existing invoice with NAV data."""
        
        # Update fields that might have changed
        invoice.supplier_name = nav_data.get('supplier_name', invoice.supplier_name)
        invoice.customer_name = nav_data.get('customer_name', invoice.customer_name)
        invoice.fulfillment_date = self._parse_nav_date(nav_data.get('fulfillment_date')) or invoice.fulfillment_date
        invoice.payment_due_date = self._parse_nav_date(nav_data.get('payment_due_date')) or invoice.payment_due_date
        invoice.invoice_net_amount = self._parse_decimal(nav_data.get('net_amount', str(invoice.invoice_net_amount)))
        invoice.invoice_vat_amount = self._parse_decimal(nav_data.get('vat_amount', str(invoice.invoice_vat_amount)))
        invoice.invoice_gross_amount = self._parse_decimal(nav_data.get('gross_amount', str(invoice.invoice_gross_amount)))
        invoice.last_modified_date = self._parse_nav_date(nav_data.get('last_modified_date')) or invoice.last_modified_date or django_timezone.now()
        
        # Update XML data if available
        if nav_data.get('nav_invoice_xml'):
            invoice.nav_invoice_xml = nav_data.get('nav_invoice_xml')
        if nav_data.get('nav_invoice_hash'):
            invoice.nav_invoice_hash = nav_data.get('nav_invoice_hash')
            
        invoice.sync_status = 'SYNCED'
        
        invoice.save()
        
        # Update line items
        line_items = nav_data.get('lineItems', [])
        if line_items:
            # Remove existing line items and recreate
            invoice.line_items.all().delete()
            for line_data in line_items:
                self._create_line_item_from_nav_data(invoice, line_data)
        
        logger.info(f"Számla frissítve: {invoice.nav_invoice_number}")
    
    def _create_line_item_from_nav_data(self, invoice: Invoice, line_data: Dict):
        """Create invoice line item from NAV data."""
        
        return InvoiceLineItem.objects.create(
            invoice=invoice,
            line_number=line_data.get('lineNumber', 1),
            line_description=line_data.get('lineDescription', ''),
            quantity=self._parse_decimal(line_data.get('quantity', '1')),
            unit_of_measure=line_data.get('unitOfMeasure', 'db'),
            unit_price=self._parse_decimal(line_data.get('unitPrice', '0')),
            line_net_amount=self._parse_decimal(line_data.get('lineNetAmount', '0')),
            line_vat_amount=self._parse_decimal(line_data.get('lineVatAmount', '0')),
            line_gross_amount=self._parse_decimal(line_data.get('lineGrossAmount', '0')),
            vat_rate=self._parse_decimal(line_data.get('vatRate', '0')),
            product_code_category=line_data.get('productCodeCategory', ''),
            product_code_value=line_data.get('productCodeValue', '')
        )
    
    def _parse_nav_date(self, date_str: str) -> Optional[datetime]:
        """Parse NAV date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # NAV uses YYYY-MM-DD format
            return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
    
    def _parse_decimal(self, value: str) -> Decimal:
        """Parse string to Decimal for monetary amounts."""
        if not value:
            return Decimal('0.00')
        
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return Decimal('0.00')
    
    def sync_all_companies(
        self, 
        date_from: datetime = None, 
        date_to: datetime = None
    ) -> Dict:
        """
        Sync invoices for all companies with active NAV configurations.
        
        READ-ONLY OPERATION: Only queries data from NAV systems.
        """
        
        results = {
            'companies_processed': 0,
            'total_invoices_created': 0,
            'total_invoices_updated': 0,
            'companies_succeeded': 0,
            'companies_failed': 0,
            'company_results': []
        }
        
        # Get all companies with active NAV configurations
        nav_configs = NavConfiguration.objects.filter(
            is_active=True,
            sync_enabled=True
        ).select_related('company')
        
        for nav_config in nav_configs:
            company = nav_config.company
            logger.info(f"NAV szinkronizáció indítása: {company.name}")
            
            try:
                # Sync both inbound and outbound invoices
                for direction in ['OUTBOUND', 'INBOUND']:
                    sync_result = self.sync_company_invoices(
                        company=company,
                        date_from=date_from,
                        date_to=date_to,
                        direction=direction
                    )
                    
                    if sync_result['success']:
                        results['total_invoices_created'] += sync_result['invoices_created']
                        results['total_invoices_updated'] += sync_result['invoices_updated']
                    
                    results['company_results'].append({
                        'company_name': company.name,
                        'direction': direction,
                        **sync_result
                    })
                
                results['companies_succeeded'] += 1
                
            except Exception as e:
                logger.error(f"Hiba a cég szinkronizációjában: {company.name} - {str(e)}")
                results['companies_failed'] += 1
                
                results['company_results'].append({
                    'company_name': company.name,
                    'success': False,
                    'errors': [str(e)]
                })
            
            results['companies_processed'] += 1
        
        logger.info(f"Teljes NAV szinkronizáció befejezve: {results}")
        
        return results
    
    def _get_nav_configuration(self, company: Company, environment: str = None, prefer_production: bool = True) -> NavConfiguration:
        """
        Get NAV configuration for a company with intelligent environment selection.
        
        Args:
            company: Company instance
            environment: Specific environment ('production'/'test') or None for auto-select
            prefer_production: If True and environment=None, prefer production over test
            
        Returns:
            NavConfiguration instance or None
            
        Logic:
        - If environment specified: Use exact environment
        - If environment=None: Use get_active_config with preference
        """
        if environment:
            # Specific environment requested
            config = NavConfiguration.objects.for_company_and_environment(company, environment)
            if not config:
                logger.warning(f"No {environment} NAV config found for {company.name}")
            return config
        else:
            # Auto-select best available configuration
            config = NavConfiguration.objects.get_active_config(company, prefer_production)
            if config:
                selected_env = config.api_environment
                logger.info(f"Auto-selected {selected_env} NAV config for {company.name}")
            else:
                logger.warning(f"No active NAV config found for {company.name}")
            return config
    
    def _initialize_nav_client(self, nav_config: NavConfiguration):
        """
        Initialize NAV API client with the given configuration.
        
        Args:
            nav_config: NavConfiguration instance
            
        Returns:
            NavApiClient instance
        """
        try:
            nav_client = NavApiClient(nav_config)
            logger.info(f"NAV client initialized for {nav_config.api_environment} environment")
            return nav_client
        except Exception as e:
            logger.error(f"Failed to initialize NAV client: {e}")
            raise