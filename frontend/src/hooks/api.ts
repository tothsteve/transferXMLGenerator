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
  bankStatementsApi,
  bankTransactionsApi,
  otherCostsApi,
  supplierCategoriesApi,
  supplierTypesApi,
  suppliersApi,
  customersApi,
  productPricesApi,
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
  SupplierCategory,
  SupplierType,
  Supplier,
  Customer,
  ProductPrice,
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
} from '../schemas/bankStatement.schemas';

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
  bankStatements: ['bankStatements'] as const,
  bankStatement: (id: number) => ['bankStatements', id] as const,
  bankTransactions: (statementId: number) => ['bankTransactions', statementId] as const,
  bankTransaction: (id: number) => ['bankTransaction', id] as const,
  supportedBanks: ['supportedBanks'] as const,
  otherCosts: ['otherCosts'] as const,
  otherCost: (id: number) => ['otherCosts', id] as const,
  supplierCategories: ['supplierCategories'] as const,
  supplierCategory: (id: number) => ['supplierCategories', id] as const,
  supplierTypes: ['supplierTypes'] as const,
  supplierType: (id: number) => ['supplierTypes', id] as const,
  suppliers: ['suppliers'] as const,
  supplier: (id: number) => ['suppliers', id] as const,
  customers: ['customers'] as const,
  customer: (id: number) => ['customers', id] as const,
  productPrices: ['productPrices'] as const,
  productPrice: (id: number) => ['productPrices', id] as const,
};

/**
 * Helper to handle 403 Forbidden errors gracefully for feature-gated endpoints.
 * Returns empty data instead of throwing, allowing components to show "no data" messages.
 *
 * @param queryFn - The original query function
 * @param emptyData - The empty data to return on 403 (default: empty ApiResponse)
 */
function handleForbiddenGracefully<T>(
  queryFn: () => Promise<T>,
  emptyData?: T
): () => Promise<T> {
  return async () => {
    try {
      return await queryFn();
    } catch (error: unknown) {
      // Check if it's a 403 Forbidden error
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 403) {
          // Return empty data instead of throwing - user doesn't have access
          return (emptyData ?? { count: 0, next: null, previous: null, results: [] }) as T;
        }
      }
      // For all other errors, rethrow
      throw error;
    }
  };
}

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

export function useFrequentBeneficiaries(): UseQueryResult<Beneficiary[], Error> {
  return useQuery({
    queryKey: queryKeys.beneficiariesFrequent,
    queryFn: async () => {
      const response = await beneficiariesApi.getFrequent();
      return response.data;
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

/**
 * Bank Statements Hooks
 *
 * React Query hooks for managing bank statements with Zod validation.
 * All external data is validated before use to ensure type safety.
 */

/**
 * Hook for fetching paginated bank statements with filtering.
 *
 * Implements automatic caching, refetching, and Zod validation.
 * All API responses are validated before use.
 *
 * @param params - Query parameters for filtering and pagination
 * @returns Query result with validated bank statement data
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useBankStatements({
 *   page: 1,
 *   page_size: 20,
 *   bank_code: 'GRANIT',
 *   status: 'COMPLETED'
 * });
 *
 * if (isLoading) return <LoadingSpinner />;
 * if (error) return <ErrorMessage error={error} />;
 * if (!data) return <EmptyState />;
 *
 * return <BankStatementList statements={data.results} />;
 * ```
 */
export function useBankStatements(
  params?: BankStatementQueryParams
): UseQueryResult<BankStatementListResponse, Error> {
  return useQuery({
    queryKey: [...queryKeys.bankStatements, params],
    queryFn: () => bankStatementsApi.getAll(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  });
}

/**
 * Hook for fetching single bank statement by ID.
 *
 * @param id - Bank statement ID
 * @returns Query result with validated bank statement
 *
 * @example
 * ```tsx
 * const { data: statement } = useBankStatement(123);
 * ```
 */
export function useBankStatement(id: number): UseQueryResult<BankStatement, Error> {
  return useQuery({
    queryKey: queryKeys.bankStatement(id),
    queryFn: () => bankStatementsApi.getById(id),
    staleTime: 5 * 60 * 1000,
    retry: 3,
  });
}

/**
 * Hook for fetching list of supported banks.
 *
 * Results are cached indefinitely as supported banks rarely change.
 *
 * @returns Query result with supported banks list
 *
 * @example
 * ```tsx
 * const { data: banks } = useSupportedBanks();
 * ```
 */
export function useSupportedBanks(): UseQueryResult<SupportedBanksResponse, Error> {
  return useQuery({
    queryKey: queryKeys.supportedBanks,
    queryFn: () => bankStatementsApi.getSupportedBanks(),
    staleTime: Infinity, // Cache forever
    gcTime: Infinity, // Garbage collection time (renamed from cacheTime in v5)
    retry: 3,
  });
}

/**
 * Hook for uploading bank statement file.
 *
 * Invalidates bank statements list on success.
 *
 * @returns Mutation result for file upload
 *
 * @example
 * ```tsx
 * const uploadMutation = useUploadBankStatement();
 *
 * const handleUpload = async (file: File) => {
 *   try {
 *     const result = await uploadMutation.mutateAsync(file);
 *     console.log('Uploaded:', result.statement.id);
 *   } catch (error) {
 *     console.error('Upload failed:', error);
 *   }
 * };
 * ```
 */
export function useUploadBankStatement(): UseMutationResult<UploadResponse, Error, File> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => bankStatementsApi.upload(file),
    retry: false, // NEVER retry file uploads - prevents duplicates
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.bankStatements });
    },
  });
}

/**
 * Hook for deleting bank statement.
 *
 * Invalidates bank statements list on success.
 *
 * @returns Mutation result for deletion
 *
 * @example
 * ```tsx
 * const deleteMutation = useDeleteBankStatement();
 *
 * const handleDelete = async (id: number) => {
 *   if (window.confirm('Biztosan törölni szeretné?')) {
 *     await deleteMutation.mutateAsync(id);
 *   }
 * };
 * ```
 */
export function useDeleteBankStatement(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => bankStatementsApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.bankStatements });
    },
  });
}

/**
 * Bank Transactions Hooks
 *
 * React Query hooks for managing transactions within bank statements.
 */

/**
 * Hook for fetching paginated transactions for a statement.
 *
 * @param statementId - Parent bank statement ID
 * @param params - Query parameters for filtering and pagination
 * @returns Query result with validated transaction data
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useBankTransactions(123, {
 *   page: 1,
 *   transaction_type: 'TRANSFER',
 *   is_matched: false
 * });
 * ```
 */
export function useBankTransactions(
  statementId: number,
  params?: BankTransactionQueryParams
): UseQueryResult<BankTransactionListResponse, Error> {
  return useQuery({
    queryKey: [...queryKeys.bankTransactions(statementId), params],
    queryFn: () => bankTransactionsApi.getAll(statementId, params),
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 3,
  });
}

/**
 * Hook for fetching single transaction by ID.
 *
 * @param id - Transaction ID
 * @returns Query result with validated transaction
 */
export function useBankTransaction(id: number): UseQueryResult<BankTransaction, Error> {
  return useQuery({
    queryKey: queryKeys.bankTransaction(id),
    queryFn: () => bankTransactionsApi.getById(id),
    staleTime: 2 * 60 * 1000,
    retry: 3,
  });
}

/**
 * Hook for manually matching transaction to invoice.
 *
 * Invalidates transactions list on success.
 *
 * @returns Mutation result for matching
 *
 * @example
 * ```tsx
 * const matchMutation = useMatchTransactionToInvoice();
 *
 * const handleMatch = async (transactionId: number, invoiceId: number) => {
 *   await matchMutation.mutateAsync({ transactionId, invoiceId });
 * };
 * ```
 */
export function useMatchTransactionToInvoice(): UseMutationResult<
  BankTransaction,
  Error,
  { transactionId: number; invoiceId: number }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ transactionId, invoiceId }) =>
      bankTransactionsApi.matchInvoice(transactionId, invoiceId),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bankTransactions(data.bank_statement),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bankTransaction(data.id),
      });
    },
  });
}

/**
 * Hook for removing invoice match from transaction.
 *
 * Invalidates transactions list on success.
 *
 * @returns Mutation result for unmatching
 */
export function useUnmatchTransaction(): UseMutationResult<BankTransaction, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transactionId: number) => bankTransactionsApi.unmatch(transactionId),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bankTransactions(data.bank_statement),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bankTransaction(data.id),
      });
    },
  });
}

/**
 * Other Costs Hooks
 *
 * React Query hooks for managing categorized expense records.
 */

/**
 * Hook for fetching paginated other costs with filtering.
 *
 * @param params - Query parameters for filtering and pagination
 * @returns Query result with validated other costs data
 *
 * @example
 * ```tsx
 * const { data } = useOtherCosts({
 *   page: 1,
 *   category: 'BANK_FEE',
 *   date_from: '2025-01-01'
 * });
 * ```
 */
export function useOtherCosts(
  params?: OtherCostQueryParams
): UseQueryResult<OtherCostListResponse, Error> {
  return useQuery({
    queryKey: [...queryKeys.otherCosts, params],
    queryFn: () => otherCostsApi.getAll(params),
    staleTime: 5 * 60 * 1000,
    retry: 3,
  });
}

/**
 * Hook for fetching single other cost by ID.
 *
 * @param id - Other cost ID
 * @returns Query result with validated other cost
 */
export function useOtherCost(id: number): UseQueryResult<OtherCost, Error> {
  return useQuery({
    queryKey: queryKeys.otherCost(id),
    queryFn: () => otherCostsApi.getById(id),
    staleTime: 5 * 60 * 1000,
    retry: 3,
  });
}

/**
 * Hook for creating other cost record.
 *
 * Invalidates other costs list on success.
 *
 * @returns Mutation result for creation
 */
export function useCreateOtherCost(): UseMutationResult<
  OtherCost,
  Error,
  Omit<OtherCost, 'id' | 'created_at' | 'updated_at'>
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => otherCostsApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.otherCosts });
    },
  });
}

/**
 * Hook for updating other cost record.
 *
 * Invalidates other costs list on success.
 *
 * @returns Mutation result for update
 */
export function useUpdateOtherCost(): UseMutationResult<
  OtherCost,
  Error,
  { id: number; data: Partial<OtherCost> }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => otherCostsApi.update(id, data),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.otherCosts });
      void queryClient.invalidateQueries({ queryKey: queryKeys.otherCost(data.id) });
    },
  });
}

/**
 * Hook for deleting other cost record.
 *
 * Invalidates other costs list on success.
 *
 * @returns Mutation result for deletion
 */
export function useDeleteOtherCost(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => otherCostsApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.otherCosts });
    },
  });
}

// ============================================================================
// BASE_TABLES - Alaptáblák (Suppliers, Customers, Product Prices)
// ============================================================================

/**
 * Supplier Categories Hooks - Beszállító kategóriák kezelése
 *
 * React Query hooks for managing supplier category data
 */

export function useSupplierCategories(params?: {
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}): UseQueryResult<ApiResponse<SupplierCategory>, Error> {
  return useQuery({
    queryKey: [...queryKeys.supplierCategories, params],
    queryFn: handleForbiddenGracefully(async () => {
      const response = await supplierCategoriesApi.getAll(params);
      return response.data;
    }),
  });
}

export function useSupplierCategory(id: number): UseQueryResult<SupplierCategory, Error> {
  return useQuery({
    queryKey: queryKeys.supplierCategory(id),
    queryFn: () => supplierCategoriesApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateSupplierCategory(): UseMutationResult<
  SupplierCategory,
  Error,
  Omit<SupplierCategory, 'id' | 'company' | 'company_name' | 'created_at' | 'updated_at' | 'display_order'> & { display_order?: number }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => supplierCategoriesApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierCategories });
    },
  });
}

export function useUpdateSupplierCategory(): UseMutationResult<SupplierCategory, Error, { id: number; data: Partial<SupplierCategory> }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => supplierCategoriesApi.update(id, data),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierCategories });
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierCategory(data.id) });
    },
  });
}

export function useDeleteSupplierCategory(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => supplierCategoriesApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierCategories });
    },
  });
}

/**
 * Supplier Types Hooks - Beszállító típusok kezelése
 *
 * React Query hooks for managing supplier type data
 */

export function useSupplierTypes(params?: {
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}): UseQueryResult<ApiResponse<SupplierType>, Error> {
  return useQuery({
    queryKey: [...queryKeys.supplierTypes, params],
    queryFn: handleForbiddenGracefully(async () => {
      const response = await supplierTypesApi.getAll(params);
      return response.data;
    }),
  });
}

export function useSupplierType(id: number): UseQueryResult<SupplierType, Error> {
  return useQuery({
    queryKey: queryKeys.supplierType(id),
    queryFn: () => supplierTypesApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateSupplierType(): UseMutationResult<
  SupplierType,
  Error,
  Omit<SupplierType, 'id' | 'company' | 'company_name' | 'created_at' | 'updated_at' | 'display_order'> & { display_order?: number }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => supplierTypesApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierTypes });
    },
  });
}

export function useUpdateSupplierType(): UseMutationResult<SupplierType, Error, { id: number; data: Partial<SupplierType> }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => supplierTypesApi.update(id, data),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierTypes });
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierType(data.id) });
    },
  });
}

export function useDeleteSupplierType(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => supplierTypesApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplierTypes });
    },
  });
}

/**
 * Suppliers Hooks - Beszállítók kezelése
 *
 * React Query hooks for managing supplier data with Zod validation
 */

export function useSuppliers(params?: {
  search?: string;
  category?: string;
  type?: string;
  valid_only?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}): UseQueryResult<ApiResponse<Supplier>, Error> {
  return useQuery({
    queryKey: [...queryKeys.suppliers, params],
    queryFn: handleForbiddenGracefully(async () => {
      const response = await suppliersApi.getAll(params);
      return response.data;
    }),
  });
}

export function useSupplier(id: number): UseQueryResult<Supplier, Error> {
  return useQuery({
    queryKey: queryKeys.supplier(id),
    queryFn: () => suppliersApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateSupplier(): UseMutationResult<
  Supplier,
  Error,
  Omit<Supplier, 'id' | 'company' | 'company_name' | 'is_valid' | 'created_at' | 'updated_at'>
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => suppliersApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.suppliers });
    },
  });
}

export function useUpdateSupplier(): UseMutationResult<Supplier, Error, { id: number; data: Partial<Supplier> }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => suppliersApi.update(id, data),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.suppliers });
      void queryClient.invalidateQueries({ queryKey: queryKeys.supplier(data.id) });
    },
  });
}

export function useDeleteSupplier(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => suppliersApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.suppliers });
    },
  });
}

/**
 * Customers Hooks - Vevők kezelése
 *
 * React Query hooks for managing customer data with Zod validation
 */

export function useCustomers(params?: {
  search?: string;
  valid_only?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}): UseQueryResult<ApiResponse<Customer>, Error> {
  return useQuery({
    queryKey: [...queryKeys.customers, params],
    queryFn: handleForbiddenGracefully(async () => {
      const response = await customersApi.getAll(params);
      return response.data;
    }),
  });
}

export function useCustomer(id: number): UseQueryResult<Customer, Error> {
  return useQuery({
    queryKey: queryKeys.customer(id),
    queryFn: () => customersApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateCustomer(): UseMutationResult<
  Customer,
  Error,
  Omit<Customer, 'id' | 'company' | 'company_name' | 'is_valid' | 'created_at' | 'updated_at'>
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => customersApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.customers });
    },
  });
}

export function useUpdateCustomer(): UseMutationResult<Customer, Error, { id: number; data: Partial<Customer> }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => customersApi.update(id, data),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.customers });
      void queryClient.invalidateQueries({ queryKey: queryKeys.customer(data.id) });
    },
  });
}

export function useDeleteCustomer(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => customersApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.customers });
    },
  });
}

/**
 * Product Prices Hooks - CONMED árak kezelése
 *
 * React Query hooks for managing product price data with Zod validation
 */

export function useProductPrices(params?: {
  search?: string;
  product_value?: string;
  is_inventory_managed?: boolean;
  valid_only?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}): UseQueryResult<ApiResponse<ProductPrice>, Error> {
  return useQuery({
    queryKey: [...queryKeys.productPrices, params],
    queryFn: handleForbiddenGracefully(async () => {
      const response = await productPricesApi.getAll(params);
      return response.data;
    }),
  });
}

export function useProductPrice(id: number): UseQueryResult<ProductPrice, Error> {
  return useQuery({
    queryKey: queryKeys.productPrice(id),
    queryFn: () => productPricesApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateProductPrice(): UseMutationResult<
  ProductPrice,
  Error,
  Omit<ProductPrice, 'id' | 'company' | 'company_name' | 'is_valid' | 'created_at' | 'updated_at'>
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => productPricesApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.productPrices });
    },
  });
}

export function useUpdateProductPrice(): UseMutationResult<ProductPrice, Error, { id: number; data: Partial<ProductPrice> }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => productPricesApi.update(id, data),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.productPrices });
      void queryClient.invalidateQueries({ queryKey: queryKeys.productPrice(data.id) });
    },
  });
}

export function useDeleteProductPrice(): UseMutationResult<void, Error, number> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => productPricesApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.productPrices });
    },
  });
}
