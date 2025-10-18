import { useState, Dispatch, SetStateAction } from 'react';
import { NavigateFunction } from 'react-router-dom';
import { navInvoicesApi, bankAccountsApi } from '../services/api';
import { hasResponseData, hasResponseStatus, getErrorMessage } from '../utils/errorTypeGuards';
import { Invoice } from './useInvoiceData';

export interface UseInvoiceSelectionParams {
  invoices: Invoice[];
  refetch: () => void;
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  addToast: (type: string, title: string, message: string, duration?: number) => void;
  navigate: NavigateFunction;
  bulkMarkUnpaidMutation: {
    mutateAsync: (invoiceIds: number[]) => Promise<void>;
    isPending: boolean;
  };
  bulkMarkPreparedMutation: {
    mutateAsync: (invoiceIds: number[]) => Promise<void>;
    isPending: boolean;
  };
  bulkMarkPaidMutation: {
    mutateAsync: (data: unknown) => Promise<void>;
    isPending: boolean;
  };
}

export interface UseInvoiceSelectionReturn {
  selectedInvoices: number[];
  setSelectedInvoices: Dispatch<SetStateAction<number[]>>;
  paymentDate: string;
  setPaymentDate: Dispatch<SetStateAction<string>>;
  usePaymentDueDate: boolean;
  setUsePaymentDueDate: Dispatch<SetStateAction<boolean>>;
  handleSelectInvoice: (invoiceId: number, selected: boolean) => void;
  handleSelectAll: (selected: boolean) => void;
  handleBulkMarkUnpaid: () => Promise<void>;
  handleBulkMarkPrepared: () => Promise<void>;
  handleBulkMarkPaid: () => Promise<void>;
  handleGenerateTransfers: () => Promise<void>;
}

export const useInvoiceSelection = ({
  invoices,
  refetch,
  showSuccess,
  showError,
  addToast,
  navigate,
  bulkMarkUnpaidMutation,
  bulkMarkPreparedMutation,
  bulkMarkPaidMutation,
}: UseInvoiceSelectionParams): UseInvoiceSelectionReturn => {
  // Selection state
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);

  // Payment date state for bulk update
  const [paymentDate, setPaymentDate] = useState<string>(
    new Date().toISOString().split('T')[0]!
  );
  const [usePaymentDueDate, setUsePaymentDueDate] = useState<boolean>(true);

  // Selection handlers
  const handleSelectInvoice = (invoiceId: number, selected: boolean): void => {
    if (selected) {
      setSelectedInvoices((prev) => [...prev, invoiceId]);
    } else {
      setSelectedInvoices((prev) => prev.filter((id) => id !== invoiceId));
    }
  };

  const handleSelectAll = (selected: boolean): void => {
    if (selected) {
      setSelectedInvoices(invoices.map((invoice) => invoice.id));
    } else {
      setSelectedInvoices([]);
    }
  };

  // Helper: Handle transfer generation response feedback
  const handleTransferGenerationFeedback = (
    errors: string[],
    warnings: string[],
    transfer_count: number,
    transfers: unknown[]
  ): void => {
    if (errors.length > 0) {
      showError(errors.join('\n\n'));
    }

    if (warnings.length > 0) {
      addToast('warning', 'Figyelmeztetések', warnings.join('\n\n'), 15000);
    }

    if (transfer_count > 0) {
      addToast('success', `${transfer_count} átutalás sikeresen létrehozva`, '', 8000);
      void navigate('/transfers', {
        state: {
          source: 'nav_invoices_generated',
          transfers: transfers,
          message: `${transfer_count} átutalás létrehozva NAV számlákból`,
        },
      });
    } else {
      showError('Nem sikerült átutalást létrehozni a kiválasztott számlákból');
    }
  };

  // Helper: Handle transfer generation error
  const handleTransferGenerationError = (error: unknown): void => {
    if (hasResponseStatus(error)) {
      if (error.response.status === 401) {
        showError('Nincs jogosultság az átutalások generálásához. Kérjük jelentkezzen be újra.');
        return;
      }
      if (error.response.status === 403) {
        showError('Nincs engedély az átutalások generálásához');
        return;
      }
    }

    if (hasResponseData(error)) {
      if (
        error.response.data.error !== null &&
        error.response.data.error !== undefined &&
        error.response.data.error !== ''
      ) {
        showError(error.response.data.error);
        return;
      }
      if (
        error.response.data.errors !== null &&
        error.response.data.errors !== undefined &&
        Array.isArray(error.response.data.errors)
      ) {
        showError(error.response.data.errors.join('\n\n'));
        return;
      }
      if (
        error.response.data.detail !== null &&
        error.response.data.detail !== undefined &&
        error.response.data.detail !== ''
      ) {
        showError(`API hiba: ${error.response.data.detail}`);
        return;
      }
    }

    showError(
      `Hiba történt az átutalások generálásakor: ${getErrorMessage(error, 'Ismeretlen hiba')}`
    );
  };

  // Generate transfers from selected invoices
  const handleGenerateTransfers = async (): Promise<void> => {
    if (selectedInvoices.length === 0) {
      showError('Kérjük, válasszon ki legalább egy számlát');
      return;
    }

    try {
      // Get default bank account for originator
      const defaultAccountResponse = await bankAccountsApi.getDefault();
      const originatorAccountId = defaultAccountResponse.data.id;

      if (!originatorAccountId) {
        showError(
          'Nincs beállítva alapértelmezett bankszámla. Kérjük, állítson be egyet a beállítások menüben.'
        );
        return;
      }

      // Call the generate_transfers endpoint
      const requestData = {
        invoice_ids: selectedInvoices,
        originator_account_id: originatorAccountId,
        execution_date: new Date().toISOString().split('T')[0]!,
      };

      showSuccess('Átutalások generálása folyamatban...');

      const response = await navInvoicesApi.generateTransfers(requestData);
      const { transfers, transfer_count, errors, warnings } = response.data;

      // Handle response feedback
      handleTransferGenerationFeedback(errors, warnings, transfer_count, transfers);

      // Clear selections
      setSelectedInvoices([]);
    } catch (error: unknown) {
      handleTransferGenerationError(error);
    }
  };

  // Bulk payment status update handlers
  const handleBulkMarkUnpaid = async (): Promise<void> => {
    if (selectedInvoices.length === 0) return;

    try {
      await bulkMarkUnpaidMutation.mutateAsync(selectedInvoices);
      showSuccess(`${selectedInvoices.length} számla megjelölve "Fizetésre vár" státuszként`);
      setSelectedInvoices([]);
      refetch();
    } catch (error: unknown) {
      showError(getErrorMessage(error, 'Hiba történt a státusz frissítésekor'));
    }
  };

  const handleBulkMarkPrepared = async (): Promise<void> => {
    if (selectedInvoices.length === 0) return;

    try {
      await bulkMarkPreparedMutation.mutateAsync(selectedInvoices);
      showSuccess(`${selectedInvoices.length} számla megjelölve "Előkészítve" státuszként`);
      setSelectedInvoices([]);
      refetch();
    } catch (error: unknown) {
      showError(getErrorMessage(error, 'Hiba történt a státusz frissítésekor'));
    }
  };

  const handleBulkMarkPaid = async (): Promise<void> => {
    if (selectedInvoices.length === 0) return;

    try {
      let requestData;

      if (usePaymentDueDate) {
        // Option 2: Use individual payment_due_date for each invoice
        const selectedInvoiceObjects = invoices.filter((invoice) =>
          selectedInvoices.includes(invoice.id)
        );
        const today = new Date().toISOString().split('T')[0]!;
        requestData = {
          invoices: selectedInvoiceObjects.map((invoice) => ({
            invoice_id: invoice.id,
            payment_date:
              invoice.payment_due_date !== null &&
              invoice.payment_due_date !== undefined &&
              invoice.payment_due_date !== ''
                ? invoice.payment_due_date
                : today,
          })),
        };
      } else {
        // Option 1: Use single custom date for all invoices
        requestData = {
          invoice_ids: selectedInvoices,
          ...(paymentDate !== null &&
            paymentDate !== undefined &&
            paymentDate !== '' && { payment_date: paymentDate }),
        };
      }

      await bulkMarkPaidMutation.mutateAsync(requestData);
      showSuccess(`${selectedInvoices.length} számla megjelölve "Kifizetve" státuszként`);
      setSelectedInvoices([]);
      refetch();
    } catch (error: unknown) {
      showError(getErrorMessage(error, 'Hiba történt a státusz frissítésekor'));
    }
  };

  return {
    selectedInvoices,
    setSelectedInvoices,
    paymentDate,
    setPaymentDate,
    usePaymentDueDate,
    setUsePaymentDueDate,
    handleSelectInvoice,
    handleSelectAll,
    handleBulkMarkUnpaid,
    handleBulkMarkPrepared,
    handleBulkMarkPaid,
    handleGenerateTransfers,
  };
};
