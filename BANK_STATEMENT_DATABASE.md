# Bank Statement Import - Database Schema Documentation
## Transfer XML Generator - Bank Statement Import & Transaction Matching

**Last Updated:** 2025-11-08
**Database:** PostgreSQL (Production on Railway) / SQL Server (Local Development)
**Schema Version:** Bank Statement Import with Batch Invoice Matching (Migration 0062)

> **Note:** This documentation covers bank statement import tables only. For complete database schema, see `DATABASE_DOCUMENTATION.md`.
> SQL comment scripts are maintained separately in `backend/sql/` directory.

---

## Overview

The bank statement import system provides:
- **Multi-bank support**: GRÁNIT, Revolut, MagNet, K&H
- **Duplicate prevention**: SHA256 file hashing per company
- **Intelligent matching**: 7 automatic matching strategies
- **Batch invoice matching**: One payment for multiple invoices (NEW in Migration 0062)
- **Company isolation**: Multi-tenant architecture with data separation

---

## 21. **bank_transfers_bankstatement**
**Table Comment:** *Uploaded bank statement files with parsed metadata and transaction statistics. Supports multi-bank formats (PDF, CSV, XML) with automatic bank detection and duplicate prevention.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique identifier for statement file |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id), CASCADE | Company owner of this statement |
| `bank_code` | VARCHAR(20) | NOT NULL | Bank identifier code (GRANIT, REVOLUT, MAGNET, KH) |
| `bank_name` | VARCHAR(200) | NOT NULL | Bank display name for UI |
| `bank_bic` | VARCHAR(11) | | Bank BIC/SWIFT code |
| `account_number` | VARCHAR(50) | | Account number extracted from statement |
| `account_iban` | VARCHAR(34) | | IBAN extracted from statement |
| `statement_number` | VARCHAR(100) | | Statement reference/serial number |
| `statement_period_from` | DATE | | Statement period start date |
| `statement_period_to` | DATE | | Statement period end date |
| `opening_balance` | DECIMAL(15,2) | | Opening balance at period start |
| `closing_balance` | DECIMAL(15,2) | | Closing balance at period end |
| `currency` | VARCHAR(3) | DEFAULT 'HUF' | Statement currency (ISO 4217 code) |
| `file_name` | VARCHAR(255) | NOT NULL | Original uploaded filename |
| `file_hash` | VARCHAR(64) | NOT NULL, INDEX | SHA256 hash for duplicate detection |
| `file_size` | INTEGER | | File size in bytes |
| `file_path` | VARCHAR(500) | | Server storage path |
| `uploaded_by_id` | INTEGER | FK(auth_user.id), SET_NULL | User who uploaded the file |
| `uploaded_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Upload timestamp |
| `status` | VARCHAR(20) | NOT NULL, CHECK, DEFAULT 'UPLOADED' | Processing status |
| `total_transactions` | INTEGER | DEFAULT 0 | Total number of transactions parsed |
| `credit_count` | INTEGER | DEFAULT 0 | Number of credit transactions (incoming) |
| `debit_count` | INTEGER | DEFAULT 0 | Number of debit transactions (outgoing) |
| `total_credits` | DECIMAL(15,2) | DEFAULT 0.00 | Sum of all credit amounts |
| `total_debits` | DECIMAL(15,2) | DEFAULT 0.00 | Sum of all debit amounts (absolute values) |
| `matched_count` | INTEGER | DEFAULT 0 | Number of successfully matched transactions |
| `parse_error` | TEXT | | Error message if parsing failed |
| `parse_warnings` | JSON | DEFAULT '[]' | Non-fatal warnings during parsing |
| `raw_metadata` | JSON | DEFAULT '{}' | Bank-specific metadata from statement |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Status Choices (STATUS_CHOICES):**
- `UPLOADED` - File uploaded successfully, awaiting parsing
- `PARSING` - Currently parsing transactions from file
- `COMPLETED` - Parsing completed successfully
- `ERROR` - Parsing failed, see parse_error for details

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `file_hash` for duplicate detection
- Composite index on `(company_id, uploaded_at)` for recent statements lookup
- Composite index on `(company_id, bank_code)` for bank filtering

**UNIQUE Constraints:**
- Unique constraint on `(company_id, file_hash)` - Prevents duplicate file uploads per company

**CHECK Constraints:**
- `status` CHECK constraint: Must be one of STATUS_CHOICES

**Business Rules:**
- **Duplicate Prevention**: File hash is SHA256 of file content, scoped to company
- **Statistics Calculation**: `total_transactions`, `matched_count`, etc. updated after parsing completion
- **Status Workflow**: UPLOADED → PARSING → (COMPLETED | ERROR)
- **Balance Validation**: `opening_balance + total_credits - total_debits` should equal `closing_balance` (advisory)
- **Company Isolation**: Same file can be uploaded by different companies (different `company_id`)

---

## 22. **bank_transfers_banktransaction**
**Table Comment:** *Individual transaction records extracted from bank statements. Supports all transaction types including AFR transfers, POS purchases, bank fees, interest, and other banking operations. Contains matching to NAV invoices, transfers, and reimbursement pairs.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique identifier for transaction record |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id), CASCADE | Company owner of this transaction |
| `bank_statement_id` | INTEGER | NOT NULL, FK(bank_transfers_bankstatement.id), CASCADE | Reference to parent bank statement |
| `transaction_type` | VARCHAR(30) | NOT NULL, CHECK, INDEX | Transaction type code (see TRANSACTION_TYPES below) |
| `booking_date` | DATE | NOT NULL, INDEX | Date when transaction was booked to account |
| `value_date` | DATE | NOT NULL, INDEX | Value date (effective date) for interest calculation |
| `amount` | DECIMAL(15,2) | NOT NULL, INDEX | Transaction amount (negative for debit, positive for credit) |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'HUF' | ISO currency code |
| `description` | TEXT | NOT NULL | Full transaction description from bank |
| `short_description` | VARCHAR(200) | | Shortened or summarized description |
| `payment_id` | VARCHAR(100) | INDEX | Payment identifier from bank system |
| `transaction_id` | VARCHAR(100) | | Unique transaction identifier |
| `payer_name` | VARCHAR(200) | INDEX | Name of payer (for incoming transfers) |
| `payer_iban` | VARCHAR(34) | | IBAN of payer |
| `payer_account_number` | VARCHAR(50) | | Account number of payer |
| `payer_bic` | VARCHAR(11) | | BIC of payer's bank |
| `beneficiary_name` | VARCHAR(200) | INDEX | Name of beneficiary (for outgoing transfers) |
| `beneficiary_iban` | VARCHAR(34) | | IBAN of beneficiary |
| `beneficiary_account_number` | VARCHAR(50) | | Account number of beneficiary |
| `beneficiary_bic` | VARCHAR(11) | | BIC of beneficiary's bank |
| `reference` | VARCHAR(500) | INDEX | Unstructured remittance information (közlemény) - critical for invoice matching |
| `partner_id` | VARCHAR(100) | | End-to-end identifier between transaction partners |
| `transaction_type_code` | VARCHAR(100) | | Bank-specific transaction type code (e.g., "001-00") |
| `fee_amount` | DECIMAL(15,2) | | Transaction fee charged by bank |
| `card_number` | VARCHAR(20) | | Masked card number for POS/ATM transactions |
| `merchant_name` | VARCHAR(200) | | Merchant name for POS purchases |
| `merchant_location` | VARCHAR(200) | | Merchant location for POS purchases |
| `original_amount` | DECIMAL(15,2) | | Original amount in foreign currency (before conversion) |
| `original_currency` | VARCHAR(3) | | Original currency code for FX transactions |
| `exchange_rate` | DECIMAL(15,6) | | Exchange rate used for currency conversion (6 decimal precision) |
| `matched_invoice_id` | INTEGER | FK(bank_transfers_invoice.id), SET_NULL | **DEPRECATED** - NAV invoice matched to this transaction (use matched_invoices instead) |
| `matched_transfer_id` | INTEGER | FK(bank_transfers_transfer.id), SET_NULL | Transfer from executed batch matched to this transaction |
| `matched_reimbursement_id` | INTEGER | FK(bank_transfers_banktransaction.id), SET_NULL | Offsetting transaction (e.g., POS purchase + personal reimbursement transfer) |
| `match_confidence` | DECIMAL(3,2) | DEFAULT 0.00 | Matching confidence score (0.00 to 1.00) |
| `match_method` | VARCHAR(50) | CHECK | Method used for matching (see MATCH_METHOD_CHOICES below) |
| `match_notes` | TEXT | | Additional notes about matching process |
| `matched_at` | TIMESTAMP | | Timestamp when transaction was matched |
| `matched_by_id` | INTEGER | FK(auth_user.id), SET_NULL | User who performed matching (NULL for automatic) |
| `raw_data` | JSON | DEFAULT '{}' | Raw transaction data from bank statement (sanitized for JSON storage) |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Transaction Types (TRANSACTION_TYPES):**
- `AFR_CREDIT` - AFR jóváírás (Incoming instant payment)
- `AFR_DEBIT` - AFR terhelés (Outgoing instant payment)
- `TRANSFER_CREDIT` - Átutalás jóváírás (Incoming transfer)
- `TRANSFER_DEBIT` - Átutalás terhelés (Outgoing transfer)
- `POS_PURCHASE` - POS vásárlás (Card purchase)
- `ATM_WITHDRAWAL` - ATM készpénzfelvétel (Cash withdrawal)
- `BANK_FEE` - Banki jutalék/költség (Bank fee)
- `INTEREST_CREDIT` - Kamatjóváírás (Interest credit)
- `INTEREST_DEBIT` - Kamatköltség (Interest charge)
- `CORRECTION` - Helyesbítés/Sztornó (Correction)
- `OTHER` - Egyéb tranzakció (Other)

**Match Methods (MATCH_METHOD_CHOICES):**
- `REFERENCE_EXACT` - Közlemény alapján (pontos) - Exact reference match (1.00 confidence)
- `AMOUNT_IBAN` - Összeg + IBAN alapján - Amount and IBAN match (0.95 confidence)
- `BATCH_INVOICES` - **Több számla párosítás - Batch invoice match (0.85-1.00 confidence)** ⭐ NEW in Migration 0061
- `FUZZY_NAME` - Összeg + név hasonlóság alapján - Amount and fuzzy name match (0.70-0.90 confidence)
- `AMOUNT_DATE_ONLY` - Összeg + dátum alapján - Amount and date only (0.60 confidence)
- `TRANSFER_EXACT` - Átutalási köteg alapján - Transfer batch match (1.00 confidence)
- `REIMBURSEMENT_PAIR` - Ellentételezés (személyes visszafizetés) - Reimbursement offsetting (0.70 confidence)
- `MANUAL` - Manuális párosítás - Manual single matching by user (1.00 confidence)
- `MANUAL_BATCH` - **Manuális több számla párosítás - Manual batch matching** ⭐ NEW in Migration 0061

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Index on `bank_statement_id` for statement transaction lookup
- Index on `transaction_type` for type filtering
- Index on `booking_date` for date-based queries
- Index on `value_date` for value date filtering
- Index on `amount` for amount-based queries
- Index on `payment_id` for payment ID lookup
- Index on `reference` for reference-based matching
- Index on `payer_name` for payer search
- Index on `beneficiary_name` for beneficiary search
- Index on `matched_invoice_id` for invoice matching queries (will be deprecated)
- Composite index on `(bank_statement_id, booking_date)` for statement timeline
- Composite index on `(company_id, booking_date)` for company transaction history
- Composite index on `(company_id, transaction_type, booking_date)` for type-based reporting
- Composite index on `(amount, currency)` for amount-based matching

**CHECK Constraints:**
- `transaction_type` CHECK constraint: Must be one of TRANSACTION_TYPES
- `match_method` CHECK constraint: Must be one of MATCH_METHOD_CHOICES

**Business Rules:**
- **Negative for Debit**: Negative amounts indicate money leaving account (debit)
- **Positive for Credit**: Positive amounts indicate money entering account (credit)
- **Multi-Type Support**: Single model handles all transaction types (transfers, POS, fees, etc.)
- **NAV Invoice Matching**: Automatic matching to invoices using 7 matching strategies (see transaction_matching_service.py)
- **Transfer Matching**: Links to executed transfers from TransferBatch (used_in_bank=True)
- **Reimbursement Pairs**: Self-referencing FK for offsetting transactions (e.g., POS purchase + personal reimbursement)
- **Confidence Scoring**: Match confidence from 0.00 (no match) to 1.00 (perfect match)
- **Auto-Payment**: Invoices with match_confidence >= 0.90 are automatically marked as PAID
- **Backward Compatibility**: `matched_invoice_id` field kept for legacy support, new code should use `matched_invoices` ManyToMany
- **Raw Data Storage**: Complete transaction data preserved in JSON for audit trail
- **FX Support**: Original amount and exchange rate stored for foreign currency transactions

**API Access:**
- `GET /api/bank-transactions/` - List transactions with filtering and pagination
- `GET /api/bank-transactions/{id}/` - Transaction details
- `POST /api/bank-transactions/{id}/match_invoice/` - Manually match single invoice (backward compatibility)
- `POST /api/bank-transactions/{id}/batch_match_invoices/` - **Manually match MULTIPLE invoices (batch payment)** ⭐ NEW
- `POST /api/bank-transactions/{id}/unmatch/` - Remove invoice match(es) - supports both single and batch
- `POST /api/bank-transactions/{id}/rematch/` - Re-run automatic matching
- `GET /api/bank-transactions/statistics/` - Transaction statistics and summaries

---

## 23. **bank_transfers_banktransactioninvoicematch**
**Table Comment:** *Intermediate table for ManyToMany relationship between BankTransaction and Invoice. Stores per-invoice match metadata (confidence, method, notes) for both single and batch invoice matching. Enables one payment to cover multiple invoices from the same supplier.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique identifier for match record |
| `transaction_id` | INTEGER | NOT NULL, FK(bank_transfers_banktransaction.id), CASCADE | Bank transaction that was matched |
| `invoice_id` | INTEGER | NOT NULL, FK(bank_transfers_invoice.id), CASCADE | NAV invoice that was matched |
| `match_confidence` | DECIMAL(4,2) | NOT NULL, DEFAULT 0.00 | Match confidence score (0.00 to 1.00) |
| `match_method` | VARCHAR(50) | NOT NULL | Method used for matching (see MATCH_METHOD_CHOICES below) |
| `matched_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Timestamp when match was created |
| `matched_by_id` | INTEGER | FK(auth_user.id), SET_NULL | User who created manual match (NULL for automatic) |
| `match_notes` | TEXT | | Detailed match information for audit trail |

**Match Methods (MATCH_METHOD_CHOICES):**
- `REFERENCE_EXACT` - Reference Exact Match (invoice number in reference field)
- `AMOUNT_IBAN` - Amount + IBAN Match (exact amount + supplier IBAN)
- `BATCH_INVOICES` - **Batch Invoice Match (one payment for multiple invoices) - Automatic** ⭐ NEW
- `FUZZY_NAME` - Fuzzy Name Match (amount + name similarity)
- `AMOUNT_DATE_ONLY` - Amount + Date Only (fallback match with low confidence)
- `MANUAL` - Manual Single Match (user-initiated single invoice)
- `MANUAL_BATCH` - **Manual Batch Match (user-initiated multiple invoices)** ⭐ NEW

**Indexes:**
- Primary key on `id`
- Composite index on `(transaction_id, invoice_id)` - Name: `idx_tx_invoice_match`
- Index on `invoice_id` - Name: `idx_invoice_matches`

**UNIQUE Constraints:**
- Unique constraint on `(transaction_id, invoice_id)` - Prevents duplicate matches

**Business Rules:**
- **Batch Payment Support**: One transaction can be matched to multiple invoices (e.g., 450 HUF payment for 3 invoices: 100, 150, 200 HUF)
- **Same Supplier Requirement**: All invoices in a batch match must be from the same supplier (same `supplier_tax_number`)
- **Amount Validation**: Total invoice amounts must equal transaction amount (±1% tolerance)
- **Minimum Count**: Batch matching requires at least 2 invoices
- **Direction Requirement**: Only debit transactions (negative `amount`) can be batch matched to INBOUND invoices
- **Confidence Scoring** (Automatic Batch Match):
  - Base confidence: 0.85 for automatic batch matches
  - IBAN bonus: +0.10 if ANY invoice has matching `supplier_bank_account_number`
  - Name similarity bonus: +0.05 if average name similarity >= 70%
  - Manual matches: Always 1.00 confidence
- **Auto-Payment**: Invoices with `match_confidence >= 0.90` are automatically marked as PAID
- **Audit Trail**: `match_notes` field stores detailed information for each invoice in the batch
- **Backward Compatibility**: Single invoice matches also create one record in this table

**Batch Matching Algorithm:**
The system uses combinatorial search to find invoice combinations that sum to the transaction amount:
1. Get candidate invoices (same company, unpaid/prepared, correct direction, date range ±90 days)
2. Group invoices by supplier (`supplier_tax_number`)
3. For each supplier, try combinations of 2-5 invoices using `itertools.combinations()`
4. Check if sum of invoice amounts equals transaction amount (±1% tolerance)
5. Calculate confidence: Base 0.85 + IBAN bonus (+0.10) + Name similarity bonus (+0.05)
6. Select combination with highest confidence
7. Create one `BankTransactionInvoiceMatch` record per invoice in the combination

**API Access:**
- `POST /api/bank-transactions/{id}/batch_match_invoices/` - Create batch match
  - Request Body: `{"invoice_ids": [123, 456, 789]}`
  - Validates: Same supplier, amount match (±1% tolerance), minimum 2 invoices
  - Response: Match details with confidence, method, and matched invoice summary
- `POST /api/bank-transactions/{id}/unmatch/` - Remove all matches (works for both single and batch)
  - Deletes all `BankTransactionInvoiceMatch` records for the transaction
  - Clears legacy `matched_invoice_id` field
  - Response: Indicates if it was a batch match and how many invoices were unmatched

**Frontend Integration:**
The `BankTransactionSerializer` includes batch matching fields:
- `matched_invoices_details` - Array of all matched invoices with per-invoice metadata
- `is_batch_match` - Boolean flag (true if matched to more than 1 invoice)
- `total_matched_amount` - Sum of all matched invoice amounts
- `matched_invoice_details` - Single invoice details (DEPRECATED, kept for backward compatibility)

---

## 24. **bank_transfers_othercost**
**Table Comment:** *Additional cost records derived from bank transactions. Allows enhanced categorization, detailed notes, and flexible tagging beyond standard BankTransaction fields. Used for expense tracking, cost analysis, and financial reporting.*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique identifier for other cost record |
| `company_id` | INTEGER | NOT NULL, FK(bank_transfers_company.id), CASCADE | Company owner of this cost record |
| `bank_transaction_id` | INTEGER | FK(bank_transfers_banktransaction.id), CASCADE, UNIQUE | Optional reference to originating bank transaction |
| `category` | VARCHAR(50) | NOT NULL, CHECK | Cost category code (see CATEGORY_CHOICES below) |
| `amount` | DECIMAL(15,2) | NOT NULL | Cost amount (always positive for costs) |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'HUF' | ISO currency code |
| `date` | DATE | NOT NULL | Date of the cost |
| `description` | TEXT | NOT NULL | Detailed description of the cost |
| `notes` | TEXT | | Additional notes, context, or justification |
| `tags` | JSON | DEFAULT '[]' | Array of tag strings for flexible categorization (e.g., ["fuel", "travel", "office"]) |
| `created_by_id` | INTEGER | FK(auth_user.id), SET_NULL | User who created this cost record |
| `created_at` | TIMESTAMP | NOT NULL, AUTO_NOW_ADD | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO_NOW | Last modification timestamp |

**Category Choices (CATEGORY_CHOICES):**
- `BANK_FEE` - Banki költség (Bank fees, account maintenance)
- `CARD_PURCHASE` - Kártyás vásárlás (Card purchases, POS transactions)
- `INTEREST` - Kamat (Interest charges or credits)
- `TAX_DUTY` - Adó/illeték (Taxes, duties, government fees)
- `CASH_WITHDRAWAL` - Készpénzfelvétel (Cash withdrawals, ATM fees)
- `OTHER` - Egyéb költség (Other costs not categorized above)

**Indexes:**
- Primary key on `id`
- Index on `company_id` for company-scoped queries
- Unique index on `bank_transaction_id` for one-to-one relationship
- Index on `category` for category filtering
- Index on `date` for date-based queries
- Composite index on `(company_id, date)` for cost reporting

**CHECK Constraints:**
- `category` CHECK constraint: Must be one of CATEGORY_CHOICES

**Business Rules:**
- **One-to-One**: Each BankTransaction can have at most one OtherCost record
- **Positive Amounts**: Amounts are always positive (cost magnitude)
- **Flexible Tagging**: `tags` field allows custom categorization beyond predefined categories
- **Standalone Costs**: `bank_transaction_id` can be NULL for manually entered costs not tied to transactions
- **Company Isolation**: All costs are company-scoped

---

## Migration History

### Migration 0062 (2025-11-08) - Batch Invoice Matching Data Migration

**Purpose**: Migrate existing single invoice matches to new ManyToMany system

**Changes**:
- Migrated 73 existing `matched_invoice` (ForeignKey) matches to `BankTransactionInvoiceMatch` records
- Set `match_confidence = 0.95` for all legacy matches (assumed valid)
- Set `match_method = 'MANUAL'` for all legacy matches (unknown original method)
- Set `match_notes = 'Migrated from legacy matched_invoice field'`
- Preserved `matched_invoice_id` field for backward compatibility (not cleared)

**Reversibility**: Migration includes reverse operation to delete all `BankTransactionInvoiceMatch` records

### Migration 0061 (2025-11-08) - Batch Invoice Matching Schema

**Purpose**: Add database support for matching one bank transaction to multiple invoices

**Changes**:
- Created `BankTransactionInvoiceMatch` intermediate model with fields:
  - `transaction_id`, `invoice_id` (ForeignKeys with CASCADE)
  - `match_confidence`, `match_method`, `matched_at`, `matched_by_id`, `match_notes`
- Added `matched_invoices` ManyToManyField to `BankTransaction` model
  - Uses `through='BankTransactionInvoiceMatch'`
  - Related name: `bank_transactions_many`
- Added helper properties to `BankTransaction` model:
  - `is_batch_match` - Returns True if matched to multiple invoices
  - `total_matched_amount` - Sum of all matched invoice amounts
  - `matched_invoices_count` - Count of matched invoices
- Updated `matched_invoice` ForeignKey help_text to indicate deprecation
- Created indexes: `idx_tx_invoice_match`, `idx_invoice_matches`
- Created unique constraint on `(transaction_id, invoice_id)`

**New Match Methods Added**:
- `BATCH_INVOICES` - Automatic batch invoice matching
- `MANUAL_BATCH` - Manual batch invoice matching

---

**End of Bank Statement Database Documentation**
