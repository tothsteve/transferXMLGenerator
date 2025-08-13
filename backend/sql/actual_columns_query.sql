-- Query to get actual column information from the database
USE administration;
GO

-- Get all columns for bank_transfers tables
SELECT 
    t.TABLE_NAME AS [Table],
    c.COLUMN_NAME AS [Column],
    c.DATA_TYPE AS [Data Type],
    CASE 
        WHEN c.DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar') 
        THEN CAST(c.CHARACTER_MAXIMUM_LENGTH AS VARCHAR(10))
        WHEN c.DATA_TYPE IN ('decimal', 'numeric') 
        THEN CAST(c.NUMERIC_PRECISION AS VARCHAR(10)) + ',' + CAST(c.NUMERIC_SCALE AS VARCHAR(10))
        ELSE ''
    END AS [Length],
    c.IS_NULLABLE AS [Nullable],
    c.COLUMN_DEFAULT AS [Default],
    c.ORDINAL_POSITION AS [Position]
FROM INFORMATION_SCHEMA.TABLES t
JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
WHERE t.TABLE_TYPE = 'BASE TABLE'
AND t.TABLE_NAME LIKE 'bank_transfers_%'
ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION;