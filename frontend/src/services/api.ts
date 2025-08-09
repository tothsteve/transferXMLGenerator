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
  LoadTemplateResponse,
  ExcelImportResponse,
} from '../types/api';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  
  loadTransfers: (id: number) =>
    apiClient.post<LoadTemplateResponse>(`/templates/${id}/load_transfers/`),
};

// Transfers API
export const transfersApi = {
  bulkCreate: (data: BulkCreateTransferRequest) =>
    apiClient.post<Transfer[]>('/transfers/bulk_create/', data),
  
  generateXml: (data: GenerateXmlRequest) =>
    apiClient.post<GenerateXmlResponse>('/transfers/generate_xml/', data),
};

// Bank Accounts API
export const bankAccountsApi = {
  getDefault: () =>
    apiClient.get<BankAccount>('/bank-accounts/default/'),
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

export default apiClient;