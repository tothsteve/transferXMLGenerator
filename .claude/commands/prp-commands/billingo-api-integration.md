# Billingo API Integration PRP (Specification-Driven)

## Executive Summary

Integrate **Billingo API v3** to synchronize invoices/documents for all companies with configured API keys. Support both **manual (on-demand)** and **automatic (cron-based)** synchronization. Follows existing multi-company architecture patterns, feature flag system, and role-based access control.

---

## Current State Assessment

### Existing Similar Features
- **NAV Invoice Integration**: Syncs Hungarian Tax Authority invoices with payment status tracking
  - Models: `NAVInvoice`, `NAVConfiguration`, `InvoiceSyncLog`
  - Service: `nav_sync_service.py` with API integration
  - Management command: `sync_nav_invoices`
  - Feature flag: `NAV_SYNC`
  - Credential encryption: Fernet symmetric encryption

- **Multi-Company Architecture**: Complete data isolation with feature flags
  - Company-scoped data with `company_id` foreign key on all business models
  - Role-based permissions: ADMIN, FINANCIAL, ACCOUNTANT, USER
  - Feature enablement per company via `CompanyFeature` model

- **Exchange Rate Integration**: Automated sync from external API (MNB)
  - Management command with cron scheduling
  - Sync history logging
  - Manual trigger endpoint (ADMIN only)

### Pain Points
- No Billingo invoice data available in system
- Manual invoice entry required for Billingo users
- Duplicate data management across platforms

---

## Desired State

### Business Goals
1. **Automated Billingo invoice synchronization** for all companies with configured API keys
2. **Manual sync trigger** for ADMIN users to force immediate refresh
3. **Complete audit trail** of all sync operations with error tracking
4. **Company-scoped invoice storage** with full isolation
5. **Feature flag control** to enable/disable per company

### Technical Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         Django Backend                           │
├─────────────────────────────────────────────────────────────────┤
│  Models:                                                         │
│  - CompanyBillingoSettings (API key, last_sync_time)            │
│  - BillingoInvoice (invoice data from /documents endpoint)      │
│  - BillingoInvoiceItem (line items from invoice)                │
│  - BillingoSyncLog (audit trail)                                │
├─────────────────────────────────────────────────────────────────┤
│  Services:                                                       │
│  - BillingoSyncService (handles API calls, pagination, errors)  │
│  - CredentialManager (API key encryption/decryption)            │
├─────────────────────────────────────────────────────────────────┤
│  API Endpoints:                                                  │
│  - GET /api/billingo-invoices/ (list with filtering)            │
│  - GET /api/billingo-invoices/{id}/ (detail)                    │
│  - POST /api/billingo-invoices/sync/ (manual sync - ADMIN)      │
│  - GET /api/billingo-invoices/sync_history/ (audit log)         │
│  - GET /api/billingo-settings/ (get settings)                   │
│  - PUT /api/billingo-settings/ (update API key - ADMIN)         │
├─────────────────────────────────────────────────────────────────┤
│  Management Command:                                             │
│  - sync_billingo_invoices (cron job every 30 minutes)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Billingo API v3 (External)                    │
│  GET https://api.billingo.hu/v3/documents                       │
│  Headers: X-API-KEY: {company_api_key}                          │
│  Pagination: page, per_page (max 100)                           │
│  Rate Limit: 60 requests/minute                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                           │
│  Components:                                                     │
│  - BillingoInvoiceList (table with filtering/sorting)           │
│  - BillingoInvoiceDetail (full invoice view)                    │
│  - BillingoSettings (API key management)                        │
│  - BillingoSyncButton (manual trigger + status indicator)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Documentation

### current_state
```yaml
files:
  - bank_transfers/models.py (NAVInvoice, NAVConfiguration exist)
  - bank_transfers/serializers.py (NAV serializers)
  - bank_transfers/api_views.py (NAV ViewSets)
  - bank_transfers/services/nav_sync_service.py (NAV sync logic)
  - frontend/src/components/NAVInvoices/ (NAV UI)

behavior:
  - NAV invoice sync works via management command + manual trigger
  - Feature flag system controls company feature access
  - Role-based permissions control endpoint access
  - Encrypted credentials stored in database

issues:
  - No Billingo integration exists
  - Cannot sync Billingo invoices automatically
  - Billingo users must manually enter invoice data
```

### desired_state
```yaml
files:
  - bank_transfers/models.py (ADD: CompanyBillingoSettings, BillingoInvoice, BillingoInvoiceItem, BillingoSyncLog)
  - bank_transfers/serializers.py (ADD: Billingo serializers)
  - bank_transfers/api_views.py (ADD: BillingoInvoiceViewSet, BillingoSettingsViewSet)
  - bank_transfers/services/billingo_sync_service.py (CREATE: Billingo sync logic)
  - bank_transfers/management/commands/sync_billingo_invoices.py (CREATE: cron command)
  - bank_transfers/migrations/ (CREATE: new migration for Billingo models)
  - frontend/src/components/BillingoInvoices/ (CREATE: UI components)
  - frontend/src/types/api.ts (ADD: Billingo TypeScript types)
  - frontend/src/schemas/api.schemas.ts (ADD: Billingo Zod schemas)
  - DATABASE_DOCUMENTATION.md (UPDATE: add Billingo table documentation)
  - FEATURES.md (UPDATE: add BILLINGO_SYNC feature)
  - API_GUIDE.md (UPDATE: add Billingo API endpoints)

behavior:
  - Automated sync every 30 minutes via cron for all active companies
  - Manual sync trigger via REST endpoint for ADMIN users
  - Complete audit trail in BillingoSyncLog
  - Encrypted API key storage with Fernet
  - Company-scoped invoice data with full isolation
  - Feature flag control (BILLINGO_SYNC)
  - Role-based access (ADMIN can manage settings, all can view invoices)
  - Pagination handling for large invoice datasets
  - Rate limit retry logic (429 responses)
  - Error handling per company (continue sync for others on failure)

benefits:
  - Automated invoice data availability
  - No manual data entry required
  - Complete sync audit trail
  - Company-specific API key management
  - Follows existing architecture patterns
```

---

## Hierarchical Objectives

### High-Level Goal
**Integrate Billingo API v3 to automatically synchronize invoices for all companies with configured API keys, following existing multi-company architecture and feature flag patterns.**

### Mid-Level Milestones

#### Milestone 1: Database Schema & Models
Create Django models for Billingo integration following existing patterns (NAVInvoice, NAVConfiguration as reference).

#### Milestone 2: Sync Service & Business Logic
Implement BillingoSyncService with API calls, pagination, error handling, and rate limit retry.

#### Milestone 3: Management Command & Cron Setup
Create Django management command for automated sync via cron job.

#### Milestone 4: REST API Endpoints
Create ViewSets and serializers for invoice listing, detail view, manual sync, and settings management.

#### Milestone 5: Frontend Integration
Build React components for invoice management, settings, and sync status visualization.

#### Milestone 6: Documentation & Testing
Update all documentation files and create comprehensive test suite.

### Low-Level Tasks (with validation)

---

## Task 1: Create Database Models

### Action: CREATE
### Files:
- `bank_transfers/models.py`
- `bank_transfers/migrations/XXXX_add_billingo_models.py`

### Changes:
```python
# ADD to bank_transfers/models.py after NAVConfiguration model

class CompanyBillingoSettings(models.Model):
    """
    Billingo API configuration for invoice synchronization.
    One configuration per company (company-scoped).
    """
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='billingo_settings'
    )
    api_key = models.CharField(
        max_length=255,
        help_text="Encrypted Billingo API key (X-API-KEY header)"
    )
    last_sync_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful sync timestamp"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable sync for this company"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_transfers_companybillingosettings'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company'],
                name='unique_billingo_settings_per_company'
            )
        ]

    def __str__(self):
        return f"Billingo Settings - {self.company.name}"


class BillingoInvoice(models.Model):
    """
    Billingo invoice/document record from /documents API endpoint.
    Company-scoped for multi-tenant isolation.
    """
    # Billingo ID is the primary key (BigInteger from API response)
    id = models.BigIntegerField(primary_key=True)

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='billingo_invoices'
    )

    # Invoice identification
    invoice_number = models.CharField(max_length=50)
    type = models.CharField(max_length=30)  # invoice, receipt, proforma, etc.
    correction_type = models.CharField(max_length=30, blank=True)
    cancelled = models.BooleanField(default=False)
    block_id = models.IntegerField(null=True)

    # Payment information
    payment_status = models.CharField(max_length=30)  # paid, unpaid, overdue, etc.
    payment_method = models.CharField(max_length=30, blank=True)  # wire_transfer, cash, etc.

    # Financial data
    gross_total = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=5)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1)

    # Dates
    invoice_date = models.DateField()
    fulfillment_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)

    # Organization (our company information from Billingo)
    organization_name = models.CharField(max_length=255)
    organization_tax_number = models.CharField(max_length=50)
    organization_bank_account_number = models.CharField(max_length=100, blank=True)
    organization_bank_account_iban = models.CharField(max_length=100, blank=True)
    organization_swift = models.CharField(max_length=20, blank=True)

    # Partner (customer/supplier information)
    partner_id = models.BigIntegerField(null=True)
    partner_name = models.CharField(max_length=255)
    partner_tax_number = models.CharField(max_length=50, blank=True)
    partner_iban = models.CharField(max_length=100, blank=True)
    partner_swift = models.CharField(max_length=20, blank=True)
    partner_account_number = models.CharField(max_length=100, blank=True)

    # Additional metadata
    comment = models.TextField(blank=True)
    online_szamla_status = models.CharField(max_length=30, blank=True)

    # Audit fields
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_transfers_billingoinvoice'
        indexes = [
            models.Index(fields=['company', 'invoice_date']),
            models.Index(fields=['company', 'payment_status']),
            models.Index(fields=['company', 'partner_tax_number']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.partner_name}"


class BillingoInvoiceItem(models.Model):
    """
    Line items for Billingo invoices.
    Represents individual products/services on the invoice.
    """
    invoice = models.ForeignKey(
        'BillingoInvoice',
        on_delete=models.CASCADE,
        related_name='items'
    )
    product_id = models.BigIntegerField(null=True, blank=True)
    name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # PIECE, HOUR, LITER, etc.
    net_unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2)
    gross_amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat = models.CharField(max_length=10)  # "27%", "5%", "0%", etc.
    entitlement = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_transfers_billingoinvoiceitem'
        indexes = [
            models.Index(fields=['invoice']),
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.name}"


class BillingoSyncLog(models.Model):
    """
    Audit log for Billingo invoice synchronization operations.
    """
    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial Success'),
    ]

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='billingo_sync_logs'
    )
    sync_type = models.CharField(max_length=20)  # MANUAL, AUTOMATIC

    # Sync metrics
    invoices_processed = models.IntegerField(default=0)
    invoices_created = models.IntegerField(default=0)
    invoices_updated = models.IntegerField(default=0)
    invoices_skipped = models.IntegerField(default=0)
    items_extracted = models.IntegerField(default=0)

    # Performance metrics
    sync_duration_seconds = models.IntegerField(null=True)
    api_calls_made = models.IntegerField(default=0)

    # Error tracking
    errors = models.TextField(blank=True)  # JSON array of errors
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RUNNING')

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bank_transfers_billingosynclog'
        indexes = [
            models.Index(fields=['company', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['sync_type']),
        ]

    def __str__(self):
        return f"Billingo Sync - {self.company.name} - {self.started_at}"
```

### Validation:
```bash
# Run makemigrations
python manage.py makemigrations bank_transfers -n add_billingo_models

# Check migration file
cat bank_transfers/migrations/XXXX_add_billingo_models.py

# Run migration
python manage.py migrate bank_transfers

# Verify tables exist
python manage.py dbshell
\dt bank_transfers_billingo*
\q
```

**Expected result**: Migration succeeds, 4 new tables created (companybillingosettings, billingoinvoice, billingoinvoiceitem, billingosynclog)

---

## Task 2: Create Billingo Sync Service

### Action: CREATE
### File: `bank_transfers/services/billingo_sync_service.py`

### Changes:
```python
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
            api_key = self.credential_manager.decrypt(settings.api_key)

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
                    raise BillingoAPIError(f"API request failed after {self.MAX_RETRIES} attempts: {str(e)}")

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
        org_address = org.get('address', {})

        # Extract partner data
        partner = invoice_data.get('partner', {})
        partner_address = partner.get('address', {})

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
                'partner_tax_number': partner.get('taxcode', ''),
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
```

### Validation:
```bash
# Test import
python manage.py shell
from bank_transfers.services.billingo_sync_service import BillingoSyncService
service = BillingoSyncService()
print("Service imported successfully")
exit()
```

**Expected result**: No import errors, service class loads successfully

---

## Task 3: Create Management Command

### Action: CREATE
### File: `bank_transfers/management/commands/sync_billingo_invoices.py`

### Changes:
```python
"""
Django management command for Billingo invoice synchronization.

Usage:
    python manage.py sync_billingo_invoices

This command is designed to run via cron job every 30 minutes.
"""

from django.core.management.base import BaseCommand
from bank_transfers.services.billingo_sync_service import BillingoSyncService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Synchronize invoices from Billingo API for all active companies"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Billingo invoice sync...'))

        try:
            service = BillingoSyncService()
            results = service.sync_all_companies()

            # Display results
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nBillingo sync completed:\n"
                    f"  Total companies: {results['total_companies']}\n"
                    f"  Successful: {results['successful']}\n"
                    f"  Failed: {results['failed']}\n"
                )
            )

            # Display per-company details
            for company_result in results['companies']:
                if company_result['status'] == 'success':
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {company_result['company_name']}: "
                            f"{company_result['invoices_processed']} invoices processed"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ {company_result['company_name']}: "
                            f"{company_result['error']}"
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Billingo sync failed: {str(e)}')
            )
            raise
```

### Validation:
```bash
# Test command (will fail without API key, but structure should work)
python manage.py sync_billingo_invoices

# Expected output: Command runs, reports 0 companies (no settings configured yet)
```

**Expected result**: Command executes without errors, reports 0 companies to sync

---

## Task 4: Create Serializers

### Action: MODIFY
### File: `bank_transfers/serializers.py`

### Changes:
```python
# ADD at end of file

class BillingoInvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for Billingo invoice line items."""

    class Meta:
        model = BillingoInvoiceItem
        fields = [
            'id', 'product_id', 'name', 'quantity', 'unit',
            'net_unit_price', 'net_amount', 'gross_amount',
            'vat', 'entitlement', 'created_at'
        ]
        read_only_fields = fields


class BillingoInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Billingo invoices with nested items."""

    items = BillingoInvoiceItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = BillingoInvoice
        fields = [
            'id', 'invoice_number', 'type', 'correction_type', 'cancelled',
            'block_id', 'payment_status', 'payment_method',
            'gross_total', 'currency', 'conversion_rate',
            'invoice_date', 'fulfillment_date', 'due_date', 'paid_date',
            'organization_name', 'organization_tax_number',
            'organization_bank_account_number', 'organization_bank_account_iban',
            'organization_swift',
            'partner_id', 'partner_name', 'partner_tax_number',
            'partner_iban', 'partner_swift', 'partner_account_number',
            'comment', 'online_szamla_status',
            'items', 'item_count', 'last_modified', 'created_at'
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.items.count()


class BillingoInvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for invoice list views (no items)."""

    class Meta:
        model = BillingoInvoice
        fields = [
            'id', 'invoice_number', 'type', 'payment_status', 'payment_method',
            'gross_total', 'currency', 'invoice_date', 'fulfillment_date',
            'due_date', 'paid_date', 'partner_name', 'partner_tax_number',
            'created_at'
        ]
        read_only_fields = fields


class BillingoSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for Billingo sync audit logs."""

    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = BillingoSyncLog
        fields = [
            'id', 'company', 'company_name', 'sync_type',
            'invoices_processed', 'invoices_created', 'invoices_updated',
            'invoices_skipped', 'items_extracted',
            'sync_duration_seconds', 'api_calls_made',
            'errors', 'status', 'started_at', 'completed_at'
        ]
        read_only_fields = fields


class CompanyBillingoSettingsSerializer(serializers.ModelSerializer):
    """Serializer for Billingo settings (API key write-only)."""

    api_key = serializers.CharField(write_only=True, required=False)
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = CompanyBillingoSettings
        fields = [
            'id', 'company', 'api_key', 'has_api_key',
            'last_sync_time', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'last_sync_time', 'created_at', 'updated_at']

    def get_has_api_key(self, obj):
        """Indicate if API key is configured without exposing it."""
        return bool(obj.api_key)

    def create(self, validated_data):
        """Encrypt API key before saving."""
        from bank_transfers.services.credential_manager import CredentialManager

        api_key = validated_data.get('api_key')
        if api_key:
            credential_manager = CredentialManager()
            validated_data['api_key'] = credential_manager.encrypt(api_key)

        validated_data['company'] = self.context['request'].user.active_company
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Encrypt API key before updating."""
        from bank_transfers.services.credential_manager import CredentialManager

        api_key = validated_data.get('api_key')
        if api_key:
            credential_manager = CredentialManager()
            validated_data['api_key'] = credential_manager.encrypt(api_key)

        return super().update(instance, validated_data)
```

### Validation:
```bash
# Test import
python manage.py shell
from bank_transfers.serializers import BillingoInvoiceSerializer
print("Serializers imported successfully")
exit()
```

**Expected result**: No import errors

---

## Task 5: Create ViewSets and API Endpoints

### Action: MODIFY
### File: `bank_transfers/api_views.py`

### Changes:
```python
# ADD at end of file

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from bank_transfers.models import (
    BillingoInvoice, BillingoSyncLog, CompanyBillingoSettings
)
from bank_transfers.serializers import (
    BillingoInvoiceSerializer, BillingoInvoiceListSerializer,
    BillingoSyncLogSerializer, CompanyBillingoSettingsSerializer
)
from bank_transfers.services.billingo_sync_service import BillingoSyncService


class BillingoInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Billingo invoices (read-only).

    list: List invoices with filtering
    retrieve: Get invoice details with line items
    sync: Manual sync trigger (ADMIN only)
    sync_history: View sync audit logs
    """
    permission_classes = [IsAuthenticated, CompanyContextPermission]
    filterset_fields = ['payment_status', 'type', 'cancelled']
    search_fields = ['invoice_number', 'partner_name', 'partner_tax_number']
    ordering_fields = ['invoice_date', 'due_date', 'gross_total', 'created_at']
    ordering = ['-invoice_date']

    def get_queryset(self):
        return BillingoInvoice.objects.filter(
            company=self.request.user.active_company
        ).prefetch_related('items')

    def get_serializer_class(self):
        if self.action == 'list':
            return BillingoInvoiceListSerializer
        return BillingoInvoiceSerializer

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Trigger manual Billingo invoice sync for current company.

        Requires ADMIN role.
        """
        # Check if user is ADMIN
        company_user = request.user.company_users.filter(
            company=request.user.active_company
        ).first()

        if not company_user or company_user.role != 'ADMIN':
            return Response(
                {'error': 'Only ADMIN users can trigger manual sync'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            service = BillingoSyncService()
            result = service.sync_company(
                company=request.user.active_company,
                sync_type='MANUAL'
            )

            return Response({
                'message': 'Sync completed successfully',
                'results': result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sync_history(self, request):
        """View sync audit logs for current company."""
        logs = BillingoSyncLog.objects.filter(
            company=request.user.active_company
        ).order_by('-started_at')[:20]

        serializer = BillingoSyncLogSerializer(logs, many=True)
        return Response(serializer.data)


class BillingoSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Billingo API settings.

    Allows ADMIN users to configure Billingo API key.
    """
    permission_classes = [IsAuthenticated, CompanyContextPermission]
    serializer_class = CompanyBillingoSettingsSerializer
    http_method_names = ['get', 'post', 'put', 'patch']  # No DELETE

    def get_queryset(self):
        return CompanyBillingoSettings.objects.filter(
            company=self.request.user.active_company
        )

    def create(self, request, *args, **kwargs):
        """Only ADMIN can create settings."""
        company_user = request.user.company_users.filter(
            company=request.user.active_company
        ).first()

        if not company_user or company_user.role != 'ADMIN':
            return Response(
                {'error': 'Only ADMIN users can configure Billingo settings'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Only ADMIN can update settings."""
        company_user = request.user.company_users.filter(
            company=request.user.active_company
        ).first()

        if not company_user or company_user.role != 'ADMIN':
            return Response(
                {'error': 'Only ADMIN users can update Billingo settings'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)
```

### Action: MODIFY
### File: `bank_transfers/urls.py`

### Changes:
```python
# ADD to router registration section

router.register(r'billingo-invoices', BillingoInvoiceViewSet, basename='billingoinvoice')
router.register(r'billingo-settings', BillingoSettingsViewSet, basename='billingosettings')
```

### Validation:
```bash
# Check URL patterns
python manage.py show_urls | grep billingo

# Expected output:
# /api/billingo-invoices/ [name='billingoinvoice-list']
# /api/billingo-invoices/{id}/ [name='billingoinvoice-detail']
# /api/billingo-invoices/sync/ [name='billingoinvoice-sync']
# /api/billingo-invoices/sync_history/ [name='billingoinvoice-sync-history']
# /api/billingo-settings/ [name='billingosettings-list']
# /api/billingo-settings/{id}/ [name='billingosettings-detail']
```

**Expected result**: All endpoint URLs registered correctly

---

## Task 6: Add Feature Flag for Billingo Sync

### Action: ADD
### Method: Django shell data migration

### Changes:
```python
# Run in Django shell: python manage.py shell

from bank_transfers.models import FeatureTemplate

# Create BILLINGO_SYNC feature template
feature, created = FeatureTemplate.objects.get_or_create(
    feature_code='BILLINGO_SYNC',
    defaults={
        'display_name': 'Billingo Invoice Synchronization',
        'description': 'Synchronize invoices from Billingo API v3 automatically',
        'category': 'SYNC',
        'default_enabled': False,
        'is_system_critical': False,
    }
)

if created:
    print(f"✓ Created BILLINGO_SYNC feature template (ID: {feature.id})")
else:
    print(f"✓ BILLINGO_SYNC feature template already exists (ID: {feature.id})")

exit()
```

### Validation:
```bash
# Verify feature exists
python manage.py shell
from bank_transfers.models import FeatureTemplate
feature = FeatureTemplate.objects.get(feature_code='BILLINGO_SYNC')
print(f"Feature: {feature.display_name} ({feature.category})")
exit()
```

**Expected result**: Feature template exists with correct attributes

---

## Task 7: Create Frontend TypeScript Types

### Action: MODIFY
### File: `frontend/src/types/api.ts`

### Changes:
```typescript
// ADD at end of file

export interface BillingoInvoiceItem {
  id: number;
  product_id: number | null;
  name: string;
  quantity: string;
  unit: string;
  net_unit_price: string;
  net_amount: string;
  gross_amount: string;
  vat: string;
  entitlement: string;
  created_at: string;
}

export interface BillingoInvoice {
  id: number;
  invoice_number: string;
  type: string;
  correction_type: string;
  cancelled: boolean;
  block_id: number | null;
  payment_status: string;
  payment_method: string;
  gross_total: string;
  currency: string;
  conversion_rate: string;
  invoice_date: string;
  fulfillment_date: string | null;
  due_date: string | null;
  paid_date: string | null;
  organization_name: string;
  organization_tax_number: string;
  organization_bank_account_number: string;
  organization_bank_account_iban: string;
  organization_swift: string;
  partner_id: number | null;
  partner_name: string;
  partner_tax_number: string;
  partner_iban: string;
  partner_swift: string;
  partner_account_number: string;
  comment: string;
  online_szamla_status: string;
  items?: BillingoInvoiceItem[];
  item_count?: number;
  last_modified: string;
  created_at: string;
}

export interface BillingoSyncLog {
  id: number;
  company: number;
  company_name: string;
  sync_type: string;
  invoices_processed: number;
  invoices_created: number;
  invoices_updated: number;
  invoices_skipped: number;
  items_extracted: number;
  sync_duration_seconds: number | null;
  api_calls_made: number;
  errors: string;
  status: string;
  started_at: string;
  completed_at: string | null;
}

export interface CompanyBillingoSettings {
  id: number;
  company: number;
  api_key?: string; // write-only
  has_api_key: boolean;
  last_sync_time: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### Validation:
```bash
# Check TypeScript compilation
cd frontend
npx tsc --noEmit
```

**Expected result**: No TypeScript errors

---

## Task 8: Create Frontend Zod Schemas

### Action: MODIFY
### File: `frontend/src/schemas/api.schemas.ts`

### Changes:
```typescript
// ADD at end of file

// ============================================================================
// Billingo Schemas
// ============================================================================

export const BillingoInvoiceItemSchema = z.object({
  id: z.number(),
  product_id: z.number().nullable(),
  name: z.string(),
  quantity: z.string(),
  unit: z.string(),
  net_unit_price: z.string(),
  net_amount: z.string(),
  gross_amount: z.string(),
  vat: z.string(),
  entitlement: z.string(),
  created_at: z.string(),
});

export type BillingoInvoiceItemSchemaType = z.infer<typeof BillingoInvoiceItemSchema>;

export const BillingoInvoiceSchema = z.object({
  id: z.number(),
  invoice_number: z.string(),
  type: z.string(),
  correction_type: z.string(),
  cancelled: z.boolean(),
  block_id: z.number().nullable(),
  payment_status: z.string(),
  payment_method: z.string(),
  gross_total: z.string(),
  currency: z.string(),
  conversion_rate: z.string(),
  invoice_date: z.string(),
  fulfillment_date: z.string().nullable(),
  due_date: z.string().nullable(),
  paid_date: z.string().nullable(),
  organization_name: z.string(),
  organization_tax_number: z.string(),
  organization_bank_account_number: z.string(),
  organization_bank_account_iban: z.string(),
  organization_swift: z.string(),
  partner_id: z.number().nullable(),
  partner_name: z.string(),
  partner_tax_number: z.string(),
  partner_iban: z.string(),
  partner_swift: z.string(),
  partner_account_number: z.string(),
  comment: z.string(),
  online_szamla_status: z.string(),
  items: z.array(BillingoInvoiceItemSchema).optional(),
  item_count: z.number().optional(),
  last_modified: z.string(),
  created_at: z.string(),
});

export type BillingoInvoiceSchemaType = z.infer<typeof BillingoInvoiceSchema>;

export const BillingoSyncLogSchema = z.object({
  id: z.number(),
  company: z.number(),
  company_name: z.string(),
  sync_type: z.string(),
  invoices_processed: z.number(),
  invoices_created: z.number(),
  invoices_updated: z.number(),
  invoices_skipped: z.number(),
  items_extracted: z.number(),
  sync_duration_seconds: z.number().nullable(),
  api_calls_made: z.number(),
  errors: z.string(),
  status: z.string(),
  started_at: z.string(),
  completed_at: z.string().nullable(),
});

export type BillingoSyncLogSchemaType = z.infer<typeof BillingoSyncLogSchema>;

export const CompanyBillingoSettingsSchema = z.object({
  id: z.number(),
  company: z.number(),
  api_key: z.string().optional(), // write-only
  has_api_key: z.boolean(),
  last_sync_time: z.string().nullable(),
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type CompanyBillingoSettingsSchemaType = z.infer<typeof CompanyBillingoSettingsSchema>;
```

### Validation:
```bash
# Check TypeScript compilation
cd frontend
npx tsc --noEmit
```

**Expected result**: No TypeScript errors

---

## Task 9: Update Documentation Files

### Action: MODIFY
### Files:
- `DATABASE_DOCUMENTATION.md`
- `FEATURES.md`
- `API_GUIDE.md`

### Changes:

#### DATABASE_DOCUMENTATION.md
```markdown
# ADD after bank_transfers_navconfiguration section

## XX. **bank_transfers_companybillingosettings**
**Table Comment:** *Billingo API configuration for invoice synchronization. One configuration per company with encrypted API key storage.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for Billingo settings |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company owner of this configuration |
| `api_key` | VARCHAR(255) | NOT NULL | Encrypted Billingo API key (X-API-KEY header, encrypted with Fernet) |
| `last_sync_time` | TIMESTAMP | NULL | Last successful sync timestamp |
| `is_active` | BOOLEAN | DEFAULT TRUE | Enable/disable sync for this company |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Configuration creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `company_id`
- Index on `is_active`

**Security Notes:**
- `api_key` is encrypted using Fernet symmetric encryption
- Decryption handled by `CredentialManager` service

---

## XX. **bank_transfers_billingoinvoice**
**Table Comment:** *Billingo invoice/document records from /documents API endpoint. Company-scoped for multi-tenant isolation.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Billingo document ID from API (not auto-increment) |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company owner of this invoice |
| `invoice_number` | VARCHAR(50) | NOT NULL | Invoice number (e.g., "INV-2025-204") |
| `type` | VARCHAR(30) | NOT NULL | Document type: invoice, receipt, proforma, etc. |
| `correction_type` | VARCHAR(30) | | Correction document type if applicable |
| `cancelled` | BOOLEAN | DEFAULT FALSE | Whether invoice is cancelled |
| `block_id` | INTEGER | NULL | Billingo block ID |
| `payment_status` | VARCHAR(30) | NOT NULL | Payment status: paid, unpaid, overdue, etc. |
| `payment_method` | VARCHAR(30) | | Payment method: wire_transfer, cash, card, etc. |
| `gross_total` | DECIMAL(15,2) | NOT NULL | Total gross amount |
| `currency` | VARCHAR(5) | NOT NULL | Currency code (HUF, EUR, USD, etc.) |
| `conversion_rate` | DECIMAL(10,6) | DEFAULT 1 | Currency conversion rate to HUF |
| `invoice_date` | DATE | NOT NULL | Invoice issue date |
| `fulfillment_date` | DATE | NULL | Service/product fulfillment date |
| `due_date` | DATE | NULL | Payment due date |
| `paid_date` | DATE | NULL | Actual payment date |
| `organization_name` | VARCHAR(255) | NOT NULL | Our company name from Billingo |
| `organization_tax_number` | VARCHAR(50) | NOT NULL | Our company tax number |
| `organization_bank_account_number` | VARCHAR(100) | | Our bank account number |
| `organization_bank_account_iban` | VARCHAR(100) | | Our IBAN |
| `organization_swift` | VARCHAR(20) | | Our SWIFT/BIC code |
| `partner_id` | BIGINT | NULL | Billingo partner ID |
| `partner_name` | VARCHAR(255) | NOT NULL | Customer/supplier name |
| `partner_tax_number` | VARCHAR(50) | | Customer/supplier tax number |
| `partner_iban` | VARCHAR(100) | | Customer/supplier IBAN |
| `partner_swift` | VARCHAR(20) | | Customer/supplier SWIFT/BIC |
| `partner_account_number` | VARCHAR(100) | | Customer/supplier account number |
| `comment` | TEXT | | Invoice comment/notes |
| `online_szamla_status` | VARCHAR(30) | | Online Számla integration status |
| `last_modified` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |

**Indexes:**
- Primary key on `id`
- Composite index on `company_id, invoice_date`
- Composite index on `company_id, payment_status`
- Composite index on `company_id, partner_tax_number`
- Index on `invoice_number`
- Index on `payment_status`
- Index on `invoice_date`

---

## XX. **bank_transfers_billingoinvoiceitem**
**Table Comment:** *Line items for Billingo invoices. Represents individual products/services on each invoice.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for line item |
| `invoice_id` | BIGINT | NOT NULL, FK(bank_transfers_billingoinvoice.id) | Reference to parent invoice |
| `product_id` | BIGINT | NULL | Billingo product ID if applicable |
| `name` | VARCHAR(255) | NOT NULL | Product/service name |
| `quantity` | DECIMAL(10,2) | NOT NULL | Quantity |
| `unit` | VARCHAR(20) | NOT NULL | Unit of measure (PIECE, HOUR, LITER, etc.) |
| `net_unit_price` | DECIMAL(15,2) | NOT NULL | Net price per unit |
| `net_amount` | DECIMAL(15,2) | NOT NULL | Total net amount for line |
| `gross_amount` | DECIMAL(15,2) | NOT NULL | Total gross amount for line |
| `vat` | VARCHAR(10) | NOT NULL | VAT rate (e.g., "27%", "5%", "0%") |
| `entitlement` | VARCHAR(50) | | VAT entitlement type |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key index on `invoice_id`

---

## XX. **bank_transfers_billingosynclog**
**Table Comment:** *Audit log for Billingo invoice synchronization operations with error tracking and performance metrics.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for sync log entry |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company for which sync was performed |
| `sync_type` | VARCHAR(20) | NOT NULL | Type: MANUAL or AUTOMATIC |
| `invoices_processed` | INTEGER | DEFAULT 0 | Total invoices processed in this sync |
| `invoices_created` | INTEGER | DEFAULT 0 | New invoices created |
| `invoices_updated` | INTEGER | DEFAULT 0 | Existing invoices updated |
| `invoices_skipped` | INTEGER | DEFAULT 0 | Invoices skipped due to errors |
| `items_extracted` | INTEGER | DEFAULT 0 | Total line items extracted |
| `sync_duration_seconds` | INTEGER | NULL | Sync operation duration in seconds |
| `api_calls_made` | INTEGER | DEFAULT 0 | Number of API calls to Billingo |
| `errors` | TEXT | | JSON array of errors encountered |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'RUNNING' | Status: RUNNING, COMPLETED, FAILED, PARTIAL |
| `started_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Sync start timestamp |
| `completed_at` | TIMESTAMP | NULL | Sync completion timestamp |

**Indexes:**
- Primary key on `id`
- Composite index on `company_id, started_at` (DESC)
- Index on `status`
- Index on `sync_type`

**Constraints:**
- `status` CHECK constraint: VALUES ('RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL')
- `sync_type` CHECK constraint: VALUES ('MANUAL', 'AUTOMATIC')
```

#### FEATURES.md
```markdown
# ADD to Active Features section

### Sync Features (2)
- **NAV_SYNC**: NAV invoice synchronization and import
- **BILLINGO_SYNC**: Billingo invoice synchronization and import (NEW)
```

#### API_GUIDE.md
```markdown
# ADD new section after Bank Transactions

### Billingo Invoices
```bash
# List Billingo invoices
GET /api/billingo-invoices/?payment_status=paid&search=ACME

# Get invoice details with items
GET /api/billingo-invoices/{id}/

# Manual sync trigger (ADMIN only)
POST /api/billingo-invoices/sync/

# Response
{
  "message": "Sync completed successfully",
  "results": {
    "invoices_processed": 42,
    "invoices_created": 5,
    "invoices_updated": 37,
    "invoices_skipped": 0,
    "items_extracted": 156,
    "api_calls": 3,
    "duration_seconds": 8,
    "errors": []
  }
}

# View sync history
GET /api/billingo-invoices/sync_history/
```

### Billingo Settings
```bash
# Get settings
GET /api/billingo-settings/

# Create/update settings (ADMIN only)
POST /api/billingo-settings/
PUT /api/billingo-settings/{id}/
{
  "api_key": "your-billingo-api-key",
  "is_active": true
}

# Response
{
  "id": 1,
  "company": 1,
  "has_api_key": true,
  "last_sync_time": "2025-10-26T14:30:00Z",
  "is_active": true,
  "created_at": "2025-10-26T10:00:00Z",
  "updated_at": "2025-10-26T14:30:00Z"
}
```
```

### Validation:
```bash
# Check documentation files render correctly
cat DATABASE_DOCUMENTATION.md | grep billingo
cat FEATURES.md | grep BILLINGO
cat API_GUIDE.md | grep billingo
```

**Expected result**: All documentation updates are present

---

## Task 10: Setup Cron Job

### Action: ADD
### File: Server crontab (manual setup required)

### Changes:
```bash
# ADD to server crontab (crontab -e)
# Run Billingo sync every 30 minutes
*/30 * * * * /path/to/venv/bin/python /path/to/manage.py sync_billingo_invoices >> /var/log/billingo_sync.log 2>&1
```

### Validation:
```bash
# List current cron jobs
crontab -l

# Test manual run
/path/to/venv/bin/python /path/to/manage.py sync_billingo_invoices

# Check log file
tail -f /var/log/billingo_sync.log
```

**Expected result**: Cron job appears in crontab, manual run succeeds

---

## Implementation Strategy

### Dependencies
1. Task 1 (Models) must complete before all other tasks
2. Task 2 (Service) depends on Task 1
3. Task 3 (Management Command) depends on Task 2
4. Task 4 (Serializers) depends on Task 1
5. Task 5 (ViewSets) depends on Task 2 and Task 4
6. Task 6 (Feature Flag) can run in parallel with Task 7-9
7. Task 7-8 (Frontend Types/Schemas) can run in parallel
8. Task 9 (Documentation) can run at any time
9. Task 10 (Cron) should be last

### Implementation Order
```
Phase 1: Backend Models & Service
├── Task 1: Database Models (2 hours)
├── Task 2: Sync Service (4 hours)
└── Task 3: Management Command (1 hour)

Phase 2: API Endpoints
├── Task 4: Serializers (2 hours)
├── Task 5: ViewSets (3 hours)
└── Task 6: Feature Flag (0.5 hours)

Phase 3: Frontend Integration
├── Task 7: TypeScript Types (1 hour)
└── Task 8: Zod Schemas (1 hour)

Phase 4: Documentation & Deployment
├── Task 9: Documentation Updates (2 hours)
└── Task 10: Cron Setup (0.5 hours)

Total Estimated Time: 17 hours
```

### Progressive Enhancement
- **Phase 1**: Core sync functionality works via management command
- **Phase 2**: REST API available for manual triggers and viewing
- **Phase 3**: Frontend can display and manage invoices
- **Phase 4**: Full documentation and automated sync via cron

### Rollback Plan
If issues occur during deployment:

1. **Database rollback**: `python manage.py migrate bank_transfers <previous_migration>`
2. **Feature flag disable**: Set `BILLINGO_SYNC` to disabled for all companies
3. **Cron disable**: Comment out cron job line
4. **API disable**: Remove ViewSet registration from `urls.py`

---

## Risk Assessment & Mitigations

### Risk 1: API Rate Limiting (429 errors)
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**:
- Implement exponential backoff retry logic (3 attempts with increasing delays)
- Respect `Retry-After` header from API responses
- Log rate limit events for monitoring
- Consider reducing sync frequency if rate limits are consistently hit

### Risk 2: Large Invoice Datasets (Slow Sync)
**Likelihood**: Medium
**Impact**: Low
**Mitigation**:
- Pagination already implemented (100 per page max)
- Track sync performance metrics in `BillingoSyncLog`
- Can add filtering by date range if needed in future
- Database indexes on key query fields

### Risk 3: API Key Security
**Likelihood**: Low
**Impact**: High
**Mitigation**:
- API keys encrypted with Fernet (existing pattern from NAV integration)
- Write-only serializer field (never expose in API responses)
- ADMIN-only access to settings management
- Audit trail in sync logs

### Risk 4: Sync Errors for Individual Companies
**Likelihood**: Medium
**Impact**: Low
**Mitigation**:
- Per-company error handling (continue sync for other companies)
- Detailed error logging in `BillingoSyncLog.errors` field
- Status indicators: COMPLETED, PARTIAL, FAILED
- Automatic retry on next scheduled sync (30 min)

### Risk 5: Database Migration Conflicts
**Likelihood**: Low
**Impact**: Medium
**Mitigation**:
- Migration designed to be reversible
- No changes to existing tables
- Test migration on staging environment first
- Rollback plan documented

---

## Testing Strategy

### Unit Tests
```python
# tests/test_billingo_sync_service.py
- test_fetch_documents_page_success()
- test_fetch_documents_page_rate_limit_retry()
- test_process_invoice_create()
- test_process_invoice_update()
- test_sync_company_success()
- test_sync_company_no_settings()
- test_sync_company_api_error()
- test_sync_all_companies()

# tests/test_billingo_api_views.py
- test_invoice_list_authenticated()
- test_invoice_detail()
- test_manual_sync_admin_only()
- test_sync_history()
- test_settings_create_admin_only()
- test_settings_update_api_key_encryption()
```

### Integration Tests
```python
# tests/test_billingo_integration.py
- test_full_sync_flow_with_mock_api()
- test_pagination_handling()
- test_error_recovery()
- test_sync_log_creation()
```

### Manual Testing Checklist
- [ ] Create Billingo API key in Billingo dashboard
- [ ] Configure settings via API endpoint
- [ ] Trigger manual sync
- [ ] Verify invoices appear in database
- [ ] Verify invoice items are extracted
- [ ] Check sync log entries
- [ ] Test rate limit retry (mock 429 response)
- [ ] Test error handling (invalid API key)
- [ ] Run management command
- [ ] Check cron job execution in logs

---

## Quality Checklist

- [x] Current state fully documented
- [x] Desired state clearly defined
- [x] All objectives measurable
- [x] Tasks ordered by dependency
- [x] Each task has validation command
- [x] Risks identified with mitigations
- [x] Rollback strategy included
- [x] Integration points noted
- [x] Testing strategy defined
- [x] Documentation updates included

---

## Next Steps After PRP Approval

1. **Review with user**: Confirm approach aligns with expectations
2. **Obtain Billingo API key**: Test API access before development
3. **Create feature branch**: `git checkout -b feature/billingo-api-interface`
4. **Execute tasks in order**: Follow dependency chain
5. **Test each phase**: Validate before moving to next phase
6. **Update documentation**: Keep docs in sync with implementation
7. **Deploy to staging**: Test full flow in staging environment
8. **Production deployment**: Enable feature flag for companies
9. **Monitor sync logs**: Watch for errors in first 24 hours

---

**Remember**: Focus on the transformation journey, not just the destination. Each task builds upon the previous one to create a robust, maintainable Billingo integration following established architectural patterns.
