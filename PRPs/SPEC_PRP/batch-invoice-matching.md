name: "Batch Invoice Matching - Multi-Invoice Payment Support"
description: |
  Enable matching a single bank transaction to multiple NAV invoices when paying several invoices from the same supplier in one combined payment.

---

## Goal

**Feature Goal**: Support automatic and manual matching of a single bank transaction to 2-5 NAV invoices when a company pays multiple invoices from the same supplier in one combined payment.

**Deliverable**:
- Database schema supporting ManyToMany relationship between BankTransaction and Invoice
- Batch matching algorithm (Strategy 2c) integrated into existing priority cascade
- API endpoints returning multiple matched invoices per transaction
- Frontend UI displaying batch matches with expandable invoice details
- Manual batch matching dialog for user-initiated matching

**Success Definition**:
- A bank transaction of 450 HUF automatically matches to 3 invoices (100 HUF + 150 HUF + 200 HUF) from the same supplier
- All 3 invoices are auto-marked as PAID if confidence ≥0.90
- Frontend displays "3 számlák" badge with expandable table showing all matched invoices
- Users can manually select and match multiple invoices to a single transaction

## User Persona

**Target User**: Financial Administrator / Accountant at SMB companies using the transferXMLGenerator system

**Use Case**:
- Company receives 3-5 small invoices from IT Cardigan Kft. during the month
- Instead of making 3-5 separate bank transfers, finance team combines them into one payment of total amount
- User uploads bank statement and expects system to automatically match the combined payment to all invoices
- For edge cases, user needs manual interface to select and match multiple invoices

**User Journey**:
1. User receives bank statement showing single debit of 450 HUF to IT Cardigan Kft.
2. User uploads PDF bank statement via "Banki Kivonatok" screen
3. System automatically parses statement and finds 3 unpaid invoices (100, 150, 200 HUF) from IT Cardigan Kft.
4. System matches transaction to all 3 invoices with confidence 0.95 (IBAN + name match)
5. All 3 invoices auto-marked as PAID (confidence ≥ 0.90 threshold)
6. User sees transaction row with badge "3 számlák" instead of single invoice number
7. User clicks badge to expand and see all 3 matched invoices in sub-table
8. User verifies match is correct and continues with reconciliation

**Pain Points Addressed**:
- ❌ **Current**: User must manually match each invoice separately or leave transaction unmatched
- ❌ **Current**: No way to represent "this payment covers these 3 invoices" in the system
- ❌ **Current**: Invoice payment status remains UNPAID even though payment was made
- ✅ **Solution**: Automatic detection and matching of batch payments with high confidence
- ✅ **Solution**: Clear UI showing all invoices covered by a single payment
- ✅ **Solution**: All invoices correctly marked as PAID in one operation

## Why

**Business Value**:
- Reduces manual reconciliation work by 60-70% for batch payments (common scenario)
- Improves cash flow visibility by accurately tracking which invoices are paid
- Prevents duplicate payments by marking all invoices as PAID automatically
- Supports real-world business practice of combining small payments

**Integration with Existing Features**:
- Extends existing 7 matching strategies (TRANSFER_EXACT, REFERENCE_EXACT, AMOUNT_IBAN, FUZZY_NAME, etc.)
- Reuses existing invoice candidate filtering (`_get_candidate_invoices`)
- Maintains backward compatibility with single-invoice matches
- Works with existing auto-payment threshold logic (confidence ≥ 0.90)

**Problems Solved**:
- **For Finance Teams**: No more manual matching of combined payments
- **For Accountants**: Accurate invoice payment tracking reduces audit errors
- **For Management**: Better cash flow reporting with accurate payment dates
- **For System**: Reduces unmatched transactions, improves match rate KPI

## What

### User-Visible Behavior

**Automatic Matching**:
- When bank statement is uploaded, system tries to match each transaction
- For debit transactions with no single-invoice match, system tries batch matching
- Searches for combinations of 2-5 invoices from same supplier where sum ≈ transaction amount
- If found with confidence ≥ 0.90, auto-marks all invoices as PAID
- Transaction displays badge with invoice count (e.g., "3 számlák")

**Manual Matching**:
- User can click "Batch Match" button on unmatched transaction
- Dialog opens with multi-select invoice dropdown
- User filters/searches invoices by supplier, date, amount
- System shows real-time total: "Selected: 450 HUF / Transaction: 450 HUF"
- Color indicator: green (exact), yellow (within 5%), red (>5% difference)
- User can force match even if amounts differ (with warning)
- On submit, all invoices linked to transaction with confidence 1.00

**Display**:
- Transaction table shows "3 számlák" chip instead of invoice number
- Click chip to expand row showing sub-table with all invoices
- Sub-table columns: Invoice Number, Supplier, Amount, Confidence
- Each invoice number is clickable link to invoice detail
- Total row at bottom shows sum of matched amounts

### Technical Requirements

**Database**:
- Add `BankTransactionInvoiceMatch` intermediate model (ManyToMany through table)
- Migrate existing single `matched_invoice` ForeignKey data to `matched_invoices` ManyToMany
- Keep `matched_invoice` for backward compatibility (mark deprecated)
- Add indexes for performance: `(transaction_id, invoice_id)`, `(invoice_id)`

**Backend**:
- Implement `_match_by_batch_invoices()` algorithm in `TransactionMatchingService`
- Insert batch matching as Strategy 2c in priority cascade (after AMOUNT_IBAN, before FUZZY_NAME)
- Update serializers to return `matched_invoices` array with metadata per invoice
- Add `POST /api/bank-transactions/{id}/batch_match_invoices/` endpoint
- Update `unmatch` endpoint to clear all batch matches

**Frontend**:
- Update TypeScript interfaces: `matched_invoices: BankTransactionInvoiceMatch[]`
- Update transaction table to render badge and expandable rows
- Create `BatchMatchDialog` component with multi-select and real-time total
- Add "Batch Match" action button to transaction menu

**Algorithm**:
- Group candidate invoices by `(supplier_tax_number, supplier_name)`
- Try combinations of 2, 3, 4, 5 invoices (skip if >20 invoices per supplier)
- Calculate sum for each combination, check if within 1% tolerance of transaction amount
- Confidence: base 0.85 + IBAN bonus (+0.10) + name similarity bonus (+0.05)
- Verify all invoices pass direction compatibility check
- Return best match (highest confidence)

### Success Criteria

- [x] Database supports ManyToMany relationship between BankTransaction and Invoice
- [x] Automatic batch matching finds 2-5 invoice combinations matching transaction amount (within 1% tolerance)
- [x] Confidence scoring: 0.85 base + 0.10 IBAN + 0.05 name = up to 1.00
- [x] High-confidence matches (≥0.90) auto-mark ALL invoices as PAID
- [x] API returns `matched_invoices` array with per-invoice metadata (confidence, method, notes)
- [x] Frontend displays "3 számlák" badge with expandable invoice table
- [x] Manual batch matching dialog validates supplier consistency and shows real-time total
- [x] Unmatch clears all matched invoices (both single and batch)
- [x] Backward compatible: existing single-invoice matches continue working
- [x] Performance: Algorithm completes in <2 seconds for 50 candidate invoices
- [x] All unit tests pass (20+ test cases covering edge cases)
- [x] Documentation updated (DATABASE_DOCUMENTATION.md, FEATURES.md, SQL comments)

## All Needed Context

### Context Completeness Check

✅ **Validated**: Implementation requires understanding of:
1. Existing bank statement matching system (7 strategies, priority cascade)
2. Django REST Framework patterns (ViewSets, Serializers, permissions)
3. React + TypeScript + MUI DataGrid patterns
4. Database migration with data preservation (existing matches)
5. Combinatorial algorithm design (performance considerations)

All necessary context is provided below.

### Documentation & References

```yaml
# MUST READ - Core matching logic
- file: backend/bank_transfers/services/transaction_matching_service.py
  why: Understand existing 7 matching strategies and priority cascade
  pattern: Study _match_by_amount_iban(), _match_by_fuzzy_name() for algorithm structure
  critical: |
    - All methods return Tuple[Optional[Invoice], Decimal] - need to change to List[Invoice]
    - _get_candidate_invoices() filters by date/direction - reuse this
    - _is_direction_compatible() must pass for ALL invoices in batch
    - AUTO_PAYMENT_THRESHOLD = 0.90 triggers invoice.mark_as_paid()
  gotcha: |
    - matched_invoice is ForeignKey (single), not ManyToMany
    - Need backward compatibility during migration

# MUST READ - Database schema
- file: backend/bank_transfers/models.py
  why: Understand BankTransaction and Invoice models
  pattern: Follow CompanyOwnedTimestampedModel base class pattern
  critical: |
    - BankTransaction.matched_invoice (line ~1641) is ForeignKey - single invoice only
    - Need to add matched_invoices ManyToManyField with through='BankTransactionInvoiceMatch'
    - Invoice.mark_as_paid() method exists - use for auto-payment
  gotcha: |
    - Must use 'through' model to store per-match metadata (confidence, method, notes)
    - Related_name conflicts: use 'bank_transactions_many' for new ManyToMany

# MUST READ - Existing manual matching plan
- file: MANUAL_TRANSACTION_MATCHING_FEATURE_PLAN.md
  why: Understand planned manual matching UI patterns
  section: "Manual Invoice Match" (line 40-45)
  critical: |
    - Dialog-based UI with tabs for different match types
    - Validation of direction compatibility required
    - match_confidence = 1.00 for manual matches
  pattern: Follow dialog structure for BatchMatchDialog component

# MUST READ - Bank statement documentation
- file: BANK_STATEMENT_IMPORT_DOCUMENTATION.md
  why: Understand transaction matching workflow
  section: "Transaction Matching" (line ~300-500)
  critical: |
    - Matching runs automatically after PDF parse completes
    - 7 strategies tried in priority order (cascade)
    - Each strategy has specific confidence level
  gotcha: |
    - Performance: Parser processes 100+ transactions per statement
    - Need to limit combinatorial search to prevent timeouts

# MUST READ - Existing SPEC_PRP example
- file: PRPs/SPEC_PRP/base-tables-feature.md
  why: Follow established PRP structure and detail level
  pattern: Study Implementation Notes, Low-Level Tasks structure
  critical: |
    - Include database migration strategy (additive, then migrate data)
    - Document performance indexes
    - Detail TypeScript interface changes

# MUST READ - Django coding standards
- file: backend/CLAUDE-PYTHON-BASIC.md
  why: Follow Django/DRF patterns for models, serializers, views
  section: "Django Models", "Django REST Framework"
  critical: |
    - Use select_related() and prefetch_related() to avoid N+1 queries
    - ViewSets with action decorators for custom endpoints
    - Serializer nested relationships for invoice_data expansion

# MUST READ - React coding standards
- file: frontend/CLAUDE-REACT.md
  why: Follow React 19 + TypeScript + Zod patterns
  section: "Data Validation with Zod", "Component Guidelines"
  critical: |
    - MANDATORY: Zod schemas for all external data (API responses)
    - Use React Query for state management (caching, optimistic updates)
    - MUI DataGrid for table rendering with expandable rows

# HELPFUL - Feature flag system (may need new permission)
- file: FEATURES.md
  section: "Bank Statement Import" (line ~200)
  why: Understand existing feature structure - may need to document batch matching
  pattern: No new feature flag needed - part of BANK_STATEMENT_IMPORT feature
```

### Current Codebase Tree (Relevant Sections)

```bash
transferXMLGenerator/
├── backend/
│   ├── bank_transfers/
│   │   ├── models.py                      # BankTransaction, Invoice models
│   │   ├── serializers.py                 # BankTransactionSerializer
│   │   ├── api_views.py                   # BankTransactionViewSet with match/unmatch endpoints
│   │   ├── services/
│   │   │   ├── transaction_matching_service.py  # 7 matching strategies
│   │   │   └── bank_statement_parser_service.py # Orchestrates matching after parse
│   │   ├── migrations/
│   │   │   └── 0060_add_billingo_related_documents.py  # Latest migration
│   │   └── tests/
│   │       └── # Need to add: test_batch_matching.py
│   ├── sql/
│   │   ├── complete_database_comments_postgresql.sql
│   │   └── complete_database_comments_sqlserver.sql
│   └── DATABASE_DOCUMENTATION.md
├── frontend/
│   ├── src/
│   │   ├── types/
│   │   │   └── api.ts                    # BankTransaction interface
│   │   ├── components/
│   │   │   └── BankStatements/
│   │   │       ├── BankStatementDetails.tsx  # Transaction table
│   │   │       └── ManualMatchDialog.tsx     # Single invoice matching
│   │   ├── services/
│   │   │   └── api.ts                    # API client methods
│   │   └── hooks/
│   │       └── api.ts                    # React Query hooks
├── PRPs/
│   ├── SPEC_PRP/
│   │   ├── base-tables-feature.md        # Reference example
│   │   └── batch-invoice-matching.md     # THIS FILE
│   └── templates/
│       └── prp_base.md                   # Template
├── BANK_STATEMENT_IMPORT_DOCUMENTATION.md
├── MANUAL_TRANSACTION_MATCHING_FEATURE_PLAN.md
└── FEATURES.md
```

### Desired Codebase Tree (Files to ADD/MODIFY)

```bash
backend/
├── bank_transfers/
│   ├── models.py                                    # MODIFY: Add BankTransactionInvoiceMatch model
│   ├── serializers.py                               # MODIFY: Add matched_invoices field
│   ├── api_views.py                                 # MODIFY: Add batch_match_invoices endpoint
│   ├── services/
│   │   └── transaction_matching_service.py          # MODIFY: Add _match_by_batch_invoices()
│   ├── migrations/
│   │   ├── 0061_add_batch_invoice_matching.py       # CREATE: Schema migration
│   │   └── 0062_migrate_single_matches_to_many.py   # CREATE: Data migration
│   └── tests/
│       ├── test_batch_matching.py                   # CREATE: Unit tests
│       └── test_batch_matching_integration.py       # CREATE: Integration tests
├── sql/
│   ├── complete_database_comments_postgresql.sql    # MODIFY: Add BankTransactionInvoiceMatch
│   └── complete_database_comments_sqlserver.sql     # MODIFY: Add BankTransactionInvoiceMatch
└── DATABASE_DOCUMENTATION.md                        # MODIFY: Document new table

frontend/
└── src/
    ├── types/
    │   └── api.ts                                   # MODIFY: Add matched_invoices interface
    ├── components/
    │   └── BankStatements/
    │       ├── BankStatementDetails.tsx             # MODIFY: Add badge + expandable rows
    │       └── BatchMatchDialog.tsx                 # CREATE: Manual batch matching UI
    ├── services/
    │   └── api.ts                                   # MODIFY: Add batchMatchInvoices() method
    └── hooks/
        └── api.ts                                   # MODIFY: Add useBatchMatchInvoices hook

PRPs/
└── DEPLOYMENT/
    └── batch-matching-rollout.md                    # CREATE: Deployment checklist

FEATURES.md                                          # MODIFY: Add batch matching to Bank Statement Import
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Django ManyToMany 'through' model requirements
# When using ManyToManyField with through='Model', Django requires:
# 1. The through model MUST have ForeignKeys to both sides
# 2. Cannot use .add(), .create(), .set() - must create through instances manually
# 3. Must include unique_together constraint to prevent duplicate matches
# Example:
matched_invoices = models.ManyToManyField(
    'Invoice',
    through='BankTransactionInvoiceMatch',  # Intermediate model
    related_name='bank_transactions_many'   # Avoid conflict with existing 'bank_transactions'
)

# CRITICAL: Python itertools.combinations() performance
# combinations(20, 5) = 15,504 combinations - manageable
# combinations(50, 5) = 2,118,760 combinations - TOO SLOW
# SOLUTION: Skip supplier groups with >20 invoices to prevent timeout
from itertools import combinations
if len(supplier_invoices) > 20:
    logger.warning(f"Skipping supplier {tax_number}: {len(supplier_invoices)} invoices (max 20)")
    continue

# CRITICAL: Django ORM N+1 query prevention
# When checking invoice amounts in loop, use select_related/prefetch_related
candidate_invoices = Invoice.objects.filter(...).select_related('company')
# NOT: for invoice in Invoice.objects.filter(...):  # N+1 queries!

# CRITICAL: Decimal precision for money calculations
# Python floats lose precision: 100.00 + 150.00 + 200.00 might != 450.00
# SOLUTION: Use Decimal for all amount calculations
from decimal import Decimal
total = sum(Decimal(str(inv.invoice_gross_amount)) for inv in combo)
tolerance = transaction_amount * Decimal('0.01')  # 1% tolerance
if abs(total - transaction_amount) <= tolerance:  # Safe comparison

# GOTCHA: React Query cache invalidation for batch matches
# After batch match, must invalidate BOTH transaction AND invoice queries
queryClient.invalidateQueries(['bankTransactions'])
queryClient.invalidateQueries(['invoices'])
# Otherwise, UI shows stale invoice payment status

# GOTCHA: MUI DataGrid expandable rows require unique row IDs
# When nesting invoice table inside transaction row, each invoice needs unique ID
# Use transaction.id + invoice.id combination to avoid conflicts
const expandedRowId = `${transaction.id}-${invoice.id}`;
```

## Implementation Blueprint

### Data Models and Structure

#### Backend: Django Models

```python
# File: backend/bank_transfers/models.py
# Location: After Invoice model, before BankTransaction model

class BankTransactionInvoiceMatch(models.Model):
    """
    Intermediate model for ManyToMany relationship between BankTransaction and Invoice.

    Stores per-invoice match metadata (confidence, method, notes) for both single
    and batch invoice matching. Replaces the deprecated matched_invoice ForeignKey.

    Business Logic:
    - Used for BOTH single and batch invoice matching
    - match_method = 'BATCH_INVOICES' for automatic batch matches
    - match_method = 'MANUAL_BATCH' for user-created batch matches
    - match_confidence = 1.00 for all manual matches

    Performance:
    - Unique index on (transaction, invoice) prevents duplicate matches
    - Index on invoice_id for reverse lookups (all transactions for an invoice)
    """
    transaction = models.ForeignKey(
        'BankTransaction',
        on_delete=models.CASCADE,
        related_name='invoice_matches',
        verbose_name='Bank tranzakció',
        help_text='The bank transaction that was matched'
    )
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='transaction_matches',
        verbose_name='NAV számla',
        help_text='The NAV invoice that was matched'
    )
    match_confidence = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Párosítás megbízhatósága',
        help_text='Match confidence score (0.00-1.00)'
    )
    match_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Párosítási módszer',
        help_text='Matching method used (BATCH_INVOICES, MANUAL_BATCH, etc.)',
        choices=[
            ('REFERENCE_EXACT', 'Reference Exact Match'),
            ('AMOUNT_IBAN', 'Amount + IBAN Match'),
            ('BATCH_INVOICES', 'Batch Invoice Match'),
            ('FUZZY_NAME', 'Fuzzy Name Match'),
            ('AMOUNT_DATE_ONLY', 'Amount + Date Only'),
            ('MANUAL', 'Manual Single Match'),
            ('MANUAL_BATCH', 'Manual Batch Match'),
        ]
    )
    matched_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Párosítás időpontja',
        help_text='When the match was created'
    )
    matched_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Párosította',
        help_text='User who created manual match (NULL for automatic)'
    )
    match_notes = models.TextField(
        blank=True,
        verbose_name='Párosítási megjegyzések',
        help_text='Detailed match information for audit trail'
    )

    class Meta:
        db_table = 'bank_transfers_banktransactioninvoicematch'
        verbose_name = 'Tranzakció-számla párosítás'
        verbose_name_plural = 'Tranzakció-számla párosítások'
        unique_together = [['transaction', 'invoice']]
        indexes = [
            models.Index(fields=['transaction', 'invoice'], name='idx_tx_invoice_match'),
            models.Index(fields=['invoice'], name='idx_invoice_matches'),
        ]
        ordering = ['transaction', 'invoice']

    def __str__(self):
        return f"Transaction {self.transaction.id} → Invoice {self.invoice.nav_invoice_number} ({self.match_confidence})"


# MODIFY: BankTransaction model (around line 1437)
class BankTransaction(CompanyOwnedTimestampedModel):
    # ... existing fields ...

    # DEPRECATED: Keep for backward compatibility during migration
    matched_invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transactions',
        verbose_name='Párosított számla',
        help_text='(DEPRECATED) Use matched_invoices instead - single invoice match'
    )

    # NEW: ManyToMany relationship for batch matching
    matched_invoices = models.ManyToManyField(
        'Invoice',
        through='BankTransactionInvoiceMatch',
        related_name='bank_transactions_many',
        blank=True,
        verbose_name='Párosított számlák',
        help_text='Multiple matched invoices (for batch payments)'
    )

    # ... rest of existing fields ...

    @property
    def is_batch_match(self) -> bool:
        """Returns True if transaction is matched to multiple invoices"""
        return self.matched_invoices.count() > 1

    @property
    def total_matched_amount(self) -> Decimal:
        """Sum of all matched invoice amounts"""
        return sum(
            match.invoice.invoice_gross_amount
            for match in self.invoice_matches.all()
        )

    @property
    def matched_invoices_count(self) -> int:
        """Count of matched invoices (0 if unmatched)"""
        return self.matched_invoices.count()
```

#### Backend: Serializers

```python
# File: backend/bank_transfers/serializers.py
# Location: After InvoiceListSerializer

class BankTransactionInvoiceMatchSerializer(serializers.ModelSerializer):
    """
    Serializer for BankTransactionInvoiceMatch intermediate model.

    Returns detailed match information including expanded invoice data.
    """
    invoice_data = InvoiceListSerializer(source='invoice', read_only=True)
    matched_by_username = serializers.SerializerMethodField()

    class Meta:
        model = BankTransactionInvoiceMatch
        fields = [
            'id', 'invoice', 'invoice_data', 'match_confidence',
            'match_method', 'matched_at', 'matched_by', 'matched_by_username',
            'match_notes'
        ]

    def get_matched_by_username(self, obj):
        return obj.matched_by.username if obj.matched_by else None


# MODIFY: BankTransactionSerializer (around line 600)
class BankTransactionSerializer(serializers.ModelSerializer):
    # ... existing fields ...

    # Keep for backward compatibility
    matched_invoice = InvoiceListSerializer(read_only=True)

    # NEW: Batch matching fields
    matched_invoices = BankTransactionInvoiceMatchSerializer(
        source='invoice_matches',
        many=True,
        read_only=True
    )
    matched_invoices_count = serializers.SerializerMethodField()
    total_matched_amount = serializers.SerializerMethodField()
    is_batch_match = serializers.SerializerMethodField()

    class Meta:
        model = BankTransaction
        fields = [
            # ... existing fields ...
            'matched_invoice',  # Backward compat
            'matched_invoices',  # NEW
            'matched_invoices_count',  # NEW
            'total_matched_amount',  # NEW
            'is_batch_match',  # NEW
        ]

    def get_matched_invoices_count(self, obj):
        return obj.matched_invoices.count()

    def get_total_matched_amount(self, obj):
        return str(obj.total_matched_amount)

    def get_is_batch_match(self, obj):
        return obj.is_batch_match
```

#### Frontend: TypeScript Interfaces

```typescript
// File: frontend/src/types/api.ts
// Location: After NAVInvoice interface

export interface BankTransactionInvoiceMatch {
  id: number;
  invoice: number;
  invoice_data: NAVInvoice;
  match_confidence: string;  // "0.95"
  match_method: string;  // "BATCH_INVOICES"
  matched_at: string;  // ISO datetime
  matched_by?: number;  // User ID
  matched_by_username?: string;
  match_notes: string;
}

// MODIFY: BankTransaction interface (around line 60)
export interface BankTransaction {
  // ... existing fields ...

  // Keep for backward compatibility
  matched_invoice?: NAVInvoice | null;

  // NEW: Batch matching fields
  matched_invoices?: BankTransactionInvoiceMatch[];
  matched_invoices_count?: number;
  total_matched_amount?: string;
  is_batch_match?: boolean;
}
```

### Implementation Tasks (Ordered by Dependencies)

```yaml
## PHASE 1: DATABASE SCHEMA (Backend) ##

Task 1.1: CREATE backend/bank_transfers/models.py - BankTransactionInvoiceMatch
  - IMPLEMENT: BankTransactionInvoiceMatch model with all fields
  - FOLLOW pattern: backend/bank_transfers/models.py (CompanyOwnedTimestampedModel if needed)
  - NAMING: BankTransactionInvoiceMatch class, snake_case for field names
  - PLACEMENT: After Invoice model, before BankTransaction model
  - CRITICAL: Add unique_together = [['transaction', 'invoice']]
  - CRITICAL: Add indexes for (transaction, invoice) and (invoice)
  - DEPENDENCIES: None

Task 1.2: MODIFY backend/bank_transfers/models.py - BankTransaction.matched_invoices
  - IMPLEMENT: Add matched_invoices ManyToManyField with through='BankTransactionInvoiceMatch'
  - FOLLOW pattern: Django ManyToMany with through model
  - NAMING: matched_invoices (plural), related_name='bank_transactions_many'
  - PLACEMENT: After matched_invoice field in BankTransaction model
  - CRITICAL: related_name MUST be different from existing 'bank_transactions'
  - DEPENDENCIES: Task 1.1

Task 1.3: MODIFY backend/bank_transfers/models.py - BankTransaction properties
  - IMPLEMENT: Add @property methods: is_batch_match, total_matched_amount, matched_invoices_count
  - FOLLOW pattern: Python @property decorator
  - NAMING: is_batch_match (bool), total_matched_amount (Decimal), matched_invoices_count (int)
  - PLACEMENT: After model fields in BankTransaction
  - DEPENDENCIES: Task 1.2

Task 1.4: CREATE backend/bank_transfers/migrations/0061_add_batch_invoice_matching.py
  - RUN: python manage.py makemigrations bank_transfers --name add_batch_invoice_matching
  - VERIFY: Migration includes CreateModel (BankTransactionInvoiceMatch), AddField (matched_invoices), AddIndex
  - CRITICAL: DO NOT run migrate yet - data migration comes next
  - DEPENDENCIES: Tasks 1.1, 1.2, 1.3

Task 1.5: CREATE backend/bank_transfers/migrations/0062_migrate_single_matches_to_many.py
  - RUN: python manage.py makemigrations bank_transfers --empty --name migrate_single_matches_to_many
  - IMPLEMENT: Data migration to copy matched_invoice → matched_invoices
  - FOLLOW pattern: Django data migration with forwards_func and backwards_func
  - CRITICAL: For each BankTransaction where matched_invoice IS NOT NULL:
    * Create BankTransactionInvoiceMatch with same confidence, method, notes
  - DEPENDENCIES: Task 1.4

Task 1.6: RUN migrations on development database
  - RUN: python manage.py migrate bank_transfers
  - VERIFY: python manage.py showmigrations bank_transfers (both 0061 and 0062 applied)
  - TEST: Check BankTransactionInvoiceMatch table exists
  - TEST: Verify existing matches migrated (count should match)
  - DEPENDENCIES: Task 1.5

## PHASE 2: BATCH MATCHING ALGORITHM (Backend) ##

Task 2.1: CREATE backend/bank_transfers/services/transaction_matching_service.py - _match_by_batch_invoices
  - IMPLEMENT: def _match_by_batch_invoices(self, transaction, invoices) -> Tuple[List[Invoice], Decimal]
  - FOLLOW pattern: transaction_matching_service.py _match_by_amount_iban (lines 578-631)
  - NAMING: _match_by_batch_invoices (method)
  - PLACEMENT: After _match_by_amount_iban method (around line 632)
  - ALGORITHM:
    1. Pre-filter invoices by amount range (transaction_amount * 0.95 to 1.05)
    2. Group by (supplier_tax_number, supplier_name)
    3. For each supplier group:
       - Skip if >20 invoices (performance limit)
       - Try combinations(invoices, 2), (invoices, 3), ..., (invoices, 5)
       - For each combo: sum amounts, check tolerance, calculate confidence
       - Verify direction_compatible for ALL invoices
    4. Return (best_invoices_list, best_confidence) or ([], Decimal('0.00'))
  - CRITICAL: from itertools import combinations
  - CRITICAL: Use Decimal for all amount calculations
  - GOTCHA: Performance - skip if >20 invoices per supplier
  - DEPENDENCIES: None

Task 2.2: MODIFY backend/bank_transfers/services/transaction_matching_service.py - _try_invoice_matching
  - IMPLEMENT: Add batch matching strategy between _match_by_amount_iban and _match_by_fuzzy_name
  - FOLLOW pattern: Existing strategy cascade (lines 205-297)
  - PLACEMENT: After _match_by_amount_iban (line 238), before _match_by_fuzzy_name
  - LOGIC:
    matched_invoices, confidence = self._match_by_batch_invoices(transaction, candidate_invoices)
    if matched_invoices:
        method = 'BATCH_INVOICES'
        # Create BankTransactionInvoiceMatch for EACH invoice
        for invoice in matched_invoices:
            BankTransactionInvoiceMatch.objects.create(...)
        # Update transaction (backward compat)
        transaction.matched_invoice = matched_invoices[0]
        transaction.match_confidence = confidence
        transaction.match_method = 'BATCH_INVOICES'
        # Auto-payment if confidence >= 0.90
        if confidence >= AUTO_PAYMENT_THRESHOLD:
            for invoice in matched_invoices:
                self._update_invoice_payment_status(invoice, transaction, auto=True)
        return {'matched': True, 'invoice_ids': [...], 'confidence': confidence, ...}
  - DEPENDENCIES: Task 2.1

Task 2.3: MODIFY backend/bank_transfers/services/transaction_matching_service.py - _update_invoice_payment_status
  - IMPLEMENT: Support both single Invoice and List[Invoice]
  - CHANGE signature: def _update_invoice_payment_status(self, invoices, transaction, auto=True)
  - LOGIC:
    if isinstance(invoices, Invoice):
        invoices = [invoices]
    for invoice in invoices:
        invoice.mark_as_paid(payment_date=transaction.booking_date, auto_marked=auto)
        logger.info(f"Invoice {invoice.nav_invoice_number} marked as PAID")
  - UPDATE all call sites to pass invoice or [invoice]
  - DEPENDENCIES: Task 2.2

## PHASE 3: API LAYER (Backend) ##

Task 3.1: CREATE backend/bank_transfers/serializers.py - BankTransactionInvoiceMatchSerializer
  - IMPLEMENT: BankTransactionInvoiceMatchSerializer class
  - FOLLOW pattern: serializers.py InvoiceListSerializer structure
  - PLACEMENT: After InvoiceListSerializer (around line 200)
  - FIELDS: id, invoice, invoice_data (nested), match_confidence, match_method, matched_at, matched_by, match_notes
  - CRITICAL: invoice_data = InvoiceListSerializer(source='invoice', read_only=True)
  - DEPENDENCIES: Task 1.1

Task 3.2: MODIFY backend/bank_transfers/serializers.py - BankTransactionSerializer
  - IMPLEMENT: Add matched_invoices, matched_invoices_count, total_matched_amount, is_batch_match fields
  - FOLLOW pattern: serializers.py SerializerMethodField usage
  - PLACEMENT: BankTransactionSerializer class (around line 600)
  - FIELDS:
    * matched_invoices = BankTransactionInvoiceMatchSerializer(source='invoice_matches', many=True)
    * matched_invoices_count = SerializerMethodField()
    * total_matched_amount = SerializerMethodField()
    * is_batch_match = SerializerMethodField()
  - DEPENDENCIES: Task 3.1

Task 3.3: CREATE backend/bank_transfers/api_views.py - batch_match_invoices endpoint
  - IMPLEMENT: @action(detail=True, methods=['post']) def batch_match_invoices(self, request, pk=None)
  - FOLLOW pattern: api_views.py match_invoice endpoint (lines 2048-2085)
  - PLACEMENT: BankTransactionViewSet after match_invoice method
  - INPUT: {"invoice_ids": [101, 102, 103]}
  - VALIDATION:
    * invoice_ids is list with 2-20 items
    * All invoices exist and belong to company
    * All invoices from same supplier (tax_number + name)
    * Total amount within 5% of transaction amount (or force=true)
  - LOGIC:
    * Delete existing matches: transaction.invoice_matches.all().delete()
    * Create BankTransactionInvoiceMatch for each invoice with:
      - match_method = 'MANUAL_BATCH'
      - match_confidence = Decimal('1.00')
      - matched_by = request.user
      - match_notes = f"Manual batch match: {len(invoice_ids)} invoices, total {total} HUF"
    * Return: {'message': 'Success', 'matched_invoices': [...], 'total': total}
  - DEPENDENCIES: Task 3.2

Task 3.4: MODIFY backend/bank_transfers/api_views.py - unmatch endpoint
  - IMPLEMENT: Update unmatch to clear all matched_invoices
  - FOLLOW pattern: Existing unmatch method (lines 2088-2101)
  - PLACEMENT: BankTransactionViewSet.unmatch method
  - LOGIC:
    * Clear matched_invoice (existing)
    * Clear matched_invoices: transaction.invoice_matches.all().delete()
    * Reset match fields
    * Return: {'message': 'Success', 'cleared_count': count}
  - DEPENDENCIES: Task 3.3

## PHASE 4: FRONTEND UI (TypeScript/React) ##

Task 4.1: MODIFY frontend/src/types/api.ts - BankTransactionInvoiceMatch interface
  - IMPLEMENT: export interface BankTransactionInvoiceMatch
  - FOLLOW pattern: types/api.ts NAVInvoice interface
  - PLACEMENT: After NAVInvoice interface
  - FIELDS: id, invoice, invoice_data, match_confidence, match_method, matched_at, matched_by, match_notes
  - DEPENDENCIES: None

Task 4.2: MODIFY frontend/src/types/api.ts - BankTransaction interface
  - IMPLEMENT: Add matched_invoices, matched_invoices_count, total_matched_amount, is_batch_match fields
  - FOLLOW pattern: Existing BankTransaction interface fields
  - PLACEMENT: BankTransaction interface (around line 60)
  - KEEP: matched_invoice field (backward compat)
  - DEPENDENCIES: Task 4.1

Task 4.3: MODIFY frontend/src/components/BankStatements/BankStatementDetails.tsx - Batch match display
  - IMPLEMENT: Render badge "X számlák" for batch matches, expandable row with invoice table
  - FOLLOW pattern: MUI Chip for badge, Collapse for expandable row
  - PLACEMENT: Transaction table "Matched Invoice" column (around line 300)
  - LOGIC:
    if (transaction.is_batch_match) {
      return (
        <>
          <Chip label={`${transaction.matched_invoices_count} számlák`} color="info" onClick={toggleExpand} />
          <Collapse in={expanded}>
            <Table size="small">
              {transaction.matched_invoices.map(match => (
                <TableRow>
                  <TableCell><Link to={`/invoices/${match.invoice}`}>{match.invoice_data.nav_invoice_number}</Link></TableCell>
                  <TableCell>{match.invoice_data.supplier_name}</TableCell>
                  <TableCell>{match.invoice_data.invoice_gross_amount}</TableCell>
                  <TableCell>{match.match_confidence}</TableCell>
                </TableRow>
              ))}
              <TableRow><TableCell>Total:</TableCell><TableCell colSpan={3}>{transaction.total_matched_amount}</TableCell></TableRow>
            </Table>
          </Collapse>
        </>
      )
    }
  - DEPENDENCIES: Task 4.2

Task 4.4: CREATE frontend/src/components/BankStatements/BatchMatchDialog.tsx
  - IMPLEMENT: Dialog component for manual batch matching
  - FOLLOW pattern: ManualMatchDialog.tsx structure
  - PLACEMENT: New file in components/BankStatements/
  - PROPS: open, onClose, transaction, onMatchComplete
  - UI:
    * Dialog title: "Batch Invoice Matching"
    * Transaction details display (amount, date, beneficiary)
    * MUI Autocomplete with multiple selection for invoices
    * Supplier filter dropdown
    * Real-time total calculation: "Selected: {total} HUF / Transaction: {amount} HUF"
    * Color indicator: green (exact), yellow (±5%), red (>5%)
    * Warning if >5% difference
    * Checkbox: "Force match even if amounts differ"
    * "Match" button (submit)
  - LOGIC:
    * Fetch candidate invoices (UNPAID/PREPARED, ±90 days, amount range)
    * On submit: POST /api/bank-transactions/{id}/batch_match_invoices/
    * Handle success: snackbar, onMatchComplete(), close
    * Handle error: display error message
  - DEPENDENCIES: Task 4.3

Task 4.5: MODIFY frontend/src/components/BankStatements/BankStatementDetails.tsx - Add batch match button
  - IMPLEMENT: Add "Batch Match" button to transaction actions menu
  - FOLLOW pattern: Existing action buttons (match, unmatch)
  - PLACEMENT: Transaction row actions column
  - LOGIC:
    * Show button only if transaction.matched_invoices_count === 0 (unmatched)
    * On click: open BatchMatchDialog
    * Pass onMatchComplete callback to refresh transaction list
  - DEPENDENCIES: Task 4.4

Task 4.6: MODIFY frontend/src/services/api.ts - batchMatchInvoices method
  - IMPLEMENT: export const batchMatchInvoices = async (transactionId, invoiceIds) => { ... }
  - FOLLOW pattern: services/api.ts existing methods
  - PLACEMENT: After matchInvoice method
  - LOGIC:
    return axios.post(`/api/bank-transactions/${transactionId}/batch_match_invoices/`, {
      invoice_ids: invoiceIds
    })
  - DEPENDENCIES: None

Task 4.7: MODIFY frontend/src/hooks/api.ts - useBatchMatchInvoices hook
  - IMPLEMENT: export const useBatchMatchInvoices = () => { ... }
  - FOLLOW pattern: hooks/api.ts React Query mutation hooks
  - PLACEMENT: After useMatchInvoice hook
  - LOGIC:
    const mutation = useMutation({
      mutationFn: ({transactionId, invoiceIds}) => batchMatchInvoices(transactionId, invoiceIds),
      onSuccess: () => {
        queryClient.invalidateQueries(['bankTransactions'])
        queryClient.invalidateQueries(['invoices'])
      }
    })
  - DEPENDENCIES: Task 4.6

## PHASE 5: TESTING & DOCUMENTATION ##

Task 5.1: CREATE backend/bank_transfers/tests/test_batch_matching.py
  - IMPLEMENT: Unit tests for batch matching algorithm
  - FOLLOW pattern: Django TestCase pattern
  - PLACEMENT: New file in bank_transfers/tests/
  - TEST CASES:
    1. test_exact_batch_match_two_invoices: 100 + 150 = 250
    2. test_exact_batch_match_three_invoices: 100 + 150 + 200 = 450
    3. test_batch_match_with_tolerance: 449 matches 450 (within 1%)
    4. test_batch_match_requires_same_supplier: Different suppliers → no match
    5. test_batch_match_direction_compatibility: INBOUND invoices only match debit
    6. test_batch_match_confidence_iban_bonus: +0.10 bonus
    7. test_batch_match_confidence_name_bonus: +0.05 bonus for 90%+ match
    8. test_batch_match_auto_payment: Confidence ≥0.90 marks all PAID
    9. test_batch_match_skips_large_groups: >20 invoices skipped
    10. test_batch_match_creates_multiple_records: Verify BankTransactionInvoiceMatch count
  - DEPENDENCIES: All backend tasks

Task 5.2: CREATE backend/bank_transfers/tests/test_batch_matching_integration.py
  - IMPLEMENT: Integration test for full workflow
  - FOLLOW pattern: APITestCase pattern
  - PLACEMENT: New file in bank_transfers/tests/
  - TEST WORKFLOW:
    1. Upload bank statement with batch payment
    2. Verify automatic batch matching
    3. Verify all invoices marked PAID
    4. Test API returns matched_invoices array
    5. Test manual batch matching via API
    6. Test unmatch clears all matches
    7. Test rematch finds batch match again
  - DEPENDENCIES: Task 5.1

Task 5.3: RUN all tests
  - RUN: python manage.py test bank_transfers.tests.test_batch_matching
  - RUN: python manage.py test bank_transfers.tests.test_batch_matching_integration
  - VERIFY: All tests pass (expected: 20+ tests, 0 failures)
  - DEPENDENCIES: Tasks 5.1, 5.2

Task 5.4: MODIFY DATABASE_DOCUMENTATION.md
  - IMPLEMENT: Add BankTransactionInvoiceMatch table documentation
  - FOLLOW pattern: Existing table documentation in DATABASE_DOCUMENTATION.md
  - PLACEMENT: After BankTransaction table section (around line 600)
  - CONTENT:
    * Table name: bank_transfers_banktransactioninvoicematch
    * Purpose: Intermediate table for ManyToMany relationship
    * Columns with descriptions
    * Indexes and constraints
    * Relationships
    * Business logic notes
  - DEPENDENCIES: None

Task 5.5: MODIFY backend/sql/complete_database_comments_postgresql.sql
  - IMPLEMENT: Add SQL comments for BankTransactionInvoiceMatch table
  - FOLLOW pattern: Existing COMMENT statements
  - PLACEMENT: After bank_transfers_banktransaction comments
  - CONTENT: Table comment, column comments with examples
  - DEPENDENCIES: Task 5.4

Task 5.6: MODIFY backend/sql/complete_database_comments_sqlserver.sql
  - IMPLEMENT: Add SQL Server comments for BankTransactionInvoiceMatch table
  - FOLLOW pattern: SQL Server EXEC sp_addextendedproperty syntax
  - PLACEMENT: After bank_transfers_banktransaction comments
  - CONTENT: Same as PostgreSQL version but SQL Server syntax
  - DEPENDENCIES: Task 5.5

Task 5.7: MODIFY FEATURES.md
  - IMPLEMENT: Document batch invoice matching in Bank Statement Import section
  - FOLLOW pattern: Existing feature documentation in FEATURES.md
  - PLACEMENT: Bank Statement Import section (around line 200)
  - CONTENT:
    * Add subsection: "Batch Invoice Matching"
    * Describe use case and algorithm
    * Update matching strategies list (now 8 total, was 7)
    * Note performance limits and confidence scoring
  - DEPENDENCIES: None
```

### Implementation Patterns & Key Details

```python
# PATTERN: Batch matching algorithm structure
def _match_by_batch_invoices(
    self,
    transaction: BankTransaction,
    invoices: QuerySet
) -> Tuple[List[Invoice], Decimal]:
    """
    Match transaction to 2-5 invoices from same supplier.

    CRITICAL: Performance limit - skip if >20 invoices per supplier
    GOTCHA: Use Decimal for all amount calculations to avoid float precision errors
    """
    from itertools import combinations
    from decimal import Decimal

    amount = abs(transaction.amount)
    tolerance = amount * Decimal('0.01')  # 1% tolerance

    # Pre-filter by amount range (performance optimization)
    candidate_invoices = invoices.filter(
        invoice_gross_amount__gte=amount * Decimal('0.95'),
        invoice_gross_amount__lte=amount * Decimal('1.05')
    )

    # Group by supplier (tax_number, name)
    supplier_groups = {}
    for invoice in candidate_invoices:
        key = (invoice.supplier_tax_number, invoice.supplier_name)
        if key not in supplier_groups:
            supplier_groups[key] = []
        supplier_groups[key].append(invoice)

    best_match = None
    best_confidence = Decimal('0.00')

    for (tax_number, name), supplier_invoices in supplier_groups.items():
        # CRITICAL: Performance protection
        if len(supplier_invoices) > 20:
            logger.warning(f"Skipping supplier {tax_number}: {len(supplier_invoices)} invoices (max 20)")
            continue

        # Try combinations of 2-5 invoices
        for r in range(2, min(6, len(supplier_invoices) + 1)):
            for combo in combinations(supplier_invoices, r):
                # CRITICAL: Use Decimal for precise amount calculation
                combo_total = sum(Decimal(str(inv.invoice_gross_amount)) for inv in combo)

                # Check tolerance
                if abs(combo_total - amount) <= tolerance:
                    # Base confidence
                    confidence = Decimal('0.85')

                    # Bonus: IBAN match
                    if transaction.beneficiary_iban:
                        iban_norm = self._normalize_iban(transaction.beneficiary_iban)
                        supplier_iban = self._normalize_iban(combo[0].supplier_bank_account_number)
                        if iban_norm == supplier_iban:
                            confidence += Decimal('0.10')  # 0.95 total

                    # Bonus: Name similarity
                    if transaction.beneficiary_name:
                        similarity = self._calculate_name_similarity(
                            transaction.beneficiary_name,
                            name
                        )
                        if similarity >= 90:
                            confidence += Decimal('0.05')  # Up to 1.00 total

                    # Verify direction compatibility for ALL invoices
                    if all(self._is_direction_compatible(transaction, inv) for inv in combo):
                        if confidence > best_confidence:
                            best_match = list(combo)
                            best_confidence = confidence

    return best_match or [], best_confidence


# PATTERN: Creating batch match records
def _try_invoice_matching(self, transaction, user=None):
    # ... existing strategies ...

    # NEW: Batch invoice matching (after AMOUNT_IBAN, before FUZZY_NAME)
    if not matched_invoice:
        matched_invoices, confidence = self._match_by_batch_invoices(transaction, candidate_invoices)
        if matched_invoices:
            from django.db import transaction as db_transaction

            method = 'BATCH_INVOICES'

            # Build detailed match notes
            invoice_details = ', '.join([
                f"{inv.nav_invoice_number} ({inv.invoice_gross_amount} HUF)"
                for inv in matched_invoices
            ])
            total = sum(inv.invoice_gross_amount for inv in matched_invoices)
            match_notes = (
                f"Batch match: {len(matched_invoices)} invoices, "
                f"total {total} HUF - "
                f"{invoice_details} - "
                f"{'Automatic match' if not user else 'Manual match'}"
            )

            # CRITICAL: Use atomic transaction for consistency
            with db_transaction.atomic():
                # Create match record for EACH invoice
                for invoice in matched_invoices:
                    BankTransactionInvoiceMatch.objects.create(
                        transaction=transaction,
                        invoice=invoice,
                        match_confidence=confidence,
                        match_method=method,
                        matched_by=user,
                        match_notes=match_notes
                    )

                # Update transaction fields (backward compatibility)
                transaction.matched_invoice = matched_invoices[0]  # First invoice
                transaction.match_confidence = confidence
                transaction.match_method = method
                transaction.matched_at = timezone.now()
                transaction.matched_by = user
                transaction.match_notes = match_notes
                transaction.save()

                # Auto-payment for high confidence
                if confidence >= self.AUTO_PAYMENT_THRESHOLD:
                    for invoice in matched_invoices:
                        self._update_invoice_payment_status(invoice, transaction, auto=True)
                    auto_paid = True

            logger.info(
                f"Batch match: transaction {transaction.id} → "
                f"{len(matched_invoices)} invoices (confidence: {confidence})"
            )

            return {
                'matched': True,
                'invoice_ids': [inv.id for inv in matched_invoices],
                'confidence': confidence,
                'method': method,
                'auto_paid': auto_paid
            }


# PATTERN: Frontend batch match display (React/TypeScript)
const TransactionRow: React.FC<{transaction: BankTransaction}> = ({transaction}) => {
  const [expanded, setExpanded] = useState(false);

  // Render matched invoice column
  const renderMatchedInvoice = () => {
    if (transaction.is_batch_match && transaction.matched_invoices) {
      return (
        <>
          <Chip
            label={`${transaction.matched_invoices_count} számlák`}
            color="info"
            size="small"
            onClick={() => setExpanded(!expanded)}
            sx={{ cursor: 'pointer' }}
          />
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Table size="small" sx={{ mt: 1, mb: 1 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Invoice Number</TableCell>
                  <TableCell>Supplier</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell>Confidence</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transaction.matched_invoices.map((match) => (
                  <TableRow key={match.id}>
                    <TableCell>
                      <Link to={`/invoices/${match.invoice}`}>
                        {match.invoice_data.nav_invoice_number}
                      </Link>
                    </TableCell>
                    <TableCell>{match.invoice_data.supplier_name}</TableCell>
                    <TableCell align="right">
                      {formatCurrency(match.invoice_data.invoice_gross_amount)}
                    </TableCell>
                    <TableCell>{(parseFloat(match.match_confidence) * 100).toFixed(0)}%</TableCell>
                  </TableRow>
                ))}
                <TableRow sx={{ fontWeight: 'bold' }}>
                  <TableCell colSpan={2}>Total:</TableCell>
                  <TableCell align="right">
                    {formatCurrency(transaction.total_matched_amount)}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableBody>
            </Table>
          </Collapse>
        </>
      );
    } else if (transaction.matched_invoice) {
      return <Link to={`/invoices/${transaction.matched_invoice.id}`}>
        {transaction.matched_invoice.nav_invoice_number}
      </Link>;
    } else {
      return <Typography variant="body2" color="text.secondary">Nincs párosítás</Typography>;
    }
  };

  return (
    <TableRow>
      {/* ... other cells ... */}
      <TableCell>{renderMatchedInvoice()}</TableCell>
    </TableRow>
  );
};
```

### Integration Points

```yaml
DATABASE:
  - migration: "0061_add_batch_invoice_matching.py - Add BankTransactionInvoiceMatch model and matched_invoices field"
  - migration: "0062_migrate_single_matches_to_many.py - Migrate existing matched_invoice data"
  - index: "CREATE INDEX idx_tx_invoice_match ON bank_transfers_banktransactioninvoicematch (transaction_id, invoice_id)"
  - index: "CREATE INDEX idx_invoice_matches ON bank_transfers_banktransactioninvoicematch (invoice_id)"
  - constraint: "UNIQUE (transaction_id, invoice_id) to prevent duplicate matches"

API:
  - endpoint: "POST /api/bank-transactions/{id}/batch_match_invoices/"
  - request: {"invoice_ids": [101, 102, 103], "force": false}
  - response: {"message": "Success", "matched_invoices": [...], "total": "450.00"}
  - existing: "POST /api/bank-transactions/{id}/unmatch/ - Updated to clear batch matches"
  - existing: "POST /api/bank-transactions/{id}/rematch/ - Works with batch matching"

SERVICES:
  - modify: "TransactionMatchingService._try_invoice_matching() - Add batch matching strategy"
  - modify: "TransactionMatchingService._update_invoice_payment_status() - Support list of invoices"
  - create: "TransactionMatchingService._match_by_batch_invoices() - Core algorithm"

SERIALIZERS:
  - create: "BankTransactionInvoiceMatchSerializer - Intermediate model serializer"
  - modify: "BankTransactionSerializer - Add matched_invoices, matched_invoices_count, total_matched_amount"

FRONTEND:
  - component: "BatchMatchDialog.tsx - Manual batch matching UI"
  - modify: "BankStatementDetails.tsx - Display batch matches with expandable rows"
  - types: "api.ts - Add BankTransactionInvoiceMatch interface"
  - hooks: "api.ts - Add useBatchMatchInvoices mutation hook"
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Backend validation
cd backend
python manage.py check  # Django system check
python -m py_compile bank_transfers/models.py bank_transfers/services/transaction_matching_service.py
python -m py_compile bank_transfers/serializers.py bank_transfers/api_views.py

# Frontend validation
cd frontend
npm run build  # TypeScript compilation check
# Expected: Zero errors

# If errors: READ output, fix syntax/type errors before proceeding
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend unit tests
cd backend
python manage.py test bank_transfers.tests.test_batch_matching -v
# Expected: All tests pass (10+ test cases)

# Test specific scenarios
python manage.py test bank_transfers.tests.test_batch_matching.TestBatchInvoiceMatching.test_exact_batch_match_three_invoices -v
python manage.py test bank_transfers.tests.test_batch_matching.TestBatchInvoiceMatching.test_batch_match_auto_payment -v

# If failing: Debug root cause, add logging, fix implementation
# Use: python manage.py shell to test algorithm manually
```

### Level 3: Integration Testing (System Validation)

```bash
# Start Django development server
cd backend
python manage.py runserver 8002 &
sleep 3

# Test API endpoints
# 1. Check batch matching endpoint exists
curl -f http://localhost:8002/api/bank-transactions/123/batch_match_invoices/ \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invoice_ids": [101, 102, 103]}' \
  | jq .

# 2. Verify serializer returns matched_invoices
curl -f http://localhost:8002/api/bank-transactions/123/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.matched_invoices'

# 3. Upload test bank statement and verify automatic batch matching
curl -f http://localhost:8002/api/bank-statements/upload/ \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_statement.pdf" \
  | jq '.matched_count'

# Frontend integration test
cd frontend
npm start &
sleep 5

# Open browser and test:
# - Navigate to Bank Statements
# - Click on statement with batch payment
# - Verify "3 számlák" badge appears
# - Click badge to expand - verify invoice table
# - Click "Batch Match" button
# - Verify dialog opens and works

# Expected: All integrations working, no 500 errors, UI renders correctly
```

### Level 4: Creative & Domain-Specific Validation

```bash
# Performance testing - batch matching algorithm
python manage.py shell <<EOF
from bank_transfers.services.transaction_matching_service import TransactionMatchingService
from bank_transfers.models import BankTransaction, Invoice
import time

# Create test data: 50 invoices, 1 transaction (450 HUF)
# ... (setup code)

service = TransactionMatchingService(company)
start = time.time()
matched_invoices, confidence = service._match_by_batch_invoices(transaction, invoices)
duration = time.time() - start

print(f"Performance: {duration:.2f} seconds for 50 invoices")
assert duration < 2.0, "Algorithm too slow!"
print(f"Result: {len(matched_invoices)} invoices matched with confidence {confidence}")
EOF

# Database query optimization check
python manage.py shell <<EOF
from django.db import connection
from django.test.utils import override_settings
from bank_transfers.models import BankTransaction

# Enable query logging
import logging
logging.basicConfig()
logging.getLogger('django.db.backends').setLevel(logging.DEBUG)

# Fetch transaction with batch matches
transaction = BankTransaction.objects.prefetch_related(
    'invoice_matches__invoice'
).get(id=123)

print(f"Matched invoices: {transaction.matched_invoices.count()}")
print(f"Total queries: {len(connection.queries)}")

# Expected: <5 queries (not N+1)
assert len(connection.queries) < 5, "N+1 query detected!"
EOF

# Frontend performance - render 100 transactions with batch matches
# Open Chrome DevTools → Performance tab
# Record page load and scroll through transaction list
# Expected: <3 seconds to render, smooth scrolling (60fps)

# Security validation - ensure batch matching respects company isolation
python manage.py shell <<EOF
from bank_transfers.models import BankTransaction, Invoice, Company

company1 = Company.objects.get(id=2)
company2 = Company.objects.get(id=3)

# Try to batch match invoices from different companies
transaction = BankTransaction.objects.filter(company=company1).first()
invoices = Invoice.objects.filter(company=company2)[:3]

# This should FAIL or skip (company isolation)
service = TransactionMatchingService(company1)
result = service._match_by_batch_invoices(transaction, invoices)

assert result == ([], Decimal('0.00')), "Company isolation violated!"
print("✓ Company isolation working correctly")
EOF

# Data integrity check after migration
python manage.py shell <<EOF
from bank_transfers.models import BankTransaction, BankTransactionInvoiceMatch

# Verify all existing matches migrated
old_matches = BankTransaction.objects.filter(matched_invoice__isnull=False).count()
new_matches = BankTransactionInvoiceMatch.objects.count()

print(f"Old matches (matched_invoice): {old_matches}")
print(f"New matches (invoice_matches): {new_matches}")
assert new_matches >= old_matches, "Data migration incomplete!"
print("✓ Data migration successful")
EOF
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] All unit tests pass: `python manage.py test bank_transfers.tests.test_batch_matching -v`
- [ ] Integration test passes: `python manage.py test bank_transfers.tests.test_batch_matching_integration -v`
- [ ] No Django system check errors: `python manage.py check`
- [ ] Frontend builds without errors: `npm run build`
- [ ] No console errors in browser DevTools
- [ ] Database migrations applied successfully: `python manage.py migrate`
- [ ] Data migration preserves all existing matches

### Feature Validation

- [ ] Automatic batch matching finds 2-5 invoice combinations (tested with real data)
- [ ] Confidence calculation correct: 0.85 base + bonuses = up to 1.00
- [ ] High-confidence matches (≥0.90) auto-mark all invoices as PAID
- [ ] API returns `matched_invoices` array with per-invoice metadata
- [ ] Frontend displays "3 számlák" badge correctly
- [ ] Expandable row shows all matched invoices with details
- [ ] Manual batch matching dialog validates inputs and shows real-time total
- [ ] Unmatch clears all matched invoices (tested)
- [ ] Rematch can find batch matches again
- [ ] Performance: Algorithm completes in <2 seconds for 50 invoices (tested)

### Code Quality Validation

- [ ] Follows Django model patterns (CompanyOwnedTimestampedModel, Meta options)
- [ ] Follows DRF patterns (ViewSets, Serializers, nested relationships)
- [ ] Follows React patterns (functional components, hooks, TypeScript strict)
- [ ] No N+1 database queries (verified with query logging)
- [ ] Proper error handling (try/except, validation, user-friendly messages)
- [ ] Logging is informative but not verbose (debug, info, warning levels)
- [ ] Code is self-documenting with clear variable/function names
- [ ] Anti-patterns avoided (no hardcoded values, no sync in async, specific exceptions)

### Documentation & Deployment

- [ ] DATABASE_DOCUMENTATION.md updated with BankTransactionInvoiceMatch table
- [ ] SQL comments added to complete_database_comments_postgresql.sql
- [ ] SQL comments added to complete_database_comments_sqlserver.sql
- [ ] FEATURES.md updated with batch matching description
- [ ] Migration files committed with clear names (0061, 0062)
- [ ] Git commit messages follow conventions (no Claude Code attribution)
- [ ] Backward compatibility verified: Existing single-invoice matches work
- [ ] Deployment checklist created (PRPs/DEPLOYMENT/batch-matching-rollout.md)

---

## Anti-Patterns to Avoid

- ❌ Don't use float for money calculations - use Decimal
- ❌ Don't try all combinations if >20 invoices - skip for performance
- ❌ Don't create ManyToMany without 'through' model - lose metadata
- ❌ Don't forget to invalidate React Query cache after batch match
- ❌ Don't assume all invoices from same supplier - verify tax_number AND name
- ❌ Don't create match records without atomic transaction - data inconsistency
- ❌ Don't display confidence as decimal "0.95" - show as percentage "95%"
- ❌ Don't forget direction compatibility check for ALL invoices in batch
- ❌ Don't use .add() on ManyToMany with through model - create records manually
- ❌ Don't forget to update matched_invoice for backward compatibility
- ❌ Don't skip data migration - existing matches must be preserved
- ❌ Don't hardcode supplier group size limit (20) - make it configurable
