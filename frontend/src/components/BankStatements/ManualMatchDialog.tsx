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
  ArrowUpward,
  ArrowDownward,
  Search,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import { hu } from 'date-fns/locale';
import { BankTransaction } from '../../schemas/bankStatement.schemas';
import { NAVInvoiceSchemaType } from '../../schemas/api.schemas';
import { TransferWithBeneficiary } from '../../types/api';
import { useNAVInvoices, useTransfers, useBankTransactions } from '../../hooks/api';
import { useMatchTransactionToInvoice } from '../../hooks/api';
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
          <Tab label="Tranzakciók" value="transactions" />
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
                        <IconButton
                          size="small"
                          onClick={() => handleMatch(invoice.id)}
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
 * Transfer matching tab component.
 */
const TransferMatchTab: React.FC<TabProps> = ({
  transaction,
  searchTerm,
  onSearchChange,
  onMatch: _onMatch,
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

  // TODO: Implement useMatchTransactionToTransfer hook for transfer matching
  // const matchMutation = useMatchTransactionToTransfer();

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
        const beneficiaryName = transfer.beneficiary?.name?.toLowerCase() || '';
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

  const handleMatch = (_transferId: number): void => {
    // TODO: Implement transfer matching when backend endpoint is ready
    toast.error('Átutalás párosítás még nem implementált');
    // matchMutation.mutate(
    //   { transactionId: transaction.id, transferId },
    //   {
    //     onSuccess: () => {
    //       toast.success('Tranzakció sikeresen párosítva átutaláshoz');
    //       onMatch();
    //     },
    //     onError: (error: Error) => {
    //       toast.error(`Párosítás sikertelen: ${error.message}`);
    //     },
    //   }
    // );
  };

  const isCompatible = (_transfer: TransferWithBeneficiary): boolean => {
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
                      onClick={() => handleSort('beneficiary__name')}
                      endIcon={getSortIcon('beneficiary__name')}
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
                  const beneficiaryName = transfer.beneficiary?.name || 'N/A';

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
                          disabled={!compatible}
                          color="primary"
                          title={!compatible ? 'A tranzakció iránya nem kompatibilis' : 'Párosítás (még nem implementált)'}
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
  transaction,
  searchTerm,
  onSearchChange,
}): ReactElement => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [showOnlyOppositeSign, setShowOnlyOppositeSign] = useState(false);
  const toast = useToast();

  // Fetch transactions from the same statement
  const { data: transactionsData, isLoading } = useBankTransactions(
    transaction.bank_statement
  );

  const allTransactions = useMemo(
    () => transactionsData?.results ?? [],
    [transactionsData]
  );

  // Filter transactions: exclude current transaction, optionally filter by opposite sign
  const filteredTransactions = useMemo(() => {
    const currentAmount = parseFloat(transaction.amount);
    return allTransactions.filter((t) => {
      // Exclude the current transaction
      if (t.id === transaction.id) return false;

      // Optionally show only transactions with opposite sign (for reimbursement pairs)
      if (showOnlyOppositeSign) {
        const txAmount = parseFloat(t.amount);
        if (Math.sign(currentAmount) === Math.sign(txAmount)) return false;
      }

      // Apply search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        return (
          t.description?.toLowerCase().includes(search) ||
          t.reference?.toLowerCase().includes(search) ||
          t.payer_name?.toLowerCase().includes(search) ||
          t.beneficiary_name?.toLowerCase().includes(search)
        );
      }

      return true;
    });
  }, [allTransactions, transaction, searchTerm, showOnlyOppositeSign]);

  const paginatedTransactions = useMemo(() => {
    const start = page * rowsPerPage;
    return filteredTransactions.slice(start, start + rowsPerPage);
  }, [filteredTransactions, page, rowsPerPage]);

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  const totalInStatement = allTransactions.length - 1; // Exclude current transaction
  const currentAmount = parseFloat(transaction.amount);
  const isCurrentDebit = currentAmount < 0;

  return (
    <Stack spacing={2}>
      <TextField
        label="Keresés"
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        fullWidth
        placeholder="Keresés leírás, hivatkozás vagy partner szerint..."
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
      />

      <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography variant="body2" color="text.secondary">
            Összes tranzakció a kivonatban: <strong>{totalInStatement}</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            •
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Szűrt: <strong>{filteredTransactions.length}</strong>
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography variant="body2">
            Csak {isCurrentDebit ? 'jóváírások' : 'terhelések'}
          </Typography>
          <input
            type="checkbox"
            checked={showOnlyOppositeSign}
            onChange={(e) => {
              setShowOnlyOppositeSign(e.target.checked);
              setPage(0);
            }}
            style={{ cursor: 'pointer' }}
          />
        </Stack>
      </Stack>

      <Alert severity="info">
        {showOnlyOppositeSign ? (
          <>
            Visszatérítés párosításhoz válasszon egy ellentétes előjelű tranzakciót.
            (Jelenlegi tranzakció: <strong>{isCurrentDebit ? 'terhelés' : 'jóváírás'}</strong>, keresés: <strong>{isCurrentDebit ? 'jóváírások' : 'terhelések'}</strong>)
          </>
        ) : (
          <>
            Az összes tranzakció megjelenik. A visszatérítés párosításhoz kapcsolja be az "Csak {isCurrentDebit ? 'jóváírások' : 'terhelések'}" szűrőt.
          </>
        )}
      </Alert>

      {filteredTransactions.length === 0 ? (
        <Alert severity="warning">
          Nem található megfelelő tranzakció a párosításhoz.
          {showOnlyOppositeSign && (
            <> Próbálja meg kikapcsolni az ellentétes előjel szűrőt.</>
          )}
        </Alert>
      ) : (
        <>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Dátum</TableCell>
                  <TableCell>Típus</TableCell>
                  <TableCell>Partner</TableCell>
                  <TableCell>Leírás</TableCell>
                  <TableCell align="right">Összeg</TableCell>
                  <TableCell>Párosítás</TableCell>
                  <TableCell></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedTransactions.map((t) => {
                  const amount = parseFloat(t.amount);
                  const isCredit = amount > 0;

                  return (
                    <TableRow key={t.id} hover>
                      <TableCell>
                        {format(parseISO(t.booking_date), 'yyyy. MM. dd.', { locale: hu })}
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={0.5} alignItems="center">
                          {isCredit ? <ArrowUpward fontSize="small" color="success" /> : <ArrowDownward fontSize="small" color="error" />}
                          <Typography variant="body2">
                            {isCredit ? 'Jóváírás' : 'Terhelés'}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {isCredit ? t.payer_name : t.beneficiary_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {t.description || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          fontWeight="medium"
                          color={isCredit ? 'success.main' : 'error.main'}
                        >
                          {amount > 0 ? '+' : ''}{Math.abs(amount).toLocaleString('hu-HU', { minimumFractionDigits: 2 })} {t.currency}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {t.matched_invoice || t.matched_transfer || t.matched_reimbursement ? (
                          <Chip label="Párosítva" size="small" color="success" icon={<CheckIcon />} />
                        ) : (
                          <Chip label="Nincs" size="small" />
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          disabled
                          onClick={() => {
                            toast.warning('A manuális párosítás funkció hamarosan elérhető lesz');
                          }}
                        >
                          Párosítás
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={filteredTransactions.length}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            rowsPerPageOptions={[5, 10, 25]}
            labelRowsPerPage="Sorok száma:"
            labelDisplayedRows={({ from, to, count }) => `${from}–${to} / ${count}`}
          />
        </>
      )}
    </Stack>
  );
};

export default ManualMatchDialog;
