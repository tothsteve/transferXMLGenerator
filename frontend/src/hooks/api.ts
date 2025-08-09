import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  beneficiariesApi,
  templatesApi,
  transfersApi,
  bankAccountsApi,
  uploadApi,
} from '../services/api';
import {
  Beneficiary,
  TransferTemplate,
  Transfer,
  BulkCreateTransferRequest,
  GenerateXmlRequest,
} from '../types/api';

// Query Keys
export const queryKeys = {
  beneficiaries: ['beneficiaries'] as const,
  beneficiariesFrequent: ['beneficiaries', 'frequent'] as const,
  templates: ['templates'] as const,
  template: (id: number) => ['templates', id] as const,
  bankAccountDefault: ['bankAccount', 'default'] as const,
};

// Beneficiaries Hooks
export function useBeneficiaries(params?: { 
  search?: string; 
  is_frequent?: boolean; 
  is_active?: boolean; 
  page?: number;
  ordering?: string;
}) {
  return useQuery({
    queryKey: [...queryKeys.beneficiaries, params],
    queryFn: () => beneficiariesApi.getAll(params),
    select: (data) => data.data,
  });
}

export function useFrequentBeneficiaries() {
  return useQuery({
    queryKey: queryKeys.beneficiariesFrequent,
    queryFn: () => beneficiariesApi.getFrequent(),
    select: (data) => data.data,
  });
}

export function useCreateBeneficiary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: Omit<Beneficiary, 'id'>) => beneficiariesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}

export function useUpdateBeneficiary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Beneficiary> }) =>
      beneficiariesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}

export function useDeleteBeneficiary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => beneficiariesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}

// Templates Hooks
export function useTemplates() {
  return useQuery({
    queryKey: queryKeys.templates,
    queryFn: () => templatesApi.getAll(),
    select: (data) => data.data,
  });
}

export function useTemplate(id: number) {
  return useQuery({
    queryKey: queryKeys.template(id),
    queryFn: () => templatesApi.getById(id),
    select: (data) => data.data,
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: Omit<TransferTemplate, 'id' | 'beneficiary_count' | 'created_at' | 'updated_at'>) =>
      templatesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<TransferTemplate> }) =>
      templatesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      queryClient.invalidateQueries({ queryKey: queryKeys.template(id) });
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => templatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useLoadTemplate() {
  return useMutation({
    mutationFn: (id: number) => templatesApi.loadTransfers(id),
  });
}

// Transfers Hooks
export function useBulkCreateTransfers() {
  return useMutation({
    mutationFn: (data: BulkCreateTransferRequest) => transfersApi.bulkCreate(data),
  });
}

export function useGenerateXml() {
  return useMutation({
    mutationFn: (data: GenerateXmlRequest) => transfersApi.generateXml(data),
  });
}

// Bank Account Hooks
export function useDefaultBankAccount() {
  return useQuery({
    queryKey: queryKeys.bankAccountDefault,
    queryFn: () => bankAccountsApi.getDefault(),
    select: (data) => data.data,
  });
}

// Upload Hooks
export function useUploadExcel() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (file: File) => uploadApi.uploadExcel(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}