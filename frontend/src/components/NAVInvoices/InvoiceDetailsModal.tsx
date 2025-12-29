import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  TrendingDown as TrendingDownIcon,
  TrendingUp as TrendingUpIcon,
  AddCircle as AddTrustedIcon,
  Verified as VerifiedIcon,
} from '@mui/icons-material';

interface InvoiceLineItem {
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

interface SelectedInvoice {
  id: number;
  nav_invoice_number: string;
  invoice_direction: string;
  invoice_direction_display: string;
  invoice_operation: string | null;
  supplier_name?: string | null | undefined;
  supplier_tax_number?: string | null | undefined;
  supplier_bank_account_number?: string | null | undefined;
  customer_name?: string | null | undefined;
  customer_tax_number?: string | null | undefined;
  customer_bank_account_number?: string | null | undefined;
  fulfillment_date_formatted: string | null;
  issue_date_formatted: string;
  payment_due_date_formatted: string | null;
  original_invoice_number: string | null;
  invoice_net_amount: number;
  invoice_vat_amount: number;
  invoice_gross_amount: number;
}

interface InvoiceDetailsModalProps {
  open: boolean;
  onClose: () => void;
  invoice: SelectedInvoice | null;
  lineItems: InvoiceLineItem[];
  loading: boolean;
  isSupplierTrusted: boolean;
  checkingTrustedStatus: boolean;
  addingTrustedPartner: boolean;
  onAddTrustedPartner: () => void;
  formatNumber: (value: number | string | null) => string;
}

const InvoiceDetailsModal: React.FC<InvoiceDetailsModalProps> = ({
  open,
  onClose,
  invoice,
  lineItems,
  loading,
  isSupplierTrusted,
  checkingTrustedStatus,
  addingTrustedPartner,
  onAddTrustedPartner,
  formatNumber,
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <Typography variant="h6" component="span">
            Számla részletei:{' '}
            {invoice?.nav_invoice_number !== null &&
            invoice?.nav_invoice_number !== undefined &&
            invoice?.nav_invoice_number !== ''
              ? invoice.nav_invoice_number
              : 'Betöltés...'}
          </Typography>
          {invoice !== null && invoice !== undefined && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {/* Direction Badge */}
              <Chip
                label={invoice.invoice_direction_display}
                color={invoice.invoice_direction === 'INBOUND' ? 'secondary' : 'primary'}
                size="small"
                variant="outlined"
                icon={
                  invoice.invoice_direction === 'INBOUND' ? (
                    <TrendingDownIcon />
                  ) : (
                    <TrendingUpIcon />
                  )
                }
              />
              {invoice.invoice_operation === 'STORNO' && (
                <Chip
                  label="Stornó"
                  color="error"
                  size="small"
                  variant="filled"
                  sx={{ height: 24, fontSize: '0.75rem' }}
                />
              )}
            </Box>
          )}
        </Box>
      </DialogTitle>
      <DialogContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          invoice && (
            <Box>
              {/* Partners Section */}
              <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                {/* Supplier Column */}
                {invoice.supplier_name !== null &&
                  invoice.supplier_name !== undefined &&
                  invoice.supplier_name !== '' && (
                    <Box
                      sx={{
                        flex: 1,
                        borderRight:
                          invoice.customer_name !== null &&
                          invoice.customer_name !== undefined &&
                          invoice.customer_name !== ''
                            ? '1px solid #e0e0e0'
                            : 'none',
                        pr:
                          invoice.customer_name !== null &&
                          invoice.customer_name !== undefined &&
                          invoice.customer_name !== ''
                            ? 2
                            : 0,
                      }}
                    >
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Eladó: {invoice.supplier_name}
                      </Typography>
                      {invoice.supplier_tax_number !== null &&
                        invoice.supplier_tax_number !== undefined &&
                        invoice.supplier_tax_number !== '' && (
                          <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                            Magyar adószám: {invoice.supplier_tax_number}
                          </Typography>
                        )}
                      {invoice.supplier_bank_account_number !== null &&
                        invoice.supplier_bank_account_number !== undefined &&
                        invoice.supplier_bank_account_number !== '' && (
                          <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                            Bankszámlaszám: {invoice.supplier_bank_account_number}
                          </Typography>
                        )}

                      {/* Trusted Partner Status */}
                      <Box sx={{ mt: 1 }}>
                        {checkingTrustedStatus ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <CircularProgress size={14} />
                            <Typography variant="caption" color="text.secondary">
                              Ellenőrzés...
                            </Typography>
                          </Box>
                        ) : isSupplierTrusted ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <VerifiedIcon color="success" fontSize="small" />
                            <Typography
                              variant="caption"
                              color="success.main"
                              sx={{ fontWeight: 'medium' }}
                            >
                              Megbízható partner
                            </Typography>
                          </Box>
                        ) : (
                          invoice.supplier_tax_number !== null &&
                          invoice.supplier_tax_number !== undefined &&
                          invoice.supplier_tax_number !== '' && (
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<AddTrustedIcon />}
                              onClick={onAddTrustedPartner}
                              disabled={addingTrustedPartner}
                              sx={{ fontSize: '0.75rem', py: 0.5, px: 1 }}
                            >
                              {addingTrustedPartner ? 'Hozzáadás...' : 'Megbízható partner'}
                            </Button>
                          )
                        )}
                      </Box>
                    </Box>
                  )}

                {/* Customer Column */}
                {invoice.customer_name !== null &&
                  invoice.customer_name !== undefined &&
                  invoice.customer_name !== '' && (
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Vevő: {invoice.customer_name}
                      </Typography>
                      {invoice.customer_tax_number !== null &&
                        invoice.customer_tax_number !== undefined &&
                        invoice.customer_tax_number !== '' && (
                          <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                            Magyar adószám: {invoice.customer_tax_number}
                          </Typography>
                        )}
                      {invoice.customer_bank_account_number !== null &&
                        invoice.customer_bank_account_number !== undefined &&
                        invoice.customer_bank_account_number !== '' && (
                          <Typography variant="body2" sx={{ mb: 0.3, fontSize: '0.875rem' }}>
                            Bankszámlaszám: {invoice.customer_bank_account_number}
                          </Typography>
                        )}
                    </Box>
                  )}
              </Stack>

              {/* Details Row */}
              <Box sx={{ borderTop: '1px solid #e0e0e0', pt: 1.5, mb: 2 }}>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}>
                    Teljesítés:{' '}
                    {invoice.fulfillment_date_formatted !== null &&
                    invoice.fulfillment_date_formatted !== undefined &&
                    invoice.fulfillment_date_formatted !== ''
                      ? invoice.fulfillment_date_formatted
                      : invoice.issue_date_formatted}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}>
                    Keltezés: {invoice.issue_date_formatted}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}>
                    Fizetési határidő:{' '}
                    {invoice.payment_due_date_formatted !== null &&
                    invoice.payment_due_date_formatted !== undefined &&
                    invoice.payment_due_date_formatted !== ''
                      ? invoice.payment_due_date_formatted
                      : 'N/A'}
                  </Typography>
                  {invoice.original_invoice_number !== null &&
                    invoice.original_invoice_number !== undefined &&
                    invoice.original_invoice_number !== '' && (
                      <Typography
                        variant="body2"
                        sx={{ fontWeight: 'bold', minWidth: 'fit-content' }}
                      >
                        Eredeti szám: {invoice.original_invoice_number}
                      </Typography>
                    )}
                </Stack>
              </Box>

              {/* Summary Section */}
              <Box sx={{ backgroundColor: '#f9f9f9', p: 1.5, borderRadius: 1, mb: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  Számla összesítő:
                </Typography>

                <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
                  <Stack spacing={0.5} sx={{ flex: 1 }}>
                    {invoice.invoice_net_amount !== null && invoice.invoice_net_amount !== undefined && (
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          Számla nettó értéke
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {formatNumber(invoice.invoice_net_amount)} Ft
                        </Typography>
                      </Stack>
                    )}
                    {invoice.invoice_vat_amount !== null && invoice.invoice_vat_amount !== undefined && (
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="body2">Áfa összege</Typography>
                        <Typography variant="body2">
                          {formatNumber(invoice.invoice_vat_amount)} Ft
                        </Typography>
                      </Stack>
                    )}
                    <Stack
                      direction="row"
                      justifyContent="space-between"
                      sx={{ borderTop: '1px solid #ddd', pt: 0.5 }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        Számla bruttó végösszege
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {formatNumber(invoice.invoice_gross_amount)} Ft
                      </Typography>
                    </Stack>
                  </Stack>
                </Stack>
              </Box>

              {/* Line Items */}
              <Box>
                <Typography variant="subtitle1" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
                  Számla tételek
                </Typography>
                {lineItems.length > 0 ? (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Sor</TableCell>
                          <TableCell>Megnevezés</TableCell>
                          <TableCell align="right">Mennyiség</TableCell>
                          <TableCell align="right">Egységár</TableCell>
                          <TableCell align="right">Nettó</TableCell>
                          <TableCell align="right">ÁFA %</TableCell>
                          <TableCell align="right">ÁFA összeg</TableCell>
                          <TableCell align="right">Bruttó</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {lineItems.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell>{item.line_number}</TableCell>
                            <TableCell>{item.line_description}</TableCell>
                            <TableCell align="right">
                              {item.quantity !== null && item.quantity !== undefined
                                ? `${item.quantity} ${item.unit_of_measure}`
                                : '-'}
                            </TableCell>
                            <TableCell align="right">{formatNumber(item.unit_price)}</TableCell>
                            <TableCell align="right">{formatNumber(item.line_net_amount)}</TableCell>
                            <TableCell align="right">
                              {item.vat_rate !== null && item.vat_rate !== undefined
                                ? `${formatNumber(item.vat_rate)}%`
                                : '-'}
                            </TableCell>
                            <TableCell align="right">{formatNumber(item.line_vat_amount)}</TableCell>
                            <TableCell align="right">
                              {formatNumber(item.line_gross_amount)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">Nincsenek részletes tételek</Alert>
                )}
              </Box>
            </Box>
          )
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Bezárás</Button>
      </DialogActions>
    </Dialog>
  );
};

export default InvoiceDetailsModal;
