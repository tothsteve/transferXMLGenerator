import { useAuth } from '../contexts/AuthContext';

/**
 * Hook for checking feature-based and role-based permissions
 * 
 * Implements two-layer permission checking:
 * 1. Company Feature Level: Is feature enabled for company?
 * 2. User Role Level: Does user role allow this specific action?
 */
export const usePermissions = () => {
  const { state } = useAuth();
  
  const enabledFeatures = state.currentCompany?.enabled_features || [];
  const userRole = state.currentCompany?.user_role || 'USER';
  
  /**
   * Check if a feature is enabled for the current company
   */
  const hasFeature = (featureCode: string): boolean => {
    return enabledFeatures.includes(featureCode);
  };
  
  /**
   * Check if user has permission for a specific feature and action
   */
  const hasPermission = (featureCode: string, action: 'view' | 'manage' = 'view'): boolean => {
    // Must have the feature enabled
    if (!hasFeature(featureCode)) {
      return false;
    }
    
    // For manage actions, check role-based permissions
    if (action === 'manage') {
      switch (featureCode) {
        case 'TRANSFER_AND_TEMPLATE_MANAGEMENT':
          return ['ADMIN', 'FINANCIAL'].includes(userRole);
        case 'BENEFICIARY_MANAGEMENT':
          return ['ADMIN', 'FINANCIAL'].includes(userRole);
        case 'BATCH_MANAGEMENT':
          return ['ADMIN'].includes(userRole);
        case 'NAV_SYNC':
          return ['ADMIN', 'ACCOUNTANT'].includes(userRole);
        case 'EXPORT_XML_SEPA':
        case 'EXPORT_CSV_KH':
          return ['ADMIN', 'FINANCIAL'].includes(userRole);
        default:
          return false;
      }
    }
    
    // For view actions, most roles can view if feature is enabled
    return true;
  };
  
  // Convenience methods for common permission checks
  return {
    // Basic feature checks
    hasFeature,
    hasPermission,
    
    // Beneficiary permissions
    canViewBeneficiaries: hasFeature('BENEFICIARY_VIEW') || hasFeature('BENEFICIARY_MANAGEMENT'),
    canManageBeneficiaries: hasPermission('BENEFICIARY_MANAGEMENT', 'manage'),
    
    // Transfer permissions  
    canViewTransfers: hasFeature('TRANSFER_VIEW') || hasFeature('TRANSFER_AND_TEMPLATE_MANAGEMENT'),
    canManageTransfers: hasPermission('TRANSFER_AND_TEMPLATE_MANAGEMENT', 'manage'),
    
    // Template permissions (same as transfers)
    canViewTemplates: hasFeature('TRANSFER_VIEW') || hasFeature('TRANSFER_AND_TEMPLATE_MANAGEMENT'),
    canManageTemplates: hasPermission('TRANSFER_AND_TEMPLATE_MANAGEMENT', 'manage'),
    
    // PDF Import permissions (same as transfers) 
    canAccessPDFImport: hasPermission('TRANSFER_AND_TEMPLATE_MANAGEMENT', 'manage'),
    
    // Batch permissions
    canViewBatches: hasFeature('BATCH_VIEW') || hasFeature('BATCH_MANAGEMENT'),
    canManageBatches: hasPermission('BATCH_MANAGEMENT', 'manage'),
    
    // NAV permissions
    canAccessNavInvoices: hasFeature('NAV_SYNC'),
    canManageNavInvoices: hasPermission('NAV_SYNC', 'manage'),
    
    // Export permissions
    canExportXML: hasPermission('EXPORT_XML_SEPA', 'manage'),
    canExportCSV: hasPermission('EXPORT_CSV_KH', 'manage'),
    
    // Current user info
    userRole,
    enabledFeatures,
    isAdmin: userRole === 'ADMIN',
  };
};

export default usePermissions;