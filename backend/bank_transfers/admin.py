from django.apps import AppConfig

class BankTransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_transfers'
    verbose_name = 'Bank Utalások'

# bank_transfers/admin.py
from django.contrib import admin
from .models import (
    BankAccount, Beneficiary, Transfer, TransferTemplate, TransferBatch,
    NavConfiguration, Invoice, InvoiceLineItem, InvoiceSyncLog,
    FeatureTemplate, CompanyFeature, Company, CompanyUser, UserProfile,
    ExchangeRate, ExchangeRateSyncLog,
    BankStatement, BankTransaction, OtherCost
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
    list_display = ['company', 'tax_number', 'technical_user_login', 'api_environment', 'sync_enabled', 'is_active']
    list_filter = ['api_environment', 'sync_enabled', 'is_active', 'created_at']
    search_fields = ['company__name', 'tax_number', 'technical_user_login']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Cég információk', {
            'fields': ('company', 'tax_number')
        }),
        ('NAV API adatok', {
            'fields': ('technical_user_login', 'technical_user_password', 'signing_key', 'exchange_key'),
            'description': 'Adja meg a NAV API adatokat sima szövegként. Az adatok automatikusan titkosítva lesznek mentéskor.'
        }),
        ('Automatikus kulcsok', {
            'fields': ('company_encryption_key',),
            'description': 'Ez a kulcs automatikusan generálódik és titkosítva tárolódik.',
            'classes': ('collapse',)
        }),
        ('Beállítások', {
            'fields': ('api_environment', 'is_active', 'sync_enabled')
        }),
        ('Státusz', {
            'fields': ('created_at', 'updated_at')
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


# Feature Management Admin

@admin.register(FeatureTemplate)
class FeatureTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for managing feature templates.
    Defines the catalog of available features across the system.
    """
    list_display = ['feature_code', 'display_name', 'category', 'default_enabled', 'is_system_critical', 'company_count', 'created_at']
    list_filter = ['category', 'default_enabled', 'is_system_critical', 'created_at']
    search_fields = ['feature_code', 'display_name', 'description']
    ordering = ['category', 'display_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('feature_code', 'display_name', 'description'),
            'description': 'Core feature identification and description'
        }),
        ('Configuration', {
            'fields': ('category', 'default_enabled', 'is_system_critical'),
            'description': 'Feature categorization and default behavior'
        }),
        ('Advanced Schema', {
            'fields': ('config_schema',),
            'classes': ('collapse',),
            'description': 'JSON schema for feature-specific configuration validation'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with company feature counts"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('company_instances')
    
    def company_count(self, obj):
        """Show how many companies have this feature enabled"""
        return obj.company_instances.filter(is_enabled=True).count()
    company_count.short_description = 'Companies Using'


@admin.register(CompanyFeature)
class CompanyFeatureAdmin(admin.ModelAdmin):
    """
    Admin interface for managing company-specific feature enablement.
    Allows enabling/disabling features per company with detailed tracking.
    """
    list_display = ['company', 'feature_code_display', 'feature_category', 'is_enabled', 'enabled_at', 'enabled_by']
    list_filter = ['is_enabled', 'feature_template__category', 'feature_template__is_system_critical', 'enabled_at']
    search_fields = ['company__name', 'feature_template__feature_code', 'feature_template__display_name']
    raw_id_fields = ['company', 'enabled_by']
    ordering = ['company__name', 'feature_template__category', 'feature_template__display_name']
    
    fieldsets = (
        ('Company & Feature', {
            'fields': ('company', 'feature_template'),
            'description': 'Select the company and feature template'
        }),
        ('Status', {
            'fields': ('is_enabled',),
            'description': 'Enable or disable this feature for the company'
        }),
        ('Configuration', {
            'fields': ('config_data',),
            'classes': ('collapse',),
            'description': 'Company-specific JSON configuration for this feature'
        }),
        ('Tracking', {
            'fields': ('enabled_at', 'enabled_by'),
            'classes': ('collapse',),
            'description': 'Automatic tracking of when and by whom feature was enabled'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['enabled_at', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with related objects"""
        qs = super().get_queryset(request)
        return qs.select_related('company', 'feature_template', 'enabled_by')
    
    def feature_code_display(self, obj):
        """Display the feature code from the template"""
        return obj.feature_template.feature_code
    feature_code_display.short_description = 'Feature Code'
    feature_code_display.admin_order_field = 'feature_template__feature_code'
    
    def feature_category(self, obj):
        """Display the feature category"""
        return obj.feature_template.get_category_display()
    feature_category.short_description = 'Category'
    feature_category.admin_order_field = 'feature_template__category'
    
    def feature_is_system_critical(self, obj):
        """Show if feature is system critical"""
        return obj.feature_template.is_system_critical
    feature_is_system_critical.short_description = 'Critical'
    feature_is_system_critical.boolean = True
    feature_is_system_critical.admin_order_field = 'feature_template__is_system_critical'
    
    # Bulk actions
    actions = ['enable_features', 'disable_features', 'reset_feature_config']
    
    def enable_features(self, request, queryset):
        """Bulk enable selected features"""
        updated = queryset.filter(feature_template__is_system_critical=False).update(
            is_enabled=True
        )
        self.message_user(request, f'{updated} features enabled.')
        
        # Count system critical features that couldn't be modified
        critical_count = queryset.filter(feature_template__is_system_critical=True).count()
        if critical_count > 0:
            self.message_user(
                request, 
                f'{critical_count} system critical features were not modified.', 
                level='WARNING'
            )
    enable_features.short_description = "Enable selected features"
    
    def disable_features(self, request, queryset):
        """Bulk disable selected features (except system critical)"""
        # Don't allow disabling system critical features
        critical_features = queryset.filter(feature_template__is_system_critical=True)
        if critical_features.exists():
            critical_names = ', '.join([f.feature_template.feature_code for f in critical_features[:5]])
            self.message_user(
                request, 
                f"Cannot disable system critical features: {critical_names}{'...' if critical_features.count() > 5 else ''}", 
                level='ERROR'
            )
            return
        
        updated = queryset.update(is_enabled=False, enabled_at=None)
        self.message_user(request, f'{updated} features disabled.')
    disable_features.short_description = "Disable selected features"
    
    def reset_feature_config(self, request, queryset):
        """Reset configuration data for selected features"""
        updated = queryset.update(config_data=None)
        self.message_user(request, f'Configuration reset for {updated} features.')
    reset_feature_config.short_description = "Reset feature configuration"
    
    def save_model(self, request, obj, form, change):
        """Set enabled_by when enabling a feature"""
        if obj.is_enabled and not obj.enabled_by:
            obj.enabled_by = request.user
        super().save_model(request, obj, form, change)


# Enhanced Company Admin with Feature Overview
class CompanyFeatureInline(admin.TabularInline):
    """Inline for managing company features directly from Company admin"""
    model = CompanyFeature
    extra = 0
    fields = ['feature_template', 'is_enabled', 'enabled_at', 'enabled_by']
    readonly_fields = ['enabled_at', 'enabled_by']
    raw_id_fields = ['enabled_by']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('feature_template', 'enabled_by')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Enhanced Company admin with feature management capabilities"""
    list_display = ['name', 'tax_id', 'feature_count', 'user_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'tax_id']
    inlines = [CompanyFeatureInline]
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'tax_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('features', 'users')
    
    def feature_count(self, obj):
        """Show count of enabled features"""
        enabled_count = obj.features.filter(is_enabled=True).count()
        total_count = obj.features.count()
        return f"{enabled_count}/{total_count}"
    feature_count.short_description = 'Features (Enabled/Total)'
    
    def user_count(self, obj):
        """Show count of active users"""
        return obj.users.filter(is_active=True).count()
    user_count.short_description = 'Active Users'
    
    actions = ['initialize_default_features']
    
    def initialize_default_features(self, request, queryset):
        """Initialize default features for selected companies"""
        from .models import CompanyFeatureManager
        
        total_features_created = 0
        for company in queryset:
            created_features = CompanyFeatureManager.initialize_company_features(
                company, user=request.user
            )
            total_features_created += len(created_features)
        
        self.message_user(
            request, 
            f'Initialized {total_features_created} default features for {queryset.count()} companies.'
        )
    initialize_default_features.short_description = "Initialize default features"


# Enhanced CompanyUser Admin with Permission Overview
@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    """Enhanced CompanyUser admin with role and permission management"""
    list_display = ['user', 'company', 'role', 'feature_access_summary', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at', 'company']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'company__name']
    raw_id_fields = ['user', 'company']
    
    fieldsets = (
        ('User & Company', {
            'fields': ('user', 'company', 'role')
        }),
        ('Status', {
            'fields': ('is_active', 'joined_at')
        }),
        ('Custom Permissions', {
            'fields': ('custom_permissions', 'permission_restrictions'),
            'classes': ('collapse',),
            'description': 'Override default role permissions with custom access rules'
        }),
    )
    
    readonly_fields = ['joined_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'company')
    
    def feature_access_summary(self, obj):
        """Show summary of user's feature access"""
        allowed_features = obj.get_allowed_features()
        
        if '*' in allowed_features:
            return "All Features (Admin)"
        
        feature_count = len([f for f in allowed_features if not f.endswith('*')])
        wildcard_count = len([f for f in allowed_features if f.endswith('*')])
        
        summary = f"{feature_count} features"
        if wildcard_count:
            summary += f", {wildcard_count} wildcards"
        
        return summary
    feature_access_summary.short_description = 'Feature Access'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for user profiles"""
    list_display = ['user', 'user_full_name', 'phone', 'preferred_language', 'last_active_company', 'user_email']
    list_filter = ['preferred_language', 'timezone', 'last_active_company']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    raw_id_fields = ['user', 'last_active_company']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Settings', {
            'fields': ('phone', 'preferred_language', 'timezone')
        }),
        ('Company Settings', {
            'fields': ('last_active_company',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'last_active_company')
    
    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'Full Name'
    user_full_name.admin_order_field = 'user__first_name'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'


# MNB Exchange Rate Admin

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """
    Admin interface for MNB Exchange Rates.
    Provides read-only view with filtering and search capabilities.
    """
    list_display = ['rate_date', 'currency', 'rate', 'unit', 'rate_display', 'sync_date', 'source']
    list_filter = ['currency', 'source', 'rate_date', 'sync_date']
    search_fields = ['currency']
    date_hierarchy = 'rate_date'
    ordering = ['-rate_date', 'currency']

    # Make all fields read-only (rates should only be updated via sync)
    readonly_fields = ['rate_date', 'currency', 'rate', 'unit', 'sync_date', 'source', 'created_at', 'updated_at']

    fieldsets = (
        ('Árfolyam adatok', {
            'fields': ('rate_date', 'currency', 'rate', 'unit')
        }),
        ('Szinkronizáció', {
            'fields': ('source', 'sync_date')
        }),
        ('Időbélyegek', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rate_display(self, obj):
        """Display formatted exchange rate"""
        return f"{obj.rate:.4f} HUF"
    rate_display.short_description = 'Árfolyam (formázott)'

    def has_add_permission(self, request):
        """Disable manual creation (only via sync)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable manual deletion"""
        return request.user.is_superuser


@admin.register(ExchangeRateSyncLog)
class ExchangeRateSyncLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Exchange Rate Sync Logs.
    Provides audit trail and troubleshooting capabilities.
    """
    list_display = ['sync_start_time', 'date_range_display', 'currencies_synced',
                   'rates_created', 'rates_updated', 'total_rates_processed',
                   'duration_seconds', 'sync_status']
    list_filter = ['sync_status', 'currencies_synced', 'sync_start_time']
    search_fields = ['currencies_synced', 'error_message']
    date_hierarchy = 'sync_start_time'
    ordering = ['-sync_start_time']

    readonly_fields = ['sync_start_time', 'sync_end_time', 'currencies_synced',
                      'date_range_start', 'date_range_end', 'rates_created',
                      'rates_updated', 'total_rates_processed', 'duration_seconds',
                      'sync_status', 'error_message', 'created_at', 'updated_at']

    fieldsets = (
        ('Szinkronizáció időpontja', {
            'fields': ('sync_start_time', 'sync_end_time', 'duration_seconds')
        }),
        ('Szinkronizált adatok', {
            'fields': ('currencies_synced', 'date_range_start', 'date_range_end')
        }),
        ('Eredmények', {
            'fields': ('sync_status', 'rates_created', 'rates_updated', 'total_rates_processed')
        }),
        ('Hibák', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Időbélyegek', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def date_range_display(self, obj):
        """Display date range in compact format"""
        if obj.date_range_start == obj.date_range_end:
            return f"{obj.date_range_start}"
        return f"{obj.date_range_start} - {obj.date_range_end}"
    date_range_display.short_description = 'Dátum tartomány'

    def duration_seconds(self, obj):
        """Calculate and display sync duration"""
        if obj.sync_end_time and obj.sync_start_time:
            duration = (obj.sync_end_time - obj.sync_start_time).total_seconds()
            return f"{duration:.2f}s"
        return "N/A"
    duration_seconds.short_description = 'Időtartam'

    def total_rates_processed(self, obj):
        """Show total rates processed"""
        return obj.rates_created + obj.rates_updated
    total_rates_processed.short_description = 'Összes feldolgozott'

    def has_add_permission(self, request):
        """Disable manual creation (only via sync)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete logs"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Make logs read-only"""
        return False

# =============================================================================
# Bank Statement Import Admin
# =============================================================================

@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    """
    Admin interface for bank statements.
    
    Provides read-only view of uploaded PDF statements with filtering and search.
    """
    list_display = [
        'id', 'company', 'bank_name', 'account_number', 'statement_period_display',
        'total_transactions', 'matched_count', 'status', 'uploaded_at', 'uploaded_by'
    ]
    list_filter = ['status', 'bank_code', 'uploaded_at']
    search_fields = ['account_number', 'account_iban', 'statement_number', 'file_name']
    readonly_fields = [
        'company', 'bank_code', 'bank_name', 'bank_bic',
        'account_number', 'account_iban',
        'statement_period_from', 'statement_period_to', 'statement_number',
        'opening_balance', 'closing_balance',
        'file_name', 'file_hash', 'file_size', 'file_path',
        'uploaded_by', 'uploaded_at',
        'status', 'parse_error', 'parse_warnings', 'raw_metadata',
        'total_transactions', 'credit_count', 'debit_count', 'total_credits', 'total_debits', 'matched_count',
        'created_at', 'updated_at'
    ]
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    def statement_period_display(self, obj):
        """Display statement period"""
        return f"{obj.statement_period_from} - {obj.statement_period_to}"
    statement_period_display.short_description = 'Időszak'
    
    def has_add_permission(self, request):
        """Disable manual creation (only via PDF upload)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete statements"""
        return request.user.is_superuser


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for bank transactions.
    
    Provides read-only view of parsed transactions with filtering and search.
    """
    list_display = [
        'id', 'company', 'transaction_type', 'booking_date', 'amount_display',
        'description_short', 'matched_invoice', 'match_confidence'
    ]
    list_filter = ['transaction_type', 'booking_date', 'currency', 'is_extra_cost', 'extra_cost_category']
    search_fields = [
        'description', 'payer_name', 'beneficiary_name', 'reference',
        'payment_id', 'merchant_name'
    ]
    readonly_fields = [
        'company', 'bank_statement',
        'transaction_type', 'booking_date', 'value_date',
        'amount', 'currency', 'description', 'short_description',
        'payment_id', 'transaction_id',
        'payer_name', 'payer_iban', 'payer_account_number', 'payer_bic',
        'beneficiary_name', 'beneficiary_iban', 'beneficiary_account_number',
        'reference',
        'card_number', 'merchant_name', 'merchant_location',
        'original_amount', 'original_currency',
        'matched_invoice', 'match_confidence', 'match_method', 'match_notes', 'matched_by', 'matched_at',
        'is_extra_cost', 'extra_cost_category', 'raw_data',
        'created_at', 'updated_at'
    ]
    ordering = ['-booking_date']
    date_hierarchy = 'booking_date'
    
    fieldsets = (
        ('Alapadatok', {
            'fields': ('company', 'bank_statement', 'transaction_type', 'booking_date', 'value_date')
        }),
        ('Összeg', {
            'fields': ('amount', 'currency', 'original_amount', 'original_currency')
        }),
        ('Leírás', {
            'fields': ('description', 'short_description', 'reference')
        }),
        ('Fizető fél', {
            'fields': ('payer_name', 'payer_iban', 'payer_account_number', 'payer_bic')
        }),
        ('Kedvezményezett', {
            'fields': ('beneficiary_name', 'beneficiary_iban', 'beneficiary_account_number')
        }),
        ('Tranzakció azonosítók', {
            'fields': ('payment_id', 'transaction_id')
        }),
        ('Kártyás adatok', {
            'fields': ('card_number', 'merchant_name', 'merchant_location')
        }),
        ('Számla párosítás', {
            'fields': ('matched_invoice', 'match_confidence', 'match_method', 'match_notes', 'matched_by', 'matched_at')
        }),
        ('Egyéb költség', {
            'fields': ('is_extra_cost', 'extra_cost_category')
        }),
        ('Nyers adat', {
            'fields': ('raw_data',)
        }),
        ('Metaadatok', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def amount_display(self, obj):
        """Display amount with currency"""
        return f"{obj.amount:,.2f} {obj.currency}"
    amount_display.short_description = 'Összeg'
    
    def description_short(self, obj):
        """Truncated description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Leírás'
    
    def has_add_permission(self, request):
        """Disable manual creation (only via PDF parsing)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete transactions"""
        return request.user.is_superuser


@admin.register(OtherCost)
class OtherCostAdmin(admin.ModelAdmin):
    """
    Admin interface for other costs.
    
    Allows categorization and tagging of expenses for cost tracking.
    """
    list_display = [
        'id', 'company', 'category', 'date', 'amount_display',
        'description_short', 'bank_transaction', 'created_by'
    ]
    list_filter = ['category', 'date', 'currency']
    search_fields = ['description', 'notes']
    readonly_fields = ['company', 'created_at', 'updated_at']
    ordering = ['-date']
    date_hierarchy = 'date'
    
    fields = [
        'company', 'bank_transaction', 'category',
        'amount', 'currency', 'date',
        'description', 'notes', 'tags',
        'created_by', 'created_at', 'updated_at'
    ]
    
    def amount_display(self, obj):
        """Display amount with currency"""
        return f"{obj.amount:,.2f} {obj.currency}"
    amount_display.short_description = 'Összeg'
    
    def description_short(self, obj):
        """Truncated description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Leírás'
