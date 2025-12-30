"""
Bank Statement Import ViewSets

This module handles bank statement and transaction operations:
- Bank statement upload (PDF processing)
- Transaction listing with comprehensive filtering
- Manual invoice matching (single and batch)
- Automatic transaction rematching
- Match approval and unmatching
- Other cost categorization for expense tracking

Domain: Bank Statement Import & Transaction Matching
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

from ..models import (
    BankStatement, BankTransaction, OtherCost, Invoice,
    BankTransactionInvoiceMatch
)
from ..serializers import (
    BankStatementListSerializer, BankStatementDetailSerializer,
    BankStatementUploadSerializer, BankTransactionSerializer,
    OtherCostSerializer, SupportedBanksSerializer
)
from ..permissions import IsCompanyMember, RequireBankStatementImport
from ..filters import BankTransactionFilterSet


class BankStatementViewSet(viewsets.ModelViewSet):
    """
    Bank kivonatok kezelése - PDF feltöltés és tranzakciók listázása

    Endpoints:
    - GET /api/bank-statements/ - Kivonatok listázása
    - GET /api/bank-statements/{id}/ - Kivonat részletei tranzakciókkal
    - POST /api/bank-statements/upload/ - PDF feltöltés
    - GET /api/bank-statements/supported_banks/ - Támogatott bankok listája
    - DELETE /api/bank-statements/{id}/ - Kivonat törlése

    Permissions:
    - Requires BANK_STATEMENT_IMPORT feature to be enabled
    - ADMIN/FINANCIAL: Full access (upload, view, delete)
    - ACCOUNTANT/USER: View only
    """
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBankStatementImport]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['bank_name', 'account_number', 'statement_number', 'file_name']
    ordering_fields = ['uploaded_at', 'statement_period_from', 'statement_period_to', 'total_transactions']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        """Csak a cég kivonatai"""
        company = getattr(self.request, 'company', None)
        if not company:
            return BankStatement.objects.none()

        queryset = BankStatement.objects.filter(company=company).select_related(
            'uploaded_by'
        ).prefetch_related(
            'transactions'
        )

        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by bank code
        bank_code = self.request.query_params.get('bank_code')
        if bank_code:
            queryset = queryset.filter(bank_code=bank_code)

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(statement_period_from__gte=from_date)
        if to_date:
            queryset = queryset.filter(statement_period_to__lte=to_date)

        return queryset

    def get_serializer_class(self):
        """Use different serializers for list vs detail"""
        if self.action == 'retrieve':
            return BankStatementDetailSerializer
        elif self.action == 'upload':
            return BankStatementUploadSerializer
        return BankStatementListSerializer

    @swagger_auto_schema(
        operation_description="PDF kivonat feltöltése és automatikus feldolgozás",
        request_body=BankStatementUploadSerializer,
        responses={
            201: BankStatementDetailSerializer,
            400: "Validation error"
        }
    )
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload(self, request):
        """
        Bank statement PDF feltöltése

        Automatikusan:
        - Felismeri a bankot
        - Feldolgozza a PDF-et
        - Létrehozza a tranzakciókat
        - Ellenőrzi a duplikációt
        """
        from ..services.bank_statement_parser_service import BankStatementParserService

        company = getattr(request, 'company', None)
        if not company:
            return Response(
                {'error': 'Nincs aktív cég kiválasztva'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file
        serializer = BankStatementUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']

        # Parse and save
        try:
            parser_service = BankStatementParserService(company, request.user)
            statement = parser_service.parse_and_save(uploaded_file)

            # Return detailed response
            response_serializer = BankStatementDetailSerializer(statement)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            return Response(
                {'error': f'Feldolgozási hiba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Támogatott bankok listája",
        responses={200: SupportedBanksSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def supported_banks(self, request):
        """Támogatott bankok listája"""
        from ..services.bank_statement_parser_service import BankStatementParserService

        banks = BankStatementParserService.get_supported_banks()
        serializer = SupportedBanksSerializer(banks, many=True)
        return Response(serializer.data)


class BankTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Bank tranzakciók kezelése (csak olvasás)

    A tranzakciók automatikusan jönnek létre a kivonat feldolgozásakor.
    Csak lekérdezés és szűrés lehetséges.

    Filtering: Uses BankTransactionFilterSet for declarative filtering (~35 lines of manual logic replaced)

    Permissions:
    - Requires BANK_STATEMENT_IMPORT feature to be enabled
    - All roles (ADMIN/FINANCIAL/ACCOUNTANT/USER): View only
    """
    serializer_class = BankTransactionSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBankStatementImport]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BankTransactionFilterSet
    search_fields = ['description', 'payer_name', 'beneficiary_name', 'reference', 'payment_id']
    ordering_fields = ['booking_date', 'value_date', 'amount']
    ordering = ['-booking_date']

    def get_queryset(self):
        """
        Company-scoped queryset with prefetch optimization.

        Filtering is handled by BankTransactionFilterSet.
        """
        company = getattr(self.request, 'company', None)
        if not company:
            return BankTransaction.objects.none()

        return BankTransaction.objects.filter(company=company).select_related(
            'bank_statement',
            'matched_invoice'
        )

    def _update_statement_match_count(self, transaction):
        """
        Recalculate and update statement's matched_count after manual match operations.

        Counts ALL types of matches:
        - Single invoice matches (matched_invoice FK)
        - Batch invoice matches (BankTransactionInvoiceMatch many-to-many)
        - Transfer matches
        - Reimbursement pairs
        """
        statement = transaction.bank_statement

        # Get IDs of transactions with batch matches
        batch_matched_ids = BankTransactionInvoiceMatch.objects.filter(
            transaction__bank_statement=statement
        ).values_list('transaction_id', flat=True).distinct()

        # Count all matched transactions (including auto-categorized OtherCost)
        matched_count = BankTransaction.objects.filter(
            bank_statement=statement
        ).filter(
            models.Q(matched_invoice__isnull=False) |
            models.Q(matched_transfer__isnull=False) |
            models.Q(matched_reimbursement__isnull=False) |
            models.Q(id__in=batch_matched_ids) |
            models.Q(other_cost_detail__isnull=False)  # Include auto-categorized system transactions
        ).count()

        # Update statement
        statement.matched_count = matched_count
        statement.save(update_fields=['matched_count'])

        logger.info(
            f"Statement {statement.id} matched_count updated: {matched_count}/{statement.total_transactions}"
        )

    @action(detail=True, methods=['post'])
    def match_invoice(self, request, pk=None):
        """
        Manually match transaction to invoice.

        POST /api/bank-transactions/{id}/match_invoice/
        Body: {"invoice_id": 123}
        """
        transaction = self.get_object()
        invoice_id = request.data.get('invoice_id')

        if not invoice_id:
            return Response(
                {'error': 'invoice_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invoice = Invoice.objects.get(id=invoice_id, company=transaction.company)
        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Manual match
        transaction.matched_invoice = invoice
        transaction.match_confidence = Decimal('1.00')
        transaction.match_method = 'MANUAL'
        transaction.save()

        # Update statement counter
        self._update_statement_match_count(transaction)

        return Response({
            'message': 'Transaction matched successfully',
            'transaction_id': transaction.id,
            'invoice_id': invoice.id,
            'confidence': str(transaction.match_confidence),
            'method': transaction.match_method
        })

    @action(detail=True, methods=['post'])
    def batch_match_invoices(self, request, pk=None):
        """
        Manually match transaction to MULTIPLE invoices (batch payment).

        POST /api/bank-transactions/{id}/batch_match_invoices/
        Body: {"invoice_ids": [123, 456, 789]}

        Business case: One payment covers multiple invoices from same supplier.
        Example: 450 HUF payment for invoices: 100, 150, 200 HUF
        """
        transaction = self.get_object()
        invoice_ids = request.data.get('invoice_ids', [])

        if not invoice_ids or not isinstance(invoice_ids, list):
            return Response(
                {'error': 'invoice_ids is required and must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(invoice_ids) < 2:
            return Response(
                {'error': 'Batch matching requires at least 2 invoices'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch and validate invoices
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            company=transaction.company
        )

        if invoices.count() != len(invoice_ids):
            return Response(
                {'error': f'Some invoices not found. Expected {len(invoice_ids)}, found {invoices.count()}'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate: All invoices from same supplier
        supplier_tax_numbers = set(inv.supplier_tax_number for inv in invoices if inv.supplier_tax_number)
        if len(supplier_tax_numbers) > 1:
            return Response(
                {'error': 'All invoices must be from the same supplier (same tax number)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate total and validate amount
        total_invoice_amount = sum(inv.invoice_gross_amount for inv in invoices if inv.invoice_gross_amount)
        transaction_amount = abs(transaction.amount)
        tolerance = transaction_amount * Decimal('0.01')  # ±1% tolerance

        if abs(total_invoice_amount - transaction_amount) > tolerance:
            return Response({
                'error': 'Total invoice amount must match transaction amount (±1% tolerance)',
                'transaction_amount': str(transaction_amount),
                'total_invoice_amount': str(total_invoice_amount),
                'difference': str(abs(total_invoice_amount - transaction_amount))
            }, status=status.HTTP_400_BAD_REQUEST)

        # Clear any existing matches first
        transaction.matched_invoice = None
        BankTransactionInvoiceMatch.objects.filter(transaction=transaction).delete()

        # Create batch match
        confidence = Decimal('1.00')  # Manual match = 100% confidence
        method = 'MANUAL_BATCH'
        match_timestamp = timezone.now()

        # Save transaction metadata
        transaction.match_confidence = confidence
        transaction.match_method = method
        transaction.matched_at = match_timestamp
        transaction.matched_by = request.user
        transaction.match_notes = (
            f"Manual batch match to {len(invoices)} invoices: "
            f"{', '.join(inv.nav_invoice_number for inv in invoices)} - "
            f"Total: {total_invoice_amount} HUF"
        )
        transaction.save()

        # Create BankTransactionInvoiceMatch records
        created_matches = []
        for invoice in invoices:
            match = BankTransactionInvoiceMatch.objects.create(
                transaction=transaction,
                invoice=invoice,
                match_confidence=confidence,
                match_method=method,
                matched_by=request.user,
                match_notes=f"Part of manual batch payment ({len(invoices)} invoices)"
            )
            created_matches.append({
                'invoice_id': invoice.id,
                'invoice_number': invoice.nav_invoice_number,
                'amount': str(invoice.invoice_gross_amount)
            })

        # Update statement counter
        self._update_statement_match_count(transaction)

        return Response({
            'message': f'Transaction matched to {len(invoices)} invoices successfully',
            'transaction_id': transaction.id,
            'batch_match': True,
            'invoice_count': len(invoices),
            'matched_invoices': created_matches,
            'total_matched_amount': str(total_invoice_amount),
            'confidence': str(confidence),
            'method': method
        })

    @action(detail=True, methods=['post'])
    def unmatch(self, request, pk=None):
        """
        Remove invoice match(es) from transaction.

        Supports both single invoice matches and batch invoice matches.

        POST /api/bank-transactions/{id}/unmatch/
        """
        transaction = self.get_object()

        # Check if this is a batch match
        match_count = BankTransactionInvoiceMatch.objects.filter(transaction=transaction).count()
        was_batch = match_count > 1

        # Delete all BankTransactionInvoiceMatch records
        BankTransactionInvoiceMatch.objects.filter(transaction=transaction).delete()

        # Clear old ForeignKey field (backward compatibility)
        transaction.matched_invoice = None
        transaction.match_confidence = Decimal('0.00')
        transaction.match_method = ''
        transaction.matched_at = None
        transaction.matched_by = None
        transaction.match_notes = ''
        transaction.save()

        # Update statement counter
        self._update_statement_match_count(transaction)

        return Response({
            'message': 'Transaction unmatched successfully',
            'was_batch_match': was_batch,
            'invoices_unmatched': match_count
        })

    @action(detail=True, methods=['post'])
    def rematch(self, request, pk=None):
        """
        Re-run automatic matching for single transaction.

        POST /api/bank-transactions/{id}/rematch/
        """
        transaction = self.get_object()

        from ..services.transaction_matching_service import TransactionMatchingService

        matching_service = TransactionMatchingService(transaction.company)
        result = matching_service.match_transaction(transaction)

        return Response({
            'matched': result['matched'],
            'invoice_id': result.get('invoice_id'),
            'confidence': str(result.get('confidence')) if result.get('confidence') else None,
            'method': result.get('method'),
            'auto_paid': result.get('auto_paid', False)
        })

    @action(detail=True, methods=['post'])
    def approve_match(self, request, pk=None):
        """
        Manually approve an automatic match (upgrade confidence to 1.00).

        Use this to confirm that an automatic match is correct, even if it has
        medium or low confidence. This sets confidence to 1.00 and marks the
        match as manually approved by the current user.

        POST /api/bank-transactions/{id}/approve_match/

        Response:
        {
            "message": "Match approved successfully",
            "previous_confidence": "0.60",
            "new_confidence": "1.00",
            "matched_invoices": 1,
            "is_batch_match": false
        }
        """
        transaction = self.get_object()

        # Check if transaction has any matches
        invoice_matches = BankTransactionInvoiceMatch.objects.filter(transaction=transaction)

        if not invoice_matches.exists() and not transaction.matched_transfer and not transaction.matched_reimbursement:
            return Response(
                {'error': 'Transaction has no matches to approve'},
                status=status.HTTP_400_BAD_REQUEST
            )

        previous_confidence = str(transaction.match_confidence)

        # Update transaction metadata
        transaction.match_confidence = Decimal('1.00')
        transaction.matched_by = request.user
        transaction.matched_at = timezone.now()

        # Add approval note
        original_notes = transaction.match_notes or ''
        approval_note = f"Manually approved by {request.user.get_full_name() or request.user.username} (upgraded from {previous_confidence})"

        if original_notes:
            transaction.match_notes = f"{original_notes}\n{approval_note}"
        else:
            transaction.match_notes = approval_note

        transaction.save()

        # Update all invoice match records in through table
        invoice_count = 0
        for match in invoice_matches:
            match.match_confidence = Decimal('1.00')
            match.matched_by = request.user
            match.match_notes = f"{match.match_notes or ''}\nManually approved".strip()
            match.save()
            invoice_count += 1

        # Update statement counter
        self._update_statement_match_count(transaction)

        return Response({
            'message': 'Match approved successfully',
            'previous_confidence': previous_confidence,
            'new_confidence': '1.00',
            'matched_invoices': invoice_count,
            'is_batch_match': invoice_count > 1,
            'approved_by': request.user.get_full_name() or request.user.username,
            'approved_at': transaction.matched_at.isoformat()
        })


class OtherCostViewSet(viewsets.ModelViewSet):
    """
    Egyéb költségek kezelése

    Lehetővé teszi bank tranzakciók kategorizálását és címkézését
    költségkövetés és elemzés céljából.
    """
    serializer_class = OtherCostSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'notes']
    ordering_fields = ['date', 'amount', 'category']
    ordering = ['-date']

    def get_queryset(self):
        """Csak a cég költségei"""
        company = getattr(self.request, 'company', None)
        if not company:
            return OtherCost.objects.none()

        queryset = OtherCost.objects.filter(company=company).select_related(
            'bank_transaction',
            'created_by'
        )

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        # Filter by tags
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__contains=[tag])

        return queryset

    def perform_create(self, serializer):
        """Set company and creator"""
        company = getattr(self.request, 'company', None)
        serializer.save(company=company, created_by=self.request.user)
