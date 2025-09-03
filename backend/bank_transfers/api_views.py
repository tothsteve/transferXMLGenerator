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

from .models import BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, CompanyUser, Invoice, InvoiceLineItem, InvoiceSyncLog
from .serializers import (
    BankAccountSerializer, BeneficiarySerializer, TransferTemplateSerializer,
    TemplateBeneficiarySerializer, TransferSerializer, TransferBatchSerializer,
    TransferCreateFromTemplateSerializer, BulkTransferSerializer,
    ExcelImportSerializer, XMLGenerateSerializer, InvoiceListSerializer, 
    InvoiceDetailSerializer, InvoiceSyncLogSerializer
)
from .utils import generate_xml
from .pdf_processor import PDFTransactionProcessor
from .kh_export import KHBankExporter
from .permissions import IsCompanyMember, IsCompanyAdmin, IsCompanyAdminOrReadOnly, RequireBeneficiaryManagement, RequireTransferManagement, RequireBatchManagement, RequireNavSync, RequireExportFeatures, require_feature_api
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
    
    Jogosultság: BENEFICIARY_MANAGEMENT (írás) vagy BENEFICIARY_VIEW (olvasás)
    """
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBeneficiaryManagement]
    
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
        
        # For modification operations (PUT, PATCH, DELETE), always include inactive templates
        # so users can edit/delete inactive templates they can see
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            include_inactive = True
        else:
            # For list operations, check if inactive templates should be included
            show_inactive = self.request.query_params.get('show_inactive', 'false').lower() == 'true'
            include_inactive = show_inactive
        
        return TemplateService.get_company_templates(self.request.company, include_inactive=include_inactive)
    
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
    
    Jogosultság: TRANSFER_MANAGEMENT (írás) vagy TRANSFER_VIEW (olvasás)
    """
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireTransferManagement]
    
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
    @require_feature_api('EXPORT_XML_SEPA')
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
                    'content': openapi.Schema(type=openapi.TYPE_STRING, description='KH Bank .HUF.csv file tartalma'),
                    'filename': openapi.Schema(type=openapi.TYPE_STRING, description='Ajánlott fájlnév'),
                    'transfer_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_amount': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            404: 'No transfers found',
            400: 'Export error'
        }
    )
    @require_feature_api('EXPORT_CSV_KH')
    @action(detail=False, methods=['post'])
    def generate_kh_export(self, request):
        """KH Bank formátumú .HUF.csv export generálás"""
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

class TransferBatchViewSet(viewsets.ModelViewSet):
    """
    Utalási kötegek megtekintése
    
    A kötegek automatikusan létrejönnek XML generáláskor,
    és nyilvántartják a feldolgozott utalásokat.
    
    Jogosultság: BATCH_MANAGEMENT (írás) vagy BATCH_VIEW (olvasás)
    """
    serializer_class = TransferBatchSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBatchManagement]
    
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
        """Fájl letöltése - regenerálja a fájlt a mentett adatokból (XML vagy CSV formátumban)"""
        batch = self.get_object()
        
        try:
            if batch.batch_format == 'KH_CSV':
                # Generate KH Bank CSV content
                from bank_transfers.kh_export import KHBankExporter
                transfers = batch.transfers.all().select_related('beneficiary', 'originator_account').order_by('order', 'execution_date')
                exporter = KHBankExporter()
                content = exporter.generate_kh_export_encoded(transfers)
                response = HttpResponse(content, content_type='text/csv; charset=iso-8859-2')
            else:
                # Generate SEPA XML content
                content = TransferBatchService.regenerate_xml_for_batch(batch)
                response = HttpResponse(content, content_type='application/xml')
            
            response['Content-Disposition'] = f'attachment; filename="{batch.filename}"'
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
    
    @swagger_auto_schema(
        operation_description="Utalási köteg törlése (csak akkor engedélyezett, ha nincs bankban felhasználva)",
        responses={
            204: 'Batch successfully deleted',
            400: 'Batch cannot be deleted - already used in bank',
            404: 'Batch not found'
        }
    )
    def destroy(self, request, *args, **kwargs):
        """
        Utalási köteg törlése
        
        A törlés csak akkor engedélyezett, ha a köteg nincs még bankban felhasználva.
        
        Megjegyzés: A jogosultság ellenőrzést a RequireBatchManagement permission osztály végzi,
        amely biztosítja, hogy csak BATCH_MANAGEMENT jogosultsággal rendelkező felhasználók
        törölhessenek kötegeket (BATCH_VIEW jogosultság nem elég).
        """
        batch = self.get_object()
        
        # Check if batch has been used in bank
        if batch.used_in_bank:
            return Response({
                'error': 'A köteg nem törölhető, mert már fel lett használva a bankban.',
                'detail': 'Cannot delete batch that has been used in bank.',
                'used_in_bank': True,
                'bank_usage_date': batch.bank_usage_date
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Batch can be safely deleted
        batch_name = batch.name
        batch.delete()
        
        return Response({
            'detail': f'A köteg "{batch_name}" sikeresen törölve.',
            'message': f'Batch "{batch_name}" successfully deleted.'
        }, status=status.HTTP_204_NO_CONTENT)

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


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    NAV számlák megtekintése és keresése
    
    list: Az összes NAV számla listája (szűréssel és keresés)
    retrieve: Egy konkrét NAV számla részletes adatai tételekkel együtt
    
    Jogosultság: NAV_SYNC
    """
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireNavSync]
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail view"""
        if self.action == 'retrieve':
            return InvoiceDetailSerializer
        return InvoiceListSerializer
    
    def get_queryset(self):
        """Company-scoped queryset with comprehensive filtering support"""
        queryset = Invoice.objects.filter(company=self.request.company).select_related('company')
        
        # For detail view, prefetch line items
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('line_items')
        
        # Filter by direction (INBOUND/OUTBOUND)
        direction = self.request.query_params.get('direction', None)
        if direction and direction in ['INBOUND', 'OUTBOUND']:
            queryset = queryset.filter(invoice_direction=direction)
        
        # Date range filtering for issue date
        issue_date_from = self.request.query_params.get('issue_date_from', None)
        issue_date_to = self.request.query_params.get('issue_date_to', None)
        if issue_date_from:
            queryset = queryset.filter(issue_date__gte=issue_date_from)
        if issue_date_to:
            queryset = queryset.filter(issue_date__lte=issue_date_to)
        
        # Date range filtering for fulfillment date
        fulfillment_date_from = self.request.query_params.get('fulfillment_date_from', None)
        fulfillment_date_to = self.request.query_params.get('fulfillment_date_to', None)
        if fulfillment_date_from:
            queryset = queryset.filter(fulfillment_date__gte=fulfillment_date_from)
        if fulfillment_date_to:
            queryset = queryset.filter(fulfillment_date__lte=fulfillment_date_to)
        
        # Date range filtering for payment due date
        payment_due_from = self.request.query_params.get('payment_due_from', None)
        payment_due_to = self.request.query_params.get('payment_due_to', None)
        if payment_due_from:
            queryset = queryset.filter(payment_due_date__gte=payment_due_from)
        if payment_due_to:
            queryset = queryset.filter(payment_due_date__lte=payment_due_to)
        
        # Payment status filtering
        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status == 'paid':
            queryset = queryset.filter(payment_date__isnull=False)
        elif payment_status == 'unpaid':
            queryset = queryset.filter(payment_date__isnull=True)
        elif payment_status == 'overdue':
            from datetime import date
            queryset = queryset.filter(payment_date__isnull=True, payment_due_date__lt=date.today())
        
        # Amount range filtering
        amount_from = self.request.query_params.get('amount_from', None)
        amount_to = self.request.query_params.get('amount_to', None)
        if amount_from:
            queryset = queryset.filter(invoice_gross_amount__gte=amount_from)
        if amount_to:
            queryset = queryset.filter(invoice_gross_amount__lte=amount_to)
        
        # Currency filter
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency_code=currency)
        
        # Invoice operation filter (CREATE, STORNO, MODIFY)
        operation = self.request.query_params.get('operation', None)
        if operation:
            queryset = queryset.filter(invoice_operation=operation)
        
        # Payment method filter
        payment_method = self.request.query_params.get('payment_method', None)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Search by invoice number, names, tax numbers, original invoice number
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(nav_invoice_number__icontains=search) |
                models.Q(supplier_name__icontains=search) |
                models.Q(customer_name__icontains=search) |
                models.Q(supplier_tax_number__icontains=search) |
                models.Q(customer_tax_number__icontains=search) |
                models.Q(original_invoice_number__icontains=search)
            )
        
        # STORNO filtering - hide both STORNO invoices and invoices that have been storno'd
        hide_storno_invoices = self.request.query_params.get('hide_storno_invoices', 'true').lower() == 'true'
        if hide_storno_invoices:
            # Exclude STORNO invoices and invoices that have been storno'd
            # This uses the ForeignKey relationship for better performance and accuracy
            queryset = queryset.exclude(
                models.Q(invoice_operation='STORNO') |  # Exclude STORNO invoices themselves
                models.Q(storno_invoices__isnull=False)  # Exclude invoices that have been storno'd
            )
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-issue_date')
        if ordering:
            # Validate ordering fields
            allowed_fields = [
                'issue_date', 'fulfillment_date', 'payment_due_date', 'payment_date',
                'nav_invoice_number', 'invoice_gross_amount', 'invoice_net_amount',
                'supplier_name', 'customer_name', 'created_at'
            ]
            # Remove - prefix for validation
            field = ordering.lstrip('-')
            if field in allowed_fields:
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by('-issue_date')
        
        return queryset
    
    @swagger_auto_schema(
        operation_summary="NAV számlák listája",
        operation_description="Company-scoped NAV invoice list with comprehensive filtering and search",
        manual_parameters=[
            openapi.Parameter('direction', openapi.IN_QUERY, description="Filter by direction (INBOUND/OUTBOUND)", type=openapi.TYPE_STRING),
            openapi.Parameter('issue_date_from', openapi.IN_QUERY, description="Filter from issue date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('issue_date_to', openapi.IN_QUERY, description="Filter to issue date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('fulfillment_date_from', openapi.IN_QUERY, description="Filter from fulfillment date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('fulfillment_date_to', openapi.IN_QUERY, description="Filter to fulfillment date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('payment_due_from', openapi.IN_QUERY, description="Filter from payment due date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('payment_due_to', openapi.IN_QUERY, description="Filter to payment due date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('payment_status', openapi.IN_QUERY, description="Filter by payment status (paid/unpaid/overdue)", type=openapi.TYPE_STRING),
            openapi.Parameter('amount_from', openapi.IN_QUERY, description="Filter from amount", type=openapi.TYPE_NUMBER),
            openapi.Parameter('amount_to', openapi.IN_QUERY, description="Filter to amount", type=openapi.TYPE_NUMBER),
            openapi.Parameter('currency', openapi.IN_QUERY, description="Filter by currency code", type=openapi.TYPE_STRING),
            openapi.Parameter('operation', openapi.IN_QUERY, description="Filter by operation (CREATE/STORNO/MODIFY)", type=openapi.TYPE_STRING),
            openapi.Parameter('payment_method', openapi.IN_QUERY, description="Filter by payment method (TRANSFER/CASH/CARD)", type=openapi.TYPE_STRING),
            openapi.Parameter('hide_storno_invoices', openapi.IN_QUERY, description="Hide both STORNO invoices and invoices that have been canceled by STORNO (true/false, default: true)", type=openapi.TYPE_BOOLEAN, default=True),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in invoice number, names, tax numbers, original invoice", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field (prefix with - for descending)", type=openapi.TYPE_STRING),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="NAV számla részletei",
        operation_description="Get detailed information about a specific NAV invoice including line items"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get invoice statistics for the company"""
        queryset = self.get_queryset()
        
        stats = {
            'total_count': queryset.count(),
            'inbound_count': queryset.filter(invoice_direction='INBOUND').count(),
            'outbound_count': queryset.filter(invoice_direction='OUTBOUND').count(),
            'total_gross_amount': queryset.aggregate(total=models.Sum('invoice_gross_amount'))['total'] or 0,
            'currencies': list(queryset.values_list('currency_code', flat=True).distinct()),
            'recent_sync_date': queryset.aggregate(latest=models.Max('created_at'))['latest'],
        }
        
        return Response(stats)


class InvoiceSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    NAV szinkronizáció naplók megtekintése
    
    list: Az összes szinkronizáció napló listája
    retrieve: Egy konkrét szinkronizáció napló részletei
    
    Jogosultság: NAV_SYNC
    """
    serializer_class = InvoiceSyncLogSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireNavSync]
    
    def get_queryset(self):
        """Company-scoped queryset"""
        return InvoiceSyncLog.objects.filter(company=self.request.company).select_related('company')
    
    @swagger_auto_schema(
        operation_summary="NAV szinkronizáció naplók",
        operation_description="List of NAV synchronization logs for the company"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Szinkronizáció napló részletei",
        operation_description="Detailed information about a specific synchronization log"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
