"""
Company User Management Views - User and role management endpoints

Handles CRUD operations for company users and role assignments.
Only accessible to company admins.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import CompanyUser
from ..permissions import IsCompanyAdmin


class CompanyUsersView(APIView):
    """
    Company user management endpoints
    Only admins can access these endpoints
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def get(self, request):
        """Get all users for the current company"""
        company = request.company

        company_users = CompanyUser.objects.filter(
            company=company,
            is_active=True
        ).select_related('user').order_by('user__last_name', 'user__first_name')

        users_data = []
        for company_user in company_users:
            users_data.append({
                'id': company_user.id,
                'user': {
                    'id': company_user.user.id,
                    'username': company_user.user.username,
                    'email': company_user.user.email,
                    'first_name': company_user.user.first_name,
                    'last_name': company_user.user.last_name,
                },
                'role': company_user.role,
                'is_active': company_user.is_active,
                'joined_at': company_user.joined_at.isoformat(),
            })

        return Response(users_data)


class CompanyUserDetailView(APIView):
    """
    Company user detail endpoints (update/delete)
    Only admins can access these endpoints
    """
    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def put(self, request, user_id):
        """Update user role"""
        try:
            company_user = CompanyUser.objects.get(
                id=user_id,
                company=request.company,
                is_active=True
            )
        except CompanyUser.DoesNotExist:
            return Response({'detail': 'Felhasználó nem található'}, status=404)

        # Don't allow users to change their own role
        if company_user.user.id == request.user.id:
            return Response({'detail': 'Nem módosíthatja saját szerepkörét'}, status=400)

        role = request.data.get('role')
        if role not in ['ADMIN', 'USER']:
            return Response({'detail': 'Érvénytelen szerepkör'}, status=400)

        company_user.role = role
        company_user.save()

        return Response({
            'id': company_user.id,
            'role': company_user.role,
            'message': f'Szerepkör frissítve: {role}'
        })

    def delete(self, request, user_id):
        """Remove user from company"""
        try:
            company_user = CompanyUser.objects.get(
                id=user_id,
                company=request.company,
                is_active=True
            )
        except CompanyUser.DoesNotExist:
            return Response({'detail': 'Felhasználó nem található'}, status=404)

        # Don't allow users to remove themselves
        if company_user.user.id == request.user.id:
            return Response({'detail': 'Nem távolíthatja el önmagát'}, status=400)

        # Soft delete - set is_active to False
        company_user.is_active = False
        company_user.save()

        return Response({'message': 'Felhasználó eltávolítva a cégből'})
