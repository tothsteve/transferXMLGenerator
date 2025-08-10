# Database Schema Documentation
## Transfer XML Generator - Hungarian Banking System

### Database Tables and Column Descriptions

---

## 1. **bank_transfers_bankaccount**
**Table Comment:** *Stores originator bank accounts for transfers. Contains company/organization accounts that will be debited during XML generation.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for bank account record |
| `name` | VARCHAR(200) | NOT NULL | Display name for the bank account (e.g., "Main Business Account", "Payroll Account") |
| `account_number` | VARCHAR(50) | NOT NULL, UNIQUE | Hungarian bank account number in standard format (with dashes, e.g., "1210001119014874") |
| `is_default` | BOOLEAN | DEFAULT FALSE | Flags the default account for new transfers. Only one account should be default |
| `created_at` | DATETIME | NOT NULL, AUTO_NOW_ADD | Timestamp when the account record was created |
| `updated_at` | DATETIME | NOT NULL, AUTO_NOW | Timestamp when the account record was last modified |

**Indexes:**
- Primary key on `id`
- Unique index on `account_number`

---

## 2. **bank_transfers_beneficiary**
**Table Comment:** *Stores beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities that receive payments.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for beneficiary record |
| `name` | VARCHAR(200) | NOT NULL | Full legal name of the beneficiary (person or organization) |
| `account_number` | VARCHAR(50) | NOT NULL | Beneficiary's bank account number in Hungarian format |
| `bank_name` | VARCHAR(200) | NULLABLE | Name of the beneficiary's bank (optional, for reference) |
| `is_frequent` | BOOLEAN | DEFAULT FALSE | Marks frequently used beneficiaries for quick access |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag - inactive beneficiaries are hidden from selection |
| `notes` | TEXT | NULLABLE | Additional notes about the beneficiary (payment terms, contact info, etc.) |
| `created_at` | DATETIME | NOT NULL, AUTO_NOW_ADD | Timestamp when the beneficiary was added to the system |
| `updated_at` | DATETIME | NOT NULL, AUTO_NOW | Timestamp when the beneficiary record was last modified |

**Indexes:**
- Primary key on `id`
- Index on `name` for search performance
- Index on `is_frequent` for filtering frequent beneficiaries
- Index on `is_active` for filtering active beneficiaries

---

## 3. **bank_transfers_transfertemplate**
**Table Comment:** *Defines reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for transfer template |
| `name` | VARCHAR(200) | NOT NULL | Descriptive name for the template (e.g., "Monthly Payroll", "Q1 VAT Payments") |
| `description` | TEXT | NULLABLE | Detailed description of when and how to use this template |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag - inactive templates are hidden from selection |
| `created_at` | DATETIME | NOT NULL, AUTO_NOW_ADD | Timestamp when the template was created |
| `updated_at` | DATETIME | NOT NULL, AUTO_NOW | Timestamp when the template was last modified |

**Indexes:**
- Primary key on `id`

---

## 4. **bank_transfers_templatebeneficiary**
**Table Comment:** *Junction table linking templates to beneficiaries with default payment amounts and remittance information.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for template-beneficiary relationship |
| `template_id` | INTEGER | NOT NULL, FK | Reference to the transfer template |
| `beneficiary_id` | INTEGER | NOT NULL, FK | Reference to the beneficiary |
| `default_amount` | DECIMAL(15,2) | NULLABLE | Default payment amount for this beneficiary in this template |
| `default_remittance` | VARCHAR(500) | NULLABLE | Default remittance information/memo for payments to this beneficiary |
| `order` | INTEGER | DEFAULT 0 | Display order of beneficiaries within the template |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether this beneficiary is active in the template |

**Constraints:**
- Foreign key to `bank_transfers_transfertemplate(id)` ON DELETE CASCADE
- Foreign key to `bank_transfers_beneficiary(id)` ON DELETE CASCADE
- Unique constraint on `(template_id, beneficiary_id)` - each beneficiary can only appear once per template

**Indexes:**
- Primary key on `id`
- Index on `template_id`
- Index on `beneficiary_id`

---

## 5. **bank_transfers_transfer**
**Table Comment:** *Individual transfer records representing single bank payments. These are processed into XML batches for bank import.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for individual transfer |
| `originator_account_id` | INTEGER | NOT NULL, FK | Reference to the bank account that will be debited |
| `beneficiary_id` | INTEGER | NOT NULL, FK | Reference to the payment recipient |
| `amount` | DECIMAL(15,2) | NOT NULL, > 0.01 | Transfer amount in the specified currency |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'HUF' | ISO currency code (HUF, EUR, USD) |
| `execution_date` | DATE | NOT NULL | Requested date for the bank to process the transfer |
| `remittance_info` | VARCHAR(500) | NOT NULL | Payment reference/memo that appears on bank statements |
| `template_id` | INTEGER | NULLABLE, FK | Reference to template if this transfer was created from a template |
| `is_processed` | BOOLEAN | DEFAULT FALSE | Marks transfers that have been included in generated XML files |
| `notes` | TEXT | NULLABLE | Internal notes about this specific transfer |
| `created_at` | DATETIME | NOT NULL, AUTO_NOW_ADD | Timestamp when the transfer was created |
| `updated_at` | DATETIME | NOT NULL, AUTO_NOW | Timestamp when the transfer was last modified |

**Constraints:**
- Foreign key to `bank_transfers_bankaccount(id)` ON DELETE CASCADE
- Foreign key to `bank_transfers_beneficiary(id)` ON DELETE CASCADE
- Foreign key to `bank_transfers_transfertemplate(id)` ON DELETE SET NULL
- Check constraint: `amount >= 0.01`

**Indexes:**
- Primary key on `id`
- Index on `execution_date` for date-based queries
- Index on `is_processed` for filtering processed/unprocessed transfers
- Index on `created_at` for chronological sorting

---

## 6. **bank_transfers_transferbatch**
**Table Comment:** *Groups transfers into batches for XML generation. Each batch represents one XML file sent to the bank.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for transfer batch |
| `name` | VARCHAR(200) | NOT NULL | User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3") |
| `description` | TEXT | NULLABLE | Detailed description of the batch contents and purpose |
| `total_amount` | DECIMAL(15,2) | DEFAULT 0 | Sum of all transfer amounts in this batch |
| `created_at` | DATETIME | NOT NULL, AUTO_NOW_ADD | Timestamp when the batch was created |
| `xml_generated_at` | DATETIME | NULLABLE | Timestamp when the XML file was generated for this batch |

**Indexes:**
- Primary key on `id`

---

## 7. **bank_transfers_transferbatch_transfers**
**Table Comment:** *Many-to-many junction table linking transfer batches to individual transfers.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for batch-transfer relationship |
| `transferbatch_id` | INTEGER | NOT NULL, FK | Reference to the transfer batch |
| `transfer_id` | INTEGER | NOT NULL, FK | Reference to the individual transfer |

**Constraints:**
- Foreign key to `bank_transfers_transferbatch(id)` ON DELETE CASCADE
- Foreign key to `bank_transfers_transfer(id)` ON DELETE CASCADE
- Unique constraint on `(transferbatch_id, transfer_id)` - each transfer can only appear once per batch

**Indexes:**
- Primary key on `id`
- Index on `transferbatch_id`
- Index on `transfer_id`

---

## Business Rules and Data Flow

### 1. **Account Management**
- Only one bank account should have `is_default = TRUE` at any time
- Account numbers are stored with dashes but cleaned (dashes removed) for XML generation

### 2. **Beneficiary Management**
- Beneficiaries marked `is_frequent = TRUE` appear first in selection lists
- Beneficiaries with `is_active = FALSE` are soft-deleted and hidden from normal operations
- Account numbers follow Hungarian banking format

### 3. **Template System**
- Templates allow pre-configuration of recurring payment scenarios
- Template beneficiaries have default amounts and remittance info that can be customized per execution
- Templates can be activated/deactivated without losing historical data

### 4. **Transfer Processing**
- Transfers start with `is_processed = FALSE`
- When XML is generated, included transfers are marked `is_processed = TRUE`
- Processed transfers should not be modified to maintain audit trail

### 5. **Batch Generation**
- Batches group transfers for XML file generation
- `total_amount` is calculated sum of all transfers in the batch
- `xml_generated_at` timestamp marks when the batch was exported

### 6. **XML Output**
- Generated XML follows Hungarian SEPA format
- Account numbers are cleaned (no dashes/spaces)
- Currency is always specified (HUF, EUR, USD)
- Execution dates follow ISO format (YYYY-MM-DD)

---

## Common Queries

```sql
-- Get default bank account
SELECT * FROM bank_transfers_bankaccount WHERE is_default = TRUE;

-- Get frequent beneficiaries
SELECT * FROM bank_transfers_beneficiary 
WHERE is_frequent = TRUE AND is_active = TRUE 
ORDER BY name;

-- Get unprocessed transfers for a specific date range
SELECT t.*, b.name as beneficiary_name 
FROM bank_transfers_transfer t
JOIN bank_transfers_beneficiary b ON t.beneficiary_id = b.id
WHERE t.is_processed = FALSE 
  AND t.execution_date BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY t.execution_date, b.name;

-- Get template with beneficiaries and default amounts
SELECT t.name as template_name, b.name as beneficiary_name, 
       tb.default_amount, tb.default_remittance
FROM bank_transfers_transfertemplate t
JOIN bank_transfers_templatebeneficiary tb ON t.id = tb.template_id
JOIN bank_transfers_beneficiary b ON tb.beneficiary_id = b.id
WHERE t.id = 1 AND t.is_active = TRUE AND tb.is_active = TRUE
ORDER BY tb.order, b.name;
```