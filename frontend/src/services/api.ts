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
  SupplierCategory,
  SupplierType,
  Supplier,
  Customer,
  ProductPrice,
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

// ============================================================================
// BASE_TABLES - Alaptáblák (Suppliers, Customers, Product Prices)
// ============================================================================

/**
 * Supplier Categories API - Beszállító kategóriák kezelése
 */
export const supplierCategoriesApi = {
  /**
   * Get all supplier categories with optional filtering.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to paginated category list
   */
  getAll: (params?: {
    search?: string;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => apiClient.get<ApiResponse<SupplierCategory>>('/supplier-categories/', { params }),

  /**
   * Get single supplier category by ID.
   *
   * @param id - Category ID
   * @returns Promise resolving to category
   */
  getById: async (id: number): Promise<SupplierCategory> => {
    const response = await apiClient.get(`/supplier-categories/${id}/`);
    return response.data;
  },

  /**
   * Create new supplier category.
   *
   * @param data - Category data (without ID and system fields, display_order is optional)
   * @returns Promise resolving to created category
   */
  create: async (
    data: Omit<SupplierCategory, 'id' | 'company' | 'company_name' | 'created_at' | 'updated_at' | 'display_order'> & { display_order?: number }
  ): Promise<SupplierCategory> => {
    const response = await apiClient.post('/supplier-categories/', data);
    return response.data;
  },

  /**
   * Update existing supplier category.
   *
   * @param id - Category ID
   * @param data - Partial category data to update
   * @returns Promise resolving to updated category
   */
  update: async (id: number, data: Partial<SupplierCategory>): Promise<SupplierCategory> => {
    const response = await apiClient.patch(`/supplier-categories/${id}/`, data);
    return response.data;
  },

  /**
   * Delete supplier category.
   *
   * @param id - Category ID
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/supplier-categories/${id}/`);
  },
};

/**
 * Supplier Types API - Beszállító típusok kezelése
 */
export const supplierTypesApi = {
  /**
   * Get all supplier types with optional filtering.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to paginated type list
   */
  getAll: (params?: {
    search?: string;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => apiClient.get<ApiResponse<SupplierType>>('/supplier-types/', { params }),

  /**
   * Get single supplier type by ID.
   *
   * @param id - Type ID
   * @returns Promise resolving to type
   */
  getById: async (id: number): Promise<SupplierType> => {
    const response = await apiClient.get(`/supplier-types/${id}/`);
    return response.data;
  },

  /**
   * Create new supplier type.
   *
   * @param data - Type data (without ID and system fields, display_order is optional)
   * @returns Promise resolving to created type
   */
  create: async (
    data: Omit<SupplierType, 'id' | 'company' | 'company_name' | 'created_at' | 'updated_at' | 'display_order'> & { display_order?: number }
  ): Promise<SupplierType> => {
    const response = await apiClient.post('/supplier-types/', data);
    return response.data;
  },

  /**
   * Update existing supplier type.
   *
   * @param id - Type ID
   * @param data - Partial type data to update
   * @returns Promise resolving to updated type
   */
  update: async (id: number, data: Partial<SupplierType>): Promise<SupplierType> => {
    const response = await apiClient.patch(`/supplier-types/${id}/`, data);
    return response.data;
  },

  /**
   * Delete supplier type.
   *
   * @param id - Type ID
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/supplier-types/${id}/`);
  },
};

/**
 * Suppliers API - Beszállítók kezelése
 */
export const suppliersApi = {
  /**
   * Get all suppliers with optional filtering.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to paginated supplier list
   */
  getAll: (params?: {
    search?: string;
    category?: string;
    type?: string;
    valid_only?: boolean;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => apiClient.get<ApiResponse<Supplier>>('/suppliers/', { params }),

  /**
   * Get single supplier by ID.
   *
   * @param id - Supplier ID
   * @returns Promise resolving to supplier
   */
  getById: async (id: number): Promise<Supplier> => {
    const response = await apiClient.get(`/suppliers/${id}/`);
    return response.data;
  },

  /**
   * Create new supplier.
   *
   * @param data - Supplier data (without ID and system fields)
   * @returns Promise resolving to created supplier
   */
  create: async (
    data: Omit<Supplier, 'id' | 'company' | 'company_name' | 'is_valid' | 'created_at' | 'updated_at'>
  ): Promise<Supplier> => {
    const response = await apiClient.post('/suppliers/', data);
    return response.data;
  },

  /**
   * Update existing supplier.
   *
   * @param id - Supplier ID
   * @param data - Partial supplier data to update
   * @returns Promise resolving to updated supplier
   */
  update: async (id: number, data: Partial<Supplier>): Promise<Supplier> => {
    const response = await apiClient.patch(`/suppliers/${id}/`, data);
    return response.data;
  },

  /**
   * Delete supplier.
   *
   * @param id - Supplier ID to delete
   * @returns Promise resolving when deletion is complete
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/suppliers/${id}/`);
  },
};

/**
 * Customers API - Vevők kezelése
 */
export const customersApi = {
  /**
   * Get all customers with optional filtering.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to paginated customer list
   */
  getAll: (params?: {
    search?: string;
    valid_only?: boolean;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => apiClient.get<ApiResponse<Customer>>('/customers/', { params }),

  /**
   * Get single customer by ID.
   *
   * @param id - Customer ID
   * @returns Promise resolving to customer
   */
  getById: async (id: number): Promise<Customer> => {
    const response = await apiClient.get(`/customers/${id}/`);
    return response.data;
  },

  /**
   * Create new customer.
   *
   * @param data - Customer data (without ID and system fields)
   * @returns Promise resolving to created customer
   */
  create: async (
    data: Omit<Customer, 'id' | 'company' | 'company_name' | 'is_valid' | 'created_at' | 'updated_at'>
  ): Promise<Customer> => {
    const response = await apiClient.post('/customers/', data);
    return response.data;
  },

  /**
   * Update existing customer.
   *
   * @param id - Customer ID
   * @param data - Partial customer data to update
   * @returns Promise resolving to updated customer
   */
  update: async (id: number, data: Partial<Customer>): Promise<Customer> => {
    const response = await apiClient.patch(`/customers/${id}/`, data);
    return response.data;
  },

  /**
   * Delete customer.
   *
   * @param id - Customer ID to delete
   * @returns Promise resolving when deletion is complete
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/customers/${id}/`);
  },
};

/**
 * Product Prices API - CONMED árak kezelése
 */
export const productPricesApi = {
  /**
   * Get all product prices with optional filtering.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to paginated product price list
   */
  getAll: (params?: {
    search?: string;
    product_value?: string;
    is_inventory_managed?: boolean;
    valid_only?: boolean;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => apiClient.get<ApiResponse<ProductPrice>>('/product-prices/', { params }),

  /**
   * Get single product price by ID.
   *
   * @param id - Product price ID
   * @returns Promise resolving to product price
   */
  getById: async (id: number): Promise<ProductPrice> => {
    const response = await apiClient.get(`/product-prices/${id}/`);
    return response.data;
  },

  /**
   * Create new product price.
   *
   * @param data - Product price data (without ID and system fields)
   * @returns Promise resolving to created product price
   */
  create: async (
    data: Omit<ProductPrice, 'id' | 'company' | 'company_name' | 'is_valid' | 'created_at' | 'updated_at'>
  ): Promise<ProductPrice> => {
    const response = await apiClient.post('/product-prices/', data);
    return response.data;
  },

  /**
   * Update existing product price.
   *
   * @param id - Product price ID
   * @param data - Partial product price data to update
   * @returns Promise resolving to updated product price
   */
  update: async (id: number, data: Partial<ProductPrice>): Promise<ProductPrice> => {
    const response = await apiClient.patch(`/product-prices/${id}/`, data);
    return response.data;
  },

  /**
   * Delete product price.
   *
   * @param id - Product price ID to delete
   * @returns Promise resolving when deletion is complete
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/product-prices/${id}/`);
  },
};

export default apiClient;
