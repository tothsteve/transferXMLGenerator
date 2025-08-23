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
        direction: str = 'OUTBOUND'
    ) -> Dict:
        """
        Synchronize invoices for a specific company.
        
        READ-ONLY OPERATION: Only queries data from NAV, never modifies NAV.
        
        Args:
            company: Company to sync invoices for
            date_from: Start date for invoice query (defaults to 30 days ago)
            date_to: End date for invoice query (defaults to today)
            direction: Invoice direction ('OUTBOUND' or 'INBOUND')
            
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
            # Get active NAV configuration for company
            nav_config = self._get_nav_configuration(company)
            if not nav_config:
                raise ValueError(f"Nincs aktív NAV konfiguráció a {company.name} céghez")
            
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
                
                # Check if invoice already exists
                existing_invoice = Invoice.objects.filter(
                    company=company,
                    nav_invoice_number=nav_invoice_number
                ).first()
                
                # Query detailed invoice data from NAV (READ-ONLY)
                # Pass the direction from the original query and supplier info from digest
                try:
                    detailed_invoice_data = nav_client.query_invoice_data(
                        nav_invoice_number, 
                        direction=direction, 
                        supplier_tax_number=supplier_tax_number,
                        batch_index=batch_index
                    )
                except Exception as e:
                    # If detailed query fails, continue with digest data only
                    logger.warning(f"Detailed query failed for {nav_invoice_number}: {str(e)}")
                    detailed_invoice_data = None
                
                # Create invoice data from available information
                invoice_data = self._create_invoice_data_from_digest(
                    digest_entry, direction, detailed_invoice_data
                )
                
                if existing_invoice:
                    # Update existing invoice
                    self._update_invoice_from_nav_data(existing_invoice, invoice_data)
                    invoices_updated += 1
                else:
                    # Create new invoice
                    self._create_invoice_from_nav_data(company, invoice_data)
                    invoices_created += 1
                
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
    
    def _create_invoice_data_from_digest(self, digest_entry: Dict, direction: str, detailed_data: Dict = None) -> Dict:
        """Create comprehensive invoice data from digest and detailed information."""
        from datetime import date
        from django.utils import timezone
        
        # Start with digest data
        invoice_data = {
            'invoice_number': digest_entry.get('invoiceNumber', ''),
            'invoice_direction': direction,
            'supplier_name': digest_entry.get('supplierName', ''),
            'supplier_tax_number': digest_entry.get('supplierTaxNumber', ''),
            'batch_index': digest_entry.get('batchIndex', 1),
            # Defaults for required fields
            'issue_date': date.today().isoformat(),  # Use today as fallback
            'currency': 'HUF',
            'net_amount': 0.0,
            'gross_amount': 0.0,
            'customer_name': '',
            'customer_tax_number': '',
            'last_modified_date': timezone.now().isoformat(),  # Default to now
        }
        
        # Override with detailed data if available
        if detailed_data:
            invoice_data.update(detailed_data)
        
        return invoice_data
    
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
            nav_transaction_id=nav_data.get('transactionId', ''),
            last_modified_date=self._parse_nav_date(nav_data.get('last_modified_date')) or django_timezone.now(),
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