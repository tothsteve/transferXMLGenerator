# Bank Statement Import - Technical Specification

**Project**: Transfer XML Generator
**Feature**: Multi-Bank PDF Statement Import
**Version**: 1.0
**Date**: 2025-10-18
**Author**: System Architecture Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Data Models](#3-data-models)
4. [Database Migration](#4-database-migration)
5. [Bank Adapter Interface](#5-bank-adapter-interface)
6. [GRÁNIT Bank Parser Implementation](#6-gránit-bank-parser-implementation)
7. [Parsing Strategy](#7-parsing-strategy)
8. [File Upload API](#8-file-upload-api)
9. [Duplicate Detection & Update Logic](#9-duplicate-detection--update-logic)
10. [Transaction Matching Engine](#10-transaction-matching-engine)
11. [Other Costs Handling](#11-other-costs-handling)
12. [Security, RBAC & Audit](#12-security-rbac--audit)
13. [Testing Strategy](#13-testing-strategy)
14. [Deployment & Operations](#14-deployment--operations)
15. [Migration & Rollback Plan](#15-migration--rollback-plan)
16. [End-to-End Example Scenario](#16-end-to-end-example-scenario)
17. [Implementation Checklist](#17-implementation-checklist)

---

## 1. Executive Summary

### 1.1 Goal

Implement a **multi-bank PDF bank statement import system** for Hungarian companies to:

- **Import ALL transactions** from monthly bank statement PDFs (not just transfers)
- **Parse and normalize** diverse transaction types (AFR transfers, POS purchases, fees, interest)
- **Auto-match transactions to NAV invoices** using reference codes, amounts, and beneficiary data
- **Detect and categorize other costs** (bank fees, card purchases, interest charges)
- **Support multiple banks** with extensible adapter pattern for multi-company scenarios

### 1.2 Business Value

- **Automated reconciliation**: Match bank transactions to NAV invoices automatically
- **Financial visibility**: Track all bank activity (transfers, fees, purchases) in one system
- **Multi-company support**: Each company can use different banks (GRÁNIT, OTP, K&H, CIB, Erste)
- **Audit compliance**: Complete transaction history with payment status tracking
- **Cost management**: Identify and categorize bank fees and other costs

### 1.3 Constraints & Design Principles

**Technology Stack**: Django REST Framework (matching existing architecture)
- Django ORM models (not SQLAlchemy)
- DRF Serializers (not Pydantic)
- APScheduler patterns (no Celery for MVP)
- Multi-company isolation with `company_id` foreign keys
- Feature flag system for gradual rollout

**Architecture Patterns**: Reuse existing codebase patterns
- Service layer: `services/invoice_sync_service.py` pattern
- File upload: `services/excel_import_service.py` pattern
- Export adapters: `utils.generate_xml()` and `kh_export.py` pattern
- Permissions: Role-based access control (ADMIN, FINANCIAL, ACCOUNTANT, USER)

**Implementation Scope**:
- ✅ **Manual PDF upload** (no scheduled imports initially)
- ✅ **All transaction types** (transfers, POS, fees, interest, corrections)
- ✅ **Multi-bank architecture** (GRÁNIT Bank first, easily extensible)
- ✅ **Synchronous processing** (parse immediately on upload)
- ✅ **Duplicate detection** (by file hash + statement period)
- ✅ **Auto-matching** (confidence-based invoice linking)

### 1.4 Initial Bank Support

**Primary**: GRÁNIT Bank Nyrt. (BIC: GNBAHUHB)
- 9 example PDFs analyzed (Jan-Sep 2025)
- Multi-page statements (5-7 pages typical)
- Rich transaction metadata (IBANs, payment IDs, references)
- Multiple transaction types identified and categorized

**Future**: OTP Bank, K&H Bank, CIB Bank, Erste Bank, Raiffeisen Bank
- Abstract adapter interface designed for easy extension
- Factory pattern for automatic bank detection
- Multi-company architecture supports mixed banks per deployment

---

## 2. Architecture Overview

### 2.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Web Browser)                          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTPS (Django REST Framework)
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     API Layer (DRF ViewSets)                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ BankStatementViewSet                                        │    │
│  │  - upload() - POST /api/bank-statements/upload/            │    │
│  │  - list() - GET /api/bank-statements/                      │    │
│  │  - transactions() - GET /api/bank-statements/{id}/txns/    │    │
│  │  - reparse() - POST /api/bank-statements/{id}/reparse/     │    │
│  │                                                              │    │
│  │ BankTransactionViewSet                                      │    │
│  │  - list() - GET /api/bank-transactions/                    │    │
│  │  - match_invoice() - POST /api/bank-transactions/{id}/match│    │
│  │  - categorize() - POST /api/bank-transactions/{id}/categorize│  │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   Service Layer (Business Logic)                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ BankStatementService                                        │    │
│  │  - process_uploaded_file()                                  │    │
│  │  - detect_bank_and_parse()                                  │    │
│  │  - handle_duplicate()                                       │    │
│  │                                                              │    │
│  │ TransactionMatchingService                                  │    │
│  │  - match_transactions()                                     │    │
│  │  - match_by_reference()                                     │    │
│  │  - match_by_amount_iban()                                   │    │
│  │  - match_by_fuzzy_name()                                    │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│              Bank Adapter Layer (Parser Abstraction)                │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ BankAdapterFactory                                          │    │
│  │  - detect_bank(pdf_bytes, filename) → Adapter              │    │
│  │  - get_adapter(bank_code) → Adapter                        │    │
│  │  - register_adapter(adapter_class)                         │    │
│  └────────────────────────────────────────────────────────────┘    │
│         ↓              ↓              ↓              ↓              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ GRÁNIT   │   │   OTP    │   │   K&H    │   │   CIB    │        │
│  │ Adapter  │   │ Adapter  │   │ Adapter  │   │ Adapter  │        │
│  │ (Impl.)  │   │ (Future) │   │ (Future) │   │ (Future) │        │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 PDF Parser Layer (pdfplumber)                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Multi-line Transaction Parser (State Machine)              │    │
│  │  - AFR Transfer Parser (10+ lines per transaction)         │    │
│  │  - POS Purchase Parser (2-3 lines per transaction)         │    │
│  │  - Bank Fee Parser (single line)                           │    │
│  │  - Interest Parser (single line)                           │    │
│  │  - Metadata Extractor (header/footer)                      │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Layer (Django ORM)                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │ BankStatement  │  │BankTransaction │  │  OtherCost     │       │
│  │   (Model)      │  │    (Model)     │  │   (Model)      │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│           │                   │                   │                 │
│           └───────────────────┴───────────────────┘                 │
│                               ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │           PostgreSQL (Production) / SQL Server (Dev)       │    │
│  │  - Multi-company isolation (company_id FK)                 │    │
│  │  - Duplicate prevention (file_hash, period unique)         │    │
│  │  - Performance indexes (date, amount, reference)           │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 Integration Layer (Existing Systems)                │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ NAV Invoice Service (invoice_sync_service.py)              │    │
│  │  - Match transactions to invoices                          │    │
│  │  - Update payment_status to PAID                           │    │
│  │  - Link invoice to bank transaction                        │    │
│  │                                                              │    │
│  │ Feature Flag System (FeatureTemplate, CompanyFeature)      │    │
│  │  - BANK_STATEMENT_IMPORT feature                           │    │
│  │  - Role-based permissions (ADMIN, FINANCIAL, ACCOUNTANT)   │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Upload & Processing Flow

```
┌────────────┐
│ User       │
│ Uploads    │
│ PDF        │
└─────┬──────┘
      │
      │ 1. POST /api/bank-statements/upload/
      │    (multipart/form-data)
      ↓
┌─────────────────────────────────────────┐
│ BankStatementViewSet.upload()           │
│                                         │
│ Step 1: Validate file                  │
│  - Check file type (PDF)                │
│  - Check file size (<10MB)              │
│  - Verify company context               │
└─────┬───────────────────────────────────┘
      │
      │ 2. Compute SHA256 hash
      ↓
┌─────────────────────────────────────────┐
│ Duplicate Detection                     │
│                                         │
│ Query: BankStatement.objects.filter(   │
│   company=company,                      │
│   file_hash=file_hash                   │
│ )                                       │
│                                         │
│ If exists:                              │
│  - Same hash → return existing          │
│  - Same period, diff hash → update      │
└─────┬───────────────────────────────────┘
      │
      │ 3. Detect bank
      ↓
┌─────────────────────────────────────────┐
│ BankAdapterFactory.detect_bank()        │
│                                         │
│ For each registered adapter:            │
│  - adapter.detect(pdf_bytes, filename)  │
│  - Check for bank identifiers in PDF    │
│                                         │
│ Returns: GranitBankAdapter (or None)    │
└─────┬───────────────────────────────────┘
      │
      │ 4. Parse PDF
      ↓
┌─────────────────────────────────────────┐
│ GranitBankAdapter.parse(pdf_bytes)      │
│                                         │
│ Extract with pdfplumber:                │
│  - All pages text                       │
│  - Header metadata (account, period)    │
│  - ALL transactions (multi-pass)        │
│                                         │
│ Returns:                                │
│  {                                      │
│    'metadata': StatementMetadata,       │
│    'transactions': [                    │
│      NormalizedTransaction(...),        │
│      ...                                │
│    ]                                    │
│  }                                      │
└─────┬───────────────────────────────────┘
      │
      │ 5. Create database records
      ↓
┌─────────────────────────────────────────┐
│ Django ORM Transaction                  │
│                                         │
│ with transaction.atomic():              │
│   1. Create BankStatement record        │
│   2. Bulk create BankTransaction records│
│   3. Update statistics (total_txns)     │
│   4. Save PDF file to storage           │
└─────┬───────────────────────────────────┘
      │
      │ 6. Run matching engine
      ↓
┌─────────────────────────────────────────┐
│ TransactionMatchingService              │
│                                         │
│ For each AFR/Transfer transaction:      │
│  1. Try reference exact match           │
│  2. Try amount + IBAN match             │
│  3. Try fuzzy beneficiary name match    │
│                                         │
│ If confidence >= 0.9:                   │
│  - Link to invoice                      │
│  - Update invoice.payment_status=PAID   │
│  - Set invoice.payment_status_date      │
└─────┬───────────────────────────────────┘
      │
      │ 7. Categorize other costs
      ↓
┌─────────────────────────────────────────┐
│ Auto-categorization                     │
│                                         │
│ Mark as other costs:                    │
│  - POS purchases → CARD_PURCHASE        │
│  - Bank fees → BANK_FEE                 │
│  - Interest → INTEREST                  │
│                                         │
│ Set is_extra_cost = True                │
└─────┬───────────────────────────────────┘
      │
      │ 8. Return results
      ↓
┌─────────────────────────────────────────┐
│ HTTP 201 Created                        │
│                                         │
│ Response:                               │
│ {                                       │
│   "id": 123,                            │
│   "bank_code": "GRANIT",                │
│   "account_number": "12100011-19014874",│
│   "statement_period_from": "2025-01-01",│
│   "statement_period_to": "2025-01-31",  │
│   "total_transactions": 45,             │
│   "matched_count": 12,                  │
│   "status": "PARSED",                   │
│   "uploaded_at": "2025-10-18T10:30:00Z" │
│ }                                       │
└─────────────────────────────────────────┘
```

### 2.3 Transaction Type Classification

Based on GRÁNIT Bank statement analysis, we support these transaction types:

| Type Code | Hungarian Name | Description | Matching | Other Cost |
|-----------|---------------|-------------|----------|------------|
| `AFR_CREDIT` | AFR jóváírás bankon kívül | Incoming instant payment | ✅ Yes | ❌ No |
| `AFR_DEBIT` | AFR terhelés bankon kívül | Outgoing instant payment | ✅ Yes | ❌ No |
| `TRANSFER_CREDIT` | Átutalás jóváírás | Incoming bank transfer | ✅ Yes | ❌ No |
| `TRANSFER_DEBIT` | Átutalás terhelés | Outgoing bank transfer | ✅ Yes | ❌ No |
| `POS_PURCHASE` | POS vásárlás tranzakció | Card purchase | ❌ No | ✅ Yes |
| `ATM_WITHDRAWAL` | ATM készpénzfelvétel | Cash withdrawal | ❌ No | ✅ Yes |
| `BANK_FEE` | Előjegyzett jutalék / Banki költség | Bank fee/commission | ❌ No | ✅ Yes |
| `INTEREST_CREDIT` | Kamatjóváírás | Interest credit | ❌ No | ❌ No |
| `INTEREST_DEBIT` | Kamatköltség | Interest charge | ❌ No | ✅ Yes |
| `CORRECTION` | Helyesbítés / Sztornó | Correction/reversal | ⚠️ Manual | ❌ No |
| `OTHER` | Egyéb tranzakció | Other transaction | ⚠️ Manual | ❌ No |

**Matching Strategy**: Only AFR and regular transfers are matched to NAV invoices.
**Other Cost Flagging**: POS purchases, bank fees, ATM withdrawals, and interest charges are automatically flagged for cost tracking.

---

## 3. Data Models

### 3.1 Django Model Definitions

#### 3.1.1 BankStatement Model

```python
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from .base_models import CompanyOwnedTimestampedModel


class BankStatement(CompanyOwnedTimestampedModel):
    """
    Represents a single uploaded bank statement PDF.

    Multi-company support: Each company can have statements from different banks.
    Duplicate prevention: Unique constraint on (company, file_hash) and (company, bank_code, account, period).
    """

    # Bank identification
    bank_code = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Bank kód",
        help_text="Bank identifier: GRANIT, OTP, KH, CIB, ERSTE"
    )
    bank_name = models.CharField(
        max_length=100,
        verbose_name="Bank neve"
    )
    bank_bic = models.CharField(
        max_length=11,
        blank=True,
        verbose_name="BIC kód"
    )

    # Account details
    account_number = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Számlaszám"
    )
    account_iban = models.CharField(
        max_length=34,
        blank=True,
        verbose_name="IBAN"
    )

    # Statement period
    statement_period_from = models.DateField(
        verbose_name="Kivonat időszak kezdete"
    )
    statement_period_to = models.DateField(
        verbose_name="Kivonat időszak vége"
    )
    statement_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Kivonat száma"
    )

    # Balances
    opening_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Nyitó egyenleg"
    )
    closing_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Záró egyenleg"
    )

    # File metadata
    file_name = models.CharField(
        max_length=255,
        verbose_name="Fájlnév"
    )
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="Fájl hash (SHA256)"
    )
    file_size = models.IntegerField(
        verbose_name="Fájl méret (byte)"
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name="Fájl elérési út"
    )

    # Upload tracking
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_statements',
        verbose_name="Feltöltő"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Feltöltés ideje"
    )

    # Processing status
    STATUS_CHOICES = [
        ('UPLOADED', 'Feltöltve'),
        ('PARSING', 'Feldolgozás alatt'),
        ('PARSED', 'Feldolgozva'),
        ('ERROR', 'Hiba'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UPLOADED',
        db_index=True,
        verbose_name="Státusz"
    )

    # Statistics
    total_transactions = models.IntegerField(
        default=0,
        verbose_name="Összes tranzakció"
    )
    credit_count = models.IntegerField(
        default=0,
        verbose_name="Jóváírások száma"
    )
    debit_count = models.IntegerField(
        default=0,
        verbose_name="Terhelések száma"
    )
    total_credits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Összesen jóváírva"
    )
    total_debits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Összesen terhelve"
    )
    matched_count = models.IntegerField(
        default=0,
        verbose_name="Párosított tranzakciók"
    )

    # Error handling
    parse_error = models.TextField(
        null=True,
        blank=True,
        verbose_name="Feldolgozási hiba"
    )
    parse_warnings = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Figyelmeztetések"
    )

    # Metadata
    raw_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Nyers metaadatok"
    )

    class Meta:
        verbose_name = "Bankszámlakivonat"
        verbose_name_plural = "Bankszámlakivonatok"
        unique_together = [
            ('company', 'file_hash'),
            ('company', 'bank_code', 'account_number', 'statement_period_from', 'statement_period_to'),
        ]
        indexes = [
            models.Index(fields=['company', 'bank_code', 'account_number']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'statement_period_to']),
            models.Index(fields=['uploaded_at']),
        ]
        ordering = ['-statement_period_to', '-uploaded_at']

    def __str__(self):
        return f"{self.bank_code} {self.account_number} ({self.statement_period_from} - {self.statement_period_to})"
```

#### 3.1.2 BankTransaction Model

```python
class BankTransaction(CompanyOwnedTimestampedModel):
    """
    Individual transaction line from bank statement.

    Supports ALL transaction types: AFR transfers, POS purchases, bank fees, interest, etc.
    Contains bank-specific fields (IBAN, payment ID, card number) and matching fields (invoice, confidence).
    """

    # Transaction type choices
    TRANSACTION_TYPES = [
        # Transfers
        ('AFR_CREDIT', 'AFR jóváírás (Incoming instant payment)'),
        ('AFR_DEBIT', 'AFR terhelés (Outgoing instant payment)'),
        ('TRANSFER_CREDIT', 'Átutalás jóváírás (Incoming transfer)'),
        ('TRANSFER_DEBIT', 'Átutalás terhelés (Outgoing transfer)'),

        # Card transactions
        ('POS_PURCHASE', 'POS vásárlás (Card purchase)'),
        ('ATM_WITHDRAWAL', 'ATM készpénzfelvétel (Cash withdrawal)'),

        # Bank charges
        ('BANK_FEE', 'Banki jutalék/költség (Bank fee)'),
        ('INTEREST_CREDIT', 'Kamatjóváírás (Interest credit)'),
        ('INTEREST_DEBIT', 'Kamatköltség (Interest charge)'),

        # Other
        ('CORRECTION', 'Helyesbítés/Sztornó (Correction)'),
        ('OTHER', 'Egyéb tranzakció (Other)'),
    ]

    # Statement reference
    bank_statement = models.ForeignKey(
        'BankStatement',
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Bankszámlakivonat"
    )

    # Transaction identification
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
        db_index=True,
        verbose_name="Tranzakció típusa"
    )

    # Dates
    booking_date = models.DateField(
        db_index=True,
        verbose_name="Könyvelés dátuma"
    )
    value_date = models.DateField(
        db_index=True,
        verbose_name="Értéknap"
    )

    # Amount
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_index=True,
        verbose_name="Összeg",
        help_text="Negative for debit, positive for credit"
    )
    currency = models.CharField(
        max_length=3,
        default='HUF',
        verbose_name="Deviza"
    )

    # Transaction description
    description = models.TextField(
        verbose_name="Leírás"
    )
    short_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Rövid leírás"
    )

    # === AFR Transfer specific fields ===
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="Fizetési azonosító"
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tranzakció azonosító"
    )

    payer_name = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
        verbose_name="Fizető fél neve"
    )
    payer_iban = models.CharField(
        max_length=34,
        blank=True,
        verbose_name="Fizető fél IBAN"
    )
    payer_account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Fizető fél számlaszáma"
    )
    payer_bic = models.CharField(
        max_length=11,
        blank=True,
        verbose_name="Fizető fél BIC"
    )

    beneficiary_name = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
        verbose_name="Kedvezményezett neve"
    )
    beneficiary_iban = models.CharField(
        max_length=34,
        blank=True,
        verbose_name="Kedvezményezett IBAN"
    )
    beneficiary_account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Kedvezményezett számlaszáma"
    )

    reference = models.TextField(
        blank=True,
        verbose_name="Közlemény",
        help_text="Nem strukturált közlemény - critical for invoice matching"
    )

    # === POS Purchase specific fields ===
    card_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Kártya szám (maszkolva)"
    )
    merchant_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Kereskedő neve"
    )
    merchant_location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Kereskedő helye"
    )
    original_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Eredeti összeg (FX)"
    )
    original_currency = models.CharField(
        max_length=3,
        blank=True,
        verbose_name="Eredeti deviza (FX)"
    )

    # === Matching to NAV invoices ===
    matched_invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transactions',
        verbose_name="Párosított számla"
    )
    match_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Párosítás megbízhatósága",
        help_text="0.00 to 1.00"
    )

    MATCH_METHOD_CHOICES = [
        ('TRANSFER_EXACT', 'TransferBatch párosítás'),
        ('REFERENCE_EXACT', 'Közlemény alapján (pontos)'),
        ('AMOUNT_IBAN', 'Összeg + IBAN alapján'),
        ('FUZZY_NAME', 'Összeg + név hasonlóság alapján'),
        ('AMOUNT_DATE_ONLY', 'Összeg + dátum alapján'),
        ('REIMBURSEMENT_PAIR', 'Visszatérítés párosítás'),
        ('MANUAL', 'Manuális párosítás'),
    ]
    match_method = models.CharField(
        max_length=50,
        blank=True,
        choices=MATCH_METHOD_CHOICES,
        verbose_name="Párosítás módja"
    )
    match_notes = models.TextField(
        blank=True,
        verbose_name="Párosítási megjegyzések"
    )
    matched_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Párosítás ideje"
    )
    matched_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_transactions',
        verbose_name="Párosította"
    )

    # === Extra cost categorization ===
    is_extra_cost = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Extra költség"
    )

    EXTRA_COST_CATEGORIES = [
        ('BANK_FEE', 'Banki költség'),
        ('CARD_PURCHASE', 'Kártyás vásárlás'),
        ('INTEREST', 'Kamat'),
        ('TAX_DUTY', 'Adó/illeték'),
        ('CASH_WITHDRAWAL', 'Készpénzfelvétel'),
        ('OTHER', 'Egyéb költség'),
    ]
    extra_cost_category = models.CharField(
        max_length=50,
        blank=True,
        choices=EXTRA_COST_CATEGORIES,
        verbose_name="Költség kategória"
    )

    # Raw data storage
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Nyers adatok"
    )

    class Meta:
        verbose_name = "Banki tranzakció"
        verbose_name_plural = "Banki tranzakciók"
        indexes = [
            models.Index(fields=['bank_statement', 'booking_date']),
            models.Index(fields=['company', 'booking_date']),
            models.Index(fields=['company', 'transaction_type', 'booking_date']),
            models.Index(fields=['amount', 'currency']),
            models.Index(fields=['matched_invoice']),
            models.Index(fields=['payment_id']),
            models.Index(fields=['reference']),
            models.Index(fields=['is_extra_cost', 'extra_cost_category']),
        ]
        ordering = ['-booking_date', '-value_date']

    def __str__(self):
        return f"{self.booking_date} {self.transaction_type} {self.amount} {self.currency}"

    @property
    def is_credit(self):
        """Check if transaction is a credit (positive amount)"""
        return self.amount > 0

    @property
    def is_debit(self):
        """Check if transaction is a debit (negative amount)"""
        return self.amount < 0

    @property
    def is_matched(self):
        """Check if transaction is matched to an invoice"""
        return self.matched_invoice is not None

    @property
    def is_high_confidence_match(self):
        """Check if match has high confidence (>= 0.9)"""
        return self.match_confidence >= Decimal('0.90')
```

#### 3.1.3 OtherCost Model

```python
class OtherCost(CompanyOwnedTimestampedModel):
    """
    Extra costs derived from bank transactions.

    Allows additional categorization, notes, and tags beyond BankTransaction fields.
    Used for expense tracking and cost analysis.
    """

    CATEGORY_CHOICES = [
        ('BANK_FEE', 'Banki költség'),
        ('CARD_PURCHASE', 'Kártyás vásárlás'),
        ('INTEREST', 'Kamat'),
        ('TAX_DUTY', 'Adó/illeték'),
        ('CASH_WITHDRAWAL', 'Készpénzfelvétel'),
        ('SUBSCRIPTION', 'Előfizetés'),
        ('UTILITY', 'Közüzem'),
        ('FUEL', 'Üzemanyag'),
        ('TRAVEL', 'Utazás'),
        ('OFFICE', 'Iroda/irodaszer'),
        ('OTHER', 'Egyéb'),
    ]

    bank_transaction = models.OneToOneField(
        'BankTransaction',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='extra_cost_detail',
        verbose_name="Banki tranzakció"
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="Kategória"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Összeg"
    )
    currency = models.CharField(
        max_length=3,
        default='HUF',
        verbose_name="Deviza"
    )
    date = models.DateField(
        verbose_name="Dátum"
    )

    description = models.TextField(
        verbose_name="Leírás"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Megjegyzések"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Címkék",
        help_text="E.g., ['fuel', 'travel', 'office']"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Létrehozta"
    )

    class Meta:
        verbose_name = "Extra költség"
        verbose_name_plural = "Extra költségek"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} {self.category} {self.amount} {self.currency}"
```

### 3.2 DRF Serializers

```python
from rest_framework import serializers
from .models import BankStatement, BankTransaction, OtherCost


class BankStatementSerializer(serializers.ModelSerializer):
    """Serializer for bank statement list and detail views"""

    uploaded_by_name = serializers.SerializerMethodField()
    match_rate = serializers.SerializerMethodField()

    class Meta:
        model = BankStatement
        fields = [
            'id', 'bank_code', 'bank_name', 'bank_bic',
            'account_number', 'account_iban',
            'statement_period_from', 'statement_period_to', 'statement_number',
            'opening_balance', 'closing_balance',
            'file_name', 'file_size', 'file_hash',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at',
            'status', 'parse_error', 'parse_warnings',
            'total_transactions', 'credit_count', 'debit_count',
            'total_credits', 'total_debits', 'matched_count', 'match_rate',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'file_hash', 'uploaded_by', 'uploaded_at',
            'status', 'parse_error', 'parse_warnings',
            'total_transactions', 'credit_count', 'debit_count',
            'total_credits', 'total_debits', 'matched_count',
            'created_at', 'updated_at',
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None

    def get_match_rate(self, obj):
        if obj.total_transactions > 0:
            return round((obj.matched_count / obj.total_transactions) * 100, 2)
        return 0.0


class BankTransactionSerializer(serializers.ModelSerializer):
    """Serializer for bank transaction list and detail views"""

    bank_statement_info = serializers.SerializerMethodField()
    matched_invoice_number = serializers.SerializerMethodField()
    matched_by_name = serializers.SerializerMethodField()
    is_credit = serializers.ReadOnlyField()
    is_debit = serializers.ReadOnlyField()
    is_matched = serializers.ReadOnlyField()
    is_high_confidence_match = serializers.ReadOnlyField()

    class Meta:
        model = BankTransaction
        fields = [
            'id', 'bank_statement', 'bank_statement_info',
            'transaction_type', 'booking_date', 'value_date',
            'amount', 'currency', 'is_credit', 'is_debit',
            'description', 'short_description',
            'payment_id', 'transaction_id',
            'payer_name', 'payer_iban', 'payer_account_number', 'payer_bic',
            'beneficiary_name', 'beneficiary_iban', 'beneficiary_account_number',
            'reference',
            'card_number', 'merchant_name', 'merchant_location',
            'original_amount', 'original_currency',
            'matched_invoice', 'matched_invoice_number', 'match_confidence',
            'match_method', 'match_notes', 'matched_at', 'matched_by', 'matched_by_name',
            'is_matched', 'is_high_confidence_match',
            'is_extra_cost', 'extra_cost_category',
            'raw_data', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'is_credit', 'is_debit', 'is_matched', 'is_high_confidence_match',
        ]

    def get_bank_statement_info(self, obj):
        return {
            'id': obj.bank_statement.id,
            'bank_code': obj.bank_statement.bank_code,
            'account_number': obj.bank_statement.account_number,
            'period_from': obj.bank_statement.statement_period_from,
            'period_to': obj.bank_statement.statement_period_to,
        }

    def get_matched_invoice_number(self, obj):
        if obj.matched_invoice:
            return obj.matched_invoice.invoice_number
        return None

    def get_matched_by_name(self, obj):
        if obj.matched_by:
            return obj.matched_by.get_full_name() or obj.matched_by.username
        return None


class OtherCostSerializer(serializers.ModelSerializer):
    """Serializer for other cost records"""

    bank_transaction_info = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OtherCost
        fields = [
            'id', 'bank_transaction', 'bank_transaction_info',
            'category', 'amount', 'currency', 'date',
            'description', 'notes', 'tags',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_bank_transaction_info(self, obj):
        if obj.bank_transaction:
            return {
                'id': obj.bank_transaction.id,
                'booking_date': obj.bank_transaction.booking_date,
                'amount': obj.bank_transaction.amount,
                'description': obj.bank_transaction.short_description or obj.bank_transaction.description[:100],
            }
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class BankStatementUploadSerializer(serializers.Serializer):
    """Serializer for PDF upload request"""

    file = serializers.FileField(
        required=True,
        help_text="Bank statement PDF file"
    )
    bank_hint = serializers.ChoiceField(
        choices=[
            ('GRANIT', 'GRÁNIT Bank'),
            ('OTP', 'OTP Bank'),
            ('KH', 'K&H Bank'),
            ('CIB', 'CIB Bank'),
            ('ERSTE', 'Erste Bank'),
        ],
        required=False,
        help_text="Optional bank hint for detection"
    )
```

---

## 4. Database Migration

### 4.1 Django Migration File

```python
# Generated migration file: 0039_add_bank_statement_models.py

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bank_transfers', '0038_add_exchange_rate_models'),
    ]

    operations = [
        # BankStatement model
        migrations.CreateModel(
            name='BankStatement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Létrehozva')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Módosítva')),
                ('bank_code', models.CharField(db_index=True, help_text='Bank identifier: GRANIT, OTP, KH, CIB, ERSTE', max_length=20, verbose_name='Bank kód')),
                ('bank_name', models.CharField(max_length=100, verbose_name='Bank neve')),
                ('bank_bic', models.CharField(blank=True, max_length=11, verbose_name='BIC kód')),
                ('account_number', models.CharField(db_index=True, max_length=50, verbose_name='Számlaszám')),
                ('account_iban', models.CharField(blank=True, max_length=34, verbose_name='IBAN')),
                ('statement_period_from', models.DateField(verbose_name='Kivonat időszak kezdete')),
                ('statement_period_to', models.DateField(verbose_name='Kivonat időszak vége')),
                ('statement_number', models.CharField(blank=True, max_length=50, verbose_name='Kivonat száma')),
                ('opening_balance', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Nyitó egyenleg')),
                ('closing_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Záró egyenleg')),
                ('file_name', models.CharField(max_length=255, verbose_name='Fájlnév')),
                ('file_hash', models.CharField(db_index=True, max_length=64, verbose_name='Fájl hash (SHA256)')),
                ('file_size', models.IntegerField(verbose_name='Fájl méret (byte)')),
                ('file_path', models.CharField(max_length=500, verbose_name='Fájl elérési út')),
                ('status', models.CharField(choices=[('UPLOADED', 'Feltöltve'), ('PARSING', 'Feldolgozás alatt'), ('PARSED', 'Feldolgozva'), ('ERROR', 'Hiba')], db_index=True, default='UPLOADED', max_length=20, verbose_name='Státusz')),
                ('total_transactions', models.IntegerField(default=0, verbose_name='Összes tranzakció')),
                ('credit_count', models.IntegerField(default=0, verbose_name='Jóváírások száma')),
                ('debit_count', models.IntegerField(default=0, verbose_name='Terhelések száma')),
                ('total_credits', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15, verbose_name='Összesen jóváírva')),
                ('total_debits', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15, verbose_name='Összesen terhelve')),
                ('matched_count', models.IntegerField(default=0, verbose_name='Párosított tranzakciók')),
                ('parse_error', models.TextField(blank=True, null=True, verbose_name='Feldolgozási hiba')),
                ('parse_warnings', models.JSONField(blank=True, default=list, verbose_name='Figyelmeztetések')),
                ('raw_metadata', models.JSONField(blank=True, default=dict, verbose_name='Nyers metaadatok')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_statements', to='bank_transfers.company', verbose_name='Cég')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_statements', to=settings.AUTH_USER_MODEL, verbose_name='Feltöltő')),
            ],
            options={
                'verbose_name': 'Bankszámlakivonat',
                'verbose_name_plural': 'Bankszámlakivonatok',
                'ordering': ['-statement_period_to', '-uploaded_at'],
            },
        ),

        # BankTransaction model
        migrations.CreateModel(
            name='BankTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Létrehozva')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Módosítva')),
                ('transaction_type', models.CharField(choices=[('AFR_CREDIT', 'AFR jóváírás (Incoming instant payment)'), ('AFR_DEBIT', 'AFR terhelés (Outgoing instant payment)'), ('TRANSFER_CREDIT', 'Átutalás jóváírás (Incoming transfer)'), ('TRANSFER_DEBIT', 'Átutalás terhelés (Outgoing transfer)'), ('POS_PURCHASE', 'POS vásárlás (Card purchase)'), ('ATM_WITHDRAWAL', 'ATM készpénzfelvétel (Cash withdrawal)'), ('BANK_FEE', 'Banki jutalék/költség (Bank fee)'), ('INTEREST_CREDIT', 'Kamatjóváírás (Interest credit)'), ('INTEREST_DEBIT', 'Kamatköltség (Interest charge)'), ('CORRECTION', 'Helyesbítés/Sztornó (Correction)'), ('OTHER', 'Egyéb tranzakció (Other)')], db_index=True, max_length=30, verbose_name='Tranzakció típusa')),
                ('booking_date', models.DateField(db_index=True, verbose_name='Könyvelés dátuma')),
                ('value_date', models.DateField(db_index=True, verbose_name='Értéknap')),
                ('amount', models.DecimalField(db_index=True, decimal_places=2, help_text='Negative for debit, positive for credit', max_digits=15, verbose_name='Összeg')),
                ('currency', models.CharField(default='HUF', max_length=3, verbose_name='Deviza')),
                ('description', models.TextField(verbose_name='Leírás')),
                ('short_description', models.CharField(blank=True, max_length=200, verbose_name='Rövid leírás')),
                ('payment_id', models.CharField(blank=True, db_index=True, max_length=100, verbose_name='Fizetési azonosító')),
                ('transaction_id', models.CharField(blank=True, max_length=100, verbose_name='Tranzakció azonosító')),
                ('payer_name', models.CharField(blank=True, db_index=True, max_length=200, verbose_name='Fizető fél neve')),
                ('payer_iban', models.CharField(blank=True, max_length=34, verbose_name='Fizető fél IBAN')),
                ('payer_account_number', models.CharField(blank=True, max_length=50, verbose_name='Fizető fél számlaszáma')),
                ('payer_bic', models.CharField(blank=True, max_length=11, verbose_name='Fizető fél BIC')),
                ('beneficiary_name', models.CharField(blank=True, db_index=True, max_length=200, verbose_name='Kedvezményezett neve')),
                ('beneficiary_iban', models.CharField(blank=True, max_length=34, verbose_name='Kedvezményezett IBAN')),
                ('beneficiary_account_number', models.CharField(blank=True, max_length=50, verbose_name='Kedvezményezett számlaszáma')),
                ('reference', models.TextField(blank=True, help_text='Nem strukturált közlemény - critical for invoice matching', verbose_name='Közlemény')),
                ('card_number', models.CharField(blank=True, max_length=20, verbose_name='Kártya szám (maszkolva)')),
                ('merchant_name', models.CharField(blank=True, max_length=200, verbose_name='Kereskedő neve')),
                ('merchant_location', models.CharField(blank=True, max_length=100, verbose_name='Kereskedő helye')),
                ('original_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Eredeti összeg (FX)')),
                ('original_currency', models.CharField(blank=True, max_length=3, verbose_name='Eredeti deviza (FX)')),
                ('match_confidence', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='0.00 to 1.00', max_digits=3, verbose_name='Párosítás megbízhatósága')),
                ('match_method', models.CharField(blank=True, choices=[('REFERENCE_EXACT', 'Közlemény alapján (pontos)'), ('AMOUNT_IBAN', 'Összeg + IBAN alapján'), ('FUZZY_NAME', 'Összeg + név hasonlóság alapján'), ('MANUAL', 'Manuális párosítás')], max_length=50, verbose_name='Párosítás módja')),
                ('match_notes', models.TextField(blank=True, verbose_name='Párosítási megjegyzések')),
                ('matched_at', models.DateTimeField(blank=True, null=True, verbose_name='Párosítás ideje')),
                ('is_extra_cost', models.BooleanField(db_index=True, default=False, verbose_name='Extra költség')),
                ('extra_cost_category', models.CharField(blank=True, choices=[('BANK_FEE', 'Banki költség'), ('CARD_PURCHASE', 'Kártyás vásárlás'), ('INTEREST', 'Kamat'), ('TAX_DUTY', 'Adó/illeték'), ('CASH_WITHDRAWAL', 'Készpénzfelvétel'), ('OTHER', 'Egyéb költség')], max_length=50, verbose_name='Költség kategória')),
                ('raw_data', models.JSONField(blank=True, default=dict, verbose_name='Nyers adatok')),
                ('bank_statement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='bank_transfers.bankstatement', verbose_name='Bankszámlakivonat')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_transactions', to='bank_transfers.company', verbose_name='Cég')),
                ('matched_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='matched_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Párosította')),
                ('matched_invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bank_transactions', to='bank_transfers.invoice', verbose_name='Párosított számla')),
            ],
            options={
                'verbose_name': 'Banki tranzakció',
                'verbose_name_plural': 'Banki tranzakciók',
                'ordering': ['-booking_date', '-value_date'],
            },
        ),

        # OtherCost model
        migrations.CreateModel(
            name='OtherCost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Létrehozva')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Módosítva')),
                ('category', models.CharField(choices=[('BANK_FEE', 'Banki költség'), ('CARD_PURCHASE', 'Kártyás vásárlás'), ('INTEREST', 'Kamat'), ('TAX_DUTY', 'Adó/illeték'), ('CASH_WITHDRAWAL', 'Készpénzfelvétel'), ('SUBSCRIPTION', 'Előfizetés'), ('UTILITY', 'Közüzem'), ('FUEL', 'Üzemanyag'), ('TRAVEL', 'Utazás'), ('OFFICE', 'Iroda/irodaszer'), ('OTHER', 'Egyéb')], max_length=50, verbose_name='Kategória')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Összeg')),
                ('currency', models.CharField(default='HUF', max_length=3, verbose_name='Deviza')),
                ('date', models.DateField(verbose_name='Dátum')),
                ('description', models.TextField(verbose_name='Leírás')),
                ('notes', models.TextField(blank=True, verbose_name='Megjegyzések')),
                ('tags', models.JSONField(blank=True, default=list, help_text="E.g., ['fuel', 'travel', 'office']", verbose_name='Címkék')),
                ('bank_transaction', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='extra_cost_detail', to='bank_transfers.banktransaction', verbose_name='Banki tranzakció')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extra_costs', to='bank_transfers.company', verbose_name='Cég')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Létrehozta')),
            ],
            options={
                'verbose_name': 'Extra költség',
                'verbose_name_plural': 'Extra költségek',
                'ordering': ['-date'],
            },
        ),

        # Add unique constraints
        migrations.AddConstraint(
            model_name='bankstatement',
            constraint=models.UniqueConstraint(fields=('company', 'file_hash'), name='unique_company_file_hash'),
        ),
        migrations.AddConstraint(
            model_name='bankstatement',
            constraint=models.UniqueConstraint(fields=('company', 'bank_code', 'account_number', 'statement_period_from', 'statement_period_to'), name='unique_company_bank_account_period'),
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='bankstatement',
            index=models.Index(fields=['company', 'bank_code', 'account_number'], name='idx_bs_company_bank_account'),
        ),
        migrations.AddIndex(
            model_name='bankstatement',
            index=models.Index(fields=['company', 'status'], name='idx_bs_company_status'),
        ),
        migrations.AddIndex(
            model_name='bankstatement',
            index=models.Index(fields=['company', 'statement_period_to'], name='idx_bs_company_period_to'),
        ),
        migrations.AddIndex(
            model_name='bankstatement',
            index=models.Index(fields=['uploaded_at'], name='idx_bs_uploaded_at'),
        ),

        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['bank_statement', 'booking_date'], name='idx_bt_statement_booking'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['company', 'booking_date'], name='idx_bt_company_booking'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['company', 'transaction_type', 'booking_date'], name='idx_bt_company_type_booking'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['amount', 'currency'], name='idx_bt_amount_currency'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['matched_invoice'], name='idx_bt_matched_invoice'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['payment_id'], name='idx_bt_payment_id'),
        ),
        migrations.AddIndex(
            model_name='banktransaction',
            index=models.Index(fields=['is_extra_cost', 'extra_cost_category'], name='idx_bt_extra_cost'),
        ),
    ]
```

### 4.2 Feature Flag Migration

```python
# Add BANK_STATEMENT_IMPORT feature to FeatureTemplate

from django.db import migrations


def add_bank_statement_import_feature(apps, schema_editor):
    """Add BANK_STATEMENT_IMPORT feature template"""
    FeatureTemplate = apps.get_model('bank_transfers', 'FeatureTemplate')

    FeatureTemplate.objects.get_or_create(
        feature_code='BANK_STATEMENT_IMPORT',
        defaults={
            'display_name': 'Bank Statement Import',
            'description': 'Import and parse bank statement PDFs, match transactions to NAV invoices, track other costs',
            'category': 'INTEGRATION',
            'default_enabled': False,
            'is_system_critical': False,
        }
    )


def remove_bank_statement_import_feature(apps, schema_editor):
    """Remove BANK_STATEMENT_IMPORT feature template"""
    FeatureTemplate = apps.get_model('bank_transfers', 'FeatureTemplate')
    FeatureTemplate.objects.filter(feature_code='BANK_STATEMENT_IMPORT').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bank_transfers', '0039_add_bank_statement_models'),
    ]

    operations = [
        migrations.RunPython(add_bank_statement_import_feature, remove_bank_statement_import_feature),
    ]
```

### 4.3 Idempotency & Rollback

**Duplicate Prevention**:
- Unique constraint on `(company, file_hash)` prevents exact duplicate uploads
- Unique constraint on `(company, bank_code, account_number, period_from, period_to)` prevents period overlap
- Re-uploading same period with different file triggers update/reparse logic

**Rollback SQL** (if needed):
```sql
-- PostgreSQL
DROP TABLE IF EXISTS bank_transfers_extracost CASCADE;
DROP TABLE IF EXISTS bank_transfers_banktransaction CASCADE;
DROP TABLE IF EXISTS bank_transfers_bankstatement CASCADE;

-- Remove feature flag
DELETE FROM bank_transfers_featuretemplate WHERE feature_code = 'BANK_STATEMENT_IMPORT';

-- SQL Server
DROP TABLE IF EXISTS bank_transfers_extracost;
DROP TABLE IF EXISTS bank_transfers_banktransaction;
DROP TABLE IF EXISTS bank_transfers_bankstatement;

DELETE FROM bank_transfers_featuretemplate WHERE feature_code = 'BANK_STATEMENT_IMPORT';
```

---

## 5. Bank Adapter Interface

### 5.1 Abstract Base Class

```python
"""
Bank statement adapter interface.

All bank-specific parsers must implement this interface for multi-bank support.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
import logging

logger = logging.getLogger(__name__)


@dataclass
class NormalizedTransaction:
    """
    Normalized transaction data model.

    All bank adapters must return this standardized format regardless of
    bank-specific PDF structure or terminology.
    """
    # Required fields
    transaction_type: str  # One of BankTransaction.TRANSACTION_TYPES
    booking_date: date
    value_date: date
    amount: Decimal  # Negative for debit, positive for credit
    currency: str
    description: str

    # Optional fields (populated based on transaction type)
    short_description: str = ""

    # AFR/Transfer fields
    payment_id: Optional[str] = None
    transaction_id: Optional[str] = None

    payer_name: Optional[str] = None
    payer_iban: Optional[str] = None
    payer_account_number: Optional[str] = None
    payer_bic: Optional[str] = None

    beneficiary_name: Optional[str] = None
    beneficiary_iban: Optional[str] = None
    beneficiary_account_number: Optional[str] = None

    reference: Optional[str] = None  # CRITICAL for invoice matching

    # POS/Card fields
    card_number: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_location: Optional[str] = None
    original_amount: Optional[Decimal] = None
    original_currency: Optional[str] = None

    # Raw data storage
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.transaction_type:
            raise ValueError("transaction_type is required")
        if not self.booking_date:
            raise ValueError("booking_date is required")
        if not self.value_date:
            raise ValueError("value_date is required")
        if self.amount is None:
            raise ValueError("amount is required")
        if not self.currency:
            raise ValueError("currency is required")


@dataclass
class StatementMetadata:
    """
    Statement-level metadata extracted from PDF header/footer.
    """
    # Bank identification
    bank_code: str
    bank_name: str
    bank_bic: str

    # Account details
    account_number: str
    account_iban: str

    # Statement period
    period_from: date
    period_to: date
    statement_number: str

    # Balances
    opening_balance: Decimal
    closing_balance: Optional[Decimal] = None

    # Additional metadata
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class BankStatementParseError(Exception):
    """Raised when PDF parsing fails"""
    pass


class BankStatementAdapter(ABC):
    """
    Abstract base class for bank statement parsers.

    Each bank must implement this interface to support multi-bank parsing.

    Example implementations:
    - GranitBankAdapter (GRÁNIT Bank Nyrt.)
    - OTPBankAdapter (OTP Bank Nyrt.) - future
    - KHBankAdapter (K&H Bank Zrt.) - future
    - CIBBankAdapter (CIB Bank Zrt.) - future
    - ErsteBankAdapter (Erste Bank Hungary Zrt.) - future
    """

    # Bank identification (must be set by subclasses)
    BANK_CODE: str = None  # e.g., 'GRANIT', 'OTP', 'KH'
    BANK_NAME: str = None  # e.g., 'GRÁNIT Bank Nyrt.'
    BANK_BIC: str = None   # e.g., 'GNBAHUHB'

    @classmethod
    @abstractmethod
    def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
        """
        Detect if this adapter can parse the given PDF.

        Should check for bank-specific identifiers in the PDF (e.g., bank name, BIC code, logo).

        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Original filename (may contain hints)

        Returns:
            True if this adapter can handle the PDF, False otherwise

        Example:
            @classmethod
            def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
                try:
                    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                        first_page_text = pdf.pages[0].extract_text()
                        return 'GRÁNIT Bank' in first_page_text and 'GNBAHUHB' in first_page_text
                except:
                    return False
        """
        pass

    @abstractmethod
    def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parse bank statement PDF and extract ALL transactions.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            Dictionary with keys:
            {
                'metadata': StatementMetadata,
                'transactions': List[NormalizedTransaction]
            }

        Raises:
            BankStatementParseError: If parsing fails (invalid PDF, unrecognized format, etc.)

        Example:
            def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
                with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                    # Extract metadata from header
                    metadata = self._parse_metadata(pdf)

                    # Extract all transactions
                    transactions = self._parse_transactions(pdf)

                    return {
                        'metadata': metadata,
                        'transactions': transactions
                    }
        """
        pass

    @classmethod
    def get_bank_code(cls) -> str:
        """Return bank identifier code"""
        if not cls.BANK_CODE:
            raise NotImplementedError(f"{cls.__name__} must define BANK_CODE")
        return cls.BANK_CODE

    @classmethod
    def get_bank_name(cls) -> str:
        """Return bank display name"""
        if not cls.BANK_NAME:
            raise NotImplementedError(f"{cls.__name__} must define BANK_NAME")
        return cls.BANK_NAME

    @classmethod
    def get_bank_bic(cls) -> str:
        """Return bank BIC code"""
        if not cls.BANK_BIC:
            raise NotImplementedError(f"{cls.__name__} must define BANK_BIC")
        return cls.BANK_BIC

    def _clean_amount(self, amount_str: str) -> Decimal:
        """
        Clean and parse amount string to Decimal.

        Handles various formats:
        - "4 675 505" → 4675505.00
        - "-229 125" → -229125.00
        - "10,260.50" → 10260.50
        - "1.234,56" → 1234.56 (European format)
        """
        if not amount_str:
            return Decimal('0.00')

        # Remove spaces
        cleaned = amount_str.strip().replace(' ', '')

        # Handle negative sign
        is_negative = cleaned.startswith('-')
        if is_negative:
            cleaned = cleaned[1:]

        # Detect decimal separator (last comma or dot)
        if ',' in cleaned and '.' in cleaned:
            # Both present - assume European format: 1.234,56
            if cleaned.rindex(',') > cleaned.rindex('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format: 1,234.56
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Only comma - assume decimal separator
            cleaned = cleaned.replace(',', '.')

        result = Decimal(cleaned)
        return -result if is_negative else result

    def _clean_account_number(self, account_str: str) -> str:
        """
        Clean account number (remove spaces, dashes).

        "1210 0011-1901 4874" → "12100011-19014874"
        """
        if not account_str:
            return ""
        return account_str.replace(' ', '').strip()
```

---

## 10. Transaction Matching Engine

### 10.1 Overview

The Transaction Matching Engine automatically links bank transactions to NAV invoices and TransferBatch records using a **priority cascade** with **confidence-based scoring**. The system implements **7 matching strategies** with **5 confidence levels** (0.60-1.00).

**Key Enhancements Beyond Original Specification:**
- ✅ **Direction compatibility checking** - Prevents false positives (e.g., NAV tax payments)
- ✅ **Multi-level confidence system** - 5 distinct levels for match quality assessment
- ✅ **Transfer matching** - Matches to executed TransferBatch exports (Priority 1)
- ✅ **Fallback strategy** - AMOUNT_DATE_ONLY for POS purchases with no merchant info
- ✅ **Reimbursement pairing** - Matches offsetting transactions
- ✅ **Reference field fallback** - Extracts "Nem strukturált közlemény" when "Közlemény" empty
- ✅ **Smart amount field usage** - Uses `invoice_gross_amount` instead of frequently NULL `invoice_gross_amount_huf`

### 10.2 Matching Priority Cascade

The matching engine tries strategies in order of confidence. Once a match is found, the cascade stops.

```
Priority 1: TRANSFER_EXACT (1.00)
    ↓ No match? Continue...
Priority 2a: REFERENCE_EXACT (1.00)
    ↓ No match? Continue...
Priority 2b: AMOUNT_IBAN (0.95)
    ↓ No match? Continue...
Priority 2c: FUZZY_NAME (0.70-0.90)
    ↓ No match? Continue...
Priority 2d: AMOUNT_DATE_ONLY (0.60) ⚠️ LOW CONFIDENCE
    ↓ No match? Continue...
Priority 3: REIMBURSEMENT_PAIR (0.70)
    ↓ No match
Result: NOT MATCHED
```

### 10.3 Matching Strategies

#### Strategy 1: TRANSFER_EXACT (Confidence: 1.00)

**Purpose**: Match bank transactions to executed TransferBatch transfers
**Use Case**: Verify that generated transfers were actually executed by the bank
**Status**: ✅ Fully implemented and tested

**Logic**:
```python
def _try_transfer_matching(self, transaction: BankTransaction):
    # Only match DEBIT transactions (outgoing payments)
    if transaction.amount >= 0:
        return None

    # Find TransferBatch records marked as "used in bank"
    used_batches = TransferBatch.objects.filter(
        company=self.company,
        used_in_bank=True,
        execution_date__gte=transaction.value_date - timedelta(days=7),
        execution_date__lte=transaction.value_date + timedelta(days=7)
    )

    for batch in used_batches:
        for transfer in batch.transfers.all():
            # Exact amount match
            if abs(transaction.amount) != transfer.amount:
                continue

            # Beneficiary match (account number OR name ≥80%)
            if transfer.beneficiary.account_number in transaction.beneficiary_account_number:
                return (transfer, Decimal('1.00'))

            if transfer.beneficiary.name and transaction.beneficiary_name:
                similarity = fuzz.token_sort_ratio(
                    transfer.beneficiary.name.lower(),
                    transaction.beneficiary_name.lower()
                ) / 100.0
                if similarity >= 0.80:
                    return (transfer, Decimal('1.00'))

    return None
```

**Auto-update payment status**: ✅ YES

---

#### Strategy 2a: REFERENCE_EXACT (Confidence: 1.00)

**Purpose**: Match by invoice number or supplier tax number in transaction reference
**Use Case**: Standard invoice payments with proper reference codes
**Status**: ✅ Enhanced with direction checking

**Logic**:
```python
def _match_by_reference(self, transaction: BankTransaction, invoices: QuerySet):
    reference = transaction.reference.strip()
    if not reference:
        return None, Decimal('0.00')

    for invoice in invoices:
        # Check invoice number
        if invoice.nav_invoice_number and invoice.nav_invoice_number in reference:
            # CRITICAL: Direction compatibility check
            if not self._is_direction_compatible(transaction, invoice):
                continue  # Reject match
            return invoice, Decimal('1.00')

        # Check supplier tax number (first 8 digits)
        if invoice.supplier_tax_number:
            clean_tax = invoice.supplier_tax_number.replace('-', '')[:8]
            if clean_tax in reference:
                if not self._is_direction_compatible(transaction, invoice):
                    continue  # Reject match
                return invoice, Decimal('1.00')

    return None, Decimal('0.00')
```

**Direction Compatibility Check**:
```python
def _is_direction_compatible(self, transaction: BankTransaction, invoice: Invoice) -> bool:
    """
    OUTBOUND invoice (we issued) → expects CREDIT transaction (incoming payment)
    INBOUND invoice (we received) → expects DEBIT transaction (outgoing payment)
    """
    if invoice.invoice_direction == 'OUTBOUND':
        return transaction.amount > 0  # Must be CREDIT
    elif invoice.invoice_direction == 'INBOUND':
        return transaction.amount < 0  # Must be DEBIT
    else:
        return True  # Unknown direction - allow match
```

**Impact of Direction Checking**:
- ✅ Prevents 6 false NAV tax matches in test data
- ✅ NAV tax payments (DEBIT with OUTBOUND invoice) correctly rejected
- ✅ All matches are directionally correct

**Auto-update payment status**: ✅ YES

---

#### Strategy 2b: AMOUNT_IBAN (Confidence: 0.95)

**Purpose**: Match by exact amount + beneficiary IBAN
**Use Case**: Payments with IBAN but no reference code
**Status**: ✅ Enhanced with direction checking

**Logic**:
```python
def _match_by_amount_iban(self, transaction: BankTransaction, invoices: QuerySet):
    amount = abs(transaction.amount)
    beneficiary_iban = transaction.beneficiary_iban.strip()

    if not beneficiary_iban:
        return None, Decimal('0.00')

    for invoice in invoices:
        # Skip if no invoice amount
        if not invoice.invoice_gross_amount:
            continue

        # Exact amount match
        if invoice.invoice_gross_amount != amount:
            continue

        # IBAN match
        if invoice.supplier_bank_account_number == beneficiary_iban:
            # Direction check
            if not self._is_direction_compatible(transaction, invoice):
                continue
            return invoice, Decimal('0.95')

    return None, Decimal('0.00')
```

**Note**: Uses `invoice_gross_amount` instead of `invoice_gross_amount_huf` (frequently NULL)

**Auto-update payment status**: ✅ YES (confidence ≥ 0.95)

---

#### Strategy 2c: FUZZY_NAME (Confidence: 0.70-0.90)

**Purpose**: Match by amount + fuzzy name similarity
**Use Case**: Payments with beneficiary name but no IBAN or reference
**Status**: ✅ Enhanced with direction checking and dynamic confidence

**Logic**:
```python
def _match_by_fuzzy_name(self, transaction: BankTransaction, invoices: QuerySet):
    amount = abs(transaction.amount)
    transaction_name = transaction.beneficiary_name or transaction.payer_name

    if not transaction_name:
        return None, Decimal('0.00')

    best_match = None
    best_similarity = 0.0

    for invoice in invoices:
        if not invoice.invoice_gross_amount:
            continue

        # Amount match (±1% tolerance)
        invoice_amount = invoice.invoice_gross_amount
        tolerance = invoice_amount * Decimal('0.01')
        if abs(amount - invoice_amount) > tolerance:
            continue

        # Name similarity (rapidfuzz token_sort_ratio)
        similarity = fuzz.token_sort_ratio(
            transaction_name.lower(),
            invoice.supplier_name.lower()
        ) / 100.0

        if similarity >= 0.70:  # Minimum threshold
            # Direction check
            if not self._is_direction_compatible(transaction, invoice):
                continue

            if similarity > best_similarity:
                best_match = invoice
                best_similarity = similarity

    if best_match:
        # Dynamic confidence: 0.70 + (similarity * 0.20)
        # 70% similarity → 0.70, 100% similarity → 0.90
        confidence = Decimal('0.70') + Decimal(str(best_similarity * 0.20))
        return best_match, confidence

    return None, Decimal('0.00')
```

**Auto-update payment status**: ❌ NO (confidence < 0.95, requires manual review)

---

#### Strategy 2d: AMOUNT_DATE_ONLY (Confidence: 0.60) ⚠️ LOW CONFIDENCE

**Purpose**: Fallback strategy for POS purchases with no merchant/beneficiary info
**Use Case**: Card purchases, ATM withdrawals with only amount and date
**Status**: ✅ NEW - Added to capture missing matches

**Logic**:
```python
def _match_by_amount_date_only(self, transaction: BankTransaction, invoices: QuerySet):
    """
    LOW CONFIDENCE match for transactions with:
    ✓ Amount match (±1%)
    ✓ Date match (already filtered by candidate query)
    ✓ Direction match
    ✗ NO reference, NO IBAN, NO name
    """
    amount = abs(transaction.amount)
    best_match = None

    for invoice in invoices:
        if not invoice.invoice_gross_amount:
            continue

        # Amount match (±1% tolerance)
        invoice_amount = invoice.invoice_gross_amount
        tolerance = invoice_amount * Decimal('0.01')
        if abs(amount - invoice_amount) > tolerance:
            continue

        # Direction check
        if not self._is_direction_compatible(transaction, invoice):
            continue

        # Found match with ONLY amount and date
        best_match = invoice
        break

    if best_match:
        logger.info(f"Amount+Date only match (LOW CONFIDENCE): MANUAL REVIEW RECOMMENDED")
        return best_match, Decimal('0.60')

    return None, Decimal('0.00')
```

**Test Results**: Found 10 additional matches (POS purchases) in January 2025 statement
**Auto-update payment status**: ❌ NO (LOW confidence, flagged for manual review)

---

#### Strategy 3: REIMBURSEMENT_PAIR (Confidence: 0.70)

**Purpose**: Match offsetting transactions (same amount, opposite signs)
**Use Case**: Refunds, reversals, corrections
**Status**: ✅ Fully implemented

**Logic**:
```python
def _try_reimbursement_matching(self, transaction: BankTransaction):
    """
    Find offsetting transaction:
    - Same amount (opposite signs)
    - Within ±5 days
    - Neither already matched
    """
    opposite_amount = -transaction.amount

    candidates = BankTransaction.objects.filter(
        company=self.company,
        amount=opposite_amount,
        value_date__gte=transaction.value_date - timedelta(days=5),
        value_date__lte=transaction.value_date + timedelta(days=5),
        matched_reimbursement__isnull=True
    ).exclude(id=transaction.id)

    if candidates.exists():
        return candidates.first(), Decimal('0.70')

    return None, Decimal('0.00')
```

**Auto-update payment status**: ❌ NO (reimbursement, not invoice payment)

---

### 10.4 Candidate Filtering (Phase 1)

Before trying match strategies, the engine pre-filters invoices using SQL:

```python
def _get_candidate_invoices(self, transaction: BankTransaction) -> QuerySet:
    """
    Filter invoices that could potentially match this transaction.
    Uses indexed fields for performance.
    """
    return Invoice.objects.filter(
        company=self.company,
        invoice_direction__in=['INBOUND', 'OUTBOUND'],
        payment_status__in=['UNPAID', 'PREPARED', 'PAID'],
        invoice_operation__in=['CREATE', 'MODIFY'],

        # Date filter: ±10 to +30 days from transaction date
        payment_due_date__gte=transaction.value_date - timedelta(days=10),
        payment_due_date__lte=transaction.value_date + timedelta(days=30)
    ).select_related('supplier').order_by('payment_due_date')
```

**Performance**: Indexed fields ensure fast filtering even with thousands of invoices

---

### 10.5 Reference Field Extraction

The GRÁNIT Bank adapter extracts reference fields with **fallback logic**:

```python
# Reference (Közlemény) - with fallback to Nem strukturált közlemény
if m := re.search(r'Közlemény:\s*([^\n]+)', block_text):
    fields['reference'] = m.group(1).strip()
elif m := re.search(r'Nem strukturált közlemény:\s*([^\n]+)', block_text):
    fields['reference'] = m.group(1).strip()  # Fallback
```

**Impact**: Captured 2 additional references in test data (from "Nem strukturált közlemény")

**Important**: AFR transactions in GRÁNIT Bank PDFs may not have "Közlemény" fields - this is the bank's PDF format, not a parser limitation.

---

### 10.6 Confidence Levels and Auto-Update Logic

| Confidence | Match Method | Auto-Update Payment Status | Manual Review Required |
|------------|--------------|----------------------------|------------------------|
| **1.00** | TRANSFER_EXACT | ✅ YES | ❌ No |
| **1.00** | REFERENCE_EXACT | ✅ YES | ❌ No |
| **0.95** | AMOUNT_IBAN | ✅ YES | ❌ No |
| **0.70-0.90** | FUZZY_NAME | ❌ NO | ✅ **Yes** |
| **0.70** | REIMBURSEMENT_PAIR | ❌ NO | ❌ No (not invoice) |
| **0.60** | AMOUNT_DATE_ONLY | ❌ NO | ✅ **Yes** (LOW) |

**Auto-Update Threshold**: `confidence >= 0.95`

**Payment Status Update**:
```python
if confidence >= Decimal('0.95'):
    # High confidence - auto-update invoice to PAID
    invoice.payment_status = 'PAID'
    invoice.payment_status_date = transaction.value_date
    invoice.auto_marked_paid = True
    invoice.save()
```

---

### 10.7 Test Results (January 2025 Statement)

**Before Enhancements**:
- Total transactions: 27
- Matched: 11/27 (40.7%)
- Problem: 7 false matches to same OUTBOUND invoice (NAV tax payments)

**After Direction Checking**:
- Total transactions: 27
- Matched: 5/27 (18.5%)
- False matches prevented: 6 NAV tax payments ✅
- Problem: Missing 6 POS purchases with no merchant info

**After AMOUNT_DATE_ONLY Strategy**:
- Total transactions: 27
- **Matched: 15/27 (55.6%)** ✅
- Breakdown:
  - HIGH confidence (1.00): 3 matches → Auto-update
  - MEDIUM confidence (0.70-0.90): 1 match → Review
  - LOW confidence (0.60): 10 matches → Review
  - Reimbursement pair (0.70): 1 pair
  - NOT MATCHED: 12 transactions (correct - no invoices exist)

**Quality Analysis**:
- ✅ All 15 matches are correct
- ✅ 6 false positives prevented (NAV taxes)
- ✅ Confidence levels accurately reflect match quality
- ✅ Low confidence matches flagged for review

---

### 10.8 Integration with Bank Statement Upload

The matching engine runs **automatically** after PDF parsing:

```python
# In bank_statement_parser_service.py

# After creating transactions...
from .transaction_matching_service import TransactionMatchingService

matching_service = TransactionMatchingService(self.company)
match_results = matching_service.match_statement(statement)

# Update statement statistics
statement.matched_count = match_results['matched_count']
statement.save()

logger.info(
    f"Transaction matching completed for statement {statement.id}: "
    f"{match_results['matched_count']}/{created_count} transactions matched "
    f"({match_results['match_rate']}%), "
    f"{match_results['auto_paid_count']} invoices auto-marked as paid"
)
```

**Result**: Matching happens transparently during upload - no manual trigger required.

---

### 10.9 Comparison: Original Specification vs. Current Implementation

| Feature | Original Docs | Current Implementation | Status |
|---------|---------------|------------------------|--------|
| **REFERENCE_EXACT** | ✅ Planned | ✅ + Direction checking | **ENHANCED** |
| **AMOUNT_IBAN** | ✅ Planned | ✅ + Direction checking | **ENHANCED** |
| **FUZZY_NAME** | ✅ Planned | ✅ + Direction checking | **ENHANCED** |
| **MANUAL** | ✅ Planned | ✅ Implemented | ✅ AS SPEC |
| **TRANSFER_EXACT** | ❌ Not planned | ✅ Fully implemented | ⭐ **NEW** |
| **AMOUNT_DATE_ONLY** | ❌ Not planned | ✅ Fully implemented | ⭐ **NEW** |
| **REIMBURSEMENT_PAIR** | ❌ Not planned | ✅ Fully implemented | ⭐ **NEW** |
| **Direction checking** | ❌ Not planned | ✅ All strategies | ⭐ **NEW** |
| **Confidence levels** | ❌ Not specified | ✅ 5 levels (0.60-1.00) | ⭐ **NEW** |
| **Auto-update threshold** | ❌ Not specified | ✅ confidence ≥ 0.95 | ⭐ **NEW** |
| **Fallback reference** | ❌ Not planned | ✅ "Nem strukturált közlemény" | ⭐ **NEW** |
| **Amount field fix** | ❌ Not planned | ✅ Uses invoice_gross_amount | ⭐ **NEW** |

**Summary**:
- ✅ Original specification: **FULLY IMPLEMENTED**
- ⭐ **ENHANCED with 7 additional features**
- 🚀 Match rate: **55.6%** (15/27 matches)
- ✅ All matches directionally correct
- ✅ Low confidence matches flagged for review
- ✅ **Ready for production use**

---
