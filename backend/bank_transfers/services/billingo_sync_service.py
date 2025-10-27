"""
Billingo API v3 synchronization service.

Handles invoice fetching from Billingo API with pagination,
error handling, rate limit retry, and company-specific sync.
"""

import requests
import json
import time
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction

from bank_transfers.models import (
    Company,
    CompanyBillingoSettings,
    BillingoInvoice,
    BillingoInvoiceItem,
    BillingoSyncLog
)
from bank_transfers.services.credential_manager import CredentialManager

logger = logging.getLogger(__name__)


class BillingoAPIError(Exception):
    """Base exception for Billingo API errors."""
    pass


class BillingoRateLimitError(BillingoAPIError):
    """Raised when API rate limit is exceeded (429)."""
    pass


class BillingoSyncService:
    """
    Service for synchronizing invoices from Billingo API.

    Supports:
    - Pagination (max 100 per page)
    - Rate limit handling with exponential backoff
    - Error recovery per company
    - Complete audit logging
    """

    BASE_URL = "https://api.billingo.hu/v3"
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    def __init__(self):
        self.credential_manager = CredentialManager()

    def sync_all_companies(self) -> Dict[str, any]:
        """
        Sync invoices for all companies with active Billingo settings.

        Returns:
            dict: Summary of sync results for all companies
        """
        companies = Company.objects.filter(
            is_active=True,
            billingo_settings__is_active=True
        ).prefetch_related('billingo_settings')

        results = {
            'total_companies': companies.count(),
            'successful': 0,
            'failed': 0,
            'companies': []
        }

        for company in companies:
            try:
                result = self.sync_company(company)
                results['successful'] += 1
                results['companies'].append({
                    'company_id': company.id,
                    'company_name': company.name,
                    'status': 'success',
                    'invoices_processed': result['invoices_processed']
                })
            except Exception as e:
                logger.error(
                    f"Billingo sync failed for company {company.name}: {str(e)}",
                    exc_info=True
                )
                results['failed'] += 1
                results['companies'].append({
                    'company_id': company.id,
                    'company_name': company.name,
                    'status': 'failed',
                    'error': str(e)
                })

        return results

    def sync_company(
        self,
        company: Company,
        sync_type: str = 'AUTOMATIC'
    ) -> Dict[str, any]:
        """
        Sync invoices for a single company.

        Args:
            company: Company to sync
            sync_type: 'MANUAL' or 'AUTOMATIC'

        Returns:
            dict: Sync results with metrics
        """
        # Create sync log
        sync_log = BillingoSyncLog.objects.create(
            company=company,
            sync_type=sync_type,
            status='RUNNING'
        )

        start_time = time.time()

        try:
            # Get company settings
            settings = company.billingo_settings.first()
            if not settings:
                raise BillingoAPIError("No Billingo settings configured")

            if not settings.is_active:
                raise BillingoAPIError("Billingo sync is disabled for this company")

            # Decrypt API key
            api_key = self.credential_manager.decrypt_credential(settings.api_key)

            # Fetch all invoices with pagination
            all_invoices = []
            page = 1
            total_pages = 1
            api_calls = 0

            while page <= total_pages:
                invoices_data, pagination = self._fetch_documents_page(
                    api_key=api_key,
                    page=page
                )
                api_calls += 1

                all_invoices.extend(invoices_data)
                total_pages = pagination.get('last_page', 1)
                page += 1

                logger.info(
                    f"Fetched page {page-1}/{total_pages} for {company.name} "
                    f"({len(invoices_data)} invoices)"
                )

            # Process invoices
            created_count = 0
            updated_count = 0
            items_extracted = 0
            errors = []

            for invoice_data in all_invoices:
                try:
                    created, item_count = self._process_invoice(company, invoice_data)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    items_extracted += item_count
                except Exception as e:
                    errors.append({
                        'invoice_id': invoice_data.get('id'),
                        'invoice_number': invoice_data.get('invoice_number'),
                        'error': str(e)
                    })
                    logger.error(
                        f"Error processing invoice {invoice_data.get('invoice_number')}: {str(e)}"
                    )

            # Update sync log
            duration = int(time.time() - start_time)
            sync_log.invoices_processed = len(all_invoices)
            sync_log.invoices_created = created_count
            sync_log.invoices_updated = updated_count
            sync_log.invoices_skipped = len(errors)
            sync_log.items_extracted = items_extracted
            sync_log.api_calls_made = api_calls
            sync_log.sync_duration_seconds = duration
            sync_log.errors = json.dumps(errors) if errors else ""
            sync_log.status = 'PARTIAL' if errors else 'COMPLETED'
            sync_log.completed_at = timezone.now()
            sync_log.save()

            # Update last_sync_time
            settings.last_sync_time = timezone.now()
            settings.save()

            logger.info(
                f"Billingo sync completed for {company.name}: "
                f"{created_count} created, {updated_count} updated, "
                f"{len(errors)} errors in {duration}s"
            )

            return {
                'invoices_processed': len(all_invoices),
                'invoices_created': created_count,
                'invoices_updated': updated_count,
                'invoices_skipped': len(errors),
                'items_extracted': items_extracted,
                'api_calls': api_calls,
                'duration_seconds': duration,
                'errors': errors
            }

        except Exception as e:
            # Update sync log with failure
            sync_log.status = 'FAILED'
            sync_log.errors = json.dumps([{'error': str(e)}])
            sync_log.completed_at = timezone.now()
            sync_log.sync_duration_seconds = int(time.time() - start_time)
            sync_log.save()
            raise

    def _fetch_documents_page(
        self,
        api_key: str,
        page: int = 1,
        per_page: int = 100
    ) -> Tuple[List[Dict], Dict]:
        """
        Fetch a single page of documents from Billingo API.

        Args:
            api_key: Decrypted Billingo API key
            page: Page number (1-indexed)
            per_page: Results per page (max 100)

        Returns:
            tuple: (list of invoice data dicts, pagination metadata)
        """
        url = f"{self.BASE_URL}/documents"
        headers = {
            'X-API-KEY': api_key,
            'Accept': 'application/json'
        }
        params = {
            'page': page,
            'per_page': min(per_page, 100)  # API limit
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 429:
                    # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', self.RETRY_DELAY))
                    if attempt < self.MAX_RETRIES - 1:
                        logger.warning(
                            f"Rate limit exceeded, retrying after {retry_after}s "
                            f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        time.sleep(retry_after)
                        continue
                    else:
                        raise BillingoRateLimitError("Rate limit exceeded after max retries")

                response.raise_for_status()
                data = response.json()

                return (
                    data.get('data', []),
                    {
                        'total': data.get('total', 0),
                        'per_page': data.get('per_page', per_page),
                        'current_page': data.get('current_page', page),
                        'last_page': data.get('last_page', 1)
                    }
                )

            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"API request failed, retrying in {self.RETRY_DELAY}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES}): {str(e)}"
                    )
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise BillingoAPIError(
                        f"API request failed after {self.MAX_RETRIES} attempts: {str(e)}"
                    )

        raise BillingoAPIError("Unexpected error in _fetch_documents_page")

    @transaction.atomic
    def _process_invoice(
        self,
        company: Company,
        invoice_data: Dict
    ) -> Tuple[bool, int]:
        """
        Process a single invoice: create or update.

        Args:
            company: Company object
            invoice_data: Raw invoice data from API

        Returns:
            tuple: (was_created: bool, item_count: int)
        """
        invoice_id = invoice_data.get('id')

        # Extract organization data
        org = invoice_data.get('organization', {})
        org_bank = org.get('bank_account', {})

        # Extract partner data
        partner = invoice_data.get('partner', {}) or invoice_data.get('document_partner', {})

        # Create or update invoice
        invoice, created = BillingoInvoice.objects.update_or_create(
            id=invoice_id,
            company=company,
            defaults={
                'invoice_number': invoice_data.get('invoice_number', ''),
                'type': invoice_data.get('type', ''),
                'correction_type': invoice_data.get('correction_type', ''),
                'cancelled': invoice_data.get('cancelled', False),
                'block_id': invoice_data.get('block_id'),
                'payment_status': invoice_data.get('payment_status', ''),
                'payment_method': invoice_data.get('payment_method', ''),
                'gross_total': Decimal(str(invoice_data.get('gross_total', 0))),
                'currency': invoice_data.get('currency', 'HUF'),
                'conversion_rate': Decimal(str(invoice_data.get('conversion_rate', 1))),
                'invoice_date': invoice_data.get('invoice_date'),
                'fulfillment_date': invoice_data.get('fulfillment_date'),
                'due_date': invoice_data.get('due_date'),
                'paid_date': invoice_data.get('paid_date'),
                'organization_name': org.get('name', ''),
                'organization_tax_number': org.get('tax_number', ''),
                'organization_bank_account_number': org_bank.get('account_number', ''),
                'organization_bank_account_iban': org_bank.get('account_number_iban', ''),
                'organization_swift': org_bank.get('swift', ''),
                'partner_id': partner.get('id'),
                'partner_name': partner.get('name', ''),
                'partner_tax_number': partner.get('taxcode', '') or partner.get('tax_number', ''),
                'partner_iban': partner.get('iban', ''),
                'partner_swift': partner.get('swift', ''),
                'partner_account_number': partner.get('account_number', ''),
                'comment': invoice_data.get('comment', ''),
                'online_szamla_status': invoice_data.get('online_szamla_status', ''),
            }
        )

        # Delete existing items if updating
        if not created:
            invoice.items.all().delete()

        # Create invoice items
        items_data = invoice_data.get('items', [])
        item_count = 0

        for item_data in items_data:
            BillingoInvoiceItem.objects.create(
                invoice=invoice,
                product_id=item_data.get('product_id'),
                name=item_data.get('name', ''),
                quantity=Decimal(str(item_data.get('quantity', 0))),
                unit=item_data.get('unit', ''),
                net_unit_price=Decimal(str(item_data.get('net_unit_price', 0))),
                net_amount=Decimal(str(item_data.get('net_amount', 0))),
                gross_amount=Decimal(str(item_data.get('gross_amount', 0))),
                vat=item_data.get('vat', ''),
                entitlement=item_data.get('entitlement', ''),
            )
            item_count += 1

        return (created, item_count)
