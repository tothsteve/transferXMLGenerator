import { useState, useCallback, useEffect, Dispatch, SetStateAction } from 'react';
import { navInvoicesApi } from '../services/api';

export interface Invoice {
  id: number;
  nav_invoice_number: string;
  invoice_direction: string;
  invoice_direction_display: string;
  partner_name: string;
  partner_tax_number: string;
  issue_date: string;
  issue_date_formatted: string;
  fulfillment_date: string | null;
  fulfillment_date_formatted: string | null;
  payment_due_date: string | null;
  payment_due_date_formatted: string | null;
  payment_date: string | null;
  payment_date_formatted: string | null;
  completion_date?: string | null;
  last_modified_date?: string | null;
  currency_code: string;
  invoice_net_amount: number;
  invoice_net_amount_formatted: string;
  invoice_vat_amount: number;
  invoice_vat_amount_formatted: string;
  invoice_gross_amount: number;
  invoice_gross_amount_formatted: string;
  invoice_operation: string | null;
  invoice_category?: string | null;
  invoice_appearance?: string | null;
  payment_method: string | null;
  original_invoice_number: string | null;
  payment_status: {
    status: string;
    label: string;
    icon: string;
    class: string;
  };
  payment_status_date: string | null;
  payment_status_date_formatted: string | null;
  auto_marked_paid: boolean;
  is_overdue: boolean;
  is_paid: boolean;
  sync_status: string;
  created_at: string;
  nav_source?: string | null;
  original_request_version?: string | null;
  supplier_name?: string | null;
  customer_name?: string | null;
  supplier_tax_number?: string | null;
  customer_tax_number?: string | null;
  supplier_bank_account_number?: string | null;
  customer_bank_account_number?: string | null;
  line_items?: unknown[];
}

export interface UseInvoiceDataParams {
  queryParams: Record<string, unknown>;
  showError: (message: string) => void;
  setSelectedInvoices: Dispatch<SetStateAction<number[]>>;
}

export interface UseInvoiceDataReturn {
  invoices: Invoice[];
  loading: boolean;
  totalCount: number;
  refetch: () => void;
}

export const useInvoiceData = ({
  queryParams,
  showError,
  setSelectedInvoices,
}: UseInvoiceDataParams): UseInvoiceDataReturn => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Serialize queryParams for stable comparison
  const queryParamsKey = JSON.stringify(queryParams);

  // Load invoices from API
  useEffect(() => {
    const loadInvoices = async (): Promise<void> => {
      try {
        setLoading(true);
        const response = await navInvoicesApi.getAll(queryParams);

        // Handle both paginated and non-paginated responses
        if (Array.isArray(response.data)) {
          // Non-paginated response (direct array)
          setInvoices(response.data);
          setTotalCount(response.data.length);
        } else if (response.data.results !== null && response.data.results !== undefined) {
          // Paginated response with results array
          setInvoices(response.data.results);
          setTotalCount(response.data.count || 0);
        } else {
          // Fallback
          setInvoices([]);
          setTotalCount(0);
        }
      } catch (error) {
        console.error('Error loading invoices:', error);
        showError('Hiba a számlák betöltése során');
      } finally {
        setLoading(false);
      }
    };

    void loadInvoices();
    // Clear selections when query changes
    setSelectedInvoices([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryParamsKey, showError, setSelectedInvoices]);

  // Simple refetch wrapper - forces re-fetch by updating loading state
  const refetch = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      const response = await navInvoicesApi.getAll(queryParams);

      if (Array.isArray(response.data)) {
        setInvoices(response.data);
        setTotalCount(response.data.length);
      } else if (response.data.results !== null && response.data.results !== undefined) {
        setInvoices(response.data.results);
        setTotalCount(response.data.count || 0);
      } else {
        setInvoices([]);
        setTotalCount(0);
      }
    } catch (error) {
      console.error('Error loading invoices:', error);
      showError('Hiba a számlák betöltése során');
    } finally {
      setLoading(false);
    }
  }, [queryParams, showError]);

  return {
    invoices,
    loading,
    totalCount,
    refetch,
  };
};
