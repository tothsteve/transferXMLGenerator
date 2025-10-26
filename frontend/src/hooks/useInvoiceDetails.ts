import { useState } from 'react';
import { navInvoicesApi, trustedPartnersApi } from '../services/api';
import { hasResponseData, getErrorMessage } from '../utils/errorTypeGuards';
import { Invoice } from './useInvoiceData';

export interface InvoiceLineItem {
  id: number;
  line_number: number;
  line_description: string;
  quantity: number | null;
  unit_of_measure: string;
  unit_price: number | null;
  line_net_amount: number;
  vat_rate: number | null;
  line_vat_amount: number;
  line_gross_amount: number;
  product_code_category: string;
  product_code_value: string;
}

export interface UseInvoiceDetailsParams {
  refetch: () => void;
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  bulkMarkPaidMutation: {
    mutateAsync: (data: { invoice_ids: number[]; payment_date: string }) => Promise<void>;
  };
}

export interface UseInvoiceDetailsReturn {
  selectedInvoice: Invoice | null;
  setSelectedInvoice: React.Dispatch<React.SetStateAction<Invoice | null>>;
  invoiceDetailsOpen: boolean;
  invoiceLineItems: InvoiceLineItem[];
  invoiceDetailsLoading: boolean;
  isSupplierTrusted: boolean;
  checkingTrustedStatus: boolean;
  addingTrustedPartner: boolean;
  handleViewInvoice: (invoice: Invoice) => Promise<void>;
  handleViewInvoiceById: (invoiceId: number) => Promise<void>;
  handleCloseInvoiceDetails: () => void;
  handleAddTrustedPartner: () => Promise<void>;
}

export const useInvoiceDetails = ({
  refetch,
  showSuccess,
  showError,
  bulkMarkPaidMutation,
}: UseInvoiceDetailsParams): UseInvoiceDetailsReturn => {
  // Modal states
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [invoiceDetailsOpen, setInvoiceDetailsOpen] = useState(false);
  const [invoiceLineItems, setInvoiceLineItems] = useState<InvoiceLineItem[]>([]);
  const [invoiceDetailsLoading, setInvoiceDetailsLoading] = useState(false);

  // Trusted partner states
  const [isSupplierTrusted, setIsSupplierTrusted] = useState<boolean>(false);
  const [checkingTrustedStatus, setCheckingTrustedStatus] = useState<boolean>(false);
  const [addingTrustedPartner, setAddingTrustedPartner] = useState<boolean>(false);

  // Track if we need to refresh the invoice list when closing the detail dialog
  const [shouldRefreshOnClose, setShouldRefreshOnClose] = useState<boolean>(false);

  // Check if supplier is already a trusted partner
  const checkSupplierTrustedStatus = async (supplierTaxNumber: string): Promise<boolean> => {
    if (!supplierTaxNumber) {
      setIsSupplierTrusted(false);
      return false;
    }

    try {
      setCheckingTrustedStatus(true);
      const response = await trustedPartnersApi.getAll({
        search: supplierTaxNumber,
        is_active: true,
      });

      // Check if any trusted partner matches this tax number
      const isTrusted =
        (response.data?.results !== null &&
          response.data?.results !== undefined &&
          response.data.results.some((partner: { tax_number: string }) => partner.tax_number === supplierTaxNumber)) ||
        false;

      setIsSupplierTrusted(isTrusted);
      return isTrusted;
    } catch (error) {
      console.error('Error checking trusted partner status:', error);
      setIsSupplierTrusted(false);
      return false;
    } finally {
      setCheckingTrustedStatus(false);
    }
  };

  // Load invoice details with line items
  const loadInvoiceDetails = async (invoiceId: number): Promise<void> => {
    try {
      setInvoiceDetailsLoading(true);
      const response = await navInvoicesApi.getById(invoiceId);
      setSelectedInvoice(response.data);
      setInvoiceLineItems(
        response.data.line_items !== null && response.data.line_items !== undefined
          ? response.data.line_items
          : []
      );

      // Check trusted partner status for supplier
      if (
        response.data.supplier_tax_number !== null &&
        response.data.supplier_tax_number !== undefined &&
        response.data.supplier_tax_number !== ''
      ) {
        await checkSupplierTrustedStatus(response.data.supplier_tax_number);
      } else {
        setIsSupplierTrusted(false);
      }
    } catch (error) {
      console.error('Error loading invoice details:', error);
      showError('Hiba a számla részletek betöltése során');
    } finally {
      setInvoiceDetailsLoading(false);
    }
  };

  // Open invoice details modal
  const handleViewInvoice = async (invoice: Invoice): Promise<void> => {
    setInvoiceDetailsOpen(true);
    await loadInvoiceDetails(invoice.id);
  };

  // Open invoice details modal by ID (for deep linking)
  const handleViewInvoiceById = async (invoiceId: number): Promise<void> => {
    setInvoiceDetailsOpen(true);
    await loadInvoiceDetails(invoiceId);
  };

  // Close invoice details modal
  const handleCloseInvoiceDetails = (): void => {
    setInvoiceDetailsOpen(false);
    setSelectedInvoice(null);
    setInvoiceLineItems([]);
    setInvoiceDetailsLoading(false);
    setIsSupplierTrusted(false);
    setCheckingTrustedStatus(false);
    setAddingTrustedPartner(false);

    // Refresh the invoice list if changes were made (preserving filters)
    if (shouldRefreshOnClose) {
      refetch();
      setShouldRefreshOnClose(false);
    }
  };

  // Helper: Validate supplier data for trusted partner
  const validateSupplierData = (): boolean => {
    const hasSupplierName =
      selectedInvoice?.supplier_name !== null &&
      selectedInvoice?.supplier_name !== undefined &&
      selectedInvoice?.supplier_name !== '';
    const hasSupplierTaxNumber =
      selectedInvoice?.supplier_tax_number !== null &&
      selectedInvoice?.supplier_tax_number !== undefined &&
      selectedInvoice?.supplier_tax_number !== '';

    return Boolean(selectedInvoice && hasSupplierName && hasSupplierTaxNumber);
  };

  // Helper: Auto-mark invoice as PAID after adding trusted partner
  const autoMarkInvoicePaid = async (supplierName: string): Promise<void> => {
    if (!selectedInvoice || selectedInvoice.payment_status.status !== 'UNPAID') {
      return;
    }

    try {
      await bulkMarkPaidMutation.mutateAsync({
        invoice_ids: [selectedInvoice.id],
        payment_date: new Date().toISOString().split('T')[0]!,
      });

      // Update the invoice in state to reflect the new payment status
      setSelectedInvoice((prev) =>
        prev
          ? {
              ...prev,
              payment_status: {
                status: 'PAID',
                label: 'Kifizetve',
                icon: 'CheckCircle',
                class: 'success',
              },
              payment_status_date: new Date().toISOString().split('T')[0]!,
              payment_status_date_formatted: new Date().toLocaleDateString('hu-HU'),
              is_paid: true,
            }
          : null
      );

      showSuccess(
        `${supplierName} hozzáadva a megbízható partnerekhez és a számla megjelölve kifizetettként`
      );
    } catch (paymentError) {
      console.error('Error marking invoice as paid:', paymentError);
      showSuccess(
        `${supplierName} hozzáadva a megbízható partnerekhez (fizetési állapot frissítése sikertelen)`
      );
    }
  };

  // Helper: Handle trusted partner API error
  const handleTrustedPartnerError = (error: unknown): void => {
    console.error('Error adding trusted partner:', error);

    if (!hasResponseData(error)) {
      showError('Hiba a megbízható partner hozzáadása során');
      return;
    }

    if (error.response.data.non_field_errors && Array.isArray(error.response.data.non_field_errors)) {
      const errorMsg = error.response.data.non_field_errors[0];
      showError(
        typeof errorMsg === 'string' ? errorMsg : 'Hiba a megbízható partner hozzáadása során'
      );
    } else if (error.response.data.tax_number && Array.isArray(error.response.data.tax_number)) {
      const errorMsg = error.response.data.tax_number[0];
      showError(`Adószám hiba: ${typeof errorMsg === 'string' ? errorMsg : 'Ismeretlen hiba'}`);
    } else {
      showError(getErrorMessage(error, 'Hiba a megbízható partner hozzáadása során'));
    }
  };

  // Add supplier as trusted partner
  const handleAddTrustedPartner = async (): Promise<void> => {
    if (!validateSupplierData()) {
      showError('Hiányzó szállító adatok a partner hozzáadásához');
      return;
    }

    try {
      setAddingTrustedPartner(true);

      const trustedPartnerData = {
        partner_name: selectedInvoice!.supplier_name!,
        tax_number: selectedInvoice!.supplier_tax_number!,
        is_active: true,
        auto_pay: true,
      };

      // Add trusted partner
      await trustedPartnersApi.create(trustedPartnerData);
      setIsSupplierTrusted(true);
      setShouldRefreshOnClose(true); // Mark that we need to refresh the list

      // Auto-mark invoice as PAID if it's currently UNPAID
      await autoMarkInvoicePaid(selectedInvoice!.supplier_name!);

      // Show success message if invoice was not unpaid (no auto-payment)
      if (selectedInvoice!.payment_status.status !== 'UNPAID') {
        showSuccess(`${selectedInvoice!.supplier_name} hozzáadva a megbízható partnerekhez`);
      }
    } catch (error: unknown) {
      handleTrustedPartnerError(error);
    } finally {
      setAddingTrustedPartner(false);
    }
  };

  return {
    selectedInvoice,
    setSelectedInvoice,
    invoiceDetailsOpen,
    invoiceLineItems,
    invoiceDetailsLoading,
    isSupplierTrusted,
    checkingTrustedStatus,
    addingTrustedPartner,
    handleViewInvoice,
    handleViewInvoiceById,
    handleCloseInvoiceDetails,
    handleAddTrustedPartner,
  };
};
