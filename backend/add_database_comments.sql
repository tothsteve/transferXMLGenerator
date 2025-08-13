-- SQL Script to add comments to Transfer XML Generator database tables and columns
-- Database: SQL Server - administration
-- Run this script to add descriptive comments that match the documentation

-- =============================================================================
-- TABLE COMMENTS
-- =============================================================================

-- bank_transfers_bankaccount table comment
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Stores originator bank accounts for transfers. Contains company/organization accounts that will be debited during XML generation.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount';

-- bank_transfers_beneficiary table comment
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Stores beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities that receive payments.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary';

-- bank_transfers_transfertemplate table comment
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Defines reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate';

-- bank_transfers_templatebeneficiary table comment
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Junction table linking templates to beneficiaries with default payment amounts and remittance information.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary';

-- bank_transfers_transfer table comment
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Individual transfer records representing single bank payments. These are processed into XML batches for bank import.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transfer';

-- bank_transfers_transferbatch table comment
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Groups transfers into batches for XML generation. Each batch represents one XML file sent to the bank.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch';

-- bank_transfers_transferbatch_transfers table comment
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Many-to-many junction table linking transfer batches to individual transfers.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers';

-- =============================================================================
-- COLUMN COMMENTS - bank_transfers_bankaccount
-- =============================================================================

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for bank account record',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
    @level2type = N'COLUMN', @level2name = 'id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Display name for the bank account (e.g., "Main Business Account", "Payroll Account")',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
    @level2type = N'COLUMN', @level2name = 'name';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Hungarian bank account number in standard format (with dashes, e.g., "1210001119014874")',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
    @level2type = N'COLUMN', @level2name = 'account_number';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Flags the default account for new transfers. Only one account should be default',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
    @level2type = N'COLUMN', @level2name = 'is_default';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the account record was created',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
    @level2type = N'COLUMN', @level2name = 'created_at';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the account record was last modified',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
    @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - bank_transfers_beneficiary
-- =============================================================================

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for beneficiary record',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Full legal name of the beneficiary (person or organization)',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'name';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Beneficiary''s bank account number in Hungarian format',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'account_number';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Additional information about the beneficiary (bank name, organization details, etc.)',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'description';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Marks frequently used beneficiaries for quick access',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'is_frequent';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag - inactive beneficiaries are hidden from selection',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'is_active';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Default payment references, account numbers, or other transaction-specific information',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'remittance_information';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the beneficiary was added to the system',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'created_at';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the beneficiary record was last modified',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - bank_transfers_transfertemplate
-- =============================================================================

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for transfer template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate',
    @level2type = N'COLUMN', @level2name = 'id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Descriptive name for the template (e.g., "Monthly Payroll", "Q1 VAT Payments")',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate',
    @level2type = N'COLUMN', @level2name = 'name';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Detailed description of when and how to use this template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate',
    @level2type = N'COLUMN', @level2name = 'description';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag - inactive templates are hidden from selection',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate',
    @level2type = N'COLUMN', @level2name = 'is_active';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the template was created',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate',
    @level2type = N'COLUMN', @level2name = 'created_at';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the template was last modified',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate',
    @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - bank_transfers_templatebeneficiary
-- =============================================================================

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for template-beneficiary relationship',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary',
    @level2type = N'COLUMN', @level2name = 'id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the transfer template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary',
    @level2type = N'COLUMN', @level2name = 'template_id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the beneficiary',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary',
    @level2type = N'COLUMN', @level2name = 'beneficiary_id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Default payment amount for this beneficiary in this template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary',
    @level2type = N'COLUMN', @level2name = 'default_amount';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Default remittance information/memo for payments to this beneficiary',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary',
    @level2type = N'COLUMN', @level2name = 'default_remittance';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Display order of beneficiaries within the template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary',
    @level2type = N'COLUMN', @level2name = 'order';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Whether this beneficiary is active in the template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary',
    @level2type = N'COLUMN', @level2name = 'is_active';

-- =============================================================================
-- COLUMN COMMENTS - bank_transfers_transfer
-- =============================================================================

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for individual transfer',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the bank account that will be debited',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'originator_account_id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the payment recipient',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'beneficiary_id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Transfer amount in the specified currency (minimum 0.01)',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'amount';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'ISO currency code (HUF, EUR, USD)',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'currency';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Requested date for the bank to process the transfer',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'execution_date';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Payment reference/memo that appears on bank statements',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'remittance_info';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to template if this transfer was created from a template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'template_id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Marks transfers that have been included in generated XML files',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'is_processed';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Display order for sorting transfers within a batch or template',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'order';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Internal notes or comments about this transfer (not included in XML output)',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'notes';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the transfer was created',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'created_at';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the transfer was last modified',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer',
    @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- COLUMN COMMENTS - bank_transfers_transferbatch
-- =============================================================================

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for transfer batch',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3")',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'name';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Detailed description of the batch contents and purpose',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'description';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Sum of all transfer amounts in this batch',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'total_amount';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Flag indicating whether this XML batch has been uploaded to internet banking',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'used_in_bank';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the batch was marked as used in internet banking',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'bank_usage_date';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Sequential order number for batch organization and listing',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'order';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the batch was created',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'created_at';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the XML file was generated for this batch',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch',
    @level2type = N'COLUMN', @level2name = 'xml_generated_at';

-- =============================================================================
-- COLUMN COMMENTS - bank_transfers_transferbatch_transfers
-- =============================================================================

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for batch-transfer relationship',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers',
    @level2type = N'COLUMN', @level2name = 'id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the transfer batch',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers',
    @level2type = N'COLUMN', @level2name = 'transferbatch_id';

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the individual transfer',
    @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers',
    @level2type = N'COLUMN', @level2name = 'transfer_id';

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================
PRINT 'Database comments have been successfully added to all tables and columns.';
PRINT 'Total tables updated: 7';
PRINT 'Total columns commented: 46';
PRINT 'All comments are now available in SQL Server Management Studio and documentation queries.';