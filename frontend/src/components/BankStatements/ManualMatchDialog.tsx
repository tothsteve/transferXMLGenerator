/**
 * @fileoverview Manual matching dialog for bank transactions
 * @module components/BankStatements/ManualMatchDialog
 */

import { ReactElement, useState, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Tabs,
  Tab,
  Box,
  Stack,
  TextField,
  Typography,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Link as LinkIcon,
  ArrowUpward,
  ArrowDownward,
  Search,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';
import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { NAVInvoiceSchemaType } from '../../schemas/api.schemas';
import { Transfer } from '../../types/api';
import { useNAVInvoices, useTransfers } from '../../hooks/api';
import { useMatchTransactionToInvoice, useMatchTransactionToTransfer } from '../../hooks/api';
import { useToast } from '../../hooks/useToast';

/**
 * Tab type for the manual matching dialog.
 */
type MatchTabType = 'invoices' | 'transfers' | 'transactions';

/**
 * Props for ManualMatchDialog component.
 */
interface ManualMatchDialogProps {
  /** Whether dialog is open */
  open: boolean;
  /** Close handler */
  onClose: () => void;
  /** Transaction to match */
  transaction: BankTransaction | null;
  /** Callback after successful match */
  onMatchComplete: () => void;
}

/**
 * Manual matching dialog component.
 *
 * Provides tabbed interface for matching transactions to NAV invoices.
 */
const ManualMatchDialog: React.FC<ManualMatchDialogProps> = ({
  open,
  onClose,
  transaction,
  onMatchComplete,
}): ReactElement => {
  const [activeTab, setActiveTab] = useState<MatchTabType>('invoices');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const handleClose = (): void => {
    setSearchTerm('');
    setActiveTab('invoices');
    onClose();
  };

  const handleMatchSuccess = (): void => {
    onMatchComplete();
    handleClose();
  };

  if (!transaction) {
    return <></>;
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Tranzakció párosítása
        <Typography variant="body2" color="text.secondary">
          {transaction.description} • {transaction.amount} {transaction.currency}
        </Typography>
      </DialogTitle>
      <DialogContent>
        <Tabs
          value={activeTab}
          onChange={(_, val) => setActiveTab(val as MatchTabType)}
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
        >
          <Tab label="NAV Számlák" value="invoices" />
          <Tab label="Átutalások" value="transfers" />
          <Tab label="Tranzakciók" value="transactions" disabled />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {activeTab === 'invoices' && (
            <InvoiceMatchTab
              transaction={transaction}
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              onMatch={handleMatchSuccess}
            />
          )}
          {activeTab === 'transfers' && (
            <TransferMatchTab
              transaction={transaction}
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              onMatch={handleMatchSuccess}
            />
          )}
          {activeTab === 'transactions' && (
            <ReimbursementMatchTab
              transaction={transaction}
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              onMatch={handleMatchSuccess}
            />
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Props for tab components.
 */
interface TabProps {
  transaction: BankTransaction;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onMatch: () => void;
}

/**
 * Invoice matching tab component.
 */
const InvoiceMatchTab: React.FC<TabProps> = ({
  transaction,
  searchTerm,
  onSearchChange,
  onMatch,
}): ReactElement => {
  const toast = useToast();

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Sorting state
  const [ordering, setOrdering] = useState<string>('-issue_date');

  // Amount filtering state
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');

  // Fetch invoices with pagination
  const { data: invoicesData, isLoading, error } = useNAVInvoices({
    page: page + 1,
    page_size: rowsPerPage,
    ...(searchTerm && { search: searchTerm }),
    ...(ordering && { ordering }),
  });

  const matchMutation = useMatchTransactionToInvoice();

  // Filter invoices by amount range (client-side)
  const filteredInvoices = useMemo(() => {
    if (!invoicesData?.results) {
      return [];
    }

    let results = invoicesData.results;

    // Apply amount filtering
    if (minAmount !== '' || maxAmount !== '') {
      results = results.filter((invoice) => {
        const amount = typeof invoice.invoice_gross_amount === 'number'
          ? invoice.invoice_gross_amount
          : parseFloat(String(invoice.invoice_gross_amount));
        const min = minAmount !== '' ? parseFloat(minAmount) : -Infinity;
        const max = maxAmount !== '' ? parseFloat(maxAmount) : Infinity;
        return amount >= min && amount <= max;
      });
    }

    return results;
  }, [invoicesData, minAmount, maxAmount]);

  const totalCount = invoicesData?.count ?? 0;

  const handleMatch = (invoiceId: number): void => {
    matchMutation.mutate(
      { transactionId: transaction.id, invoiceId },
      {
        onSuccess: () => {
          toast.success('Tranzakció sikeresen párosítva számlához');
          onMatch();
        },
        onError: (error) => {
          toast.error(`Párosítás sikertelen: ${error.message}`);
        },
      }
    );
  };

  const isCompatible = (invoice: NAVInvoiceSchemaType): boolean => {
    // Check direction compatibility
    const amount = parseFloat(transaction.amount);
    if (invoice.invoice_direction === 'OUTBOUND') {
      // We issued invoice → expect incoming payment (CREDIT, amount > 0)
      return amount > 0;
    } else if (invoice.invoice_direction === 'INBOUND') {
      // We received invoice → expect outgoing payment (DEBIT, amount < 0)
      return amount < 0;
    }
    return true;
  };

  const formatAmount = (amount: string | number): string => {
    const num = typeof amount === 'number' ? amount : parseFloat(String(amount));
    return new Intl.NumberFormat('hu-HU', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  const handleSort = (field: string): void => {
    const isCurrentlyAsc = ordering === field;
    const newOrdering = isCurrentlyAsc ? `-${field}` : field;
    setOrdering(newOrdering);
    setPage(0);
  };

  const getSortIcon = (field: string): ReactElement | null => {
    if (ordering === field) {
      return <ArrowUpward sx={{ fontSize: 16 }} />;
    } else if (ordering === `-${field}`) {
      return <ArrowDownward sx={{ fontSize: 16 }} />;
    }
    return null;
  };

  const handlePageChange = (_event: unknown, newPage: number): void => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    onSearchChange(event.target.value);
    setPage(0);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Hiba történt a számlák betöltésekor: {error.message}
      </Alert>
    );
  }

  return (
    <Stack spacing={2}>
      {/* Search and Amount Filters */}
      <Stack direction="row" spacing={2} alignItems="center">
        <TextField
          placeholder="Keresés számlaszám vagy partner szerint..."
          value={searchTerm}
          onChange={handleSearchChange}
          size="small"
          sx={{ flex: 1 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
        />
        <TextField
          label="Min összeg"
          value={minAmount}
          onChange={(e) => setMinAmount(e.target.value)}
          size="small"
          type="number"
          sx={{ width: 120 }}
          placeholder="0"
        />
        <TextField
          label="Max összeg"
          value={maxAmount}
          onChange={(e) => setMaxAmount(e.target.value)}
          size="small"
          type="number"
          sx={{ width: 120 }}
          placeholder="∞"
        />
      </Stack>

      {filteredInvoices.length === 0 ? (
        <Alert severity="info">
          Nincs párosítható számla. Próbáljon más keresési feltételt használni.
        </Alert>
      ) : (
        <>
          <TableContainer sx={{ maxHeight: 400 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Irány</TableCell>
                  <TableCell>
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleSort('nav_invoice_number')}
                      endIcon={getSortIcon('nav_invoice_number')}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 600,
                        color: 'text.primary',
                        '&:hover': { backgroundColor: 'transparent' },
                      }}
                    >
                      Számlaszám
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleSort('partner_name')}
                      endIcon={getSortIcon('partner_name')}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 600,
                        color: 'text.primary',
                        '&:hover': { backgroundColor: 'transparent' },
                      }}
                    >
                      Partner
                    </Button>
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleSort('invoice_gross_amount')}
                      endIcon={getSortIcon('invoice_gross_amount')}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 600,
                        color: 'text.primary',
                        '&:hover': { backgroundColor: 'transparent' },
                      }}
                    >
                      Összeg
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleSort('issue_date')}
                      endIcon={getSortIcon('issue_date')}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 600,
                        color: 'text.primary',
                        '&:hover': { backgroundColor: 'transparent' },
                      }}
                    >
                      Kelte
                    </Button>
                  </TableCell>
                  <TableCell align="center">Párosítás</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredInvoices.map((invoice) => {
                  const compatible = isCompatible(invoice);
                  const direction = invoice.invoice_direction === 'OUTBOUND' ? '→' : '←';
                  const partnerName = invoice.partner_name;

                  return (
                    <TableRow
                      key={invoice.id}
                      hover
                      sx={{
                        backgroundColor: !compatible ? 'error.lighter' : undefined,
                      }}
                    >
                      <TableCell>
                        <Chip
                          label={direction}
                          size="small"
                          color={compatible ? 'success' : 'error'}
                          sx={{ minWidth: 40 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="500">
                          {invoice.nav_invoice_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {partnerName}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="500">
                          {formatAmount(invoice.invoice_gross_amount)} {invoice.currency_code}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {format(parseISO(invoice.issue_date), 'yyyy. MM. dd.', { locale: hu })}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        {invoice.is_matched_to_transaction ? (
                          <Chip
                            icon={<LinkIcon />}
                            label="Párosítva"
                            size="small"
                            color="info"
                            variant="outlined"
                          />
                        ) : (
                          <IconButton
                            size="small"
                            onClick={() => handleMatch(invoice.id)}
                            disabled={!compatible || matchMutation.isPending}
                            color="primary"
                            title={!compatible ? 'A tranzakció iránya nem kompatibilis' : 'Párosítás'}
                          >
                            <CheckIcon />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={totalCount}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handlePageChange}
            onRowsPerPageChange={handleRowsPerPageChange}
            labelRowsPerPage="Sorok száma:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
          />
        </>
      )}
    </Stack>
  );
};

/**
 * Transfer matching tab component.
 */
const TransferMatchTab: React.FC<TabProps> = ({
  transaction,
  searchTerm,
  onSearchChange,
  onMatch,
}): ReactElement => {
  const toast = useToast();

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Sorting state
  const [ordering, setOrdering] = useState<string>('-execution_date');

  // Amount filtering state
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');

  // Fetch transfers with pagination - only show processed transfers (used in batches)
  const { data: transfersData, isLoading, error } = useTransfers({
    page: page + 1,
    page_size: rowsPerPage,
    is_processed: true,  // Only show transfers that have been used in batches
    ...(ordering && { ordering }),
  });

  const matchMutation = useMatchTransactionToTransfer();

  // Filter transfers by search term and amount range (client-side)
  const filteredTransfers = useMemo(() => {
    if (!transfersData?.results) {
      return [];
    }

    let results = transfersData.results;

    // Apply search filter (beneficiary name or amount)
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      results = results.filter((transfer) => {
        const beneficiaryName = transfer.beneficiary_data?.name?.toLowerCase() || '';
        const amount = transfer.amount.toString();
        return beneficiaryName.includes(search) || amount.includes(search);
      });
    }

    // Apply amount filtering
    if (minAmount !== '' || maxAmount !== '') {
      results = results.filter((transfer) => {
        const amount = typeof transfer.amount === 'number'
          ? transfer.amount
          : parseFloat(String(transfer.amount));
        const min = minAmount !== '' ? parseFloat(minAmount) : -Infinity;
        const max = maxAmount !== '' ? parseFloat(maxAmount) : Infinity;
        return amount >= min && amount <= max;
      });
    }

    return results;
  }, [transfersData, searchTerm, minAmount, maxAmount]);

  const totalCount = transfersData?.count ?? 0;

  const handleMatch = (transferId: number): void => {
    matchMutation.mutate(
      { transactionId: transaction.id, transferId },
      {
        onSuccess: () => {
          toast.success('Tranzakció sikeresen párosítva átutaláshoz');
          onMatch();
        },
        onError: (error) => {
          toast.error(`Párosítás sikertelen: ${error.message}`);
        },
      }
    );
  };

  const isCompatible = (_transfer: Transfer): boolean => {
    // Check direction compatibility: transfer amounts are positive (outgoing payment)
    // So we expect negative transaction amount (DEBIT)
    const transactionAmount = parseFloat(transaction.amount);
    return transactionAmount < 0;
  };

  const formatAmount = (amount: string | number): string => {
    const num = typeof amount === 'number' ? amount : parseFloat(String(amount));
    return new Intl.NumberFormat('hu-HU', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  const handleSort = (field: string): void => {
    const isCurrentlyAsc = ordering === field;
    const newOrdering = isCurrentlyAsc ? `-${field}` : field;
    setOrdering(newOrdering);
    setPage(0);
  };

  const getSortIcon = (field: string): ReactElement | null => {
    if (ordering === field) {
      return <ArrowUpward sx={{ fontSize: 16 }} />;
    } else if (ordering === `-${field}`) {
      return <ArrowDownward sx={{ fontSize: 16 }} />;
    }
    return null;
  };

  const handlePageChange = (_event: unknown, newPage: number): void => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    onSearchChange(event.target.value);
    setPage(0);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Hiba történt az átutalások betöltésekor: {error.message}
      </Alert>
    );
  }

  return (
    <Stack spacing={2}>
      {/* Search and Amount Filters */}
      <Stack direction="row" spacing={2} alignItems="center">
        <TextField
          placeholder="Keresés kedvezményezett vagy összeg szerint..."
          value={searchTerm}
          onChange={handleSearchChange}
          size="small"
          sx={{ flex: 1 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
        />
        <TextField
          label="Min összeg"
          value={minAmount}
          onChange={(e) => setMinAmount(e.target.value)}
          size="small"
          type="number"
          sx={{ width: 120 }}
          placeholder="0"
        />
        <TextField
          label="Max összeg"
          value={maxAmount}
          onChange={(e) => setMaxAmount(e.target.value)}
          size="small"
          type="number"
          sx={{ width: 120 }}
          placeholder="∞"
        />
      </Stack>

      {filteredTransfers.length === 0 ? (
        <Alert severity="info">
          Nincs párosítható átutalás. Próbáljon más keresési feltételt használni.
        </Alert>
      ) : (
        <>
          <TableContainer sx={{ maxHeight: 400 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleSort('beneficiary_data__name')}
                      endIcon={getSortIcon('beneficiary_data__name')}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 600,
                        color: 'text.primary',
                        '&:hover': { backgroundColor: 'transparent' },
                      }}
                    >
                      Kedvezményezett
                    </Button>
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleSort('amount')}
                      endIcon={getSortIcon('amount')}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 600,
                        color: 'text.primary',
                        '&:hover': { backgroundColor: 'transparent' },
                      }}
                    >
                      Összeg
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleSort('execution_date')}
                      endIcon={getSortIcon('execution_date')}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 600,
                        color: 'text.primary',
                        '&:hover': { backgroundColor: 'transparent' },
                      }}
                    >
                      Végrehajtás dátuma
                    </Button>
                  </TableCell>
                  <TableCell>Közlemény</TableCell>
                  <TableCell align="center">Párosítás</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTransfers.map((transfer) => {
                  const compatible = isCompatible(transfer);
                  const beneficiaryName = transfer.beneficiary_data?.name || 'N/A';

                  return (
                    <TableRow
                      key={transfer.id}
                      hover
                      sx={{
                        backgroundColor: !compatible ? 'error.lighter' : undefined,
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight="500">
                          {beneficiaryName}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="500">
                          {formatAmount(transfer.amount)} {transfer.currency}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {format(parseISO(transfer.execution_date), 'yyyy. MM. dd.', { locale: hu })}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {transfer.remittance_info || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={() => handleMatch(transfer.id!)}
                          disabled={!compatible || matchMutation.isPending}
                          color="primary"
                          title={!compatible ? 'A tranzakció iránya nem kompatibilis' : 'Párosítás'}
                        >
                          <CheckIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={totalCount}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handlePageChange}
            onRowsPerPageChange={handleRowsPerPageChange}
            labelRowsPerPage="Sorok száma:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
          />
        </>
      )}
    </Stack>
  );
};

/**
 * Reimbursement pair matching tab component (stub - to be implemented).
 */
const ReimbursementMatchTab: React.FC<TabProps> = ({
  searchTerm,
  onSearchChange,
}): ReactElement => {
  return (
    <Stack spacing={2}>
      <TextField
        label="Keresés leírás szerint"
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        fullWidth
        placeholder="Írja be a tranzakció leírását..."
      />
      <Alert severity="info">
        A visszatérítés párosítás funkció hamarosan elérhető lesz.
      </Alert>
    </Stack>
  );
};

export default ManualMatchDialog;
