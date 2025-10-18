import { useState, useCallback } from 'react';
import { startOfMonth, endOfMonth, subMonths, format } from 'date-fns';

export interface UseInvoiceFiltersReturn {
  // State
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  directionFilter: string;
  setDirectionFilter: (value: string) => void;
  paymentStatusFilter: string;
  setPaymentStatusFilter: (value: string) => void;
  hideStornoInvoices: boolean;
  setHideStornoInvoices: (value: boolean) => void;
  inboundTransferFilter: boolean;
  setInboundTransferFilter: (value: boolean) => void;
  dateFilterType: 'issue_date' | 'fulfillment_date' | 'payment_due_date' | '';
  setDateFilterType: (value: 'issue_date' | 'fulfillment_date' | 'payment_due_date' | '') => void;
  dateFrom: string;
  setDateFrom: (value: string) => void;
  dateTo: string;
  setDateTo: (value: string) => void;
  filterAnchorEl: HTMLElement | null;
  setFilterAnchorEl: (value: HTMLElement | null) => void;

  // Actions
  handleDateFilterTypeChange: (value: 'issue_date' | 'fulfillment_date' | 'payment_due_date' | '') => void;
  applyDatePreset: (preset: 'current' | 'previous' | 'next') => void;
  navigateMonth: (direction: 'previous' | 'next') => void;
  clearFilters: () => void;
  buildInvoiceQueryParams: (currentPage: number, pageSize: number, sortField: string, sortDirection: 'asc' | 'desc') => Record<string, unknown>;
  handleFilterClick: (event: React.MouseEvent<HTMLElement>) => void;
  handleFilterClose: () => void;

  // Computed
  hasActiveFilters: boolean;
  filterMenuOpen: boolean;
}

export const useInvoiceFilters = (): UseInvoiceFiltersReturn => {
  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [directionFilter, setDirectionFilter] = useState<string>('');
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<string>('');
  const [hideStornoInvoices, setHideStornoInvoices] = useState(true);
  const [inboundTransferFilter, setInboundTransferFilter] = useState(false);

  // Date filter state
  const [dateFilterType, setDateFilterType] = useState<'issue_date' | 'fulfillment_date' | 'payment_due_date' | ''>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  // Filter menu state
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const filterMenuOpen = Boolean(filterAnchorEl);

  // Date range helper functions
  const getMonthRange = (date: Date): { from: string; to: string } => {
    return {
      from: format(startOfMonth(date), 'yyyy-MM-dd'),
      to: format(endOfMonth(date), 'yyyy-MM-dd'),
    };
  };

  const getCurrentMonthRange = (): { from: string; to: string } => getMonthRange(new Date());

  const getPreviousMonthRange = (): { from: string; to: string } => getMonthRange(subMonths(new Date(), 1));

  const getNextMonthRange = (): { from: string; to: string } =>
    getMonthRange(new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1));

  const getCurrentBaseDate = (): Date => {
    if (dateFrom) {
      return new Date(dateFrom + 'T00:00:00');
    }
    return new Date();
  };

  // Apply date range preset
  const applyDatePreset = (preset: 'current' | 'previous' | 'next'): void => {
    let range;
    if (preset === 'current') {
      range = getCurrentMonthRange();
    } else if (preset === 'previous') {
      range = getPreviousMonthRange();
    } else {
      range = getNextMonthRange();
    }
    setDateFrom(range.from);
    setDateTo(range.to);
  };

  // Navigate to previous/next month
  const navigateMonth = (direction: 'previous' | 'next'): void => {
    const baseDate = getCurrentBaseDate();
    const targetDate =
      direction === 'previous'
        ? subMonths(baseDate, 1)
        : new Date(baseDate.getFullYear(), baseDate.getMonth() + 1, 1);

    const range = getMonthRange(targetDate);
    setDateFrom(range.from);
    setDateTo(range.to);
  };

  // Handle date filter type change
  const handleDateFilterTypeChange = (
    value: 'issue_date' | 'fulfillment_date' | 'payment_due_date' | ''
  ): void => {
    setDateFilterType(value);

    if (value !== '') {
      // Set default date range to previous month
      const range = getPreviousMonthRange();
      setDateFrom(range.from);
      setDateTo(range.to);
    } else {
      // Clear dates when no date type is selected
      setDateFrom('');
      setDateTo('');
    }
  };

  // Helper function to add date filters to params
  const addDateFilters = useCallback((params: Record<string, unknown>) => {
    if (!dateFilterType) return;

    const dateFieldMap: Record<string, { from: string; to: string }> = {
      issue_date: { from: 'issue_date_from', to: 'issue_date_to' },
      fulfillment_date: { from: 'fulfillment_date_from', to: 'fulfillment_date_to' },
      payment_due_date: { from: 'payment_due_date_from', to: 'payment_due_date_to' },
    };

    const fields = dateFieldMap[dateFilterType];
    if (fields) {
      if (dateFrom) params[fields.from] = dateFrom;
      if (dateTo) params[fields.to] = dateTo;
    }
  }, [dateFilterType, dateFrom, dateTo]);

  // Build query parameters for API call
  const buildInvoiceQueryParams = useCallback((
    currentPage: number,
    pageSize: number,
    sortField: string,
    sortDirection: 'asc' | 'desc'
  ) => {
    const params: Record<string, unknown> = {
      page: currentPage,
      page_size: pageSize,
      ordering: `${sortDirection === 'desc' ? '-' : ''}${sortField}`,
      hide_storno_invoices: hideStornoInvoices,
    };

    if (searchTerm) {
      params.search = searchTerm;
    }

    if (inboundTransferFilter) {
      params.direction = 'INBOUND';
      params.payment_method = 'TRANSFER';
    } else if (directionFilter) {
      params.direction = directionFilter;
    }

    if (paymentStatusFilter) {
      params.payment_status = paymentStatusFilter;
    }

    addDateFilters(params);

    return params;
  }, [
    searchTerm,
    inboundTransferFilter,
    directionFilter,
    paymentStatusFilter,
    hideStornoInvoices,
    addDateFilters,
  ]);

  // Clear all filters
  const clearFilters = (): void => {
    setSearchTerm('');
    setDirectionFilter('');
    setPaymentStatusFilter('');
    setInboundTransferFilter(false);
    setHideStornoInvoices(true);
    handleDateFilterTypeChange('');
  };

  // Filter menu handlers
  const handleFilterClick = (event: React.MouseEvent<HTMLElement>): void => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterClose = (): void => {
    setFilterAnchorEl(null);
  };

  // Computed: Check if any filters are active
  const hasActiveFilters =
    (searchTerm !== null && searchTerm !== undefined && searchTerm !== '') ||
    (directionFilter !== null && directionFilter !== undefined && directionFilter !== '') ||
    (paymentStatusFilter !== null && paymentStatusFilter !== undefined && paymentStatusFilter !== '') ||
    !hideStornoInvoices ||
    inboundTransferFilter ||
    (dateFilterType !== null && dateFilterType !== undefined && dateFilterType !== '');

  return {
    // State
    searchTerm,
    setSearchTerm,
    directionFilter,
    setDirectionFilter,
    paymentStatusFilter,
    setPaymentStatusFilter,
    hideStornoInvoices,
    setHideStornoInvoices,
    inboundTransferFilter,
    setInboundTransferFilter,
    dateFilterType,
    setDateFilterType,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    filterAnchorEl,
    setFilterAnchorEl,

    // Actions
    handleDateFilterTypeChange,
    applyDatePreset,
    navigateMonth,
    clearFilters,
    buildInvoiceQueryParams,
    handleFilterClick,
    handleFilterClose,

    // Computed
    hasActiveFilters,
    filterMenuOpen,
  };
};
