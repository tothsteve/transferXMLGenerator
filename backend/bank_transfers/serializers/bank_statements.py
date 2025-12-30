"""
Bank Statement Import Serializers Module

This module contains serializers for bank statement import and transaction matching:
- Bank statement upload and parsing
- Bank transaction records with invoice matching
- Transaction-invoice match intermediate model
- Batch invoice matching support
- Other cost categorization
- Supported banks information

Supports multiple banks: GRÁNIT, Revolut, MagNet, K&H
"""

from rest_framework import serializers
from decimal import Decimal
from ..models import (
    BankStatement, BankTransaction, BankTransactionInvoiceMatch, OtherCost
)


class BankTransactionInvoiceMatchSerializer(serializers.ModelSerializer):
    """
    Serializer for BankTransactionInvoiceMatch intermediate model.

    Provides invoice match details with confidence and method metadata.
    """
    invoice_details = serializers.SerializerMethodField()

    class Meta:
        model = BankTransactionInvoiceMatch
        fields = [
            'id', 'transaction', 'invoice', 'invoice_details',
            'match_confidence', 'match_method', 'matched_at',
            'matched_by', 'match_notes'
        ]
        read_only_fields = ['matched_at']

    def get_invoice_details(self, obj):
        """Return matched invoice summary"""
        if obj.invoice:
            return {
                'id': obj.invoice.id,
                'invoice_number': obj.invoice.nav_invoice_number,
                'supplier_name': obj.invoice.supplier_name,
                'supplier_tax_number': obj.invoice.supplier_tax_number,
                'gross_amount': str(obj.invoice.invoice_gross_amount) if obj.invoice.invoice_gross_amount else None,
                'payment_due_date': obj.invoice.payment_due_date.isoformat() if obj.invoice.payment_due_date else None,
                'payment_status': obj.invoice.payment_status,
            }
        return None


class BankTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for bank transaction records.

    Provides full transaction details with nested invoice match information.
    Supports both single invoice matches and batch invoice matches.
    """
    statement_details = serializers.SerializerMethodField()
    matched_invoice_details = serializers.SerializerMethodField()
    matched_invoices_details = serializers.SerializerMethodField()  # NEW: Batch matching support
    is_batch_match = serializers.SerializerMethodField()  # NEW: Batch flag
    total_matched_amount = serializers.SerializerMethodField()  # NEW: Sum of matched invoices
    matched_transfer_batch = serializers.SerializerMethodField()
    matched_reimbursement_details = serializers.SerializerMethodField()
    has_other_cost = serializers.SerializerMethodField()
    other_cost_detail = serializers.SerializerMethodField()

    class Meta:
        model = BankTransaction
        fields = [
            'id', 'bank_statement', 'statement_details',
            'transaction_type', 'booking_date', 'value_date',
            'amount', 'currency', 'description', 'short_description',
            'payment_id', 'transaction_id',
            'payer_name', 'payer_iban', 'payer_account_number', 'payer_bic',
            'beneficiary_name', 'beneficiary_iban', 'beneficiary_account_number', 'beneficiary_bic',
            'reference', 'partner_id', 'transaction_type_code', 'fee_amount',
            'card_number', 'merchant_name', 'merchant_location',
            'original_amount', 'original_currency',
            'matched_invoice', 'matched_invoice_details', 'match_confidence', 'match_method',
            'matched_invoices_details', 'is_batch_match', 'total_matched_amount',  # NEW: Batch matching fields
            'matched_transfer', 'matched_transfer_batch',
            'matched_reimbursement', 'matched_reimbursement_details',
            'has_other_cost', 'other_cost_detail',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_statement_details(self, obj):
        """Return basic statement info"""
        if obj.bank_statement:
            return {
                'id': obj.bank_statement.id,
                'bank_name': obj.bank_statement.bank_name,
                'account_number': obj.bank_statement.account_number,
                'period_from': obj.bank_statement.statement_period_from.isoformat() if obj.bank_statement.statement_period_from else None,
                'period_to': obj.bank_statement.statement_period_to.isoformat() if obj.bank_statement.statement_period_to else None,
            }
        return None

    def get_matched_invoice_details(self, obj):
        """Return matched invoice summary (backward compatibility - single invoice)"""
        if obj.matched_invoice:
            return {
                'id': obj.matched_invoice.id,
                'invoice_number': obj.matched_invoice.nav_invoice_number,
                'supplier_name': obj.matched_invoice.supplier_name,
                'supplier_tax_number': obj.matched_invoice.supplier_tax_number,
                'customer_name': obj.matched_invoice.customer_name,
                'customer_tax_number': obj.matched_invoice.customer_tax_number,
                'gross_amount': str(obj.matched_invoice.invoice_gross_amount) if obj.matched_invoice.invoice_gross_amount else None,
                'payment_due_date': obj.matched_invoice.payment_due_date.isoformat() if obj.matched_invoice.payment_due_date else None,
                'payment_status': obj.matched_invoice.payment_status,
            }
        return None

    def get_matched_invoices_details(self, obj):
        """Return list of all matched invoices with metadata (batch matching support)"""
        matches = obj.invoice_matches.select_related('invoice').all()
        if not matches:
            return []

        return [
            {
                'id': match.invoice.id,
                'invoice_number': match.invoice.nav_invoice_number,
                'supplier_name': match.invoice.supplier_name,
                'supplier_tax_number': match.invoice.supplier_tax_number,
                'gross_amount': str(match.invoice.invoice_gross_amount) if match.invoice.invoice_gross_amount else None,
                'payment_due_date': match.invoice.payment_due_date.isoformat() if match.invoice.payment_due_date else None,
                'payment_status': match.invoice.payment_status,
                'match_confidence': str(match.match_confidence),
                'match_method': match.match_method,
                'match_notes': match.match_notes,
            }
            for match in matches
        ]

    def get_is_batch_match(self, obj):
        """Return True if transaction is matched to multiple invoices"""
        return obj.is_batch_match

    def get_total_matched_amount(self, obj):
        """Return sum of all matched invoice amounts"""
        total = obj.total_matched_amount
        return str(total) if total else None

    def get_matched_transfer_batch(self, obj):
        """Return batch ID for matched transfer"""
        if obj.matched_transfer:
            # Get the first batch that contains this transfer
            # In most cases, a transfer belongs to only one batch
            batch = obj.matched_transfer.transferbatch_set.first()
            if batch:
                return batch.id
        return None

    def get_matched_reimbursement_details(self, obj):
        """Return paired reimbursement transaction summary"""
        if obj.matched_reimbursement:
            paired = obj.matched_reimbursement
            return {
                'id': paired.id,
                'bank_statement': paired.bank_statement_id,
                'transaction_type': paired.transaction_type,
                'booking_date': paired.booking_date.isoformat(),
                'amount': str(paired.amount),
                'currency': paired.currency,
                'description': paired.description or '',
                'partner_name': paired.payer_name or paired.beneficiary_name or paired.merchant_name or '',
            }
        return None

    def get_has_other_cost(self, obj):
        """Check if transaction has associated other cost record"""
        return hasattr(obj, 'other_cost_detail') and obj.other_cost_detail is not None

    def get_other_cost_detail(self, obj):
        """Return other cost categorization details"""
        if hasattr(obj, 'other_cost_detail') and obj.other_cost_detail:
            cost = obj.other_cost_detail
            # Ensure tags is always a list (JSONField can sometimes serialize as string)
            tags = cost.tags if isinstance(cost.tags, list) else []
            return {
                'id': cost.id,
                'category': cost.category,
                'category_display': cost.get_category_display(),
                'amount': str(cost.amount),
                'currency': cost.currency,
                'date': cost.date.isoformat(),
                'description': cost.description,
                'notes': cost.notes,
                'tags': tags,
                'created_by': cost.created_by_id,
                'created_at': cost.created_at.isoformat(),
            }
        return None


class BankStatementListSerializer(serializers.ModelSerializer):
    """
    Serializer for bank statement list view.

    Provides summary information without nested transactions.
    """
    bank_name = serializers.CharField(read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    matched_percentage = serializers.SerializerMethodField()

    class Meta:
        model = BankStatement
        fields = [
            'id', 'bank_code', 'bank_name', 'bank_bic',
            'account_number', 'account_iban',
            'statement_period_from', 'statement_period_to', 'statement_number',
            'opening_balance', 'closing_balance',
            'file_name', 'file_size', 'file_hash',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at',
            'status', 'parse_error',
            'total_transactions', 'credit_count', 'debit_count',
            'total_credits', 'total_debits', 'matched_count', 'matched_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company']

    def get_uploaded_by_name(self, obj):
        """Return uploader's full name"""
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return None

    def get_matched_percentage(self, obj):
        """Calculate percentage of matched transactions"""
        if obj.total_transactions > 0:
            return round((obj.matched_count / obj.total_transactions) * 100, 1)
        return 0.0


class BankStatementDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for bank statement detail view.

    Includes full transaction list and detailed metadata.
    """
    transactions = BankTransactionSerializer(many=True, read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    matched_percentage = serializers.SerializerMethodField()
    raw_metadata_json = serializers.SerializerMethodField()

    class Meta:
        model = BankStatement
        fields = [
            'id', 'bank_code', 'bank_name', 'bank_bic',
            'account_number', 'account_iban',
            'statement_period_from', 'statement_period_to', 'statement_number',
            'opening_balance', 'closing_balance',
            'file_name', 'file_size', 'file_hash', 'file_path',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at',
            'status', 'parse_error', 'parse_warnings',
            'total_transactions', 'credit_count', 'debit_count',
            'total_credits', 'total_debits', 'matched_count', 'matched_percentage',
            'transactions',
            'raw_metadata_json',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company']

    def get_uploaded_by_name(self, obj):
        """Return uploader's full name"""
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return None

    def get_matched_percentage(self, obj):
        """Calculate percentage of matched transactions"""
        if obj.total_transactions > 0:
            return round((obj.matched_count / obj.total_transactions) * 100, 1)
        return 0.0

    def get_raw_metadata_json(self, obj):
        """Convert raw_metadata to JSON-serializable format"""
        import json
        from datetime import date, datetime
        from decimal import Decimal

        def convert_to_serializable(data):
            """Recursively convert non-serializable objects"""
            if isinstance(data, dict):
                return {k: convert_to_serializable(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_to_serializable(item) for item in data]
            elif isinstance(data, (date, datetime)):
                return data.isoformat()
            elif isinstance(data, Decimal):
                return str(data)
            else:
                return data

        if obj.raw_metadata:
            return convert_to_serializable(obj.raw_metadata)
        return None


class BankStatementUploadSerializer(serializers.Serializer):
    """
    Serializer for bank statement file upload.

    Handles PDF file validation and upload metadata.
    """
    file = serializers.FileField(
        required=True,
        help_text="Bank statement PDF file"
    )

    def validate_file(self, value):
        """Validate uploaded file - accepts PDF, CSV, and XML formats"""
        # Check file extension - support multiple bank statement formats
        allowed_extensions = ('.pdf', '.csv', '.xml')
        filename_lower = value.name.lower()

        if not filename_lower.endswith(allowed_extensions):
            raise serializers.ValidationError(
                "Csak PDF, CSV vagy XML fájlok tölthetők fel (banki kivonathoz)"
            )

        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"A fájl mérete nem lehet nagyobb mint {max_size // (1024*1024)}MB"
            )

        return value


class OtherCostSerializer(serializers.ModelSerializer):
    """
    Serializer for other cost records.

    Provides expense categorization and tagging functionality.
    """
    transaction_details = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OtherCost
        fields = [
            'id', 'bank_transaction', 'transaction_details',
            'category', 'amount', 'currency', 'date',
            'description', 'notes', 'tags',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'created_by']

    def get_transaction_details(self, obj):
        """Return basic transaction info if linked"""
        if obj.bank_transaction:
            return {
                'id': obj.bank_transaction.id,
                'transaction_type': obj.bank_transaction.transaction_type,
                'booking_date': obj.bank_transaction.booking_date,
                'description': obj.bank_transaction.description,
            }
        return None

    def get_created_by_name(self, obj):
        """Return creator's full name"""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return None

    def validate_tags(self, value):
        """Validate tags are list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Címkéknek listának kell lennie")

        if not all(isinstance(tag, str) for tag in value):
            raise serializers.ValidationError("Minden címkének szövegnek kell lennie")

        return value


class SupportedBanksSerializer(serializers.Serializer):
    """
    Serializer for supported banks list.

    Returns available bank adapters from factory.
    """
    code = serializers.CharField()
    name = serializers.CharField()
    bic = serializers.CharField()
