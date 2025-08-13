-- Comprehensive Database Schema Query
-- Gets tables, columns, foreign keys, and comments for SQL Server database

USE administration;
GO

-- Query to get complete database schema information
WITH TableInfo AS (
    SELECT 
        t.TABLE_SCHEMA,
        t.TABLE_NAME,
        c.COLUMN_NAME,
        c.ORDINAL_POSITION,
        c.DATA_TYPE,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.NUMERIC_PRECISION,
        c.NUMERIC_SCALE,
        c.IS_NULLABLE,
        c.COLUMN_DEFAULT,
        CASE 
            WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES'
            ELSE 'NO'
        END AS IS_PRIMARY_KEY,
        CASE 
            WHEN c.COLUMN_NAME LIKE '%_id' AND c.COLUMN_NAME != 'id' THEN 'LIKELY_FK'
            WHEN fk.COLUMN_NAME IS NOT NULL THEN 'YES'
            ELSE 'NO'
        END AS IS_FOREIGN_KEY,
        fk.REFERENCED_TABLE_SCHEMA,
        fk.REFERENCED_TABLE_NAME,
        fk.REFERENCED_COLUMN_NAME,
        fk.CONSTRAINT_NAME AS FK_CONSTRAINT_NAME
    FROM INFORMATION_SCHEMA.TABLES t
    JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
    LEFT JOIN (
        -- Primary Key Information
        SELECT 
            tc.TABLE_SCHEMA,
            tc.TABLE_NAME,
            kcu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
    ) pk ON t.TABLE_SCHEMA = pk.TABLE_SCHEMA AND t.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
    LEFT JOIN (
        -- Foreign Key Information
        SELECT 
            kcu.TABLE_SCHEMA,
            kcu.TABLE_NAME,
            kcu.COLUMN_NAME,
            kcu.REFERENCED_TABLE_SCHEMA,
            kcu.REFERENCED_TABLE_NAME,
            kcu.REFERENCED_COLUMN_NAME,
            kcu.CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
    ) fk ON t.TABLE_SCHEMA = fk.TABLE_SCHEMA AND t.TABLE_NAME = fk.TABLE_NAME AND c.COLUMN_NAME = fk.COLUMN_NAME
    WHERE t.TABLE_TYPE = 'BASE TABLE'
    AND t.TABLE_NAME LIKE 'bank_transfers_%'
),
Comments AS (
    -- Extended Properties (Comments)
    SELECT 
        s.name AS schema_name,
        o.name AS table_name,
        c.name AS column_name,
        ep.value AS comment
    FROM sys.extended_properties ep
    JOIN sys.objects o ON ep.major_id = o.object_id
    JOIN sys.schemas s ON o.schema_id = s.schema_id
    LEFT JOIN sys.columns c ON ep.major_id = c.object_id AND ep.minor_id = c.column_id
    WHERE ep.name = 'MS_Description'
    AND o.type = 'U'  -- User tables only
    AND o.name LIKE 'bank_transfers_%'
)

SELECT 
    ti.TABLE_SCHEMA AS [Schema],
    ti.TABLE_NAME AS [Table],
    ti.COLUMN_NAME AS [Column],
    ti.ORDINAL_POSITION AS [Position],
    ti.DATA_TYPE AS [Data Type],
    CASE 
        WHEN ti.DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar') 
        THEN CAST(ti.CHARACTER_MAXIMUM_LENGTH AS VARCHAR(10))
        WHEN ti.DATA_TYPE IN ('decimal', 'numeric') 
        THEN CAST(ti.NUMERIC_PRECISION AS VARCHAR(10)) + ',' + CAST(ti.NUMERIC_SCALE AS VARCHAR(10))
        ELSE ''
    END AS [Length/Precision],
    ti.IS_NULLABLE AS [Nullable],
    ti.COLUMN_DEFAULT AS [Default],
    ti.IS_PRIMARY_KEY AS [Primary Key],
    ti.IS_FOREIGN_KEY AS [Foreign Key],
    CASE 
        WHEN ti.REFERENCED_TABLE_NAME IS NOT NULL 
        THEN ti.REFERENCED_TABLE_SCHEMA + '.' + ti.REFERENCED_TABLE_NAME + '(' + ti.REFERENCED_COLUMN_NAME + ')'
        ELSE ''
    END AS [References],
    ti.FK_CONSTRAINT_NAME AS [FK Constraint],
    ISNULL(c.comment, '') AS [Comment]
FROM TableInfo ti
LEFT JOIN Comments c ON ti.TABLE_SCHEMA = c.schema_name 
    AND ti.TABLE_NAME = c.table_name 
    AND ti.COLUMN_NAME = c.column_name
ORDER BY ti.TABLE_NAME, ti.ORDINAL_POSITION;

-- Additional query for table-level comments
SELECT 
    s.name AS [Schema],
    o.name AS [Table],
    ep.value AS [Table Comment]
FROM sys.extended_properties ep
JOIN sys.objects o ON ep.major_id = o.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE ep.name = 'MS_Description'
AND ep.minor_id = 0  -- Table-level comments have minor_id = 0
AND o.type = 'U'
AND o.name LIKE 'bank_transfers_%'
ORDER BY o.name;

-- Foreign Key Relationships Summary
SELECT 
    fk.name AS [FK Constraint],
    OBJECT_SCHEMA_NAME(fk.parent_object_id) AS [From Schema],
    OBJECT_NAME(fk.parent_object_id) AS [From Table],
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS [From Column],
    OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS [To Schema], 
    OBJECT_NAME(fk.referenced_object_id) AS [To Table],
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS [To Column],
    fk.delete_referential_action_desc AS [On Delete],
    fk.update_referential_action_desc AS [On Update]
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE OBJECT_NAME(fk.parent_object_id) LIKE 'bank_transfers_%'
   OR OBJECT_NAME(fk.referenced_object_id) LIKE 'bank_transfers_%'
ORDER BY [From Table], [From Column];

-- Index Information
SELECT 
    OBJECT_SCHEMA_NAME(i.object_id) AS [Schema],
    OBJECT_NAME(i.object_id) AS [Table],
    i.name AS [Index Name],
    i.type_desc AS [Index Type],
    i.is_unique AS [Is Unique],
    i.is_primary_key AS [Is Primary Key],
    STRING_AGG(c.name + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END, ', ') AS [Columns]
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE OBJECT_NAME(i.object_id) LIKE 'bank_transfers_%'
AND i.type > 0  -- Exclude heaps
GROUP BY i.object_id, i.name, i.type_desc, i.is_unique, i.is_primary_key
ORDER BY [Table], [Index Name];