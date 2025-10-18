import {
  useMutation,
  useQuery,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from '@tanstack/react-query';
import {
  beneficiariesApi,
  templatesApi,
  transfersApi,
  bankAccountsApi,
  batchesApi,
  uploadApi,
  navInvoicesApi,
} from '../services/api';
import {
  Beneficiary,
  TransferTemplate,
  Transfer,
  BulkCreateTransferRequest,
  GenerateXmlRequest,
  GenerateXmlResponse,
  GenerateKHExportResponse,
  LoadTemplateResponse,
  ExcelImportResponse,
  ApiResponse,
  BankAccount,
  TransferBatch,
  NAVInvoice,
} from '../types/api';
import {
  BeneficiarySchema,
  TransferTemplateSchema,
  TransferSchema,
  NAVInvoiceSchema,
  BankAccountSchema,
  TransferBatchSchema,
  ApiResponseSchema,
} from '../schemas/api.schemas';

// Query Keys
export const queryKeys = {
  beneficiaries: ['beneficiaries'] as const,
  beneficiariesFrequent: ['beneficiaries', 'frequent'] as const,
  templates: ['templates'] as const,
  template: (id: number) => ['templates', id] as const,
  transfers: ['transfers'] as const,
  bankAccountDefault: ['bankAccount', 'default'] as const,
  batches: ['batches'] as const,
  navInvoices: ['navInvoices'] as const,
};

/**
 * Beneficiaries Hooks
 *
 * React Query hooks for managing beneficiary data with Zod validation
 */

export function useBeneficiaries(params?: {
  search?: string;
  is_frequent?: boolean;
  is_active?: boolean;
  page?: number;
  ordering?: string;
}): UseQueryResult<ApiResponse<Beneficiary>, Error> {
  return useQuery({
    queryKey: [...queryKeys.beneficiaries, params],
    queryFn: () => beneficiariesApi.getAll(params),
    select: (data) => {
      try {
        // Validate API response with Zod schema
        const schema = ApiResponseSchema(BeneficiarySchema);
        const parsed = schema.parse(data.data);
        return parsed;
      } catch (error) {
        console.error('❌ Zod validation error in useBeneficiaries:', error);
        console.error('Raw data:', data.data);
        // Return raw data as fallback
        return data.data;
      }
    },
  });
}

export function useFrequentBeneficiaries(): UseQueryResult<ApiResponse<Beneficiary>, Error> {
  return useQuery({
    queryKey: queryKeys.beneficiariesFrequent,
    queryFn: () => beneficiariesApi.getFrequent(),
    select: (data) => {
      const schema = ApiResponseSchema(BeneficiarySchema);
      return schema.parse(data.data);
    },
  });
}

export function useCreateBeneficiary(): UseMutationResult<Beneficiary, Error, Omit<Beneficiary, 'id'>> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Omit<Beneficiary, 'id'>) => {
      const response = await beneficiariesApi.create(data);
      return response.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}

export function useUpdateBeneficiary(): UseMutationResult<Beneficiary, Error, { id: number; data: Partial<Beneficiary> }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Beneficiary> }) => {
      const response = await beneficiariesApi.update(id, data);
      return response.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}

export function useDeleteBeneficiary(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await beneficiariesApi.delete(id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}

/**
 * Templates Hooks
 *
 * React Query hooks for managing transfer template data with Zod validation
 */

export function useTemplates(showInactive?: boolean): UseQueryResult<ApiResponse<TransferTemplate>, Error> {
  return useQuery({
    queryKey: [...queryKeys.templates, showInactive],
    queryFn: () => templatesApi.getAll(showInactive ? { show_inactive: true } : undefined),
    select: (data) => {
      try {
        const schema = ApiResponseSchema(TransferTemplateSchema);
        const parsed = schema.parse(data.data);
        return parsed;
      } catch (error) {
        console.error('❌ Zod validation error in useTemplates:', error);
        console.error('Raw data:', data.data);
        return data.data;
      }
    },
  });
}

export function useTemplate(id: number): UseQueryResult<TransferTemplate, Error> {
  return useQuery({
    queryKey: queryKeys.template(id),
    queryFn: () => templatesApi.getById(id),
    select: (data) => TransferTemplateSchema.parse(data.data),
    enabled: !!id,
  });
}

export function useCreateTemplate(): UseMutationResult<
  TransferTemplate,
  Error,
  Omit<TransferTemplate, 'id' | 'beneficiary_count' | 'created_at' | 'updated_at'>
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      data: Omit<TransferTemplate, 'id' | 'beneficiary_count' | 'created_at' | 'updated_at'>
    ) => {
      const response = await templatesApi.create(data);
      return response.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useUpdateTemplate(): UseMutationResult<
  TransferTemplate,
  Error,
  { id: number; data: Partial<TransferTemplate> }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<TransferTemplate> }) => {
      const response = await templatesApi.update(id, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      void queryClient.invalidateQueries({ queryKey: queryKeys.template(id) });
    },
  });
}

export function useDeleteTemplate(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await templatesApi.delete(id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useLoadTemplate(): UseMutationResult<
  LoadTemplateResponse,
  Error,
  {
    templateId: number;
    data: {
      template_id: number;
      originator_account_id: number;
      execution_date: string;
    };
  }
> {
  return useMutation({
    mutationFn: async ({
      templateId,
      data,
    }: {
      templateId: number;
      data: {
        template_id: number;
        originator_account_id: number;
        execution_date: string;
      };
    }) => {
      const response = await templatesApi.loadTransfers(templateId, data);
      return response.data;
    },
  });
}

export function useAddTemplateBeneficiary(): UseMutationResult<
  unknown,
  Error,
  {
    templateId: number;
    data: {
      beneficiary_id: number;
      default_amount?: number;
      default_remittance?: string;
      order?: number;
      is_active?: boolean;
    };
  }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      data,
    }: {
      templateId: number;
      data: {
        beneficiary_id: number;
        default_amount?: number;
        default_remittance?: string;
        order?: number;
        is_active?: boolean;
      };
    }) => templatesApi.addBeneficiary(templateId, data),
    onSuccess: (_, { templateId }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      void queryClient.invalidateQueries({ queryKey: queryKeys.template(templateId) });
    },
  });
}

export function useRemoveTemplateBeneficiary(): UseMutationResult<
  void,
  Error,
  { templateId: number; beneficiaryId: number }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ templateId, beneficiaryId }: { templateId: number; beneficiaryId: number }) => {
      await templatesApi.removeBeneficiary(templateId, beneficiaryId);
    },
    onSuccess: (_, { templateId }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      void queryClient.invalidateQueries({ queryKey: queryKeys.template(templateId) });
    },
  });
}

export function useUpdateTemplateBeneficiary(): UseMutationResult<
  unknown,
  Error,
  {
    templateId: number;
    data: {
      beneficiary_id: number;
      default_amount?: number;
      default_remittance?: string;
      order?: number;
      is_active?: boolean;
    };
  }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      data,
    }: {
      templateId: number;
      data: {
        beneficiary_id: number;
        default_amount?: number;
        default_remittance?: string;
        order?: number;
        is_active?: boolean;
      };
    }) => templatesApi.updateBeneficiary(templateId, data),
    onSuccess: (_, { templateId }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.templates });
      void queryClient.invalidateQueries({ queryKey: queryKeys.template(templateId) });
    },
  });
}

/**
 * Transfers Hooks
 *
 * React Query hooks for managing transfer data with Zod validation
 */

export function useTransfers(params?: {
  page?: number;
  page_size?: number;
  is_processed?: boolean;
  template_id?: number;
  execution_date_from?: string;
  execution_date_to?: string;
  ordering?: string;
}): UseQueryResult<ApiResponse<Transfer>, Error> {
  return useQuery({
    queryKey: [...queryKeys.transfers, params],
    queryFn: () => transfersApi.getAll(params),
    select: (data) => {
      const schema = ApiResponseSchema(TransferSchema);
      return schema.parse(data.data);
    },
  });
}

export function useBulkCreateTransfers(): UseMutationResult<unknown, Error, BulkCreateTransferRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkCreateTransferRequest) => transfersApi.bulkCreate(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.transfers });
    },
  });
}

export function useUpdateTransfer(): UseMutationResult<Transfer, Error, { id: number; data: Partial<Transfer> }> {
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Transfer> }) => {
      const response = await transfersApi.partialUpdate(id, data);
      return response.data;
    },
  });
}

export function useBulkUpdateTransfers(): UseMutationResult<Transfer[], Error, { id: number; data: Partial<Transfer> }[]> {
  return useMutation({
    mutationFn: async (transfers: { id: number; data: Partial<Transfer> }[]) => {
      // Execute all updates in parallel
      const updatePromises = transfers.map(async ({ id, data }) => {
        const response = await transfersApi.partialUpdate(id, data);
        return response.data;
      });
      return Promise.all(updatePromises);
    },
  });
}

export function useDeleteTransfer(): UseMutationResult<void, Error, number> {
  return useMutation({
    mutationFn: async (id: number) => {
      await transfersApi.delete(id);
    },
  });
}

export function useGenerateXml(): UseMutationResult<GenerateXmlResponse, Error, GenerateXmlRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: GenerateXmlRequest) => {
      const response = await transfersApi.generateXml(data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate batches query to update the dashboard counter
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useGenerateKHExport(): UseMutationResult<GenerateKHExportResponse, Error, GenerateXmlRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: GenerateXmlRequest) => {
      const response = await transfersApi.generateKHExport(data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate batches query to update the dashboard counter
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

/**
 * Bank Account Hooks
 *
 * React Query hooks for managing bank account data with Zod validation
 */

export function useDefaultBankAccount(): UseQueryResult<BankAccount, Error> {
  return useQuery({
    queryKey: queryKeys.bankAccountDefault,
    queryFn: () => bankAccountsApi.getDefault(),
    select: (data) => BankAccountSchema.parse(data.data),
  });
}

/**
 * Batches Hooks
 *
 * React Query hooks for managing batch data with Zod validation
 */

export function useBatches(): UseQueryResult<ApiResponse<TransferBatch>, Error> {
  return useQuery({
    queryKey: queryKeys.batches,
    queryFn: () => batchesApi.getAll(),
    select: (data) => {
      try {
        const schema = ApiResponseSchema(TransferBatchSchema);
        const parsed = schema.parse(data.data);
        return parsed;
      } catch (error) {
        console.error('❌ Zod validation error in useBatches:', error);
        console.error('Raw data:', data.data);
        return data.data;
      }
    },
  });
}

export function useBatch(id: number | undefined, enabled = true): UseQueryResult<TransferBatch, Error> {
  return useQuery({
    queryKey: ['batch', id],
    queryFn: () => batchesApi.getById(id!),
    select: (data) => TransferBatchSchema.parse(data.data),
    enabled: enabled && !!id,
  });
}

export function useMarkBatchUsedInBank(): UseMutationResult<unknown, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (batchId: number) => batchesApi.markUsedInBank(batchId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useMarkBatchUnusedInBank(): UseMutationResult<unknown, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (batchId: number) => batchesApi.markUnusedInBank(batchId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

export function useDownloadBatchXml(): UseMutationResult<unknown, Error, number> {
  return useMutation({
    mutationFn: async (batchId: number) => {
      const response = await batchesApi.downloadXml(batchId);
      return response;
    },
  });
}

export function useDeleteBatch(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (batchId: number) => {
      await batchesApi.delete(batchId);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
  });
}

/**
 * NAV Invoices Hooks
 *
 * React Query hooks for managing NAV invoice data with Zod validation
 */

export function useNAVInvoices(params?: {
  search?: string;
  direction?: string;
  currency?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
  hide_storno_invoices?: boolean;
}): UseQueryResult<ApiResponse<NAVInvoice>, Error> {
  return useQuery({
    queryKey: [...queryKeys.navInvoices, params],
    queryFn: () => navInvoicesApi.getAll(params),
    select: (data) => {
      const schema = ApiResponseSchema(NAVInvoiceSchema);
      return schema.parse(data.data);
    },
  });
}

export function useBulkMarkUnpaid(): UseMutationResult<unknown, Error, number[]> {
  return useMutation({
    mutationFn: (invoice_ids: number[]) => navInvoicesApi.bulkMarkUnpaid(invoice_ids),
  });
}

export function useBulkMarkPrepared(): UseMutationResult<unknown, Error, number[]> {
  return useMutation({
    mutationFn: (invoice_ids: number[]) => navInvoicesApi.bulkMarkPrepared(invoice_ids),
  });
}

export function useBulkMarkPaid(): UseMutationResult<
  unknown,
  Error,
  {
    invoice_ids?: number[];
    payment_date?: string;
    invoices?: { invoice_id: number; payment_date: string }[];
  }
> {
  return useMutation({
    mutationFn: (data: {
      invoice_ids?: number[];
      payment_date?: string;
      invoices?: { invoice_id: number; payment_date: string }[];
    }) => navInvoicesApi.bulkMarkPaid(data),
  });
}

// Upload Hooks
export function useUploadExcel(): UseMutationResult<ExcelImportResponse, Error, File> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const response = await uploadApi.uploadExcel(file);
      return response.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiaries });
      void queryClient.invalidateQueries({ queryKey: queryKeys.beneficiariesFrequent });
    },
  });
}
