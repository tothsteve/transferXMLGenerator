-- SQL Server Database Comments Update Script
-- Transfer XML Generator - Hungarian Banking System  
-- Updates MSSQL comments to match DATABASE_DOCUMENTATION.md (Single Source of Truth)
-- Execute this script on SQL Server (localhost:1435, database: administration)

USE administration;
GO

-- =============================================
-- ADD NEW TABLE COMMENTS FOR MULTI-COMPANY ARCHITECTURE
-- =============================================

-- Company table
IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_company'))
BEGIN
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Company entities for multi-tenant architecture. Each company has complete data isolation.',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_company';
    PRINT 'Added comment for bank_transfers_company table';
END
GO

-- CompanyUser table
IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_companyuser'))
BEGIN
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'User-company relationships with role-based access control. Enables multi-company membership.',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser';
    PRINT 'Added comment for bank_transfers_companyuser table';
END
GO

-- UserProfile table
IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_userprofile'))
BEGIN
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Extended user profile information with company preferences and localization settings.',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile';
    PRINT 'Added comment for bank_transfers_userprofile table';
END
GO

-- =============================================
-- UPDATE EXISTING TABLE COMMENTS
-- =============================================

-- Update BankAccount table comment to reflect multi-company
IF EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_bankaccount') AND minor_id = 0)
BEGIN
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount';
END

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Company-scoped originator bank accounts for transfers. Contains accounts that will be debited during XML generation.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount';
PRINT 'Updated comment for bank_transfers_bankaccount table';
GO

-- Update Beneficiary table comment to reflect multi-company
IF EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_beneficiary') AND minor_id = 0)
BEGIN
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary';
END

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Company-scoped beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary';
PRINT 'Updated comment for bank_transfers_beneficiary table';
GO

-- Update TransferTemplate table comment to reflect multi-company
IF EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_transfertemplate') AND minor_id = 0)
BEGIN
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate';
END

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Company-scoped reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate';
PRINT 'Updated comment for bank_transfers_transfertemplate table';
GO

-- Update TransferBatch table comment to reflect multi-company
IF EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_transferbatch') AND minor_id = 0)
BEGIN
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch';
END

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Groups transfers into batches for XML generation. Each batch represents one XML file sent to the bank.',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch';
PRINT 'Updated comment for bank_transfers_transferbatch table';
GO

-- =============================================
-- ADD NEW COLUMN COMMENTS FOR MULTI-COMPANY FIELDS
-- =============================================

-- Company table columns
IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_company') AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_company'), 'id', 'ColumnId'))
BEGIN
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'id';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company legal name', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'name';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Hungarian tax identification number (adószám)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'tax_id';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company registered address', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'address';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Primary contact phone number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'phone';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Primary contact email address', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'email';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Soft delete flag for company deactivation', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'is_active';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company registration timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'created_at';
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'updated_at';
    PRINT 'Added column comments for bank_transfers_company';
END
GO

-- Add company_id column comments to existing tables
IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_bankaccount') AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_bankaccount'), 'company_id', 'ColumnId'))
BEGIN
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this account', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'company_id';
    PRINT 'Added company_id comment for bank_transfers_bankaccount';
END
GO

IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_beneficiary') AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_beneficiary'), 'company_id', 'ColumnId'))
BEGIN
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'company_id';
    PRINT 'Added company_id comment for bank_transfers_beneficiary';
END
GO

IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_transfertemplate') AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_transfertemplate'), 'company_id', 'ColumnId'))
BEGIN
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'company_id';
    PRINT 'Added company_id comment for bank_transfers_transfertemplate';
END
GO

IF NOT EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_transferbatch') AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_transferbatch'), 'company_id', 'ColumnId'))
BEGIN
    EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Company owner of this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'company_id';
    PRINT 'Added company_id comment for bank_transfers_transferbatch';
END
GO

-- =============================================
-- UPDATE EXISTING COLUMN COMMENTS
-- =============================================

-- Update BankAccount.account_number comment to include Hungarian format validation
IF EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_bankaccount') AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_bankaccount'), 'account_number', 'ColumnId'))
BEGIN
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
        @level2type = N'COLUMN', @level2name = 'account_number';
END

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Hungarian bank account number in formatted form (e.g., "1210001119014874" or "12100011-19014874")',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount',
    @level2type = N'COLUMN', @level2name = 'account_number';
PRINT 'Updated account_number comment for bank_transfers_bankaccount';
GO

-- Update Beneficiary.account_number comment to include validation info
IF EXISTS (SELECT * FROM sys.extended_properties WHERE major_id = OBJECT_ID('bank_transfers_beneficiary') AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_beneficiary'), 'account_number', 'ColumnId'))
BEGIN
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
        @level2type = N'COLUMN', @level2name = 'account_number';
END

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Beneficiary''s bank account number in Hungarian format (validated and formatted)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'account_number';
PRINT 'Updated account_number comment for bank_transfers_beneficiary';
GO

-- =============================================
-- VERIFICATION QUERIES
-- =============================================

PRINT 'Verifying multi-company table comments:';
SELECT 
    t.name AS table_name,
    ep.value AS table_comment
FROM sys.tables t
LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id 
    AND ep.minor_id = 0 
    AND ep.name = 'MS_Description'
WHERE t.name IN ('bank_transfers_company', 'bank_transfers_companyuser', 'bank_transfers_userprofile')
ORDER BY t.name;

PRINT 'Verifying company_id column comments:';
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
    AND c.name = 'company_id'
ORDER BY t.name;

PRINT 'MSSQL comment updates completed successfully!';
GO