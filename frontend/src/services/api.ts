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
} from '../types/api';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? `${process.env.REACT_APP_BACKEND_URL || 'https://transferxmlgenerator-production.up.railway.app'}/api`
  : 'http://localhost:8000/api';

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
  login: (username: string, password: string) =>
    axios.post('/auth/login/', { username, password }),
  
  register: (data: any) =>
    axios.post('/auth/register/', data),
  
  refreshToken: (refreshToken: string) =>
    axios.post('/auth/token/refresh/', { refresh: refreshToken }),
  
  switchCompany: (companyId: number) =>
    apiClient.post('/auth/switch_company/', { company_id: companyId }),
  
  getProfile: () =>
    apiClient.get('/auth/profile/'),
};

// Beneficiaries API
export const beneficiariesApi = {
  getAll: (params?: { search?: string; is_frequent?: boolean; is_active?: boolean; page?: number; ordering?: string }) =>
    apiClient.get<ApiResponse<Beneficiary>>('/beneficiaries/', { params }),
  
  getFrequent: () =>
    apiClient.get<Beneficiary[]>('/beneficiaries/frequent/'),
  
  getById: (id: number) =>
    apiClient.get<Beneficiary>(`/beneficiaries/${id}/`),
  
  create: (data: Omit<Beneficiary, 'id'>) =>
    apiClient.post<Beneficiary>('/beneficiaries/', data),
  
  update: (id: number, data: Partial<Beneficiary>) =>
    apiClient.put<Beneficiary>(`/beneficiaries/${id}/`, data),
  
  delete: (id: number) =>
    apiClient.delete(`/beneficiaries/${id}/`),
};

// Templates API
export const templatesApi = {
  getAll: () =>
    apiClient.get<ApiResponse<TransferTemplate>>('/templates/'),
  
  getById: (id: number) =>
    apiClient.get<TransferTemplate>(`/templates/${id}/`),
  
  create: (data: Omit<TransferTemplate, 'id' | 'beneficiary_count' | 'created_at' | 'updated_at'>) =>
    apiClient.post<TransferTemplate>('/templates/', data),
  
  update: (id: number, data: Partial<TransferTemplate>) =>
    apiClient.put<TransferTemplate>(`/templates/${id}/`, data),
  
  delete: (id: number) =>
    apiClient.delete(`/templates/${id}/`),
  
  loadTransfers: (id: number, data: {
    template_id: number;
    originator_account_id: number;
    execution_date: string;
  }) =>
    apiClient.post<LoadTemplateResponse>(`/templates/${id}/load_transfers/`, data),
  
  addBeneficiary: (templateId: number, data: {
    beneficiary_id: number;
    default_amount?: number;
    default_remittance?: string;
    order?: number;
    is_active?: boolean;
  }) =>
    apiClient.post(`/templates/${templateId}/add_beneficiary/`, data),
  
  updateBeneficiary: (templateId: number, data: {
    beneficiary_id: number;
    default_amount?: number;
    default_remittance?: string;
    order?: number;
    is_active?: boolean;
  }) =>
    apiClient.put(`/templates/${templateId}/update_beneficiary/`, data),
  
  removeBeneficiary: (templateId: number, beneficiaryId: number) =>
    apiClient.delete(`/templates/${templateId}/remove_beneficiary/`, {
      data: { beneficiary_id: beneficiaryId }
    }),
};

// Transfers API
export const transfersApi = {
  bulkCreate: (data: BulkCreateTransferRequest) =>
    apiClient.post<Transfer[]>('/transfers/bulk_create/', data),
  
  update: (id: number, data: Partial<Transfer>) =>
    apiClient.put<Transfer>(`/transfers/${id}/`, data),
  
  partialUpdate: (id: number, data: Partial<Transfer>) =>
    apiClient.patch<Transfer>(`/transfers/${id}/`, data),
  
  delete: (id: number) =>
    apiClient.delete(`/transfers/${id}/`),
  
  generateXml: (data: GenerateXmlRequest) =>
    apiClient.post<GenerateXmlResponse>('/transfers/generate_xml/', data),
  
  generateKHExport: (data: GenerateXmlRequest) =>
    apiClient.post<GenerateKHExportResponse>('/transfers/generate_kh_export/', data),
};

// Bank Accounts API
export const bankAccountsApi = {
  getDefault: () =>
    apiClient.get<BankAccount>('/bank-accounts/default/'),
  
  getAll: () =>
    apiClient.get<ApiResponse<BankAccount>>('/bank-accounts/'),
  
  create: (data: Omit<BankAccount, 'id'>) =>
    apiClient.post<BankAccount>('/bank-accounts/', data),
  
  update: (id: number, data: Partial<BankAccount>) =>
    apiClient.put<BankAccount>(`/bank-accounts/${id}/`, data),
  
  delete: (id: number) =>
    apiClient.delete(`/bank-accounts/${id}/`),
};

// Batches API
export const batchesApi = {
  getAll: () =>
    apiClient.get<ApiResponse<TransferBatch>>('/batches/'),
  
  getById: (id: number) =>
    apiClient.get<TransferBatch>(`/batches/${id}/`),
  
  downloadXml: (id: number) =>
    apiClient.get(`/batches/${id}/download_xml/`, { responseType: 'blob' }),
  
  markUsedInBank: (id: number) =>
    apiClient.post(`/batches/${id}/mark_used_in_bank/`),
  
  markUnusedInBank: (id: number) =>
    apiClient.post(`/batches/${id}/mark_unused_in_bank/`),
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
  getCompanyUsers: () =>
    apiClient.get<any[]>('/company/users/'),
  
  updateUserRole: (userId: number, role: 'ADMIN' | 'USER') =>
    apiClient.put(`/company/users/${userId}/`, { role }),
  
  removeUser: (userId: number) =>
    apiClient.delete(`/company/users/${userId}/`),
};

export default apiClient;