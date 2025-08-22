from django.apps import AppConfig

class BankTransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_transfers'
    verbose_name = 'Bank Utalások'

# bank_transfers/admin.py
from django.contrib import admin
from .models import (
    BankAccount, Beneficiary, Transfer, TransferTemplate, TransferBatch,
    NavConfiguration, Invoice, InvoiceLineItem, InvoiceSyncLog
)

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_number', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'account_number']

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_number', 'description', 'is_frequent', 'created_at']
    list_filter = ['is_frequent', 'created_at']
    search_fields = ['name', 'account_number', 'description']

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['beneficiary', 'amount', 'currency', 'execution_date', 'created_at']
    list_filter = ['currency', 'execution_date', 'created_at']
    search_fields = ['beneficiary__name', 'remittance_info']
    date_hierarchy = 'execution_date'

@admin.register(TransferTemplate)
class TransferTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']

@admin.register(TransferBatch)
class TransferBatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'xml_generated_at']
    filter_horizontal = ['transfers']


# NAV Invoice Synchronization Admin

@admin.register(NavConfiguration)
class NavConfigurationAdmin(admin.ModelAdmin):
    list_display = ['company', 'tax_number', 'api_environment', 'sync_enabled', 'is_active', 'last_sync_timestamp']
    list_filter = ['api_environment', 'sync_enabled', 'is_active', 'created_at']
    search_fields = ['company__name', 'tax_number', 'technical_user_login']
    readonly_fields = ['created_at', 'updated_at', 'last_sync_timestamp']
    
    fieldsets = (
        ('Cég információk', {
            'fields': ('company', 'tax_number')
        }),
        ('NAV API adatok', {
            'fields': ('technical_user_login', 'technical_user_password', 'signing_key', 'exchange_key'),
            'description': 'Adja meg a NAV API adatokat sima szövegként. Az adatok automatikusan titkosítva lesznek mentéskor.'
        }),
        ('Tanúsítvány beállítások', {
            'fields': ('client_certificate', 'certificate_password'),
            'description': 'Töltse fel a NAV kliens tanúsítványt (.p12/.pfx) ha szükséges. A tanúsítvány jelszó automatikusan titkosítva lesz.',
            'classes': ('collapse',)
        }),
        ('Automatikus kulcsok', {
            'fields': ('company_encryption_key',),
            'description': 'Ez a kulcs automatikusan generálódik és titkosítva tárolódik.',
            'classes': ('collapse',)
        }),
        ('Beállítások', {
            'fields': ('api_environment', 'is_active', 'sync_enabled', 'sync_frequency_hours')
        }),
        ('Státusz', {
            'fields': ('last_sync_timestamp', 'created_at', 'updated_at')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['nav_invoice_number', 'company', 'invoice_direction', 'supplier_name', 'customer_name', 
                   'invoice_gross_amount', 'currency_code', 'issue_date', 'sync_status']
    list_filter = ['invoice_direction', 'currency_code', 'sync_status', 'issue_date', 'created_at']
    search_fields = ['nav_invoice_number', 'supplier_name', 'customer_name', 'supplier_tax_number', 'customer_tax_number']
    date_hierarchy = 'issue_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Számla alapadatok', {
            'fields': ('company', 'nav_invoice_number', 'invoice_direction')
        }),
        ('Felek adatai', {
            'fields': ('supplier_name', 'supplier_tax_number', 'customer_name', 'customer_tax_number')
        }),
        ('Dátumok', {
            'fields': ('issue_date', 'fulfillment_date', 'payment_due_date')
        }),
        ('Pénzügyi adatok', {
            'fields': ('currency_code', 'invoice_net_amount', 'invoice_vat_amount', 'invoice_gross_amount')
        }),
        ('NAV metaadatok', {
            'fields': ('original_request_version', 'completion_date', 'source', 'nav_transaction_id', 'last_modified_date')
        }),
        ('Szinkronizáció', {
            'fields': ('sync_status', 'created_at', 'updated_at')
        }),
    )


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0
    readonly_fields = ['created_at']


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'line_number', 'line_description', 'quantity', 'unit_price', 
                   'line_gross_amount', 'vat_rate']
    list_filter = ['vat_rate', 'unit_of_measure', 'created_at']
    search_fields = ['invoice__nav_invoice_number', 'line_description', 'product_code_value']
    readonly_fields = ['created_at']


@admin.register(InvoiceSyncLog)
class InvoiceSyncLogAdmin(admin.ModelAdmin):
    list_display = ['company', 'sync_start_time', 'sync_end_time', 'direction_synced', 
                   'invoices_processed', 'invoices_created', 'sync_status']
    list_filter = ['sync_status', 'direction_synced', 'sync_start_time']
    search_fields = ['company__name', 'last_error_message']
    readonly_fields = ['created_at']
    date_hierarchy = 'sync_start_time'
