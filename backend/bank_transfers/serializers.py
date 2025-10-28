from rest_framework import serializers
from decimal import Decimal
from .models import (
    BankAccount, Beneficiary, TransferTemplate, TemplateBeneficiary, Transfer, TransferBatch, Company,
    NavConfiguration, Invoice, InvoiceLineItem, InvoiceSyncLog, TrustedPartner,
    ExchangeRate, ExchangeRateSyncLog,
    BankStatement, BankTransaction, OtherCost,
    CompanyBillingoSettings, BillingoInvoice, BillingoInvoiceItem, BillingoSyncLog, BillingoSpending,
    SupplierCategory, SupplierType, Supplier, Customer, ProductPrice
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
            'id', 'name', 'account_number', 'vat_number', 'tax_number', 'description',
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

    def validate_tax_number(self, value):
        """Validate Hungarian company tax number format"""
        if not value:
            return value

        # Clean the tax number (remove spaces and dashes)
        clean_tax = value.replace(' ', '').replace('-', '')

        # Validate format: exactly 8 digits
        if not clean_tax.isdigit() or len(clean_tax) != 8:
            raise serializers.ValidationError(
                "Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)"
            )

        # Return the cleaned tax number
        return clean_tax

    def validate(self, data):
        """Validate that at least one identifier is provided"""
        account_number = data.get('account_number')
        vat_number = data.get('vat_number')
        tax_number = data.get('tax_number')

        if not account_number and not vat_number and not tax_number:
            raise serializers.ValidationError(
                "Meg kell adni a számlaszámot, adóazonosító jelet vagy céges adószámot"
            )

        return data

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


# Exchange Rate Serializers

class ExchangeRateSerializer(serializers.ModelSerializer):
    """
    Serializer for ExchangeRate model.
    Provides exchange rate data with formatted output.
    """
    rate_display = serializers.SerializerMethodField()
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)

    class Meta:
        model = ExchangeRate
        fields = [
            'id',
            'rate_date',
            'currency',
            'currency_display',
            'rate',
            'rate_display',
            'unit',
            'sync_date',
            'source',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'sync_date',
            'created_at',
            'updated_at'
        ]

    def get_rate_display(self, obj):
        """Format rate with 4 decimal places for display"""
        return f"{obj.rate:.4f} HUF"


class ExchangeRateSyncLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ExchangeRateSyncLog model.
    Provides sync history and statistics.
    """
    duration_seconds = serializers.ReadOnlyField()
    total_rates_processed = serializers.ReadOnlyField()
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)

    class Meta:
        model = ExchangeRateSyncLog
        fields = [
            'id',
            'sync_start_time',
            'sync_end_time',
            'duration_seconds',
            'currencies_synced',
            'date_range_start',
            'date_range_end',
            'rates_created',
            'rates_updated',
            'total_rates_processed',
            'sync_status',
            'sync_status_display',
            'error_message',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'sync_start_time',
            'sync_end_time',
            'duration_seconds',
            'total_rates_processed',
            'created_at'
        ]


class ExchangeRateListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for exchange rate lists.
    Used for compact API responses.
    """
    class Meta:
        model = ExchangeRate
        fields = [
            'rate_date',
            'currency',
            'rate',
            'sync_date'
        ]


class CurrentRatesSerializer(serializers.Serializer):
    """
    Serializer for current exchange rates endpoint response.
    """
    USD = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True)
    EUR = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True)
    last_sync = serializers.DateTimeField(allow_null=True)
    rate_date = serializers.DateField(allow_null=True)


class ExchangeRateHistorySerializer(serializers.Serializer):
    """
    Serializer for exchange rate history endpoint response.
    Used for charting and analysis.
    """
    date = serializers.DateField()
    rate = serializers.DecimalField(max_digits=12, decimal_places=6)


class CurrencyConversionSerializer(serializers.Serializer):
    """
    Serializer for currency conversion requests and responses.
    """
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    currency = serializers.ChoiceField(choices=['USD', 'EUR'], required=True)
    conversion_date = serializers.DateField(required=False, allow_null=True)

    # Response fields
    huf_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    exchange_rate = serializers.DecimalField(max_digits=12, decimal_places=6, read_only=True)
    rate_date = serializers.DateField(read_only=True)

# =============================================================================
# Bank Statement Import Serializers
# =============================================================================

class BankTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for bank transaction records.

    Provides full transaction details with nested invoice match information.
    """
    statement_details = serializers.SerializerMethodField()
    matched_invoice_details = serializers.SerializerMethodField()
    matched_transfer_batch = serializers.SerializerMethodField()
    matched_reimbursement_details = serializers.SerializerMethodField()
    has_other_cost = serializers.SerializerMethodField()

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
            'matched_transfer', 'matched_transfer_batch',
            'matched_reimbursement', 'matched_reimbursement_details',
            'has_other_cost',
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
        """Return matched invoice summary"""
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
        read_only_fields = ['created_at', 'updated_at', 'company']
    
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


# ============================================================================
# Billingo Integration Serializers
# ============================================================================

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


class BillingoInvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Billingo invoices.

    Read-only serializer as invoices are synced from Billingo API.
    Includes nested invoice items.
    """
    items = BillingoInvoiceItemSerializer(many=True, read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    # Formatted display fields
    gross_total_formatted = serializers.SerializerMethodField()
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
            'currency', 'conversion_rate',

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

            # Nested items
            'items',

            # Metadata
            'created_at', 'updated_at', 'last_modified'
        ]
        read_only_fields = fields  # All fields are read-only (synced from API)

    def get_gross_total_formatted(self, obj):
        """Format gross total with currency"""
        return f"{obj.gross_total:,.2f} {obj.currency}"

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

    class Meta:
        model = BillingoInvoice
        fields = [
            'id', 'company', 'company_name', 'invoice_number', 'type',
            'payment_status', 'payment_method', 'gross_total', 'gross_total_formatted',
            'currency', 'invoice_date', 'invoice_date_formatted',
            'due_date', 'paid_date', 'partner_name', 'partner_tax_number',
            'cancelled', 'item_count', 'created_at'
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


# ============================================================================
# BASE_TABLES Serializers - Alaptáblák (Suppliers, Customers, Product Prices)
# ============================================================================

class SupplierCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for SupplierCategory (Beszállító kategória) model.

    Provides CRUD operations for supplier cost categories.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = SupplierCategory
        fields = [
            'id', 'company', 'company_name', 'name', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate category name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A kategória neve kötelező.")
        return value.strip()


class SupplierTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for SupplierType (Beszállító típus) model.

    Provides CRUD operations for supplier cost subcategories.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = SupplierType
        fields = [
            'id', 'company', 'company_name', 'name', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate type name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A típus neve kötelező.")
        return value.strip()


class SupplierSerializer(serializers.ModelSerializer):
    """
    Serializer for Supplier (Beszállító) model.

    Provides CRUD operations with company auto-assignment and validity period support.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    type_name = serializers.CharField(source='type.name', read_only=True, allow_null=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'company', 'company_name', 'partner_name',
            'category', 'category_name', 'type', 'type_name',
            'valid_from', 'valid_to', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'category_name', 'type_name', 'created_at', 'updated_at']

    def get_is_valid(self, obj):
        """Check if supplier record is currently valid"""
        return obj.is_valid()

    def validate_partner_name(self, value):
        """Validate partner name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A partner neve kötelező.")
        return value.strip()

    def validate(self, data):
        """Validate validity period"""
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({
                'valid_to': 'Az érvényesség vége nem lehet korábbi, mint a kezdete.'
            })

        return data


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer (Vevő) model.

    Provides CRUD operations with company auto-assignment and cashflow adjustment support.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'company', 'company_name', 'customer_name', 'cashflow_adjustment',
            'valid_from', 'valid_to', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def get_is_valid(self, obj):
        """Check if customer record is currently valid"""
        return obj.is_valid()

    def validate_customer_name(self, value):
        """Validate customer name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A vevő neve kötelező.")
        return value.strip()

    def validate(self, data):
        """Validate validity period"""
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({
                'valid_to': 'Az érvényesség vége nem lehet korábbi, mint a kezdete.'
            })

        return data


class ProductPriceSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductPrice (CONMED árak) model.

    Provides CRUD operations for product pricing with USD/HUF support and validity periods.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = ProductPrice
        fields = [
            'id', 'company', 'company_name',
            'product_value', 'product_description',
            'uom', 'uom_hun',
            'purchase_price_usd', 'purchase_price_huf',
            'markup', 'sales_price_huf',
            'cap_disp', 'is_inventory_managed',
            'valid_from', 'valid_to', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'company_name', 'created_at', 'updated_at']

    def get_is_valid(self, obj):
        """Check if product price record is currently valid"""
        return obj.is_valid()

    def validate_product_value(self, value):
        """Validate product code is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A termék kód kötelező.")
        return value.strip()

    def validate_product_description(self, value):
        """Validate product description is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("A termék leírás kötelező.")
        return value.strip()

    def validate(self, data):
        """Validate validity period and pricing logic"""
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({
                'valid_to': 'Az érvényesség vége nem lehet korábbi, mint a kezdete.'
            })

        return data


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
