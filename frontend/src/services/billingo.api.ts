/**
 * Billingo API Service
 *
 * Dedicated API client for Billingo invoice synchronization.
 * Handles settings, invoices, and sync logs.
 */

import { apiClient } from './api';
import {
  BillingoInvoice,
  BillingoInvoiceDetail,
  CompanyBillingoSettings,
  CompanyBillingoSettingsInput,
  BillingoSyncLog,
  BillingoSyncTriggerResponse,
  ApiResponse,
} from '../types/api';
import {
  BillingoInvoiceDetailSchema,
  CompanyBillingoSettingsSchema,
  BillingoSyncTriggerResponseSchema,
} from '../schemas/api.schemas';

/**
 * Billingo API client functions
 */
export const billingoApi = {
  /**
   * Get company Billingo settings (API key configuration).
   *
   * @returns Promise resolving to settings or null if not configured
   */
  getSettings: async (): Promise<CompanyBillingoSettings | null> => {
    const response = await apiClient.get('/billingo-settings/');
    const data = response.data;

    // API returns paginated response with results array
    // If no settings configured, results will be empty
    if (!data.results || !Array.isArray(data.results) || data.results.length === 0) {
      return null;
    }

    // Get first settings object from results
    const settings = data.results[0];

    // Check if settings object exists and has required fields
    if (!settings || typeof settings !== 'object' || !settings.id) {
      return null;
    }

    return CompanyBillingoSettingsSchema.parse(settings);
  },

  /**
   * Create or update Billingo settings (API key).
   * ADMIN role required.
   *
   * @param data - Settings data with API key
   * @returns Promise resolving to created/updated settings
   */
  saveSettings: async (data: CompanyBillingoSettingsInput): Promise<CompanyBillingoSettings> => {
    const response = await apiClient.post('/billingo-settings/', data);
    return CompanyBillingoSettingsSchema.parse(response.data);
  },

  /**
   * Trigger manual Billingo invoice sync.
   * ADMIN role required.
   *
   * @param full_sync - If true, ignores last sync date and fetches all invoices
   * @returns Promise resolving to sync result metrics
   */
  triggerSync: async (full_sync: boolean = false): Promise<BillingoSyncTriggerResponse> => {
    const response = await apiClient.post('/billingo-settings/trigger_sync/', { full_sync });
    return BillingoSyncTriggerResponseSchema.parse(response.data);
  },

  /**
   * Get paginated list of Billingo invoices.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to invoice list response
   */
  getInvoices: async (params?: {
    page?: number;
    page_size?: number;
    payment_status?: string;
    search?: string;
    ordering?: string;
  }): Promise<ApiResponse<BillingoInvoice>> => {
    const response = await apiClient.get('/billingo-invoices/', { params });
    return response.data;
  },

  /**
   * Get single Billingo invoice with line items.
   *
   * @param id - Billingo invoice ID
   * @returns Promise resolving to invoice detail with items
   */
  getInvoiceById: async (id: number): Promise<BillingoInvoiceDetail> => {
    const response = await apiClient.get(`/billingo-invoices/${id}/`);
    return BillingoInvoiceDetailSchema.parse(response.data) as BillingoInvoiceDetail;
  },

  /**
   * Get paginated list of sync logs.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Promise resolving to sync log list response
   */
  getSyncLogs: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    ordering?: string;
  }): Promise<ApiResponse<BillingoSyncLog>> => {
    const response = await apiClient.get('/billingo-sync-logs/', { params });
    return response.data;
  },
};
