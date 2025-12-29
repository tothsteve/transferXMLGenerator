/**
 * Bank Transaction API Service
 *
 * API client for bank transaction match management operations.
 * Handles approve, unmatch, rematch, and manual matching.
 */

import { apiClient } from './api';

/**
 * Response from approve_match endpoint
 */
export interface ApproveMatchResponse {
  message: string;
  previous_confidence: string;
  new_confidence: string;
  matched_invoices: number;
  is_batch_match: boolean;
  approved_by: string;
  approved_at: string;
}

/**
 * Response from unmatch endpoint
 */
export interface UnmatchResponse {
  message: string;
  was_batch_match: boolean;
  invoices_unmatched: number;
}

/**
 * Response from rematch endpoint
 */
export interface RematchResponse {
  matched: boolean;
  invoice_id?: number;
  invoice_ids?: number[];
  confidence?: string;
  method?: string;
  auto_paid: boolean;
}

/**
 * Response from manual match endpoint
 */
export interface ManualMatchResponse {
  message: string;
  transaction_id: number;
  invoice_id: number;
  confidence: string;
  method: string;
}

/**
 * Response from batch match endpoint
 */
export interface BatchMatchResponse {
  message: string;
  transaction_id: number;
  invoice_ids: number[];
  total_amount: string;
  confidence: string;
  method: string;
}

/**
 * Bank Transaction API client functions
 */
export const bankTransactionApi = {
  /**
   * Approve an automatic match (upgrade confidence to 1.00).
   *
   * @param transactionId - ID of the transaction
   * @returns Promise resolving to approval response
   */
  approveMatch: async (transactionId: number): Promise<ApproveMatchResponse> => {
    const response = await apiClient.post(
      `/bank-transactions/${transactionId}/approve_match/`
    );
    return response.data;
  },

  /**
   * Remove all matches from a transaction.
   *
   * @param transactionId - ID of the transaction
   * @returns Promise resolving to unmatch response
   */
  unmatch: async (transactionId: number): Promise<UnmatchResponse> => {
    const response = await apiClient.post(
      `/bank-transactions/${transactionId}/unmatch/`
    );
    return response.data;
  },

  /**
   * Re-run automatic matching for a transaction.
   *
   * @param transactionId - ID of the transaction
   * @returns Promise resolving to rematch response
   */
  rematch: async (transactionId: number): Promise<RematchResponse> => {
    const response = await apiClient.post(
      `/bank-transactions/${transactionId}/rematch/`
    );
    return response.data;
  },

  /**
   * Manually match transaction to a single invoice.
   *
   * @param transactionId - ID of the transaction
   * @param invoiceId - ID of the invoice to match
   * @returns Promise resolving to match response
   */
  matchInvoice: async (
    transactionId: number,
    invoiceId: number
  ): Promise<ManualMatchResponse> => {
    const response = await apiClient.post(
      `/bank-transactions/${transactionId}/match_invoice/`,
      { invoice_id: invoiceId }
    );
    return response.data;
  },

  /**
   * Manually match transaction to multiple invoices (batch payment).
   *
   * @param transactionId - ID of the transaction
   * @param invoiceIds - Array of invoice IDs to match
   * @returns Promise resolving to batch match response
   */
  batchMatchInvoices: async (
    transactionId: number,
    invoiceIds: number[]
  ): Promise<BatchMatchResponse> => {
    const response = await apiClient.post(
      `/bank-transactions/${transactionId}/batch_match_invoices/`,
      { invoice_ids: invoiceIds }
    );
    return response.data;
  },
};
