from rest_framework import permissions
from .models import CompanyUser, UserProfile, CompanyFeature, FeatureTemplate
from functools import wraps
from django.http import JsonResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class FeatureNotEnabledException(Exception):
    """Exception raised when a feature is not enabled for the company"""
    def __init__(self, feature_code, company_name=None):
        self.feature_code = feature_code
        self.company_name = company_name
        super().__init__(f"Feature '{feature_code}' not enabled for company '{company_name}'")


class FeatureChecker:
    """Central service for checking feature enablement"""
    
    @staticmethod
    def is_feature_enabled(company, feature_code):
        """Check if a feature is enabled for the company"""
        try:
            company_feature = CompanyFeature.objects.select_related('feature_template').get(
                company=company,
                feature_template__feature_code=feature_code
            )
            return company_feature.is_enabled
        except CompanyFeature.DoesNotExist:
            # Feature doesn't exist for company - check if it's system critical
            try:
                feature_template = FeatureTemplate.objects.get(feature_code=feature_code)
                if feature_template.is_system_critical:
                    logger.warning(f"System critical feature {feature_code} not found for company {company.name}")
                    return True  # System critical features are assumed enabled if not explicitly disabled
                return False
            except FeatureTemplate.DoesNotExist:
                logger.error(f"Feature template {feature_code} does not exist")
                return False
    
    @staticmethod
    def check_feature_or_raise(company, feature_code):
        """Check feature and raise exception if not enabled"""
        if not FeatureChecker.is_feature_enabled(company, feature_code):
            raise FeatureNotEnabledException(feature_code, company.name if company else None)
    
    @staticmethod
    def check_multiple_features_or_raise(company, feature_codes, require_all=True):
        """Check multiple features - require_all=True means ALL must be enabled, False means ANY must be enabled"""
        if not feature_codes:
            return
        
        enabled_features = []
        disabled_features = []
        
        for feature_code in feature_codes:
            if FeatureChecker.is_feature_enabled(company, feature_code):
                enabled_features.append(feature_code)
            else:
                disabled_features.append(feature_code)
        
        if require_all and disabled_features:
            # ALL features required but some are disabled
            raise FeatureNotEnabledException(disabled_features[0], company.name if company else None)
        elif not require_all and not enabled_features:
            # ANY feature allowed but NONE are enabled
            raise FeatureNotEnabledException(feature_codes[0], company.name if company else None)
    
    @staticmethod
    def get_enabled_features_for_company(company):
        """Get all enabled features for a company"""
        return list(
            CompanyFeature.objects.filter(
                company=company,
                is_enabled=True
            ).select_related('feature_template').values_list(
                'feature_template__feature_code', flat=True
            )
        )


def require_feature_api(feature_code):
    """Decorator for API view methods that require a specific feature"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            # Extract request from args (self, request) or (request,)
            request = None
            if len(args) >= 2 and hasattr(args[1], 'company'):
                request = args[1]  # (self, request, ...)
            elif len(args) >= 1 and hasattr(args[0], 'company'):
                request = args[0]  # (request, ...)
            
            if not request:
                return JsonResponse({
                    'error': 'Could not determine request context',
                    'feature_required': feature_code
                }, status=400)
            
            if hasattr(request, 'company') and request.company:
                try:
                    FeatureChecker.check_feature_or_raise(request.company, feature_code)
                except FeatureNotEnabledException as e:
                    return JsonResponse({
                        'error': str(e),
                        'feature_required': feature_code,
                        'company': request.company.name,
                        'enabled_features': FeatureChecker.get_enabled_features_for_company(request.company)
                    }, status=403)
            else:
                return JsonResponse({
                    'error': 'No company context available',
                    'feature_required': feature_code
                }, status=400)
            
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator


def require_features_api(*feature_codes, require_all=True):
    """Decorator for API view methods that require multiple features"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            # Extract request from args
            request = None
            if len(args) >= 2 and hasattr(args[1], 'company'):
                request = args[1]  # (self, request, ...)
            elif len(args) >= 1 and hasattr(args[0], 'company'):
                request = args[0]  # (request, ...)
            
            if not request:
                return JsonResponse({
                    'error': 'Could not determine request context',
                    'features_required': list(feature_codes),
                    'require_all': require_all
                }, status=400)
            
            if hasattr(request, 'company') and request.company:
                try:
                    FeatureChecker.check_multiple_features_or_raise(
                        request.company, feature_codes, require_all=require_all
                    )
                except FeatureNotEnabledException as e:
                    return JsonResponse({
                        'error': str(e),
                        'features_required': list(feature_codes),
                        'require_all': require_all,
                        'company': request.company.name,
                        'enabled_features': FeatureChecker.get_enabled_features_for_company(request.company)
                    }, status=403)
            else:
                return JsonResponse({
                    'error': 'No company context available',
                    'features_required': list(feature_codes),
                    'require_all': require_all
                }, status=400)
            
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator


class FeatureBasedPermission(permissions.BasePermission):
    """DRF Permission class that checks feature enablement"""
    required_features = []
    require_all_features = True
    
    def has_permission(self, request, view):
        if not self.required_features:
            return True
        
        if not hasattr(request, 'company') or not request.company:
            return False
        
        try:
            FeatureChecker.check_multiple_features_or_raise(
                request.company, 
                self.required_features, 
                require_all=self.require_all_features
            )
            return True
        except FeatureNotEnabledException:
            return False
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class RequireBeneficiaryManagement(FeatureBasedPermission):
    """Permission class for beneficiary management features with role-based restrictions"""
    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False
        
        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user, 
                company=request.company,
                is_active=True
            )
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            return False
        
        # Check for write operations vs read operations
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Write operations require BENEFICIARY_MANAGEMENT
            required_feature = 'BENEFICIARY_MANAGEMENT'
            
            # Check both company feature enablement AND user role permission
            return (
                FeatureChecker.is_feature_enabled(request.company, required_feature) and
                (required_feature in user_allowed_features or '*' in user_allowed_features)
            )
        else:
            # Read operations - allow either management or view-only
            company_has_feature = (
                FeatureChecker.is_feature_enabled(request.company, 'BENEFICIARY_MANAGEMENT') or
                FeatureChecker.is_feature_enabled(request.company, 'BENEFICIARY_VIEW')
            )
            
            user_has_permission = (
                'BENEFICIARY_MANAGEMENT' in user_allowed_features or
                'BENEFICIARY_VIEW' in user_allowed_features or
                '*' in user_allowed_features
            )
            
            return company_has_feature and user_has_permission


class RequireTransferManagement(FeatureBasedPermission):
    """Permission class for transfer management features with role-based restrictions"""
    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False
        
        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user, 
                company=request.company,
                is_active=True
            )
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            return False
        
        # Check for write operations vs read operations
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Write operations require TRANSFER_MANAGEMENT or TRANSFER_AND_TEMPLATE_MANAGEMENT (backwards compatibility)
            company_has_feature = (
                FeatureChecker.is_feature_enabled(request.company, 'TRANSFER_MANAGEMENT') or
                FeatureChecker.is_feature_enabled(request.company, 'TRANSFER_AND_TEMPLATE_MANAGEMENT')
            )
            
            user_has_permission = (
                'TRANSFER_MANAGEMENT' in user_allowed_features or
                'TRANSFER_AND_TEMPLATE_MANAGEMENT' in user_allowed_features or
                '*' in user_allowed_features
            )
            
            return company_has_feature and user_has_permission
        else:
            # Read operations - allow either management or view-only
            company_has_feature = (
                FeatureChecker.is_feature_enabled(request.company, 'TRANSFER_MANAGEMENT') or
                FeatureChecker.is_feature_enabled(request.company, 'TRANSFER_AND_TEMPLATE_MANAGEMENT') or
                FeatureChecker.is_feature_enabled(request.company, 'TRANSFER_VIEW')
            )
            
            user_has_permission = (
                'TRANSFER_MANAGEMENT' in user_allowed_features or
                'TRANSFER_AND_TEMPLATE_MANAGEMENT' in user_allowed_features or
                'TRANSFER_VIEW' in user_allowed_features or
                '*' in user_allowed_features
            )
            
            return company_has_feature and user_has_permission


class RequireBatchManagement(FeatureBasedPermission):
    """Permission class for batch management features with role-based restrictions"""
    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False
        
        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user, 
                company=request.company,
                is_active=True
            )
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            return False
        
        # Check for write operations vs read operations
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Write operations require BATCH_MANAGEMENT
            required_feature = 'BATCH_MANAGEMENT'
            
            # Check both company feature enablement AND user role permission
            return (
                FeatureChecker.is_feature_enabled(request.company, required_feature) and
                (required_feature in user_allowed_features or '*' in user_allowed_features)
            )
        else:
            # Read operations - allow either management or view-only
            company_has_feature = (
                FeatureChecker.is_feature_enabled(request.company, 'BATCH_MANAGEMENT') or
                FeatureChecker.is_feature_enabled(request.company, 'BATCH_VIEW')
            )
            
            user_has_permission = (
                'BATCH_MANAGEMENT' in user_allowed_features or
                'BATCH_VIEW' in user_allowed_features or
                '*' in user_allowed_features
            )
            
            return company_has_feature and user_has_permission


class RequireNavSync(FeatureBasedPermission):
    """Permission class for NAV synchronization features with role-based restrictions"""
    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False
        
        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user, 
                company=request.company,
                is_active=True
            )
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            return False
        
        # NAV_SYNC feature required
        required_feature = 'NAV_SYNC'
        
        # Check both company feature enablement AND user role permission
        return (
            FeatureChecker.is_feature_enabled(request.company, required_feature) and
            (required_feature in user_allowed_features or '*' in user_allowed_features)
        )


class RequireExportFeatures(FeatureBasedPermission):
    """Permission class for export features with role-based restrictions"""
    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False

        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user,
                company=request.company,
                is_active=True
            )
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            return False

        # For export endpoints, require at least one export feature
        export_features = ['EXPORT_XML_SEPA', 'EXPORT_CSV_KH', 'EXPORT_CSV_CUSTOM']

        for feature in export_features:
            # Check both company feature enablement AND user role permission
            if (FeatureChecker.is_feature_enabled(request.company, feature) and
                (feature in user_allowed_features or '*' in user_allowed_features)):
                return True

        return False


class RequireBankStatementImport(FeatureBasedPermission):
    """
    Permission class for bank statement import functionality.

    Requires BANK_STATEMENT_IMPORT feature to be enabled for the company.

    Access levels by role:
    - ADMIN: Full access (upload, view, delete, match/unmatch, categorize)
    - FINANCIAL: Full access (same as ADMIN)
    - ACCOUNTANT: View only (cannot upload, delete, or modify)
    - USER: View only (cannot upload, delete, or modify)
    """

    required_features = ['BANK_STATEMENT_IMPORT']

    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False

        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user,
                company=request.company,
                is_active=True
            )
            user_role = company_user.role
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            logger.warning(f"User {request.user.username} has no role in company {request.company}")
            return False

        # Check if BANK_STATEMENT_IMPORT feature is enabled for company AND user has permission
        required_feature = 'BANK_STATEMENT_IMPORT'
        if not (FeatureChecker.is_feature_enabled(request.company, required_feature) and
                (required_feature in user_allowed_features or '*' in user_allowed_features)):
            return False

        # Read operations (GET, HEAD, OPTIONS) - all roles with feature enabled
        if request.method in permissions.SAFE_METHODS:
            return user_role in ['ADMIN', 'FINANCIAL', 'ACCOUNTANT', 'USER']

        # Write operations - check view action and role
        action = getattr(view, 'action', None)

        # Upload, delete, match, unmatch, categorize - ADMIN and FINANCIAL only
        if action in ['create', 'upload', 'destroy', 'match_invoice', 'unmatch_invoice', 'categorize_cost']:
            return user_role in ['ADMIN', 'FINANCIAL']

        # Update operations - ADMIN and FINANCIAL only
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return user_role in ['ADMIN', 'FINANCIAL']

        # Default deny
        return False


class RequireBillingoSync(FeatureBasedPermission):
    """
    Permission class for Billingo invoice synchronization functionality.

    Requires BILLINGO_SYNC feature to be enabled for the company.

    Access levels by role:
    - ADMIN: Full access (manage settings, trigger sync, view invoices)
    - FINANCIAL: View only (cannot manage settings or trigger sync)
    - ACCOUNTANT: View only (cannot manage settings or trigger sync)
    - USER: No access
    """

    required_features = ['BILLINGO_SYNC']

    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False

        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user,
                company=request.company,
                is_active=True
            )
            user_role = company_user.role
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            logger.warning(f"User {request.user.username} has no role in company {request.company}")
            return False

        # Check if BILLINGO_SYNC feature is enabled for company
        if not FeatureChecker.is_feature_enabled(request.company, 'BILLINGO_SYNC'):
            return False

        # Check if user's role allows BILLINGO_SYNC
        if 'BILLINGO_SYNC' not in user_allowed_features and '*' not in user_allowed_features:
            return False

        # Settings management and sync trigger - ADMIN only
        if view.action in ['create', 'update', 'partial_update', 'destroy', 'trigger_sync']:
            return user_role == 'ADMIN'

        # View operations - ADMIN, FINANCIAL, ACCOUNTANT
        if request.method in permissions.SAFE_METHODS:
            return user_role in ['ADMIN', 'FINANCIAL', 'ACCOUNTANT']

        # Default deny
        return False


class RequireBaseTables(FeatureBasedPermission):
    """
    Permission class for BASE_TABLES (Alaptáblák) functionality.

    Requires BASE_TABLES feature to be enabled for the company.

    Access levels by role:
    - ADMIN: Full access (create, read, update, delete)
    - FINANCIAL: No access
    - ACCOUNTANT: No access
    - USER: No access
    """

    required_features = ['BASE_TABLES']

    def has_permission(self, request, view):
        if not hasattr(request, 'company') or not request.company:
            return False

        # Get user's company membership and allowed features
        try:
            from .models import CompanyUser
            company_user = CompanyUser.objects.get(
                user=request.user,
                company=request.company,
                is_active=True
            )
            user_role = company_user.role
            user_allowed_features = company_user.get_allowed_features()
        except CompanyUser.DoesNotExist:
            logger.warning(f"User {request.user.username} has no role in company {request.company}")
            return False

        # Check if BASE_TABLES feature is enabled for company
        if not FeatureChecker.is_feature_enabled(request.company, 'BASE_TABLES'):
            return False

        # Check if user's role allows BASE_TABLES
        if 'BASE_TABLES' not in user_allowed_features and '*' not in user_allowed_features:
            return False

        # All operations (read and write) - ADMIN only
        return user_role == 'ADMIN'


class IsCompanyMember(permissions.BasePermission):
    """
    Engedély: felhasználó tagja a cégnek
    ALSO sets request.company if not already set
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Set company context if not already set
        if not hasattr(request, 'company') or not request.company:
            self._set_company_context(request)

        # Get company from request context
        company = getattr(request, 'company', None)
        if not company:
            return False

        # Check if user is a member of this company
        return CompanyUser.objects.filter(
            user=request.user,
            company=company,
            is_active=True
        ).exists()

    def _set_company_context(self, request):
        """Set request.company based on X-Company-ID header or user profile"""
        # Get company from header
        company_id = request.META.get('HTTP_X_COMPANY_ID')

        if company_id:
            try:
                company_id = int(company_id)
                # Verify user has access to this company
                membership = CompanyUser.objects.filter(
                    user=request.user,
                    company_id=company_id,
                    is_active=True
                ).select_related('company').first()

                if membership:
                    request.company = membership.company
                    return
            except (ValueError, TypeError):
                pass

        # Fallback to user's last active company
        try:
            profile = UserProfile.objects.select_related('last_active_company').get(user=request.user)
            if profile.last_active_company:
                # Verify user still has access to this company
                if CompanyUser.objects.filter(
                    user=request.user,
                    company=profile.last_active_company,
                    is_active=True
                ).exists():
                    request.company = profile.last_active_company
                    return
        except UserProfile.DoesNotExist:
            pass

        # Find first available company for user
        membership = CompanyUser.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if membership:
            request.company = membership.company
            # Update user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.last_active_company = membership.company
            profile.save()
        else:
            request.company = None


class IsCompanyAdmin(IsCompanyMember):
    """
    Engedély: felhasználó adminisztrátor a cégben
    Inherits company context setting from IsCompanyMember
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Set company context if not already set
        if not hasattr(request, 'company') or not request.company:
            self._set_company_context(request)
        
        # Get company from request context
        company = getattr(request, 'company', None)
        if not company:
            return False
        
        # Check if user is an admin of this company
        return CompanyUser.objects.filter(
            user=request.user,
            company=company,
            role='ADMIN',
            is_active=True
        ).exists()


class IsCompanyAdminOrReadOnly(IsCompanyMember):
    """
    Engedély: felhasználó adminisztrátor vagy csak olvasási jog
    Inherits company context setting from IsCompanyMember
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Set company context if not already set
        if not hasattr(request, 'company') or not request.company:
            self._set_company_context(request)
        
        # Get company from request context
        company = getattr(request, 'company', None)
        if not company:
            return False
        
        # Check if user is a member of this company
        membership = CompanyUser.objects.filter(
            user=request.user,
            company=company,
            is_active=True
        ).first()
        
        if not membership:
            return False
        
        # Allow read operations for all members
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations only for admins
        return membership.role == 'ADMIN'

