-- COMPLETE PostgreSQL Database Comments Script
-- Transfer XML Generator - Hungarian Banking System
-- Adds table and column comments for ALL current models
-- Execute against PostgreSQL production database (Railway)

-- =============================================================================
-- TABLE COMMENTS - Multi-Company Architecture
-- =============================================================================

-- Company table
COMMENT ON TABLE bank_transfers_company IS 'Company entities for multi-tenant architecture. Each company has complete data isolation.';

-- CompanyUser table  
COMMENT ON TABLE bank_transfers_companyuser IS 'User-company relationships with role-based access control. Enables multi-company membership.';

-- UserProfile table
COMMENT ON TABLE bank_transfers_userprofile IS 'Extended user profile information with company preferences and localization settings.';

-- =============================================================================
-- TABLE COMMENTS - Core Transfer System
-- =============================================================================

-- BankAccount table
COMMENT ON TABLE bank_transfers_bankaccount IS 'Company-scoped originator bank accounts for transfers. Contains accounts that will be debited during XML/CSV export generation.';

-- Beneficiary table
COMMENT ON TABLE bank_transfers_beneficiary IS 'Company-scoped beneficiary information for bank transfers. Contains payees, suppliers, employees, and tax authorities.';

-- TransferTemplate table
COMMENT ON TABLE bank_transfers_transfertemplate IS 'Company-scoped reusable transfer templates for recurring payments like monthly payroll, VAT payments, or supplier batches.';

-- TemplateBeneficiary table
COMMENT ON TABLE bank_transfers_templatebeneficiary IS 'Junction table linking templates to beneficiaries with default payment amounts and remittance information.';

-- Transfer table
COMMENT ON TABLE bank_transfers_transfer IS 'Individual transfer records representing single bank payments. These are processed into XML/CSV batches for bank import.';

-- TransferBatch table
COMMENT ON TABLE bank_transfers_transferbatch IS 'Groups transfers into batches for XML/CSV export generation. Each batch represents one file (XML or CSV) sent to the bank.';

-- TransferBatch_transfers junction table
COMMENT ON TABLE bank_transfers_transferbatch_transfers IS 'Many-to-many junction table linking transfer batches to individual transfers.';

-- =============================================================================
-- TABLE COMMENTS - NAV Integration System
-- =============================================================================

-- NAVConfiguration table
COMMENT ON TABLE bank_transfers_navconfiguration IS 'NAV (Hungarian Tax Authority) API configuration for invoice synchronization. Company-specific credentials and settings.';

-- Invoice table
COMMENT ON TABLE bank_transfers_invoice IS 'Invoice records synchronized from NAV (Hungarian Tax Authority) system with complete XML storage.';

-- InvoiceLineItem table
COMMENT ON TABLE bank_transfers_invoicelineitem IS 'Line items extracted from NAV invoice XML data. Represents individual products/services on invoices.';

-- InvoiceSyncLog table
COMMENT ON TABLE bank_transfers_invoicesynclog IS 'Audit log for NAV invoice synchronization operations with error tracking and performance metrics.';

-- =============================================================================
-- COLUMN COMMENTS - Company (Multi-tenant)
-- =============================================================================

COMMENT ON COLUMN bank_transfers_company.id IS 'Unique identifier for company';
COMMENT ON COLUMN bank_transfers_company.name IS 'Company legal name';
COMMENT ON COLUMN bank_transfers_company.tax_id IS 'Hungarian tax identification number (adószám)';
COMMENT ON COLUMN bank_transfers_company.address IS 'Company registered address';
COMMENT ON COLUMN bank_transfers_company.phone IS 'Primary contact phone number';
COMMENT ON COLUMN bank_transfers_company.email IS 'Primary contact email address';
COMMENT ON COLUMN bank_transfers_company.is_active IS 'Soft delete flag for company deactivation';
COMMENT ON COLUMN bank_transfers_company.created_at IS 'Company registration timestamp';
COMMENT ON COLUMN bank_transfers_company.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - CompanyUser (User-Company Relationships)
-- =============================================================================

COMMENT ON COLUMN bank_transfers_companyuser.id IS 'Unique identifier for user-company relationship';
COMMENT ON COLUMN bank_transfers_companyuser.user_id IS 'Reference to Django User (auth_user.id)';
COMMENT ON COLUMN bank_transfers_companyuser.company_id IS 'Reference to Company (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_companyuser.role IS 'User role in company: ADMIN or USER';
COMMENT ON COLUMN bank_transfers_companyuser.is_active IS 'Active membership flag';
COMMENT ON COLUMN bank_transfers_companyuser.joined_at IS 'Membership creation timestamp';

-- =============================================================================
-- COLUMN COMMENTS - UserProfile (Extended User Info)
-- =============================================================================

COMMENT ON COLUMN bank_transfers_userprofile.id IS 'Unique identifier for user profile';
COMMENT ON COLUMN bank_transfers_userprofile.user_id IS 'One-to-one reference to Django User (auth_user.id)';
COMMENT ON COLUMN bank_transfers_userprofile.phone IS 'User phone number';
COMMENT ON COLUMN bank_transfers_userprofile.preferred_language IS 'UI language preference (default: hu)';
COMMENT ON COLUMN bank_transfers_userprofile.timezone IS 'User timezone setting (default: Europe/Budapest)';
COMMENT ON COLUMN bank_transfers_userprofile.last_active_company_id IS 'Last company context used by user';
COMMENT ON COLUMN bank_transfers_userprofile.created_at IS 'Profile creation timestamp';
COMMENT ON COLUMN bank_transfers_userprofile.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - BankAccount
-- =============================================================================

COMMENT ON COLUMN bank_transfers_bankaccount.id IS 'Unique identifier for bank account record';
COMMENT ON COLUMN bank_transfers_bankaccount.company_id IS 'Company owner of this account (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_bankaccount.name IS 'Display name for the account (e.g., "Main Business Account", "Payroll Account")';
COMMENT ON COLUMN bank_transfers_bankaccount.account_number IS 'Hungarian bank account number in formatted form (e.g., "1210001119014874" or "12100011-19014874")';
COMMENT ON COLUMN bank_transfers_bankaccount.bank_name IS 'Name of the bank holding this account';
COMMENT ON COLUMN bank_transfers_bankaccount.is_default IS 'Flags the default account for new transfers within the company';
COMMENT ON COLUMN bank_transfers_bankaccount.created_at IS 'Account registration timestamp';
COMMENT ON COLUMN bank_transfers_bankaccount.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - Beneficiary
-- =============================================================================

COMMENT ON COLUMN bank_transfers_beneficiary.id IS 'Unique identifier for beneficiary record';
COMMENT ON COLUMN bank_transfers_beneficiary.company_id IS 'Company owner of this beneficiary (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_beneficiary.name IS 'Full legal name of the beneficiary (person or organization)';
COMMENT ON COLUMN bank_transfers_beneficiary.account_number IS 'Beneficiary''s bank account number in Hungarian format (validated and formatted)';
COMMENT ON COLUMN bank_transfers_beneficiary.description IS 'Additional information about the beneficiary (bank name, organization details, etc.)';
COMMENT ON COLUMN bank_transfers_beneficiary.is_frequent IS 'Marks frequently used beneficiaries for quick access in UI';
COMMENT ON COLUMN bank_transfers_beneficiary.is_active IS 'Soft delete flag - inactive beneficiaries are hidden from selection';
COMMENT ON COLUMN bank_transfers_beneficiary.remittance_information IS 'Default payment references, invoice numbers, or transaction-specific information';
COMMENT ON COLUMN bank_transfers_beneficiary.created_at IS 'Beneficiary registration timestamp';
COMMENT ON COLUMN bank_transfers_beneficiary.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - TransferTemplate
-- =============================================================================

COMMENT ON COLUMN bank_transfers_transfertemplate.id IS 'Unique identifier for transfer template';
COMMENT ON COLUMN bank_transfers_transfertemplate.company_id IS 'Company owner of this template (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_transfertemplate.name IS 'Descriptive name for the template (e.g., "Monthly Payroll", "Q1 VAT Payments")';
COMMENT ON COLUMN bank_transfers_transfertemplate.description IS 'Detailed description of when and how to use this template';
COMMENT ON COLUMN bank_transfers_transfertemplate.is_active IS 'Soft delete flag - inactive templates are hidden from selection';
COMMENT ON COLUMN bank_transfers_transfertemplate.created_at IS 'Template creation timestamp';
COMMENT ON COLUMN bank_transfers_transfertemplate.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - TemplateBeneficiary
-- =============================================================================

COMMENT ON COLUMN bank_transfers_templatebeneficiary.id IS 'Unique identifier for template-beneficiary relationship';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.template_id IS 'Reference to the transfer template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.beneficiary_id IS 'Reference to the beneficiary';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_amount IS 'Default payment amount for this beneficiary in this template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_remittance IS 'Default remittance information/memo for payments to this beneficiary';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.default_execution_date IS 'Default execution date for this beneficiary''s payments';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.order IS 'Display order of beneficiaries within the template';
COMMENT ON COLUMN bank_transfers_templatebeneficiary.is_active IS 'Whether this beneficiary is active in the template';

-- =============================================================================
-- COLUMN COMMENTS - Transfer
-- =============================================================================

COMMENT ON COLUMN bank_transfers_transfer.id IS 'Unique identifier for individual transfer';
COMMENT ON COLUMN bank_transfers_transfer.originator_account_id IS 'Reference to the bank account that will be debited';
COMMENT ON COLUMN bank_transfers_transfer.beneficiary_id IS 'Reference to the payment recipient';
COMMENT ON COLUMN bank_transfers_transfer.amount IS 'Transfer amount in the specified currency';
COMMENT ON COLUMN bank_transfers_transfer.currency IS 'ISO currency code (HUF, EUR, USD)';
COMMENT ON COLUMN bank_transfers_transfer.execution_date IS 'Requested date for the bank to process the transfer';
COMMENT ON COLUMN bank_transfers_transfer.remittance_info IS 'Payment reference/memo that appears on bank statements';
COMMENT ON COLUMN bank_transfers_transfer.template_id IS 'Reference to template if this transfer was created from a template';
COMMENT ON COLUMN bank_transfers_transfer.order IS 'Transfer order within batch for XML/CSV export generation';
COMMENT ON COLUMN bank_transfers_transfer.is_processed IS 'Marks transfers that have been included in generated XML/CSV files';
COMMENT ON COLUMN bank_transfers_transfer.notes IS 'Internal notes about this specific transfer';
COMMENT ON COLUMN bank_transfers_transfer.created_at IS 'Transfer creation timestamp';
COMMENT ON COLUMN bank_transfers_transfer.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - TransferBatch
-- =============================================================================

COMMENT ON COLUMN bank_transfers_transferbatch.id IS 'Unique identifier for transfer batch';
COMMENT ON COLUMN bank_transfers_transferbatch.company_id IS 'Company owner of this batch (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_transferbatch.name IS 'User-defined name for the batch (e.g., "Payroll 2025-01", "Supplier Payments Week 3")';
COMMENT ON COLUMN bank_transfers_transferbatch.description IS 'Detailed description of the batch contents and purpose';
COMMENT ON COLUMN bank_transfers_transferbatch.total_amount IS 'Sum of all transfer amounts in this batch';
COMMENT ON COLUMN bank_transfers_transferbatch.used_in_bank IS 'Flag indicating whether export file (XML/CSV) was uploaded to internet banking';
COMMENT ON COLUMN bank_transfers_transferbatch.bank_usage_date IS 'Timestamp when the export file was uploaded to bank system';
COMMENT ON COLUMN bank_transfers_transferbatch.order IS 'Display order for batch listing and downloads';
COMMENT ON COLUMN bank_transfers_transferbatch.xml_generated_at IS 'Timestamp when the export file was generated for this batch';
COMMENT ON COLUMN bank_transfers_transferbatch.batch_format IS 'Export file format: XML (SEPA XML) or KH_CSV (KH Bank CSV)';
COMMENT ON COLUMN bank_transfers_transferbatch.created_at IS 'Batch creation timestamp';
COMMENT ON COLUMN bank_transfers_transferbatch.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - TransferBatch_transfers junction
-- =============================================================================

COMMENT ON COLUMN bank_transfers_transferbatch_transfers.id IS 'Unique identifier for batch-transfer relationship';
COMMENT ON COLUMN bank_transfers_transferbatch_transfers.transferbatch_id IS 'Reference to the transfer batch';
COMMENT ON COLUMN bank_transfers_transferbatch_transfers.transfer_id IS 'Reference to the individual transfer';

-- =============================================================================
-- COLUMN COMMENTS - NAVConfiguration
-- =============================================================================

COMMENT ON COLUMN bank_transfers_navconfiguration.id IS 'Unique identifier for NAV configuration';
COMMENT ON COLUMN bank_transfers_navconfiguration.company_id IS 'Company reference for multi-tenant isolation (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_navconfiguration.tax_number IS 'Hungarian tax number for NAV authentication';
COMMENT ON COLUMN bank_transfers_navconfiguration.technical_user_login IS 'NAV API technical user login name';
COMMENT ON COLUMN bank_transfers_navconfiguration.technical_user_password IS 'NAV API password (encrypted with Fernet)';
COMMENT ON COLUMN bank_transfers_navconfiguration.signing_key IS 'NAV API signing key (encrypted with Fernet)';
COMMENT ON COLUMN bank_transfers_navconfiguration.exchange_key IS 'NAV API exchange key (encrypted with Fernet)';
COMMENT ON COLUMN bank_transfers_navconfiguration.company_encryption_key IS 'Company-specific encryption key (auto-generated, encrypted)';
COMMENT ON COLUMN bank_transfers_navconfiguration.api_environment IS 'API environment: test or production';
COMMENT ON COLUMN bank_transfers_navconfiguration.is_active IS 'Whether this configuration is active';
COMMENT ON COLUMN bank_transfers_navconfiguration.sync_enabled IS 'Whether automatic synchronization is enabled';
COMMENT ON COLUMN bank_transfers_navconfiguration.last_sync_timestamp IS 'Timestamp of last successful synchronization';
COMMENT ON COLUMN bank_transfers_navconfiguration.sync_frequency_hours IS 'How often to run automatic sync (hours)';
COMMENT ON COLUMN bank_transfers_navconfiguration.created_at IS 'Configuration creation timestamp';
COMMENT ON COLUMN bank_transfers_navconfiguration.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - Invoice (NAV Integration)
-- =============================================================================

COMMENT ON COLUMN bank_transfers_invoice.id IS 'Unique identifier for invoice record';
COMMENT ON COLUMN bank_transfers_invoice.company_id IS 'Company owner of this invoice (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_invoice.nav_invoice_number IS 'NAV invoice number (e.g., "A/A28700200/1180/00013")';
COMMENT ON COLUMN bank_transfers_invoice.invoice_direction IS 'Invoice direction: INBOUND or OUTBOUND';
COMMENT ON COLUMN bank_transfers_invoice.supplier_name IS 'Name of invoice supplier/issuer';
COMMENT ON COLUMN bank_transfers_invoice.supplier_tax_number IS 'Supplier tax identification number';
COMMENT ON COLUMN bank_transfers_invoice.customer_name IS 'Name of invoice customer/recipient';
COMMENT ON COLUMN bank_transfers_invoice.customer_tax_number IS 'Customer tax identification number';
COMMENT ON COLUMN bank_transfers_invoice.issue_date IS 'Invoice issue date';
COMMENT ON COLUMN bank_transfers_invoice.fulfillment_date IS 'Service/product fulfillment date';
COMMENT ON COLUMN bank_transfers_invoice.payment_due_date IS 'Payment due date';
COMMENT ON COLUMN bank_transfers_invoice.currency_code IS 'ISO currency code (HUF, EUR, USD)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_net_amount IS 'Net amount without VAT';
COMMENT ON COLUMN bank_transfers_invoice.invoice_vat_amount IS 'VAT amount';
COMMENT ON COLUMN bank_transfers_invoice.invoice_gross_amount IS 'Total gross amount (net + VAT)';
COMMENT ON COLUMN bank_transfers_invoice.original_request_version IS 'NAV API version used for original request';
COMMENT ON COLUMN bank_transfers_invoice.completion_date IS 'NAV processing completion timestamp';
COMMENT ON COLUMN bank_transfers_invoice.source IS 'Data source indicator (NAV_SYNC, MANUAL, etc.)';
COMMENT ON COLUMN bank_transfers_invoice.nav_transaction_id IS 'NAV system transaction identifier';
COMMENT ON COLUMN bank_transfers_invoice.last_modified_date IS 'Last modification date in NAV system';
COMMENT ON COLUMN bank_transfers_invoice.invoice_operation IS 'Invoice operation type (CREATE, STORNO, MODIFY)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_category IS 'Invoice category (NORMAL, SIMPLIFIED)';
COMMENT ON COLUMN bank_transfers_invoice.payment_method IS 'Payment method (TRANSFER, CASH, CARD)';
COMMENT ON COLUMN bank_transfers_invoice.payment_date IS 'Actual payment date';
COMMENT ON COLUMN bank_transfers_invoice.invoice_appearance IS 'Invoice format (PAPER, ELECTRONIC)';
COMMENT ON COLUMN bank_transfers_invoice.supplier_bank_account_number IS 'Supplier bank account number (extracted from XML)';
COMMENT ON COLUMN bank_transfers_invoice.customer_bank_account_number IS 'Customer bank account number (extracted from XML)';
COMMENT ON COLUMN bank_transfers_invoice.nav_source IS 'NAV data source indicator (OSZ, XML)';
COMMENT ON COLUMN bank_transfers_invoice.completeness_indicator IS 'Data completeness indicator from NAV';
COMMENT ON COLUMN bank_transfers_invoice.modification_index IS 'Modification sequence number';
COMMENT ON COLUMN bank_transfers_invoice.original_invoice_number IS 'Original invoice number (for STORNO invoices)';
COMMENT ON COLUMN bank_transfers_invoice.storno_of_id IS 'Reference to original invoice that this STORNO cancels';
COMMENT ON COLUMN bank_transfers_invoice.invoice_index IS 'Invoice sequence number in NAV system';
COMMENT ON COLUMN bank_transfers_invoice.batch_index IS 'Batch index number in NAV system';
COMMENT ON COLUMN bank_transfers_invoice.nav_creation_date IS 'Invoice creation timestamp in NAV system';
COMMENT ON COLUMN bank_transfers_invoice.invoice_net_amount_huf IS 'Net amount converted to HUF (for foreign currency invoices)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_vat_amount_huf IS 'VAT amount converted to HUF (for foreign currency invoices)';
COMMENT ON COLUMN bank_transfers_invoice.invoice_gross_amount_huf IS 'Gross amount converted to HUF (for foreign currency invoices)';
COMMENT ON COLUMN bank_transfers_invoice.nav_invoice_xml IS 'Complete NAV invoice XML data (base64 decoded)';
COMMENT ON COLUMN bank_transfers_invoice.nav_invoice_hash IS 'Hash/checksum of invoice XML for integrity verification';
COMMENT ON COLUMN bank_transfers_invoice.sync_status IS 'Data synchronization status (SUCCESS, PARTIAL, FAILED)';
COMMENT ON COLUMN bank_transfers_invoice.created_at IS 'Local record creation timestamp';
COMMENT ON COLUMN bank_transfers_invoice.updated_at IS 'Last local modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - InvoiceLineItem
-- =============================================================================

COMMENT ON COLUMN bank_transfers_invoicelineitem.id IS 'Unique identifier for invoice line item';
COMMENT ON COLUMN bank_transfers_invoicelineitem.invoice_id IS 'Reference to parent invoice (bank_transfers_invoice.id)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_number IS 'Line item sequence number (1, 2, 3...)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_description IS 'Description of product/service';
COMMENT ON COLUMN bank_transfers_invoicelineitem.quantity IS 'Quantity of product/service';
COMMENT ON COLUMN bank_transfers_invoicelineitem.unit_of_measure IS 'Unit of measurement (e.g., PIECE, LITER, HOUR)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.unit_price IS 'Price per unit before VAT';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_net_amount IS 'Line total net amount (quantity × unit_price)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.vat_rate IS 'VAT rate as decimal (e.g., 0.27 for 27%)';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_vat_amount IS 'VAT amount for this line';
COMMENT ON COLUMN bank_transfers_invoicelineitem.line_gross_amount IS 'Total gross amount for this line';
COMMENT ON COLUMN bank_transfers_invoicelineitem.product_code_category IS 'Product code classification category';
COMMENT ON COLUMN bank_transfers_invoicelineitem.product_code_value IS 'Product code value/identifier';
COMMENT ON COLUMN bank_transfers_invoicelineitem.created_at IS 'Line item extraction timestamp';
COMMENT ON COLUMN bank_transfers_invoicelineitem.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- COLUMN COMMENTS - InvoiceSyncLog
-- =============================================================================

COMMENT ON COLUMN bank_transfers_invoicesynclog.id IS 'Unique identifier for sync log entry';
COMMENT ON COLUMN bank_transfers_invoicesynclog.company_id IS 'Company for which sync was performed (bank_transfers_company.id)';
COMMENT ON COLUMN bank_transfers_invoicesynclog.sync_start_time IS 'Sync operation start timestamp';
COMMENT ON COLUMN bank_transfers_invoicesynclog.sync_end_time IS 'Sync operation completion timestamp';
COMMENT ON COLUMN bank_transfers_invoicesynclog.direction_synced IS 'Invoice direction synced (INBOUND, OUTBOUND, BOTH)';
COMMENT ON COLUMN bank_transfers_invoicesynclog.invoices_processed IS 'Total number of invoices processed';
COMMENT ON COLUMN bank_transfers_invoicesynclog.invoices_created IS 'Number of new invoices created';
COMMENT ON COLUMN bank_transfers_invoicesynclog.invoices_updated IS 'Number of existing invoices updated';
COMMENT ON COLUMN bank_transfers_invoicesynclog.errors_count IS 'Number of errors encountered';
COMMENT ON COLUMN bank_transfers_invoicesynclog.last_error_message IS 'Most recent error message encountered';
COMMENT ON COLUMN bank_transfers_invoicesynclog.sync_status IS 'Overall sync status (RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED)';
COMMENT ON COLUMN bank_transfers_invoicesynclog.created_at IS 'Sync log creation timestamp';
COMMENT ON COLUMN bank_transfers_invoicesynclog.updated_at IS 'Last modification timestamp';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify table comments
SELECT schemaname, tablename, obj_description(oid) AS table_comment
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE schemaname = 'public' AND tablename LIKE 'bank_transfers_%'
ORDER BY tablename;

-- Verify column comments
SELECT t.table_name, c.column_name, 
       col_description(pgc.oid, c.ordinal_position) AS column_comment
FROM information_schema.tables t
JOIN information_schema.columns c ON c.table_name = t.table_name
JOIN pg_class pgc ON pgc.relname = t.table_name
WHERE t.table_schema = 'public' 
  AND t.table_name LIKE 'bank_transfers_%'
ORDER BY t.table_name, c.ordinal_position;