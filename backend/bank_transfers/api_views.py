from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import transaction, models
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json
from datetime import date

from .models import BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, CompanyUser
from .serializers import (
    BankAccountSerializer, BeneficiarySerializer, TransferTemplateSerializer,
    TemplateBeneficiarySerializer, TransferSerializer, TransferBatchSerializer,
    TransferCreateFromTemplateSerializer, BulkTransferSerializer,
    ExcelImportSerializer, XMLGenerateSerializer
)
from .utils import generate_xml
from .pdf_processor import PDFTransactionProcessor
from .kh_export import KHBankExporter
from .permissions import IsCompanyMember, IsCompanyAdmin, IsCompanyAdminOrReadOnly
from .services.bank_account_service import BankAccountService
from .services.beneficiary_service import BeneficiaryService
from .services.template_service import TemplateService
from .services.transfer_service import TransferService, TransferBatchService
from .services.excel_import_service import ExcelImportService

# Health check endpoint for Railway
def health_check(request):
    """Simple health check endpoint for Railway deployment"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'transferXMLGenerator-backend'
    })

# DEBUG ENDPOINTS REMOVED - Clean production code

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

class BeneficiaryViewSet(viewsets.ModelViewSet):
    """
    Kedvezményezettek kezelése
    
    Támogatott szűrések:
    - is_active: true/false
    - is_frequent: true/false  
    - search: név, számlaszám és leírás alapján keresés
    """
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        if not hasattr(self.request, 'company') or not self.request.company:
            return Beneficiary.objects.none()
        
        # Build filters from query parameters
        filters = {}
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            filters['is_active'] = is_active.lower() == 'true'
            
        is_frequent = self.request.query_params.get('is_frequent', None)
        if is_frequent is not None:
            filters['is_frequent'] = is_frequent.lower() == 'true'
            
        search = self.request.query_params.get('search', None)
        if search:
            filters['search'] = search
        
        return BeneficiaryService.get_company_beneficiaries(self.request.company, filters)
    
    def perform_create(self, serializer):
        """Assign company on creation"""
        serializer.save(company=self.request.company)
    
    @swagger_auto_schema(
        operation_description="Gyakori kedvezményezettek listája",
        responses={200: BeneficiarySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def frequent(self, request):
        """Gyakori kedvezményezettek listája"""
        beneficiaries = BeneficiaryService.get_frequent_beneficiaries(request.company)
        serializer = self.get_serializer(beneficiaries, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Kedvezményezett gyakori státuszának váltása",
        responses={200: BeneficiarySerializer}
    )
    @action(detail=True, methods=['post'])
    def toggle_frequent(self, request, pk=None):
        """Gyakori státusz váltása"""
        beneficiary = self.get_object()
        beneficiary = BeneficiaryService.toggle_frequent_status(beneficiary)
        serializer = self.get_serializer(beneficiary)
        return Response(serializer.data)

class TransferTemplateViewSet(viewsets.ModelViewSet):
    """
    Utalási sablonok kezelése
    
    A sablonok lehetővé teszik gyakori utalási ciklusok (pl. hó eleji fizetések)
    gyors betöltését és ismételt használatát.
    """
    serializer_class = TransferTemplateSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        if not hasattr(self.request, 'company') or not self.request.company:
            return TransferTemplate.objects.none()
        return TemplateService.get_company_templates(self.request.company)
    
    def perform_create(self, serializer):
        """Assign company on creation"""
        serializer.save(company=self.request.company)
    
    @swagger_auto_schema(
        operation_description="Kedvezményezett hozzáadása sablonhoz",
        request_body=TemplateBeneficiarySerializer,
        responses={201: TemplateBeneficiarySerializer, 400: 'Validation error'}
    )
    @action(detail=True, methods=['post'])
    def add_beneficiary(self, request, pk=None):
        """Kedvezményezett hozzáadása sablonhoz"""
        template = self.get_object()
        serializer = TemplateBeneficiarySerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(template=template)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Kedvezményezett eltávolítása sablonból",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'beneficiary_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Kedvezményezett ID')
            }
        ),
        responses={204: 'Successfully removed', 404: 'Beneficiary not found'}
    )
    @action(detail=True, methods=['delete'])
    def remove_beneficiary(self, request, pk=None):
        """Kedvezményezett eltávolítása sablonból"""
        template = self.get_object()
        beneficiary_id = request.data.get('beneficiary_id')
        
        try:
            template_beneficiary = TemplateBeneficiary.objects.get(
                template=template, 
                beneficiary_id=beneficiary_id
            )
            template_beneficiary.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TemplateBeneficiary.DoesNotExist:
            return Response({'detail': 'Beneficiary not found in template'}, status=404)
    
    @swagger_auto_schema(
        operation_description="Sablon kedvezményezett frissítése",
        request_body=TemplateBeneficiarySerializer,
        responses={
            200: TemplateBeneficiarySerializer,
            404: 'Template beneficiary not found'
        }
    )
    @action(detail=True, methods=['put'])
    def update_beneficiary(self, request, pk=None):
        """Sablon kedvezményezett frissítése (összeg, közlemény, sorrend)"""
        template = self.get_object()
        beneficiary_id = request.data.get('beneficiary_id')
        
        try:
            template_beneficiary = TemplateBeneficiary.objects.get(
                template=template, 
                beneficiary_id=beneficiary_id
            )
            serializer = TemplateBeneficiarySerializer(template_beneficiary, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TemplateBeneficiary.DoesNotExist:
            return Response({'detail': 'Beneficiary not found in template'}, status=404)
    
    @swagger_auto_schema(
        operation_description="Sablon betöltése utalások létrehozásához",
        request_body=TransferCreateFromTemplateSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'template': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'transfers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )
        }
    )
    @action(detail=True, methods=['post'])
    def load_transfers(self, request, pk=None):
        """Sablon betöltése és utalás adatok generálása"""
        template = self.get_object()
        serializer = TransferCreateFromTemplateSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            originator_account_id = data['originator_account_id']
            execution_date = data['execution_date']
            
            transfers = TemplateService.load_template_transfers(
                template, originator_account_id, execution_date
            )
            
            return Response({
                'template': TransferTemplateSerializer(template).data,
                'transfers': transfers
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="PDF fájlokból sablon létrehozása/frissítése",
        manual_parameters=[
            openapi.Parameter('pdf_files', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='PDF fájlok (több is)'),
            openapi.Parameter('template_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Sablon neve (opcionális)'),
            openapi.Parameter('template_id', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description='Meglévő sablon ID frissítéshez (opcionális)')
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'template': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'transactions_processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'beneficiaries_matched': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'beneficiaries_created': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'consolidations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'preview': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            ),
            400: 'Hibás PDF vagy feldolgozási hiba'
        }
    )
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def process_pdf(self, request):
        """
        PDF fájlokból tranzakciók kinyerése és sablon létrehozása
        
        Támogatott formátumok:
        - NAV adó és járulék befizetési PDF-ek
        - Banki utalások / fizetési lista PDF-ek
        
        A rendszer automatikusan:
        - Felismeri a meglévő kedvezményezetteket (nem hoz létre duplikátumokat)
        - Összevonja az azonos számlára érkező átutalásokat
        - Létrehoz új sablont vagy frissíti a meglévőt
        """
        try:
            pdf_files = request.FILES.getlist('pdf_files')
            template_name = request.data.get('template_name')
            template_id = request.data.get('template_id')
            
            if not pdf_files:
                return Response({
                    'error': 'Nem található PDF fájl',
                    'details': 'Legalább egy PDF fájlt fel kell tölteni'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate PDF files
            for pdf_file in pdf_files:
                if not pdf_file.name.lower().endswith('.pdf'):
                    return Response({
                        'error': f'Hibás fájl formátum: {pdf_file.name}',
                        'details': 'Csak PDF fájlok engedélyezettek'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process PDFs with company context
            processor = PDFTransactionProcessor()
            result = processor.process_pdf_files(
                pdf_files=pdf_files,
                template_name=template_name,
                template_id=int(template_id) if template_id else None,
                company=request.company
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'error': 'PDF feldolgozási hiba',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': 'Váratlan hiba történt',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransferViewSet(viewsets.ModelViewSet):
    """
    Utalások kezelése
    
    Támogatott szűrések:
    - is_processed: true/false
    - template: sablon ID
    - execution_date_from: dátum (YYYY-MM-DD)
    - execution_date_to: dátum (YYYY-MM-DD)
    """
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        if not hasattr(self.request, 'company') or not self.request.company:
            return Transfer.objects.none()
        
        # Build filters from query parameters
        filters = {}
        
        is_processed = self.request.query_params.get('is_processed', None)
        if is_processed is not None:
            filters['is_processed'] = is_processed.lower() == 'true'
            
        template_id = self.request.query_params.get('template', None)
        if template_id:
            filters['template_id'] = template_id
            
        execution_date_from = self.request.query_params.get('execution_date_from', None)
        if execution_date_from:
            filters['execution_date_from'] = execution_date_from
            
        execution_date_to = self.request.query_params.get('execution_date_to', None)
        if execution_date_to:
            filters['execution_date_to'] = execution_date_to
        
        return TransferService.get_company_transfers(self.request.company, filters)
    
    @swagger_auto_schema(
        operation_description="Több utalás egyszerre létrehozása",
        request_body=BulkTransferSerializer,
        responses={201: 'Successfully created', 400: 'Validation error'}
    )
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Tömeges utalás létrehozás"""
        serializer = BulkTransferSerializer(data=request.data)
        
        if serializer.is_valid():
            transfers_data = serializer.validated_data['transfers']
            batch_name = serializer.validated_data.get('batch_name')
            
            # Validate all transfers first
            validated_transfers = []
            for transfer_data in transfers_data:
                transfer_serializer = TransferSerializer(data=transfer_data)
                if transfer_serializer.is_valid():
                    validated_transfers.append(transfer_serializer.validated_data)
                else:
                    return Response(transfer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Use service for bulk creation
            transfers, batch = TransferService.bulk_create_transfers(validated_transfers, batch_name)
            
            return Response({
                'transfers': TransferSerializer(transfers, many=True).data,
                'count': len(transfers)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="XML generálás kiválasztott utalásokból",
        request_body=XMLGenerateSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'xml': openapi.Schema(type=openapi.TYPE_STRING, description='Generált XML tartalom'),
                    'transfer_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_amount': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            404: 'No transfers found'
        }
    )
    @action(detail=False, methods=['post'])
    def generate_xml(self, request):
        """XML generálás kiválasztott utalásokból"""
        serializer = XMLGenerateSerializer(data=request.data)
        
        if serializer.is_valid():
            transfer_ids = serializer.validated_data['transfer_ids']
            batch_name = serializer.validated_data.get('batch_name')
            
            try:
                result = TransferService.generate_xml_from_transfers(transfer_ids, batch_name)
                return Response(result)
            except ValueError as e:
                return Response({'detail': str(e)}, status=404)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="KH Bank formátumú szöveges export generálás",
        request_body=XMLGenerateSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'content': openapi.Schema(type=openapi.TYPE_STRING, description='KH Bank .HUF.CSV file tartalma'),
                    'filename': openapi.Schema(type=openapi.TYPE_STRING, description='Ajánlott fájlnév'),
                    'transfer_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_amount': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            404: 'No transfers found',
            400: 'Export error'
        }
    )
    @action(detail=False, methods=['post'])
    def generate_kh_export(self, request):
        """KH Bank formátumú .HUF.CSV export generálás"""
        serializer = XMLGenerateSerializer(data=request.data)
        
        if serializer.is_valid():
            transfer_ids = serializer.validated_data['transfer_ids']
            batch_name = serializer.validated_data.get('batch_name')
            
            try:
                result = TransferService.generate_kh_export_from_transfers(transfer_ids, batch_name)
                return Response(result)
            except ValueError as e:
                return Response({
                    'detail': 'KH Bank export error',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransferBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Utalási kötegek megtekintése
    
    A kötegek automatikusan létrejönnek XML generáláskor,
    és nyilvántartják a feldolgozott utalásokat.
    """
    serializer_class = TransferBatchSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        if not hasattr(self.request, 'company') or not self.request.company:
            return TransferBatch.objects.none()
        return TransferBatchService.get_company_batches(self.request.company)
    
    @swagger_auto_schema(
        operation_description="XML fájl letöltése köteghez",
        responses={200: 'XML file', 404: 'No transfers in batch'}
    )
    @action(detail=True, methods=['get'])
    def download_xml(self, request, pk=None):
        """XML fájl letöltése - regenerálja az XML-t a mentett adatokból"""
        batch = self.get_object()
        
        try:
            xml_content = TransferBatchService.regenerate_xml_for_batch(batch)
            response = HttpResponse(xml_content, content_type='application/xml')
            response['Content-Disposition'] = f'attachment; filename="{batch.xml_filename}"'
            return response
        except ValueError as e:
            return Response({'detail': str(e)}, status=404)
    
    @swagger_auto_schema(
        operation_description="XML köteg megjelölése bankban felhasználtként",
        responses={200: 'Batch marked as used', 404: 'Batch not found'}
    )
    @action(detail=True, methods=['post'])
    def mark_used_in_bank(self, request, pk=None):
        """XML köteg megjelölése bankban felhasználtként"""
        batch = self.get_object()
        batch = TransferBatchService.mark_batch_as_used(batch)
        
        return Response({
            'detail': 'Batch marked as used in bank',
            'used_in_bank': batch.used_in_bank,
            'bank_usage_date': batch.bank_usage_date
        })
    
    @swagger_auto_schema(
        operation_description="XML köteg megjelölése nem felhasználtként",
        responses={200: 'Batch marked as unused', 404: 'Batch not found'}
    )
    @action(detail=True, methods=['post'])
    def mark_unused_in_bank(self, request, pk=None):
        """XML köteg megjelölése nem felhasználtként"""
        batch = self.get_object()
        batch = TransferBatchService.mark_batch_as_unused(batch)
        
        return Response({
            'detail': 'Batch marked as unused in bank',
            'used_in_bank': batch.used_in_bank,
            'bank_usage_date': batch.bank_usage_date
        })

class ExcelImportView(APIView):
    """
    Excel fájl import kedvezményezettek tömeges feltöltéséhez
    
    Támogatott formátum:
    - 3. sortól kezdődnek az adatok
    - Oszlopok: Megjegyzés, Név, Számlaszám, Összeg, Dátum, Közlemény
    - Csak a Név és Számlaszám kötelező
    """
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    @swagger_auto_schema(
        operation_description="Excel fájl feltöltése kedvezményezettek importálásához",
        request_body=ExcelImportSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'beneficiaries': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            ),
            400: 'Import error'
        }
    )
    def post(self, request):
        serializer = ExcelImportSerializer(data=request.data)
        
        if serializer.is_valid():
            excel_file = serializer.validated_data['file']
            import_type = serializer.validated_data['import_type']
            
            try:
                if import_type == 'beneficiaries':
                    result = ExcelImportService.import_beneficiaries_from_excel(
                        excel_file, request.company
                    )
                    
                    return Response({
                        'imported_count': result['imported_count'],
                        'errors': result['errors'],
                        'beneficiaries': BeneficiarySerializer(result['beneficiaries'], many=True).data
                    })
                else:
                    return Response({'detail': 'Invalid import type'}, status=400)
                    
            except Exception as e:
                return Response({'detail': str(e)}, status=400)
        
        return Response(serializer.errors, status=400)

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
