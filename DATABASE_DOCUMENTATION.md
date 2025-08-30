# Database Schema Documentation
## Transfer XML Generator - Hungarian Banking System

**Last Updated:** 2025-08-23  
**Database:** PostgreSQL (Production on Railway) / SQL Server (Local Development)  
**Schema Version:** Multi-Company Architecture with NAV Integration (Migration 0019)  

> **Note:** This documentation is the **single source of truth** for database schema. All database comment scripts should be generated from this document.

## Multi-Company Architecture Overview

The system implements a **multi-tenant architecture** where:
- **Companies** are isolated data containers
- **Users** can belong to multiple companies with different roles
- **All business data** is company-scoped for complete data isolation
- **Authentication** is handled via JWT with company context switching

---

## 1. **bank_transfers_company**
**Table Comment:** *Company entities for multi-tenant architecture. Each company has complete data isolation.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for company |
| `name` | VARCHAR(200) | NOT NULL | Company legal name |
| `tax_id` | VARCHAR(20) | NOT NULL, UNIQUE | Hungarian tax identification number (adószám) |
| `address` | TEXT | | Company registered address |
| `phone` | VARCHAR(50) | | Primary contact phone number |
| `email` | VARCHAR(254) | | Primary contact email address |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag for company deactivation |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Company registration timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `tax_id`
- Index on `is_active` for filtering

---

## 2. **bank_transfers_companyuser**
**Table Comment:** *User-company relationships with role-based access control. Enables multi-company membership.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for user-company relationship |
| `user_id` | INTEGER | NOT NULL, FK(auth_user.id) | Reference to Django User |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Reference to Company |
| `role` | VARCHAR(10) | NOT NULL, DEFAULT 'USER' | Role: 'ADMIN' or 'USER' |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active membership flag |
| `joined_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Membership creation timestamp |

**Indexes:**
- Primary key on `id`
- Unique constraint on `user_id, company_id`
- Index on `company_id` for membership queries
- Index on `role` for role filtering

**Constraints:**
- `role` CHECK constraint: VALUES ('ADMIN', 'USER')

---

## 3. **bank_transfers_userprofile**
**Table Comment:** *Extended user profile information with company preferences and localization settings.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for user profile |
| `user_id` | INTEGER | NOT NULL, UNIQUE, FK(auth_user.id) | One-to-one reference to Django User |
| `phone` | VARCHAR(50) | | User phone number |
| `preferred_language` | VARCHAR(10) | DEFAULT 'hu' | UI language preference |
| `timezone` | VARCHAR(50) | DEFAULT 'Europe/Budapest' | User timezone setting |
| `last_active_company_id` | INTEGER | FK(bank_transfers_company.id) | Last company context used |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Profile creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `user_id`
- Index on `last_active_company_id`

---

## 4. **bank_transfers_bankaccount**
**Table Comment:** *Company-scoped originator bank accounts for transfers. Contains accounts that will be debited during XML/CSV export generation.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for bank account record |
| `company_id` | INTEGER | FK(bank_transfers_company.id) | Company owner of this account |
| `name` | VARCHAR(200) | NOT NULL | Display name for the account (e.g., "Main Business Account", "Payroll Account") |
| `account_number` | VARCHAR(50) | NOT NULL | Hungarian bank account number in formatted form (e.g., "1210001119014874" or "12100011-19014874") |
| `bank_name` | VARCHAR(200) | | Name of the bank holding this account |
| `is_default` | BOOLEAN | DEFAULT FALSE | Flags the default account for new transfers within the company |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Account registration timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `is_default` for default account lookup

**Business Rules:**
- Only one account per company should have `is_default = TRUE`
- Account numbers must follow Hungarian banking format validation

---

## 5. **bank_transfers_beneficiary**
**Table Comment:** *Company-scoped beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for beneficiary record |
| `company_id` | INTEGER | FK(bank_transfers_company.id) | Company owner of this beneficiary |
| `name` | VARCHAR(200) | NOT NULL | Full legal name of the beneficiary (person or organization) |
| `account_number` | VARCHAR(50) | NOT NULL | Beneficiary's bank account number in Hungarian format (validated and formatted) |
| `description` | VARCHAR(200) | | Additional information about the beneficiary (bank name, organization details, etc.) |
| `is_frequent` | BOOLEAN | DEFAULT FALSE | Marks frequently used beneficiaries for quick access in UI |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag - inactive beneficiaries are hidden from selection |
| `remittance_information` | TEXT | | Default payment references, invoice numbers, or transaction-specific information |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Beneficiary registration timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `name` for search functionality
- Index on `is_frequent` for frequent beneficiary lookup
- Index on `is_active` for active filtering

**Business Rules:**
- Account numbers are validated using Hungarian banking rules (16 or 24 digits)
- Account numbers are automatically formatted (8-8 or 8-8-8 with dashes)

---

## 6. **bank_transfers_transfertemplate**
**Table Comment:** *Company-scoped reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for transfer template |
| `company_id` | INTEGER | FK(bank_transfers_company.id) | Company owner of this template |
| `name` | VARCHAR(200) | NOT NULL | Descriptive name for the template (e.g., "Monthly Payroll", "Q1 VAT Payments") |
| `description` | TEXT | | Detailed description of when and how to use this template |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag - inactive templates are hidden from selection |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Template creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `name` for search functionality
- Index on `is_active` for active filtering

---

## 7. **bank_transfers_templatebeneficiary**
**Table Comment:** *Junction table linking templates to beneficiaries with default payment amounts and remittance information.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for template-beneficiary relationship |
| `template_id` | INTEGER | NOT NULL, FK(bank_transfers_transfertemplate.id) | Reference to the transfer template |
| `beneficiary_id` | INTEGER | NOT NULL, FK(bank_transfers_beneficiary.id) | Reference to the beneficiary |
| `default_amount` | DECIMAL(15,2) | | Default payment amount for this beneficiary in this template |
| `default_remittance` | VARCHAR(500) | | Default remittance information/memo for payments to this beneficiary |
| `default_execution_date` | DATE | | Default execution date for this beneficiary's payments |
| `order` | INTEGER | DEFAULT 0 | Display order of beneficiaries within the template |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether this beneficiary is active in the template |

**Indexes:**
- Primary key on `id`
- Unique constraint on `template_id, beneficiary_id`
- Index on `template_id` for template beneficiary lookup
- Index on `order` for ordered display

---

## 8. **bank_transfers_transfer**
**Table Comment:** *Individual transfer records representing single bank payments. These are processed into XML batches for bank import.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for individual transfer |
| `originator_account_id` | INTEGER | NOT NULL, FK(bank_transfers_bankaccount.id) | Reference to the bank account that will be debited |
| `beneficiary_id` | INTEGER | NOT NULL, FK(bank_transfers_beneficiary.id) | Reference to the payment recipient |
| `amount` | DECIMAL(15,2) | NOT NULL, CHECK(amount >= 0.01) | Transfer amount in the specified currency |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'HUF' | ISO currency code (HUF, EUR, USD) |
| `execution_date` | DATE | NOT NULL | Requested date for the bank to process the transfer |
| `remittance_info` | VARCHAR(500) | NOT NULL | Payment reference/memo that appears on bank statements |
| `template_id` | INTEGER | FK(bank_transfers_transfertemplate.id) | Reference to template if this transfer was created from a template |
| `order` | INTEGER | DEFAULT 0 | Transfer order within batch for XML/CSV export generation |
| `is_processed` | BOOLEAN | DEFAULT FALSE | Marks transfers that have been included in generated XML/CSV files |
| `notes` | TEXT | | Internal notes about this specific transfer |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Transfer creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `originator_account_id` for account-based queries
- Index on `beneficiary_id` for beneficiary-based queries
- Index on `execution_date` for date-based filtering
- Index on `is_processed` for processing status queries
- Index on `created_at` for chronological ordering

**Constraints:**
- `currency` CHECK constraint: VALUES ('HUF', 'EUR', 'USD')
- `amount` must be >= 0.01

---

## 9. **bank_transfers_transferbatch**
**Table Comment:** *Groups transfers into batches for XML/CSV export generation. Each batch represents one export file (XML or CSV) sent to the bank.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for transfer batch |
| `company_id` | INTEGER | FK(bank_transfers_company.id) | Company owner of this batch |
| `name` | VARCHAR(200) | NOT NULL | User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3") |
| `description` | TEXT | | Detailed description of the batch contents and purpose |
| `total_amount` | DECIMAL(15,2) | DEFAULT 0 | Sum of all transfer amounts in this batch |
| `used_in_bank` | BOOLEAN | DEFAULT FALSE | Flag indicating whether export file (XML/CSV) was uploaded to internet banking |
| `bank_usage_date` | TIMESTAMP | | Timestamp when the export file was uploaded to bank system |
| `order` | INTEGER | DEFAULT 0 | Display order for batch listing and downloads |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Batch creation timestamp |
| `batch_format` | VARCHAR(10) | DEFAULT 'XML' | Export file format: XML (SEPA XML) or KH_CSV (KH Bank CSV) |
| `xml_generated_at` | TIMESTAMP | | Timestamp when the export file was generated for this batch |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `created_at` for chronological ordering
- Index on `used_in_bank` for filtering processed batches

---

## 10. **bank_transfers_transferbatch_transfers**
**Table Comment:** *Many-to-many junction table linking transfer batches to individual transfers.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for batch-transfer relationship |
| `transferbatch_id` | INTEGER | NOT NULL, FK(bank_transfers_transferbatch.id) | Reference to the transfer batch |
| `transfer_id` | INTEGER | NOT NULL, FK(bank_transfers_transfer.id) | Reference to the individual transfer |

**Indexes:**
- Primary key on `id`
- Unique constraint on `transferbatch_id, transfer_id`
- Index on `transferbatch_id` for batch transfer lookup
- Index on `transfer_id` for transfer batch lookup

---

## 11. **bank_transfers_navconfiguration**
**Table Comment:** *NAV (Hungarian Tax Authority) API configuration for invoice synchronization. One configuration per company.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for NAV configuration |
| `company_id` | INTEGER | NOT NULL, UNIQUE, FK(bank_transfers_company.id) | One-to-one reference to company |
| `tax_number` | VARCHAR(20) | NOT NULL | Hungarian tax number for NAV authentication |
| `username` | VARCHAR(100) | NOT NULL | NAV API username |
| `password` | VARCHAR(255) | NOT NULL | NAV API password (encrypted with Fernet) |
| `signature_key` | VARCHAR(255) | NOT NULL | NAV API signature key (encrypted with Fernet) |
| `is_production` | BOOLEAN | DEFAULT FALSE | Use production NAV API (true) or test environment (false) |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Configuration creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `company_id`
- Index on `tax_number`

**Security Notes:**
- `password` and `signature_key` are encrypted using Fernet symmetric encryption
- Decryption handled by `CredentialManager` service
- Production/test endpoint automatically selected based on `is_production` flag

---

## 12. **bank_transfers_invoice**
**Table Comment:** *Invoice records synchronized from NAV (Hungarian Tax Authority) system with complete XML storage.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for invoice record |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company owner of this invoice |
| `invoice_number` | VARCHAR(100) | NOT NULL | NAV invoice number (e.g., "A/A28700200/1180/00013") |
| `supplier_name` | VARCHAR(200) | | Name of invoice supplier/issuer |
| `customer_name` | VARCHAR(200) | | Name of invoice customer/recipient |
| `net_amount` | DECIMAL(15,2) | | Net amount without VAT |
| `vat_amount` | DECIMAL(15,2) | | VAT amount |
| `gross_amount` | DECIMAL(15,2) | | Total gross amount (net + VAT) |
| `currency` | VARCHAR(3) | DEFAULT 'HUF' | ISO currency code |
| `issue_date` | DATE | | Invoice issue date |
| `due_date` | DATE | | Payment due date |
| `payment_method` | VARCHAR(50) | | Payment method (e.g., "TRANSFER", "CASH") |
| `direction` | VARCHAR(10) | | Invoice direction: "INBOUND" or "OUTBOUND" |
| `nav_transaction_id` | VARCHAR(100) | | NAV system transaction identifier |
| `nav_index` | INTEGER | | NAV system index number |
| `nav_source` | VARCHAR(10) | | NAV data source indicator |
| `nav_creation_date` | TIMESTAMP | | Invoice creation date in NAV system |
| `original_request_version` | VARCHAR(10) | | NAV API version used for original request |
| `nav_invoice_xml` | TEXT | | **Complete XML invoice data from NAV system** |
| `nav_invoice_hash` | VARCHAR(200) | | Hash/checksum of invoice XML for integrity verification |
| `ins_cus_user` | VARCHAR(100) | | NAV system user who inserted/modified the record |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Local creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last local modification timestamp |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `invoice_number` for invoice lookup
- Index on `issue_date` for date-based filtering
- Index on `direction` for inbound/outbound filtering
- Index on `nav_transaction_id` for NAV transaction lookup

**Constraints:**
- `currency` CHECK constraint: VALUES ('HUF', 'EUR', 'USD')
- `direction` CHECK constraint: VALUES ('INBOUND', 'OUTBOUND')

**Business Rules:**
- `nav_invoice_xml` contains the complete base64-decoded XML invoice data from NAV
- Gross amounts are extracted from XML when available, otherwise calculated from net + VAT
- Invoice numbers must be unique within company scope

---

## 13. **bank_transfers_invoicelineitem**
**Table Comment:** *Line items extracted from NAV invoice XML data. Represents individual products/services on invoices.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for invoice line item |
| `invoice_id` | INTEGER | NOT NULL, FK(bank_transfers_invoice.id) | Reference to parent invoice |
| `line_number` | INTEGER | NOT NULL | Line item sequence number (1, 2, 3...) |
| `line_description` | VARCHAR(500) | | Description of product/service |
| `quantity` | DECIMAL(15,6) | | Quantity of product/service |
| `unit_of_measure` | VARCHAR(50) | | Unit of measurement (e.g., "PIECE", "LITER", "HOUR") |
| `unit_price` | DECIMAL(15,2) | | Price per unit before VAT |
| `line_net_amount` | DECIMAL(15,2) | | Line total net amount (quantity × unit_price) |
| `vat_rate` | DECIMAL(5,4) | | VAT rate as decimal (e.g., 0.27 for 27%) |
| `line_vat_amount` | DECIMAL(15,2) | | VAT amount for this line |
| `line_gross_amount` | DECIMAL(15,2) | | Total gross amount for this line |
| `product_code` | VARCHAR(100) | | Internal product/service code |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Line item extraction timestamp |

**Indexes:**
- Primary key on `id`
- Index on `invoice_id` for invoice line lookup
- Index on `line_number` for ordered display

**Business Rules:**
- Line items are automatically extracted from NAV invoice XML
- Some older invoices (pre-2021) may not have detailed line item data
- VAT rates stored as decimals (0.27 = 27%, 0.05 = 5%)

---

## 14. **bank_transfers_invoicesynclog**
**Table Comment:** *Audit log for NAV invoice synchronization operations with error tracking and performance metrics.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for sync log entry |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id) | Company for which sync was performed |
| `sync_type` | VARCHAR(20) | NOT NULL | Type of sync operation (e.g., "DAILY", "HISTORICAL", "MANUAL") |
| `direction` | VARCHAR(10) | NOT NULL | Invoice direction synced: "INBOUND" or "OUTBOUND" |
| `date_from` | DATE | NOT NULL | Start date of sync range |
| `date_to` | DATE | NOT NULL | End date of sync range |
| `invoices_processed` | INTEGER | DEFAULT 0 | Total number of invoices processed |
| `invoices_created` | INTEGER | DEFAULT 0 | Number of new invoices created |
| `invoices_updated` | INTEGER | DEFAULT 0 | Number of existing invoices updated |
| `invoices_skipped` | INTEGER | DEFAULT 0 | Number of invoices skipped due to errors |
| `line_items_extracted` | INTEGER | DEFAULT 0 | Total line items extracted from XML |
| `errors` | TEXT | | JSON array of error messages encountered |
| `sync_duration_seconds` | INTEGER | | Total sync operation duration |
| `api_calls_made` | INTEGER | DEFAULT 0 | Number of NAV API calls performed |
| `xml_data_size_mb` | DECIMAL(10,3) | | Total size of XML data processed (MB) |
| `started_at` | TIMESTAMP | NOT NULL | Sync operation start timestamp |
| `completed_at` | TIMESTAMP | | Sync operation completion timestamp |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'RUNNING' | Sync status: "RUNNING", "COMPLETED", "FAILED", "PARTIAL" |

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company sync history
- Index on `started_at` for chronological ordering
- Index on `status` for filtering by sync status
- Index on `sync_type` for sync operation analysis

**Constraints:**
- `direction` CHECK constraint: VALUES ('INBOUND', 'OUTBOUND')
- `status` CHECK constraint: VALUES ('RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL')
- `sync_type` CHECK constraint: VALUES ('DAILY', 'HISTORICAL', 'MANUAL', 'REALTIME')

---

## NAV Integration Architecture

### API Integration Pattern
The NAV integration uses a sophisticated **multi-step query pattern**:

1. **Query Invoice Digest**: Get list of invoices for date range
2. **Query Invoice Chain Digest**: Get metadata for specific invoice
3. **Query Invoice Data**: Get complete XML invoice data

### Data Flow
```
NAV API → Base64 XML → Decoded XML → Database Storage
   ↓           ↓            ↓             ↓
Token      Invoice      Financial    Line Items
Auth       Metadata     Amounts      Extraction
```

### XML Data Storage
- Complete NAV invoice XML stored in `nav_invoice_xml` field
- Average XML size: 2-40KB per invoice
- Base64 decoded and UTF-8 encoded for storage
- Line items extracted using XML parsing with proper namespace handling

### Production vs Test Environment
- **Production**: `https://api.onlineszamla.nav.gov.hu/invoiceService/v3`
- **Test**: `https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3`
- Controlled by `NavConfiguration.is_production` flag

### Security Features
- Fernet encryption for NAV credentials
- SHA3-512 request signatures
- Automatic token refresh and expiration handling
- Comprehensive audit logging

---

## Data Isolation and Multi-Company Features

### Company Scoping
All core business models include a `company_id` foreign key:
- `BankAccount.company_id`
- `Beneficiary.company_id` 
- `TransferTemplate.company_id`
- `TransferBatch.company_id`

### Company Context Resolution
- **Transfer.company**: Derived from `originator_account.company`
- **TemplateBeneficiary.company**: Derived from `template.company` and `beneficiary.company`

### Permission Model
- **ADMIN**: Full CRUD access to company data, user management
- **USER**: Read/write access to transfers, beneficiaries, templates

### Authentication Flow
1. User logs in → JWT token issued
2. `X-Company-ID` header or user profile determines active company
3. All API requests scoped to active company context
4. Company switching updates `UserProfile.last_active_company`

---

## Hungarian Banking Validation

### Account Number Format
- **16-digit legacy**: `XXXXXXXX-XXXXXXXX`
- **24-digit BBAN**: `XXXXXXXX-XXXXXXXX-XXXXXXXX`
- Validated using Hungarian checksum algorithm
- Stored with proper formatting (dashes included)

### Export Formats

#### XML Export Format
- Clean account numbers (no dashes) for XML generation
- SEPA-compatible Hungarian transaction format
- Support for HUF, EUR, USD currencies
- Unlimited transfers per batch

#### KH Bank CSV Format
- Hungarian "Egyszerűsített forintátutalás" (.HUF.csv) format
- Specialized for KH Bank import system
- Maximum 40 transfers per batch (KH Bank limitation)
- HUF currency only

---

## Performance Optimizations

### Database Indexes
- All foreign keys indexed for fast joins
- Search fields (`name`, `account_number`) indexed
- Filtering fields (`is_active`, `is_frequent`, `is_processed`) indexed
- Chronological fields (`created_at`, `execution_date`) indexed

### Query Optimization
- Company-scoped queries use `company_id` index
- Pagination implemented for large result sets
- Select-related used for foreign key joins

---

## Migration History

- **0008**: Added multi-company architecture (`Company`, `CompanyUser`, `UserProfile`)
- **0009**: Populated default company for existing data
- **0010**: Added unique constraints for company-scoped models
- **0011**: Added NAV invoice models (`Invoice`, `InvoiceLineItem`, `InvoiceSyncLog`)
- **0012-0015**: NAV configuration and credential management
- **0016**: NAV business fields and tax number integration
- **0017**: Fixed NAV field nullable constraints
- **0018**: Added batch index field for NAV processing
- **0019**: Added XML storage fields (`nav_invoice_xml`, `nav_invoice_hash`)
- **Current**: Full multi-tenant isolation with complete NAV integration

---

## Development vs Production

### Local Development (SQL Server)
- Database: `administration` on `localhost:1435`
- Uses SQL Server extended properties for comments
- MSSQL-specific data types and constraints

### Production (Railway + PostgreSQL)  
- Database: PostgreSQL managed by Railway
- Uses PostgreSQL COMMENT ON statements
- PostgreSQL-specific data types and constraints

**Note**: This documentation represents the PostgreSQL production schema. SQL Server development retains compatibility through Django model abstraction.

## Database Comment Implementation

### SQL Comment Scripts Available:
- **SQL Server (Local)**: `/backend/sql/complete_database_comments_sqlserver.sql`
- **PostgreSQL (Production)**: `/backend/sql/complete_database_comments_postgresql.sql`

Both scripts provide complete table and column comments for all 14 tables and their columns, including:
- Multi-company architecture tables (Company, CompanyUser, UserProfile)
- Core transfer system (BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch)
- NAV integration system (NavConfiguration, Invoice, InvoiceLineItem, InvoiceSyncLog)

### Script Features:
- **Complete coverage**: All current models and fields documented
- **Database-specific syntax**: SQL Server extended properties vs PostgreSQL COMMENT ON
- **Verification queries**: Built-in queries to confirm comments were added
- **Clean installation**: Optional cleanup of existing comments before adding new ones

### Usage:
```sql
-- SQL Server
USE administration;
-- Execute: complete_database_comments_sqlserver.sql

-- PostgreSQL  
-- Execute: complete_database_comments_postgresql.sql
```