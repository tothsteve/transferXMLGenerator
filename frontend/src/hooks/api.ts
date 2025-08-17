import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  beneficiariesApi,
  templatesApi,
  transfersApi,
  bankAccountsApi,
  batchesApi,
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
  batches: ['batches'] as const,
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
    mutationFn: ({ templateId, data }: { 
      templateId: number, 
      data: { 
        template_id: number;
        originator_account_id: number;
        execution_date: string;
      }
    }) => templatesApi.loadTransfers(templateId, data),
  });
}

export function useAddTemplateBeneficiary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ templateId, data }: { 
      templateId: number; 
      data: {
        beneficiary_id: number;
        default_amount?: number;
        default_remittance?: string;
        order?: number;
        is_active?: boolean;
      }
    }) => templatesApi.addBeneficiary(templateId, data),
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      queryClient.invalidateQueries({ queryKey: queryKeys.template(templateId) });
    },
  });
}

export function useRemoveTemplateBeneficiary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ templateId, beneficiaryId }: { templateId: number; beneficiaryId: number }) =>
      templatesApi.removeBeneficiary(templateId, beneficiaryId),
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      queryClient.invalidateQueries({ queryKey: queryKeys.template(templateId) });
    },
  });
}

export function useUpdateTemplateBeneficiary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ templateId, data }: { 
      templateId: number; 
      data: {
        beneficiary_id: number;
        default_amount?: number;
        default_remittance?: string;
        order?: number;
        is_active?: boolean;
      }
    }) => templatesApi.updateBeneficiary(templateId, data),
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      queryClient.invalidateQueries({ queryKey: queryKeys.template(templateId) });
    },
  });
}

// Transfers Hooks
export function useBulkCreateTransfers() {
  return useMutation({
    mutationFn: (data: BulkCreateTransferRequest) => transfersApi.bulkCreate(data),
  });
}

export function useUpdateTransfer() {
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Transfer> }) => 
      transfersApi.update(id, data),
  });
}

export function useBulkUpdateTransfers() {
  return useMutation({
    mutationFn: async (transfers: { id: number; data: Partial<Transfer> }[]) => {
      // Execute all updates in parallel
      const updatePromises = transfers.map(({ id, data }) => 
        transfersApi.partialUpdate(id, data)
      );
      return Promise.all(updatePromises);
    },
  });
}

export function useDeleteTransfer() {
  return useMutation({
    mutationFn: (id: number) => transfersApi.delete(id),
  });
}

export function useGenerateXml() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: GenerateXmlRequest) => transfersApi.generateXml(data),
    onSuccess: () => {
      // Invalidate batches query to update the dashboard counter
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useGenerateKHExport() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: GenerateXmlRequest) => transfersApi.generateKHExport(data),
    onSuccess: () => {
      // Invalidate batches query to update the dashboard counter
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
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

// Batches Hooks
export function useBatches() {
  return useQuery({
    queryKey: queryKeys.batches,
    queryFn: () => batchesApi.getAll(),
    select: (data) => data.data,
  });
}

export function useMarkBatchUsedInBank() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (batchId: number) => batchesApi.markUsedInBank(batchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useMarkBatchUnusedInBank() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (batchId: number) => batchesApi.markUnusedInBank(batchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useDownloadBatchXml() {
  return useMutation({
    mutationFn: async (batchId: number) => {
      const response = await batchesApi.downloadXml(batchId);
      return response;
    },
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