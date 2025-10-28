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
COMMENT ON TABLE bank_transfers_beneficiary IS 'Recipients of bank transfers. Contains account details, VAT numbers, contact information, and transfer preferences per company. Supports both bank account and VAT number identification.';
COMMENT ON COLUMN bank_transfers_beneficiary.id IS 'Primary key - unique beneficiary identifier';
COMMENT ON COLUMN bank_transfers_beneficiary.company_id IS 'Foreign key to company that owns this beneficiary record';
COMMENT ON COLUMN bank_transfers_beneficiary.name IS 'Full legal name of the beneficiary (person or organization)';
COMMENT ON COLUMN bank_transfers_beneficiary.account_number IS 'Bank account number for receiving transfers (nullable - can use VAT number instead)';
COMMENT ON COLUMN bank_transfers_beneficiary.vat_number IS 'Hungarian personal VAT number (személyi adóazonosító jel) - 10 digits (e.g. 8440961790). Nullable when account_number is provided.';
COMMENT ON COLUMN bank_transfers_beneficiary.tax_number IS 'Hungarian company tax number - 8 digits (first 8 digits of full tax ID, e.g. 12345678). Used for NAV invoice integration fallback when bank account is missing.';
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
COMMENT ON COLUMN bank_transfers_transfer.nav_invoice_id IS 'Foreign key to NAV invoice - links transfer to the invoice it pays (optional)';
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
COMMENT ON COLUMN bank_transfers_invoice.payment_status IS 'Payment status tracking: UNPAID (Fizetésre vár), PREPARED (Előkészítve), PAID (Kifizetve)';
COMMENT ON COLUMN bank_transfers_invoice.payment_status_date IS 'Date when payment status was last changed';
COMMENT ON COLUMN bank_transfers_invoice.auto_marked_paid IS 'Whether invoice was automatically marked as paid during batch processing (TRUE=automatic, FALSE=manual)';
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
-- MNB EXCHANGE RATE INTEGRATION
-- =============================================================================

-- Exchange Rate Records
COMMENT ON TABLE bank_transfers_exchangerate IS 'Official exchange rates from Magyar Nemzeti Bank (MNB) for USD and EUR currencies. Provides accurate, government-sourced exchange rates for currency conversion and financial calculations.';
COMMENT ON COLUMN bank_transfers_exchangerate.id IS 'Primary key - unique exchange rate identifier';
COMMENT ON COLUMN bank_transfers_exchangerate.rate_date IS 'Date for which this exchange rate is valid';
COMMENT ON COLUMN bank_transfers_exchangerate.currency IS 'ISO currency code (USD or EUR)';
COMMENT ON COLUMN bank_transfers_exchangerate.rate IS 'Exchange rate: 1 unit of currency = X HUF (6 decimal precision)';
COMMENT ON COLUMN bank_transfers_exchangerate.unit IS 'Number of currency units this rate applies to (typically 1)';
COMMENT ON COLUMN bank_transfers_exchangerate.sync_date IS 'Timestamp when this rate was fetched from MNB API';
COMMENT ON COLUMN bank_transfers_exchangerate.source IS 'Data source identifier (always MNB for official rates)';
COMMENT ON COLUMN bank_transfers_exchangerate.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN bank_transfers_exchangerate.updated_at IS 'Last modification timestamp';

-- Exchange Rate Sync Log
COMMENT ON TABLE bank_transfers_exchangeratesynclog IS 'Audit trail for MNB exchange rate synchronization operations. Tracks all sync attempts with statistics, errors, and performance metrics.';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.id IS 'Primary key - unique sync log identifier';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.sync_start_time IS 'Exact timestamp when sync operation started';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.sync_end_time IS 'Timestamp when sync operation completed (NULL if still running)';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.currencies_synced IS 'Comma-separated list of currency codes synced (e.g., USD,EUR)';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.date_range_start IS 'Start date of the sync range (inclusive)';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.date_range_end IS 'End date of the sync range (inclusive)';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.rates_created IS 'Number of new exchange rate records created during sync';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.rates_updated IS 'Number of existing exchange rate records updated during sync';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.sync_status IS 'Sync operation status: RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.error_message IS 'Error details if sync failed (NULL if successful)';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.created_at IS 'Log record creation timestamp';
COMMENT ON COLUMN bank_transfers_exchangeratesynclog.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- TRUSTED PARTNERS AUTO-PAYMENT SYSTEM
-- =============================================================================

-- Trusted Partner Management
COMMENT ON TABLE bank_transfers_trustedpartner IS 'Company-scoped trusted partners for automatic NAV invoice payment processing. When invoices are received from trusted partners, they are automatically marked as PAID.';
COMMENT ON COLUMN bank_transfers_trustedpartner.id IS 'Primary key - unique trusted partner identifier';
COMMENT ON COLUMN bank_transfers_trustedpartner.company_id IS 'Foreign key to company - which company owns this trusted partner';
COMMENT ON COLUMN bank_transfers_trustedpartner.partner_name IS 'Full name of the trusted partner (supplier/organization)';
COMMENT ON COLUMN bank_transfers_trustedpartner.tax_number IS 'Hungarian tax identification number of the partner (supports multiple formats)';
COMMENT ON COLUMN bank_transfers_trustedpartner.is_active IS 'Active status - inactive partners are ignored during auto-processing';
COMMENT ON COLUMN bank_transfers_trustedpartner.auto_pay IS 'Auto-payment enabled - when TRUE, invoices are automatically marked as PAID';
COMMENT ON COLUMN bank_transfers_trustedpartner.notes IS 'Additional notes or comments about this trusted partner';
COMMENT ON COLUMN bank_transfers_trustedpartner.invoice_count IS 'Statistics: Total number of invoices processed from this partner';
COMMENT ON COLUMN bank_transfers_trustedpartner.last_invoice_date IS 'Statistics: Date of the most recent invoice from this partner';
COMMENT ON COLUMN bank_transfers_trustedpartner.created_at IS 'Partner registration timestamp';
COMMENT ON COLUMN bank_transfers_trustedpartner.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- BANK STATEMENT IMPORT SYSTEM
-- =============================================================================

-- Bank Statement Records
COMMENT ON TABLE bank_transfers_bankstatement IS 'Company-scoped bank statement records from uploaded PDF/CSV/XML files. Represents a single uploaded bank statement with parsing status, transaction statistics, and error tracking.';
COMMENT ON COLUMN bank_transfers_bankstatement.id IS 'Primary key - unique bank statement identifier';
COMMENT ON COLUMN bank_transfers_bankstatement.company_id IS 'Foreign key to company - which company owns this statement';
COMMENT ON COLUMN bank_transfers_bankstatement.bank_code IS 'Bank identifier code: GRANIT, MAGNET, REVOLUT, KH, OTP, CIB, ERSTE';
COMMENT ON COLUMN bank_transfers_bankstatement.bank_name IS 'Full name of the bank';
COMMENT ON COLUMN bank_transfers_bankstatement.bank_bic IS 'Bank Identifier Code (SWIFT code)';
COMMENT ON COLUMN bank_transfers_bankstatement.account_number IS 'Hungarian bank account number (formatted with dashes)';
COMMENT ON COLUMN bank_transfers_bankstatement.account_iban IS 'International Bank Account Number';
COMMENT ON COLUMN bank_transfers_bankstatement.statement_period_from IS 'Start date of statement period';
COMMENT ON COLUMN bank_transfers_bankstatement.statement_period_to IS 'End date of statement period';
COMMENT ON COLUMN bank_transfers_bankstatement.statement_number IS 'Bank statement reference number';
COMMENT ON COLUMN bank_transfers_bankstatement.opening_balance IS 'Account balance at statement period start';
COMMENT ON COLUMN bank_transfers_bankstatement.closing_balance IS 'Account balance at statement period end (NULL if not available)';
COMMENT ON COLUMN bank_transfers_bankstatement.file_name IS 'Original uploaded filename';
COMMENT ON COLUMN bank_transfers_bankstatement.file_hash IS 'SHA256 hash of uploaded file for duplicate detection';
COMMENT ON COLUMN bank_transfers_bankstatement.file_size IS 'File size in bytes';
COMMENT ON COLUMN bank_transfers_bankstatement.file_path IS 'Storage path for uploaded file';
COMMENT ON COLUMN bank_transfers_bankstatement.uploaded_by_id IS 'Foreign key to auth_user - user who uploaded this statement';
COMMENT ON COLUMN bank_transfers_bankstatement.uploaded_at IS 'Timestamp when statement was uploaded';
COMMENT ON COLUMN bank_transfers_bankstatement.status IS 'Processing status: UPLOADED, PARSING, PARSED, ERROR';
COMMENT ON COLUMN bank_transfers_bankstatement.total_transactions IS 'Total number of transactions in statement';
COMMENT ON COLUMN bank_transfers_bankstatement.credit_count IS 'Number of credit transactions (positive amounts)';
COMMENT ON COLUMN bank_transfers_bankstatement.debit_count IS 'Number of debit transactions (negative amounts)';
COMMENT ON COLUMN bank_transfers_bankstatement.total_credits IS 'Sum of all credit transactions';
COMMENT ON COLUMN bank_transfers_bankstatement.total_debits IS 'Sum of all debit transactions (absolute value)';
COMMENT ON COLUMN bank_transfers_bankstatement.matched_count IS 'Number of transactions matched to NAV invoices';
COMMENT ON COLUMN bank_transfers_bankstatement.parse_error IS 'Error message if parsing failed (NULL if successful)';
COMMENT ON COLUMN bank_transfers_bankstatement.parse_warnings IS 'JSON array of warning messages from parsing process';
COMMENT ON COLUMN bank_transfers_bankstatement.raw_metadata IS 'JSON object with raw metadata extracted from statement file';
COMMENT ON COLUMN bank_transfers_bankstatement.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN bank_transfers_bankstatement.updated_at IS 'Last modification timestamp';

-- Bank Transaction Records
COMMENT ON TABLE bank_transfers_banktransaction IS 'Individual transaction records extracted from bank statements. Supports all transaction types including AFR transfers, POS purchases, bank fees, interest, and other banking operations. Contains matching to NAV invoices, transfers, and reimbursement pairs.';
COMMENT ON COLUMN bank_transfers_banktransaction.id IS 'Primary key - unique transaction identifier';
COMMENT ON COLUMN bank_transfers_banktransaction.company_id IS 'Foreign key to company - which company owns this transaction';
COMMENT ON COLUMN bank_transfers_banktransaction.bank_statement_id IS 'Foreign key to bank_transfers_bankstatement - parent statement';
COMMENT ON COLUMN bank_transfers_banktransaction.transaction_type IS 'Transaction type code: AFR_CREDIT, AFR_DEBIT, TRANSFER_CREDIT, TRANSFER_DEBIT, POS_PURCHASE, ATM_WITHDRAWAL, BANK_FEE, INTEREST_CREDIT, INTEREST_DEBIT, CORRECTION, OTHER';
COMMENT ON COLUMN bank_transfers_banktransaction.booking_date IS 'Date when transaction was booked to account';
COMMENT ON COLUMN bank_transfers_banktransaction.value_date IS 'Value date (effective date) for interest calculation';
COMMENT ON COLUMN bank_transfers_banktransaction.amount IS 'Transaction amount (negative for debit, positive for credit)';
COMMENT ON COLUMN bank_transfers_banktransaction.currency IS 'ISO currency code (default: HUF)';
COMMENT ON COLUMN bank_transfers_banktransaction.description IS 'Full transaction description from bank';
COMMENT ON COLUMN bank_transfers_banktransaction.short_description IS 'Shortened or summarized description';
COMMENT ON COLUMN bank_transfers_banktransaction.payment_id IS 'Payment identifier from bank system';
COMMENT ON COLUMN bank_transfers_banktransaction.transaction_id IS 'Unique transaction identifier';
COMMENT ON COLUMN bank_transfers_banktransaction.payer_name IS 'Name of payer (for incoming transfers)';
COMMENT ON COLUMN bank_transfers_banktransaction.payer_iban IS 'IBAN of payer';
COMMENT ON COLUMN bank_transfers_banktransaction.payer_account_number IS 'Account number of payer';
COMMENT ON COLUMN bank_transfers_banktransaction.payer_bic IS 'BIC of payer''s bank';
COMMENT ON COLUMN bank_transfers_banktransaction.beneficiary_name IS 'Name of beneficiary (for outgoing transfers)';
COMMENT ON COLUMN bank_transfers_banktransaction.beneficiary_iban IS 'IBAN of beneficiary';
COMMENT ON COLUMN bank_transfers_banktransaction.beneficiary_account_number IS 'Account number of beneficiary';
COMMENT ON COLUMN bank_transfers_banktransaction.beneficiary_bic IS 'BIC of beneficiary''s bank';
COMMENT ON COLUMN bank_transfers_banktransaction.reference IS 'Unstructured remittance information (közlemény) - critical for invoice matching';
COMMENT ON COLUMN bank_transfers_banktransaction.partner_id IS 'End-to-end identifier between transaction partners';
COMMENT ON COLUMN bank_transfers_banktransaction.transaction_type_code IS 'Bank-specific transaction type code (e.g., 001-00)';
COMMENT ON COLUMN bank_transfers_banktransaction.fee_amount IS 'Transaction fee charged by bank';
COMMENT ON COLUMN bank_transfers_banktransaction.card_number IS 'Masked card number for POS/ATM transactions';
COMMENT ON COLUMN bank_transfers_banktransaction.merchant_name IS 'Merchant name for POS purchases';
COMMENT ON COLUMN bank_transfers_banktransaction.merchant_location IS 'Merchant location for POS purchases';
COMMENT ON COLUMN bank_transfers_banktransaction.original_amount IS 'Original amount in foreign currency (before conversion)';
COMMENT ON COLUMN bank_transfers_banktransaction.original_currency IS 'Original currency code for FX transactions';
COMMENT ON COLUMN bank_transfers_banktransaction.exchange_rate IS 'Exchange rate used for currency conversion (6 decimal precision)';
COMMENT ON COLUMN bank_transfers_banktransaction.matched_invoice_id IS 'Foreign key to bank_transfers_invoice - NAV invoice matched to this transaction';
COMMENT ON COLUMN bank_transfers_banktransaction.matched_transfer_id IS 'Foreign key to bank_transfers_transfer - Transfer from executed batch matched to this transaction';
COMMENT ON COLUMN bank_transfers_banktransaction.matched_reimbursement_id IS 'Foreign key to self - Offsetting transaction (e.g., POS purchase + personal reimbursement transfer)';
COMMENT ON COLUMN bank_transfers_banktransaction.match_confidence IS 'Matching confidence score (0.00 to 1.00)';
COMMENT ON COLUMN bank_transfers_banktransaction.match_method IS 'Method used for matching: REFERENCE_EXACT, AMOUNT_IBAN, FUZZY_NAME, TRANSFER_EXACT, REIMBURSEMENT_PAIR, MANUAL';
COMMENT ON COLUMN bank_transfers_banktransaction.match_notes IS 'Additional notes about matching process';
COMMENT ON COLUMN bank_transfers_banktransaction.matched_at IS 'Timestamp when transaction was matched';
COMMENT ON COLUMN bank_transfers_banktransaction.matched_by_id IS 'Foreign key to auth_user - User who performed matching (NULL for automatic)';
COMMENT ON COLUMN bank_transfers_banktransaction.is_extra_cost IS 'Flag indicating if this is an extra cost (bank fee, interest, etc.)';
COMMENT ON COLUMN bank_transfers_banktransaction.extra_cost_category IS 'Category for extra costs: BANK_FEE, CARD_PURCHASE, INTEREST, TAX_DUTY, CASH_WITHDRAWAL, OTHER';
COMMENT ON COLUMN bank_transfers_banktransaction.raw_data IS 'JSON object with raw transaction data from bank statement (sanitized for JSON storage)';
COMMENT ON COLUMN bank_transfers_banktransaction.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN bank_transfers_banktransaction.updated_at IS 'Last modification timestamp';

-- Other Cost Records
COMMENT ON TABLE bank_transfers_othercost IS 'Additional cost records derived from bank transactions. Allows enhanced categorization, detailed notes, and flexible tagging beyond standard BankTransaction fields. Used for expense tracking, cost analysis, and financial reporting.';
COMMENT ON COLUMN bank_transfers_othercost.id IS 'Primary key - unique cost record identifier';
COMMENT ON COLUMN bank_transfers_othercost.company_id IS 'Foreign key to company - which company owns this cost record';
COMMENT ON COLUMN bank_transfers_othercost.bank_transaction_id IS 'Foreign key to bank_transfers_banktransaction - optional reference to originating bank transaction (one-to-one)';
COMMENT ON COLUMN bank_transfers_othercost.category IS 'Cost category: BANK_FEE, CARD_PURCHASE, INTEREST, TAX_DUTY, CASH_WITHDRAWAL, SUBSCRIPTION, UTILITY, FUEL, TRAVEL, OFFICE, OTHER';
COMMENT ON COLUMN bank_transfers_othercost.amount IS 'Cost amount (always positive for costs)';
COMMENT ON COLUMN bank_transfers_othercost.currency IS 'ISO currency code (default: HUF)';
COMMENT ON COLUMN bank_transfers_othercost.date IS 'Date of the cost';
COMMENT ON COLUMN bank_transfers_othercost.description IS 'Detailed description of the cost';
COMMENT ON COLUMN bank_transfers_othercost.notes IS 'Additional notes, context, or justification';
COMMENT ON COLUMN bank_transfers_othercost.tags IS 'JSON array of tag strings for flexible categorization (e.g., ["fuel", "travel", "office"])';
COMMENT ON COLUMN bank_transfers_othercost.created_by_id IS 'Foreign key to auth_user - User who created this cost record';
COMMENT ON COLUMN bank_transfers_othercost.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN bank_transfers_othercost.updated_at IS 'Last modification timestamp';

-- Supplier Master Data (BASE_TABLES Feature)
COMMENT ON TABLE bank_transfers_supplier IS 'Company-scoped supplier master data. Stores partner information with validity period management for temporal data tracking.';
COMMENT ON COLUMN bank_transfers_supplier.id IS 'Primary key - unique supplier identifier';
COMMENT ON COLUMN bank_transfers_supplier.company_id IS 'Foreign key to company - which company owns this supplier';
COMMENT ON COLUMN bank_transfers_supplier.partner_name IS 'Legal name of the supplier/partner';
COMMENT ON COLUMN bank_transfers_supplier.category IS 'Supplier category (e.g., "Medical Devices", "IT Services")';
COMMENT ON COLUMN bank_transfers_supplier.type IS 'Supplier type classification (e.g., "Distributor", "Manufacturer")';
COMMENT ON COLUMN bank_transfers_supplier.valid_from IS 'Start date of validity period (NULL = valid from beginning of time)';
COMMENT ON COLUMN bank_transfers_supplier.valid_to IS 'End date of validity period (NULL = valid indefinitely)';
COMMENT ON COLUMN bank_transfers_supplier.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN bank_transfers_supplier.updated_at IS 'Last modification timestamp';

-- Customer Master Data (BASE_TABLES Feature)
COMMENT ON TABLE bank_transfers_customer IS 'Company-scoped customer master data. Stores customer information with cashflow adjustment days for payment term management and validity tracking.';
COMMENT ON COLUMN bank_transfers_customer.id IS 'Primary key - unique customer identifier';
COMMENT ON COLUMN bank_transfers_customer.company_id IS 'Foreign key to company - which company owns this customer';
COMMENT ON COLUMN bank_transfers_customer.customer_name IS 'Legal name of the customer';
COMMENT ON COLUMN bank_transfers_customer.cashflow_adjustment IS 'Days to adjust cashflow calculations (e.g., payment terms offset) - negative = early payment, positive = delayed payment';
COMMENT ON COLUMN bank_transfers_customer.valid_from IS 'Start date of validity period (NULL = valid from beginning of time)';
COMMENT ON COLUMN bank_transfers_customer.valid_to IS 'End date of validity period (NULL = valid indefinitely)';
COMMENT ON COLUMN bank_transfers_customer.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN bank_transfers_customer.updated_at IS 'Last modification timestamp';

-- Product Price Master Data (BASE_TABLES Feature)
COMMENT ON TABLE bank_transfers_productprice IS 'Company-scoped product price master data for CONMED products. Comprehensive pricing information with multi-currency support, markup tracking, unit of measure, and inventory management flags with validity periods.';
COMMENT ON COLUMN bank_transfers_productprice.id IS 'Primary key - unique product price identifier';
COMMENT ON COLUMN bank_transfers_productprice.company_id IS 'Foreign key to company - which company owns this product price';
COMMENT ON COLUMN bank_transfers_productprice.product_value IS 'Product code/SKU (unique identifier for the product)';
COMMENT ON COLUMN bank_transfers_productprice.product_description IS 'Detailed product description';
COMMENT ON COLUMN bank_transfers_productprice.uom IS 'Unit of measure in English (e.g., "piece", "box", "kg")';
COMMENT ON COLUMN bank_transfers_productprice.uom_hun IS 'Unit of measure in Hungarian (e.g., "darab", "doboz", "kg")';
COMMENT ON COLUMN bank_transfers_productprice.purchase_price_usd IS 'Purchase price in USD (stored as string for formatting flexibility)';
COMMENT ON COLUMN bank_transfers_productprice.purchase_price_huf IS 'Purchase price in HUF (stored as string for formatting flexibility)';
COMMENT ON COLUMN bank_transfers_productprice.markup IS 'Markup percentage (e.g., "25%", "1.5x")';
COMMENT ON COLUMN bank_transfers_productprice.sales_price_huf IS 'Sales price in HUF (stored as string for formatting flexibility)';
COMMENT ON COLUMN bank_transfers_productprice.cap_disp IS 'Capital/Disposable classification or additional product categorization';
COMMENT ON COLUMN bank_transfers_productprice.is_inventory_managed IS 'Indicates if this product requires inventory tracking';
COMMENT ON COLUMN bank_transfers_productprice.valid_from IS 'Start date of validity period (NULL = valid from beginning of time)';
COMMENT ON COLUMN bank_transfers_productprice.valid_to IS 'End date of validity period (NULL = valid indefinitely)';
COMMENT ON COLUMN bank_transfers_productprice.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN bank_transfers_productprice.updated_at IS 'Last modification timestamp';

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