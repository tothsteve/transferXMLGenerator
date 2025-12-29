"""
Transfer ViewSets - Transfer and batch management endpoints

Handles transfer templates, individual transfers, transfer batches, and Excel import functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch
from ..serializers import (
    TransferTemplateSerializer, TemplateBeneficiarySerializer, TransferSerializer,
    TransferBatchSerializer, TransferCreateFromTemplateSerializer, BulkTransferSerializer,
    ExcelImportSerializer, XMLGenerateSerializer, BeneficiarySerializer
)
from ..pdf_processor import PDFTransactionProcessor
from ..permissions import (
    IsCompanyMember, RequireTransferManagement, RequireBatchManagement, require_feature_api
)
from ..services.template_service import TemplateService
from ..services.transfer_service import TransferService, TransferBatchService
from ..services.excel_import_service import ExcelImportService


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
