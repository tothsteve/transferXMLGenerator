from rest_framework import serializers
from decimal import Decimal
from .models import (
    BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, Company,
    NavConfiguration, Invoice, InvoiceLineItem, InvoiceSyncLog
)

class BankAccountSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = ['id', 'name', 'account_number', 'bank_name', 'is_default', 'company_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

class BeneficiarySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'account_number', 'description', 
            'is_frequent', 'is_active', 'remittance_information', 
            'company_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

class TemplateBeneficiarySerializer(serializers.ModelSerializer):
    beneficiary = BeneficiarySerializer(read_only=True)
    beneficiary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TemplateBeneficiary
        fields = [
            'id', 'beneficiary', 'beneficiary_id', 
            'default_amount', 'default_remittance', 'default_execution_date',
            'order', 'is_active'
        ]

class TransferTemplateSerializer(serializers.ModelSerializer):
    template_beneficiaries = TemplateBeneficiarySerializer(many=True, read_only=True)
    beneficiary_count = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = TransferTemplate
        fields = [
            'id', 'name', 'description', 'is_active',
            'template_beneficiaries', 'beneficiary_count', 'company_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']
    
    def get_beneficiary_count(self, obj):
        return obj.template_beneficiaries.filter(is_active=True).count()

class TransferSerializer(serializers.ModelSerializer):
    beneficiary = BeneficiarySerializer(read_only=True)
    beneficiary_id = serializers.IntegerField(write_only=True)
    originator_account = BankAccountSerializer(read_only=True)
    originator_account_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            'id', 'originator_account', 'originator_account_id',
            'beneficiary', 'beneficiary_id', 'amount', 'currency',
            'execution_date', 'remittance_info', 'template', 'order',
            'is_processed', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TransferBatchSerializer(serializers.ModelSerializer):
    transfers = TransferSerializer(many=True, read_only=True)
    transfer_count = serializers.SerializerMethodField()
    xml_filename = serializers.ReadOnlyField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = TransferBatch
        fields = [
            'id', 'name', 'description', 'transfers',
            'total_amount', 'transfer_count', 'order',
            'used_in_bank', 'bank_usage_date', 'xml_filename',
            'company_name', 'created_at', 'xml_generated_at'
        ]
        read_only_fields = ['created_at', 'xml_generated_at', 'total_amount', 'xml_filename', 'company', 'company_name']
    
    def get_transfer_count(self, obj):
        return obj.transfers.count()

# Transfer creation for template loading
class TransferCreateFromTemplateSerializer(serializers.Serializer):
    template_id = serializers.IntegerField()
    originator_account_id = serializers.IntegerField()
    execution_date = serializers.DateField()
    
class BulkTransferSerializer(serializers.Serializer):
    transfers = TransferSerializer(many=True)
    batch_name = serializers.CharField(max_length=200, required=False)

# Excel import serializer
class ExcelImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    import_type = serializers.ChoiceField(choices=[
        ('beneficiaries', 'Kedvezményezettek'),
        ('transfers', 'Utalások')
    ], default='beneficiaries')

# XML generation serializer
class XMLGenerateSerializer(serializers.Serializer):
    transfer_ids = serializers.ListField(child=serializers.IntegerField())
    batch_name = serializers.CharField(max_length=200, required=False)


# NAV Invoice Synchronization Serializers (READ-ONLY)

class NavConfigurationSerializer(serializers.ModelSerializer):
    """READ-ONLY serializer for NAV configuration."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    last_sync_formatted = serializers.SerializerMethodField()
    sync_status = serializers.SerializerMethodField()
    
    class Meta:
        model = NavConfiguration
        fields = [
            'id', 'company', 'company_name', 'tax_number', 'technical_user_login',
            'api_environment', 'sync_enabled', 'is_active', 'sync_frequency_hours',
            'last_sync_timestamp', 'last_sync_formatted', 'sync_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['__all__']
    
    def get_last_sync_formatted(self, obj):
        if obj.last_sync_timestamp:
            return obj.last_sync_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return 'Még nem szinkronizált'
    
    def get_sync_status(self, obj):
        if not obj.sync_enabled:
            return 'Kikapcsolva'
        elif not obj.is_active:
            return 'Inaktív'
        else:
            return 'Aktív'


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    """READ-ONLY serializer for invoice line items."""
    
    line_gross_amount_formatted = serializers.SerializerMethodField()
    unit_price_formatted = serializers.SerializerMethodField()
    vat_rate_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceLineItem
        fields = [
            'id', 'line_number', 'line_description', 'quantity', 'unit_of_measure',
            'unit_price', 'unit_price_formatted', 'line_net_amount', 'line_vat_amount',
            'line_gross_amount', 'line_gross_amount_formatted', 'vat_rate', 'vat_rate_formatted',
            'product_code_category', 'product_code_value', 'created_at'
        ]
        read_only_fields = ['__all__']
    
    def get_line_gross_amount_formatted(self, obj):
        return f"{obj.line_gross_amount:,.2f} Ft"
    
    def get_unit_price_formatted(self, obj):
        return f"{obj.unit_price:,.2f} Ft"
    
    def get_vat_rate_formatted(self, obj):
        return f"{obj.vat_rate}%"


class InvoiceSerializer(serializers.ModelSerializer):
    """READ-ONLY serializer for invoices."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    invoice_direction_display = serializers.SerializerMethodField()
    invoice_gross_amount_formatted = serializers.SerializerMethodField()
    issue_date_formatted = serializers.SerializerMethodField()
    sync_status_display = serializers.SerializerMethodField()
    line_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'company', 'company_name', 'nav_invoice_number', 'invoice_direction',
            'invoice_direction_display', 'supplier_name', 'supplier_tax_number', 'customer_name',
            'customer_tax_number', 'issue_date', 'issue_date_formatted', 'fulfillment_date',
            'payment_due_date', 'currency_code', 'invoice_net_amount', 'invoice_vat_amount',
            'invoice_gross_amount', 'invoice_gross_amount_formatted', 'sync_status',
            'sync_status_display', 'line_items', 'line_items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['__all__']
    
    def get_invoice_direction_display(self, obj):
        return 'Kimenő számla' if obj.invoice_direction == 'OUTBOUND' else 'Bejövő számla'
    
    def get_invoice_gross_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_gross_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_gross_amount:,.2f} {obj.currency_code}"
    
    def get_issue_date_formatted(self, obj):
        if obj.issue_date:
            return obj.issue_date.strftime('%Y-%m-%d')
        return None
    
    def get_sync_status_display(self, obj):
        status_map = {'PENDING': 'Függőben', 'SYNCED': 'Szinkronizálva', 'ERROR': 'Hiba'}
        return status_map.get(obj.sync_status, obj.sync_status)
    
    def get_line_items_count(self, obj):
        return obj.line_items.count()


class InvoiceSummarySerializer(serializers.ModelSerializer):
    """READ-ONLY summary serializer for invoices (lighter version for lists)."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    invoice_direction_display = serializers.SerializerMethodField()
    invoice_gross_amount_formatted = serializers.SerializerMethodField()
    issue_date_formatted = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'company', 'company_name', 'nav_invoice_number', 'invoice_direction',
            'invoice_direction_display', 'partner_name', 'issue_date', 'issue_date_formatted',
            'currency_code', 'invoice_gross_amount', 'invoice_gross_amount_formatted',
            'sync_status', 'created_at'
        ]
        read_only_fields = ['__all__']
    
    def get_invoice_direction_display(self, obj):
        return 'Kimenő' if obj.invoice_direction == 'OUTBOUND' else 'Bejövő'
    
    def get_invoice_gross_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_gross_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_gross_amount:,.2f} {obj.currency_code}"
    
    def get_issue_date_formatted(self, obj):
        if obj.issue_date:
            return obj.issue_date.strftime('%Y-%m-%d')
        return None
    
    def get_partner_name(self, obj):
        if obj.invoice_direction == 'OUTBOUND':
            return obj.customer_name
        else:
            return obj.supplier_name


class InvoiceSyncLogSerializer(serializers.ModelSerializer):
    """READ-ONLY serializer for invoice synchronization logs."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    sync_duration = serializers.SerializerMethodField()
    sync_start_formatted = serializers.SerializerMethodField()
    sync_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceSyncLog
        fields = [
            'id', 'company', 'company_name', 'sync_start_time', 'sync_start_formatted',
            'sync_end_time', 'sync_duration', 'direction_synced', 'invoices_processed',
            'invoices_created', 'invoices_updated', 'sync_status', 'sync_status_display',
            'last_error_message', 'created_at'
        ]
        read_only_fields = ['__all__']
    
    def get_sync_duration(self, obj):
        if obj.sync_start_time and obj.sync_end_time:
            duration = obj.sync_end_time - obj.sync_start_time
            return duration.total_seconds()
        return None
    
    def get_sync_start_formatted(self, obj):
        if obj.sync_start_time:
            return obj.sync_start_time.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_sync_status_display(self, obj):
        status_map = {'RUNNING': 'Futó', 'COMPLETED': 'Befejezett', 'ERROR': 'Hiba'}
        return status_map.get(obj.sync_status, obj.sync_status)


class InvoiceStatsSerializer(serializers.Serializer):
    """READ-ONLY serializer for invoice statistics."""
    
    total_invoices = serializers.IntegerField(read_only=True)
    outbound_invoices = serializers.IntegerField(read_only=True)
    inbound_invoices = serializers.IntegerField(read_only=True)
    total_gross_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_gross_amount_formatted = serializers.SerializerMethodField()
    last_sync_date = serializers.DateTimeField(read_only=True)
    last_sync_formatted = serializers.SerializerMethodField()
    
    def get_total_gross_amount_formatted(self, obj):
        amount = obj.get('total_gross_amount', 0)
        return f"{amount:,.0f} Ft"
    
    def get_last_sync_formatted(self, obj):
        last_sync = obj.get('last_sync_date')
        if last_sync:
            return last_sync.strftime('%Y-%m-%d %H:%M:%S')
        return 'Még nem szinkronizált'
