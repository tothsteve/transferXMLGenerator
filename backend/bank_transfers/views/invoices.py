"""
NAV Invoice Management ViewSets

This module handles NAV (National Tax and Customs Administration) invoice operations:
- Invoice listing with comprehensive filtering and search
- Invoice detail retrieval with line items
- Payment status management (bulk operations)
- Invoice-to-transfer generation with tax number fallback
- Invoice statistics and sync logs

Domain: NAV Integration
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import models
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import date
from decimal import Decimal

from ..models import Invoice, InvoiceSyncLog, BankAccount, Beneficiary, Transfer
from ..serializers import (
    InvoiceListSerializer, InvoiceDetailSerializer, InvoiceSyncLogSerializer,
    TransferSerializer
)
from ..permissions import IsCompanyMember, RequireNavSync


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
        """Override list to handle empty search results gracefully (return empty list instead of 404)"""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            # If pagination raises 404 for invalid page on empty queryset, return empty results
            if 'EmptyPage' in str(type(e).__name__) or 'NotFound' in str(type(e).__name__):
                queryset = self.filter_queryset(self.get_queryset())
                # If queryset is empty, return empty paginated response
                if not queryset.exists():
                    return Response({
                        'count': 0,
                        'next': None,
                        'previous': None,
                        'results': []
                    })
            raise

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
        from ..services.beneficiary_service import BeneficiaryService
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
                # Determine execution date - use payment_due_date if available, otherwise use provided date
                if invoice.payment_due_date:
                    execution_date = invoice.payment_due_date
                else:
                    execution_date = datetime.strptime(execution_date_str, '%Y-%m-%d').date()

                # If execution date is in the past, set it to today
                today = date.today()
                if execution_date < today:
                    execution_date = today
                    warnings.append(f'Számla {invoice.nav_invoice_number}: Lejárati dátum múltbeli volt ({invoice.payment_due_date if invoice.payment_due_date else execution_date_str}), mai dátumra állítva')

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
                from ..services.transfer_service import TransferService
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
