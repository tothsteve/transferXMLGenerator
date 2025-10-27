# Billingo Invoice Synchronization - Database Schema Documentation

**Feature**: Billingo API v3 Integration
**Created**: 2025-10-27
**Status**: Production Ready

## Overview

This document describes the database schema for the Billingo Invoice Synchronization feature. The system synchronizes invoices from Billingo accounting software via their API v3, storing invoice data locally for reporting, analysis, and potential integration with other business processes.

## Table of Contents

1. [Table Relationships](#table-relationships)
2. [Table Definitions](#table-definitions)
3. [Indexes and Constraints](#indexes-and-constraints)
4. [Data Flow](#data-flow)
5. [Security Considerations](#security-considerations)

---

## Table Relationships

```
Company (existing)
    |
    ├─── CompanyBillingoSettings (1:1)
    |       └─── Encrypted API Key Storage
    |
    ├─── BillingoInvoice (1:N)
    |       └─── BillingoInvoiceItem (1:N)
    |
    └─── BillingoSyncLog (1:N)
            └─── Audit trail for sync operations
```

---

## Table Definitions

### 1. bank_transfers_companybillingosettings

**Purpose**: Stores Billingo API configuration and credentials for each company.

**Django Model**: `CompanyBillingoSettings`

#### Columns

| Column | Type | Null | Default | Description |
|--------|------|------|---------|-------------|
| `id` | BIGINT | NO | AUTO | Primary key |
| `company_id` | BIGINT | NO | - | Foreign key to Company table |
| `api_key` | VARCHAR(255) | NO | - | **Encrypted** Billingo API key using Fernet symmetric encryption |
| `last_sync_time` | DATETIME | YES | NULL | Timestamp of last successful sync completion |
| `is_active` | BOOLEAN | NO | TRUE | Whether sync is enabled for this company |
| `created_at` | DATETIME | NO | NOW() | Record creation timestamp |
| `updated_at` | DATETIME | NO | NOW() | Last modification timestamp |

#### Constraints

- **Primary Key**: `id`
- **Foreign Key**: `company_id` → `bank_transfers_company.id` (CASCADE DELETE)
- **Unique Constraint**: `unique_billingo_settings_per_company` on (`company_id`)
  - Ensures each company has exactly one Billingo settings record

#### Security Notes

- **API Key Encryption**: The `api_key` field stores encrypted data using the Fernet symmetric encryption algorithm
- **Encryption Key**: Managed by `CredentialManager` service, stored in environment variables
- **Never Exposed**: The decrypted API key is never returned via API responses (only `has_api_key` boolean flag)

#### Sample Data

```sql
-- Example encrypted API key (actual key would be longer)
INSERT INTO bank_transfers_companybillingosettings
(company_id, api_key, is_active) VALUES
(4, 'gAAAAABh...encrypted_data...', TRUE);
```

---

### 2. bank_transfers_billingoinvoice

**Purpose**: Stores master invoice data synchronized from Billingo `/documents` API endpoint.

**Django Model**: `BillingoInvoice`

**API Endpoint**: `https://api.billingo.hu/v3/documents`

#### Columns

| Column | Type | Null | Default | Description |
|--------|------|------|---------|-------------|
| `id` | BIGINT | NO | - | **Billingo invoice ID** (not auto-increment) |
| `company_id` | BIGINT | NO | - | Foreign key to Company |
| `invoice_number` | VARCHAR(50) | NO | - | Human-readable invoice number (e.g., "INV-2025-244") |
| `type` | VARCHAR(30) | NO | - | Document type (invoice, proforma, receipt, etc.) |
| `correction_type` | VARCHAR(30) | YES | NULL | Type of correction if applicable |
| `cancelled` | BOOLEAN | NO | FALSE | Whether invoice has been cancelled |
| `block_id` | BIGINT | YES | NULL | Billingo block identifier |
| `payment_status` | VARCHAR(30) | NO | - | Payment status (outstanding, paid, cancelled) |
| `payment_method` | VARCHAR(30) | NO | - | Payment method (wire_transfer, cash, card, etc.) |
| `gross_total` | DECIMAL(15,2) | NO | - | Total amount including VAT |
| `currency` | VARCHAR(5) | NO | - | Currency code (HUF, EUR, USD) |
| `conversion_rate` | DECIMAL(10,6) | NO | 1.0 | Exchange rate if foreign currency |
| `invoice_date` | DATE | NO | - | Invoice issuance date |
| `fulfillment_date` | DATE | NO | - | Service/delivery completion date |
| `due_date` | DATE | NO | - | Payment due date |
| `paid_date` | DATE | YES | NULL | Actual payment date |
| `organization_name` | VARCHAR(255) | NO | - | Issuer organization name |
| `organization_tax_number` | VARCHAR(50) | NO | - | Issuer tax number |
| `organization_bank_account_number` | VARCHAR(50) | NO | - | Issuer bank account |
| `organization_bank_account_iban` | VARCHAR(50) | NO | - | Issuer IBAN |
| `organization_swift` | VARCHAR(20) | YES | NULL | Issuer SWIFT code |
| `partner_id` | BIGINT | NO | - | Billingo partner ID |
| `partner_name` | VARCHAR(255) | NO | - | Customer/supplier name |
| `partner_tax_number` | VARCHAR(50) | NO | - | Customer/supplier tax number |
| `partner_iban` | VARCHAR(50) | YES | NULL | Customer/supplier IBAN |
| `partner_swift` | VARCHAR(20) | YES | NULL | Customer/supplier SWIFT |
| `partner_account_number` | VARCHAR(50) | YES | NULL | Customer/supplier account number |
| `comment` | TEXT | YES | NULL | Invoice notes/comments |
| `online_szamla_status` | VARCHAR(30) | YES | NULL | NAV online invoice status |
| `created_at` | DATETIME | NO | NOW() | Sync timestamp (local) |
| `updated_at` | DATETIME | NO | NOW() | Last update timestamp |

#### Constraints

- **Primary Key**: `id` (Billingo invoice ID)
- **Foreign Key**: `company_id` → `bank_transfers_company.id` (CASCADE DELETE)
- **Unique Constraint**: `unique_billingo_invoice_per_company` on (`company_id`, `id`)

#### Indexes

```sql
-- Performance indexes for common queries
CREATE INDEX idx_billingo_invoice_company ON bank_transfers_billingoinvoice(company_id);
CREATE INDEX idx_billingo_invoice_status ON bank_transfers_billingoinvoice(payment_status);
CREATE INDEX idx_billingo_invoice_date ON bank_transfers_billingoinvoice(invoice_date);
CREATE INDEX idx_billingo_invoice_partner ON bank_transfers_billingoinvoice(partner_tax_number);
```

#### Sample Data

```sql
-- Example invoice from PETZ Kórház
INSERT INTO bank_transfers_billingoinvoice VALUES (
    111369290,  -- Billingo ID
    4,          -- Company ID
    'INV-2025-244',
    'invoice',
    NULL,
    FALSE,
    249952,
    'outstanding',
    'wire_transfer',
    19476607.00,
    'HUF',
    1.000000,
    '2025-10-22',
    '2025-10-27',
    '2025-11-21',
    '2025-10-27',
    'MEDKA Kft.',
    '32560682-2-43',
    '10410400-00000190-04894827',
    'HU28104104000000019004894827',
    '',
    1843084827,
    'GYŐR-MOSON-SOPRON VÁRMEGYEI PETZ ALADÁR EGYETEMI OKTATÓ KÓRHÁZ',
    '15366052-2-08',
    '',
    '',
    '--',
    'Lejelentő: TRA/MEDK/2025/8...',
    'done',
    '2025-10-27 05:40:22',
    '2025-10-27 05:40:22'
);
```

---

### 3. bank_transfers_billingoinvoiceitem

**Purpose**: Stores individual line items for each Billingo invoice.

**Django Model**: `BillingoInvoiceItem`

#### Columns

| Column | Type | Null | Default | Description |
|--------|------|------|---------|-------------|
| `id` | BIGINT | NO | AUTO | Primary key (auto-increment) |
| `invoice_id` | BIGINT | NO | - | Foreign key to BillingoInvoice |
| `product_id` | BIGINT | NO | - | Billingo product catalog ID |
| `name` | VARCHAR(255) | NO | - | Line item description/product name |
| `quantity` | DECIMAL(10,2) | NO | - | Quantity ordered/delivered |
| `unit` | VARCHAR(20) | NO | - | Unit of measure (PIECE, HOUR, LITER, etc.) |
| `net_unit_price` | DECIMAL(15,2) | NO | - | Unit price excluding VAT |
| `net_amount` | DECIMAL(15,2) | NO | - | Total net amount (quantity × net_unit_price) |
| `gross_amount` | DECIMAL(15,2) | NO | - | Total gross amount (including VAT) |
| `vat` | VARCHAR(10) | NO | - | VAT rate percentage (27%, 5%, 0%) |
| `entitlement` | VARCHAR(50) | YES | **NULL** | VAT entitlement code (if applicable) |
| `created_at` | DATETIME | NO | NOW() | Record creation timestamp |
| `updated_at` | DATETIME | NO | NOW() | Last modification timestamp |

#### Constraints

- **Primary Key**: `id`
- **Foreign Key**: `invoice_id` → `bank_transfers_billingoinvoice.id` (CASCADE DELETE)

#### Indexes

```sql
-- Performance index for invoice item lookup
CREATE INDEX idx_billingo_item_invoice ON bank_transfers_billingoinvoiceitem(invoice_id);
```

#### Important Notes

- **Entitlement Field**: Added `null=True` in migration 0048 to allow NULL values (some invoices don't have VAT entitlement codes)
- **Cascade Delete**: When an invoice is deleted, all its items are automatically removed

#### Sample Data

```sql
-- Medical device line item
INSERT INTO bank_transfers_billingoinvoiceitem VALUES (
    302,
    111324303,
    18015515,
    'MR004C SEQUENT MENISCAL REPAIR DEVICE, CURVED NEEDLE, 4 IMPLANTS',
    1.00,
    'db',
    0.00,
    121923.00,
    154842.21,
    '27%',
    NULL,
    '2025-10-27 05:40:22',
    '2025-10-27 05:40:22'
);
```

---

### 4. bank_transfers_billingosynclog

**Purpose**: Audit trail for Billingo synchronization operations with detailed metrics and error tracking.

**Django Model**: `BillingoSyncLog`

#### Columns

| Column | Type | Null | Default | Description |
|--------|------|------|---------|-------------|
| `id` | BIGINT | NO | AUTO | Primary key |
| `company_id` | BIGINT | NO | - | Foreign key to Company |
| `sync_type` | VARCHAR(20) | NO | - | MANUAL or AUTOMATIC |
| `status` | VARCHAR(20) | NO | - | RUNNING, COMPLETED, FAILED, PARTIAL |
| `invoices_processed` | INT | NO | 0 | Total invoices fetched from API |
| `invoices_created` | INT | NO | 0 | New invoices inserted |
| `invoices_updated` | INT | NO | 0 | Existing invoices modified |
| `invoices_skipped` | INT | NO | 0 | Invoices with errors or duplicates |
| `items_extracted` | INT | NO | 0 | Total line items processed |
| `api_calls_made` | INT | NO | 0 | Number of API requests (pagination) |
| `sync_duration_seconds` | INT | YES | NULL | Total sync time in seconds |
| `started_at` | DATETIME | NO | NOW() | Sync operation start time |
| `completed_at` | DATETIME | YES | NULL | Sync operation completion time |
| `errors` | TEXT | YES | NULL | JSON-encoded error details |
| `created_at` | DATETIME | NO | NOW() | Record creation timestamp |

#### Constraints

- **Primary Key**: `id`
- **Foreign Key**: `company_id` → `bank_transfers_company.id` (CASCADE DELETE)

#### Indexes

```sql
-- Performance indexes for log queries
CREATE INDEX idx_billingo_log_company ON bank_transfers_billingosynclog(company_id);
CREATE INDEX idx_billingo_log_started ON bank_transfers_billingosynclog(started_at);
CREATE INDEX idx_billingo_log_status ON bank_transfers_billingosynclog(status);
```

#### Status Values

- **RUNNING**: Sync operation in progress
- **COMPLETED**: All invoices synced successfully (errors = 0)
- **FAILED**: Sync operation completely failed (no invoices synced)
- **PARTIAL**: Some invoices synced, some failed (errors > 0)

#### Sample Log Entry

```sql
-- Successful sync of 282 invoices
INSERT INTO bank_transfers_billingosynclog VALUES (
    2,
    4,
    'MANUAL',
    'COMPLETED',
    282,    -- processed
    281,    -- created
    1,      -- updated
    0,      -- skipped
    581,    -- items
    3,      -- API calls (3 pages × 100 invoices)
    3,      -- duration: 3 seconds
    '2025-10-27 05:40:21',
    '2025-10-27 05:40:24',
    '',     -- no errors
    '2025-10-27 05:40:24'
);
```

---

## Indexes and Constraints

### Performance Optimization

All tables include indexes on:
- **Foreign Keys**: For efficient JOIN operations
- **Search Fields**: `invoice_number`, `partner_tax_number`, `payment_status`
- **Date Fields**: `invoice_date`, `started_at` for time-range queries

### Data Integrity

- **Cascade Deletes**: All Billingo tables cascade delete with Company
- **Unique Constraints**: Prevent duplicate settings and invoices per company
- **Non-Null Constraints**: Essential fields (amounts, dates) cannot be NULL

---

## Data Flow

### Synchronization Process

1. **Trigger**: Manual via API or automatic via cron job
2. **Authentication**: Decrypt API key from `CompanyBillingoSettings`
3. **API Call**: GET `/documents` with pagination (100 invoices per page)
4. **Processing**: For each invoice:
   - Create/update `BillingoInvoice` record
   - Delete existing items (if update)
   - Create `BillingoInvoiceItem` records
5. **Logging**: Create `BillingoSyncLog` entry with metrics
6. **Update**: Set `last_sync_time` in `CompanyBillingoSettings`

### Transaction Safety

All database operations are wrapped in Django's `@transaction.atomic` decorator:
- Invoice + items are inserted/updated atomically
- Failures roll back to maintain consistency
- Partial success is logged with error details

---

## Security Considerations

### API Key Protection

1. **Encryption at Rest**
   - Uses Fernet symmetric encryption (AES-128-CBC)
   - Encryption key stored in `CREDENTIAL_ENCRYPTION_KEY` environment variable
   - Never stored in plaintext

2. **API Response Protection**
   - Serializers never expose decrypted API keys
   - Frontend receives only `has_api_key: boolean`
   - Admin users can update but not retrieve keys

3. **Access Control**
   - Only users with `ADMIN` role can manage Billingo settings
   - Feature flag `BILLINGO_SYNC` controls access per company
   - All endpoints require authentication

### Data Privacy

- Invoice data is company-scoped (multi-tenant isolation)
- Partner information (tax numbers, bank accounts) is business data, not PII
- Audit logs track all sync operations with timestamps

---

## Migration History

### Migration 0046: Initial Schema (2025-10-27)
- Created 4 Billingo tables
- Added indexes and constraints
- Configured cascade deletes

### Migration 0047: Feature Flag (2025-10-27)
- Added `BILLINGO_SYNC` to `FeatureTemplate`
- Category: SYNC
- Default: Disabled (opt-in per company)

### Migration 0048: Null Entitlement Fix (2025-10-27)
- Changed `entitlement` field to allow NULL
- **Reason**: Some Billingo invoices don't include VAT entitlement codes
- **Impact**: Prevents sync failures for valid invoices

---

## Query Examples

### Get Company's Last Sync Status

```sql
SELECT
    s.last_sync_time,
    l.status,
    l.invoices_processed,
    l.sync_duration_seconds
FROM bank_transfers_companybillingosettings s
LEFT JOIN bank_transfers_billingosynclog l ON s.company_id = l.company_id
WHERE s.company_id = 4
ORDER BY l.started_at DESC
LIMIT 1;
```

### Find Unpaid Invoices Over Due Date

```sql
SELECT
    invoice_number,
    partner_name,
    gross_total,
    currency,
    due_date,
    DATEDIFF(NOW(), due_date) AS days_overdue
FROM bank_transfers_billingoinvoice
WHERE company_id = 4
  AND payment_status = 'outstanding'
  AND due_date < NOW()
ORDER BY due_date ASC;
```

### Sync Performance Metrics

```sql
SELECT
    DATE(started_at) AS sync_date,
    COUNT(*) AS sync_count,
    AVG(invoices_processed) AS avg_invoices,
    AVG(sync_duration_seconds) AS avg_duration_sec,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count
FROM bank_transfers_billingosynclog
WHERE company_id = 4
  AND started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(started_at)
ORDER BY sync_date DESC;
```

---

## Troubleshooting

### Common Issues

**Issue**: Sync fails with "entitlement cannot be NULL"
- **Solution**: Apply migration 0048 to allow NULL values

**Issue**: API authentication fails
- **Solution**: Verify API key is valid in Billingo dashboard, re-encrypt and save

**Issue**: Duplicate invoice errors
- **Solution**: Unique constraint prevents duplicates; update existing record instead

### Health Check Query

```sql
-- Verify Billingo integration health
SELECT
    c.name AS company,
    s.is_active,
    s.has_api_key,
    s.last_sync_time,
    COUNT(DISTINCT i.id) AS invoice_count,
    COUNT(DISTINCT it.id) AS item_count
FROM bank_transfers_companybillingosettings s
JOIN bank_transfers_company c ON s.company_id = c.id
LEFT JOIN bank_transfers_billingoinvoice i ON s.company_id = i.company_id
LEFT JOIN bank_transfers_billingoinvoiceitem it ON i.id = it.invoice_id
WHERE s.is_active = TRUE
GROUP BY c.id, c.name, s.is_active, s.has_api_key, s.last_sync_time;
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Maintained By**: Backend Team
