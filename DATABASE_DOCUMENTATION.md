# Database Schema Documentation
## Transfer XML Generator - Hungarian Banking System

**Last Updated:** 2025-08-20  
**Database:** PostgreSQL (Production on Railway) / SQL Server (Local Development)  
**Schema Version:** Multi-Company Architecture with Migration 0010  

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
**Table Comment:** *Company-scoped originator bank accounts for transfers. Contains accounts that will be debited during XML generation.*

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
| `order` | INTEGER | DEFAULT 0 | Transfer order within batch for XML generation |
| `is_processed` | BOOLEAN | DEFAULT FALSE | Marks transfers that have been included in generated XML files |
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
**Table Comment:** *Groups transfers into batches for XML generation. Each batch represents one XML file sent to the bank.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique identifier for transfer batch |
| `company_id` | INTEGER | FK(bank_transfers_company.id) | Company owner of this batch |
| `name` | VARCHAR(200) | NOT NULL | User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3") |
| `description` | TEXT | | Detailed description of the batch contents and purpose |
| `total_amount` | DECIMAL(15,2) | DEFAULT 0 | Sum of all transfer amounts in this batch |
| `used_in_bank` | BOOLEAN | DEFAULT FALSE | Flag indicating whether XML file was uploaded to internet banking |
| `bank_usage_date` | TIMESTAMP | | Timestamp when the XML was uploaded to bank system |
| `order` | INTEGER | DEFAULT 0 | Display order for batch listing and downloads |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Batch creation timestamp |
| `xml_generated_at` | TIMESTAMP | | Timestamp when the XML file was generated for this batch |

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

### XML Export Format
- Clean account numbers (no dashes) for XML generation
- SEPA-compatible Hungarian transaction format
- Support for HUF, EUR, USD currencies

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
- **Current**: Full multi-tenant isolation implemented

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