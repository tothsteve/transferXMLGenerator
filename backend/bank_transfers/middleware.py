from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import Company, CompanyUser, UserProfile


class CompanyContextMiddleware(MiddlewareMixin):
    """
    Middleware a céges kontextus beállításához
    """
    
    def process_request(self, request):
        """
        Beállítja a request.company attribútumot a felhasználó aktív cége alapján
        """
        request.company = None
        
        # Only process for authenticated users
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Skip for authentication endpoints
        if request.path.startswith('/api/auth/'):
            return None
        
        # Get company from header or user profile
        company_id = request.headers.get('X-Company-ID')
        
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
                    # Update user's last active company
                    profile, created = UserProfile.objects.get_or_create(user=request.user)
                    if profile.last_active_company != membership.company:
                        profile.last_active_company = membership.company
                        profile.save()
                else:
                    return JsonResponse({
                        'error': 'Nincs jogosultság ehhez a céghez'
                    }, status=403)
            except (ValueError, TypeError):
                return JsonResponse({
                    'error': 'Érvénytelen cég azonosító'
                }, status=400)
        else:
            # Use user's last active company
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
                    else:
                        # Find first available company for user
                        membership = CompanyUser.objects.filter(
                            user=request.user,
                            is_active=True
                        ).select_related('company').first()
                        
                        if membership:
                            request.company = membership.company
                            profile.last_active_company = membership.company
                            profile.save()
                        else:
                            return JsonResponse({
                                'error': 'Nincs aktív céges tagság'
                            }, status=403)
                else:
                    # No last active company, find first available
                    membership = CompanyUser.objects.filter(
                        user=request.user,
                        is_active=True
                    ).select_related('company').first()
                    
                    if membership:
                        request.company = membership.company
                        profile.last_active_company = membership.company
                        profile.save()
                    else:
                        return JsonResponse({
                            'error': 'Nincs aktív céges tagság'
                        }, status=403)
            except UserProfile.DoesNotExist:
                # Create profile and find first available company
                membership = CompanyUser.objects.filter(
                    user=request.user,
                    is_active=True
                ).select_related('company').first()
                
                if membership:
                    request.company = membership.company
                    UserProfile.objects.create(
                        user=request.user,
                        last_active_company=membership.company
                    )
                else:
                    return JsonResponse({
                        'error': 'Nincs aktív céges tagság'
                    }, status=403)
        
        return None