from rest_framework import serializers
from decimal import Decimal
from .models import (
    BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, Company,
    NavConfiguration, Invoice, InvoiceLineItem, InvoiceSyncLog, TrustedPartner
)
from .hungarian_account_validator import validate_and_format_hungarian_account_number
from .string_validation import validate_beneficiary_name, validate_remittance_info, normalize_whitespace, sanitize_export_string

class BankAccountSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = ['id', 'name', 'account_number', 'bank_name', 'is_default', 'company_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

    def validate_account_number(self, value):
        """Validate and format Hungarian bank account number"""
        if not value:
            raise serializers.ValidationError("Számlaszám megadása kötelező")
        
        validation = validate_and_format_hungarian_account_number(value)
        if not validation.is_valid:
            raise serializers.ValidationError(validation.error or "Érvénytelen számlaszám formátum")
        
        # Return the formatted account number for consistent storage
        return validation.formatted

class BeneficiarySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'account_number', 'vat_number', 'description', 
            'is_frequent', 'is_active', 'remittance_information', 
            'company_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'company_name']

    def validate_account_number(self, value):
        """Validate and format Hungarian bank account number"""
        if not value:
            raise serializers.ValidationError("Számlaszám megadása kötelező")
        
        validation = validate_and_format_hungarian_account_number(value)
        if not validation.is_valid:
            raise serializers.ValidationError(validation.error or "Érvénytelen számlaszám formátum")
        
        # Return the formatted account number for consistent storage
        return validation.formatted
    
    def validate_name(self, value):
        """Sanitize beneficiary name for XML/CSV export"""
        if not value or not value.strip():
            raise serializers.ValidationError("A kedvezményezett neve kötelező.")
        
        # Sanitize invalid characters and normalize whitespace
        sanitized = sanitize_export_string(value)
        return normalize_whitespace(sanitized)
    
    def validate_remittance_information(self, value):
        """Sanitize remittance information for XML/CSV export"""
        if not value:
            return value
        
        # Sanitize invalid characters and normalize whitespace
        sanitized = sanitize_export_string(value)
        return normalize_whitespace(sanitized)
    
    def validate_vat_number(self, value):
        """Validate Hungarian VAT number format"""
        if not value:
            return value
        
        # Clean the VAT number (remove spaces and dashes)
        clean_vat = value.replace(' ', '').replace('-', '')
        
        # Validate format
        if not clean_vat.isdigit() or len(clean_vat) != 10:
            raise serializers.ValidationError(
                "Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8440961790)"
            )
        
        # Return the cleaned VAT number
        return clean_vat

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
    nav_invoice_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Transfer
        fields = [
            'id', 'originator_account', 'originator_account_id',
            'beneficiary', 'beneficiary_id', 'amount', 'currency',
            'execution_date', 'remittance_info', 'template', 'nav_invoice', 'nav_invoice_id',
            'order', 'is_processed', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_remittance_info(self, value):
        """Sanitize remittance info for XML/CSV export"""
        if not value:
            return value
        
        # Sanitize invalid characters and normalize whitespace
        sanitized = sanitize_export_string(value)
        return normalize_whitespace(sanitized)
    
    def validate_beneficiary_id(self, value):
        """Validate that beneficiary has account number for transfer creation"""
        try:
            beneficiary = Beneficiary.objects.get(id=value)
            if not beneficiary.account_number:
                raise serializers.ValidationError(
                    f"Kedvezményezett '{beneficiary.name}' rendelkezik adóazonosító jellel ({beneficiary.vat_number}), "
                    f"de nincs bankszámlaszáma. Kérem adja meg a bankszámlaszámot az utalás létrehozása előtt."
                )
            return value
        except Beneficiary.DoesNotExist:
            raise serializers.ValidationError("A kedvezményezett nem található.")

class TransferBatchSerializer(serializers.ModelSerializer):
    transfers = TransferSerializer(many=True, read_only=True)
    transfer_count = serializers.SerializerMethodField()
    filename = serializers.ReadOnlyField()
    xml_filename = serializers.ReadOnlyField()  # Keep for backwards compatibility
    company_name = serializers.CharField(source='company.name', read_only=True)
    batch_format_display = serializers.CharField(source='get_batch_format_display', read_only=True)
    
    class Meta:
        model = TransferBatch
        fields = [
            'id', 'name', 'description', 'transfers',
            'total_amount', 'transfer_count', 'order',
            'used_in_bank', 'bank_usage_date', 'batch_format', 'batch_format_display',
            'filename', 'xml_filename', 'company_name', 'created_at', 'xml_generated_at'
        ]
        read_only_fields = ['created_at', 'xml_generated_at', 'total_amount', 'filename', 'xml_filename', 'company', 'company_name', 'batch_format_display']
    
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
    sync_status = serializers.SerializerMethodField()
    
    class Meta:
        model = NavConfiguration
        fields = [
            'id', 'company', 'company_name', 'tax_number', 'technical_user_login',
            'api_environment', 'sync_enabled', 'is_active', 'sync_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['__all__']
    
    
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
        if obj.unit_price is None:
            return "-"
        return f"{obj.unit_price:,.2f} Ft"
    
    def get_vat_rate_formatted(self, obj):
        if obj.vat_rate is None:
            return "-"
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
            'sync_status_display', 'line_items', 'line_items_count', 'payment_status',
            'payment_status_date', 'auto_marked_paid', 'supplier_bank_account_number',
            'customer_bank_account_number', 'created_at', 'updated_at'
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


class InvoiceListSerializer(serializers.ModelSerializer):
    """READ-ONLY serializer for invoice list with all required table fields."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    invoice_direction_display = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    partner_tax_number = serializers.SerializerMethodField()
    
    # Formatted date fields
    issue_date_formatted = serializers.SerializerMethodField()
    fulfillment_date_formatted = serializers.SerializerMethodField()
    payment_due_date_formatted = serializers.SerializerMethodField()
    payment_date_formatted = serializers.SerializerMethodField()
    
    # Formatted financial fields
    invoice_net_amount_formatted = serializers.SerializerMethodField()
    invoice_vat_amount_formatted = serializers.SerializerMethodField()
    invoice_gross_amount_formatted = serializers.SerializerMethodField()
    
    # Payment status (using new database fields) 
    payment_status = serializers.SerializerMethodField()
    payment_status_date_formatted = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            # Basic info
            'id', 'company', 'company_name', 'nav_invoice_number', 'invoice_direction',
            'invoice_direction_display', 'partner_name', 'partner_tax_number',
            
            # Dates
            'issue_date', 'issue_date_formatted',
            'fulfillment_date', 'fulfillment_date_formatted',
            'payment_due_date', 'payment_due_date_formatted',
            'payment_date', 'payment_date_formatted',
            
            # Financial
            'currency_code', 
            'invoice_net_amount', 'invoice_net_amount_formatted',
            'invoice_vat_amount', 'invoice_vat_amount_formatted',
            'invoice_gross_amount', 'invoice_gross_amount_formatted',
            
            # Business
            'invoice_operation', 'payment_method', 'original_invoice_number',
            'payment_status', 'payment_status_date', 'payment_status_date_formatted', 
            'auto_marked_paid', 'is_overdue', 'invoice_category',
            'supplier_bank_account_number', 'customer_bank_account_number',
            
            # System
            'sync_status', 'created_at'
        ]
        read_only_fields = ['__all__']
    
    def get_invoice_direction_display(self, obj):
        return 'Kimenő' if obj.invoice_direction == 'OUTBOUND' else 'Bejövő'
    
    def get_partner_name(self, obj):
        if obj.invoice_direction == 'OUTBOUND':
            return obj.customer_name
        else:
            return obj.supplier_name
    
    def get_partner_tax_number(self, obj):
        if obj.invoice_direction == 'OUTBOUND':
            return obj.customer_tax_number
        else:
            return obj.supplier_tax_number
    
    def get_issue_date_formatted(self, obj):
        return obj.issue_date.strftime('%Y-%m-%d') if obj.issue_date else None
    
    def get_fulfillment_date_formatted(self, obj):
        return obj.fulfillment_date.strftime('%Y-%m-%d') if obj.fulfillment_date else None
    
    def get_payment_due_date_formatted(self, obj):
        return obj.payment_due_date.strftime('%Y-%m-%d') if obj.payment_due_date else None
    
    def get_payment_date_formatted(self, obj):
        return obj.payment_date.strftime('%Y-%m-%d') if obj.payment_date else None
    
    def get_invoice_net_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_net_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_net_amount:,.2f} {obj.currency_code}"
    
    def get_invoice_vat_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_vat_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_vat_amount:,.2f} {obj.currency_code}"
    
    def get_invoice_gross_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_gross_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_gross_amount:,.2f} {obj.currency_code}"
    
    def get_payment_status_date_formatted(self, obj):
        if obj.payment_status_date:
            return obj.payment_status_date.strftime('%Y-%m-%d')
        return None
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()
    
    def get_payment_status(self, obj):
        """Enhanced payment status with business logic - Transfer workflow state takes priority"""
        from django.utils import timezone
        
        # PRIORITY 1: Check transfer workflow state first (overrides database status)
        has_transfer = hasattr(obj, 'generated_transfers') and obj.generated_transfers.exists()
        has_used_batch = False
        
        if has_transfer:
            # Check if any related transfer has a batch that is marked as used in bank
            for transfer in obj.generated_transfers.all():
                if hasattr(transfer, 'transferbatch_set') and transfer.transferbatch_set.filter(used_in_bank=True).exists():
                    has_used_batch = True
                    break
            
            if has_used_batch:
                # Transfer has batch marked as used in bank - PAID_SYSTEM (highest priority)
                return {
                    'status': 'PAID_SYSTEM', 
                    'label': 'Kifizetve (Bankba átadva)',
                    'icon': 'check_circle',
                    'class': 'status-paid-system'
                }
            else:
                # Has transfer but no used batch - PREPARED (overrides manual PAID status)
                return {
                    'status': 'PREPARED',
                    'label': 'Előkészítve',
                    'icon': 'upload',
                    'class': 'status-prepared'
                }
        
        # PRIORITY 2: No transfer exists, check database payment_status
        if obj.payment_status == 'UNPAID':
            # Check if overdue
            if obj.payment_due_date and obj.payment_due_date < timezone.now().date():
                return {
                    'status': 'OVERDUE',
                    'label': 'Lejárt',
                    'icon': 'warning',
                    'class': 'status-overdue'
                }
            else:
                return {
                    'status': 'UNPAID',
                    'label': 'Fizetésre vár',
                    'icon': 'schedule',
                    'class': 'status-unpaid'
                }
        elif obj.payment_status == 'PREPARED':
            return {
                'status': 'PREPARED',
                'label': 'Előkészítve',
                'icon': 'upload',
                'class': 'status-prepared'
            }
        elif obj.payment_status == 'PAID':
            # No transfer exists, but marked as PAID - check if trusted partner or manual
            if obj.auto_marked_paid:
                # Auto-marked as paid by trusted partner
                return {
                    'status': 'PAID_TRUSTED',
                    'label': 'Kifizetve (Automatikus)',
                    'icon': 'check_circle',
                    'class': 'status-paid-trusted'
                }
            else:
                # Manually marked as paid
                return {
                    'status': 'PAID_MANUAL',
                    'label': 'Kifizetve (Manuálisan)',
                    'icon': 'check_circle',
                    'class': 'status-paid-manual'
                }
        
        return {
            'status': 'UNKNOWN',
            'label': 'Ismeretlen',
            'icon': 'help',
            'class': 'status-unknown'
        }


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """READ-ONLY detailed serializer for individual invoice view with line items."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    invoice_direction_display = serializers.SerializerMethodField()
    
    # All formatted fields from list serializer
    partner_name = serializers.SerializerMethodField()
    partner_tax_number = serializers.SerializerMethodField()
    issue_date_formatted = serializers.SerializerMethodField()
    fulfillment_date_formatted = serializers.SerializerMethodField()
    payment_due_date_formatted = serializers.SerializerMethodField()
    payment_date_formatted = serializers.SerializerMethodField()
    invoice_net_amount_formatted = serializers.SerializerMethodField()
    invoice_vat_amount_formatted = serializers.SerializerMethodField()
    invoice_gross_amount_formatted = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            # Basic info
            'id', 'company', 'company_name', 'nav_invoice_number', 'invoice_direction',
            'invoice_direction_display', 'partner_name', 'partner_tax_number',
            'supplier_name', 'supplier_tax_number', 'customer_name', 'customer_tax_number',
            
            # Dates
            'issue_date', 'issue_date_formatted',
            'fulfillment_date', 'fulfillment_date_formatted',
            'payment_due_date', 'payment_due_date_formatted',
            'payment_date', 'payment_date_formatted',
            
            # Financial
            'currency_code', 
            'invoice_net_amount', 'invoice_net_amount_formatted',
            'invoice_vat_amount', 'invoice_vat_amount_formatted',
            'invoice_gross_amount', 'invoice_gross_amount_formatted',
            'invoice_net_amount_huf', 'invoice_vat_amount_huf', 'invoice_gross_amount_huf',
            
            # Business
            'invoice_operation', 'invoice_category', 'payment_method', 'invoice_appearance',
            'original_invoice_number', 'payment_status', 'supplier_bank_account_number',
            'customer_bank_account_number',
            
            # NAV metadata
            'nav_source', 'original_request_version', 'completion_date', 'last_modified_date',
            
            # Line items
            'line_items',
            
            # System
            'sync_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['__all__']
    
    # Reuse methods from InvoiceListSerializer
    def get_invoice_direction_display(self, obj):
        return 'Kimenő számla' if obj.invoice_direction == 'OUTBOUND' else 'Bejövő számla'
    
    def get_partner_name(self, obj):
        return obj.customer_name if obj.invoice_direction == 'OUTBOUND' else obj.supplier_name
    
    def get_partner_tax_number(self, obj):
        return obj.customer_tax_number if obj.invoice_direction == 'OUTBOUND' else obj.supplier_tax_number
    
    def get_issue_date_formatted(self, obj):
        return obj.issue_date.strftime('%Y-%m-%d') if obj.issue_date else None
    
    def get_fulfillment_date_formatted(self, obj):
        return obj.fulfillment_date.strftime('%Y-%m-%d') if obj.fulfillment_date else None
    
    def get_payment_due_date_formatted(self, obj):
        return obj.payment_due_date.strftime('%Y-%m-%d') if obj.payment_due_date else None
    
    def get_payment_date_formatted(self, obj):
        return obj.payment_date.strftime('%Y-%m-%d') if obj.payment_date else None
    
    def get_invoice_net_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_net_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_net_amount:,.2f} {obj.currency_code}"
    
    def get_invoice_vat_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_vat_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_vat_amount:,.2f} {obj.currency_code}"
    
    def get_invoice_gross_amount_formatted(self, obj):
        if obj.currency_code == 'HUF':
            return f"{obj.invoice_gross_amount:,.0f} Ft"
        else:
            return f"{obj.invoice_gross_amount:,.2f} {obj.currency_code}"
    
    def get_payment_status(self, obj):
        """Enhanced payment status with business logic - Transfer workflow state takes priority"""
        from django.utils import timezone
        
        # PRIORITY 1: Check transfer workflow state first (overrides database status)
        has_transfer = hasattr(obj, 'generated_transfers') and obj.generated_transfers.exists()
        has_used_batch = False
        
        if has_transfer:
            # Check if any related transfer has a batch that is marked as used in bank
            for transfer in obj.generated_transfers.all():
                if hasattr(transfer, 'transferbatch_set') and transfer.transferbatch_set.filter(used_in_bank=True).exists():
                    has_used_batch = True
                    break
            
            if has_used_batch:
                # Transfer has batch marked as used in bank - PAID_SYSTEM (highest priority)
                return {
                    'status': 'PAID_SYSTEM', 
                    'label': 'Kifizetve (Bankba átadva)',
                    'icon': 'check_circle',
                    'class': 'status-paid-system'
                }
            else:
                # Has transfer but no used batch - PREPARED (overrides manual PAID status)
                return {
                    'status': 'PREPARED',
                    'label': 'Előkészítve',
                    'icon': 'upload',
                    'class': 'status-prepared'
                }
        
        # PRIORITY 2: No transfer exists, check database payment_status
        if obj.payment_status == 'UNPAID':
            # Check if overdue
            if obj.payment_due_date and obj.payment_due_date < timezone.now().date():
                return {
                    'status': 'OVERDUE',
                    'label': 'Lejárt',
                    'icon': 'warning',
                    'class': 'status-overdue'
                }
            else:
                return {
                    'status': 'UNPAID',
                    'label': 'Fizetésre vár',
                    'icon': 'schedule',
                    'class': 'status-unpaid'
                }
        elif obj.payment_status == 'PREPARED':
            return {
                'status': 'PREPARED',
                'label': 'Előkészítve',
                'icon': 'upload',
                'class': 'status-prepared'
            }
        elif obj.payment_status == 'PAID':
            # No transfer exists, but marked as PAID - check if trusted partner or manual
            if obj.auto_marked_paid:
                # Auto-marked as paid by trusted partner
                return {
                    'status': 'PAID_TRUSTED',
                    'label': 'Kifizetve (Automatikus)',
                    'icon': 'check_circle',
                    'class': 'status-paid-trusted'
                }
            else:
                # Manually marked as paid
                return {
                    'status': 'PAID_MANUAL',
                    'label': 'Kifizetve (Manuálisan)',
                    'icon': 'check_circle',
                    'class': 'status-paid-manual'
                }
        
        return {
            'status': 'UNKNOWN',
            'label': 'Ismeretlen',
            'icon': 'help',
            'class': 'status-unknown'
        }
    
    def get_payment_status_date_formatted(self, obj):
        if obj.payment_status_date:
            return obj.payment_status_date.strftime('%Y-%m-%d')
        return None


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


class TrustedPartnerSerializer(serializers.ModelSerializer):
    """Serializer for TrustedPartner model with validation."""
    
    # Add read-only formatted fields
    last_invoice_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = TrustedPartner
        fields = [
            'id', 'partner_name', 'tax_number', 'is_active', 'auto_pay', 'notes',
            'invoice_count', 'last_invoice_date', 'last_invoice_date_formatted',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['invoice_count', 'last_invoice_date', 'created_at', 'updated_at']
    
    def get_last_invoice_date_formatted(self, obj):
        """Format the last invoice date for display"""
        if obj.last_invoice_date:
            return obj.last_invoice_date.strftime('%Y-%m-%d')
        return 'Nincs számla'
    
    def validate_tax_number(self, value):
        """Validate tax number format (Hungarian format)"""
        if value and not value.replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError('Az adószám csak számokat tartalmazhat')
        return value
    
    def validate(self, data):
        """Custom validation for unique partner per company"""
        request = self.context.get('request')
        if request and hasattr(request, 'company'):
            company = request.company
            tax_number = data.get('tax_number')
            
            # Check for duplicate tax number in the same company
            if tax_number:
                queryset = TrustedPartner.objects.filter(
                    company=company,
                    tax_number=tax_number
                )
                
                # Exclude current instance during updates
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                
                if queryset.exists():
                    raise serializers.ValidationError({
                        'tax_number': 'Ez az adószám már szerepel a megbízható partnerek között'
                    })
        
        return data
