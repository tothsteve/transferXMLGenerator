"""
Billingo Integration Serializers Module

This module contains serializers for Billingo invoice management system integration:
- Billingo invoices with line items and related documents
- Company Billingo settings with encrypted API key management
- Billingo sync logs for audit trails
- Billingo sync trigger for manual synchronization
- Billingo spending records for expense tracking

All Billingo invoice data is READ-ONLY as it's synced from Billingo API.
"""

from rest_framework import serializers
from decimal import Decimal
from ..models import (
    CompanyBillingoSettings, BillingoInvoice, BillingoInvoiceItem, BillingoRelatedDocument,
    BillingoSyncLog, BillingoSpending, Company
)


class BillingoInvoiceItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Billingo invoice line items.

    Read-only serializer as items are synced from Billingo API.
    """

    class Meta:
        model = BillingoInvoiceItem
        fields = [
            'id', 'product_id', 'name', 'quantity', 'unit',
            'net_unit_price', 'net_amount', 'gross_amount',
            'vat', 'entitlement', 'created_at', 'updated_at'
        ]
        read_only_fields = fields  # All fields are read-only (synced from API)


class BillingoRelatedDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for related Billingo documents (corrections, credit notes, etc.).

    Read-only serializer as relationships are synced from Billingo API.
    """

    class Meta:
        model = BillingoRelatedDocument
        fields = [
            'id', 'related_invoice_id', 'related_invoice_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields  # All fields are read-only (synced from API)


class BillingoInvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Billingo invoices.

    Read-only serializer as invoices are synced from Billingo API.
    Includes nested invoice items and related documents.
    """
    items = BillingoInvoiceItemSerializer(many=True, read_only=True)
    related_documents = BillingoRelatedDocumentSerializer(many=True, read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    # Formatted display fields
    gross_total_formatted = serializers.SerializerMethodField()
    net_total_formatted = serializers.SerializerMethodField()
    invoice_date_formatted = serializers.SerializerMethodField()
    fulfillment_date_formatted = serializers.SerializerMethodField()
    due_date_formatted = serializers.SerializerMethodField()
    paid_date_formatted = serializers.SerializerMethodField()

    class Meta:
        model = BillingoInvoice
        fields = [
            # Identifiers
            'id', 'company', 'company_name', 'invoice_number', 'type',
            'correction_type', 'cancelled', 'block_id',

            # Payment information
            'payment_status', 'payment_method', 'gross_total', 'gross_total_formatted',
            'net_total', 'net_total_formatted', 'currency', 'conversion_rate',

            # Dates
            'invoice_date', 'invoice_date_formatted',
            'fulfillment_date', 'fulfillment_date_formatted',
            'due_date', 'due_date_formatted',
            'paid_date', 'paid_date_formatted',

            # Organization (our company)
            'organization_name', 'organization_tax_number',
            'organization_bank_account_number', 'organization_bank_account_iban',
            'organization_swift',

            # Partner (customer/supplier)
            'partner_id', 'partner_name', 'partner_tax_number',
            'partner_iban', 'partner_swift', 'partner_account_number',

            # Additional information
            'comment', 'online_szamla_status',

            # Nested items and relationships
            'items',
            'related_documents',

            # Metadata
            'created_at', 'updated_at', 'last_modified'
        ]
        read_only_fields = fields  # All fields are read-only (synced from API)

    def get_gross_total_formatted(self, obj):
        """Format gross total with currency"""
        return f"{obj.gross_total:,.2f} {obj.currency}"

    def get_net_total_formatted(self, obj):
        """Format net total with currency"""
        if obj.net_total:
            return f"{obj.net_total:,.2f} {obj.currency}"
        return None

    def get_invoice_date_formatted(self, obj):
        """Format invoice date for display"""
        if obj.invoice_date:
            return obj.invoice_date.strftime('%Y-%m-%d')
        return None

    def get_fulfillment_date_formatted(self, obj):
        """Format fulfillment date for display"""
        if obj.fulfillment_date:
            return obj.fulfillment_date.strftime('%Y-%m-%d')
        return None

    def get_due_date_formatted(self, obj):
        """Format due date for display"""
        if obj.due_date:
            return obj.due_date.strftime('%Y-%m-%d')
        return None

    def get_paid_date_formatted(self, obj):
        """Format paid date for display"""
        if obj.paid_date:
            return obj.paid_date.strftime('%Y-%m-%d')
        return None


class BillingoInvoiceListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Billingo invoice lists.

    Excludes nested items for better performance in list views.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    gross_total_formatted = serializers.SerializerMethodField()
    invoice_date_formatted = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    related_documents_count = serializers.SerializerMethodField()
    related_invoice_number = serializers.SerializerMethodField()

    class Meta:
        model = BillingoInvoice
        fields = [
            'id', 'company', 'company_name', 'invoice_number', 'type',
            'payment_status', 'payment_method', 'gross_total', 'gross_total_formatted',
            'currency', 'invoice_date', 'invoice_date_formatted',
            'due_date', 'paid_date', 'partner_name', 'partner_tax_number',
            'cancelled', 'item_count', 'related_documents_count', 'related_invoice_number', 'created_at'
        ]
        read_only_fields = fields

    def get_gross_total_formatted(self, obj):
        """Format gross total with currency"""
        return f"{obj.gross_total:,.2f} {obj.currency}"

    def get_invoice_date_formatted(self, obj):
        """Format invoice date for display"""
        if obj.invoice_date:
            return obj.invoice_date.strftime('%Y-%m-%d')
        return None

    def get_item_count(self, obj):
        """Return number of invoice items"""
        return obj.items.count()

    def get_related_documents_count(self, obj):
        """Return number of related documents"""
        return obj.related_documents.count()

    def get_related_invoice_number(self, obj):
        """Return first related invoice number for display in list"""
        first_related = obj.related_documents.first()
        return first_related.related_invoice_number if first_related else None


class CompanyBillingoSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for Billingo API settings.

    Handles API key encryption/decryption and validation.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    last_sync_time_formatted = serializers.SerializerMethodField()

    # Write-only field for API key input (will be encrypted)
    api_key_input = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Read-only indicator if API key is set
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = CompanyBillingoSettings
        fields = [
            'id', 'company', 'company_name',
            'api_key_input', 'has_api_key',
            'last_sync_time', 'last_sync_time_formatted',
            'last_billingo_invoice_sync_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'company', 'company_name',
            'last_sync_time', 'last_billingo_invoice_sync_date'
        ]

    def get_has_api_key(self, obj):
        """Indicate if API key is configured (without exposing it)"""
        return bool(obj.api_key)

    def get_last_sync_time_formatted(self, obj):
        """Format last sync time for display"""
        if obj.last_sync_time:
            return obj.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def create(self, validated_data):
        """Create settings with encrypted API key"""
        from bank_transfers.services.credential_manager import CredentialManager

        api_key_input = validated_data.pop('api_key_input', None)

        if api_key_input:
            credential_manager = CredentialManager()
            validated_data['api_key'] = credential_manager.encrypt_credential(api_key_input)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update settings with encrypted API key"""
        from bank_transfers.services.credential_manager import CredentialManager

        api_key_input = validated_data.pop('api_key_input', None)

        if api_key_input:
            credential_manager = CredentialManager()
            validated_data['api_key'] = credential_manager.encrypt_credential(api_key_input)

        return super().update(instance, validated_data)


class BillingoSyncLogSerializer(serializers.ModelSerializer):
    """
    Serializer for Billingo sync audit logs.

    Read-only serializer for monitoring sync operations.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    started_at_formatted = serializers.SerializerMethodField()
    completed_at_formatted = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    errors_parsed = serializers.SerializerMethodField()

    class Meta:
        model = BillingoSyncLog
        fields = [
            'id', 'company', 'company_name',
            'sync_type', 'sync_type_display',
            'status', 'status_display',
            'invoices_processed', 'invoices_created', 'invoices_updated', 'invoices_skipped',
            'items_extracted', 'api_calls_made',
            'sync_duration_seconds', 'duration_formatted',
            'started_at', 'started_at_formatted',
            'completed_at', 'completed_at_formatted',
            'errors', 'errors_parsed'
        ]
        read_only_fields = fields  # All fields are read-only (created by sync service)

    def get_started_at_formatted(self, obj):
        """Format start time for display"""
        if obj.started_at:
            return obj.started_at.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_completed_at_formatted(self, obj):
        """Format completion time for display"""
        if obj.completed_at:
            return obj.completed_at.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_duration_formatted(self, obj):
        """Format duration in human-readable format"""
        if obj.sync_duration_seconds is not None:
            seconds = obj.sync_duration_seconds
            if seconds < 60:
                return f"{seconds}s"
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        return None

    def get_errors_parsed(self, obj):
        """Parse errors JSON for display"""
        if obj.errors:
            import json
            try:
                return json.loads(obj.errors)
            except json.JSONDecodeError:
                return []
        return []


class BillingoSyncTriggerSerializer(serializers.Serializer):
    """
    Serializer for triggering manual Billingo sync.

    Used for POST requests to sync endpoint.
    """
    company_id = serializers.IntegerField(required=False, help_text="Sync specific company (optional)")

    def validate_company_id(self, value):
        """Validate company exists and is active"""
        if value is not None:
            from bank_transfers.models import Company
            try:
                company = Company.objects.get(id=value, is_active=True)
            except Company.DoesNotExist:
                raise serializers.ValidationError(
                    f"Cég #{value} nem található vagy nem aktív"
                )
        return value


class BillingoSpendingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for spending list view"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = BillingoSpending
        fields = [
            'id', 'company', 'company_name', 'invoice_number', 'partner_name',
            'partner_tax_code', 'category', 'category_display', 'invoice_date',
            'due_date', 'paid_at', 'is_paid', 'total_gross_local', 'currency',
            'payment_method', 'is_created_by_nav'
        ]
        read_only_fields = fields


class BillingoSpendingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for spending detail view"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = BillingoSpending
        fields = '__all__'
        read_only_fields = [
            'id', 'company', 'organization_id', 'created_at', 'updated_at'
        ]
