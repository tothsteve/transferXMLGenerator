-- PostgreSQL Database Comments Script
-- Transfer XML Generator - Hungarian Banking System
-- Generated from DATABASE_DOCUMENTATION.md (Single Source of Truth)
-- Execute this script on PostgreSQL database to add table and column comments

-- =============================================
-- TABLE COMMENTS
-- =============================================

-- Multi-Company Architecture Tables
COMMENT ON TABLE bank_transfers_company IS 'Company entities for multi-tenant architecture. Each company has complete data isolation.';
COMMENT ON TABLE bank_transfers_companyuser IS 'User-company relationships with role-based access control. Enables multi-company membership.';
COMMENT ON TABLE bank_transfers_userprofile IS 'Extended user profile information with company preferences and localization settings.';

-- Core Business Tables
COMMENT ON TABLE bank_transfers_bankaccount IS 'Company-scoped originator bank accounts for transfers. Contains accounts that will be debited during XML generation.';
COMMENT ON TABLE bank_transfers_beneficiary IS 'Company-scoped beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities.';
COMMENT ON TABLE bank_transfers_transfertemplate IS 'Company-scoped reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.';
COMMENT ON TABLE bank_transfers_templatebeneficiary IS 'Junction table linking templates to beneficiaries with default payment amounts and remittance information.';
COMMENT ON TABLE bank_transfers_transfer IS 'Individual transfer records representing single bank payments. These are processed into XML batches for bank import.';
COMMENT ON TABLE bank_transfers_transferbatch IS 'Groups transfers into batches for XML generation. Each batch represents one XML file sent to the bank.';
COMMENT ON TABLE bank_transfers_transferbatch_transfers IS 'Many-to-many junction table linking transfer batches to individual transfers.';

-- =============================================
-- COLUMN COMMENTS - Company
-- =============================================

COMMENT ON COLUMN bank_transfers_company.id IS 'Unique identifier for company';
COMMENT ON COLUMN bank_transfers_company.name IS 'Company legal name';
COMMENT ON COLUMN bank_transfers_company.tax_id IS 'Hungarian tax identification number (adószám)';
COMMENT ON COLUMN bank_transfers_company.address IS 'Company registered address';
COMMENT ON COLUMN bank_transfers_company.phone IS 'Primary contact phone number';
COMMENT ON COLUMN bank_transfers_company.email IS 'Primary contact email address';
COMMENT ON COLUMN bank_transfers_company.is_active IS 'Soft delete flag for company deactivation';
COMMENT ON COLUMN bank_transfers_company.created_at IS 'Company registration timestamp';
COMMENT ON COLUMN bank_transfers_company.updated_at IS 'Last modification timestamp';

-- =============================================
-- COLUMN COMMENTS - CompanyUser
-- =============================================

COMMENT ON COLUMN bank_transfers_companyuser.id IS 'Unique identifier for user-company relationship';
COMMENT ON COLUMN bank_transfers_companyuser.user_id IS 'Reference to Django User';
COMMENT ON COLUMN bank_transfers_companyuser.company_id IS 'Reference to Company';
COMMENT ON COLUMN bank_transfers_companyuser.role IS 'Role: ADMIN or USER';
COMMENT ON COLUMN bank_transfers_companyuser.is_active IS 'Active membership flag';
COMMENT ON COLUMN bank_transfers_companyuser.joined_at IS 'Membership creation timestamp';

-- =============================================
-- COLUMN COMMENTS - UserProfile
-- =============================================

COMMENT ON COLUMN bank_transfers_userprofile.id IS 'Unique identifier for user profile';
COMMENT ON COLUMN bank_transfers_userprofile.user_id IS 'One-to-one reference to Django User';
COMMENT ON COLUMN bank_transfers_userprofile.phone IS 'User phone number';
COMMENT ON COLUMN bank_transfers_userprofile.preferred_language IS 'UI language preference';
COMMENT ON COLUMN bank_transfers_userprofile.timezone IS 'User timezone setting';
COMMENT ON COLUMN bank_transfers_userprofile.last_active_company_id IS 'Last company context used';
COMMENT ON COLUMN bank_transfers_userprofile.created_at IS 'Profile creation timestamp';
COMMENT ON COLUMN bank_transfers_userprofile.updated_at IS 'Last modification timestamp';

-- =============================================
-- COLUMN COMMENTS - BankAccount
-- =============================================

COMMENT ON COLUMN bank_transfers_bankaccount.id IS 'Unique identifier for bank account record';
COMMENT ON COLUMN bank_transfers_bankaccount.company_id IS 'Company owner of this account';
COMMENT ON COLUMN bank_transfers_bankaccount.name IS 'Display name for the account (e.g., "Main Business Account", "Payroll Account")';
COMMENT ON COLUMN bank_transfers_bankaccount.account_number IS 'Hungarian bank account number in formatted form (e.g., "1210001119014874" or "12100011-19014874")';
COMMENT ON COLUMN bank_transfers_bankaccount.bank_name IS 'Name of the bank holding this account';
COMMENT ON COLUMN bank_transfers_bankaccount.is_default IS 'Flags the default account for new transfers within the company';
COMMENT ON COLUMN bank_transfers_bankaccount.created_at IS 'Account registration timestamp';
COMMENT ON COLUMN bank_transfers_bankaccount.updated_at IS 'Last modification timestamp';

-- =============================================
-- COLUMN COMMENTS - Beneficiary
-- =============================================

COMMENT ON COLUMN bank_transfers_beneficiary.id IS 'Unique identifier for beneficiary record';
COMMENT ON COLUMN bank_transfers_beneficiary.company_id IS 'Company owner of this beneficiary';
COMMENT ON COLUMN bank_transfers_beneficiary.name IS 'Full legal name of the beneficiary (person or organization)';
COMMENT ON COLUMN bank_transfers_beneficiary.account_number IS 'Beneficiary''s bank account number in Hungarian format (validated and formatted)';
COMMENT ON COLUMN bank_transfers_beneficiary.description IS 'Additional information about the beneficiary (bank name, organization details, etc.)';
COMMENT ON COLUMN bank_transfers_beneficiary.is_frequent IS 'Marks frequently used beneficiaries for quick access in UI';
COMMENT ON COLUMN bank_transfers_beneficiary.is_active IS 'Soft delete flag - inactive beneficiaries are hidden from selection';
COMMENT ON COLUMN bank_transfers_beneficiary.remittance_information IS 'Default payment references, invoice numbers, or transaction-specific information';
COMMENT ON COLUMN bank_transfers_beneficiary.created_at IS 'Beneficiary registration timestamp';
COMMENT ON COLUMN bank_transfers_beneficiary.updated_at IS 'Last modification timestamp';

-- =============================================
-- COLUMN COMMENTS - TransferTemplate
-- =============================================

COMMENT ON COLUMN bank_transfers_transfertemplate.id IS 'Unique identifier for transfer template';
COMMENT ON COLUMN bank_transfers_transfertemplate.company_id IS 'Company owner of this template';
COMMENT ON COLUMN bank_transfers_transfertemplate.name IS 'Descriptive name for the template (e.g., "Monthly Payroll", "Q1 VAT Payments")';
COMMENT ON COLUMN bank_transfers_transfertemplate.description IS 'Detailed description of when and how to use this template';
COMMENT ON COLUMN bank_transfers_transfertemplate.is_active IS 'Soft delete flag - inactive templates are hidden from selection';
COMMENT ON COLUMN bank_transfers_transfertemplate.created_at IS 'Template creation timestamp';
COMMENT ON COLUMN bank_transfers_transfertemplate.updated_at IS 'Last modification timestamp';

-- =============================================
-- COLUMN COMMENTS - TemplateBeneficiary
-- =============================================

COMMENT ON COLUMN bank_transfers_templatebeneficiary.id IS 'Unique identifier for template-beneficiary relationship';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.template_id IS 'Reference to the transfer template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.beneficiary_id IS 'Reference to the beneficiary';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_amount IS 'Default payment amount for this beneficiary in this template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_remittance IS 'Default remittance information/memo for payments to this beneficiary';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_execution_date IS 'Default execution date for this beneficiary''s payments';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.order IS 'Display order of beneficiaries within the template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.is_active IS 'Whether this beneficiary is active in the template';

-- =============================================
-- COLUMN COMMENTS - Transfer
-- =============================================

COMMENT ON COLUMN bank_transfers_transfer.id IS 'Unique identifier for individual transfer';
COMMENT ON COLUMN bank_transfers_transfer.originator_account_id IS 'Reference to the bank account that will be debited';
COMMENT ON COLUMN bank_transfers_transfer.beneficiary_id IS 'Reference to the payment recipient';
COMMENT ON COLUMN bank_transfers_transfer.amount IS 'Transfer amount in the specified currency';
COMMENT ON COLUMN bank_transfers_transfer.currency IS 'ISO currency code (HUF, EUR, USD)';
COMMENT ON COLUMN bank_transfers_transfer.execution_date IS 'Requested date for the bank to process the transfer';
COMMENT ON COLUMN bank_transfers_transfer.remittance_info IS 'Payment reference/memo that appears on bank statements';
COMMENT ON COLUMN bank_transfers_transfer.template_id IS 'Reference to template if this transfer was created from a template';
COMMENT ON COLUMN bank_transfers_transfer.order IS 'Transfer order within batch for XML generation';
COMMENT ON COLUMN bank_transfers_transfer.is_processed IS 'Marks transfers that have been included in generated XML files';
COMMENT ON COLUMN bank_transfers_transfer.notes IS 'Internal notes about this specific transfer';
COMMENT ON COLUMN bank_transfers_transfer.created_at IS 'Transfer creation timestamp';
COMMENT ON COLUMN bank_transfers_transfer.updated_at IS 'Last modification timestamp';

-- =============================================
-- COLUMN COMMENTS - TransferBatch
-- =============================================

COMMENT ON COLUMN bank_transfers_transferbatch.id IS 'Unique identifier for transfer batch';
COMMENT ON COLUMN bank_transfers_transferbatch.company_id IS 'Company owner of this batch';
COMMENT ON COLUMN bank_transfers_transferbatch.name IS 'User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3")';
COMMENT ON COLUMN bank_transfers_transferbatch.description IS 'Detailed description of the batch contents and purpose';
COMMENT ON COLUMN bank_transfers_transferbatch.total_amount IS 'Sum of all transfer amounts in this batch';
COMMENT ON COLUMN bank_transfers_transferbatch.used_in_bank IS 'Flag indicating whether XML file was uploaded to internet banking';
COMMENT ON COLUMN bank_transfers_transferbatch.bank_usage_date IS 'Timestamp when the XML was uploaded to bank system';
COMMENT ON COLUMN bank_transfers_transferbatch.order IS 'Display order for batch listing and downloads';
COMMENT ON COLUMN bank_transfers_transferbatch.created_at IS 'Batch creation timestamp';
COMMENT ON COLUMN bank_transfers_transferbatch.xml_generated_at IS 'Timestamp when the XML file was generated for this batch';

-- =============================================
-- COLUMN COMMENTS - TransferBatch_transfers
-- =============================================

COMMENT ON COLUMN bank_transfers_transferbatch_transfers.id IS 'Unique identifier for batch-transfer relationship';
COMMENT ON COLUMN bank_transfers_transferbatch_transfers.transferbatch_id IS 'Reference to the transfer batch';
COMMENT ON COLUMN bank_transfers_transferbatch_transfers.transfer_id IS 'Reference to the individual transfer';

-- =============================================
-- VERIFICATION QUERIES
-- =============================================

-- Query to verify table comments were added
/*
SELECT 
    schemaname,
    tablename,
    obj_description(c.oid) as table_comment
FROM pg_tables t
LEFT JOIN pg_class c ON c.relname = t.tablename
WHERE schemaname = 'public' 
    AND tablename LIKE 'bank_transfers_%'
ORDER BY tablename;
*/

-- Query to verify column comments were added  
/*
SELECT 
    t.table_name,
    c.column_name,
    col_description(pgc.oid, c.ordinal_position) as column_comment
FROM information_schema.columns c
LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
LEFT JOIN information_schema.tables t ON t.table_name = c.table_name
WHERE t.table_schema = 'public' 
    AND c.table_name LIKE 'bank_transfers_%'
ORDER BY c.table_name, c.ordinal_position;
*/

-- =============================================
-- NOTES
-- =============================================

-- This script adds PostgreSQL comments to match the schema documented in DATABASE_DOCUMENTATION.md
-- The DATABASE_DOCUMENTATION.md file is the single source of truth for all schema information
-- Run this script after Django migrations to ensure all tables have proper documentation
-- Comments help with database introspection, documentation generation, and developer onboarding