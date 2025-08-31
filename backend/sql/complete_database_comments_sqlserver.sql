-- =============================================================================
-- COMPLETE SQL SERVER DATABASE COMMENTS SCRIPT
-- Transfer XML Generator - Enhanced Invoice Management System with Feature Flags
-- =============================================================================
-- This script adds comprehensive table and column comments for documentation
-- Run after database migrations to add descriptive metadata to SQL Server
-- Compatible with SQL Server development environment (localhost:1435)
-- Uses helper procedure to handle existing comments gracefully
-- =============================================================================

USE administration;
GO

-- Create a procedure to safely add or update extended properties
IF OBJECT_ID('tempdb..#SafeAddProperty') IS NOT NULL DROP PROCEDURE #SafeAddProperty;
GO

CREATE PROCEDURE #SafeAddProperty
    @name NVARCHAR(128),
    @value NVARCHAR(3900),
    @level0type NVARCHAR(128) = NULL,
    @level0name NVARCHAR(128) = NULL,
    @level1type NVARCHAR(128) = NULL,
    @level1name NVARCHAR(128) = NULL,
    @level2type NVARCHAR(128) = NULL,
    @level2name NVARCHAR(128) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        EXEC sys.sp_addextendedproperty 
            @name = @name, 
            @value = @value,
            @level0type = @level0type, @level0name = @level0name,
            @level1type = @level1type, @level1name = @level1name,
            @level2type = @level2type, @level2name = @level2name;
    END TRY
    BEGIN CATCH
        -- If property exists, update it
        IF ERROR_NUMBER() = 15233
        BEGIN
            EXEC sys.sp_updateextendedproperty 
                @name = @name, 
                @value = @value,
                @level0type = @level0type, @level0name = @level0name,
                @level1type = @level1type, @level1name = @level1name,
                @level2type = @level2type, @level2name = @level2name;
        END
        ELSE
        BEGIN
            THROW;
        END
    END CATCH
END
GO

-- =============================================================================
-- CORE BUSINESS TABLES
-- =============================================================================

-- Company Management
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Legal entities using the system. Each company has isolated data and feature access with multi-tenant architecture.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique company identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Legal company name as registered with authorities', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Hungarian tax identification number (adószám) - unique per company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'tax_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Full registered company address including postal code', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'address';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary contact phone number for company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'phone';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary contact email address for company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'email';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this company is currently active in the system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Company registration timestamp in system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp for company data', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_company', @level2type = N'COLUMN', @level2name = 'updated_at';

-- User-Company Relationships with Role-Based Access Control
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Links users to companies with role-based permissions. Supports multi-company user access with different roles per company.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique membership identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to Django auth_user table', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'user_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company - which company this user belongs to', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'User role: ADMIN, FINANCIAL, ACCOUNTANT, USER (determines feature access permissions)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'role';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this user membership is currently active (0=inactive, 1=active)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'JSON array of additional feature codes this user can access beyond their role permissions', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'custom_permissions';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'JSON array of feature codes this user is explicitly denied access to (overrides role permissions)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'permission_restrictions';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Timestamp when user was added to this company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyuser', @level2type = N'COLUMN', @level2name = 'joined_at';

-- User Profile Extension
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Extended user profile information beyond Django auth_user. Stores preferences and company context.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique profile identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to Django auth_user table', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'user_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'User phone number for contact purposes', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'phone';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Preferred language for UI (hu, en)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'preferred_language';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'User timezone for date/time display', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'timezone';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last company context the user was working in', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'last_active_company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Profile creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last profile modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_userprofile', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- FEATURE FLAG SYSTEM
-- =============================================================================

-- Feature Templates (Global Feature Definitions)
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Template definitions for available features that can be enabled per company. Defines the catalog of features available across the system.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique template identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Unique feature identifier (e.g. EXPORT_XML_SEPA, NAV_SYNC, BENEFICIARY_MANAGEMENT)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'feature_code';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Human-readable name displayed in admin interface and user-facing components', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'display_name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Detailed description of what this feature does and its business value', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'description';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Feature category for grouping (EXPORT, SYNC, TRACKING, REPORTING, INTEGRATION, GENERAL)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'category';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this feature should be automatically enabled for new companies (0=no, 1=yes)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'default_enabled';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'System critical features cannot be disabled as they are essential for core functionality', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'is_system_critical';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'JSON schema for validating feature-specific configuration parameters', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'config_schema';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Timestamp when this feature template was created', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp for template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_featuretemplate', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Company Feature Flags (Per-Company Feature Enablement)
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Company-specific feature flags controlling which functionality is available per company. Links companies to enabled features.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique feature enablement identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Reference to the company this feature enablement applies to', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Reference to the feature template defining what feature this is', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'feature_template_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this feature is currently enabled for the company (0=disabled, 1=enabled)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'is_enabled';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Company-specific JSON configuration data for this feature (optional parameters, settings, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'config_data';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Timestamp when this feature was first enabled for the company', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'enabled_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Reference to the user who enabled this feature (for audit trail)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'enabled_by_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Feature enablement creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_companyfeature', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- FINANCIAL DATA TABLES
-- =============================================================================

-- Bank Account Management
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Bank accounts owned by companies for originating transfers. Stores account details and default account settings.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique account identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company that owns this account', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Descriptive name for this bank account', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Bank account number or IBAN for transfers', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'account_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Name of the bank holding this account', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'bank_name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this is the default account for new transfers (only one per company)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'is_default';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Account creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_bankaccount', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Beneficiary Management
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Recipients of bank transfers. Contains account details, contact information, and transfer preferences per company.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique beneficiary identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company that owns this beneficiary record', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Full legal name of the beneficiary (person or organization)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Bank account number for receiving transfers', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'account_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Additional description or notes about this beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'description';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this beneficiary is marked as frequently used for quick access', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'is_frequent';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this beneficiary is currently active and available for transfers', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Default remittance information for transfers to this beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'remittance_information';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Beneficiary creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_beneficiary', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Transfer Templates for Recurring Payments
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Reusable templates for recurring transfer patterns like monthly payroll or vendor payments. Contains default beneficiaries and amounts.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique template identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company that owns this template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Descriptive name for this template (e.g. "Monthly Payroll", "Vendor Payments")', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Detailed description of what this template is used for', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'description';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this template is currently active and available for use', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Template creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfertemplate', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Template Beneficiary Associations
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Links templates to beneficiaries with default amounts and payment details. Defines the standard recipients for each template.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique template-beneficiary link identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to the transfer template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'template_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to the beneficiary included in this template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'beneficiary_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Default amount for transfers to this beneficiary when using template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Default remittance information/memo for transfers to this beneficiary', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_remittance';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Default execution date for transfers (NULL for current date)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'default_execution_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Display order for beneficiaries within the template', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'order';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this template beneficiary is active', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_templatebeneficiary', @level2type = N'COLUMN', @level2name = 'is_active';

-- Individual Transfer Records
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Individual bank transfer transactions. Each record represents one payment from company account to beneficiary.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique transfer identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to transfer recipient', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'beneficiary_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to originating bank account', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'originator_account_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to template used to create this transfer (if applicable)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'template_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Transfer amount in specified currency', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Currency code (HUF, EUR, USD)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'currency';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Requested execution date for the transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'execution_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Payment description/memo/reference information', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'remittance_info';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether transfer has been processed and included in XML export', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'is_processed';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Additional notes or comments about this transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'notes';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Display order for transfers within a batch or list', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'order';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Transfer creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transfer', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Transfer Batches for XML Generation
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Groups of transfers processed together for XML/CSV export. Created automatically when generating bank files.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique batch identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company that created this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Descriptive name for this batch (auto-generated or user-provided)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Additional description or notes about this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'description';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Export format used (XML_SEPA, CSV_KH, CSV_CUSTOM)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'batch_format';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Total amount of all transfers in this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'total_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Date when this batch should be processed by the bank', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'bank_usage_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this batch has been used/imported by the bank system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'used_in_bank';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Display order for batches within the system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'order';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Batch creation and processing timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'updated_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Timestamp when XML/CSV was generated for this batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch', @level2type = N'COLUMN', @level2name = 'xml_generated_at';

-- Transfer Batch Many-to-Many Relationship
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Many-to-many relationship table linking transfer batches to individual transfers. Allows transfers to be included in multiple batches.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key for the relationship', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to the transfer batch', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'transferbatch_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to the individual transfer', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_transferbatch_transfers', @level2type = N'COLUMN', @level2name = 'transfer_id';

-- =============================================================================
-- NAV INTEGRATION SYSTEM (Hungarian Tax Authority)
-- =============================================================================

-- NAV Configuration per Company
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'NAV (Hungarian Tax Authority) API configuration settings per company. Stores credentials and sync preferences for tax reporting.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique configuration identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company this NAV config belongs to', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Company tax number for NAV authentication', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'tax_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Technical user login name for NAV API', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'technical_user_login';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Technical user password for NAV API (encrypted)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'technical_user_password';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Company-specific encryption key for NAV data signing', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'company_encryption_key';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Exchange key for NAV API communication', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'exchange_key';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Signing key for NAV API requests', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'signing_key';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'NAV API environment (TEST, PRODUCTION)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'api_environment';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether this NAV configuration is currently active', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'is_active';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Whether automatic NAV synchronization is enabled', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'sync_enabled';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Configuration creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_navconfiguration', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Invoice Records for NAV Integration (Comprehensive Schema)
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Hungarian NAV invoice records with complete 40+ field schema for tax compliance. Stores both incoming and outgoing invoices for comprehensive tax reporting.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique invoice identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company that owns this invoice', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'NAV invoice number from tax authority system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_invoice_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice direction: OUTBOUND (sent) or INBOUND (received)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_direction';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Supplier/vendor company name', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'supplier_name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Supplier tax number (Hungarian adószám)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'supplier_tax_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Supplier bank account number for payments', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'supplier_bank_account_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Customer/buyer company name', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'customer_name';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Customer tax number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'customer_tax_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Customer bank account number', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'customer_bank_account_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Date when the invoice was issued by supplier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'issue_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Performance/delivery date for goods or services', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'fulfillment_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Due date for invoice payment', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'payment_due_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Date when payment was actually made', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'payment_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Payment method used (TRANSFER, CASH, CARD, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'payment_method';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice currency code (HUF, EUR, USD)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'currency_code';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Net amount in original currency (before VAT)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_net_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'VAT amount in original currency', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_vat_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Gross amount in original currency (including VAT)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_gross_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Net amount converted to HUF for tax reporting', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_net_amount_huf';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'VAT amount converted to HUF for tax reporting', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_vat_amount_huf';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Gross amount converted to HUF for tax reporting', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_gross_amount_huf';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice category for NAV classification', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_category';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice appearance type (PAPER, ELECTRONIC, EDI, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_appearance';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice operation type (CREATE, MODIFY, STORNO)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_operation';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Data completeness indicator for NAV compliance', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'completeness_indicator';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice index number within the system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'invoice_index';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Modification index for invoice revisions', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'modification_index';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Batch index for grouped invoice submissions', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'batch_index';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Original invoice number for modifications/storno', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'original_invoice_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Original request version for NAV API compatibility', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'original_request_version';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice completion date in NAV system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'completion_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Source of invoice data (MANUAL, NAV_API, IMPORT)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'source';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'NAV source system identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_source';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'NAV transaction ID from successful submission', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_transaction_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Date when invoice was created in NAV system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_creation_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modified date in NAV system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'last_modified_date';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Hash value of invoice for integrity verification', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_invoice_hash';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Complete XML representation of invoice for NAV', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'nav_invoice_xml';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Current sync status with NAV (PENDING, SYNCED, ERROR)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'sync_status';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Reference to original invoice if this is a storno', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'storno_of_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Invoice creation timestamp in local system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp in local system', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoice', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Invoice Line Items
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Individual line items within invoices. Each line represents a product or service with detailed pricing and tax information.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique line item identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to parent invoice', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'invoice_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Line number within the invoice', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_number';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Description of product or service on this line', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_description';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Quantity of items or units of service', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'quantity';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Unit of measure (pcs, kg, hours, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'unit_of_measure';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Price per unit before VAT', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'unit_price';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Total net amount for this line (quantity × unit_price)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_net_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'VAT rate applied to this line item (%)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'vat_rate';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'VAT amount for this line item', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_vat_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Total gross amount for this line (net + VAT)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'line_gross_amount';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Product code category (VTSZ, SZJ, etc.)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'product_code_category';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Product code value for tax classification', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'product_code_value';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Line item creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicelineitem', @level2type = N'COLUMN', @level2name = 'updated_at';

-- Invoice Sync Logs
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Audit log for NAV invoice synchronization operations. Tracks sync attempts, results, and error details for troubleshooting.', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Primary key - unique sync log identifier', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Foreign key to company that performed the sync', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'company_id';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Timestamp when sync operation started', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'sync_start_time';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Timestamp when sync operation completed', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'sync_end_time';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Direction of sync (INBOUND, OUTBOUND, BOTH)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'direction_synced';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Total number of invoices processed in this sync', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'invoices_processed';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Number of new invoices created', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'invoices_created';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Number of existing invoices updated', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'invoices_updated';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Number of errors encountered during sync', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'errors_count';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last error message encountered (if any)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'last_error_message';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Overall sync status (SUCCESS, PARTIAL, FAILED)', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'sync_status';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Log entry creation timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'created_at';
EXEC #SafeAddProperty @name = N'MS_Description', @value = N'Last modification timestamp', @level0type = N'SCHEMA', @level0name = 'dbo', @level1type = N'TABLE', @level1name = 'bank_transfers_invoicesynclog', @level2type = N'COLUMN', @level2name = 'updated_at';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

PRINT 'Database comments have been successfully added to all tables and columns.';
PRINT 'Run the following queries to verify comments were added:';
PRINT '';
PRINT '-- Table comments:';
PRINT 'SELECT t.name AS table_name, ep.value AS table_comment FROM sys.tables t LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = ''MS_Description'' WHERE t.name LIKE ''bank_transfers_%'' ORDER BY t.name;';
PRINT '';
PRINT '-- Column comments:';
PRINT 'SELECT t.name AS table_name, c.name AS column_name, ep.value AS column_comment FROM sys.tables t INNER JOIN sys.columns c ON c.object_id = t.object_id LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = c.column_id AND ep.name = ''MS_Description'' WHERE t.name LIKE ''bank_transfers_%'' ORDER BY t.name, c.column_id;';

GO