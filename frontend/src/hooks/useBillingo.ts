/**
 * Billingo React Query Hooks
 *
 * Custom hooks for Billingo invoice synchronization using React Query.
 * Provides data fetching, caching, and mutation capabilities.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from '@tanstack/react-query';
import { billingoApi } from '../services/billingo.api';
import {
  BillingoInvoice,
  BillingoInvoiceDetail,
  CompanyBillingoSettings,
  CompanyBillingoSettingsInput,
  BillingoSyncLog,
  BillingoSyncTriggerResponse,
  BillingoSpending,
  ApiResponse,
} from '../types/api';

/**
 * Query keys for React Query cache management
 */
export const billingoQueryKeys = {
  settings: ['billingoSettings'] as const,
  invoices: (params?: object) => ['billingoInvoices', params] as const,
  invoice: (id: number) => ['billingoInvoice', id] as const,
  syncLogs: (params?: object) => ['billingoSyncLogs', params] as const,
  spendings: (params?: object) => ['billingoSpendings', params] as const,
  spending: (id: number) => ['billingoSpending', id] as const,
};

/**
 * Hook for fetching company Billingo settings.
 *
 * @returns Query result with settings or null if not configured
 *
 * @example
 * ```tsx
 * const { data: settings, isLoading } = useBillingoSettings();
 * if (settings) {
 *   console.log('API key configured:', settings.has_api_key);
 * }
 * ```
 */
export function useBillingoSettings(): UseQueryResult<CompanyBillingoSettings | null, Error> {
  return useQuery({
    queryKey: billingoQueryKeys.settings,
    queryFn: () => billingoApi.getSettings(),
  });
}

/**
 * Hook for saving Billingo settings (create or update API key).
 * ADMIN role required.
 *
 * Automatically invalidates settings cache on success.
 *
 * @returns Mutation result for save operation
 *
 * @example
 * ```tsx
 * const saveMutation = useSaveBillingoSettings();
 *
 * const handleSave = () => {
 *   saveMutation.mutate({
 *     api_key_input: 'your-api-key',
 *     is_active: true
 *   });
 * };
 * ```
 */
export function useSaveBillingoSettings(): UseMutationResult<
  CompanyBillingoSettings,
  Error,
  CompanyBillingoSettingsInput
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CompanyBillingoSettingsInput) => billingoApi.saveSettings(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: billingoQueryKeys.settings });
    },
  });
}

/**
 * Hook for triggering manual Billingo sync.
 * ADMIN role required.
 *
 * Automatically invalidates invoices and sync logs cache on success.
 *
 * @returns Mutation result with sync metrics
 *
 * @example
 * ```tsx
 * const syncMutation = useTriggerBillingoSync();
 *
 * const handleSync = () => {
 *   syncMutation.mutate(undefined, {
 *     onSuccess: (result) => {
 *       console.log(`Synced ${result.invoices_processed} invoices`);
 *     }
 *   });
 * };
 * ```
 */
export function useTriggerBillingoSync(): UseMutationResult<
  BillingoSyncTriggerResponse,
  Error,
  boolean
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (full_sync: boolean) => billingoApi.triggerSync(full_sync),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['billingoInvoices'] });
      void queryClient.invalidateQueries({ queryKey: ['billingoSyncLogs'] });
      void queryClient.invalidateQueries({ queryKey: ['billingoSettings'] });
    },
  });
}

/**
 * Hook for fetching paginated list of Billingo invoices.
 *
 * @param params - Query parameters for filtering and pagination
 * @returns Query result with invoice list
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useBillingoInvoices({
 *   payment_status: 'outstanding',
 *   page: 1,
 *   page_size: 20,
 *   ordering: '-invoice_date'
 * });
 *
 * if (data) {
 *   console.log(`Found ${data.count} invoices`);
 *   data.results.forEach(invoice => {
 *     console.log(invoice.invoice_number, invoice.gross_total_formatted);
 *   });
 * }
 * ```
 */
export function useBillingoInvoices(params?: {
  page?: number;
  page_size?: number;
  payment_status?: string;
  search?: string;
  ordering?: string;
}): UseQueryResult<ApiResponse<BillingoInvoice>, Error> {
  return useQuery({
    queryKey: billingoQueryKeys.invoices(params),
    queryFn: () => billingoApi.getInvoices(params),
  });
}

/**
 * Hook for fetching single Billingo invoice with line items.
 *
 * @param id - Invoice ID (query disabled if 0 or undefined)
 * @returns Query result with invoice detail including items
 *
 * @example
 * ```tsx
 * const [selectedId, setSelectedId] = useState<number>(0);
 * const { data: invoice, isLoading } = useBillingoInvoice(selectedId);
 *
 * if (invoice) {
 *   console.log(`Invoice ${invoice.invoice_number}`);
 *   invoice.items.forEach(item => {
 *     console.log(`- ${item.name}: ${item.gross_amount}`);
 *   });
 * }
 * ```
 */
export function useBillingoInvoice(id: number): UseQueryResult<BillingoInvoiceDetail, Error> {
  return useQuery({
    queryKey: billingoQueryKeys.invoice(id),
    queryFn: () => billingoApi.getInvoiceById(id),
    enabled: !!id && id > 0,
  });
}

/**
 * Hook for fetching paginated list of sync logs.
 *
 * @param params - Query parameters for filtering and pagination
 * @returns Query result with sync log list
 *
 * @example
 * ```tsx
 * const { data: logs } = useBillingoSyncLogs({
 *   page: 1,
 *   page_size: 10,
 *   status: 'COMPLETED',
 *   ordering: '-started_at'
 * });
 *
 * logs?.results.forEach(log => {
 *   console.log(`${log.started_at_formatted}: ${log.invoices_processed} invoices`);
 * });
 * ```
 */
export function useBillingoSyncLogs(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  ordering?: string;
}): UseQueryResult<ApiResponse<BillingoSyncLog>, Error> {
  return useQuery({
    queryKey: billingoQueryKeys.syncLogs(params),
    queryFn: () => billingoApi.getSyncLogs(params),
  });
}

/**
 * Hook for fetching paginated list of Billingo spendings.
 *
 * @param params - Query parameters for filtering and pagination
 * @returns Query result with spending list
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useBillingoSpendings({
 *   category: 'service',
 *   paid: 'true',
 *   page: 1,
 *   page_size: 20,
 *   ordering: '-invoice_date'
 * });
 *
 * if (data) {
 *   console.log(`Found ${data.count} spendings`);
 *   data.results.forEach(spending => {
 *     console.log(spending.invoice_number, spending.total_gross_local);
 *   });
 * }
 * ```
 */
export function useBillingoSpendings(params?: {
  page?: number;
  page_size?: number;
  category?: string;
  paid?: string;
  partner_tax_code?: string;
  invoice_number?: string;
  from_date?: string;
  to_date?: string;
  payment_method?: string;
  search?: string;
  ordering?: string;
}): UseQueryResult<ApiResponse<BillingoSpending>, Error> {
  return useQuery({
    queryKey: billingoQueryKeys.spendings(params),
    queryFn: () => billingoApi.getSpendings(params),
  });
}

/**
 * Hook for fetching single Billingo spending with full details.
 *
 * @param id - Spending ID (query disabled if 0 or undefined)
 * @returns Query result with spending detail
 *
 * @example
 * ```tsx
 * const [selectedId, setSelectedId] = useState<number>(0);
 * const { data: spending, isLoading } = useBillingoSpending(selectedId);
 *
 * if (spending) {
 *   console.log(`Spending ${spending.invoice_number}`);
 *   console.log(`Partner: ${spending.partner_name}`);
 *   console.log(`Amount: ${spending.total_gross_local} HUF`);
 * }
 * ```
 */
export function useBillingoSpending(id: number): UseQueryResult<BillingoSpending, Error> {
  return useQuery({
    queryKey: billingoQueryKeys.spending(id),
    queryFn: () => billingoApi.getSpendingById(id),
    enabled: !!id && id > 0,
  });
}

/**
 * Trigger manual Billingo spendings synchronization.
 * ADMIN role required.
 *
 * @returns Mutation hook for triggering sync
 *
 * @example
 * ```tsx
 * const syncMutation = useTriggerBillingoSpendingsSync();
 *
 * // Partial sync (only new/changed)
 * syncMutation.mutate(false);
 *
 * // Full sync (all records)
 * syncMutation.mutate(true);
 * ```
 */
export function useTriggerBillingoSpendingsSync() {
  return useMutation({
    mutationFn: (full_sync: boolean) => billingoApi.triggerSpendingsSync(full_sync),
  });
}
