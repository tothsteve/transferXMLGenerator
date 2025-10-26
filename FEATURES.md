# Feature Implementation Details

This document contains detailed implementation information for all major features in the Transfer XML Generator system.

## Table of Contents
- [Multi-Company Feature Flag System](#multi-company-feature-flag-system)
- [NAV Invoice Payment Status Tracking](#nav-invoice-payment-status-tracking)
- [Trusted Partners Auto-Payment System](#trusted-partners-auto-payment-system)
- [MNB Exchange Rate Integration](#mnb-exchange-rate-integration)
- [Bank Statement Import and Transaction Matching](#bank-statement-import-and-transaction-matching)

---

## Multi-Company Feature Flag System

### Company-Specific Feature Control
The system implements a sophisticated **two-layer permission architecture**:

1. **Company Feature Level**: Features must be enabled for the company
2. **User Role Level**: User's role must permit access to the feature

### Role-Based Access Control

#### User Roles (4 Levels)
- **ADMIN**: Full access to all enabled company features + user management
- **FINANCIAL**: Transfer operations, templates, SEPA XML exports
- **ACCOUNTANT**: Invoice/expense management (NAV integration)
- **USER**: Read-only access to basic features

#### Permission Matrix
| Feature Category | ADMIN | FINANCIAL | ACCOUNTANT | USER |
|------------------|-------|-----------|------------|------|
| **Beneficiaries** | Full CRUD | Full CRUD | View only | View only |
| **Transfers** | Full CRUD | Full CRUD | View only | View only |
| **Templates** | Full CRUD | Full CRUD | View only | View only |
| **Batches** | Full CRUD | View only | View only | View only |
| **NAV Invoices** | Full CRUD | View only | Full CRUD | View only |
| **Bank Statements** | Full CRUD | Full CRUD | View only | View only |
| **Exports** | All formats | SEPA XML | None | None |
| **User Management** | Full | None | None | None |

### Active Features (16 Total)

#### Export Features (3)
- **EXPORT_XML_SEPA**: Generate SEPA-compatible XML files
- **EXPORT_CSV_KH**: Generate KH Bank specific CSV format
- **EXPORT_CSV_CUSTOM**: Custom CSV format exports

#### Sync Features (1)
- **NAV_SYNC**: NAV invoice synchronization and import

#### Tracking Features (6)
- **BENEFICIARY_MANAGEMENT**: Full CRUD operations on beneficiaries
- **BENEFICIARY_VIEW**: View beneficiaries only
- **TRANSFER_MANAGEMENT**: Full CRUD operations on transfers
- **TRANSFER_VIEW**: View transfers only
- **BATCH_MANAGEMENT**: Full CRUD operations on batches
- **BATCH_VIEW**: View batches only

#### Reporting Features (2)
- **REPORTING_DASHBOARD**: Access to dashboard views
- **REPORTING_ANALYTICS**: Advanced analytics features

#### Integration Features (3)
- **API_ACCESS**: REST API access for external integrations
- **WEBHOOK_NOTIFICATIONS**: Webhook notification system
- **BANK_STATEMENT_IMPORT**: Import and parse bank statement PDFs/CSVs/XMLs, match transactions to NAV invoices

#### General Features (1)
- **BULK_OPERATIONS**: Bulk import/export operations

### Implementation Notes
- Features are cached at login for performance
- Permission checking happens at ViewSet level with custom permission classes
- Companies can enable/disable features independently
- Admin users can force logout other users for security
- Complete audit trail for feature enablement and user actions

---

## NAV Invoice Payment Status Tracking

### Payment Status Workflow
The system implements comprehensive **payment status tracking** for NAV invoices with automated status updates:

1. **UNPAID** (Fizetésre vár) - Default status for all invoices
2. **PREPARED** (Előkészítve) - When transfer is created from invoice
3. **PAID** (Kifizetve) - When batch is marked as "used in bank"

### Key Features

#### Automated Status Updates
- **Transfer Creation**: Invoice automatically marked as PREPARED when transfer is generated
- **Batch Processing**: Invoice automatically marked as PAID when batch is used in bank
- **Dynamic Overdue Detection**: No static OVERDUE status - calculated based on payment_due_date vs current date

#### Bulk Payment Status Management
- **Bulk Mark Unpaid**: Reset multiple invoices to "Fizetésre vár" status
- **Bulk Mark Prepared**: Mark multiple invoices as "Előkészítve" status
- **Bulk Mark Paid**: Mark multiple invoices as "Kifizetve" with flexible date options:
  - **Payment Due Date Option**: Use each invoice's individual payment_due_date
  - **Custom Date Option**: Set a single custom payment date for all selected invoices

#### API Endpoints
- `POST /api/nav-invoices/bulk_mark_unpaid/` - Bulk mark as unpaid
- `POST /api/nav-invoices/bulk_mark_prepared/` - Bulk mark as prepared
- `POST /api/nav-invoices/bulk_mark_paid/` - Bulk mark as paid with flexible date options

#### Frontend Features
- **Visual Status Indicators**: Icons with tooltips showing payment status and date
- **Bulk Action Bar**: Appears when invoices are selected with status update buttons
- **Flexible Date Selection**: Checkbox to choose between payment due dates vs custom date
- **Hungarian Localization**: All UI elements in Hungarian with proper date formatting

### Database Implementation
- `payment_status` field with CHECK constraint for valid statuses
- `payment_status_date` for tracking when status was last changed
- `auto_marked_paid` flag to track automated vs manual status changes
- Indexed for efficient filtering by payment status

---

## Trusted Partners Auto-Payment System

### Business Logic
The **Trusted Partners** feature allows companies to designate specific suppliers as "trusted", enabling **automatic payment status updates** during NAV invoice synchronization. When a new invoice is received from a trusted partner, it is automatically marked as **PAID** instead of the default **UNPAID** status.

### Key Features

#### Partner Management
- **Company-scoped trusted partners** with name and tax number identification
- **Active/Inactive status control** to temporarily disable trusted partners
- **Auto-payment toggle** per partner for granular control
- **Statistics tracking**: invoice count and last invoice date per partner
- **Source integration**: Partners can be selected from existing NAV invoice suppliers

#### Automated Payment Processing
- **NAV Sync Integration**: During invoice synchronization, invoices from trusted partners are automatically marked as PAID
- **Flexible Tax Number Matching**: Supports multiple Hungarian tax number formats:
  - **8-digit format**: Base company tax number (e.g., "12345678")
  - **11-digit format**: Full tax number with check digits (e.g., "12345678-2-16")
  - **13-digit format**: Tax number with dashes (e.g., "12345678-2-16")
- **Smart Matching Algorithm**: Three-level matching approach for reliability:
  1. **Exact match**: Direct tax number comparison
  2. **Normalized match**: Remove dashes and spaces, compare full numbers
  3. **Base match**: Compare first 8 digits for cross-format compatibility

#### User Interface
- **Settings Integration**: Accessible through "Beállítások" (Settings) menu with tabbed interface
- **Dual Input Methods**:
  - Manual partner entry with name and tax number
  - Selection from existing NAV invoice suppliers with search and sort
- **Advanced Search**: Case-insensitive search by partner name or tax number
- **Flexible Sorting**: Sortable by partner name, tax number, invoice count, or last invoice date
- **Toggle Controls**: Individual switches for active status and auto-payment functionality
- **Real-time Statistics**: Display invoice count and last invoice date per partner

### Implementation Notes
- **Company Isolation**: All trusted partners are company-scoped with proper access control
- **Performance Optimization**: Database indexes on commonly filtered fields
- **Data Integrity**: Unique constraint prevents duplicate tax numbers per company
- **Hungarian Localization**: All UI elements and field labels in Hungarian
- **Error Handling**: Comprehensive validation for tax number formats and duplicate prevention
- **Statistics Maintenance**: Automatic tracking of invoice count and last invoice date per partner

---

## MNB Exchange Rate Integration

### Overview
The system integrates with the **Magyar Nemzeti Bank (MNB) official API** to retrieve and store USD and EUR exchange rates. This provides accurate, official exchange rates for currency conversion and financial calculations.

### Key Features

#### Automatic Daily Synchronization
- **GetCurrentExchangeRates**: Fetches today's official USD/EUR rates from MNB
- **GetExchangeRates**: Retrieves historical rates for date ranges
- **Scheduled Sync**: Runs every 6 hours on production (00:00, 06:00, 12:00, 18:00 UTC)
- **Performance**: Sync completes in ~2 seconds for 2 years of data (994 rates)

#### Exchange Rate Storage
- **Database Tables**: `ExchangeRate` and `ExchangeRateSyncLog`
- **Supported Currencies**: USD and EUR (expandable to 33 MNB currencies)
- **Decimal Precision**: 6 decimal places for accurate conversion
- **Historical Data**: Stores complete rate history with date indexing

#### API Endpoints
- `GET /api/exchange-rates/` - List rates with filtering
- `GET /api/exchange-rates/current/` - Today's USD/EUR rates
- `GET /api/exchange-rates/latest/` - Most recent available rates
- `POST /api/exchange-rates/convert/` - Currency conversion to HUF
- `POST /api/exchange-rates/sync_current/` - Manual sync trigger (ADMIN only)
- `POST /api/exchange-rates/sync_historical/` - Historical backfill (ADMIN only)
- `GET /api/exchange-rates/sync_history/` - View sync logs
- `GET /api/exchange-rates/history/` - Rate history for charts

### Performance & Reliability
- **2-year historical sync**: 994 rates in 2.33 seconds
- **Daily sync**: < 0.1 seconds for 2 currencies
- **SOAP endpoint**: `http://www.mnb.hu/arfolyamok.asmx`
- **Fallback logic**: Returns latest available rate if exact date missing
- **Weekend/Holiday handling**: MNB returns last business day rate

### Notes
- **Public API**: No authentication required for MNB API
- **Company isolation**: Exchange rates are global (not company-scoped)
- **Permissions**: All authenticated users can view rates, only ADMIN can trigger sync
- **Currency expansion**: See DATABASE_DOCUMENTATION.md for adding more currencies

---

## Bank Statement Import and Transaction Matching

### Overview
The system implements a **multi-bank PDF statement import** feature with **sophisticated transaction matching** to NAV invoices and TransferBatch records using **priority cascade** with **confidence-based scoring**.

### Supported Banks (4 Total)
1. **GRÁNIT Bank Nyrt.** (BIC: GNBAHUHB) - PDF format
2. **Revolut Bank** (BIC: REVOLT21) - CSV format
3. **MagNet Magyar Közösségi Bank** (BIC: MKKB) - XML (NetBankXML) format
4. **K&H Bank Zrt.** (BIC: OKHBHUHB) - PDF format

### Transaction Matching Engine

The system implements **7 matching strategies** with **5 confidence levels** (0.60-1.00):

#### Priority 1: TRANSFER_EXACT (Confidence: 1.00)
- Matches bank transactions to executed TransferBatch transfers
- Only DEBIT transactions (outgoing payments)
- Exact amount + date match (±7 days) + beneficiary match
- **Auto-updates payment status**: ✅ YES

#### Priority 2a: REFERENCE_EXACT (Confidence: 1.00)
- Matches by invoice number or supplier tax number in transaction reference
- **Enhanced with direction checking** to prevent false positives
- Reference extraction with fallback: "Közlemény" → "Nem strukturált közlemény"
- **Auto-updates payment status**: ✅ YES

#### Priority 2b: AMOUNT_IBAN (Confidence: 0.95)
- Matches by exact amount + beneficiary IBAN
- Uses `invoice_gross_amount` (not `invoice_gross_amount_huf`)
- **Enhanced with direction checking**
- **Auto-updates payment status**: ✅ YES

#### Priority 2c: FUZZY_NAME (Confidence: 0.70-0.90)
- Matches by amount (±1%) + fuzzy name similarity (rapidfuzz library)
- Dynamic confidence: 0.70 + (similarity * 0.20)
- **Enhanced with direction checking**
- **Auto-updates payment status**: ❌ NO (requires manual review)

#### Priority 2d: AMOUNT_DATE_ONLY (Confidence: 0.60)
- Fallback strategy for POS purchases with no merchant/beneficiary info
- Amount match (±1%) + date match + direction match only
- **Auto-updates payment status**: ❌ NO (LOW confidence, flagged for review)

#### Priority 3: REIMBURSEMENT_PAIR (Confidence: 0.70)
- Matches offsetting transactions (same amount, opposite signs)
- Within ±5 days, neither already matched
- Use case: Refunds, reversals, corrections
- **Auto-updates payment status**: ❌ NO (not invoice payment)

### Direction Compatibility Checking ⭐ CRITICAL ENHANCEMENT

The system prevents false positives by checking transaction direction compatibility:
- **OUTBOUND invoice** (we issued) → Expect **CREDIT** transaction (incoming payment)
- **INBOUND invoice** (we received) → Expect **DEBIT** transaction (outgoing payment)

**Impact**:
- ✅ Prevents false NAV tax payment matches
- ✅ All matches are directionally correct
- ✅ NAV tax payments correctly rejected

### Confidence Levels and Auto-Update Logic

| Confidence | Match Method | Auto-Update Payment Status | Manual Review Required |
|------------|--------------|----------------------------|------------------------|
| **1.00** | TRANSFER_EXACT | ✅ YES | ❌ No |
| **1.00** | REFERENCE_EXACT | ✅ YES | ❌ No |
| **0.95** | AMOUNT_IBAN | ✅ YES | ❌ No |
| **0.70-0.90** | FUZZY_NAME | ❌ NO | ✅ **Yes** |
| **0.70** | REIMBURSEMENT_PAIR | ❌ NO | ❌ No |
| **0.60** | AMOUNT_DATE_ONLY | ❌ NO | ✅ **Yes** (LOW) |

**Auto-Update Threshold**: `confidence >= 0.95`

### Test Results (January 2025 Statement)

- **Total transactions**: 27
- **Matched**: 15/27 (55.6%) ✅
- **Breakdown**:
  - HIGH confidence (1.00): 3 matches → Auto-update
  - MEDIUM confidence (0.70-0.90): 1 match → Review
  - LOW confidence (0.60): 10 matches → Review
  - NOT MATCHED: 12 transactions (correct - no invoices exist)

**Quality Analysis**:
- ✅ All 15 matches are correct
- ✅ 6 false positives prevented
- ✅ Confidence levels accurately reflect match quality
- ✅ Low confidence matches flagged for manual review

### Notes
- **Bank format limitations**: AFR transactions in GRÁNIT Bank PDFs may not have "Közlemény" fields - this is the bank's PDF format, not a parser bug
- **Performance**: Matching uses indexed fields for fast filtering even with thousands of invoices
- **Company isolation**: All statements and transactions are company-scoped with proper access control
- **Feature flag**: BANK_STATEMENT_IMPORT feature must be enabled for company to access functionality
- **Permissions**: ADMIN and FINANCIAL roles can upload statements, all authenticated users can view

### Implementation Files

**Bank Adapters**:
- `bank_transfers/bank_adapters/base.py` - Abstract adapter interface
- `bank_transfers/bank_adapters/factory.py` - Automatic bank detection
- `bank_transfers/bank_adapters/granit_adapter.py` - GRÁNIT Bank PDF parser
- `bank_transfers/bank_adapters/revolut_adapter.py` - Revolut CSV parser
- `bank_transfers/bank_adapters/magnet_adapter.py` - MagNet XML parser
- `bank_transfers/bank_adapters/kh_adapter.py` - K&H Bank PDF parser

**Services**:
- `bank_transfers/services/bank_statement_parser_service.py` - PDF parsing orchestration
- `bank_transfers/services/transaction_matching_service.py` - Matching engine with 7 strategies

**Documentation**:
- `/BANK_STATEMENT_IMPORT_DOCUMENTATION.md` - Complete field mapping documentation (1200+ lines)
