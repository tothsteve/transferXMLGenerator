from rest_framework import permissions
from .models import CompanyUser


class IsCompanyMember(permissions.BasePermission):
    """
    Engedély: felhasználó tagja a cégnek
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
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


class IsCompanyAdmin(permissions.BasePermission):
    """
    Engedély: felhasználó adminisztrátor a cégben
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
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


class IsCompanyAdminOrReadOnly(permissions.BasePermission):
    """
    Engedély: felhasználó adminisztrátor vagy csak olvasási jog
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
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