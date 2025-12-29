export interface Beneficiary {
  id: number;
  name: string;
  account_number?: string | null | undefined; // Optional for VAT/tax-only beneficiaries
  vat_number?: string | null | undefined; // Hungarian VAT number for employee identification
  tax_number?: string | null | undefined; // Hungarian company tax number for corporate identification
  description: string;
  remittance_information: string;
  is_frequent: boolean;
  is_active: boolean;
}

export interface BankAccount {
  id: number;
  name: string;
  account_number: string;
  bank_name: string;
  is_default: boolean;
}

export interface TransferTemplate {
  id: number;
  name: string;
  description?: string | null | undefined;
  is_active: boolean;
  beneficiary_count: number;
  created_at: string;
  updated_at: string;
  template_beneficiaries?: TemplateBeneficiary[] | undefined;
}

export interface TemplateBeneficiary {
  id: number;
  template?: number | undefined;
  beneficiary: Beneficiary;
  default_amount?: string | number | null | undefined;
  default_remittance: string;
  order: number;
  is_active: boolean;
}

// Transfer for create/update operations (uses IDs)
export interface Transfer {
  id?: number | undefined;
  beneficiary: number;
  beneficiary_data?: Beneficiary | undefined; // Optional expanded data
  amount: string;
  currency: 'HUF' | 'EUR' | 'USD';
  execution_date: string;
  remittance_info: string;
  nav_invoice?: number | null | undefined; // Optional link to NAV invoice
  order?: number | undefined;
  is_processed: boolean;
  created_at?: string | undefined;
}

// Transfer as returned from API (with expanded data)
export interface TransferWithBeneficiary {
  id?: number | undefined;
  beneficiary: Beneficiary; // Full beneficiary object
  amount: string;
  currency: 'HUF' | 'EUR' | 'USD';
  execution_date: string;
  remittance_info: string;
  nav_invoice?: number | null | undefined;
  order?: number | undefined;
  is_processed: boolean;
  created_at?: string | undefined;
}

export interface TransferBatch {
  id: number;
  name: string;
  description?: string | null | undefined;
  transfers: TransferWithBeneficiary[]; // Batches return transfers with expanded beneficiary data
  total_amount: string;
  used_in_bank: boolean;
  bank_usage_date?: string | null | undefined;
  order: number;
  transfer_count: number;
  xml_filename: string;
  xml_generated_at?: string | null | undefined;
  created_at: string;
  batch_format?: string | null | undefined;
  batch_format_display?: string | null | undefined;
}

export interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CreateTransferData {
  originator_account_id: number;
  beneficiary_id: number;
  amount: string;
  currency: 'HUF' | 'EUR' | 'USD';
  execution_date: string;
  remittance_info: string;
  order: number;
}

export interface BulkCreateTransferRequest {
  transfers: CreateTransferData[];
}

export interface GenerateXmlRequest {
  transfer_ids: number[];
  batch_name?: string | null;
}

export interface GenerateXmlResponse {
  xml: string;
  transfer_count: number;
  total_amount: string;
}

export interface LoadTemplateResponse {
  template: TransferTemplate;
  transfers: Omit<Transfer, 'id' | 'is_processed' | 'created_at'>[];
}

export interface ExcelImportResponse {
  imported_count: number;
  errors: string[];
}

export interface GenerateKHExportResponse {
  content: string;
  filename: string;
  encoding: string;
  content_encoding?: string | null; // Optional field for base64 encoding indicator
  transfer_count: number;
  total_amount: string;
}

export interface TrustedPartner {
  id: number;
  partner_name: string;
  tax_number: string;
  is_active: boolean;
  auto_pay: boolean;
  invoice_count: number;
  last_invoice_date: string | null;
  last_invoice_date_formatted?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AvailablePartner {
  partner_name: string;
  tax_number: string;
  invoice_count: number;
  last_invoice_date: string | null;
}

export interface NAVInvoice {
  id: number;
  nav_invoice_number: string;
  invoice_direction: 'INBOUND' | 'OUTBOUND';
  invoice_direction_display: string;
  partner_name: string;
  partner_tax_number: string;

  // Dates
  issue_date: string;
  issue_date_formatted: string;
  fulfillment_date: string | null;
  fulfillment_date_formatted: string | null;
  payment_due_date: string | null;
  payment_due_date_formatted: string | null;
  payment_date: string | null;
  payment_date_formatted: string | null;
  completion_date?: string | null | undefined;
  last_modified_date?: string | null | undefined;

  // Financial
  currency_code: string;
  invoice_net_amount: number;
  invoice_net_amount_formatted: string;
  invoice_vat_amount: number;
  invoice_vat_amount_formatted: string;
  invoice_gross_amount: number;
  invoice_gross_amount_formatted: string;

  // Business
  invoice_operation: string | null;
  invoice_category: string | null;
  invoice_appearance?: string | null | undefined;
  payment_method: string | null;
  original_invoice_number: string | null;
  payment_status: {
    status: string;
    label: string;
    icon: string;
    class: string;
  };
  payment_status_date: string | null;
  payment_status_date_formatted: string | null;
  auto_marked_paid: boolean;
  is_overdue: boolean;
  is_paid: boolean;

  // System
  sync_status: string;
  created_at: string;

  // NAV metadata (available in detail view)
  nav_source?: string | null | undefined;
  original_request_version?: string | null | undefined;

  // Partners (available in detail view)
  supplier_name?: string | null | undefined;
  customer_name?: string | null | undefined;
  supplier_tax_number?: string | null | undefined;
  customer_tax_number?: string | null | undefined;
  supplier_bank_account_number?: string | null | undefined;
  customer_bank_account_number?: string | null | undefined;
}

// ==================== Billingo Invoice Synchronization ====================

export interface BillingoInvoiceItem {
  id: number;
  product_id: number;
  name: string;
  quantity: string;
  unit: string;
  net_unit_price: string;
  net_amount: string;
  gross_amount: string;
  vat: string;
  entitlement: string | null;
  created_at: string;
  updated_at: string;
}

export interface BillingoRelatedDocument {
  id: number;
  related_invoice_id: number;
  related_invoice_number: string;
  created_at: string;
  updated_at: string;
}

export interface BillingoInvoice {
  id: number;
  company: number;
  company_name: string;
  invoice_number: string;
  type: string;
  payment_status: string;
  payment_method: string;
  gross_total: string;
  gross_total_formatted: string;
  net_total: string | null;
  net_total_formatted: string | null;
  currency: string;
  invoice_date: string;
  invoice_date_formatted: string;
  due_date: string;
  paid_date: string;
  partner_name: string;
  partner_tax_number: string;
  cancelled: boolean;
  item_count?: number; // Optional: list view has this, detail view has items array instead
  related_documents_count?: number; // Optional: list view has this, detail view has related_documents array instead
  related_invoice_number?: string | null; // Optional: first related invoice number for list view
  created_at: string;
}

export interface BillingoInvoiceDetail extends BillingoInvoice {
  correction_type: string;
  block_id: number;
  conversion_rate: string;
  fulfillment_date: string;
  fulfillment_date_formatted: string;
  due_date_formatted: string;
  paid_date_formatted: string;
  organization_name: string;
  organization_tax_number: string;
  organization_bank_account_number: string;
  organization_bank_account_iban: string;
  organization_swift: string;
  partner_id: number;
  partner_iban: string;
  partner_swift: string;
  partner_account_number: string;
  comment: string;
  online_szamla_status: string;
  items: BillingoInvoiceItem[];
  related_documents: BillingoRelatedDocument[];
  updated_at: string;
  last_modified: string;
}

export interface CompanyBillingoSettings {
  id: number;
  company: number;
  company_name: string;
  has_api_key: boolean;
  last_sync_time: string | null;
  last_sync_time_formatted: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyBillingoSettingsInput {
  api_key_input?: string;
  is_active: boolean;
}

export interface BillingoSyncLog {
  id: number;
  company: number;
  company_name: string;
  sync_type: 'MANUAL' | 'AUTOMATIC';
  sync_type_display: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'PARTIAL';
  status_display: string;
  invoices_processed: number;
  invoices_created: number;
  invoices_updated: number;
  invoices_skipped: number;
  items_extracted: number;
  api_calls_made: number;
  sync_duration_seconds: number | null;
  duration_formatted: string | null;
  started_at: string;
  started_at_formatted: string;
  completed_at: string | null;
  completed_at_formatted: string | null;
  errors: string;
  errors_parsed: Array<{
    invoice_id: number;
    invoice_number: string;
    error: string;
  }>;
}

export interface BillingoSyncTriggerResponse {
  status: string;
  invoices_processed: number;
  invoices_created: number;
  invoices_updated: number;
  invoices_skipped: number;
  items_extracted: number;
  api_calls: number;
  duration_seconds: number;
  errors: Array<{
    invoice_id: number;
    invoice_number: string;
    error: string;
  }>;
}

export interface BillingoSpending {
  id: number;
  company: number;
  company_name?: string;
  organization_id: number;
  category: 'advertisement' | 'development' | 'education_and_training' | 'other' | 'overheads' | 'service' | 'stock' | 'tangible_assets';
  category_display?: string;
  paid_at: string | null;
  fulfillment_date: string;
  invoice_number: string;
  currency: string;
  conversion_rate: number;
  total_gross: number;
  total_gross_local: number;
  total_vat_amount: number;
  total_vat_amount_local: number;
  invoice_date: string;
  due_date: string;
  payment_method: string;
  partner_id?: number | null;
  partner_name: string;
  partner_tax_code: string;
  partner_address?: object | null;
  partner_iban?: string;
  partner_account_number?: string;
  comment?: string;
  is_created_by_nav: boolean;
  is_paid?: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// BASE_TABLES - Alaptáblák (Suppliers, Customers, Product Prices)
// ============================================================================

export interface SupplierCategory {
  id: number;
  company: number;
  company_name?: string | undefined;
  name: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface SupplierType {
  id: number;
  company: number;
  company_name?: string | undefined;
  name: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface Supplier {
  id: number;
  company: number;
  company_name?: string | undefined;
  partner_name: string;
  category?: number | null | undefined;  // FK to SupplierCategory
  category_name?: string | null | undefined;  // Category name for display
  type?: number | null | undefined;  // FK to SupplierType
  type_name?: string | null | undefined;  // Type name for display
  valid_from?: string | null | undefined;
  valid_to?: string | null | undefined;
  is_valid?: boolean | undefined;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  company: number;
  company_name?: string | undefined;
  customer_name: string;
  cashflow_adjustment: number;
  valid_from?: string | null | undefined;
  valid_to?: string | null | undefined;
  is_valid?: boolean | undefined;
  created_at: string;
  updated_at: string;
}

export interface ProductPrice {
  id: number;
  company: number;
  company_name?: string | undefined;
  product_value: string;
  product_description: string;
  uom?: string | null | undefined;
  uom_hun?: string | null | undefined;
  purchase_price_usd?: string | null | undefined;
  purchase_price_huf?: string | null | undefined;
  markup?: string | null | undefined;
  sales_price_huf?: string | null | undefined;
  cap_disp?: string | null | undefined;
  is_inventory_managed: boolean;
  valid_from?: string | null | undefined;
  valid_to?: string | null | undefined;
  is_valid?: boolean | undefined;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Bank Statement Import - Batch Invoice Matching
// ============================================================================

export interface BankTransactionInvoiceMatch {
  id: number;
  transaction: number;
  invoice: number;
  invoice_details?: {
    id: number;
    invoice_number: string;
    supplier_name: string;
    supplier_tax_number: string;
    gross_amount: string;
    payment_due_date: string | null;
    payment_status: string;
  };
  match_confidence: string;
  match_method: string;
  matched_at: string;
  matched_by: number | null;
  match_notes: string;
}

export interface MatchedInvoiceDetail {
  id: number;
  invoice_number: string;
  supplier_name: string;
  supplier_tax_number: string;
  gross_amount: string;
  payment_due_date: string | null;
  payment_status: string;
  match_confidence: string;
  match_method: string;
  match_notes: string;
}

export interface BankTransaction {
  id: number;
  bank_statement: number;
  statement_details?: {
    id: number;
    bank_name: string;
    account_number: string;
    period_from: string | null;
    period_to: string | null;
  };

  // Transaction details
  transaction_type: 'DEBIT' | 'CREDIT';
  booking_date: string;
  value_date: string;
  amount: string;
  currency: string;
  description: string;
  short_description?: string;
  payment_id?: string | null;
  transaction_id?: string | null;

  // Payer/Beneficiary details
  payer_name?: string | null;
  payer_iban?: string | null;
  payer_account_number?: string | null;
  payer_bic?: string | null;
  beneficiary_name?: string | null;
  beneficiary_iban?: string | null;
  beneficiary_account_number?: string | null;
  beneficiary_bic?: string | null;

  // Reference and additional info
  reference?: string | null;
  partner_id?: string | null;
  transaction_type_code?: string | null;
  fee_amount?: string | null;

  // Card/Merchant details (for card transactions)
  card_number?: string | null;
  merchant_name?: string | null;
  merchant_location?: string | null;

  // Original amount (for foreign currency transactions)
  original_amount?: string | null;
  original_currency?: string | null;

  // Single invoice match (DEPRECATED - use matched_invoices_details instead)
  matched_invoice?: number | null;
  matched_invoice_details?: {
    id: number;
    invoice_number: string;
    supplier_name: string;
    supplier_tax_number?: string;
    customer_name?: string;
    customer_tax_number?: string;
    gross_amount: string;
    payment_due_date: string | null;
    payment_status: string;
  } | null;

  // Batch invoice matching (NEW)
  matched_invoices_details: MatchedInvoiceDetail[];
  is_batch_match: boolean;
  total_matched_amount: string | null;

  // Match metadata
  match_confidence: string;
  match_method: string;

  // Transfer matching
  matched_transfer?: number | null;
  matched_transfer_batch?: number | null;

  // Reimbursement matching
  matched_reimbursement?: number | null;
  matched_reimbursement_details?: {
    id: number;
    bank_statement: number;
    transaction_type: string;
    booking_date: string;
    amount: string;
    currency: string;
    description: string;
    partner_name: string;
  } | null;

  // Other cost linkage
  has_other_cost: boolean;

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface BatchMatchInvoicesRequest {
  invoice_ids: number[];
}

export interface BatchMatchInvoicesResponse {
  message: string;
  transaction_id: number;
  batch_match: boolean;
  invoice_count: number;
  matched_invoices: Array<{
    invoice_id: number;
    invoice_number: string;
    amount: string;
  }>;
  total_matched_amount: string;
  confidence: string;
  method: string;
}

export interface UnmatchResponse {
  message: string;
  was_batch_match: boolean;
  invoices_unmatched: number;
}
