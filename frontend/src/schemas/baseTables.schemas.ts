/**
 * Zod validation schemas for BASE_TABLES (Alaptáblák) API responses
 *
 * These schemas provide runtime type checking for Suppliers, Customers, and Product Prices
 * to ensure data integrity throughout the application.
 */

import { z } from 'zod';

// ============================================================================
// Supplier (Beszállító) Schema
// ============================================================================

export const SupplierSchema = z.object({
  id: z.number(),
  company: z.number(),
  company_name: z.string().optional(),
  partner_name: z.string(),
  category: z.string().nullable().optional(),
  type: z.string().nullable().optional(),
  valid_from: z.string().nullable().optional(),
  valid_to: z.string().nullable().optional(),
  is_valid: z.boolean().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type SupplierSchemaType = z.infer<typeof SupplierSchema>;

// ============================================================================
// Customer (Vevő) Schema
// ============================================================================

export const CustomerSchema = z.object({
  id: z.number(),
  company: z.number(),
  company_name: z.string().optional(),
  customer_name: z.string(),
  cashflow_adjustment: z.number(),
  valid_from: z.string().nullable().optional(),
  valid_to: z.string().nullable().optional(),
  is_valid: z.boolean().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type CustomerSchemaType = z.infer<typeof CustomerSchema>;

// ============================================================================
// Product Price (CONMED árak) Schema
// ============================================================================

export const ProductPriceSchema = z.object({
  id: z.number(),
  company: z.number(),
  company_name: z.string().optional(),
  product_value: z.string(),
  product_description: z.string(),
  uom: z.string().nullable().optional(),
  uom_hun: z.string().nullable().optional(),
  purchase_price_usd: z.string().nullable().optional(),
  purchase_price_huf: z.string().nullable().optional(),
  markup: z.string().nullable().optional(),
  sales_price_huf: z.string().nullable().optional(),
  cap_disp: z.string().nullable().optional(),
  is_inventory_managed: z.boolean(),
  valid_from: z.string().nullable().optional(),
  valid_to: z.string().nullable().optional(),
  is_valid: z.boolean().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type ProductPriceSchemaType = z.infer<typeof ProductPriceSchema>;

// ============================================================================
// Input Schemas for Create/Update Operations
// ============================================================================

export const SupplierInputSchema = SupplierSchema.omit({
  id: true,
  company: true,
  company_name: true,
  is_valid: true,
  created_at: true,
  updated_at: true,
});

export type SupplierInputSchemaType = z.infer<typeof SupplierInputSchema>;

export const CustomerInputSchema = CustomerSchema.omit({
  id: true,
  company: true,
  company_name: true,
  is_valid: true,
  created_at: true,
  updated_at: true,
});

export type CustomerInputSchemaType = z.infer<typeof CustomerInputSchema>;

export const ProductPriceInputSchema = ProductPriceSchema.omit({
  id: true,
  company: true,
  company_name: true,
  is_valid: true,
  created_at: true,
  updated_at: true,
});

export type ProductPriceInputSchemaType = z.infer<typeof ProductPriceInputSchema>;
