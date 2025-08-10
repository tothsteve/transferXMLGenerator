-- SQL Commands to Add Table and Column Comments
-- Transfer XML Generator - Hungarian Banking System Database
-- Execute these commands against your SQL Server database

-- =============================================
-- TABLE COMMENTS
-- =============================================

-- BankAccount table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Stores originator bank accounts for transfers. Contains company/organization accounts that will be debited during XML generation.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount';

-- Beneficiary table  
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Stores beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities that receive payments.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary';

-- TransferTemplate table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Defines reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.',
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
    @value = N'Individual transfer records representing single bank payments. These are processed into XML batches for bank import.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transfer';

-- TransferBatch table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Groups transfers into batches for XML generation. Each batch represents one XML file sent to the bank.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch';

-- TransferBatch_transfers junction table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Many-to-many junction table linking transfer batches to individual transfers.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers';

-- =============================================
-- COLUMN COMMENTS - BankAccount
-- =============================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for bank account record', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Display name for the bank account (e.g., "Main Business Account", "Payroll Account")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Hungarian bank account number in standard format (with dashes, e.g., "1210001119014874")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'account_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Flags the default account for new transfers. Only one account should be default', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'is_default';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the account record was created', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the account record was last modified', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================
-- COLUMN COMMENTS - Beneficiary
-- =============================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for beneficiary record', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Full legal name of the beneficiary (person or organization)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Beneficiary''s bank account number in Hungarian format', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'account_number';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Name of the beneficiary''s bank (optional, for reference)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'bank_name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Marks frequently used beneficiaries for quick access', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'is_frequent';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag - inactive beneficiaries are hidden from selection', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Additional notes about the beneficiary (payment terms, contact info, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'notes';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the beneficiary was added to the system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the beneficiary record was last modified', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================
-- COLUMN COMMENTS - TransferTemplate
-- =============================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for transfer template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Descriptive name for the template (e.g., "Monthly Payroll", "Q1 VAT Payments")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Detailed description of when and how to use this template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'description';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag - inactive templates are hidden from selection', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the template was created', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the template was last modified', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================
-- COLUMN COMMENTS - TemplateBeneficiary
-- =============================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for template-beneficiary relationship', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the transfer template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'template_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'beneficiary_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Default payment amount for this beneficiary in this template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Default remittance information/memo for payments to this beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_remittance';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Display order of beneficiaries within the template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'order';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Whether this beneficiary is active in the template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'is_active';

-- =============================================
-- COLUMN COMMENTS - Transfer
-- =============================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for individual transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the bank account that will be debited', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'originator_account_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the payment recipient', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'beneficiary_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Transfer amount in the specified currency', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'ISO currency code (HUF, EUR, USD)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'currency';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Requested date for the bank to process the transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'execution_date';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Payment reference/memo that appears on bank statements', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'remittance_info';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to template if this transfer was created from a template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'template_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Marks transfers that have been included in generated XML files', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'is_processed';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Internal notes about this specific transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'notes';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the transfer was created', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the transfer was last modified', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================
-- COLUMN COMMENTS - TransferBatch
-- =============================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for transfer batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'name';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Detailed description of the batch contents and purpose', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'description';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Sum of all transfer amounts in this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'total_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the batch was created', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when the XML file was generated for this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'xml_generated_at';

-- =============================================
-- COLUMN COMMENTS - TransferBatch_transfers junction table
-- =============================================

EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for batch-transfer relationship', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the transfer batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'transferbatch_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Reference to the individual transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'transfer_id';

-- =============================================
-- VERIFICATION QUERIES
-- =============================================

-- Query to verify table comments were added
/*
SELECT 
    t.name AS table_name,
    ep.value AS table_comment
FROM sys.tables t
LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id 
    AND ep.minor_id = 0 
    AND ep.name = 'MS_Description'
WHERE t.name LIKE 'bank_transfers_%'
ORDER BY t.name;
*/

-- Query to verify column comments were added  
/*
SELECT 
    t.name AS table_name,
    c.name AS column_name,
    ep.value AS column_comment
FROM sys.tables t
INNER JOIN sys.columns c ON c.object_id = t.object_id
LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id 
    AND ep.minor_id = c.column_id 
    AND ep.name = 'MS_Description'
WHERE t.name LIKE 'bank_transfers_%'
ORDER BY t.name, c.column_id;
*/