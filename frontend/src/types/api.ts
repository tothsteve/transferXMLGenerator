export interface Beneficiary {
  id: number;
  name: string;
  account_number: string;
  bank_name: string;
  notes: string;
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
}

export interface TemplateBeneficiary {
  id: number;
  template: number;
  beneficiary: number;
  default_amount: string;
  default_remittance_info: string;
}

export interface Transfer {
  id?: number;
  beneficiary: number;
  beneficiary_data?: Beneficiary;
  amount: string;
  currency: 'HUF' | 'EUR' | 'USD';
  execution_date: string;
  remittance_info: string;
  is_processed: boolean;
  created_at?: string;
}

export interface TransferBatch {
  id: number;
  transfers: Transfer[];
  xml_filename: string;
  created_at: string;
  transfer_count: number;
}

export interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface BulkCreateTransferRequest {
  transfers: Omit<Transfer, 'id' | 'is_processed' | 'created_at'>[];
}

export interface GenerateXmlRequest {
  transfer_ids: number[];
}

export interface GenerateXmlResponse {
  xml_content: string;
  filename: string;
  batch_id: number;
}

export interface LoadTemplateResponse {
  template: TransferTemplate;
  transfers: Omit<Transfer, 'id' | 'is_processed' | 'created_at'>[];
}

export interface ExcelImportResponse {
  imported_count: number;
  errors: string[];
}