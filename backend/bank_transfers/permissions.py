from rest_framework import permissions
from .models import CompanyUser, UserProfile


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