export interface Beneficiary {
  id: number;
  name: string;
  account_number?: string | null; // Optional for VAT/tax-only beneficiaries
  vat_number?: string | null; // Hungarian VAT number for employee identification
  tax_number?: string | null; // Hungarian company tax number for corporate identification
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
  description?: string | null;
  is_active: boolean;
  beneficiary_count: number;
  created_at: string;
  updated_at: string;
  template_beneficiaries?: TemplateBeneficiary[];
}

export interface TemplateBeneficiary {
  id: number;
  template?: number;
  beneficiary: Beneficiary;
  default_amount?: string | number | null;
  default_remittance: string;
  order: number;
  is_active: boolean;
}

// Transfer for create/update operations (uses IDs)
export interface Transfer {
  id?: number;
  beneficiary: number;
  beneficiary_data?: Beneficiary; // Optional expanded data
  amount: string;
  currency: 'HUF' | 'EUR' | 'USD';
  execution_date: string;
  remittance_info: string;
  nav_invoice?: number | null; // Optional link to NAV invoice
  is_processed: boolean;
  created_at?: string;
}

// Transfer as returned from API (with expanded data)
export interface TransferWithBeneficiary {
  id?: number;
  beneficiary: Beneficiary; // Full beneficiary object
  amount: string;
  currency: 'HUF' | 'EUR' | 'USD';
  execution_date: string;
  remittance_info: string;
  nav_invoice?: number | null;
  is_processed: boolean;
  created_at?: string;
}

export interface TransferBatch {
  id: number;
  name: string;
  description?: string | null;
  transfers: TransferWithBeneficiary[]; // Batches return transfers with expanded beneficiary data
  total_amount: string;
  used_in_bank: boolean;
  bank_usage_date?: string | null;
  order: number;
  transfer_count: number;
  xml_filename: string;
  xml_generated_at?: string | null;
  created_at: string;
  batch_format?: string | null;
  batch_format_display?: string | null;
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
  invoice_direction: string; // 'INBOUND' | 'OUTBOUND' - using string for Zod v4 compatibility
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
  completion_date?: string | null;
  last_modified_date?: string | null;

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
  invoice_category?: string | null;
  invoice_appearance?: string | null;
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
  nav_source?: string | null;
  original_request_version?: string | null;

  // Partners (available in detail view)
  supplier_name?: string | null;
  customer_name?: string | null;
  supplier_tax_number?: string | null;
  customer_tax_number?: string | null;
  supplier_bank_account_number?: string | null;
  customer_bank_account_number?: string | null;
}
