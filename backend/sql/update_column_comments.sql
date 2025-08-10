-- SQL Script to update column comments for renamed columns
-- Execute this script on SQL Server database: 'administration' on localhost:1435
-- This updates comments for columns that were renamed from bank_name->description and notes->remittance_information

USE administration;
GO

-- Step 1: Update comment for description column (was bank_name)
IF EXISTS (SELECT * FROM sys.extended_properties 
           WHERE major_id = OBJECT_ID('bank_transfers_beneficiary') 
           AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_beneficiary'), 'description', 'ColumnId')
           AND name = 'MS_Description')
BEGIN
    -- Drop existing comment
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
        @level2type = N'COLUMN', @level2name = 'description';
    PRINT 'Removed old comment for description column';
END
GO

-- Add new comment for description column
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Description field for Beneficiary. Additional information about the beneficiary (bank name, organization details, etc.)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'description';
PRINT 'Added new comment for description column';
GO

-- Step 2: Update comment for remittance_information column (was notes)
IF EXISTS (SELECT * FROM sys.extended_properties 
           WHERE major_id = OBJECT_ID('bank_transfers_beneficiary') 
           AND minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_beneficiary'), 'remittance_information', 'ColumnId')
           AND name = 'MS_Description')
BEGIN
    -- Drop existing comment
    EXEC sys.sp_dropextendedproperty 
        @name = N'MS_Description',
        @level0type = N'SCHEMA', @level0name = 'dbo',
        @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
        @level2type = N'COLUMN', @level2name = 'remittance_information';
    PRINT 'Removed old comment for remittance_information column';
END
GO

-- Add new comment for remittance_information column
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Remittance information field for Beneficiary. Default payment references, invoice numbers, or other transaction-specific information',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary',
    @level2type = N'COLUMN', @level2name = 'remittance_information';
PRINT 'Added new comment for remittance_information column';
GO

-- Step 3: Verify the updated comments
PRINT 'Verifying updated column comments:';
SELECT 
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.IS_NULLABLE,
    c.CHARACTER_MAXIMUM_LENGTH,
    CAST(ep.value AS NVARCHAR(500)) AS COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS c
LEFT JOIN sys.extended_properties ep ON ep.major_id = OBJECT_ID('bank_transfers_beneficiary')
    AND ep.minor_id = COLUMNPROPERTY(OBJECT_ID('bank_transfers_beneficiary'), c.COLUMN_NAME, 'ColumnId')
    AND ep.name = 'MS_Description'
WHERE c.TABLE_NAME = 'bank_transfers_beneficiary'
    AND c.COLUMN_NAME IN ('description', 'remittance_information')
ORDER BY c.ORDINAL_POSITION;
GO

PRINT 'Column comment updates completed successfully!';
GO