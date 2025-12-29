"""
Bank Account ViewSet - Bank account management endpoints

Handles CRUD operations for company bank accounts (originator accounts for transfers).
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from ..models import BankAccount
from ..serializers import BankAccountSerializer
from ..permissions import IsCompanyMember
from ..services.bank_account_service import BankAccountService


class BankAccountViewSet(viewsets.ModelViewSet):
    """
    Bank számlák kezelése
    
    list: Az összes bank számla listája
    create: Új bank számla létrehozása
    retrieve: Egy konkrét bank számla adatai
    update: Bank számla módosítása
    destroy: Bank számla törlése
    """
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        """Company-scoped queryset"""
        if hasattr(self.request, 'company') and self.request.company:
            return BankAccountService.get_company_accounts(self.request.company)
        return BankAccount.objects.none()
    
    def perform_create(self, serializer):
        """Assign company on creation"""
        serializer.save(company=self.request.company)
    
    @swagger_auto_schema(
        operation_description="Alapértelmezett bank számla lekérése",
        responses={200: BankAccountSerializer, 404: 'Nincs alapértelmezett számla'}
    )
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Alapértelmezett bank számla lekérése"""
        account = BankAccountService.get_default_account(request.company)
        if account:
            serializer = self.get_serializer(account)
            return Response(serializer.data)
        return Response({'detail': 'No default account found'}, status=404)
