/**
 * Zod validation schemas for API responses
 *
 * These schemas provide runtime type checking to catch API contract violations
 * and ensure data integrity throughout the application.
 */

import { z } from 'zod';

// ============================================================================
// Beneficiary Schemas
// ============================================================================

export const BeneficiarySchema = z.object({
  id: z.number(),
  name: z.string(),
  account_number: z.string().nullish(),
  vat_number: z.string().nullish(),
  tax_number: z.string().nullish(),
  description: z.string(),
  remittance_information: z.string(),
  is_frequent: z.boolean(),
  is_active: z.boolean(),
});

export type BeneficiarySchemaType = z.infer<typeof BeneficiarySchema>;

// ============================================================================
// Bank Account Schemas
// ============================================================================

export const BankAccountSchema = z.object({
  id: z.number(),
  name: z.string(),
  account_number: z.string(),
  bank_name: z.string(),
  is_default: z.boolean(),
});

export type BankAccountSchemaType = z.infer<typeof BankAccountSchema>;

// ============================================================================
// Transfer Template Schemas
// ============================================================================

export const TemplateBeneficiarySchema = z.object({
  id: z.number(),
  template: z.number().optional(),
  beneficiary: BeneficiarySchema,
  default_amount: z.union([z.string(), z.number()]).nullish(),
  default_remittance: z.string(),
  order: z.number(),
  is_active: z.boolean(),
});

export const TransferTemplateSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string().nullish(),
  is_active: z.boolean(),
  beneficiary_count: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
  template_beneficiaries: z.array(TemplateBeneficiarySchema).optional(),
});

export type TransferTemplateSchemaType = z.infer<typeof TransferTemplateSchema>;

// ============================================================================
// Transfer Schemas
// ============================================================================

export const CurrencySchema = z.enum(['HUF', 'EUR', 'USD']);

export const TransferSchema = z.object({
  id: z.number().optional(),
  beneficiary: z.number(),
  beneficiary_data: BeneficiarySchema.optional(),
  amount: z.string(),
  currency: CurrencySchema,
  execution_date: z.string(),
  remittance_info: z.string(),
  nav_invoice: z.number().nullable().optional(),
  is_processed: z.boolean(),
  created_at: z.string().optional(),
});

export const TransferWithBeneficiarySchema = z.object({
  id: z.number().optional(),
  beneficiary: BeneficiarySchema,
  amount: z.string(),
  currency: CurrencySchema,
  execution_date: z.string(),
  remittance_info: z.string(),
  nav_invoice: z.number().nullable().optional(),
  is_processed: z.boolean(),
  created_at: z.string().optional(),
});

export type TransferSchemaType = z.infer<typeof TransferSchema>;

// ============================================================================
// Transfer Batch Schemas
// ============================================================================

export const TransferBatchSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string().nullish(),
  transfers: z.array(TransferWithBeneficiarySchema),
  total_amount: z.string(),
  used_in_bank: z.boolean(),
  bank_usage_date: z.string().nullish(),
  order: z.number(),
  transfer_count: z.number(),
  xml_filename: z.string(),
  xml_generated_at: z.string().nullish(),
  created_at: z.string(),
  batch_format: z.string().nullish(),
  batch_format_display: z.string().nullish(),
});

export type TransferBatchSchemaType = z.infer<typeof TransferBatchSchema>;

// ============================================================================
// NAV Invoice Schemas
// ============================================================================

export const PaymentStatusSchema = z.object({
  status: z.string(),
  label: z.string(),
  icon: z.string(),
  class: z.string(),
});

export const InvoiceDirectionSchema = z.enum(['INBOUND', 'OUTBOUND']);

export const NAVInvoiceSchema = z.object({
  id: z.number(),
  nav_invoice_number: z.string(),
  invoice_direction: InvoiceDirectionSchema,
  invoice_direction_display: z.string(),
  partner_name: z.string(),
  partner_tax_number: z.string(),

  // Dates
  issue_date: z.string(),
  issue_date_formatted: z.string(),
  fulfillment_date: z.string().nullish(),
  fulfillment_date_formatted: z.string().nullish(),
  payment_due_date: z.string().nullish(),
  payment_due_date_formatted: z.string().nullish(),
  payment_date: z.string().nullish(),
  payment_date_formatted: z.string().nullish(),
  completion_date: z.string().nullish(),
  last_modified_date: z.string().nullish(),

  // Financial - accept both string and number, coerce to number
  currency_code: z.string(),
  invoice_net_amount: z.union([z.number(), z.string()]).transform(val => typeof val === 'string' ? parseFloat(val) : val),
  invoice_net_amount_formatted: z.string(),
  invoice_vat_amount: z.union([z.number(), z.string()]).transform(val => typeof val === 'string' ? parseFloat(val) : val),
  invoice_vat_amount_formatted: z.string(),
  invoice_gross_amount: z.union([z.number(), z.string()]).transform(val => typeof val === 'string' ? parseFloat(val) : val),
  invoice_gross_amount_formatted: z.string(),

  // Business
  invoice_operation: z.string().nullish(),
  invoice_category: z.string().nullish(),
  invoice_appearance: z.string().nullish(),
  payment_method: z.string().nullish(),
  original_invoice_number: z.string().nullish(),
  payment_status: PaymentStatusSchema,
  payment_status_date: z.string().nullish(),
  payment_status_date_formatted: z.string().nullish(),
  auto_marked_paid: z.boolean().default(false),
  is_overdue: z.boolean().default(false),
  is_paid: z.boolean().default(false),

  // System
  sync_status: z.string(),
  created_at: z.string(),

  // NAV metadata (available in detail view)
  nav_source: z.string().nullish(),
  original_request_version: z.string().nullish(),

  // Partners (available in detail view)
  supplier_name: z.string().nullish(),
  customer_name: z.string().nullish(),
  supplier_tax_number: z.string().nullish(),
  customer_tax_number: z.string().nullish(),
  supplier_bank_account_number: z.string().nullish(),
  customer_bank_account_number: z.string().nullish(),
});

export type NAVInvoiceSchemaType = z.infer<typeof NAVInvoiceSchema>;

// ============================================================================
// Trusted Partner Schemas
// ============================================================================

export const TrustedPartnerSchema = z.object({
  id: z.number(),
  partner_name: z.string(),
  tax_number: z.string(),
  is_active: z.boolean(),
  auto_pay: z.boolean(),
  invoice_count: z.number(),
  last_invoice_date: z.string().nullable(),
  last_invoice_date_formatted: z.string().nullish(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type TrustedPartnerSchemaType = z.infer<typeof TrustedPartnerSchema>;

// ============================================================================
// Generic API Response Schema
// ============================================================================

export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T): z.ZodObject<{
  count: z.ZodNumber;
  next: z.ZodNullable<z.ZodString>;
  previous: z.ZodNullable<z.ZodString>;
  results: z.ZodArray<T>;
}> =>
  z.object({
    count: z.number(),
    next: z.string().nullable(),
    previous: z.string().nullable(),
    results: z.array(dataSchema),
  });

// ============================================================================
// Request Schemas
// ============================================================================

export const CreateTransferDataSchema = z.object({
  originator_account_id: z.number(),
  beneficiary_id: z.number(),
  amount: z.string(),
  currency: CurrencySchema,
  execution_date: z.string(),
  remittance_info: z.string(),
  order: z.number(),
});

export const BulkCreateTransferRequestSchema = z.object({
  transfers: z.array(CreateTransferDataSchema),
});

export const GenerateXmlRequestSchema = z.object({
  transfer_ids: z.array(z.number()),
  batch_name: z.string().nullish(),
});

// ============================================================================
// Response Schemas
// ============================================================================

export const GenerateXmlResponseSchema = z.object({
  xml: z.string(),
  transfer_count: z.number(),
  total_amount: z.string(),
});

export const GenerateKHExportResponseSchema = z.object({
  content: z.string(),
  filename: z.string(),
  encoding: z.string(),
  content_encoding: z.string().nullish(),
  transfer_count: z.number(),
  total_amount: z.string(),
});

export const LoadTemplateResponseSchema = z.object({
  template: TransferTemplateSchema,
  transfers: z.array(TransferSchema.omit({ id: true, is_processed: true, created_at: true })),
});

export const ExcelImportResponseSchema = z.object({
  imported_count: z.number(),
  errors: z.array(z.string()),
});
