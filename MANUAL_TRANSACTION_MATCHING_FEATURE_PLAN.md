# Manual Transaction Matching & Categorization - Complete Feature Plan

## Status: Planning (0%)

**Completed:**
- ✅ Feature requirements defined
- ✅ Technical architecture designed
- ✅ Implementation plan approved

**Remaining:**
- ⏳ Backend service layer implementation
- ⏳ Backend API endpoints implementation
- ⏳ Frontend component implementation
- ⏳ Testing and validation

---

## 📋 Overview

### Business Case

The bank statement import feature automatically matches transactions to NAV invoices and executed transfers using various strategies (REFERENCE_EXACT, AMOUNT_IBAN, FUZZY_NAME, etc.). However, users need the ability to:

1. **Review and approve** low-confidence automatic matches (confidence < 0.95)
2. **Manually match** unmatched transactions to invoices, transfers, or other transactions
3. **Correct** incorrect automatic matches
4. **Categorize** transactions that don't need matching (bank fees, interest, etc.) as "Other Costs"
5. **Change transaction types** if auto-detection was incorrect

### User Workflow

#### Scenario 1: Approve Low-Confidence Match
```
User opens transaction details → sees FUZZY_NAME match (confidence 0.85)
→ clicks "Jóváhagy" (Approve) button → confidence updated to 1.00
→ invoice payment status updated to PAID (if applicable)
```

#### Scenario 2: Manual Invoice Match
```
User finds unmatched DEBIT transaction → clicks Actions menu → "Párosítás"
→ dialog opens with 3 tabs → selects "NAV Számlák" tab
→ searches for invoice by number or supplier → selects invoice
→ system validates direction compatibility → match created (confidence 1.00)
→ invoice status updated to PAID
```

#### Scenario 3: Categorize as Other Cost
```
User finds BANK_FEE transaction → clicks Actions menu → "Kategorizálás"
→ dialog opens with expense category selector → selects "Banki költségek"
→ enters description → saves → OtherCost record created
```

#### Scenario 4: Correct Transaction Type
```
User finds AFR_CREDIT mis-categorized as POS_PURCHASE
→ clicks Actions menu → "Típus módosítása" → selects correct type
→ transaction type updated → page refreshes
```

---

## 🔧 Backend Implementation

### Service Layer: ManualMatchingService

**File:** `backend/bank_transfers/services/manual_matching_service.py`

**Purpose:** Centralize validation and business logic for manual matching operations.

**Class Structure:**
```python
"""
Manual transaction matching service.

This service handles validation and business logic for manual matching operations,
including invoice matching, transfer matching, and expense categorization.

Classes:
    ManualMatchingService: Service for manual transaction matching operations.
"""

from decimal import Decimal
from typing import Optional, Tuple
from django.utils import timezone
from bank_transfers.models import (
    BankTransaction,
    Invoice,
    Transfer,
    OtherCost,
)


class ManualMatchingService:
    """
    Service for manual transaction matching operations.

    Provides validation and business logic for:
    - Invoice matching with direction compatibility checking
    - Transfer matching with batch validation
    - Reimbursement pair matching
    - Expense categorization
    - Match approval and confidence updates
    """

    @staticmethod
    def validate_invoice_match(
        transaction: BankTransaction,
        invoice: Invoice,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if transaction can match invoice.

        Checks:
        - Direction compatibility (INBOUND invoice → DEBIT, OUTBOUND → CREDIT)
        - Amount compatibility (within 1%)
        - Transaction type restrictions (BANK_FEE, INTEREST cannot match)

        Args:
            transaction: Bank transaction to validate
            invoice: NAV invoice to match

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> is_valid, error = service.validate_invoice_match(tx, inv)
            >>> if not is_valid:
            ...     return Response({'error': error}, status=400)
        """
        # Implementation under 50 lines
        pass

    @staticmethod
    def validate_transfer_match(
        transaction: BankTransaction,
        transfer: Transfer,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if transaction can match executed transfer.

        Checks:
        - Transaction must be DEBIT (outgoing payment)
        - Transfer must be in used_in_bank=True batch
        - Amount must match exactly
        - Beneficiary IBAN must match (if available)

        Args:
            transaction: Bank transaction to validate
            transfer: Executed transfer to match

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Implementation under 50 lines
        pass

    @staticmethod
    def validate_reimbursement_pair(
        transaction1: BankTransaction,
        transaction2: BankTransaction,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if two transactions can be paired as reimbursement.

        Checks:
        - Opposite signs (one positive, one negative)
        - Same absolute amount
        - Within 5 days of each other
        - Neither already matched

        Args:
            transaction1: First transaction
            transaction2: Second transaction

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Implementation under 50 lines
        pass

    @staticmethod
    def create_invoice_match(
        transaction: BankTransaction,
        invoice: Invoice,
        user,
    ) -> BankTransaction:
        """
        Create manual invoice match.

        Sets:
        - matched_invoice = invoice
        - match_confidence = 1.00 (manual)
        - match_method = 'MANUAL'
        - matched_at = now
        - matched_by = user

        Updates invoice payment status to PAID if confidence >= 0.95.

        Args:
            transaction: Transaction to match
            invoice: Invoice to match
            user: User performing the match

        Returns:
            Updated transaction instance

        Raises:
            ValueError: If validation fails
        """
        # Implementation under 50 lines
        pass

    @staticmethod
    def approve_match(
        transaction: BankTransaction,
        user,
    ) -> BankTransaction:
        """
        Approve existing low-confidence match.

        Updates:
        - match_confidence = 1.00
        - matched_at = now
        - matched_by = user
        - Invoice payment status to PAID (if matched_invoice)

        Args:
            transaction: Transaction with existing match
            user: User approving the match

        Returns:
            Updated transaction instance

        Raises:
            ValueError: If transaction has no match to approve
        """
        # Implementation under 50 lines
        pass


# File size limit: Keep under 500 lines
# Function size limit: Keep under 50 lines each
# Class size limit: Keep under 100 lines for each class
```

**Business Logic Rules (Inline):**

1. **Direction Compatibility for Invoices:**
   ```python
   if invoice.invoice_direction == 'OUTBOUND':  # We issued invoice
       if transaction.amount <= 0:
           return False, "OUTBOUND számla CREDIT tranzakciót igényel (fizetés érkezik)"

   if invoice.invoice_direction == 'INBOUND':  # We received invoice
       if transaction.amount >= 0:
           return False, "INBOUND számla DEBIT tranzakciót igényel (fizetés megy ki)"
   ```

2. **Transaction Type Restrictions:**
   ```python
   RESTRICTED_TYPES = ['BANK_FEE', 'INTEREST', 'CURRENCY_EXCHANGE', 'CORRECTION']
   if transaction.transaction_type in RESTRICTED_TYPES:
       return False, "Ez a tranzakció típus nem párosítható számlával"
   ```

3. **Confidence Score Rules:**
   - Manual matches: Always 1.00
   - Approved matches: Updated to 1.00
   - Auto-update payment status threshold: >= 0.95

4. **Transfer Match Requirements:**
   - Only DEBIT transactions (outgoing payments)
   - Transfer must be in batch with `used_in_bank=True`
   - Exact amount match required

### API Endpoints

**File:** `backend/bank_transfers/api_views.py` (update existing BankTransactionViewSet)

**Permission:** All endpoints use `RequireBankStatementImport` permission class

#### Endpoint 1: Match Invoice
```python
@action(detail=True, methods=['post'], url_path='match-invoice')
def match_invoice(self, request, pk=None):
    """
    Manually match transaction to NAV invoice.

    POST /api/bank-transactions/{id}/match-invoice/
    Body: {"invoice_id": 123}

    Returns:
        Updated transaction with matched_invoice, confidence 1.00

    Raises:
        400: If validation fails (direction incompatibility, etc.)
        404: If invoice not found or not accessible
    """
    transaction = self.get_object()
    invoice_id = request.data.get('invoice_id')

    # Use service layer for validation and creation
    try:
        service = ManualMatchingService()
        updated_tx = service.create_invoice_match(
            transaction=transaction,
            invoice=invoice,
            user=request.user,
        )
        serializer = self.get_serializer(updated_tx)
        return Response(serializer.data)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
```

#### Endpoint 2: Match Transfer
```python
@action(detail=True, methods=['post'], url_path='match-transfer')
def match_transfer(self, request, pk=None):
    """
    Manually match transaction to executed transfer.

    POST /api/bank-transactions/{id}/match-transfer/
    Body: {"transfer_id": 456}

    Returns:
        Updated transaction with matched_transfer, confidence 1.00

    Raises:
        400: If validation fails (not DEBIT, batch not used, etc.)
        404: If transfer not found or not accessible
    """
    # Implementation similar to match_invoice
    pass
```

#### Endpoint 3: Match Reimbursement
```python
@action(detail=True, methods=['post'], url_path='match-reimbursement')
def match_reimbursement(self, request, pk=None):
    """
    Manually pair two transactions as reimbursement.

    POST /api/bank-transactions/{id}/match-reimbursement/
    Body: {"other_transaction_id": 789}

    Returns:
        Both transactions updated with matched_reimbursement references

    Raises:
        400: If validation fails (same sign, already matched, etc.)
        404: If other transaction not found
    """
    # Implementation similar to match_invoice
    pass
```

#### Endpoint 4: Approve Match
```python
@action(detail=True, methods=['post'], url_path='approve-match')
def approve_match(self, request, pk=None):
    """
    Approve existing low-confidence match.

    POST /api/bank-transactions/{id}/approve-match/

    Updates confidence to 1.00 and triggers payment status update if applicable.

    Returns:
        Updated transaction with confidence 1.00

    Raises:
        400: If transaction has no match to approve
    """
    # Implementation using service layer
    pass
```

#### Endpoint 5: Unmatch (Enhanced)
```python
@action(detail=True, methods=['post'], url_path='unmatch')
def unmatch(self, request, pk=None):
    """
    Remove any type of match from transaction.

    POST /api/bank-transactions/{id}/unmatch/

    Clears:
    - matched_invoice (if present)
    - matched_transfer (if present)
    - matched_reimbursement (if present)
    - Resets confidence to 0.00
    - Clears match_method

    Note: Does NOT revert invoice payment status (requires manual review).

    Returns:
        Updated transaction with all matches cleared
    """
    transaction = self.get_object()

    # Clear all match types
    transaction.matched_invoice = None
    transaction.matched_transfer = None
    transaction.matched_reimbursement = None
    transaction.match_confidence = Decimal('0.00')
    transaction.match_method = ''
    transaction.matched_at = None
    transaction.matched_by = None
    transaction.save()

    serializer = self.get_serializer(transaction)
    return Response(serializer.data)
```

#### Endpoint 6: Rematch
```python
@action(detail=True, methods=['post'], url_path='rematch')
def rematch(self, request, pk=None):
    """
    Replace existing match with new match.

    POST /api/bank-transactions/{id}/rematch/
    Body: {
        "match_type": "invoice|transfer|reimbursement",
        "match_id": 123
    }

    Atomically removes old match and creates new match.

    Returns:
        Updated transaction with new match

    Raises:
        400: If validation fails or no existing match
    """
    # Implementation combining unmatch + new match in transaction
    pass
```

#### Endpoint 7: Categorize as Other Cost
```python
@action(detail=True, methods=['post'], url_path='categorize')
def categorize(self, request, pk=None):
    """
    Categorize transaction as Other Cost (expense).

    POST /api/bank-transactions/{id}/categorize/
    Body: {
        "category": "Banki költségek",
        "description": "Havi számlavezetési díj"
    }

    Creates OtherCost record linked to transaction.

    Returns:
        Created OtherCost record

    Raises:
        400: If transaction already has match or OtherCost
    """
    transaction = self.get_object()

    # Validate: no existing match or OtherCost
    if (transaction.matched_invoice or
        transaction.matched_transfer or
        transaction.matched_reimbursement):
        return Response(
            {'error': 'Már párosított tranzakció nem kategorizálható'},
            status=400
        )

    # Create OtherCost
    other_cost = OtherCost.objects.create(
        company=request.user.active_company,
        bank_transaction=transaction,
        category=request.data.get('category'),
        description=request.data.get('description'),
        amount=abs(transaction.amount),
        currency=transaction.currency,
        cost_date=transaction.booking_date,
    )

    serializer = OtherCostSerializer(other_cost)
    return Response(serializer.data, status=201)
```

#### Endpoint 8: Change Transaction Type
```python
@action(detail=True, methods=['post'], url_path='change-type')
def change_type(self, request, pk=None):
    """
    Change transaction type if auto-detection was incorrect.

    POST /api/bank-transactions/{id}/change-type/
    Body: {"transaction_type": "AFR_CREDIT"}

    Allowed types: All BankTransaction.TRANSACTION_TYPE_CHOICES

    Returns:
        Updated transaction with new type

    Raises:
        400: If invalid type or transaction already matched
    """
    transaction = self.get_object()
    new_type = request.data.get('transaction_type')

    # Validate type
    valid_types = [choice[0] for choice in BankTransaction.TRANSACTION_TYPE_CHOICES]
    if new_type not in valid_types:
        return Response(
            {'error': f'Érvénytelen tranzakció típus: {new_type}'},
            status=400
        )

    # Update type
    transaction.transaction_type = new_type
    transaction.save()

    serializer = self.get_serializer(transaction)
    return Response(serializer.data)
```

**Permission Configuration:**
```python
class BankTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Bank transaction management (read-only base + custom actions)"""
    serializer_class = BankTransactionSerializer
    permission_classes = [
        IsAuthenticated,
        IsCompanyMember,
        RequireBankStatementImport,  # ALL ENDPOINTS USE THIS
    ]
```

---

## 🎨 Frontend Implementation

### Component 1: ManualMatchDialog

**File:** `frontend/src/components/BankStatements/ManualMatchDialog.tsx`

**Purpose:** Main dialog for manual matching with 3 tabs (Invoices/Transfers/Transactions).

**Component Specification:**
```typescript
/**
 * @fileoverview Manual matching dialog for bank transactions
 * @module components/BankStatements/ManualMatchDialog
 */

import { ReactElement, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Tabs,
  Tab,
  Box,
} from '@mui/material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';

/**
 * Props for ManualMatchDialog component.
 *
 * @interface ManualMatchDialogProps
 */
interface ManualMatchDialogProps {
  /** Whether dialog is open */
  open: boolean;

  /** Close handler */
  onClose: () => void;

  /** Transaction to match */
  transaction: BankTransaction;

  /** Callback after successful match */
  onMatchComplete: () => void;
}

/**
 * Manual matching dialog component.
 *
 * Provides tabbed interface for matching transactions to:
 * - NAV Invoices (with search and filtering)
 * - Executed Transfers (from used_in_bank batches)
 * - Other Transactions (for reimbursement pairs)
 *
 * Features:
 * - Direction compatibility validation
 * - Amount and date range filtering
 * - Real-time search
 * - Optimistic updates with error rollback
 *
 * @component
 * @example
 * ```tsx
 * <ManualMatchDialog
 *   open={isOpen}
 *   onClose={handleClose}
 *   transaction={selectedTransaction}
 *   onMatchComplete={() => refetch()}
 * />
 * ```
 */
const ManualMatchDialog: React.FC<ManualMatchDialogProps> = ({
  open,
  onClose,
  transaction,
  onMatchComplete,
}): ReactElement => {
  const [activeTab, setActiveTab] = useState<'invoices' | 'transfers' | 'transactions'>('invoices');

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Tranzakció párosítása
      </DialogTitle>
      <DialogContent>
        <Tabs value={activeTab} onChange={(e, val) => setActiveTab(val)}>
          <Tab label="NAV Számlák" value="invoices" />
          <Tab label="Átutalások" value="transfers" />
          <Tab label="Tranzakciók" value="transactions" />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {activeTab === 'invoices' && (
            <InvoiceMatchTab
              transaction={transaction}
              onMatch={onMatchComplete}
              onClose={onClose}
            />
          )}
          {activeTab === 'transfers' && (
            <TransferMatchTab
              transaction={transaction}
              onMatch={onMatchComplete}
              onClose={onClose}
            />
          )}
          {activeTab === 'transactions' && (
            <ReimbursementMatchTab
              transaction={transaction}
              onMatch={onMatchComplete}
              onClose={onClose}
            />
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default ManualMatchDialog;
```

**Sub-Components (in same file, each under 200 lines):**

1. **InvoiceMatchTab**:
   - Search by invoice number or supplier name
   - Filter by date range, amount range, payment status
   - Display invoice cards with direction indicator
   - Disable incompatible invoices (direction check)
   - Match button with confirmation

2. **TransferMatchTab**:
   - Display transfers from used_in_bank=True batches only
   - Filter by date range, amount, beneficiary
   - Show batch information
   - Match button

3. **ReimbursementMatchTab**:
   - Display other transactions from same statement
   - Filter by opposite sign, amount range (±1%), date (±5 days)
   - Show transaction details
   - Pair button

**UI Rules (Inline):**

- **Direction Indicators**: Show "→" for DEBIT (outgoing), "←" for CREDIT (incoming)
- **Disabled States**: Gray out incompatible items with tooltip explanation
- **Amount Formatting**: Hungarian locale with sign (e.g., "-150 000 HUF", "+75 000 HUF")
- **Date Formatting**: Hungarian format "yyyy. MM. dd."
- **Search Debouncing**: 300ms delay for search input
- **Loading States**: Skeleton loaders while fetching data
- **Error Handling**: Toast notifications for errors, no inline error display

**State Management:**
```typescript
// React Query hooks
const { data: invoices, isLoading } = useInvoicesForMatching({
  company_id: companyId,
  amount_min: transaction.amount * 0.99,
  amount_max: transaction.amount * 1.01,
  date_from: addDays(transaction.booking_date, -7),
  date_to: addDays(transaction.booking_date, 7),
});

// Mutation with optimistic update
const matchMutation = useMutation({
  mutationFn: (invoiceId: number) =>
    matchTransactionToInvoice(transaction.id, invoiceId),
  onSuccess: () => {
    queryClient.invalidateQueries(['bank-transactions']);
    onMatchComplete();
    onClose();
  },
  onError: (error) => {
    toast.error(`Párosítás sikertelen: ${error.message}`);
  },
});
```

**Component Size:** Keep under 200 lines per component (split into 4 files if needed)

**Cognitive Complexity:** Keep under 15 per function

**Test Coverage:** Minimum 80% with tests for:
- Tab switching
- Search and filtering
- Direction compatibility validation
- Match button disabled states
- Error handling

### Component 2: TransactionActionsMenu

**File:** `frontend/src/components/BankStatements/TransactionActionsMenu.tsx`

**Purpose:** Dropdown menu with conditional actions based on transaction state.

**Component Specification:**
```typescript
/**
 * @fileoverview Transaction actions menu for bank transactions
 * @module components/BankStatements/TransactionActionsMenu
 */

import { ReactElement, useState } from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  MoreVert as MoreIcon,
  Link as MatchIcon,
  Check as ApproveIcon,
  LinkOff as UnmatchIcon,
  SwapHoriz as RematchIcon,
  Category as CategoryIcon,
  Edit as ChangeTypeIcon,
} from '@mui/icons-material';
import { BankTransaction } from '../../schemas/bankStatement.schemas';

/**
 * Props for TransactionActionsMenu component.
 *
 * @interface TransactionActionsMenuProps
 */
interface TransactionActionsMenuProps {
  /** Transaction to show actions for */
  transaction: BankTransaction;

  /** Callback when action is triggered */
  onAction: (action: string) => void;
}

/**
 * Transaction actions menu component.
 *
 * Displays context menu with actions based on transaction state:
 * - Unmatched: "Párosítás", "Kategorizálás", "Típus módosítása"
 * - Low confidence match: "Jóváhagy", "Újrapárosítás", "Párosítás törlése"
 * - High confidence match: "Újrapárosítás", "Párosítás törlése"
 * - Categorized: "Kategória szerkesztése", "Kategória törlése"
 *
 * @component
 * @example
 * ```tsx
 * <TransactionActionsMenu
 *   transaction={transaction}
 *   onAction={(action) => handleAction(transaction, action)}
 * />
 * ```
 */
const TransactionActionsMenu: React.FC<TransactionActionsMenuProps> = ({
  transaction,
  onAction,
}): ReactElement => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const hasMatch = transaction.matched_invoice !== null ||
                   transaction.matched_transfer !== null ||
                   transaction.matched_reimbursement !== null;

  const isLowConfidence = hasMatch && parseFloat(transaction.match_confidence) < 0.95;
  const hasCategorization = transaction.other_cost !== null;

  const handleClick = (event: React.MouseEvent<HTMLElement>): void => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = (): void => {
    setAnchorEl(null);
  };

  const handleAction = (action: string): void => {
    handleClose();
    onAction(action);
  };

  return (
    <>
      <IconButton size="small" onClick={handleClick}>
        <MoreIcon />
      </IconButton>

      <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
        {/* Unmatched transaction actions */}
        {!hasMatch && !hasCategorization && (
          <>
            <MenuItem onClick={() => handleAction('match')}>
              <ListItemIcon><MatchIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Párosítás</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAction('categorize')}>
              <ListItemIcon><CategoryIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Kategorizálás</ListItemText>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => handleAction('change-type')}>
              <ListItemIcon><ChangeTypeIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Típus módosítása</ListItemText>
            </MenuItem>
          </>
        )}

        {/* Low confidence match actions */}
        {isLowConfidence && (
          <>
            <MenuItem onClick={() => handleAction('approve')}>
              <ListItemIcon><ApproveIcon fontSize="small" color="success" /></ListItemIcon>
              <ListItemText>Jóváhagy</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAction('rematch')}>
              <ListItemIcon><RematchIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Újrapárosítás</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAction('unmatch')}>
              <ListItemIcon><UnmatchIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Párosítás törlése</ListItemText>
            </MenuItem>
          </>
        )}

        {/* High confidence match actions */}
        {hasMatch && !isLowConfidence && (
          <>
            <MenuItem onClick={() => handleAction('rematch')}>
              <ListItemIcon><RematchIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Újrapárosítás</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAction('unmatch')}>
              <ListItemIcon><UnmatchIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Párosítás törlése</ListItemText>
            </MenuItem>
          </>
        )}

        {/* Categorized transaction actions */}
        {hasCategorization && (
          <>
            <MenuItem onClick={() => handleAction('edit-category')}>
              <ListItemIcon><CategoryIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Kategória szerkesztése</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAction('remove-category')}>
              <ListItemIcon><UnmatchIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Kategória törlése</ListItemText>
            </MenuItem>
          </>
        )}
      </Menu>
    </>
  );
};

export default TransactionActionsMenu;
```

**Integration with TransactionRow:**
```typescript
// In TransactionRow.tsx, replace simple match button with actions menu
import TransactionActionsMenu from './TransactionActionsMenu';

<TableCell align="center">
  <TransactionActionsMenu
    transaction={transaction}
    onAction={(action) => handleAction(transaction, action)}
  />
</TableCell>
```

### Component 3: CategoryDialog

**File:** `frontend/src/components/BankStatements/CategoryDialog.tsx`

**Purpose:** Dialog for categorizing transactions as Other Costs.

**Component Specification:**
```typescript
/**
 * @fileoverview Expense categorization dialog for bank transactions
 * @module components/BankStatements/CategoryDialog
 */

import { ReactElement } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { BankTransaction } from '../../schemas/bankStatement.schemas';

/**
 * Form data schema for expense categorization.
 */
const categoryFormSchema = z.object({
  category: z.string().min(1, 'Kategória kötelező'),
  description: z.string().min(1, 'Leírás kötelező'),
});

type CategoryFormData = z.infer<typeof categoryFormSchema>;

/**
 * Props for CategoryDialog component.
 *
 * @interface CategoryDialogProps
 */
interface CategoryDialogProps {
  /** Whether dialog is open */
  open: boolean;

  /** Close handler */
  onClose: () => void;

  /** Transaction to categorize */
  transaction: BankTransaction;

  /** Callback after successful categorization */
  onCategorize: () => void;
}

/**
 * Expense categorization dialog component.
 *
 * Allows categorizing bank transactions as Other Costs with:
 * - Predefined expense categories
 * - Custom description
 * - Form validation with Zod
 *
 * @component
 * @example
 * ```tsx
 * <CategoryDialog
 *   open={isOpen}
 *   onClose={handleClose}
 *   transaction={transaction}
 *   onCategorize={() => refetch()}
 * />
 * ```
 */
const CategoryDialog: React.FC<CategoryDialogProps> = ({
  open,
  onClose,
  transaction,
  onCategorize,
}): ReactElement => {
  const { control, handleSubmit, formState: { errors } } = useForm<CategoryFormData>({
    resolver: zodResolver(categoryFormSchema),
    defaultValues: {
      category: '',
      description: transaction.description || '',
    },
  });

  const categorizeMutation = useMutation({
    mutationFn: (data: CategoryFormData) =>
      categorizeTransaction(transaction.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['bank-transactions']);
      onCategorize();
      onClose();
    },
    onError: (error) => {
      toast.error(`Kategorizálás sikertelen: ${error.message}`);
    },
  });

  const onSubmit = (data: CategoryFormData): void => {
    categorizeMutation.mutate(data);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Költség kategorizálása</DialogTitle>
      <DialogContent>
        <Controller
          name="category"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              select
              label="Kategória"
              fullWidth
              margin="normal"
              error={!!errors.category}
              helperText={errors.category?.message}
            >
              <MenuItem value="Banki költségek">Banki költségek</MenuItem>
              <MenuItem value="Kamat">Kamat</MenuItem>
              <MenuItem value="Devizaváltási díj">Devizaváltási díj</MenuItem>
              <MenuItem value="Kártya költségek">Kártya költségek</MenuItem>
              <MenuItem value="Egyéb költség">Egyéb költség</MenuItem>
            </TextField>
          )}
        />

        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Leírás"
              fullWidth
              margin="normal"
              multiline
              rows={3}
              error={!!errors.description}
              helperText={errors.description?.message}
            />
          )}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Mégse</Button>
        <Button
          onClick={handleSubmit(onSubmit)}
          variant="contained"
          disabled={categorizeMutation.isPending}
        >
          Mentés
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CategoryDialog;
```

**Expense Categories:**
- Banki költségek (Bank fees)
- Kamat (Interest)
- Devizaváltási díj (Currency exchange fee)
- Kártya költségek (Card fees)
- Egyéb költség (Other expense)

### Zod Schemas & API Hooks

**File:** `frontend/src/schemas/bankStatement.schemas.ts` (update existing)

**Add schemas for API responses:**
```typescript
/**
 * API response schema for match operations.
 */
export const matchResponseSchema = z.object({
  success: z.boolean(),
  data: bankTransactionSchema,
  error: z.string().optional(),
});

/**
 * API response schema for invoice matching validation.
 */
export const invoiceMatchValidationSchema = z.object({
  is_valid: z.boolean(),
  error_message: z.string().nullable(),
});

/**
 * Type exports for TypeScript.
 */
export type MatchResponse = z.infer<typeof matchResponseSchema>;
export type InvoiceMatchValidation = z.infer<typeof invoiceMatchValidationSchema>;
```

**File:** `frontend/src/hooks/useBankTransactions.ts` (create new)

**Add React Query hooks:**
```typescript
/**
 * Hook for matching transaction to invoice.
 */
export const useMatchInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ transactionId, invoiceId }: { transactionId: number; invoiceId: number }) => {
      const response = await api.post(
        `/bank-transactions/${transactionId}/match-invoice/`,
        { invoice_id: invoiceId }
      );
      return matchResponseSchema.parse(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['nav-invoices'] });
    },
  });
};

/**
 * Hook for approving existing match.
 */
export const useApproveMatch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (transactionId: number) => {
      const response = await api.post(
        `/bank-transactions/${transactionId}/approve-match/`
      );
      return matchResponseSchema.parse(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['nav-invoices'] });
    },
  });
};

// ... similar hooks for other endpoints
```

---

## 📅 Implementation Phases

### Phase 1: Backend Service Layer ⏳
- [ ] Create `services/manual_matching_service.py` with ManualMatchingService class
- [ ] Implement `validate_invoice_match()` method
- [ ] Implement `validate_transfer_match()` method
- [ ] Implement `validate_reimbursement_pair()` method
- [ ] Implement `create_invoice_match()` method
- [ ] Implement `approve_match()` method
- [ ] Write unit tests for all service methods (test_manual_matching_service.py)

### Phase 2: Backend API Endpoints ⏳
- [ ] Add 8 new endpoints to BankTransactionViewSet in api_views.py
  - [ ] `match_invoice` endpoint
  - [ ] `match_transfer` endpoint
  - [ ] `match_reimbursement` endpoint
  - [ ] `approve_match` endpoint
  - [ ] Enhanced `unmatch` endpoint
  - [ ] `rematch` endpoint
  - [ ] `categorize` endpoint
  - [ ] `change_type` endpoint
- [ ] Update Swagger documentation
- [ ] Test all endpoints with curl/Postman

### Phase 3: Frontend Components ⏳
- [ ] Create ManualMatchDialog.tsx with 3 tabs
  - [ ] InvoiceMatchTab sub-component
  - [ ] TransferMatchTab sub-component
  - [ ] ReimbursementMatchTab sub-component
- [ ] Create TransactionActionsMenu.tsx
- [ ] Create CategoryDialog.tsx
- [ ] Update TransactionRow.tsx to use TransactionActionsMenu
- [ ] Add Zod schemas to bankStatement.schemas.ts
- [ ] Create useBankTransactions.ts hook file with all mutations

### Phase 4: Testing & Validation ⏳
- [ ] Backend unit tests (80% coverage)
- [ ] Frontend component tests (80% coverage)
- [ ] Integration testing with real data
- [ ] Manual UI/UX testing
- [ ] Performance testing with large datasets
- [ ] Edge case testing (permissions, errors, etc.)

---

## 📁 Files to Create/Modify

### Backend Files (8 files)

**New Files:**
1. `backend/bank_transfers/services/manual_matching_service.py` - Service layer for matching logic
2. `backend/bank_transfers/tests/test_manual_matching_service.py` - Service unit tests

**Modified Files:**
3. `backend/bank_transfers/api_views.py` - Add 8 new endpoints to BankTransactionViewSet
4. `backend/bank_transfers/serializers.py` - Add OtherCostSerializer (if not exists)
5. `backend/bank_transfers/models.py` - Add other_cost field to BankTransaction (if not exists)
6. `backend/bank_transfers/tests/test_api_views.py` - Add endpoint tests
7. `backend/bank_transfers/admin.py` - Add OtherCost admin (if not exists)
8. `backend/bank_transfers/migrations/00XX_add_other_cost.py` - Migration for OtherCost (if needed)

### Frontend Files (11 files)

**New Files:**
9. `frontend/src/components/BankStatements/ManualMatchDialog.tsx` - Main matching dialog
10. `frontend/src/components/BankStatements/TransactionActionsMenu.tsx` - Actions dropdown menu
11. `frontend/src/components/BankStatements/CategoryDialog.tsx` - Expense categorization dialog
12. `frontend/src/hooks/useBankTransactions.ts` - React Query hooks for matching operations
13. `frontend/src/components/BankStatements/__tests__/ManualMatchDialog.test.tsx` - Component tests
14. `frontend/src/components/BankStatements/__tests__/TransactionActionsMenu.test.tsx` - Component tests
15. `frontend/src/components/BankStatements/__tests__/CategoryDialog.test.tsx` - Component tests

**Modified Files:**
16. `frontend/src/components/BankStatements/TransactionRow.tsx` - Replace match button with actions menu
17. `frontend/src/schemas/bankStatement.schemas.ts` - Add Zod schemas for API responses
18. `frontend/src/components/BankStatements/BankTransactionTable.tsx` - Update to handle new actions
19. `frontend/src/components/BankStatements/MatchDetailsCard.tsx` - Update to show approval status

---

## 🧪 Testing Strategy

### Backend Testing

**Unit Tests (test_manual_matching_service.py):**
```python
class TestManualMatchingService:
    """Tests for ManualMatchingService."""

    def test_validate_invoice_match_direction_outbound_credit_valid(self):
        """OUTBOUND invoice + CREDIT transaction = valid"""
        # Test implementation

    def test_validate_invoice_match_direction_outbound_debit_invalid(self):
        """OUTBOUND invoice + DEBIT transaction = invalid"""
        # Test implementation

    def test_validate_invoice_match_restricted_type_bank_fee(self):
        """BANK_FEE transaction cannot match invoice"""
        # Test implementation

    def test_create_invoice_match_sets_confidence_to_1(self):
        """Manual match sets confidence to 1.00"""
        # Test implementation

    def test_approve_match_updates_invoice_payment_status(self):
        """Approve match with confidence >= 0.95 updates invoice to PAID"""
        # Test implementation
```

**API Tests (test_api_views.py):**
```python
class TestBankTransactionViewSet:
    """Tests for BankTransaction API endpoints."""

    def test_match_invoice_success(self):
        """POST /match-invoice/ with valid data creates match"""
        # Test implementation

    def test_match_invoice_direction_incompatible(self):
        """POST /match-invoice/ with wrong direction returns 400"""
        # Test implementation

    def test_approve_match_no_existing_match(self):
        """POST /approve-match/ with no match returns 400"""
        # Test implementation

    def test_categorize_already_matched(self):
        """POST /categorize/ with matched transaction returns 400"""
        # Test implementation
```

### Frontend Testing

**Component Tests:**
```typescript
// ManualMatchDialog.test.tsx
describe('ManualMatchDialog', () => {
  it('renders with 3 tabs', () => {
    // Test implementation
  });

  it('switches tabs correctly', () => {
    // Test implementation
  });

  it('filters invoices by direction compatibility', () => {
    // Test implementation
  });

  it('disables match button for incompatible invoices', () => {
    // Test implementation
  });

  it('shows error toast on match failure', () => {
    // Test implementation
  });
});

// TransactionActionsMenu.test.tsx
describe('TransactionActionsMenu', () => {
  it('shows match action for unmatched transaction', () => {
    // Test implementation
  });

  it('shows approve action for low confidence match', () => {
    // Test implementation
  });

  it('hides approve action for high confidence match', () => {
    // Test implementation
  });

  it('calls onAction with correct action type', () => {
    // Test implementation
  });
});
```

**Integration Tests:**
- Full workflow: Open dialog → search invoice → match → verify UI update
- Error handling: API error → rollback → show toast
- Optimistic updates: Immediate UI update → API call → revert on error

---

## 🎯 Success Criteria

1. **Backend:**
   - ✅ All 8 endpoints implemented with RequireBankStatementImport permission
   - ✅ Service layer with validation logic under 50 lines per function
   - ✅ 80% test coverage with unit and API tests
   - ✅ Google-style docstrings for all functions

2. **Frontend:**
   - ✅ 3 components under 200 lines each
   - ✅ JSDoc documentation for all components
   - ✅ Zod validation for all API responses
   - ✅ 80% test coverage with component tests
   - ✅ Optimistic updates with error rollback
   - ✅ Hungarian localization

3. **User Experience:**
   - ✅ Direction compatibility validation prevents false matches
   - ✅ Clear visual feedback for all actions
   - ✅ Fast interactions with optimistic updates
   - ✅ Comprehensive error messages

4. **Performance:**
   - ✅ Dialog opens in < 200ms
   - ✅ Search with debouncing (300ms)
   - ✅ No UI blocking during API calls

---

## 📝 Notes

- **Permission Model**: All endpoints use `RequireBankStatementImport` for now (may expand with more granular permissions later)
- **Code Size Limits**: Strictly enforced (50 lines/function, 100 lines/class, 500 lines/file, 200 lines/component)
- **Documentation**: Google-style (backend) + JSDoc (frontend) required for all new code
- **Testing**: 80% minimum coverage for both backend and frontend
- **Validation**: Zod schemas for ALL external data (API responses, user input)
- **State Management**: React Query with optimistic updates and error rollback
- **Hungarian Localization**: All UI text, error messages, and labels in Hungarian

---

**Last Updated:** 2025-01-26
**Status:** Ready for implementation
