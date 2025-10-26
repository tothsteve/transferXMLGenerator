/**
 * @fileoverview Zod validation schemas for Bank Statement API responses
 * @module schemas/bankStatement
 *
 * This module defines runtime validation schemas for all bank statement-related
 * API responses. All external data MUST be validated through these schemas
 * before use in the application.
 *
 * Key features:
 * - Branded types for type-safe IDs
 * - Complete API response validation
 * - Hungarian banking field validation
 * - Transaction type and status enums
 */

import { z } from 'zod';

/**
 * Branded type for Bank Statement IDs.
 *
 * Ensures type safety by preventing mixing of different ID types.
 * MUST use BankStatementIdSchema.parse() to create instances.
 *
 * @example
 * ```typescript
 * const id = BankStatementIdSchema.parse(123);
 * ```
 */
export const BankStatementIdSchema = z.number().int().positive().brand<'BankStatementId'>();
export type BankStatementId = z.infer<typeof BankStatementIdSchema>;

/**
 * Branded type for Bank Transaction IDs.
 *
 * @example
 * ```typescript
 * const id = BankTransactionIdSchema.parse(456);
 * ```
 */
export const BankTransactionIdSchema = z.number().int().positive().brand<'BankTransactionId'>();
export type BankTransactionId = z.infer<typeof BankTransactionIdSchema>;

/**
 * Branded type for Other Cost IDs.
 *
 * @example
 * ```typescript
 * const id = OtherCostIdSchema.parse(789);
 * ```
 */
export const OtherCostIdSchema = z.number().int().positive().brand<'OtherCostId'>();
export type OtherCostId = z.infer<typeof OtherCostIdSchema>;

/**
 * Bank statement processing status enum.
 *
 * Lifecycle: UPLOADED → PARSING → COMPLETED (or ERROR)
 */
export const BankStatementStatusSchema = z.enum([
  'UPLOADED',
  'PARSING',
  'PARSED',
  'ERROR',
]);
export type BankStatementStatus = z.infer<typeof BankStatementStatusSchema>;

/**
 * Transaction type classification.
 *
 * Maps to backend BankTransaction.transaction_type field.
 */
export const TransactionTypeSchema = z.enum([
  // Transfers
  'AFR_CREDIT',
  'AFR_DEBIT',
  'TRANSFER_CREDIT',
  'TRANSFER_DEBIT',

  // Card transactions
  'POS_PURCHASE',
  'ATM_WITHDRAWAL',

  // Bank charges
  'BANK_FEE',
  'INTEREST_CREDIT',
  'INTEREST_DEBIT',

  // Other
  'CORRECTION',
  'OTHER',
]);
export type TransactionType = z.infer<typeof TransactionTypeSchema>;

/**
 * Transaction matching method.
 *
 * Indicates how a transaction was matched to an invoice or transfer.
 */
export const MatchMethodSchema = z.enum([
  'REFERENCE_EXACT',
  'AMOUNT_IBAN',
  'FUZZY_NAME',
  'TRANSFER_EXACT',
  'REIMBURSEMENT_PAIR',
  'AMOUNT_DATE_ONLY',
  'MANUAL',
  '',
]);
export type MatchMethod = z.infer<typeof MatchMethodSchema>;

/**
 * Bank statement schema.
 *
 * Represents a single uploaded bank statement file with metadata,
 * transaction counts, and parsing status.
 *
 * @see {@link https://github.com/tothsteve/transferXMLGenerator/blob/main/backend/bank_transfers/models.py BankStatement Model}
 */
export const bankStatementSchema = z.object({
  /** Unique identifier for the bank statement */
  id: BankStatementIdSchema,

  /** Company ID owning this statement (optional in list view) */
  company: z.number().int().positive().optional(),

  /** Bank code identifier (e.g., 'GRANIT', 'REVOLUT') */
  bank_code: z.string().min(1).max(20),

  /** Full bank name (e.g., 'GRÁNIT Bank Nyrt.') */
  bank_name: z.string().min(1).max(200),

  /** Bank BIC/SWIFT code (e.g., 'GNBAHUHB') */
  bank_bic: z.string().min(1).max(11),

  /** Account number from statement */
  account_number: z.string().min(1).max(50),

  /** IBAN from statement (empty for non-IBAN banks) */
  account_iban: z.string().max(34),

  /** Statement reference number */
  statement_number: z.string().max(100),

  /** Statement period start date (ISO format) */
  statement_period_from: z.string().date(),

  /** Statement period end date (ISO format) */
  statement_period_to: z.string().date(),

  /** Opening balance as decimal string */
  opening_balance: z.string().regex(/^-?\d+(\.\d{1,2})?$/),

  /** Closing balance as decimal string */
  closing_balance: z.string().regex(/^-?\d+(\.\d{1,2})?$/),

  /** Original uploaded filename */
  file_name: z.string().min(1).max(255),

  /** SHA256 hash for duplicate detection */
  file_hash: z.string().length(64),

  /** File size in bytes */
  file_size: z.number().int().positive(),

  /** Storage path for the file (optional in list view) */
  file_path: z.string().max(500).optional(),

  /** ID of user who uploaded */
  uploaded_by: z.number().int().positive(),

  /** Name of user who uploaded (computed field) */
  uploaded_by_name: z.string().optional(),

  /** Upload timestamp (ISO datetime with timezone) */
  uploaded_at: z.string(),

  /** Processing status */
  status: BankStatementStatusSchema,

  /** Total number of transactions */
  total_transactions: z.number().int().nonnegative(),

  /** Number of credit transactions */
  credit_count: z.number().int().nonnegative(),

  /** Number of debit transactions */
  debit_count: z.number().int().nonnegative(),

  /** Sum of all credits as decimal string */
  total_credits: z.string().regex(/^-?\d+(\.\d{1,2})?$/),

  /** Sum of all debits as decimal string */
  total_debits: z.string().regex(/^-?\d+(\.\d{1,2})?$/),

  /** Number of successfully matched transactions */
  matched_count: z.number().int().nonnegative(),

  /** Percentage of matched transactions (computed field) */
  matched_percentage: z.number().nonnegative().optional(),

  /** Error message if parsing failed */
  parse_error: z.string().nullable(),

  /** Non-fatal parsing warnings (optional in list view) */
  parse_warnings: z.array(z.string()).optional(),

  /** Bank-specific extra metadata (optional in list view) */
  raw_metadata: z.record(z.unknown()).optional(),

  /** Created timestamp */
  created_at: z.string().optional(),

  /** Updated timestamp */
  updated_at: z.string().optional(),
});

export type BankStatement = z.infer<typeof bankStatementSchema>;

/**
 * Bank transaction schema.
 *
 * Represents a single transaction extracted from a bank statement.
 * Contains fields for transfers, POS purchases, fees, and matching metadata.
 */
export const bankTransactionSchema = z.object({
  /** Unique identifier */
  id: BankTransactionIdSchema,

  /** Parent bank statement ID */
  bank_statement: BankStatementIdSchema,

  /** Transaction type classification */
  transaction_type: TransactionTypeSchema,

  /** Date when bank processed transaction (ISO date) */
  booking_date: z.string().date(),

  /** Date when amount was settled (ISO date) */
  value_date: z.string().date(),

  /** Final amount (negative=debit, positive=credit) */
  amount: z.string().regex(/^-?\d+(\.\d{1,2})?$/),

  /** Currency code (HUF, USD, EUR, etc.) */
  currency: z.string().length(3),

  /** Full transaction description */
  description: z.string(),

  /** Brief description (truncated to 200 chars) */
  short_description: z.string().max(200),

  // AFR/Transfer fields
  /** Payment reference ID */
  payment_id: z.string().max(100),

  /** Bank transaction ID */
  transaction_id: z.string().max(100),

  /** Payer name (indexed for matching) */
  payer_name: z.string().max(200),

  /** Payer IBAN */
  payer_iban: z.string().max(34),

  /** Payer account number */
  payer_account_number: z.string().max(50),

  /** Payer BIC */
  payer_bic: z.string().max(11),

  /** Beneficiary name (indexed for matching) */
  beneficiary_name: z.string().max(200),

  /** Beneficiary IBAN */
  beneficiary_iban: z.string().max(34),

  /** Beneficiary account number */
  beneficiary_account_number: z.string().max(50),

  /** Beneficiary BIC */
  beneficiary_bic: z.string().max(11),

  /** Common reference / Közlemény (CRITICAL for invoice matching) */
  reference: z.string().max(500),

  /** End-to-end ID */
  partner_id: z.string().max(100),

  /** Bank-specific type code */
  transaction_type_code: z.string().max(100),

  /** Transaction fee amount (positive) */
  fee_amount: z.string().regex(/^-?\d+(\.\d{1,2})?$/).nullable(),

  // POS/Card fields
  /** Masked card number */
  card_number: z.string().max(20),

  /** Merchant/store name */
  merchant_name: z.string().max(200),

  /** Merchant location/code */
  merchant_location: z.string().max(200),

  /** Amount before FX conversion */
  original_amount: z.string().regex(/^-?\d+(\.\d{1,2})?$/).nullable(),

  /** Currency before conversion */
  original_currency: z.string().max(3),

  /** Exchange rate for conversion */
  exchange_rate: z.string().regex(/^\d+(\.\d{1,6})?$/).nullable().optional(),

  // Matching fields
  /** Matched NAV invoice ID */
  matched_invoice: z.number().int().positive().nullable(),

  /** Matched transfer ID */
  matched_transfer: z.number().int().positive().nullable().optional(),

  /** Matched reimbursement transaction ID */
  matched_reimbursement: BankTransactionIdSchema.nullable().optional(),

  /** Match confidence score (0.00 to 1.00) */
  match_confidence: z.string().regex(/^[01](\.\d{1,2})?$/),

  /** How transaction was matched */
  match_method: MatchMethodSchema,

  /** Matching details for audit trail */
  match_notes: z.string().optional(),

  /** When matched (ISO datetime) */
  matched_at: z.string().nullable().optional(),

  /** Who matched (user ID or null for auto) */
  matched_by: z.number().int().positive().nullable().optional(),

  /** Matched invoice details (nested object) */
  matched_invoice_details: z.object({
    id: z.number().int().positive(),
    invoice_number: z.string(),
    supplier_name: z.string(),
    supplier_tax_number: z.string(),
    gross_amount: z.string().nullable(),
    payment_due_date: z.string().nullable(),
    payment_status: z.string(),
  }).nullable().optional(),

  /** Statement details (nested object) */
  statement_details: z.object({
    id: z.number().int().positive(),
    bank_name: z.string(),
    account_number: z.string(),
    period_from: z.string(),
    period_to: z.string(),
  }).optional(),

  // Metadata
  /** Bank-specific extra data */
  raw_data: z.record(z.unknown()).optional(),

  /** Record creation time */
  created_at: z.string(),

  /** Last modification time */
  updated_at: z.string(),
});

export type BankTransaction = z.infer<typeof bankTransactionSchema>;

/**
 * Other cost category enum.
 *
 * Used for categorizing expenses extracted from transactions.
 */
export const OtherCostCategorySchema = z.enum([
  'BANK_FEE',
  'CARD_PURCHASE',
  'INTEREST',
  'SUBSCRIPTION',
  'UTILITY',
  'FUEL',
  'TRAVEL',
  'OFFICE',
  'OTHER',
]);
export type OtherCostCategory = z.infer<typeof OtherCostCategorySchema>;

/**
 * Other cost schema.
 *
 * Enhanced categorization layer for bank transactions.
 * Allows detailed expense tracking beyond standard transaction fields.
 */
export const otherCostSchema = z.object({
  /** Unique identifier */
  id: OtherCostIdSchema,

  /** Company ID */
  company: z.number().int().positive(),

  /** Linked bank transaction ID (optional) */
  bank_transaction: BankTransactionIdSchema.nullable(),

  /** Expense category */
  category: OtherCostCategorySchema,

  /** Subcategory for granular tracking */
  subcategory: z.string().max(100),

  /** Amount as decimal string */
  amount: z.string().regex(/^-?\d+(\.\d{1,2})?$/),

  /** Currency code */
  currency: z.string().length(3),

  /** Transaction date (ISO date) */
  date: z.string().date(),

  /** Enhanced description */
  description: z.string(),

  /** Additional notes */
  notes: z.string(),

  /** Custom remittance information */
  remittance_info: z.string().max(500),

  /** Created by user ID */
  created_by: z.number().int().positive(),

  /** Creation timestamp */
  created_at: z.string().datetime(),

  /** Last update timestamp */
  updated_at: z.string().datetime(),
});

export type OtherCost = z.infer<typeof otherCostSchema>;

/**
 * Paginated API response schema.
 *
 * Generic wrapper for paginated list responses from Django REST Framework.
 *
 * @template T - The Zod schema for items in the results array
 */
export const paginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    /** Total count of items across all pages */
    count: z.number().int().nonnegative(),

    /** URL for next page (null if last page) */
    next: z.string().url().nullable(),

    /** URL for previous page (null if first page) */
    previous: z.string().url().nullable(),

    /** Array of items for current page */
    results: z.array(itemSchema),
  });

/**
 * Bank statement list response schema.
 *
 * Validates paginated list of bank statements from API.
 */
export const bankStatementListResponseSchema = paginatedResponseSchema(bankStatementSchema);
export type BankStatementListResponse = z.infer<typeof bankStatementListResponseSchema>;

/**
 * Bank transaction list response schema.
 *
 * Validates paginated list of transactions from API.
 */
export const bankTransactionListResponseSchema = paginatedResponseSchema(bankTransactionSchema);
export type BankTransactionListResponse = z.infer<typeof bankTransactionListResponseSchema>;

/**
 * Other cost list response schema.
 *
 * Validates paginated list of other costs from API.
 */
export const otherCostListResponseSchema = paginatedResponseSchema(otherCostSchema);
export type OtherCostListResponse = z.infer<typeof otherCostListResponseSchema>;

/**
 * Supported bank information schema.
 *
 * Validates response from /api/bank-statements/supported_banks/ endpoint.
 */
export const supportedBankSchema = z.object({
  /** Bank code identifier */
  code: z.string().min(1),

  /** Full bank name */
  name: z.string().min(1),

  /** BIC/SWIFT code */
  bic: z.string().min(1),

  /** Supported file formats (optional - may not be provided by all banks) */
  formats: z.array(z.enum(['PDF', 'CSV', 'XML', 'XLS'])).optional(),
});

export type SupportedBank = z.infer<typeof supportedBankSchema>;

/**
 * Supported banks list response schema.
 */
export const supportedBanksResponseSchema = z.array(supportedBankSchema);
export type SupportedBanksResponse = z.infer<typeof supportedBanksResponseSchema>;

/**
 * File upload response schema.
 *
 * Validates response from /api/bank-statements/upload/ endpoint.
 * Backend returns the BankStatement object directly, not wrapped.
 */
export const uploadResponseSchema = bankStatementSchema;

export type UploadResponse = z.infer<typeof uploadResponseSchema>;

/**
 * Query parameters for bank statement filtering.
 */
export interface BankStatementQueryParams {
  /** Page number (1-indexed) */
  page?: number;

  /** Items per page */
  page_size?: number;

  /** Search term (account number, file name) */
  search?: string;

  /** Filter by bank code */
  bank_code?: string;

  /** Filter by status */
  status?: BankStatementStatus;

  /** Filter by period start date (ISO date) */
  period_from?: string;

  /** Filter by period end date (ISO date) */
  period_to?: string;

  /** Sort field (prefix with '-' for descending) */
  ordering?: string;
}

/**
 * Query parameters for bank transaction filtering.
 */
export interface BankTransactionQueryParams {
  /** Page number (1-indexed) */
  page?: number;

  /** Items per page */
  page_size?: number;

  /** Search term (description, reference) */
  search?: string;

  /** Filter by transaction type */
  transaction_type?: TransactionType;

  /** Filter by matched status */
  is_matched?: boolean;

  /** Filter by match confidence (minimum) */
  min_confidence?: string;

  /** Sort field (prefix with '-' for descending) */
  ordering?: string;
}

/**
 * Query parameters for other cost filtering.
 */
export interface OtherCostQueryParams {
  /** Page number (1-indexed) */
  page?: number;

  /** Items per page */
  page_size?: number;

  /** Search term (description, notes) */
  search?: string;

  /** Filter by category */
  category?: OtherCostCategory;

  /** Filter by date from (ISO date) */
  date_from?: string;

  /** Filter by date to (ISO date) */
  date_to?: string;

  /** Sort field (prefix with '-' for descending) */
  ordering?: string;
}
