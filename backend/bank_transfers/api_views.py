from rest_framework import viewsets, status, filters
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

from .models import BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, CompanyUser, Invoice, InvoiceLineItem, InvoiceSyncLog, TrustedPartner, ExchangeRate, ExchangeRateSyncLog
from .serializers import (
    BankAccountSerializer, BeneficiarySerializer, TransferTemplateSerializer,
    TemplateBeneficiarySerializer, TransferSerializer, TransferBatchSerializer,
    TransferCreateFromTemplateSerializer, BulkTransferSerializer,
    ExcelImportSerializer, XMLGenerateSerializer, InvoiceListSerializer,
    InvoiceDetailSerializer, InvoiceSyncLogSerializer, TrustedPartnerSerializer,
    ExchangeRateSerializer, ExchangeRateSyncLogSerializer, CurrencyConversionSerializer
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
from .services.exchange_rate_sync_service import ExchangeRateSyncService

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
    - search: név, számlaszám, adószám és leírás alapján keresés
    - vat_number: adószám alapján szűrés
    - has_vat_number: true/false - adószámmal rendelkező beneficiaries
    - has_account_number: true/false - számlaszámmal rendelkező beneficiaries
    
    Jogosultság: BENEFICIARY_MANAGEMENT (írás) vagy BENEFICIARY_VIEW (olvasás)
    """
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBeneficiaryManagement]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'account_number', 'vat_number', 'description', 'remittance_information', 'is_active', 'is_frequent', 'created_at']
    ordering = ['name']  # Default ordering
    
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
        
        # VAT number specific filters
        vat_number = self.request.query_params.get('vat_number', None)
        if vat_number:
            filters['vat_number'] = vat_number
            
        has_vat_number = self.request.query_params.get('has_vat_number', None)
        if has_vat_number is not None:
            filters['has_vat_number'] = has_vat_number.lower() == 'true'
            
        has_account_number = self.request.query_params.get('has_account_number', None)
        if has_account_number is not None:
            filters['has_account_number'] = has_account_number.lower() == 'true'
        
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
    
    @swagger_auto_schema(
        operation_description="Adószámmal rendelkező, de számlaszám nélküli kedvezményezettek",
        responses={200: BeneficiarySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def vat_only(self, request):
        """Adószámmal rendelkező, de számlaszám nélküli kedvezményezettek listája"""
        filters = {
            'has_vat_number': True,
            'has_account_number': False,
            'is_active': True
        }
        beneficiaries = BeneficiaryService.get_company_beneficiaries(request.company, filters)
        serializer = self.get_serializer(beneficiaries, many=True)
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
                transfers = batch.transfers.all().select_related('beneficiary', 'originator_account').order_by('order', 'execution_date')
                content = TransferBatchService.regenerate_xml_for_batch(batch)
                response = HttpResponse(content, content_type='application/xml')

            # Mark transfers as processed when downloaded
            batch.transfers.filter(is_processed=False).update(is_processed=True)

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

        # For detail view (retrieve by ID), only prefetch line items - NO FILTERING
        if self.action == 'retrieve':
            return queryset.prefetch_related('line_items')

        # All filters below only apply to LIST view

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
        payment_due_from = self.request.query_params.get('payment_due_date_from', None)
        payment_due_to = self.request.query_params.get('payment_due_date_to', None)
        if payment_due_from:
            queryset = queryset.filter(payment_due_date__gte=payment_due_from)
        if payment_due_to:
            queryset = queryset.filter(payment_due_date__lte=payment_due_to)
        
        # Payment status filtering
        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status:
            if payment_status.upper() == 'PAID':
                queryset = queryset.filter(payment_status='PAID')
            elif payment_status.upper() == 'UNPAID':
                queryset = queryset.filter(payment_status='UNPAID')
            elif payment_status.upper() == 'PREPARED':
                queryset = queryset.filter(payment_status='PREPARED')
            # Legacy support for old format
            elif payment_status == 'paid':
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
        
        # STORNO filtering - hide both STORNO/MODIFY invoices and invoices that have been storno'd
        hide_storno_invoices = self.request.query_params.get('hide_storno_invoices', 'true').lower() == 'true'
        if hide_storno_invoices:
            # Exclude STORNO and MODIFY invoices and invoices that have been storno'd
            # This uses the ForeignKey relationship for better performance and accuracy
            queryset = queryset.exclude(
                models.Q(invoice_operation__in=['STORNO', 'MODIFY']) |  # Exclude STORNO and MODIFY invoices themselves
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
    
    @swagger_auto_schema(
        operation_summary="Számlák tömeges megjelölése fizetésre várként",
        operation_description="Mark multiple invoices as unpaid (Fizetésre vár)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'invoice_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="List of invoice IDs to mark as unpaid"
                )
            },
            required=['invoice_ids']
        )
    )
    @action(detail=False, methods=['post'])
    def bulk_mark_unpaid(self, request):
        """Mark multiple invoices as unpaid"""
        invoice_ids = request.data.get('invoice_ids', [])
        
        if not invoice_ids:
            return Response({'error': 'invoice_ids kötelező'}, status=400)
        
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            company=request.company
        )
        
        updated_count = 0
        for invoice in invoices:
            if invoice.payment_status != 'UNPAID':
                invoice.payment_status = 'UNPAID'
                invoice.payment_status_date = timezone.now().date()
                invoice.auto_marked_paid = False
                invoice.save()
                updated_count += 1
        
        return Response({
            'message': f'{updated_count} számla megjelölve fizetésre várként',
            'updated_count': updated_count
        })
    
    @swagger_auto_schema(
        operation_summary="Számlák tömeges megjelölése előkészítettként", 
        operation_description="Mark multiple invoices as prepared (Előkészítve)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'invoice_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="List of invoice IDs to mark as prepared"
                )
            },
            required=['invoice_ids']
        )
    )
    @action(detail=False, methods=['post'])
    def bulk_mark_prepared(self, request):
        """Mark multiple invoices as prepared"""
        invoice_ids = request.data.get('invoice_ids', [])
        
        if not invoice_ids:
            return Response({'error': 'invoice_ids kötelező'}, status=400)
        
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            company=request.company
        )
        
        updated_count = 0
        for invoice in invoices:
            if invoice.payment_status != 'PREPARED':
                invoice.mark_as_prepared()
                updated_count += 1
        
        return Response({
            'message': f'{updated_count} számla megjelölve előkészítettként',
            'updated_count': updated_count
        })
    
    @swagger_auto_schema(
        operation_summary="Számlák tömeges megjelölése kifizetettként",
        operation_description="Mark multiple invoices as paid (Kifizetve). Supports both single date for all invoices and individual dates per invoice.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'invoice_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="List of invoice IDs to mark as paid (used when payment_date is provided)"
                ),
                'payment_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Single payment date (YYYY-MM-DD) for all invoices, defaults to today"
                ),
                'invoices': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'invoice_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Invoice ID"),
                            'payment_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Payment date for this invoice (YYYY-MM-DD)")
                        },
                        required=['invoice_id', 'payment_date']
                    ),
                    description="List of invoices with individual payment dates"
                )
            },
            required=[]
        )
    )
    @action(detail=False, methods=['post'])
    def bulk_mark_paid(self, request):
        """Mark multiple invoices as paid with flexible date options"""
        invoice_ids = request.data.get('invoice_ids', [])
        payment_date_str = request.data.get('payment_date')
        invoices_with_dates = request.data.get('invoices', [])
        
        # Validate input - must provide either invoice_ids or invoices
        if not invoice_ids and not invoices_with_dates:
            return Response({'error': 'invoice_ids vagy invoices kötelező'}, status=400)
        
        updated_count = 0
        errors = []
        
        try:
            # Option 1: Single date for multiple invoices
            if invoice_ids:
                # Parse single payment date
                payment_date = None
                if payment_date_str:
                    try:
                        from datetime import datetime
                        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return Response({'error': 'Érvénytelen dátum formátum. Használj YYYY-MM-DD formátumot.'}, status=400)
                
                invoices = Invoice.objects.filter(
                    id__in=invoice_ids,
                    company=request.company
                )
                
                for invoice in invoices:
                    if invoice.payment_status != 'PAID':
                        invoice.mark_as_paid(payment_date=payment_date, auto_marked=False)
                        updated_count += 1
            
            # Option 2: Individual dates for each invoice
            if invoices_with_dates:
                from datetime import datetime
                
                for item in invoices_with_dates:
                    invoice_id = item.get('invoice_id')
                    item_payment_date_str = item.get('payment_date')
                    
                    if not invoice_id or not item_payment_date_str:
                        errors.append(f'Invoice ID és payment_date kötelező minden elemhez')
                        continue
                    
                    # Parse individual payment date
                    try:
                        item_payment_date = datetime.strptime(item_payment_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f'Érvénytelen dátum formátum invoice {invoice_id}-hez: {item_payment_date_str}')
                        continue
                    
                    # Find and update invoice
                    try:
                        invoice = Invoice.objects.get(id=invoice_id, company=request.company)
                        if invoice.payment_status != 'PAID':
                            invoice.mark_as_paid(payment_date=item_payment_date, auto_marked=False)
                            updated_count += 1
                    except Invoice.DoesNotExist:
                        errors.append(f'Számla nem található: {invoice_id}')
                        continue
        
        except Exception as e:
            return Response({'error': f'Hiba történt: {str(e)}'}, status=500)
        
        response_data = {
            'message': f'{updated_count} számla megjelölve kifizetettként',
            'updated_count': updated_count
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data)

    @swagger_auto_schema(
        operation_summary="Eseti átutalások generálása NAV számlákból",
        operation_description="Generate ad-hoc transfers from NAV invoices with tax number fallback for missing bank accounts",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'invoice_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="List of invoice IDs to generate transfers from"
                ),
                'originator_account_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the originator bank account"
                ),
                'execution_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Execution date for the transfers (YYYY-MM-DD)"
                )
            },
            required=['invoice_ids', 'originator_account_id', 'execution_date']
        )
    )
    @action(detail=False, methods=['post'])
    def generate_transfers(self, request):
        """Generate transfers from NAV invoices with tax number fallback logic"""
        from .services.beneficiary_service import BeneficiaryService
        from decimal import Decimal
        from datetime import datetime

        invoice_ids = request.data.get('invoice_ids', [])
        originator_account_id = request.data.get('originator_account_id')
        execution_date_str = request.data.get('execution_date')

        if not invoice_ids:
            return Response({'error': 'invoice_ids kötelező'}, status=400)

        if not originator_account_id:
            return Response({'error': 'originator_account_id kötelező'}, status=400)

        if not execution_date_str:
            return Response({'error': 'execution_date kötelező'}, status=400)

        # Parse execution date
        try:
            execution_date = datetime.strptime(execution_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Érvénytelen dátum formátum. Használj YYYY-MM-DD formátumot.'}, status=400)

        # Validate originator account
        try:
            originator_account = BankAccount.objects.get(
                id=originator_account_id,
                company=request.company
            )
        except BankAccount.DoesNotExist:
            return Response({'error': 'Originátor számla nem található'}, status=400)

        # Get invoices
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            company=request.company
        )

        if not invoices.exists():
            return Response({'error': 'Nem található számla'}, status=400)

        generated_transfers = []
        errors = []
        warnings = []

        for invoice in invoices:
            try:
                # Extract supplier tax number (normalize to 8 digits)
                supplier_tax_number = invoice.supplier_tax_number
                if not supplier_tax_number:
                    errors.append(f'Számla {invoice.nav_invoice_number}: Hiányzó beszállító adószám')
                    continue

                # Normalize tax number to 8 digits for matching
                normalized_tax_number = ''.join(filter(str.isdigit, supplier_tax_number))
                base_tax_number = normalized_tax_number[:8] if len(normalized_tax_number) >= 8 else normalized_tax_number

                if len(base_tax_number) != 8:
                    errors.append(f'Számla {invoice.nav_invoice_number}: Érvénytelen adószám formátum: {supplier_tax_number}')
                    continue

                # Only process INBOUND invoices (where we pay suppliers)
                if invoice.invoice_direction != 'INBOUND':
                    errors.append(f'Számla {invoice.nav_invoice_number}: Csak bejövő számlákhoz lehet átutalást generálni')
                    continue

                # Check if invoice has supplier bank account number
                account_number = None
                beneficiary_name = invoice.supplier_name

                if invoice.supplier_bank_account_number:
                    # Use supplier bank account from invoice
                    account_number = invoice.supplier_bank_account_number
                    warnings.append(f'Számla {invoice.nav_invoice_number}: Számla szállító számlaszámát használja')
                else:
                    # Look for beneficiary with matching tax number
                    beneficiary = BeneficiaryService.find_beneficiary_by_tax_number(
                        request.company,
                        base_tax_number
                    )

                    if beneficiary:
                        account_number = beneficiary.account_number
                        beneficiary_name = beneficiary.name
                        warnings.append(f'Számla {invoice.nav_invoice_number}: Kedvezményezett találat adószám alapján: {beneficiary.name}')
                    else:
                        errors.append(f'Számla {invoice.nav_invoice_number}: Nincs számlaszám és nem található kedvezményezett a {base_tax_number} adószámmal')
                        continue

                if not account_number:
                    errors.append(f'Számla {invoice.nav_invoice_number}: Nincs elérhető számlaszám')
                    continue

                # Find or create beneficiary
                beneficiary = None
                if invoice.supplier_bank_account_number:
                    # For invoices with supplier bank accounts, try to find or create a beneficiary
                    beneficiary, created = Beneficiary.objects.get_or_create(
                        company=request.company,
                        account_number=account_number,
                        defaults={
                            'name': beneficiary_name,
                            'description': f'Auto-created from invoice {invoice.nav_invoice_number}',
                            'remittance_information': '',
                            'is_frequent': False,
                            'is_active': True,
                            'tax_number': base_tax_number  # Add the tax number for future matching
                        }
                    )
                    if created:
                        warnings.append(f'Számla {invoice.nav_invoice_number}: Új kedvezményezett létrehozva: {beneficiary_name}')
                else:
                    # Use the found beneficiary from tax number matching
                    beneficiary = BeneficiaryService.find_beneficiary_by_tax_number(
                        request.company,
                        base_tax_number
                    )

                if not beneficiary:
                    errors.append(f'Számla {invoice.nav_invoice_number}: Nem található kedvezményezett')
                    continue

                # Create transfer data for bulk creation
                # Round HUF amounts to whole numbers (no decimals for HUF)
                amount = Decimal(str(invoice.invoice_gross_amount))
                currency = invoice.currency_code or 'HUF'
                if currency == 'HUF':
                    amount = amount.quantize(Decimal('1'))  # Round to whole number

                transfer_data = {
                    'originator_account': originator_account,
                    'beneficiary': beneficiary,
                    'amount': amount,
                    'currency': currency,
                    'execution_date': execution_date,
                    'remittance_info': invoice.nav_invoice_number,
                    'nav_invoice': invoice,
                    'order': len(generated_transfers) + 1,
                    'is_processed': False
                }

                generated_transfers.append(transfer_data)

            except Exception as e:
                errors.append(f'Számla {invoice.nav_invoice_number}: Hiba - {str(e)}')
                continue

        # Create the transfers if any were generated
        created_transfers = []
        if generated_transfers:
            try:
                from .services.transfer_service import TransferService
                transfers, batch = TransferService.bulk_create_transfers(generated_transfers)
                created_transfers = TransferSerializer(transfers, many=True).data
            except Exception as e:
                errors.append(f'Hiba a transzferek létrehozásakor: {str(e)}')

        return Response({
            'transfers': created_transfers,
            'transfer_count': len(created_transfers),
            'errors': errors,
            'warnings': warnings,
            'message': f'{len(created_transfers)} átutalás létrehozva, {len(errors)} hiba történt'
        })


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


class TrustedPartnerViewSet(viewsets.ModelViewSet):
    """
    Megbízható partnerek kezelése automatikus fizetés feldolgozáshoz
    
    list: Az összes megbízható partner listája
    create: Új megbízható partner hozzáadása
    retrieve: Egy konkrét partner részletei
    update: Partner módosítása
    destroy: Partner törlése
    available_partners: Elérhető partnerek NAV számlákból
    
    Jogosultság: Authentikált felhasználó
    """
    serializer_class = TrustedPartnerSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filterset_fields = ['is_active', 'auto_pay']
    search_fields = ['partner_name', 'tax_number']
    ordering_fields = ['partner_name', 'tax_number', 'invoice_count', 'last_invoice_date', 'created_at']
    ordering = ['partner_name']
    
    def get_queryset(self):
        """Company-scoped queryset"""
        return TrustedPartner.objects.filter(company=self.request.company)
    
    def perform_create(self, serializer):
        """Auto-set company and update statistics"""
        partner = serializer.save(company=self.request.company)
        partner.update_statistics()
    
    def perform_update(self, serializer):
        """Update statistics after modification"""
        partner = serializer.save()
        partner.update_statistics()
    
    @swagger_auto_schema(
        operation_summary="Megbízható partnerek listája",
        operation_description="List of trusted partners for automatic payment processing"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Új megbízható partner",
        operation_description="Create a new trusted partner"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Partner részletei",
        operation_description="Get detailed information about a specific trusted partner"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Partner módosítása",
        operation_description="Update a trusted partner's information"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Partner törlése",
        operation_description="Delete a trusted partner"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def available_partners(self, request):
        """
        Get available partners from NAV invoices that can be added as trusted partners.
        Supports search and ordering parameters.
        """
        from django.db.models import Count, Max, Q
        from django.core.paginator import Paginator
        
        # Get distinct suppliers from invoices that are not already trusted partners
        existing_tax_numbers = set(
            TrustedPartner.objects.filter(company=request.company)
            .values_list('tax_number', flat=True)
        )
        
        # Build base query
        query = Invoice.objects.filter(
            company=request.company,
            supplier_tax_number__isnull=False,
            supplier_name__isnull=False
        ).exclude(
            supplier_tax_number__in=existing_tax_numbers
        )
        
        # Apply search filter (case-insensitive)
        search = request.query_params.get('search', '').strip()
        if search:
            query = query.filter(
                Q(supplier_name__icontains=search) | 
                Q(supplier_tax_number__icontains=search)
            )
        
        # Group by supplier and annotate with statistics
        available = query.values(
            'supplier_name', 'supplier_tax_number'
        ).annotate(
            invoice_count=Count('id'),
            last_invoice_date=Max('issue_date')
        )
        
        # Apply ordering (default: last_invoice_date descending)
        ordering = request.query_params.get('ordering', '-last_invoice_date')
        
        # Map ordering fields for the annotated query
        ordering_map = {
            'partner_name': 'supplier_name',
            '-partner_name': '-supplier_name',
            'tax_number': 'supplier_tax_number',
            '-tax_number': '-supplier_tax_number',
            'invoice_count': 'invoice_count',
            '-invoice_count': '-invoice_count',
            'last_invoice_date': 'last_invoice_date',
            '-last_invoice_date': '-last_invoice_date',
        }
        
        if ordering in ordering_map:
            available = available.order_by(ordering_map[ordering])
        else:
            # Default ordering: most recent invoices first
            available = available.order_by('-last_invoice_date')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Convert to list to enable pagination
        available_list = list(available)
        
        # Create paginator
        paginator = Paginator(available_list, page_size)
        page_obj = paginator.get_page(page)
        
        # Format the response
        partners_data = []
        for item in page_obj.object_list:
            partners_data.append({
                'partner_name': item['supplier_name'],
                'tax_number': item['supplier_tax_number'],
                'invoice_count': item['invoice_count'],
                'last_invoice_date': item['last_invoice_date'].strftime('%Y-%m-%d') if item['last_invoice_date'] else None,
            })
        
        return Response({
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'results': partners_data
        })


class ExchangeRateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MNB (Magyar Nemzeti Bank) árfolyamok kezelése

    Támogatott funkciók:
    - Árfolyamok listázása szűréssel (currency, date_from, date_to)
    - Aktuális árfolyamok lekérdezése
    - Deviza váltás számítás
    - Árfolyam szinkronizáció MNB API-ról
    - Szinkronizációs előzmények

    Jogosultság: Minden bejelentkezett felhasználó olvashat,
                 de csak ADMIN végezhet szinkronizációt
    """
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['rate_date', 'currency', 'rate']
    ordering = ['-rate_date', 'currency']  # Default: newest first

    def get_queryset(self):
        """
        Szűrési lehetőségek:
        - currency: USD vagy EUR
        - date_from: kezdő dátum (YYYY-MM-DD)
        - date_to: befejező dátum (YYYY-MM-DD)
        """
        queryset = ExchangeRate.objects.all()

        # Currency filter
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency=currency.upper())

        # Date range filters
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(rate_date__gte=date_from)

        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(rate_date__lte=date_to)

        return queryset

    @swagger_auto_schema(
        operation_description="Aktuális (mai) árfolyamok lekérdezése USD és EUR valutákra",
        responses={
            200: openapi.Response(
                description="Aktuális árfolyamok",
                examples={
                    'application/json': {
                        'USD': {'rate': '385.5000', 'rate_date': '2025-10-01'},
                        'EUR': {'rate': '410.2500', 'rate_date': '2025-10-01'}
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Aktuális (mai) árfolyamok lekérdezése"""
        today = date.today()
        currencies = ['USD', 'EUR']

        rates_data = {}
        for currency in currencies:
            rate = ExchangeRateSyncService.get_rate_for_date(today, currency)
            if rate:
                rate_obj = ExchangeRate.objects.filter(
                    rate_date=today,
                    currency=currency
                ).first()

                if rate_obj:
                    rates_data[currency] = {
                        'rate': str(rate),
                        'rate_date': rate_obj.rate_date.strftime('%Y-%m-%d')
                    }

        return Response(rates_data)

    @swagger_auto_schema(
        operation_description="Legutóbbi elérhető árfolyamok lekérdezése (ha ma nincs, akkor a legközelebbi korábbi)",
        responses={
            200: openapi.Response(
                description="Legutóbbi árfolyamok",
                examples={
                    'application/json': {
                        'USD': {'rate': '385.5000', 'rate_date': '2025-10-01'},
                        'EUR': {'rate': '410.2500', 'rate_date': '2025-10-01'}
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Legutóbbi elérhető árfolyamok lekérdezése"""
        latest_rates = ExchangeRateSyncService.get_latest_rates(['USD', 'EUR'])

        rates_data = {}
        for currency, (rate, rate_date) in latest_rates.items():
            rates_data[currency] = {
                'rate': str(rate),
                'rate_date': rate_date.strftime('%Y-%m-%d')
            }

        return Response(rates_data)

    @swagger_auto_schema(
        operation_description="Deviza átváltás HUF-ra",
        request_body=CurrencyConversionSerializer,
        responses={
            200: openapi.Response(
                description="Átváltás eredménye",
                examples={
                    'application/json': {
                        'amount': '100.00',
                        'currency': 'USD',
                        'conversion_date': '2025-10-01',
                        'rate': '385.5000',
                        'huf_amount': '38550.00'
                    }
                }
            ),
            400: 'Hiányzó vagy érvénytelen paraméterek',
            404: 'Árfolyam nem található a megadott dátumra'
        }
    )
    @action(detail=False, methods=['post'])
    def convert(self, request):
        """Deviza átváltás HUF-ra adott árfolyamon"""
        serializer = CurrencyConversionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']
        currency = serializer.validated_data['currency']
        conversion_date = serializer.validated_data.get('conversion_date') or date.today()

        # Get exchange rate
        rate = ExchangeRateSyncService.get_rate_for_date(conversion_date, currency)

        if not rate:
            return Response(
                {'error': f'Nincs elérhető {currency} árfolyam {conversion_date} dátumra'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Convert to HUF
        huf_amount = ExchangeRateSyncService.convert_to_huf(amount, currency, conversion_date)

        return Response({
            'amount': str(amount),
            'currency': currency,
            'conversion_date': conversion_date.strftime('%Y-%m-%d'),
            'rate': str(rate),
            'huf_amount': str(huf_amount)
        })

    @swagger_auto_schema(
        operation_description="MNB árfolyamok szinkronizálása (mai napra) - Csak ADMIN",
        responses={
            200: ExchangeRateSyncLogSerializer,
            403: 'Nincs jogosultság',
            500: 'Szinkronizációs hiba'
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsCompanyAdmin])
    def sync_current(self, request):
        """Aktuális árfolyamok szinkronizálása MNB-ről (mai napra)"""
        try:
            service = ExchangeRateSyncService()
            sync_log = service.sync_current_rates()

            serializer = ExchangeRateSyncLogSerializer(sync_log)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': f'Szinkronizációs hiba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Történeti árfolyamok szinkronizálása - Csak ADMIN",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'days_back': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Hány napra visszamenőleg (pl. 730 = 2 év)',
                    default=30
                ),
                'currencies': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='Devizák listája (alapértelmezett: USD, EUR)',
                    default=['USD', 'EUR']
                )
            }
        ),
        responses={
            200: ExchangeRateSyncLogSerializer,
            403: 'Nincs jogosultság',
            500: 'Szinkronizációs hiba'
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsCompanyAdmin])
    def sync_historical(self, request):
        """Történeti árfolyamok szinkronizálása (pl. 2 év = 730 nap)"""
        days_back = request.data.get('days_back', 30)
        currencies = request.data.get('currencies', None)

        try:
            service = ExchangeRateSyncService()
            sync_log = service.sync_historical_rates(
                days_back=days_back,
                currencies=currencies
            )

            serializer = ExchangeRateSyncLogSerializer(sync_log)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': f'Szinkronizációs hiba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Szinkronizációs előzmények lekérdezése",
        responses={200: ExchangeRateSyncLogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def sync_history(self, request):
        """Szinkronizációs előzmények listája"""
        sync_logs = ExchangeRateSyncLog.objects.all().order_by('-sync_start_time')[:20]
        serializer = ExchangeRateSyncLogSerializer(sync_logs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Árfolyam történet lekérdezése (grafikonhoz)",
        manual_parameters=[
            openapi.Parameter('currency', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Deviza kód (USD vagy EUR)', required=True),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Napok száma visszamenőleg', default=30)
        ],
        responses={
            200: openapi.Response(
                description="Árfolyam történet",
                examples={
                    'application/json': [
                        {'date': '2025-09-01', 'rate': 385.5},
                        {'date': '2025-09-02', 'rate': 386.1}
                    ]
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Árfolyam történet lekérdezése (grafikonhoz, elemzéshez)"""
        currency = request.query_params.get('currency', 'USD').upper()
        days = int(request.query_params.get('days', 30))

        history_data = ExchangeRateSyncService.get_rate_history(currency, days)
        return Response(history_data)
