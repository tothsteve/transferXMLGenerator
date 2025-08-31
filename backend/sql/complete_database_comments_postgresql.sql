-- =============================================================================
-- COMPLETE POSTGRESQL DATABASE COMMENTS SCRIPT
-- Transfer XML Generator - Enhanced Invoice Management System with Feature Flags
-- =============================================================================
-- This script adds comprehensive table and column comments for documentation
-- Run after database migrations to add descriptive metadata to PostgreSQL
-- Compatible with PostgreSQL production environment (Railway deployment)
-- Uses PostgreSQL COMMENT ON syntax for database documentation
-- =============================================================================

-- =============================================================================
-- CORE BUSINESS TABLES
-- =============================================================================

-- Company Management
COMMENT ON TABLE bank_transfers_company IS 'Legal entities using the system. Each company has isolated data and feature access with multi-tenant architecture.';
COMMENT ON COLUMN bank_transfers_company.id IS 'Primary key - unique company identifier';
COMMENT ON COLUMN bank_transfers_company.name IS 'Legal company name as registered with authorities';
COMMENT ON COLUMN bank_transfers_company.tax_id IS 'Hungarian tax identification number (adószám) - unique per company';
COMMENT ON COLUMN bank_transfers_company.is_active IS 'Whether this company is currently active in the system';
COMMENT ON COLUMN bank_transfers_company.created_at IS 'Company registration timestamp in system';
COMMENT ON COLUMN bank_transfers_company.updated_at IS 'Last modification timestamp for company data';

-- User-Company Relationships with Role-Based Access Control
COMMENT ON TABLE bank_transfers_companyuser IS 'Links users to companies with role-based permissions. Supports multi-company user access with different roles per company.';
COMMENT ON COLUMN bank_transfers_companyuser.id IS 'Primary key - unique membership identifier';
COMMENT ON COLUMN bank_transfers_companyuser.user_id IS 'Foreign key to Django auth_user table';
COMMENT ON COLUMN bank_transfers_companyuser.company_id IS 'Foreign key to company - which company this user belongs to';
COMMENT ON COLUMN bank_transfers_companyuser.role IS 'User role: ADMIN, FINANCIAL, ACCOUNTANT, USER (determines feature access permissions)';
COMMENT ON COLUMN bank_transfers_companyuser.is_active IS 'Whether this user membership is currently active (0=inactive, 1=active)';
COMMENT ON COLUMN bank_transfers_companyuser.custom_permissions IS 'JSON array of additional feature codes this user can access beyond their role permissions';
COMMENT ON COLUMN bank_transfers_companyuser.permission_restrictions IS 'JSON array of feature codes this user is explicitly denied access to (overrides role permissions)';
COMMENT ON COLUMN bank_transfers_companyuser.joined_at IS 'Timestamp when user was added to this company';

-- User Profile Extension
COMMENT ON TABLE bank_transfers_userprofile IS 'Extended user profile information beyond Django auth_user. Stores preferences and company context.';
COMMENT ON COLUMN bank_transfers_userprofile.id IS 'Primary key - unique profile identifier';
COMMENT ON COLUMN bank_transfers_userprofile.user_id IS 'Foreign key to Django auth_user table';
COMMENT ON COLUMN bank_transfers_userprofile.phone IS 'User phone number for contact purposes';
COMMENT ON COLUMN bank_transfers_userprofile.preferred_language IS 'Preferred language for UI (hu, en)';
COMMENT ON COLUMN bank_transfers_userprofile.timezone IS 'User timezone for date/time display';
COMMENT ON COLUMN bank_transfers_userprofile.last_active_company_id IS 'Last company context the user was working in';
COMMENT ON COLUMN bank_transfers_userprofile.created_at IS 'Profile creation timestamp';
COMMENT ON COLUMN bank_transfers_userprofile.updated_at IS 'Last profile modification timestamp';

-- =============================================================================
-- FEATURE FLAG SYSTEM
-- =============================================================================

-- Feature Templates (Global Feature Definitions)
COMMENT ON TABLE bank_transfers_featuretemplate IS 'Template definitions for available features that can be enabled per company. Defines the catalog of features available across the system.';
COMMENT ON COLUMN bank_transfers_featuretemplate.id IS 'Primary key - unique template identifier';
COMMENT ON COLUMN bank_transfers_featuretemplate.feature_code IS 'Unique feature identifier (e.g. EXPORT_XML_SEPA, NAV_SYNC, BENEFICIARY_MANAGEMENT)';
COMMENT ON COLUMN bank_transfers_featuretemplate.display_name IS 'Human-readable name displayed in admin interface and user-facing components';
COMMENT ON COLUMN bank_transfers_featuretemplate.description IS 'Detailed description of what this feature does and its business value';
COMMENT ON COLUMN bank_transfers_featuretemplate.category IS 'Feature category for grouping (EXPORT, SYNC, TRACKING, REPORTING, INTEGRATION, GENERAL)';
COMMENT ON COLUMN bank_transfers_featuretemplate.default_enabled IS 'Whether this feature should be automatically enabled for new companies (0=no, 1=yes)';
COMMENT ON COLUMN bank_transfers_featuretemplate.is_system_critical IS 'System critical features cannot be disabled as they are essential for core functionality';
COMMENT ON COLUMN bank_transfers_featuretemplate.config_schema IS 'JSON schema for validating feature-specific configuration parameters';
COMMENT ON COLUMN bank_transfers_featuretemplate.created_at IS 'Timestamp when this feature template was created';
COMMENT ON COLUMN bank_transfers_featuretemplate.updated_at IS 'Last modification timestamp for template';

-- Company Feature Flags (Per-Company Feature Enablement)
COMMENT ON TABLE bank_transfers_companyfeature IS 'Company-specific feature flags controlling which functionality is available per company. Links companies to enabled features.';
COMMENT ON COLUMN bank_transfers_companyfeature.id IS 'Primary key - unique feature enablement identifier';
COMMENT ON COLUMN bank_transfers_companyfeature.company_id IS 'Reference to the company this feature enablement applies to';
COMMENT ON COLUMN bank_transfers_companyfeature.feature_template_id IS 'Reference to the feature template defining what feature this is';
COMMENT ON COLUMN bank_transfers_companyfeature.is_enabled IS 'Whether this feature is currently enabled for the company (0=disabled, 1=enabled)';
COMMENT ON COLUMN bank_transfers_companyfeature.config_data IS 'Company-specific JSON configuration data for this feature (optional parameters, settings, etc.)';
COMMENT ON COLUMN bank_transfers_companyfeature.enabled_at IS 'Timestamp when this feature was first enabled for the company';
COMMENT ON COLUMN bank_transfers_companyfeature.enabled_by_id IS 'Reference to the user who enabled this feature (for audit trail)';
COMMENT ON COLUMN bank_transfers_companyfeature.created_at IS 'Feature enablement creation timestamp';
COMMENT ON COLUMN bank_transfers_companyfeature.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- FINANCIAL DATA TABLES
-- =============================================================================

-- Bank Account Management
COMMENT ON TABLE bank_transfers_bankaccount IS 'Bank accounts owned by companies for originating transfers. Stores account details and default account settings.';
COMMENT ON COLUMN bank_transfers_bankaccount.id IS 'Primary key - unique account identifier';
COMMENT ON COLUMN bank_transfers_bankaccount.company_id IS 'Foreign key to company that owns this account';
COMMENT ON COLUMN bank_transfers_bankaccount.name IS 'Descriptive name for this bank account';
COMMENT ON COLUMN bank_transfers_bankaccount.account_number IS 'Bank account number or IBAN for transfers';
COMMENT ON COLUMN bank_transfers_bankaccount.bank_name IS 'Name of the bank holding this account';
COMMENT ON COLUMN bank_transfers_bankaccount.is_default IS 'Whether this is the default account for new transfers (only one per company)';
COMMENT ON COLUMN bank_transfers_bankaccount.created_at IS 'Account creation timestamp';
COMMENT ON COLUMN bank_transfers_bankaccount.updated_at IS 'Last modification timestamp';

-- Beneficiary Management
COMMENT ON TABLE bank_transfers_beneficiary IS 'Recipients of bank transfers. Contains account details, contact information, and transfer preferences per company.';
COMMENT ON COLUMN bank_transfers_beneficiary.id IS 'Primary key - unique beneficiary identifier';
COMMENT ON COLUMN bank_transfers_beneficiary.company_id IS 'Foreign key to company that owns this beneficiary record';
COMMENT ON COLUMN bank_transfers_beneficiary.name IS 'Full legal name of the beneficiary (person or organization)';
COMMENT ON COLUMN bank_transfers_beneficiary.account_number IS 'Bank account number for receiving transfers';
COMMENT ON COLUMN bank_transfers_beneficiary.description IS 'Additional description or notes about this beneficiary';
COMMENT ON COLUMN bank_transfers_beneficiary.is_frequent IS 'Whether this beneficiary is marked as frequently used for quick access';
COMMENT ON COLUMN bank_transfers_beneficiary.is_active IS 'Whether this beneficiary is currently active and available for transfers';
COMMENT ON COLUMN bank_transfers_beneficiary.remittance_information IS 'Default remittance information for transfers to this beneficiary';
COMMENT ON COLUMN bank_transfers_beneficiary.created_at IS 'Beneficiary creation timestamp';
COMMENT ON COLUMN bank_transfers_beneficiary.updated_at IS 'Last modification timestamp';

-- Transfer Templates for Recurring Payments
COMMENT ON TABLE bank_transfers_transfertemplate IS 'Reusable templates for recurring transfer patterns like monthly payroll or vendor payments. Contains default beneficiaries and amounts.';
COMMENT ON COLUMN bank_transfers_transfertemplate.id IS 'Primary key - unique template identifier';
COMMENT ON COLUMN bank_transfers_transfertemplate.company_id IS 'Foreign key to company that owns this template';
COMMENT ON COLUMN bank_transfers_transfertemplate.name IS 'Descriptive name for this template (e.g. "Monthly Payroll", "Vendor Payments")';
COMMENT ON COLUMN bank_transfers_transfertemplate.description IS 'Detailed description of what this template is used for';
COMMENT ON COLUMN bank_transfers_transfertemplate.is_active IS 'Whether this template is currently active and available for use';
COMMENT ON COLUMN bank_transfers_transfertemplate.created_at IS 'Template creation timestamp';
COMMENT ON COLUMN bank_transfers_transfertemplate.updated_at IS 'Last modification timestamp';

-- Template Beneficiary Associations
COMMENT ON TABLE bank_transfers_templatebeneficiary IS 'Links templates to beneficiaries with default amounts and payment details. Defines the standard recipients for each template.';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.id IS 'Primary key - unique template-beneficiary link identifier';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.template_id IS 'Foreign key to the transfer template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.beneficiary_id IS 'Foreign key to the beneficiary included in this template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_amount IS 'Default amount for transfers to this beneficiary when using template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_remittance IS 'Default remittance information/memo for transfers to this beneficiary';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_execution_date IS 'Default execution date for transfers (NULL for current date)';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.order IS 'Display order for beneficiaries within the template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.is_active IS 'Whether this template beneficiary is active';

-- Individual Transfer Records
COMMENT ON TABLE bank_transfers_transfer IS 'Individual bank transfer transactions. Each record represents one payment from company account to beneficiary.';
COMMENT ON COLUMN bank_transfers_transfer.id IS 'Primary key - unique transfer identifier';
COMMENT ON COLUMN bank_transfers_transfer.beneficiary_id IS 'Foreign key to transfer recipient';
COMMENT ON COLUMN bank_transfers_transfer.originator_account_id IS 'Foreign key to originating bank account';
COMMENT ON COLUMN bank_transfers_transfer.template_id IS 'Foreign key to template used to create this transfer (if applicable)';
COMMENT ON COLUMN bank_transfers_transfer.amount IS 'Transfer amount in specified currency';
COMMENT ON COLUMN bank_transfers_transfer.currency IS 'Currency code (HUF, EUR, USD)';
COMMENT ON COLUMN bank_transfers_transfer.execution_date IS 'Requested execution date for the transfer';
COMMENT ON COLUMN bank_transfers_transfer.remittance_info IS 'Payment description/memo/reference information';
COMMENT ON COLUMN bank_transfers_transfer.is_processed IS 'Whether transfer has been processed and included in XML export';
COMMENT ON COLUMN bank_transfers_transfer.notes IS 'Additional notes or comments about this transfer';
COMMENT ON COLUMN bank_transfers_transfer.order IS 'Display order for transfers within a batch or list';
COMMENT ON COLUMN bank_transfers_transfer.created_at IS 'Transfer creation timestamp';
COMMENT ON COLUMN bank_transfers_transfer.updated_at IS 'Last modification timestamp';

-- Transfer Batches for XML Generation
COMMENT ON TABLE bank_transfers_transferbatch IS 'Groups of transfers processed together for XML/CSV export. Created automatically when generating bank files.';
COMMENT ON COLUMN bank_transfers_transferbatch.id IS 'Primary key - unique batch identifier';
COMMENT ON COLUMN bank_transfers_transferbatch.company_id IS 'Foreign key to company that created this batch';
COMMENT ON COLUMN bank_transfers_transferbatch.name IS 'Descriptive name for this batch (auto-generated or user-provided)';
COMMENT ON COLUMN bank_transfers_transferbatch.description IS 'Additional description or notes about this batch';
COMMENT ON COLUMN bank_transfers_transferbatch.batch_format IS 'Export format used (XML_SEPA, CSV_KH, CSV_CUSTOM)';
COMMENT ON COLUMN bank_transfers_transferbatch.total_amount IS 'Total amount of all transfers in this batch';
COMMENT ON COLUMN bank_transfers_transferbatch.bank_usage_date IS 'Date when this batch should be processed by the bank';
COMMENT ON COLUMN bank_transfers_transferbatch.used_in_bank IS 'Whether this batch has been used/imported by the bank system';
COMMENT ON COLUMN bank_transfers_transferbatch.order IS 'Display order for batches within the system';
COMMENT ON COLUMN bank_transfers_transferbatch.created_at IS 'Batch creation and processing timestamp';
COMMENT ON COLUMN bank_transfers_transferbatch.updated_at IS 'Last modification timestamp';
COMMENT ON COLUMN bank_transfers_transferbatch.xml_generated_at IS 'Timestamp when XML/CSV was generated for this batch';

-- Transfer Batch Many-to-Many Relationship
COMMENT ON TABLE bank_transfers_transferbatch_transfers IS 'Many-to-many relationship table linking transfer batches to individual transfers. Allows transfers to be included in multiple batches.';
COMMENT ON COLUMN bank_transfers_transferbatch_transfers.id IS 'Primary key for the relationship';
COMMENT ON COLUMN bank_transfers_transferbatch_transfers.transferbatch_id IS 'Foreign key to the transfer batch';
COMMENT ON COLUMN bank_transfers_transferbatch_transfers.transfer_id IS 'Foreign key to the individual transfer';

-- =============================================================================
-- NAV INTEGRATION SYSTEM (Hungarian Tax Authority)
-- =============================================================================

-- NAV Configuration per Company
COMMENT ON TABLE bank_transfers_navconfiguration IS 'NAV (Hungarian Tax Authority) API configuration settings per company. Stores credentials and sync preferences for tax reporting.';
COMMENT ON COLUMN bank_transfers_navconfiguration.id IS 'Primary key - unique configuration identifier';
COMMENT ON COLUMN bank_transfers_navconfiguration.company_id IS 'Foreign key to company this NAV config belongs to';
COMMENT ON COLUMN bank_transfers_navconfiguration.tax_number IS 'Company tax number for NAV authentication';
COMMENT ON COLUMN bank_transfers_navconfiguration.technical_user_login IS 'Technical user login name for NAV API';
COMMENT ON COLUMN bank_transfers_navconfiguration.technical_user_password IS 'Technical user password for NAV API (encrypted)';
COMMENT ON COLUMN bank_transfers_navconfiguration.company_encryption_key IS 'Company-specific encryption key for NAV data signing';
COMMENT ON COLUMN bank_transfers_navconfiguration.exchange_key IS 'Exchange key for NAV API communication';
COMMENT ON COLUMN bank_transfers_navconfiguration.signing_key IS 'Signing key for NAV API requests';
COMMENT ON COLUMN bank_transfers_navconfiguration.api_environment IS 'NAV API environment (TEST, PRODUCTION)';
COMMENT ON COLUMN bank_transfers_navconfiguration.is_active IS 'Whether this NAV configuration is currently active';
COMMENT ON COLUMN bank_transfers_navconfiguration.sync_enabled IS 'Whether automatic NAV synchronization is enabled';
COMMENT ON COLUMN bank_transfers_navconfiguration.created_at IS 'Configuration creation timestamp';
COMMENT ON COLUMN bank_transfers_navconfiguration.updated_at IS 'Last modification timestamp';

-- Invoice Records for NAV Integration (Comprehensive Schema)
COMMENT ON TABLE bank_transfers_invoice IS 'Hungarian NAV invoice records with complete 40+ field schema for tax compliance. Stores both incoming and outgoing invoices for comprehensive tax reporting.';
COMMENT ON COLUMN bank_transfers_invoice.id IS 'Primary key - unique invoice identifier';
COMMENT ON COLUMN bank_transfers_invoice.company_id IS 'Foreign key to company that owns this invoice';
COMMENT ON COLUMN bank_transfers_invoice.nav_invoice_number IS 'NAV invoice number from tax authority system';
COMMENT ON COLUMN bank_transfers_invoice.invoice_direction IS 'Invoice direction: OUTBOUND (sent) or INBOUND (received)';
COMMENT ON COLUMN bank_transfers_invoice.supplier_name IS 'Supplier/vendor company name';
COMMENT ON COLUMN bank_transfers_invoice.supplier_tax_number IS 'Supplier tax number (Hungarian adószám)';
COMMENT ON COLUMN bank_transfers_invoice.supplier_bank_account_number IS 'Supplier bank account number for payments';
COMMENT ON COLUMN bank_transfers_invoice.customer_name IS 'Customer/buyer company name';
COMMENT ON COLUMN bank_transfers_invoice.customer_tax_number IS 'Customer tax number';
COMMENT ON COLUMN bank_transfers_invoice.customer_bank_account_number IS 'Customer bank account number';
COMMENT ON COLUMN bank_transfers_invoice.issue_date IS 'Date when the invoice was issued by supplier';
COMMENT ON COLUMN bank_transfers_invoice.fulfillment_date IS 'Performance/delivery date for goods or services';
COMMENT ON COLUMN bank_transfers_invoice.payment_due_date IS 'Due date for invoice payment';
COMMENT ON COLUMN bank_transfers_invoice.payment_date IS 'Date when payment was actually made';
COMMENT ON COLUMN bank_transfers_invoice.payment_method IS 'Payment method used (TRANSFER, CASH, CARD, etc.)';
COMMENT ON COLUMN bank_transfers_invoice.currency_code IS 'Invoice currency code (HUF, EUR, USD)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_net_amount IS 'Net amount in original currency (before VAT)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_vat_amount IS 'VAT amount in original currency';
COMMENT ON COLUMN bank_transfers_invoice.invoice_gross_amount IS 'Gross amount in original currency (including VAT)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_net_amount_huf IS 'Net amount converted to HUF for tax reporting';
COMMENT ON COLUMN bank_transfers_invoice.invoice_vat_amount_huf IS 'VAT amount converted to HUF for tax reporting';
COMMENT ON COLUMN bank_transfers_invoice.invoice_gross_amount_huf IS 'Gross amount converted to HUF for tax reporting';
COMMENT ON COLUMN bank_transfers_invoice.invoice_category IS 'Invoice category for NAV classification';
COMMENT ON COLUMN bank_transfers_invoice.invoice_appearance IS 'Invoice appearance type (PAPER, ELECTRONIC, EDI, etc.)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_operation IS 'Invoice operation type (CREATE, MODIFY, STORNO)';
COMMENT ON COLUMN bank_transfers_invoice.completeness_indicator IS 'Data completeness indicator for NAV compliance';
COMMENT ON COLUMN bank_transfers_invoice.invoice_index IS 'Invoice index number within the system';
COMMENT ON COLUMN bank_transfers_invoice.modification_index IS 'Modification index for invoice revisions';
COMMENT ON COLUMN bank_transfers_invoice.batch_index IS 'Batch index for grouped invoice submissions';
COMMENT ON COLUMN bank_transfers_invoice.original_invoice_number IS 'Original invoice number for modifications/storno';
COMMENT ON COLUMN bank_transfers_invoice.original_request_version IS 'Original request version for NAV API compatibility';
COMMENT ON COLUMN bank_transfers_invoice.completion_date IS 'Invoice completion date in NAV system';
COMMENT ON COLUMN bank_transfers_invoice.source IS 'Source of invoice data (MANUAL, NAV_API, IMPORT)';
COMMENT ON COLUMN bank_transfers_invoice.nav_source IS 'NAV source system identifier';
COMMENT ON COLUMN bank_transfers_invoice.nav_transaction_id IS 'NAV transaction ID from successful submission';
COMMENT ON COLUMN bank_transfers_invoice.nav_creation_date IS 'Date when invoice was created in NAV system';
COMMENT ON COLUMN bank_transfers_invoice.last_modified_date IS 'Last modified date in NAV system';
COMMENT ON COLUMN bank_transfers_invoice.nav_invoice_hash IS 'Hash value of invoice for integrity verification';
COMMENT ON COLUMN bank_transfers_invoice.nav_invoice_xml IS 'Complete XML representation of invoice for NAV';
COMMENT ON COLUMN bank_transfers_invoice.sync_status IS 'Current sync status with NAV (PENDING, SYNCED, ERROR)';
COMMENT ON COLUMN bank_transfers_invoice.storno_of_id IS 'Reference to original invoice if this is a storno';
COMMENT ON COLUMN bank_transfers_invoice.created_at IS 'Invoice creation timestamp in local system';
COMMENT ON COLUMN bank_transfers_invoice.updated_at IS 'Last modification timestamp in local system';

-- Invoice Line Items
COMMENT ON TABLE bank_transfers_invoicelineitem IS 'Individual line items within invoices. Each line represents a product or service with detailed pricing and tax information.';
COMMENT ON COLUMN bank_transfers_invoicelineitem.id IS 'Primary key - unique line item identifier';
COMMENT ON COLUMN bank_transfers_invoicelineitem.invoice_id IS 'Foreign key to parent invoice';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_number IS 'Line number within the invoice';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_description IS 'Description of product or service on this line';
COMMENT ON COLUMN bank_transfers_invoicelineitem.quantity IS 'Quantity of items or units of service';
COMMENT ON COLUMN bank_transfers_invoicelineitem.unit_of_measure IS 'Unit of measure (pcs, kg, hours, etc.)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.unit_price IS 'Price per unit before VAT';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_net_amount IS 'Total net amount for this line (quantity × unit_price)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.vat_rate IS 'VAT rate applied to this line item (%)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_vat_amount IS 'VAT amount for this line item';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_gross_amount IS 'Total gross amount for this line (net + VAT)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.product_code_category IS 'Product code category (VTSZ, SZJ, etc.)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.product_code_value IS 'Product code value for tax classification';
COMMENT ON COLUMN bank_transfers_invoicelineitem.created_at IS 'Line item creation timestamp';
COMMENT ON COLUMN bank_transfers_invoicelineitem.updated_at IS 'Last modification timestamp';

-- Invoice Sync Logs
COMMENT ON TABLE bank_transfers_invoicesynclog IS 'Audit log for NAV invoice synchronization operations. Tracks sync attempts, results, and error details for troubleshooting.';
COMMENT ON COLUMN bank_transfers_invoicesynclog.id IS 'Primary key - unique sync log identifier';
COMMENT ON COLUMN bank_transfers_invoicesynclog.company_id IS 'Foreign key to company that performed the sync';
COMMENT ON COLUMN bank_transfers_invoicesynclog.sync_start_time IS 'Timestamp when sync operation started';
COMMENT ON COLUMN bank_transfers_invoicesynclog.sync_end_time IS 'Timestamp when sync operation completed';
COMMENT ON COLUMN bank_transfers_invoicesynclog.direction_synced IS 'Direction of sync (INBOUND, OUTBOUND, BOTH)';
COMMENT ON COLUMN bank_transfers_invoicesynclog.invoices_processed IS 'Total number of invoices processed in this sync';
COMMENT ON COLUMN bank_transfers_invoicesynclog.invoices_created IS 'Number of new invoices created';
COMMENT ON COLUMN bank_transfers_invoicesynclog.invoices_updated IS 'Number of existing invoices updated';
COMMENT ON COLUMN bank_transfers_invoicesynclog.errors_count IS 'Number of errors encountered during sync';
COMMENT ON COLUMN bank_transfers_invoicesynclog.last_error_message IS 'Last error message encountered (if any)';
COMMENT ON COLUMN bank_transfers_invoicesynclog.sync_status IS 'Overall sync status (SUCCESS, PARTIAL, FAILED)';
COMMENT ON COLUMN bank_transfers_invoicesynclog.created_at IS 'Log entry creation timestamp';
COMMENT ON COLUMN bank_transfers_invoicesynclog.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify table comments were added
SELECT 
    schemaname,
    tablename,
    obj_description(oid) AS table_comment
FROM pg_tables pt
JOIN pg_class pc ON pc.relname = pt.tablename
WHERE schemaname = 'public' 
  AND tablename LIKE 'bank_transfers_%'
ORDER BY tablename;

-- Verify column comments were added  
SELECT 
    t.table_name,
    c.column_name,
    c.ordinal_position,
    col_description(pgc.oid, c.ordinal_position) AS column_comment
FROM information_schema.tables t
JOIN information_schema.columns c ON c.table_name = t.table_name
JOIN pg_class pgc ON pgc.relname = t.table_name
WHERE t.table_schema = 'public'
  AND t.table_name LIKE 'bank_transfers_%'
  AND col_description(pgc.oid, c.ordinal_position) IS NOT NULL
ORDER BY t.table_name, c.ordinal_position;