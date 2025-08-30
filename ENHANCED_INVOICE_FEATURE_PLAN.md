# Enhanced Invoice Management & Expense Tracking System - Complete Feature Plan

## Overview
This comprehensive plan extends your existing transfer XML generator system with advanced invoice management, expense tracking, company-specific feature flags, and bank statement reconciliation. The approach follows a database-first architecture leveraging your existing multi-company system while adding sophisticated financial management capabilities.

## Current System Architecture Analysis

### Existing Strengths:
- Multi-company architecture with Company model
- Existing NAV invoice synchronization (Invoice, InvoiceLineItem models)
- Transfer/Batch system for XML/CSV generation
- Beneficiary management system
- Service layer architecture with proper separation of concerns

### Current Core Tables:
- `Company` - Multi-tenant base
- `BankAccount` - Company bank accounts  
- `Beneficiary` - Payment recipients (will become unified Partner)
- `TransferTemplate` - Recurring transfer patterns
- `Transfer` - Individual transfers
- `TransferBatch` - Grouped transfers for XML/CSV generation
- `Invoice` - NAV-synced invoices (INBOUND/OUTBOUND)
- `InvoiceLineItem` - Invoice details
- `NavConfiguration` - NAV API credentials

## Database-First Architecture Design

### 1. Company Feature Management System

```sql
-- Feature flags per company
CREATE TABLE company_feature (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    company_id BIGINT NOT NULL REFERENCES company(id),
    feature_code VARCHAR(50) NOT NULL,  -- 'EXPORT_XML_SEPA', 'NAV_SYNC', etc.
    is_enabled BIT NOT NULL DEFAULT 0,
    config_json NVARCHAR(MAX),  -- JSON config for feature-specific settings
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_company_feature UNIQUE (company_id, feature_code),
    INDEX IX_company_feature_lookup (company_id, feature_code, is_enabled)
);

-- Default feature templates for new companies
CREATE TABLE feature_template (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    feature_code VARCHAR(50) NOT NULL UNIQUE,
    display_name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500),
    default_enabled BIT NOT NULL DEFAULT 0,
    config_schema NVARCHAR(MAX),  -- JSON schema for validation
    category VARCHAR(50) NOT NULL DEFAULT 'GENERAL',  -- EXPORT, SYNC, TRACKING, etc.
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
```

**Feature Flag Examples:**
- `EXPORT_XML_SEPA`: Enable SEPA XML export
- `EXPORT_CSV_KH`: Enable KH Bank CSV export  
- `EXPORT_CSV_CUSTOM`: Enable custom CSV formats
- `NAV_SYNC`: Enable NAV invoice synchronization
- `EXPENSE_TRACKING`: Enable expense entry management
- `BANK_STATEMENT_IMPORT`: Enable bank statement processing
- `MULTI_CURRENCY`: Enable USD/EUR invoice handling

### 2. Unified Partner System (Beneficiary Extension)

```sql
-- Extend existing beneficiary table to become unified partner
ALTER TABLE beneficiary ADD 
    partner_type VARCHAR(20) DEFAULT 'CUSTOMER',  -- SUPPLIER/CUSTOMER/BOTH
    tax_number VARCHAR(20),
    is_nav_synced BIT DEFAULT 0,
    default_payment_method VARCHAR(20),  -- TRANSFER/CARD/CASH
    always_paid_by_card BIT DEFAULT 0,
    supplier_category VARCHAR(50),  -- For expense categorization
    payment_terms_days INT,
    notes NVARCHAR(MAX);

-- Index for NAV matching
CREATE INDEX IX_beneficiary_nav_matching ON beneficiary (company_id, tax_number) 
WHERE tax_number IS NOT NULL;

-- Track partner payment behavior patterns
CREATE TABLE partner_payment_history (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    partner_id BIGINT NOT NULL REFERENCES beneficiary(id),
    payment_method VARCHAR(20) NOT NULL,
    frequency_count INT NOT NULL DEFAULT 1,
    last_used_date DATETIME2 NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_partner_payment_method UNIQUE (partner_id, payment_method)
);
```

### 3. Enhanced Invoice Management System

```sql
-- Extend existing invoice table for manual entries
ALTER TABLE invoice ADD 
    source VARCHAR(20) NOT NULL DEFAULT 'NAV_SYNC',  -- NAV_SYNC/MANUAL
    partner_id BIGINT REFERENCES beneficiary(id),  -- Link to unified partner
    payment_status VARCHAR(20) DEFAULT 'UNPAID',  -- UNPAID/PARTIAL/PAID/OVERDUE
    is_expense BIT DEFAULT 0,  -- True for supplier invoices that are expenses
    expense_category VARCHAR(50),
    notes NVARCHAR(MAX),
    attachment_path NVARCHAR(500);

-- Manual invoice entries for USD/EUR and non-NAV invoices
CREATE TABLE manual_invoice (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    company_id BIGINT NOT NULL REFERENCES company(id),
    invoice_number NVARCHAR(100) NOT NULL,
    partner_id BIGINT NOT NULL REFERENCES beneficiary(id),
    invoice_direction VARCHAR(10) NOT NULL,  -- INBOUND/OUTBOUND
    issue_date DATE NOT NULL,
    due_date DATE,
    currency_code VARCHAR(3) NOT NULL DEFAULT 'HUF',
    net_amount DECIMAL(15,2) NOT NULL,
    vat_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    gross_amount DECIMAL(15,2) NOT NULL,
    exchange_rate DECIMAL(10,4),  -- For non-HUF currencies
    gross_amount_huf DECIMAL(15,2),  -- Calculated HUF equivalent
    description NVARCHAR(MAX),
    expense_category VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'UNPAID',
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_manual_invoice_number UNIQUE (company_id, invoice_number),
    INDEX IX_manual_invoice_partner (partner_id),
    INDEX IX_manual_invoice_date (issue_date),
    INDEX IX_manual_invoice_status (payment_status)
);
```

### 4. Invoice Payment Tracking System

```sql
-- Track all invoice payments (both NAV and manual invoices)
CREATE TABLE invoice_payment (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    invoice_id BIGINT REFERENCES invoice(id),  -- NAV invoice
    manual_invoice_id BIGINT REFERENCES manual_invoice(id),  -- Manual invoice
    payment_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'HUF',
    payment_method VARCHAR(20) NOT NULL,  -- TRANSFER/CARD/CASH/OTHER
    reference NVARCHAR(200),  -- Transfer batch ref or manual note
    is_auto_matched BIT DEFAULT 0,  -- Matched from bank statement
    bank_transaction_id BIGINT,  -- Will reference bank_transaction
    notes NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    -- Ensure only one invoice type is referenced
    CONSTRAINT CHK_invoice_payment_single_ref 
        CHECK ((invoice_id IS NOT NULL AND manual_invoice_id IS NULL) OR 
               (invoice_id IS NULL AND manual_invoice_id IS NOT NULL)),
    
    INDEX IX_payment_invoice (invoice_id),
    INDEX IX_payment_manual_invoice (manual_invoice_id),
    INDEX IX_payment_date (payment_date),
    INDEX IX_payment_auto_match (is_auto_matched)
);
```

### 5. Comprehensive Expense Tracking System

```sql
-- General expense entries (salaries, taxes, utilities, etc.)
CREATE TABLE expense_entry (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    company_id BIGINT NOT NULL REFERENCES company(id),
    expense_type VARCHAR(50) NOT NULL,  -- SALARY/TAX/SUPPLIER/UTILITY/OTHER
    category VARCHAR(50) NOT NULL,  -- More specific categorization
    description NVARCHAR(MAX) NOT NULL,
    partner_id BIGINT REFERENCES beneficiary(id),  -- Optional partner link
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'HUF',
    expense_date DATE NOT NULL,
    payment_method VARCHAR(20),  -- TRANSFER/CARD/CASH/OTHER
    is_recurring BIT DEFAULT 0,
    recurrence_pattern NVARCHAR(100),  -- 'MONTHLY', 'QUARTERLY', etc.
    source_transfer_batch_id BIGINT REFERENCES transfer_batch(id),
    source_manual_invoice_id BIGINT REFERENCES manual_invoice(id),
    is_paid BIT DEFAULT 0,
    payment_date DATE,
    notes NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    INDEX IX_expense_company (company_id),
    INDEX IX_expense_category (category),
    INDEX IX_expense_date (expense_date),
    INDEX IX_expense_partner (partner_id),
    INDEX IX_expense_type (expense_type)
);

-- Expense categories configuration per company
CREATE TABLE expense_category (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    company_id BIGINT NOT NULL REFERENCES company(id),
    category_code VARCHAR(50) NOT NULL,
    display_name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500),
    default_expense_type VARCHAR(50),
    is_active BIT DEFAULT 1,
    sort_order INT DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_expense_category UNIQUE (company_id, category_code)
);
```

### 6. Bank Statement Integration & Reconciliation

```sql
-- Bank statement files
CREATE TABLE bank_statement (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    company_id BIGINT NOT NULL REFERENCES company(id),
    bank_account_id BIGINT NOT NULL REFERENCES bank_account(id),
    statement_date DATE NOT NULL,
    statement_period_start DATE,
    statement_period_end DATE,
    opening_balance DECIMAL(15,2) NOT NULL,
    closing_balance DECIMAL(15,2) NOT NULL,
    transaction_count INT NOT NULL DEFAULT 0,
    import_source VARCHAR(50) NOT NULL,  -- CSV/OFX/XLS/MANUAL
    import_filename NVARCHAR(500),
    processed BIT DEFAULT 0,
    processing_errors NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    INDEX IX_statement_account (bank_account_id),
    INDEX IX_statement_date (statement_date),
    INDEX IX_statement_processed (processed)
);

-- Individual bank transactions with smart matching
CREATE TABLE bank_transaction (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    statement_id BIGINT NOT NULL REFERENCES bank_statement(id),
    transaction_date DATE NOT NULL,
    value_date DATE,
    amount DECIMAL(15,2) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,  -- DEBIT/CREDIT
    counterparty_name NVARCHAR(200),
    counterparty_account VARCHAR(50),
    reference NVARCHAR(200),
    description NVARCHAR(MAX),
    category VARCHAR(50),
    
    -- Smart matching fields
    matched_transfer_batch_id BIGINT REFERENCES transfer_batch(id),
    matched_invoice_id BIGINT REFERENCES invoice(id),
    matched_manual_invoice_id BIGINT REFERENCES manual_invoice(id),
    matched_expense_id BIGINT REFERENCES expense_entry(id),
    is_processed BIT DEFAULT 0,
    match_confidence DECIMAL(3,2),  -- 0.00-1.00 confidence score
    processing_notes NVARCHAR(MAX),
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    INDEX IX_transaction_statement (statement_id),
    INDEX IX_transaction_date (transaction_date),
    INDEX IX_transaction_amount (amount),
    INDEX IX_transaction_counterparty (counterparty_account),
    INDEX IX_transaction_processed (is_processed),
    INDEX IX_transaction_batch_match (matched_transfer_batch_id)
);
```

### 7. Enhanced Transfer Batch Reconciliation

```sql
-- Extend existing transfer_batch table
ALTER TABLE transfer_batch ADD
    reconciliation_status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/MATCHED/PARTIAL/MANUAL
    bank_statement_id BIGINT REFERENCES bank_statement(id),
    reconciled_at DATETIME2,
    reconciliation_notes NVARCHAR(MAX);

-- Link individual transfers to their bank transactions
CREATE TABLE transfer_reconciliation (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    transfer_id BIGINT NOT NULL REFERENCES transfer(id),
    bank_transaction_id BIGINT NOT NULL REFERENCES bank_transaction(id),
    match_type VARCHAR(20) NOT NULL,  -- EXACT/FUZZY/MANUAL
    match_confidence DECIMAL(3,2) NOT NULL,
    matched_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    matched_by_user_id BIGINT,
    
    CONSTRAINT UQ_transfer_reconciliation UNIQUE (transfer_id, bank_transaction_id)
);
```

### 8. Power BI Integration & Embedded Reports

```sql
-- Comprehensive financial view for Power BI
CREATE VIEW vw_financial_transactions AS
SELECT 
    'INVOICE_PAYMENT' as transaction_type,
    c.name as company_name,
    ip.payment_date as transaction_date,
    COALESCE(i.supplier_name, i.customer_name, p.name) as counterparty,
    ip.amount,
    ip.currency,
    CASE i.invoice_direction 
        WHEN 'INBOUND' THEN 'EXPENSE' 
        WHEN 'OUTBOUND' THEN 'REVENUE' 
    END as flow_direction,
    i.supplier_tax_number as counterparty_tax_number,
    ip.payment_method,
    'NAV_INVOICE' as source_type,
    ip.created_at
FROM invoice_payment ip
JOIN invoice i ON ip.invoice_id = i.id
JOIN company c ON i.company_id = c.id
LEFT JOIN beneficiary p ON i.partner_id = p.id

UNION ALL

SELECT 
    'MANUAL_INVOICE_PAYMENT' as transaction_type,
    c.name as company_name,
    ip.payment_date as transaction_date,
    p.name as counterparty,
    ip.amount,
    ip.currency,
    CASE mi.invoice_direction 
        WHEN 'INBOUND' THEN 'EXPENSE' 
        WHEN 'OUTBOUND' THEN 'REVENUE' 
    END as flow_direction,
    p.tax_number as counterparty_tax_number,
    ip.payment_method,
    'MANUAL_INVOICE' as source_type,
    ip.created_at
FROM invoice_payment ip
JOIN manual_invoice mi ON ip.manual_invoice_id = mi.id
JOIN company c ON mi.company_id = c.id
JOIN beneficiary p ON mi.partner_id = p.id

UNION ALL

SELECT 
    'EXPENSE' as transaction_type,
    c.name as company_name,
    ee.expense_date as transaction_date,
    COALESCE(p.name, 'Direct Expense') as counterparty,
    ee.amount,
    ee.currency,
    'EXPENSE' as flow_direction,
    p.tax_number as counterparty_tax_number,
    ee.payment_method,
    'EXPENSE_ENTRY' as source_type,
    ee.created_at
FROM expense_entry ee
JOIN company c ON ee.company_id = c.id
LEFT JOIN beneficiary p ON ee.partner_id = p.id;

-- Power BI report embedding configuration
CREATE TABLE powerbi_report_config (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    company_id BIGINT NOT NULL REFERENCES company(id),
    report_name NVARCHAR(100) NOT NULL,
    powerbi_workspace_id NVARCHAR(100) NOT NULL,
    powerbi_report_id NVARCHAR(100) NOT NULL,
    embed_url NVARCHAR(1000) NOT NULL,
    is_active BIT DEFAULT 1,
    access_roles NVARCHAR(500),  -- JSON array of roles that can access
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_company_report UNIQUE (company_id, report_name)
);
```

## Smart Matching & Automation Logic

### Batch-to-Invoice Reconciliation Algorithm:
```python
# Match criteria priority:
1. Exact amount + counterparty account + reference match
2. Exact amount + counterparty name + date range match  
3. Fuzzy amount (±1%) + counterparty similarity + date range
4. Manual review queue for unmatched transactions
```

### Partner Payment Intelligence:
- Auto-matching NAV partners to existing Partners by tax_number/name
- Default payment behavior flags (always_paid_by_card, default_payment_method)
- Partner payment history tracking and preference learning

### Automatic Payment Status Updates:
- When `transfer_batch.used_in_bank = TRUE`
- Match batch transfers to NAV invoices by amount + account + remittance_info  
- Suggest marking matched NAV invoices as paid
- Create InvoicePayment records for confirmed matches

## Implementation Phases & Timeline

### Phase 1: Foundation (4-6 weeks)
**Database & Core Models**
- Implement CompanyFeature and FeatureTemplate models
- Extend Beneficiary to unified Partner model  
- Create database migrations with proper indexes
- Feature flag middleware and API endpoints

**Tests:**
- Feature flag enforcement across API endpoints
- Partner matching and conversion logic
- Database constraint validation

### Phase 2: Enhanced Invoice System (6-8 weeks)  
**Manual Invoice Management**
- ManualInvoice model and CRUD operations
- InvoicePayment tracking system
- Payment status calculation logic
- Multi-currency support with HUF conversion

**Tests:**
- Manual invoice CRUD operations
- Payment workflow end-to-end
- Currency conversion accuracy
- Payment status calculation logic

### Phase 3: Expense Tracking (6-8 weeks)
**Expense Management**
- ExpenseEntry and ExpenseCategory models
- Automatic expense creation from transfers
- Recurring expense pattern recognition
- Integration with partner system

**Tests:**
- Expense categorization accuracy
- Recurring expense detection
- Transfer-to-expense automation
- Category management per company

### Phase 4: Bank Statement Integration (6-8 weeks)
**Statement Processing & Reconciliation**
- BankStatement and BankTransaction models
- File import system (CSV/OFX/Excel)
- Smart matching algorithms implementation
- Transfer batch reconciliation

**Tests:**
- File import accuracy across formats
- Matching algorithm precision and recall
- Reconciliation workflow completeness
- Performance with large transaction volumes

### Phase 5: Advanced Features (4-6 weeks)
**Intelligence & Automation**
- Partner payment behavior learning
- Automatic invoice payment suggestions
- Advanced matching confidence scoring
- Bulk processing operations

**Tests:**
- Payment behavior prediction accuracy
- Suggestion system relevance
- Confidence scoring calibration
- Bulk operation performance

### Phase 6: Power BI & Reporting (2-3 weeks)
**Business Intelligence Integration**
- Financial transaction views optimization
- Power BI report embedding system
- Real-time data synchronization
- Performance monitoring

**Tests:**
- Data consistency across views
- Report embedding functionality
- Query performance optimization
- Real-time update accuracy

## Migration Strategy & Data Preservation

### Backward Compatibility Plan:
1. **Existing functionality preservation**: All current transfer/template/batch operations unchanged
2. **Gradual feature rollout**: Feature flags enable company-by-company activation
3. **Data migration scripts**: Convert existing beneficiaries to partners seamlessly
4. **Rollback capability**: Feature flags allow disabling new features if issues arise

### Data Migration Steps:
1. **Partner conversion**: `UPDATE beneficiary SET partner_type='CUSTOMER'` for all existing records
2. **NAV invoice linking**: Background job to match existing NAV invoices to partners by tax_number
3. **Feature initialization**: Enable current feature set for all existing companies
4. **Index optimization**: Create performance indexes for new reporting queries

## Performance & Scalability Considerations

### Database Optimization:
```sql
-- Critical performance indexes
CREATE INDEX IX_invoice_payment_lookup ON invoice_payment (payment_date, payment_method, amount);
CREATE INDEX IX_expense_reporting ON expense_entry (company_id, expense_date, category, amount);
CREATE INDEX IX_bank_transaction_matching ON bank_transaction (transaction_date, amount, counterparty_account);
CREATE INDEX IX_partner_tax_lookup ON beneficiary (company_id, tax_number) WHERE tax_number IS NOT NULL;
CREATE INDEX IX_financial_reporting ON invoice (company_id, issue_date, invoice_direction, currency_code);
```

### System Architecture Benefits:
- **Scalability**: Designed for Power BI direct database connections
- **Flexibility**: Feature flags enable progressive company onboarding  
- **Data Integrity**: Strong foreign key relationships and business logic constraints
- **Performance**: Optimized for both transactional operations and analytical reporting
- **Maintainability**: Service layer architecture with clear separation of concerns

## Business Use Cases & Workflows

### Use Case 1: Monthly Payroll Processing
1. Create salary expense entries for employees
2. Generate transfer batch for salary payments
3. Upload transfer file to bank
4. Mark batch as `used_in_bank=true`
5. System automatically creates expense entries with payment confirmation
6. Power BI reports show monthly payroll expenses

### Use Case 2: Supplier Invoice Management
1. NAV sync imports supplier invoices automatically
2. System matches suppliers to existing partners by tax number
3. For card payments: System checks partner's `always_paid_by_card` flag
4. Auto-mark invoice as paid if partner has card payment history
5. For transfer payments: Create transfer batch and process normally
6. Bank statement import confirms payment and updates invoice status

### Use Case 3: Multi-Currency Invoice Handling
1. Manual entry of USD supplier invoice
2. System calculates HUF equivalent using current exchange rate
3. Create transfer batch with HUF amount for bank processing
4. Link transfer to original USD invoice payment record
5. Power BI reports show both USD original and HUF processed amounts

### Use Case 4: Bank Statement Reconciliation
1. Import bank CSV statement file
2. System automatically matches outgoing transfers to transfer batches
3. System matches incoming payments to outbound invoices
4. Unmatched transactions create new expense entries or revenue records
5. Manual review queue shows low-confidence matches for user confirmation
6. Complete financial picture available in Power BI dashboard

This comprehensive plan transforms your transfer XML generator into a complete financial management system while preserving all existing functionality and enabling gradual feature adoption based on company-specific needs.