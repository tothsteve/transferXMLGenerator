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
    FeatureTemplate, CompanyFeature, Company, CompanyUser, UserProfile
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
