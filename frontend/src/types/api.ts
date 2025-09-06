export interface Beneficiary {
  id: number;
  name: string;
  account_number: string;
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
  description?: string;
  is_active: boolean;
  beneficiary_count: number;
  created_at: string;
  updated_at: string;
  template_beneficiaries?: TemplateBeneficiary[];
}

export interface TemplateBeneficiary {
  id: number;
  template: number;
  beneficiary: Beneficiary;
  default_amount?: number;
  default_remittance: string;
  order: number;
  is_active: boolean;
}

export interface Transfer {
  id?: number;
  beneficiary: number;
  beneficiary_data?: Beneficiary;
  amount: string;
  currency: 'HUF' | 'EUR' | 'USD';
  execution_date: string;
  remittance_info: string;
  nav_invoice?: number | null; // Optional link to NAV invoice
  is_processed: boolean;
  created_at?: string;
}

export interface TransferBatch {
  id: number;
  name: string;
  description?: string;
  transfers: Transfer[];
  total_amount: string;
  used_in_bank: boolean;
  bank_usage_date?: string;
  order: number;
  transfer_count: number;
  xml_filename: string;
  xml_generated_at?: string;
  created_at: string;
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
  batch_name?: string;
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
  content_encoding?: string;  // Optional field for base64 encoding indicator
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
  last_invoice_date_formatted?: string;
  created_at: string;
  updated_at: string;
}

export interface AvailablePartner {
  partner_name: string;
  tax_number: string;
  invoice_count: number;
  last_invoice_date: string | null;
}