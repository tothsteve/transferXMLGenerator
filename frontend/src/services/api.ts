import axios from 'axios';
import {
  Beneficiary,
  BankAccount,
  TransferTemplate,
  Transfer,
  TransferBatch,
  ApiResponse,
  BulkCreateTransferRequest,
  GenerateXmlRequest,
  GenerateXmlResponse,
  GenerateKHExportResponse,
  LoadTemplateResponse,
  ExcelImportResponse,
  TrustedPartner,
  AvailablePartner,
  NAVInvoice,
} from '../types/api';
import {
  BankStatement,
  BankTransaction,
  OtherCost,
  BankStatementQueryParams,
  BankTransactionQueryParams,
  OtherCostQueryParams,
  BankStatementListResponse,
  BankTransactionListResponse,
  OtherCostListResponse,
  SupportedBanksResponse,
  UploadResponse,
  bankStatementListResponseSchema,
  bankTransactionListResponseSchema,
  otherCostListResponseSchema,
  supportedBanksResponseSchema,
  uploadResponseSchema,
  bankStatementSchema,
  bankTransactionSchema,
  otherCostSchema,
} from '../schemas/bankStatement.schemas';

const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? `${process.env.REACT_APP_BACKEND_URL || 'https://transferxmlgenerator-production.up.railway.app'}/api`
    : 'http://localhost:8002/api';

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;
axios.defaults.headers.common['Content-Type'] = 'application/json';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication API (separate from main apiClient to avoid interceptor issues)
export const authApi = {
  login: (username: string, password: string) => axios.post('/auth/login/', { username, password }),

  register: (data: any) => axios.post('/auth/register/', data),

  refreshToken: (refreshToken: string) =>
    axios.post('/auth/token/refresh/', { refresh: refreshToken }),

  switchCompany: (companyId: number) =>
    apiClient.post('/auth/switch_company/', { company_id: companyId }),

  getProfile: () => apiClient.get('/auth/profile/'),
};

// Beneficiaries API
export const beneficiariesApi = {
  getAll: (params?: {
    search?: string;
    is_frequent?: boolean;
    is_active?: boolean;
    page?: number;
    ordering?: string;
  }) => apiClient.get<ApiResponse<Beneficiary>>('/beneficiaries/', { params }),

  getFrequent: () => apiClient.get<Beneficiary[]>('/beneficiaries/frequent/'),

  getById: (id: number) => apiClient.get<Beneficiary>(`/beneficiaries/${id}/`),

  create: (data: Omit<Beneficiary, 'id'>) => apiClient.post<Beneficiary>('/beneficiaries/', data),

  update: (id: number, data: Partial<Beneficiary>) =>
    apiClient.put<Beneficiary>(`/beneficiaries/${id}/`, data),

  delete: (id: number) => apiClient.delete(`/beneficiaries/${id}/`),
};

// Templates API
export const templatesApi = {
  getAll: (params?: { show_inactive?: boolean }) =>
    apiClient.get<ApiResponse<TransferTemplate>>('/templates/', { params }),

  getById: (id: number) => apiClient.get<TransferTemplate>(`/templates/${id}/`),

  create: (
    data: Omit<TransferTemplate, 'id' | 'beneficiary_count' | 'created_at' | 'updated_at'>
  ) => apiClient.post<TransferTemplate>('/templates/', data),

  update: (id: number, data: Partial<TransferTemplate>) =>
    apiClient.put<TransferTemplate>(`/templates/${id}/`, data),

  delete: (id: number) => apiClient.delete(`/templates/${id}/`),

  loadTransfers: (
    id: number,
    data: {
      template_id: number;
      originator_account_id: number;
      execution_date: string;
    }
  ) => apiClient.post<LoadTemplateResponse>(`/templates/${id}/load_transfers/`, data),

  addBeneficiary: (
    templateId: number,
    data: {
      beneficiary_id: number;
      default_amount?: number;
      default_remittance?: string;
      order?: number;
      is_active?: boolean;
    }
  ) => apiClient.post(`/templates/${templateId}/add_beneficiary/`, data),

  updateBeneficiary: (
    templateId: number,
    data: {
      beneficiary_id: number;
      default_amount?: number;
      default_remittance?: string;
      order?: number;
      is_active?: boolean;
    }
  ) => apiClient.put(`/templates/${templateId}/update_beneficiary/`, data),

  removeBeneficiary: (templateId: number, beneficiaryId: number) =>
    apiClient.delete(`/templates/${templateId}/remove_beneficiary/`, {
      data: { beneficiary_id: beneficiaryId },
    }),
};

// Transfers API
export const transfersApi = {
  getAll: (params?: {
    page?: number;
    page_size?: number;
    is_processed?: boolean;
    template_id?: number;
    execution_date_from?: string;
    execution_date_to?: string;
    ordering?: string;
  }) => apiClient.get<ApiResponse<Transfer>>('/transfers/', { params }),

  getById: (id: number) => apiClient.get<Transfer>(`/transfers/${id}/`),

  bulkCreate: (data: BulkCreateTransferRequest) =>
    apiClient.post<Transfer[]>('/transfers/bulk_create/', data),

  update: (id: number, data: Partial<Transfer>) =>
    apiClient.put<Transfer>(`/transfers/${id}/`, data),

  partialUpdate: (id: number, data: Partial<Transfer>) =>
    apiClient.patch<Transfer>(`/transfers/${id}/`, data),

  delete: (id: number) => apiClient.delete(`/transfers/${id}/`),

  generateXml: (data: GenerateXmlRequest) =>
    apiClient.post<GenerateXmlResponse>('/transfers/generate_xml/', data),

  generateKHExport: (data: GenerateXmlRequest) =>
    apiClient.post<GenerateKHExportResponse>('/transfers/generate_kh_export/', data),
};

// Bank Accounts API
export const bankAccountsApi = {
  getDefault: () => apiClient.get<BankAccount>('/bank-accounts/default/'),

  getAll: () => apiClient.get<ApiResponse<BankAccount>>('/bank-accounts/'),

  create: (data: Omit<BankAccount, 'id'>) => apiClient.post<BankAccount>('/bank-accounts/', data),

  update: (id: number, data: Partial<BankAccount>) =>
    apiClient.put<BankAccount>(`/bank-accounts/${id}/`, data),

  delete: (id: number) => apiClient.delete(`/bank-accounts/${id}/`),
};

// Batches API
export const batchesApi = {
  getAll: () => apiClient.get<ApiResponse<TransferBatch>>('/batches/'),

  getById: (id: number) => apiClient.get<TransferBatch>(`/batches/${id}/`),

  delete: (id: number) => apiClient.delete(`/batches/${id}/`),

  downloadXml: (id: number) =>
    apiClient.get(`/batches/${id}/download_xml/`, { responseType: 'blob' }),

  markUsedInBank: (id: number) => apiClient.post(`/batches/${id}/mark_used_in_bank/`),

  markUnusedInBank: (id: number) => apiClient.post(`/batches/${id}/mark_unused_in_bank/`),
};

// Upload API
export const uploadApi = {
  uploadExcel: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<ExcelImportResponse>('/upload/excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// User Management API
export const userManagementApi = {
  getCompanyUsers: () => apiClient.get<any[]>('/company/users/'),

  updateUserRole: (userId: number, role: 'ADMIN' | 'USER') =>
    apiClient.put(`/company/users/${userId}/`, { role }),

  removeUser: (userId: number) => apiClient.delete(`/company/users/${userId}/`),
};

// NAV Invoices API
export const navInvoicesApi = {
  getAll: (params?: {
    search?: string;
    direction?: string;
    currency?: string;
    page?: number;
    page_size?: number;
    ordering?: string;
    hide_storno_invoices?: boolean;
  }) => apiClient.get<ApiResponse<NAVInvoice>>('/nav/invoices/', { params }),

  getById: (id: number) => apiClient.get(`/nav/invoices/${id}/`),

  getStats: () => apiClient.get('/nav/invoices/stats/'),

  // Bulk payment status update endpoints
  bulkMarkUnpaid: (invoice_ids: number[]) =>
    apiClient.post('/nav/invoices/bulk_mark_unpaid/', { invoice_ids }),

  bulkMarkPrepared: (invoice_ids: number[]) =>
    apiClient.post('/nav/invoices/bulk_mark_prepared/', { invoice_ids }),

  bulkMarkPaid: (data: {
    invoice_ids?: number[];
    payment_date?: string;
    invoices?: { invoice_id: number; payment_date: string }[];
  }) => apiClient.post('/nav/invoices/bulk_mark_paid/', data),

  // Generate transfers from NAV invoices with tax number fallback
  generateTransfers: (data: {
    invoice_ids: number[];
    originator_account_id: number;
    execution_date: string;
  }) => apiClient.post('/nav/invoices/generate_transfers/', data),
};

// Trusted Partners API
export const trustedPartnersApi = {
  getAll: (params?: {
    search?: string;
    is_active?: boolean;
    auto_pay?: boolean;
    ordering?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<ApiResponse<TrustedPartner>>('/trusted-partners/', { params }),

  getById: (id: number) => apiClient.get<TrustedPartner>(`/trusted-partners/${id}/`),

  create: (
    data: Omit<
      TrustedPartner,
      'id' | 'invoice_count' | 'last_invoice_date' | 'created_at' | 'updated_at'
    >
  ) => apiClient.post<TrustedPartner>('/trusted-partners/', data),

  update: (
    id: number,
    data: Partial<
      Omit<
        TrustedPartner,
        'id' | 'invoice_count' | 'last_invoice_date' | 'created_at' | 'updated_at'
      >
    >
  ) => apiClient.put<TrustedPartner>(`/trusted-partners/${id}/`, data),

  partialUpdate: (
    id: number,
    data: Partial<
      Omit<
        TrustedPartner,
        'id' | 'invoice_count' | 'last_invoice_date' | 'created_at' | 'updated_at'
      >
    >
  ) => apiClient.patch<TrustedPartner>(`/trusted-partners/${id}/`, data),

  delete: (id: number) => apiClient.delete(`/trusted-partners/${id}/`),

  getAvailablePartners: (params?: {
    search?: string;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) =>
    apiClient.get<ApiResponse<AvailablePartner>>('/trusted-partners/available_partners/', {
      params,
    }),
};

/**
 * Bank Statements API
 *
 * Endpoints for managing bank statement uploads, parsing, and transactions.
 * All responses are validated with Zod schemas for type safety.
 */
export const bankStatementsApi = {
  /**
   * Get paginated list of bank statements with filtering.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to validated bank statement list
   */
  getAll: async (params?: BankStatementQueryParams): Promise<BankStatementListResponse> => {
    const response = await apiClient.get('/bank-statements/', { params });
    return bankStatementListResponseSchema.parse(response.data);
  },

  /**
   * Get single bank statement by ID.
   *
   * @param id - Bank statement ID
   * @returns Promise resolving to validated bank statement
   */
  getById: async (id: number): Promise<BankStatement> => {
    const response = await apiClient.get(`/bank-statements/${id}/`);
    return bankStatementSchema.parse(response.data);
  },

  /**
   * Upload bank statement file (PDF/CSV/XML).
   *
   * @param file - File to upload
   * @returns Promise resolving to upload response with created statement
   */
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/bank-statements/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return uploadResponseSchema.parse(response.data);
  },

  /**
   * Get list of supported banks and their file formats.
   *
   * @returns Promise resolving to array of supported banks
   */
  getSupportedBanks: async (): Promise<SupportedBanksResponse> => {
    const response = await apiClient.get('/bank-statements/supported_banks/');
    return supportedBanksResponseSchema.parse(response.data);
  },

  /**
   * Delete bank statement and all its transactions.
   *
   * @param id - Bank statement ID to delete
   * @returns Promise resolving when deletion is complete
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/bank-statements/${id}/`);
  },
};

/**
 * Bank Transactions API
 *
 * Endpoints for managing transactions within bank statements.
 */
export const bankTransactionsApi = {
  /**
   * Get paginated list of transactions for a statement.
   *
   * @param statementId - Parent bank statement ID
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to validated transaction list
   */
  getAll: async (
    statementId: number,
    params?: BankTransactionQueryParams
  ): Promise<BankTransactionListResponse> => {
    const response = await apiClient.get(`/bank-transactions/`, {
      params: {
        ...params,
        statement_id: statementId,
      },
    });
    return bankTransactionListResponseSchema.parse(response.data);
  },

  /**
   * Get single transaction by ID.
   *
   * @param id - Transaction ID
   * @returns Promise resolving to validated transaction
   */
  getById: async (id: number): Promise<BankTransaction> => {
    const response = await apiClient.get(`/bank-transactions/${id}/`);
    return bankTransactionSchema.parse(response.data);
  },

  /**
   * Manually match transaction to invoice.
   *
   * @param transactionId - Transaction ID
   * @param invoiceId - Invoice ID to match
   * @returns Promise resolving to updated transaction
   */
  matchInvoice: async (transactionId: number, invoiceId: number): Promise<BankTransaction> => {
    const response = await apiClient.post(`/bank-transactions/${transactionId}/match_invoice/`, {
      invoice_id: invoiceId,
    });
    return bankTransactionSchema.parse(response.data);
  },

  /**
   * Remove invoice match from transaction.
   *
   * @param transactionId - Transaction ID
   * @returns Promise resolving to updated transaction
   */
  unmatch: async (transactionId: number): Promise<BankTransaction> => {
    const response = await apiClient.post(`/bank-transactions/${transactionId}/unmatch/`);
    return bankTransactionSchema.parse(response.data);
  },
};

/**
 * Other Costs API
 *
 * Endpoints for managing categorized expense records.
 */
export const otherCostsApi = {
  /**
   * Get paginated list of other costs with filtering.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to validated other costs list
   */
  getAll: async (params?: OtherCostQueryParams): Promise<OtherCostListResponse> => {
    const response = await apiClient.get('/other-costs/', { params });
    return otherCostListResponseSchema.parse(response.data);
  },

  /**
   * Get single other cost by ID.
   *
   * @param id - Other cost ID
   * @returns Promise resolving to validated other cost
   */
  getById: async (id: number): Promise<OtherCost> => {
    const response = await apiClient.get(`/other-costs/${id}/`);
    return otherCostSchema.parse(response.data);
  },

  /**
   * Create new other cost record.
   *
   * @param data - Other cost data (without ID)
   * @returns Promise resolving to created other cost
   */
  create: async (data: Omit<OtherCost, 'id' | 'created_at' | 'updated_at'>): Promise<OtherCost> => {
    const response = await apiClient.post('/other-costs/', data);
    return otherCostSchema.parse(response.data);
  },

  /**
   * Update existing other cost.
   *
   * @param id - Other cost ID
   * @param data - Partial other cost data to update
   * @returns Promise resolving to updated other cost
   */
  update: async (id: number, data: Partial<OtherCost>): Promise<OtherCost> => {
    const response = await apiClient.patch(`/other-costs/${id}/`, data);
    return otherCostSchema.parse(response.data);
  },

  /**
   * Delete other cost record.
   *
   * @param id - Other cost ID to delete
   * @returns Promise resolving when deletion is complete
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/other-costs/${id}/`);
  },
};

export default apiClient;
