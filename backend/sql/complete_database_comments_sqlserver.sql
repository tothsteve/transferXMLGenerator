-- COMPLETE SQL Server Database Comments Script
-- Transfer XML Generator - Hungarian Banking System
-- Adds table and column comments for ALL current models
-- Execute against SQL Server 'administration' database

USE administration;
GO

-- =============================================================================
-- REMOVE EXISTING COMMENTS (Clean slate for updates)
-- =============================================================================

-- Remove all existing MS_Description extended properties for bank_transfers tables
DECLARE @sql NVARCHAR(MAX) = '';

SELECT @sql = @sql + 'EXEC sys.sp_dropextendedproperty @name = N''MS_Description'', @level0type = N''SCHEMA'', @level0name = ''dbo'', @level1type = N''TABLE'', @level1name = ''' + TABLE_NAME + ''';' + CHAR(13)
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'bank_transfers_%';

SELECT @sql = @sql + 'EXEC sys.sp_dropextendedproperty @name = N''MS_Description'', @level0type = N''SCHEMA'', @level0name = ''dbo'', @level1type = N''TABLE'', @level1name = ''' + c.TABLE_NAME + ''', @level2type = N''COLUMN'', @level2name = ''' + c.COLUMN_NAME + ''';' + CHAR(13)
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN INFORMATION_SCHEMA.TABLES t ON c.TABLE_NAME = t.TABLE_NAME
WHERE t.TABLE_NAME LIKE 'bank_transfers_%';

-- Execute cleanup (comment out if you want to preserve existing comments)
-- EXEC sp_executesql @sql;

-- =============================================================================
-- TABLE COMMENTS - Multi-Company Architecture
-- =============================================================================

-- Company table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Company entities for multi-tenant architecture. Each company has complete data isolation.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_company';

-- CompanyUser table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'User-company relationships with role-based access control. Enables multi-company membership.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser';

-- UserProfile table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Extended user profile information with company preferences and localization settings.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile';

-- =============================================================================
-- TABLE COMMENTS - Core Transfer System
-- =============================================================================

-- BankAccount table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Company-scoped originator bank accounts for transfers. Contains accounts that will be debited during XML/CSV export generation.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount';

-- Beneficiary table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Company-scoped beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary';

-- TransferTemplate table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Company-scoped reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate';

-- TemplateBeneficiary table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Junction table linking templates to beneficiaries with default payment amounts and remittance information.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary';

-- Transfer table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Individual transfer records representing single bank payments. These are processed into XML/CSV batches for bank import.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transfer';

-- TransferBatch table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Groups transfers into batches for XML/CSV export generation. Each batch represents one file (XML or CSV) sent to the bank.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch';

-- TransferBatch_transfers junction table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Many-to-many junction table linking transfer batches to individual transfers.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers';

-- =============================================================================
-- TABLE COMMENTS - NAV Integration System
-- =============================================================================

-- NAVConfiguration table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'NAV (Hungarian Tax Authority) API configuration for invoice synchronization. Company-specific credentials and settings.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration';

-- Invoice table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Invoice records synchronized from NAV (Hungarian Tax Authority) system with complete XML storage.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_invoice';

-- InvoiceLineItem table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Line items extracted from NAV invoice XML data. Represents individual products/services on invoices.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem';

-- InvoiceSyncLog table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Audit log for NAV invoice synchronization operations with error tracking and performance metrics.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog';

-- =============================================================================
-- COLUMN COMMENTS - Company (Multi-tenant)
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company legal name', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Hungarian tax identification number (adószám)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'tax_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company registered address', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'address';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Primary contact phone number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'phone';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Primary contact email address', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'email';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag for company deactivation', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company registration timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - CompanyUser (User-Company Relationships)
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for user-company relationship', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to Django User (auth_user.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'user_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to Company (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'User role in company: ADMIN or USER', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'role';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Active membership flag', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Membership creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'joined_at';

-- =============================================================================
-- COLUMN COMMENTS - UserProfile (Extended User Info)
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for user profile', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'One-to-one reference to Django User (auth_user.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'user_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'User phone number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'phone';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'UI language preference (default: hu)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'preferred_language';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'User timezone setting (default: Europe/Budapest)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'timezone';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last company context used by user', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'last_active_company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Profile creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - BankAccount
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for bank account record', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this account (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Display name for the account (e.g., "Main Business Account", "Payroll Account")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Hungarian bank account number in formatted form (e.g., "1210001119014874" or "12100011-19014874")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'account_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Name of the bank holding this account', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'bank_name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Flags the default account for new transfers within the company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'is_default';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Account registration timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - Beneficiary
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for beneficiary record', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this beneficiary (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Full legal name of the beneficiary (person or organization)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Beneficiary''s bank account number in Hungarian format (validated and formatted)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'account_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Additional information about the beneficiary (bank name, organization details, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'description';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Marks frequently used beneficiaries for quick access in UI', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'is_frequent';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag - inactive beneficiaries are hidden from selection', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Default payment references, invoice numbers, or transaction-specific information', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'remittance_information';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Beneficiary registration timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - TransferTemplate
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for transfer template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this template (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Descriptive name for the template (e.g., "Monthly Payroll", "Q1 VAT Payments")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Detailed description of when and how to use this template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'description';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag - inactive templates are hidden from selection', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Template creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - TemplateBeneficiary
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for template-beneficiary relationship', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the transfer template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'template_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'beneficiary_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Default payment amount for this beneficiary in this template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Default remittance information/memo for payments to this beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_remittance';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Default execution date for this beneficiary''s payments', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_execution_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Display order of beneficiaries within the template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'order';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Whether this beneficiary is active in the template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'is_active';

-- =============================================================================
-- COLUMN COMMENTS - Transfer
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for individual transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the bank account that will be debited', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'originator_account_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the payment recipient', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'beneficiary_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Transfer amount in the specified currency', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'ISO currency code (HUF, EUR, USD)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'currency';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Requested date for the bank to process the transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'execution_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Payment reference/memo that appears on bank statements', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'remittance_info';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to template if this transfer was created from a template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'template_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Transfer order within batch for XML/CSV export generation', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'order';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Marks transfers that have been included in generated XML/CSV files', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'is_processed';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Internal notes about this specific transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'notes';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Transfer creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - TransferBatch
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for transfer batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this batch (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Detailed description of the batch contents and purpose', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'description';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Sum of all transfer amounts in this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'total_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Flag indicating whether export file (XML/CSV) was uploaded to internet banking', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'used_in_bank';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the export file was uploaded to bank system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'bank_usage_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Display order for batch listing and downloads', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'order';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the export file was generated for this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'xml_generated_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Export file format: XML (SEPA XML) or KH_CSV (KH Bank CSV)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'batch_format';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Batch creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - TransferBatch_transfers junction
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for batch-transfer relationship', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the transfer batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'transferbatch_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the individual transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'transfer_id';

-- =============================================================================
-- COLUMN COMMENTS - NAVConfiguration
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for NAV configuration', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company reference for multi-tenant isolation (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Hungarian tax number for NAV authentication', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'tax_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV API technical user login name', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'technical_user_login';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV API password (encrypted with Fernet)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'technical_user_password';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV API signing key (encrypted with Fernet)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'signing_key';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV API exchange key (encrypted with Fernet)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'exchange_key';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company-specific encryption key (auto-generated, encrypted)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'company_encryption_key';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'API environment: test or production', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'api_environment';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Whether this configuration is active', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Whether automatic synchronization is enabled', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'sync_enabled';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp of last successful synchronization', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'last_sync_timestamp';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'How often to run automatic sync (hours)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'sync_frequency_hours';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Configuration creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - Invoice (NAV Integration)
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for invoice record', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this invoice (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV invoice number (e.g., "A/A28700200/1180/00013")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_invoice_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice direction: INBOUND or OUTBOUND', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_direction';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Name of invoice supplier/issuer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'supplier_name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Supplier tax identification number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'supplier_tax_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Name of invoice customer/recipient', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'customer_name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Customer tax identification number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'customer_tax_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice issue date', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'issue_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Service/product fulfillment date', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'fulfillment_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Payment due date', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'payment_due_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'ISO currency code (HUF, EUR, USD)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'currency_code';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Net amount without VAT', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_net_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'VAT amount', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_vat_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Total gross amount (net + VAT)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_gross_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV API version used for original request', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'original_request_version';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV processing completion timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'completion_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Data source indicator (NAV_SYNC, MANUAL, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'source';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV system transaction identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_transaction_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification date in NAV system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'last_modified_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice operation type (CREATE, STORNO, MODIFY)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_operation';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice category (NORMAL, SIMPLIFIED)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_category';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Payment method (TRANSFER, CASH, CARD)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'payment_method';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Actual payment date', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'payment_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice format (PAPER, ELECTRONIC)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_appearance';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Supplier bank account number (extracted from XML)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'supplier_bank_account_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Customer bank account number (extracted from XML)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'customer_bank_account_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'NAV data source indicator (OSZ, XML)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_source';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Data completeness indicator from NAV', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'completeness_indicator';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Modification sequence number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'modification_index';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Original invoice number (for STORNO invoices)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'original_invoice_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to original invoice that this STORNO cancels', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'storno_of_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice sequence number in NAV system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_index';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Batch index number in NAV system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'batch_index';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice creation timestamp in NAV system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_creation_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Net amount converted to HUF (for foreign currency invoices)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_net_amount_huf';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'VAT amount converted to HUF (for foreign currency invoices)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_vat_amount_huf';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Gross amount converted to HUF (for foreign currency invoices)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_gross_amount_huf';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Complete NAV invoice XML data (base64 decoded)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_invoice_xml';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Hash/checksum of invoice XML for integrity verification', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_invoice_hash';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Data synchronization status (SUCCESS, PARTIAL, FAILED)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'sync_status';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Local record creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last local modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - InvoiceLineItem
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for invoice line item', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to parent invoice (bank_transfers_invoice.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'invoice_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Line item sequence number (1, 2, 3...)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Description of product/service', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_description';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Quantity of product/service', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'quantity';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unit of measurement (e.g., PIECE, LITER, HOUR)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'unit_of_measure';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Price per unit before VAT', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'unit_price';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Line total net amount (quantity × unit_price)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_net_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'VAT rate as decimal (e.g., 0.27 for 27%)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'vat_rate';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'VAT amount for this line', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_vat_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Total gross amount for this line', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_gross_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Product code classification category', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'product_code_category';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Product code value/identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'product_code_value';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Line item extraction timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - InvoiceSyncLog
-- =============================================================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for sync log entry', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company for which sync was performed (bank_transfers_company.id)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Sync operation start timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'sync_start_time';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Sync operation completion timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'sync_end_time';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Invoice direction synced (INBOUND, OUTBOUND, BOTH)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'direction_synced';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Total number of invoices processed', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'invoices_processed';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Number of new invoices created', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'invoices_created';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Number of existing invoices updated', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'invoices_updated';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Number of errors encountered', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'errors_count';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Most recent error message encountered', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'last_error_message';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Overall sync status (RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'sync_status';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Sync log creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

PRINT 'Database comments have been added successfully.';
PRINT '';
PRINT 'Run these queries to verify the comments were added:';
PRINT '';
PRINT '-- Verify table comments:';
PRINT 'SELECT t.name AS table_name, ep.value AS table_comment';
PRINT 'FROM sys.tables t';
PRINT 'LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = ''MS_Description''';
PRINT 'WHERE t.name LIKE ''bank_transfers_%''';
PRINT 'ORDER BY t.name;';
PRINT '';
PRINT '-- Verify column comments:';
PRINT 'SELECT t.name AS table_name, c.name AS column_name, ep.value AS column_comment';
PRINT 'FROM sys.tables t';
PRINT 'INNER JOIN sys.columns c ON c.object_id = t.object_id';
PRINT 'LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = c.column_id AND ep.name = ''MS_Description''';
PRINT 'WHERE t.name LIKE ''bank_transfers_%''';
PRINT 'ORDER BY t.name, c.column_id;';