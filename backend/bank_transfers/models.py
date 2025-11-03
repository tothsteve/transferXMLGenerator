from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date
from .base_models import (
    TimestampedModel, ActiveModel, TimestampedActiveModel,
    CompanyOwnedModel, CompanyOwnedTimestampedModel, CompanyOwnedTimestampedActiveModel
)

class Company(TimestampedActiveModel):
    """Cég entitás multi-tenant architektúrához"""
    name = models.CharField(max_length=200, verbose_name="Cég neve")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="Adószám")
    
    class Meta:
        verbose_name = "Cég"
        verbose_name_plural = "Cégek"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CompanyUser(ActiveModel):
    """
    Felhasználó-cég kapcsolat szerepkörrel és feature-alapú jogosultságokkal.
    Combines user roles with feature-level permissions for granular access control.
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Cég adminisztrátor'),
        ('FINANCIAL', 'Pénzügyi munkatárs'),
        ('ACCOUNTANT', 'Könyvelő'),
        ('USER', 'Alapfelhasználó'),
    ]
    
    # Define role-based feature permissions
    ROLE_PERMISSIONS = {
        'ADMIN': ['*'],  # All features - admin has unrestricted access
        'FINANCIAL': [
            'BENEFICIARY_MANAGEMENT',
            'TRANSFER_MANAGEMENT', 
            'BATCH_MANAGEMENT',
            'EXPORT_XML_SEPA',
            'EXPORT_CSV_KH',
            'EXPENSE_TRACKING',
        ],
        'ACCOUNTANT': [
            'NAV_SYNC',
            'INVOICE_MANAGEMENT',
            'EXPENSE_TRACKING',
            'REPORTING',
            'BENEFICIARY_MANAGEMENT',
            'TRANSFER_MANAGEMENT',
            'MULTI_CURRENCY',
        ],
        'USER': [
            'BENEFICIARY_VIEW',
            'TRANSFER_VIEW',
            'BATCH_VIEW',
        ],
    }
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='USER', verbose_name="Szerepkör")
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # Additional permission fields
    custom_permissions = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Egyedi jogosultságok",
        help_text="JSON array of additional feature codes this user can access beyond their role"
    )
    permission_restrictions = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Jogosultság korlátozások", 
        help_text="JSON array of feature codes this user is explicitly denied access to"
    )
    
    class Meta:
        verbose_name = "Cég felhasználó"
        verbose_name_plural = "Cég felhasználók"
        unique_together = ['user', 'company']
        ordering = ['company__name', 'user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['company', 'role']),
            models.Index(fields=['user', 'company']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.company.name} ({self.role})"
    
    def get_allowed_features(self):
        """
        Get all feature codes this user is allowed to access.
        Combines role permissions with custom permissions and restrictions.
        """
        # Start with role-based permissions
        role_perms = self.ROLE_PERMISSIONS.get(self.role, [])
        
        # Admin gets everything
        if '*' in role_perms:
            return ['*']
        
        allowed_features = set(role_perms)
        
        # Add custom permissions
        if self.custom_permissions:
            allowed_features.update(self.custom_permissions)
        
        # Remove explicit restrictions
        if self.permission_restrictions:
            allowed_features -= set(self.permission_restrictions)
        
        return list(allowed_features)
    
    def can_access_feature(self, feature_code):
        """
        Check if this user can access a specific feature.
        
        Args:
            feature_code: String feature code to check
            
        Returns:
            Boolean indicating access permission
        """
        allowed_features = self.get_allowed_features()
        
        # Admin access
        if '*' in allowed_features:
            return True
            
        # Direct feature access
        if feature_code in allowed_features:
            return True
            
        # Check for wildcard permissions (e.g., 'EXPORT_*' for all export features)
        for perm in allowed_features:
            if perm.endswith('*') and feature_code.startswith(perm[:-1]):
                return True
        
        return False

class UserProfile(TimestampedModel):
    """Felhasználói profil kiegészítő adatokkal"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    preferred_language = models.CharField(max_length=10, default='hu', verbose_name="Nyelv")
    timezone = models.CharField(max_length=50, default='Europe/Budapest', verbose_name="Időzóna")
    last_active_company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, 
                                          verbose_name="Utoljára aktív cég")
    
    class Meta:
        verbose_name = "Felhasználói profil"
        verbose_name_plural = "Felhasználói profilok"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} profil"

class BankAccount(CompanyOwnedTimestampedModel):
    name = models.CharField(max_length=200, verbose_name="Számla neve")
    account_number = models.CharField(max_length=50, verbose_name="Számlaszám")
    bank_name = models.CharField(max_length=200, blank=True, verbose_name="Bank neve")
    is_default = models.BooleanField(default=False, verbose_name="Alapértelmezett")
    
    class Meta:
        verbose_name = "Bank számla"
        verbose_name_plural = "Bank számlák"
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.account_number})"
    
    def clean_account_number(self):
        return self.account_number.replace('-', '').replace(' ', '')

class Beneficiary(CompanyOwnedTimestampedActiveModel):
    name = models.CharField(max_length=200, verbose_name="Kedvezményezett neve")
    account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Számlaszám")
    vat_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Adóazonosító jel",
                                help_text="Magyar személyi adóazonosító jel (pl. 8440961790)")
    tax_number = models.CharField(max_length=8, blank=True, null=True, verbose_name="Céges adószám",
                                help_text="Magyar céges adószám első 8 számjegye (pl. 12345678)")
    description = models.CharField(max_length=200, blank=True, verbose_name="Leírás",
                                 help_text="További információk a kedvezményezettről (bank neve, szervezet adatai, stb.)")
    is_frequent = models.BooleanField(default=False, verbose_name="Gyakori kedvezményezett")
    remittance_information = models.TextField(blank=True, verbose_name="Utalási információ",
                                            help_text="Alapértelmezett fizetési hivatkozások, számlaszámok vagy egyéb tranzakció-specifikus információk")
    
    class Meta:
        verbose_name = "Kedvezményezett"
        verbose_name_plural = "Kedvezményezettek"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_frequent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['vat_number']),
            models.Index(fields=['tax_number']),
        ]
    
    def __str__(self):
        identifier = self.account_number or self.vat_number or self.tax_number or "No identifier"
        return f"{self.name} ({identifier})"
    
    def clean_account_number(self):
        if not self.account_number:
            return None
        return self.account_number.replace('-', '').replace(' ', '')
    
    def clean(self):
        """Validate VAT number and tax number format"""
        from django.core.exceptions import ValidationError

        if self.vat_number:
            # Remove any spaces or dashes
            clean_vat = self.vat_number.replace(' ', '').replace('-', '')

            # Hungarian personal VAT number should be exactly 10 digits
            if not clean_vat.isdigit() or len(clean_vat) != 10:
                raise ValidationError({
                    'vat_number': 'Magyar személyi adóazonosító jel 10 számjegyből kell álljon (pl. 8440961790)'
                })

            # Store cleaned version
            self.vat_number = clean_vat

        if self.tax_number:
            # Remove any spaces or dashes
            clean_tax = self.tax_number.replace(' ', '').replace('-', '')

            # Hungarian company tax number should be exactly 8 digits
            if not clean_tax.isdigit() or len(clean_tax) != 8:
                raise ValidationError({
                    'tax_number': 'Magyar céges adószám 8 számjegyből kell álljon (pl. 12345678)'
                })

            # Store cleaned version
            self.tax_number = clean_tax

class TransferTemplate(CompanyOwnedTimestampedActiveModel):
    name = models.CharField(max_length=200, verbose_name="Sablon neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    
    class Meta:
        verbose_name = "Utalási sablon"
        verbose_name_plural = "Utalási sablonok"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TemplateBeneficiary(ActiveModel):
    template = models.ForeignKey(TransferTemplate, on_delete=models.CASCADE, related_name='template_beneficiaries')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    default_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    default_remittance = models.CharField(max_length=500, blank=True)
    default_execution_date = models.DateField(null=True, blank=True, verbose_name="Alapértelmezett teljesítési dátum")
    order = models.IntegerField(default=0, verbose_name="Sorrend")
    
    class Meta:
        verbose_name = "Sablon kedvezményezett"
        verbose_name_plural = "Sablon kedvezményezettek"
        ordering = ['order', 'beneficiary__name']
        unique_together = ['template', 'beneficiary']

class Transfer(TimestampedModel):
    CURRENCY_CHOICES = [
        ('HUF', 'HUF'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    ]
    
    originator_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, verbose_name="Terhelendő számla")
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, verbose_name="Kedvezményezett")
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Összeg")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='HUF', verbose_name="Pénznem")
    execution_date = models.DateField(verbose_name="Teljesítési dátum")
    remittance_info = models.CharField(max_length=500, verbose_name="Közlemény")
    template = models.ForeignKey(TransferTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sablon")
    nav_invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='generated_transfers', verbose_name="NAV számla",
                                  help_text="A NAV számla, amelyből ez az átutalás generálva lett (opcionális)")
    order = models.IntegerField(default=0, verbose_name="Sorrend", help_text="Átutalások sorrendje XML generáláskor")
    is_processed = models.BooleanField(default=False, verbose_name="Feldolgozva")
    notes = models.TextField(blank=True, verbose_name="Megjegyzések")
    
    class Meta:
        verbose_name = "Utalás"
        verbose_name_plural = "Utalások"
        ordering = ['order', '-execution_date', '-created_at']
        indexes = [
            models.Index(fields=['execution_date']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.beneficiary.name} - {self.amount} {self.currency}"
    
    @property
    def company(self):
        """Get company from the originator account"""
        return self.originator_account.company

class TransferBatch(CompanyOwnedTimestampedModel):
    BATCH_FORMAT_CHOICES = [
        ('XML', 'SEPA XML'),
        ('KH_CSV', 'KH Bank CSV'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Köteg neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    transfers = models.ManyToManyField(Transfer, verbose_name="Utalások")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Összeg")
    used_in_bank = models.BooleanField(default=False, verbose_name="Felhasználva a bankban", help_text="Jelzi, hogy a fájl fel lett-e töltve az internetbankba")
    bank_usage_date = models.DateTimeField(null=True, blank=True, verbose_name="Bank felhasználás dátuma")
    order = models.IntegerField(default=0, verbose_name="Sorrend", help_text="Kötegek sorrendje a listázáshoz és letöltéshez")
    xml_generated_at = models.DateTimeField(null=True, blank=True, verbose_name="Fájl generálás ideje")
    batch_format = models.CharField(max_length=10, choices=BATCH_FORMAT_CHOICES, default='XML', verbose_name="Fájlformátum")
    
    class Meta:
        verbose_name = "Utalási köteg"
        verbose_name_plural = "Utalási kötegek"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.transfers.count()} utalás)"
    
    @property
    def filename(self):
        """Generate filename based on batch format, name and date"""
        if self.xml_generated_at:
            date_str = self.xml_generated_at.strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c for c in self.name if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            if self.batch_format == 'KH_CSV':
                return f"{safe_name}_{date_str}.HUF.csv"
            else:
                return f"{safe_name}_{date_str}.xml"
        else:
            safe_name = self.name.replace(' ', '_')
            if self.batch_format == 'KH_CSV':
                return f"{safe_name}.HUF.csv"
            else:
                return f"{safe_name}.xml"
    
    @property
    def xml_filename(self):
        """Legacy property for backwards compatibility"""
        return self.filename


# NAV Online Invoice Synchronization Models

class NavConfigurationManager(models.Manager):
    """Enhanced manager for NavConfiguration with environment-aware queries."""
    
    def for_company_and_environment(self, company, environment='production'):
        """
        Get NAV configuration for a company and specific environment.
        
        Args:
            company: Company instance or ID
            environment: 'production' or 'test'
            
        Returns:
            NavConfiguration instance or None
        """
        if isinstance(company, int):
            company_id = company
        else:
            company_id = company.id
            
        return self.filter(
            company_id=company_id,
            api_environment=environment,
            is_active=True
        ).first()
    
    def get_active_config(self, company, prefer_production=True):
        """
        Get the best available NAV configuration for a company.
        
        Args:
            company: Company instance or ID
            prefer_production: If True, prefer production over test
            
        Returns:
            NavConfiguration instance or None
            
        Logic:
        - If prefer_production=True: production first, fallback to test
        - If prefer_production=False: test first, fallback to production
        """
        primary_env = 'production' if prefer_production else 'test'
        fallback_env = 'test' if prefer_production else 'production'
        
        # Try primary environment first
        config = self.for_company_and_environment(company, primary_env)
        if config:
            return config
            
        # Fallback to secondary environment
        return self.for_company_and_environment(company, fallback_env)


class NavConfiguration(models.Model):
    """
    Company-specific NAV API credentials and synchronization settings.
    
    Production Multi-Company Architecture:
    - Each company can have MULTIPLE NAV configurations (test + production)
    - Environment selection happens at runtime via configuration lookup
    - All credentials encrypted with master key, no environment variables needed
    - Complete data isolation per company with shared application logic
    
    Usage Examples:
    - Company A: Test config only (for development/staging)
    - Company B: Production config only (live operations)
    - Company C: Both test AND production (full development lifecycle)
    """
    
    objects = NavConfigurationManager()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='nav_configs')
    
    # Company-specific NAV credentials
    tax_number = models.CharField(max_length=20, verbose_name="NAV adószám")
    technical_user_login = models.CharField(max_length=100, verbose_name="Technikai felhasználó", default='')
    technical_user_password = models.TextField(verbose_name="Technikai felhasználó jelszó", default='')  # Will be encrypted on save
    signing_key = models.TextField(verbose_name="Aláíró kulcs", default='')  # Will be encrypted on save
    exchange_key = models.TextField(verbose_name="Csere kulcs", default='')  # Will be encrypted on save
    
    # Company-specific NAV encryption key (for internal company use)
    company_encryption_key = models.TextField(verbose_name="Cég titkosítási kulcs", blank=True)  # Auto-generated and encrypted
    
    # Configuration settings
    api_environment = models.CharField(
        max_length=10, 
        choices=[('test', 'Test'), ('production', 'Éles')], 
        default='test',
        verbose_name="API környezet"
    )
    
    
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    sync_enabled = models.BooleanField(default=False, verbose_name="Szinkronizáció engedélyezett")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "NAV konfiguráció"
        verbose_name_plural = "NAV konfigurációk"
    
    def __str__(self):
        return f"NAV konfiguráció - {self.company.name}"
    
    def save(self, *args, **kwargs):
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        
        # Check if this is a new instance or if credential fields have changed
        if self.pk is None:
            # New instance - encrypt all credential fields
            if self.technical_user_password and not self._is_encrypted(self.technical_user_password):
                self.technical_user_password = credential_manager.encrypt_credential(self.technical_user_password)
            if self.signing_key and not self._is_encrypted(self.signing_key):
                self.signing_key = credential_manager.encrypt_credential(self.signing_key)
            if self.exchange_key and not self._is_encrypted(self.exchange_key):
                self.exchange_key = credential_manager.encrypt_credential(self.exchange_key)
        else:
            # Existing instance - only encrypt if values have changed and are not already encrypted
            original = NavConfiguration.objects.get(pk=self.pk)
            
            if self.technical_user_password != original.technical_user_password and not self._is_encrypted(self.technical_user_password):
                self.technical_user_password = credential_manager.encrypt_credential(self.technical_user_password)
            if self.signing_key != original.signing_key and not self._is_encrypted(self.signing_key):
                self.signing_key = credential_manager.encrypt_credential(self.signing_key)
            if self.exchange_key != original.exchange_key and not self._is_encrypted(self.exchange_key):
                self.exchange_key = credential_manager.encrypt_credential(self.exchange_key)
        
        # Auto-generate company encryption key if not exists
        if not self.company_encryption_key:
            company_key = credential_manager.generate_company_encryption_key()
            self.company_encryption_key = credential_manager.encrypt_credential(company_key)
        
        super().save(*args, **kwargs)
    
    def _is_encrypted(self, value):
        """Check if a value is already encrypted (simple heuristic)"""
        if not value:
            return True
        # Encrypted values are typically base64-encoded and much longer
        return len(value) > 100 and '=' in value
    
    def get_decrypted_password(self):
        """Get decrypted technical user password"""
        if not self.technical_user_password:
            return ""
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        return credential_manager.decrypt_credential(self.technical_user_password)
    
    def get_decrypted_signing_key(self):
        """Get decrypted signing key"""
        if not self.signing_key:
            return ""
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        return credential_manager.decrypt_credential(self.signing_key)
    
    def get_decrypted_exchange_key(self):
        """Get decrypted exchange key"""
        if not self.exchange_key:
            return ""
        from .services.credential_manager import CredentialManager
        credential_manager = CredentialManager()
        return credential_manager.decrypt_credential(self.exchange_key)
    


class Invoice(TimestampedModel):
    """
    Core invoice data synchronized from NAV API.
    """
    DIRECTION_CHOICES = [
        ('INBOUND', 'Bejövő számla'),
        ('OUTBOUND', 'Kimenő számla'),
    ]
    
    SYNC_STATUS_CHOICES = [
        ('SUCCESS', 'Sikeres'),
        ('PARTIAL', 'Részleges'),
        ('FAILED', 'Sikertelen'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    nav_invoice_number = models.CharField(max_length=100, verbose_name="NAV számlaszám")
    invoice_direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="Irány")
    
    # Supplier information
    supplier_name = models.CharField(max_length=200, verbose_name="Szállító neve")
    supplier_tax_number = models.CharField(max_length=20, blank=True, verbose_name="Szállító adószáma")
    
    # Customer information  
    customer_name = models.CharField(max_length=200, verbose_name="Vevő neve")
    customer_tax_number = models.CharField(max_length=20, blank=True, verbose_name="Vevő adószáma")
    
    # Invoice dates
    issue_date = models.DateField(verbose_name="Kiállítás dátuma")
    fulfillment_date = models.DateField(null=True, blank=True, verbose_name="Teljesítés dátuma")
    payment_due_date = models.DateField(null=True, blank=True, verbose_name="Fizetési határidő")
    
    # Financial data
    currency_code = models.CharField(max_length=3, default='HUF', verbose_name="Pénznem")
    invoice_net_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Nettó összeg")
    invoice_vat_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="ÁFA összeg")
    invoice_gross_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Bruttó összeg")
    
    # NAV metadata
    original_request_version = models.CharField(max_length=10, verbose_name="NAV verzió")
    completion_date = models.DateTimeField(null=True, blank=True, verbose_name="NAV feldolgozás dátuma")
    source = models.CharField(max_length=20, default='NAV_SYNC', verbose_name="Forrás")
    nav_transaction_id = models.CharField(max_length=100, blank=True, verbose_name="NAV tranzakció azonosító")
    last_modified_date = models.DateTimeField(verbose_name="Utolsó módosítás (NAV)")
    
    # Additional NAV business fields
    invoice_operation = models.CharField(max_length=20, null=True, blank=True, verbose_name="Számla művelet (CREATE/STORNO/MODIFY)")
    invoice_category = models.CharField(max_length=20, null=True, blank=True, verbose_name="Számla kategória (NORMAL/SIMPLIFIED)")
    payment_method = models.CharField(max_length=20, null=True, blank=True, verbose_name="Fizetési mód (TRANSFER/CASH/CARD)")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Fizetési dátum")
    invoice_appearance = models.CharField(max_length=20, null=True, blank=True, verbose_name="Számla megjelenés (PAPER/ELECTRONIC)")
    
    # Payment status tracking fields
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Fizetésre vár'),
        ('PREPARED', 'Előkészítve'),
        ('PAID', 'Kifizetve'),
    ]
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='UNPAID',
        verbose_name="Fizetési állapot",
        help_text="A számla aktuális fizetési státusza"
    )
    payment_status_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Fizetési állapot dátuma",
        help_text="A számla kifizetésének dátuma (PAID státusz esetén)"
    )
    auto_marked_paid = models.BooleanField(
        default=False,
        verbose_name="Automatikusan jelölve",
        help_text="Igaz, ha automatikusan lett megjelölve fizetettként köteg feldolgozáskor"
    )
    
    # Bank account information (extracted from XML)
    supplier_bank_account_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Szállító bankszámlaszáma")
    customer_bank_account_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Vevő bankszámlaszáma")
    nav_source = models.CharField(max_length=10, null=True, blank=True, verbose_name="NAV forrás (OSZ/XML)")
    completeness_indicator = models.BooleanField(null=True, blank=True, verbose_name="Teljesség jelző")
    modification_index = models.IntegerField(null=True, blank=True, verbose_name="Módosítási index")
    original_invoice_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Eredeti számla száma (storno esetén)")
    
    # STORNO relationship - ForeignKey to the original invoice that this STORNO cancels
    storno_of = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='storno_invoices',
        verbose_name="Eredeti számla (amit ez a storno érvénytelenít)",
        help_text="A STORNO számla által érvénytelenített eredeti számla"
    )
    
    invoice_index = models.IntegerField(null=True, blank=True, verbose_name="Számla index")
    batch_index = models.IntegerField(null=True, blank=True, verbose_name="Köteg index")
    nav_creation_date = models.DateTimeField(null=True, blank=True, verbose_name="NAV létrehozási dátum")
    
    # HUF amounts for foreign currency invoices
    invoice_net_amount_huf = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Nettó összeg (HUF)")
    invoice_vat_amount_huf = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="ÁFA összeg (HUF)")
    invoice_gross_amount_huf = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Bruttó összeg (HUF)")
    
    # XML Data Storage
    nav_invoice_xml = models.TextField(null=True, blank=True, verbose_name="NAV számla XML")
    nav_invoice_hash = models.CharField(max_length=200, null=True, blank=True, verbose_name="NAV számla hash")
    
    # Payment tracking
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Fizetésre vár'),
        ('PREPARED', 'Előkészítve'),
        ('PAID', 'Kifizetve'),
    ]
    payment_status = models.CharField(
        max_length=10, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='UNPAID', 
        verbose_name="Fizetési állapot"
    )
    
    # Sync metadata
    sync_status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES, default='SUCCESS')
    
    class Meta:
        verbose_name = "Számla"
        verbose_name_plural = "Számlák"
        ordering = ['-issue_date', '-created_at']
        unique_together = ['company', 'nav_invoice_number', 'invoice_direction']
        indexes = [
            models.Index(fields=['company', 'invoice_direction']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['supplier_tax_number']),
            models.Index(fields=['customer_tax_number']),
            models.Index(fields=['nav_invoice_number']),
        ]
    
    @property
    def is_active(self):
        """
        Invoice is active if:
        1. It's not a STORNO invoice itself
        2. It hasn't been canceled by a STORNO invoice
        """
        if self.invoice_operation == 'STORNO':
            return False
        
        # Check if this invoice has been storno'd
        return not self.storno_invoices.exists()
    
    @property
    def is_paid(self):
        """
        Returns True if the invoice is marked as paid.
        """
        return self.payment_status == 'PAID'

    def mark_as_paid(self, payment_date=None, auto_marked=False):
        """Mark invoice as paid"""
        from django.utils import timezone
        self.payment_status = 'PAID'
        self.payment_status_date = payment_date or timezone.now().date()
        self.auto_marked_paid = auto_marked
        self.save()
    
    def mark_as_prepared(self, prepared_date=None):
        """Mark invoice as prepared (transfer created)"""
        from django.utils import timezone
        self.payment_status = 'PREPARED'
        self.payment_status_date = prepared_date or timezone.now().date()
        self.auto_marked_paid = False
        self.save()
        
    def mark_as_unpaid(self):
        """Mark invoice as unpaid (undo payment)"""
        self.payment_status = 'UNPAID'
        self.payment_status_date = None
        self.auto_marked_paid = False
        self.save()
    
    def is_overdue(self):
        """Check if invoice is overdue (unpaid and past due date)"""
        if self.payment_status != 'UNPAID':
            return False
        
        if not self.payment_due_date:
            return False
            
        from django.utils import timezone
        today = timezone.now().date()
        return self.payment_due_date < today
    
    def __str__(self):
        return f"{self.nav_invoice_number} - {self.supplier_name} ({self.invoice_direction})"


class InvoiceLineItem(TimestampedModel):
    """
    Detailed line items for each invoice.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.IntegerField(verbose_name="Sor száma")
    line_description = models.TextField(verbose_name="Megnevezés")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Mennyiség")
    unit_of_measure = models.CharField(max_length=50, blank=True, verbose_name="Mértékegység")
    unit_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, verbose_name="Egységár")
    line_net_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Sor nettó összeg")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="ÁFA kulcs (%)")
    line_vat_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Sor ÁFA összeg")
    line_gross_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Sor bruttó összeg")
    
    # Product classification
    product_code_category = models.CharField(max_length=50, blank=True, verbose_name="Termékkód kategória")
    product_code_value = models.CharField(max_length=100, blank=True, verbose_name="Termékkód érték")
    
    class Meta:
        verbose_name = "Számla tétel"
        verbose_name_plural = "Számla tételek"
        ordering = ['line_number']
        unique_together = ['invoice', 'line_number']
    
    def __str__(self):
        return f"{self.invoice.nav_invoice_number} - Sor {self.line_number}"


class InvoiceSyncLog(TimestampedModel):
    """
    Audit trail for synchronization operations.
    """
    SYNC_STATUS_CHOICES = [
        ('RUNNING', 'Futás'),
        ('SUCCESS', 'Sikeres'),
        ('PARTIAL_SUCCESS', 'Részlegesen sikeres'),
        ('FAILED', 'Sikertelen'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sync_logs')
    sync_start_time = models.DateTimeField(verbose_name="Szinkronizáció kezdete")
    sync_end_time = models.DateTimeField(null=True, blank=True, verbose_name="Szinkronizáció vége")
    direction_synced = models.CharField(max_length=10, verbose_name="Szinkronizált irány")  # INBOUND, OUTBOUND, BOTH
    
    # Statistics
    invoices_processed = models.IntegerField(default=0, verbose_name="Feldolgozott számlák")
    invoices_created = models.IntegerField(default=0, verbose_name="Létrehozott számlák")
    invoices_updated = models.IntegerField(default=0, verbose_name="Frissített számlák")
    errors_count = models.IntegerField(default=0, verbose_name="Hibák száma")
    
    # Error information
    last_error_message = models.TextField(blank=True, verbose_name="Utolsó hibaüzenet")
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='RUNNING')
    
    class Meta:
        verbose_name = "Szinkronizáció napló"
        verbose_name_plural = "Szinkronizáció naplók"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.name} - {self.sync_start_time.strftime('%Y-%m-%d %H:%M')} ({self.sync_status})"


# Company Feature Management Models

class FeatureTemplate(TimestampedModel):
    """
    Template definitions for available features that can be enabled per company.
    Defines the catalog of features available across the system.
    """
    FEATURE_CATEGORIES = [
        ('EXPORT', 'Export Features'),
        ('SYNC', 'Synchronization Features'),
        ('TRACKING', 'Tracking & Management Features'),
        ('REPORTING', 'Reporting Features'),
        ('INTEGRATION', 'Integration Features'),
        ('GENERAL', 'General Features'),
    ]
    
    feature_code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Feature kód",
        help_text="Unique identifier for the feature (e.g., 'EXPORT_XML_SEPA')"
    )
    display_name = models.CharField(
        max_length=100, 
        verbose_name="Megjelenített név",
        help_text="Human-readable name shown in UI"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Leírás",
        help_text="Detailed description of what this feature enables"
    )
    category = models.CharField(
        max_length=20, 
        choices=FEATURE_CATEGORIES, 
        default='GENERAL',
        verbose_name="Kategória"
    )
    default_enabled = models.BooleanField(
        default=False,
        verbose_name="Alapértelmezetten engedélyezett",
        help_text="Whether this feature should be enabled for new companies"
    )
    config_schema = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Konfigurációs séma",
        help_text="JSON schema for feature-specific configuration validation"
    )
    is_system_critical = models.BooleanField(
        default=False,
        verbose_name="Rendszerkritikus",
        help_text="Critical features that cannot be disabled"
    )
    
    class Meta:
        verbose_name = "Feature sablon"
        verbose_name_plural = "Feature sablonok"
        ordering = ['category', 'display_name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['feature_code']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.feature_code})"


class CompanyFeature(TimestampedModel):
    """
    Company-specific feature enablement and configuration.
    Controls which features are active for each company.
    """
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='features',
        verbose_name="Cég"
    )
    feature_template = models.ForeignKey(
        FeatureTemplate,
        on_delete=models.CASCADE,
        related_name='company_instances',
        verbose_name="Feature sablon"
    )
    is_enabled = models.BooleanField(
        default=False,
        verbose_name="Engedélyezett",
        help_text="Whether this feature is active for the company"
    )
    config_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Konfigurációs adatok",
        help_text="Company-specific configuration for this feature"
    )
    enabled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Engedélyezve ekkor",
        help_text="When this feature was first enabled"
    )
    enabled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enabled_features',
        verbose_name="Engedélyezte"
    )
    
    class Meta:
        verbose_name = "Cég feature"
        verbose_name_plural = "Cég feature-ök"
        unique_together = ['company', 'feature_template']
        ordering = ['company__name', 'feature_template__category', 'feature_template__display_name']
        indexes = [
            models.Index(fields=['company', 'is_enabled']),
            models.Index(fields=['feature_template', 'is_enabled']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{self.company.name} - {self.feature_template.display_name} {status}"
    
    def save(self, *args, **kwargs):
        # Set enabled_at timestamp when feature is first enabled
        if self.is_enabled and not self.enabled_at:
            from django.utils import timezone
            self.enabled_at = timezone.now()
        # Clear enabled_at if feature is disabled
        elif not self.is_enabled and self.enabled_at:
            self.enabled_at = None
        
        super().save(*args, **kwargs)
    
    @property
    def feature_code(self):
        """Convenience property to access feature code"""
        return self.feature_template.feature_code


class CompanyFeatureManager:
    """
    Business logic manager for company feature operations.
    Provides high-level methods for feature management.
    """
    
    @staticmethod
    def initialize_company_features(company, user=None):
        """
        Initialize default features for a new company based on FeatureTemplate defaults.
        
        Args:
            company: Company instance
            user: User who is initializing the features (optional)
        
        Returns:
            List of CompanyFeature instances created
        """
        default_features = FeatureTemplate.objects.filter(default_enabled=True)
        created_features = []
        
        for template in default_features:
            feature, created = CompanyFeature.objects.get_or_create(
                company=company,
                feature_template=template,
                defaults={
                    'is_enabled': True,
                    'enabled_by': user,
                }
            )
            if created:
                created_features.append(feature)
        
        return created_features
    
    @staticmethod
    def is_feature_enabled(company, feature_code):
        """
        Check if a specific feature is enabled for a company.
        
        Args:
            company: Company instance or ID
            feature_code: String feature code (e.g., 'EXPORT_XML_SEPA')
        
        Returns:
            Boolean indicating if feature is enabled
        """
        try:
            feature = CompanyFeature.objects.select_related('feature_template').get(
                company=company,
                feature_template__feature_code=feature_code
            )
            return feature.is_enabled
        except CompanyFeature.DoesNotExist:
            return False
    
    @staticmethod
    def get_company_features(company, category=None, enabled_only=False):
        """
        Get features for a company with optional filtering.
        
        Args:
            company: Company instance or ID
            category: Filter by feature category (optional)
            enabled_only: If True, only return enabled features
        
        Returns:
            QuerySet of CompanyFeature instances
        """
        queryset = CompanyFeature.objects.select_related(
            'feature_template'
        ).filter(company=company)
        
        if category:
            queryset = queryset.filter(feature_template__category=category)
        
        if enabled_only:
            queryset = queryset.filter(is_enabled=True)
        
        return queryset.order_by('feature_template__category', 'feature_template__display_name')
    
    @staticmethod
    def toggle_feature(company, feature_code, user=None):
        """
        Toggle a feature on/off for a company.
        
        Args:
            company: Company instance
            feature_code: String feature code
            user: User performing the action (optional)
        
        Returns:
            Tuple (CompanyFeature instance, was_enabled_after_toggle)
        """
        try:
            feature = CompanyFeature.objects.select_related('feature_template').get(
                company=company,
                feature_template__feature_code=feature_code
            )
            
            # Check if feature is system critical and cannot be disabled
            if feature.is_enabled and feature.feature_template.is_system_critical:
                raise ValueError(f"Cannot disable system critical feature: {feature_code}")
            
            feature.is_enabled = not feature.is_enabled
            if feature.is_enabled and user:
                feature.enabled_by = user
            
            feature.save()
            return feature, feature.is_enabled
            
        except CompanyFeature.DoesNotExist:
            # Feature doesn't exist, create it as enabled
            template = FeatureTemplate.objects.get(feature_code=feature_code)
            feature = CompanyFeature.objects.create(
                company=company,
                feature_template=template,
                is_enabled=True,
                enabled_by=user
            )
            return feature, True


class TrustedPartner(TimestampedModel):
    """
    Trusted partners for automatic payment processing.
    When invoices are received from these partners, they are automatically marked as PAID.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='trusted_partners')
    partner_name = models.CharField(max_length=200, verbose_name="Partner neve")
    tax_number = models.CharField(max_length=20, verbose_name="Adószám")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    auto_pay = models.BooleanField(default=True, verbose_name="Automatikus fizetés")
    notes = models.TextField(blank=True, verbose_name="Megjegyzések")
    
    # Statistics
    invoice_count = models.IntegerField(default=0, verbose_name="Számlák száma")
    last_invoice_date = models.DateField(null=True, blank=True, verbose_name="Utolsó számla dátuma")
    
    class Meta:
        verbose_name = "Megbízható partner"
        verbose_name_plural = "Megbízható partnerek"
        ordering = ['partner_name']
        unique_together = ['company', 'tax_number']
        indexes = [
            models.Index(fields=['company', 'tax_number']),
            models.Index(fields=['is_active', 'auto_pay']),
        ]
    
    def __str__(self):
        return f"{self.partner_name} ({self.tax_number})"
    
    def update_statistics(self):
        """Update invoice count and last invoice date from NAV invoices"""
        from django.db.models import Count, Max
        
        # Count invoices from this partner
        stats = Invoice.objects.filter(
            company=self.company,
            supplier_tax_number=self.tax_number
        ).aggregate(
            count=Count('id'),
            last_date=Max('issue_date')
        )
        
        self.invoice_count = stats['count'] or 0
        self.last_invoice_date = stats['last_date']
        self.save(update_fields=['invoice_count', 'last_invoice_date'])


# MNB Exchange Rate Models

class ExchangeRate(TimestampedModel):
    """
    MNB (Magyar Nemzeti Bank) official exchange rates for foreign currencies to HUF.
    Supports historical data and multiple daily synchronizations.

    The MNB publishes official exchange rates daily, typically updated around 11:45 AM.
    This model stores historical rates for accurate currency conversions.
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]

    rate_date = models.DateField(verbose_name="Árfolyam dátuma", db_index=True)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        verbose_name="Deviza kód",
        help_text="Currency code (USD or EUR)"
    )
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        verbose_name="Árfolyam (HUF)",
        help_text="Exchange rate: 1 unit of currency = X HUF"
    )
    unit = models.IntegerField(
        default=1,
        verbose_name="Egység",
        help_text="Number of currency units this rate applies to (typically 1)"
    )

    # Sync metadata
    sync_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Szinkronizálva",
        help_text="When this rate was fetched from MNB"
    )
    source = models.CharField(
        max_length=20,
        default='MNB',
        verbose_name="Forrás",
        help_text="Data source (always MNB for official rates)"
    )

    class Meta:
        verbose_name = "Árfolyam"
        verbose_name_plural = "Árfolyamok"
        ordering = ['-rate_date', 'currency']
        unique_together = ['rate_date', 'currency']
        indexes = [
            models.Index(fields=['rate_date', 'currency']),
            models.Index(fields=['-rate_date']),
            models.Index(fields=['currency']),
        ]

    def __str__(self):
        return f"{self.currency} - {self.rate_date}: {self.rate:.4f} HUF"

    def convert_to_huf(self, amount):
        """
        Convert foreign currency amount to HUF using this exchange rate.

        Args:
            amount: Decimal amount in foreign currency

        Returns:
            Decimal amount in HUF
        """
        from decimal import Decimal
        return (Decimal(str(amount)) * self.rate) / self.unit


class ExchangeRateSyncLog(TimestampedModel):
    """
    Audit trail for MNB exchange rate synchronization operations.
    Tracks success, failures, and statistics for each sync run.
    """
    SYNC_STATUS_CHOICES = [
        ('RUNNING', 'Futás'),
        ('SUCCESS', 'Sikeres'),
        ('PARTIAL_SUCCESS', 'Részlegesen sikeres'),
        ('FAILED', 'Sikertelen'),
    ]

    sync_start_time = models.DateTimeField(verbose_name="Szinkronizáció kezdete")
    sync_end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Szinkronizáció vége"
    )

    # Sync parameters
    currencies_synced = models.CharField(
        max_length=50,
        verbose_name="Szinkronizált devizák",
        help_text="Comma-separated currency codes (e.g., 'USD,EUR')"
    )
    date_range_start = models.DateField(verbose_name="Dátum tartomány kezdete")
    date_range_end = models.DateField(verbose_name="Dátum tartomány vége")

    # Statistics
    rates_created = models.IntegerField(
        default=0,
        verbose_name="Létrehozott árfolyamok",
        help_text="Number of new exchange rates created"
    )
    rates_updated = models.IntegerField(
        default=0,
        verbose_name="Frissített árfolyamok",
        help_text="Number of existing exchange rates updated"
    )

    # Status and errors
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='RUNNING',
        verbose_name="Szinkronizáció státusza"
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Hibaüzenet",
        help_text="Error details if sync failed"
    )

    class Meta:
        verbose_name = "Árfolyam szinkronizáció napló"
        verbose_name_plural = "Árfolyam szinkronizáció naplók"
        ordering = ['-sync_start_time']
        indexes = [
            models.Index(fields=['-sync_start_time']),
            models.Index(fields=['sync_status']),
        ]

    def __str__(self):
        return f"MNB Sync - {self.sync_start_time.strftime('%Y-%m-%d %H:%M')} ({self.sync_status})"

    @property
    def duration_seconds(self):
        """Calculate sync duration in seconds"""
        if self.sync_end_time:
            delta = self.sync_end_time - self.sync_start_time
            return delta.total_seconds()
        return None

    @property
    def total_rates_processed(self):
        """Total number of rates processed (created + updated)"""
        return self.rates_created + self.rates_updated


# =============================================================================
# Bank Statement Import Models
# =============================================================================

class BankStatement(CompanyOwnedTimestampedModel):
    """
    Represents a single uploaded bank statement PDF.

    Multi-company support: Each company can have statements from different banks.
    Duplicate prevention: Unique constraint on (company, file_hash) and (company, bank_code, account, period).
    """

    # Bank identification
    bank_code = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Bank kód",
        help_text="Bank identifier: GRANIT, OTP, KH, CIB, ERSTE"
    )
    bank_name = models.CharField(
        max_length=100,
        verbose_name="Bank neve"
    )
    bank_bic = models.CharField(
        max_length=11,
        blank=True,
        verbose_name="BIC kód"
    )

    # Account details
    account_number = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Számlaszám"
    )
    account_iban = models.CharField(
        max_length=34,
        blank=True,
        verbose_name="IBAN"
    )

    # Statement period
    statement_period_from = models.DateField(
        verbose_name="Kivonat időszak kezdete"
    )
    statement_period_to = models.DateField(
        verbose_name="Kivonat időszak vége"
    )
    statement_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Kivonat száma"
    )

    # Balances
    opening_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Nyitó egyenleg"
    )
    closing_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Záró egyenleg"
    )

    # File metadata
    file_name = models.CharField(
        max_length=255,
        verbose_name="Fájlnév"
    )
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="Fájl hash (SHA256)"
    )
    file_size = models.IntegerField(
        verbose_name="Fájl méret (byte)"
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name="Fájl elérési út"
    )

    # Upload tracking
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_statements',
        verbose_name="Feltöltő"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Feltöltés ideje"
    )

    # Processing status
    STATUS_CHOICES = [
        ('UPLOADED', 'Feltöltve'),
        ('PARSING', 'Feldolgozás alatt'),
        ('PARSED', 'Feldolgozva'),
        ('ERROR', 'Hiba'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UPLOADED',
        db_index=True,
        verbose_name="Státusz"
    )

    # Statistics
    total_transactions = models.IntegerField(
        default=0,
        verbose_name="Összes tranzakció"
    )
    credit_count = models.IntegerField(
        default=0,
        verbose_name="Jóváírások száma"
    )
    debit_count = models.IntegerField(
        default=0,
        verbose_name="Terhelések száma"
    )
    total_credits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Összesen jóváírva"
    )
    total_debits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Összesen terhelve"
    )
    matched_count = models.IntegerField(
        default=0,
        verbose_name="Párosított tranzakciók"
    )

    # Error handling
    parse_error = models.TextField(
        null=True,
        blank=True,
        verbose_name="Feldolgozási hiba"
    )
    parse_warnings = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Figyelmeztetések"
    )

    # Metadata
    raw_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Nyers metaadatok"
    )

    class Meta:
        verbose_name = "Bankszámlakivonat"
        verbose_name_plural = "Bankszámlakivonatok"
        unique_together = [
            ('company', 'file_hash'),
            ('company', 'bank_code', 'account_number', 'statement_period_from', 'statement_period_to'),
        ]
        indexes = [
            models.Index(fields=['company', 'bank_code', 'account_number']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'statement_period_to']),
            models.Index(fields=['uploaded_at']),
        ]
        ordering = ['-statement_period_to', '-uploaded_at']

    def __str__(self):
        return f"{self.bank_code} {self.account_number} ({self.statement_period_from} - {self.statement_period_to})"


class BankTransaction(CompanyOwnedTimestampedModel):
    """
    Individual transaction line from bank statement.

    Supports ALL transaction types: AFR transfers, POS purchases, bank fees, interest, etc.
    Contains bank-specific fields (IBAN, payment ID, card number) and matching fields (invoice, confidence).
    """

    # Transaction type choices
    TRANSACTION_TYPES = [
        # Transfers
        ('AFR_CREDIT', 'AFR jóváírás (Incoming instant payment)'),
        ('AFR_DEBIT', 'AFR terhelés (Outgoing instant payment)'),
        ('TRANSFER_CREDIT', 'Átutalás jóváírás (Incoming transfer)'),
        ('TRANSFER_DEBIT', 'Átutalás terhelés (Outgoing transfer)'),

        # Card transactions
        ('POS_PURCHASE', 'POS vásárlás (Card purchase)'),
        ('ATM_WITHDRAWAL', 'ATM készpénzfelvétel (Cash withdrawal)'),

        # Bank charges
        ('BANK_FEE', 'Banki jutalék/költség (Bank fee)'),
        ('INTEREST_CREDIT', 'Kamatjóváírás (Interest credit)'),
        ('INTEREST_DEBIT', 'Kamatköltség (Interest charge)'),

        # Other
        ('CORRECTION', 'Helyesbítés/Sztornó (Correction)'),
        ('OTHER', 'Egyéb tranzakció (Other)'),
    ]

    # Statement reference
    bank_statement = models.ForeignKey(
        'BankStatement',
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Bankszámlakivonat"
    )

    # Transaction identification
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
        db_index=True,
        verbose_name="Tranzakció típusa"
    )

    # Dates
    booking_date = models.DateField(
        db_index=True,
        verbose_name="Könyvelés dátuma"
    )
    value_date = models.DateField(
        db_index=True,
        verbose_name="Értéknap"
    )

    # Amount
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_index=True,
        verbose_name="Összeg",
        help_text="Negative for debit, positive for credit"
    )
    currency = models.CharField(
        max_length=3,
        default='HUF',
        verbose_name="Deviza"
    )

    # Transaction description
    description = models.TextField(
        verbose_name="Leírás"
    )
    short_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Rövid leírás"
    )

    # === AFR Transfer specific fields ===
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="Fizetési azonosító"
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tranzakció azonosító"
    )

    payer_name = models.CharField(
        max_length=300,
        blank=True,
        db_index=True,
        verbose_name="Fizető fél neve"
    )
    payer_iban = models.CharField(
        max_length=34,
        blank=True,
        verbose_name="Fizető fél IBAN"
    )
    payer_account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Fizető fél számlaszáma"
    )
    payer_bic = models.CharField(
        max_length=11,
        blank=True,
        verbose_name="Fizető fél BIC"
    )

    beneficiary_name = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
        verbose_name="Kedvezményezett neve"
    )
    beneficiary_iban = models.CharField(
        max_length=34,
        blank=True,
        verbose_name="Kedvezményezett IBAN"
    )
    beneficiary_account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Kedvezményezett számlaszáma"
    )
    beneficiary_bic = models.CharField(
        max_length=11,
        blank=True,
        verbose_name="Kedvezményezett BIC"
    )

    reference = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Közlemény",
        help_text="Nem strukturált közlemény - critical for invoice matching"
    )

    # === Additional transaction metadata ===
    partner_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Partnerek közti azonosító",
        help_text="End-to-end ID between partners"
    )
    transaction_type_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tranzakció típus kód",
        help_text="Bank-specific transaction type code (e.g., 001-00)"
    )
    fee_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Jutalék összege",
        help_text="Transaction fee (Előjegyzett jutalék)"
    )

    # === POS Purchase specific fields ===
    card_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Kártya szám (maszkolva)"
    )
    merchant_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Kereskedő neve"
    )
    merchant_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Kereskedő helye"
    )
    original_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Eredeti összeg (FX)"
    )
    original_currency = models.CharField(
        max_length=3,
        blank=True,
        verbose_name="Eredeti deviza (FX)"
    )
    exchange_rate = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Átváltási árfolyam",
        help_text="Exchange rate used for currency conversion (6 decimal precision)"
    )

    # === Matching to NAV invoices ===
    matched_invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transactions',
        verbose_name="Párosított számla"
    )

    # === Matching to Transfers (from TransferBatch) ===
    matched_transfer = models.ForeignKey(
        'Transfer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transactions',
        verbose_name="Párosított átutalás",
        help_text="Transfer from executed TransferBatch (used_in_bank=True)"
    )

    # === Matching to reimbursement pair (internal offsetting) ===
    matched_reimbursement = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reimbursement_pair',
        verbose_name="Párosított ellentétel",
        help_text="Offsetting transaction (e.g., POS purchase + personal transfer)"
    )

    match_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Párosítás megbízhatósága",
        help_text="0.00 to 1.00"
    )

    MATCH_METHOD_CHOICES = [
        ('REFERENCE_EXACT', 'Közlemény alapján (pontos)'),
        ('AMOUNT_IBAN', 'Összeg + IBAN alapján'),
        ('FUZZY_NAME', 'Összeg + név hasonlóság alapján'),
        ('TRANSFER_EXACT', 'Átutalási köteg alapján'),
        ('REIMBURSEMENT_PAIR', 'Ellentételezés (személyes visszafizetés)'),
        ('MANUAL', 'Manuális párosítás'),
    ]
    match_method = models.CharField(
        max_length=50,
        blank=True,
        choices=MATCH_METHOD_CHOICES,
        verbose_name="Párosítás módja"
    )
    match_notes = models.TextField(
        blank=True,
        verbose_name="Párosítási megjegyzések"
    )
    matched_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Párosítás ideje"
    )
    matched_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_transactions',
        verbose_name="Párosította"
    )

    # === Extra cost categorization ===
    is_extra_cost = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Extra költség"
    )

    EXTRA_COST_CATEGORIES = [
        ('BANK_FEE', 'Banki költség'),
        ('CARD_PURCHASE', 'Kártyás vásárlás'),
        ('INTEREST', 'Kamat'),
        ('TAX_DUTY', 'Adó/illeték'),
        ('CASH_WITHDRAWAL', 'Készpénzfelvétel'),
        ('OTHER', 'Egyéb költség'),
    ]
    extra_cost_category = models.CharField(
        max_length=50,
        blank=True,
        choices=EXTRA_COST_CATEGORIES,
        verbose_name="Költség kategória"
    )

    # Raw data storage
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Nyers adatok"
    )

    class Meta:
        verbose_name = "Banki tranzakció"
        verbose_name_plural = "Banki tranzakciók"
        indexes = [
            models.Index(fields=['bank_statement', 'booking_date']),
            models.Index(fields=['company', 'booking_date']),
            models.Index(fields=['company', 'transaction_type', 'booking_date']),
            models.Index(fields=['amount', 'currency']),
            models.Index(fields=['matched_invoice']),
            models.Index(fields=['payment_id']),
            models.Index(fields=['reference']),
            models.Index(fields=['is_extra_cost', 'extra_cost_category']),
        ]
        ordering = ['-booking_date', '-value_date']

    def __str__(self):
        return f"{self.booking_date} {self.transaction_type} {self.amount} {self.currency}"

    @property
    def is_credit(self):
        """Check if transaction is a credit (positive amount)"""
        return self.amount > 0

    @property
    def is_debit(self):
        """Check if transaction is a debit (negative amount)"""
        return self.amount < 0

    @property
    def is_matched(self):
        """Check if transaction is matched to an invoice"""
        return self.matched_invoice is not None

    @property
    def is_high_confidence_match(self):
        """Check if match has high confidence (>= 0.9)"""
        return self.match_confidence >= Decimal('0.90')


class OtherCost(CompanyOwnedTimestampedModel):
    """
    Other costs derived from bank transactions.

    Allows additional categorization, notes, and tags beyond BankTransaction fields.
    Used for expense tracking and cost analysis.
    """

    CATEGORY_CHOICES = [
        ('BANK_FEE', 'Banki költség'),
        ('CARD_PURCHASE', 'Kártyás vásárlás'),
        ('INTEREST', 'Kamat'),
        ('TAX_DUTY', 'Adó/illeték'),
        ('CASH_WITHDRAWAL', 'Készpénzfelvétel'),
        ('SUBSCRIPTION', 'Előfizetés'),
        ('UTILITY', 'Közüzem'),
        ('FUEL', 'Üzemanyag'),
        ('TRAVEL', 'Utazás'),
        ('OFFICE', 'Iroda/irodaszer'),
        ('OTHER', 'Egyéb'),
    ]

    bank_transaction = models.OneToOneField(
        'BankTransaction',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='other_cost_detail',
        verbose_name="Banki tranzakció"
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="Kategória"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Összeg"
    )
    currency = models.CharField(
        max_length=3,
        default='HUF',
        verbose_name="Deviza"
    )
    date = models.DateField(
        verbose_name="Dátum"
    )

    description = models.TextField(
        verbose_name="Leírás"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Megjegyzések"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Címkék",
        help_text="E.g., ['fuel', 'travel', 'office']"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Létrehozta"
    )

    class Meta:
        verbose_name = "Egyéb költség"
        verbose_name_plural = "Egyéb költségek"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} {self.category} {self.amount} {self.currency}"


# ============================================================================
# Billingo API Integration Models
# ============================================================================

class CompanyBillingoSettings(TimestampedModel):
    """
    Billingo API configuration for invoice synchronization.
    One configuration per company (company-scoped).
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_settings',
        verbose_name="Cég"
    )
    api_key = models.CharField(
        max_length=255,
        verbose_name="API kulcs (titkosított)",
        help_text="Titkosított Billingo API kulcs (X-API-KEY header)"
    )
    last_sync_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Utolsó szinkronizálás",
        help_text="Utolsó sikeres szinkronizálás időpontja"
    )
    last_billingo_invoice_sync_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Utolsó Billingo számla szinkronizálás dátuma",
        help_text="Az utolsó szinkronizált Billingo számla módosítási dátuma (Billingo API last_modified_date filter)"
    )
    last_billingo_spending_sync_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Utolsó Billingo költség szinkronizálás dátuma",
        help_text="Az utolsó szinkronizált Billingo költség módosítási dátuma"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktív",
        help_text="Engedélyezi/tiltja a szinkronizálást ennél a cégnél"
    )

    class Meta:
        verbose_name = "Billingo beállítás"
        verbose_name_plural = "Billingo beállítások"
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company'],
                name='unique_billingo_settings_per_company'
            )
        ]

    def __str__(self):
        return f"Billingo beállítások - {self.company.name}"


class BillingoInvoice(TimestampedModel):
    """
    Billingo invoice/document record from /documents API endpoint.
    Company-scoped for multi-tenant isolation.
    """
    # Billingo ID is the primary key (BigInteger from API response)
    id = models.BigIntegerField(primary_key=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_invoices',
        verbose_name="Cég"
    )

    # Invoice identification
    invoice_number = models.CharField(
        max_length=50,
        verbose_name="Számlaszám"
    )
    type = models.CharField(
        max_length=30,
        verbose_name="Típus",
        help_text="invoice, receipt, proforma, stb."
    )
    correction_type = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Helyesbítés típusa"
    )
    cancelled = models.BooleanField(
        default=False,
        verbose_name="Sztornózott"
    )
    block_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Billingo blokk ID"
    )

    # Payment information
    payment_status = models.CharField(
        max_length=30,
        verbose_name="Fizetési státusz",
        help_text="paid, unpaid, overdue, stb."
    )
    payment_method = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Fizetési mód",
        help_text="wire_transfer, cash, stb."
    )

    # Financial data
    gross_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg"
    )
    net_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Nettó összeg"
    )
    currency = models.CharField(
        max_length=5,
        verbose_name="Deviza"
    )
    conversion_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1,
        verbose_name="Átváltási árfolyam"
    )

    # Dates
    invoice_date = models.DateField(
        verbose_name="Számla kelte"
    )
    fulfillment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Teljesítés dátuma"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fizetési határidő"
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Kiegyenlítés dátuma"
    )

    # Organization (our company information from Billingo)
    organization_name = models.CharField(
        max_length=255,
        verbose_name="Saját cég neve"
    )
    organization_tax_number = models.CharField(
        max_length=50,
        verbose_name="Saját adószám"
    )
    organization_bank_account_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Saját bankszámlaszám"
    )
    organization_bank_account_iban = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Saját IBAN"
    )
    organization_swift = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Saját SWIFT/BIC"
    )

    # Partner (customer/supplier information)
    partner_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Partner Billingo ID"
    )
    partner_name = models.CharField(
        max_length=255,
        verbose_name="Partner neve"
    )
    partner_tax_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Partner adószáma"
    )
    partner_iban = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Partner IBAN"
    )
    partner_swift = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Partner SWIFT/BIC"
    )
    partner_account_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Partner számlaszáma"
    )

    # Additional metadata
    comment = models.TextField(
        blank=True,
        verbose_name="Megjegyzés"
    )
    online_szamla_status = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Online Számla státusz"
    )

    # Audit fields (last_modified in addition to created_at/updated_at from TimestampedModel)
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name="Utoljára módosítva"
    )

    class Meta:
        verbose_name = "Billingo számla"
        verbose_name_plural = "Billingo számlák"
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['company', 'invoice_date']),
            models.Index(fields=['company', 'payment_status']),
            models.Index(fields=['company', 'partner_tax_number']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.partner_name}"


class BillingoInvoiceItem(TimestampedModel):
    """
    Line items for Billingo invoices.
    Represents individual products/services on the invoice.
    """
    invoice = models.ForeignKey(
        BillingoInvoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Számla"
    )
    product_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Termék ID"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Megnevezés"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Mennyiség"
    )
    unit = models.CharField(
        max_length=20,
        verbose_name="Mértékegység",
        help_text="PIECE, HOUR, LITER, stb."
    )
    net_unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Nettó egységár"
    )
    net_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Nettó összeg"
    )
    gross_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg"
    )
    vat = models.CharField(
        max_length=10,
        verbose_name="ÁFA kulcs",
        help_text="27%, 5%, 0%, stb."
    )
    entitlement = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="ÁFA jogcím"
    )

    class Meta:
        verbose_name = "Billingo számla tétel"
        verbose_name_plural = "Billingo számla tételek"
        ordering = ['invoice', 'id']
        indexes = [
            models.Index(fields=['invoice']),
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.name}"


class BillingoSyncLog(TimestampedModel):
    """
    Audit log for Billingo invoice synchronization operations.
    """
    STATUS_CHOICES = [
        ('RUNNING', 'Fut'),
        ('COMPLETED', 'Befejezve'),
        ('FAILED', 'Sikertelen'),
        ('PARTIAL', 'Részben sikeres'),
    ]

    SYNC_TYPE_CHOICES = [
        ('MANUAL', 'Kézi'),
        ('AUTOMATIC', 'Automatikus'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_sync_logs',
        verbose_name="Cég"
    )
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        verbose_name="Szinkronizálás típusa"
    )

    # Sync metrics
    invoices_processed = models.IntegerField(
        default=0,
        verbose_name="Feldolgozott számlák"
    )
    invoices_created = models.IntegerField(
        default=0,
        verbose_name="Létrehozott számlák"
    )
    invoices_updated = models.IntegerField(
        default=0,
        verbose_name="Frissített számlák"
    )
    invoices_skipped = models.IntegerField(
        default=0,
        verbose_name="Kihagyott számlák"
    )
    items_extracted = models.IntegerField(
        default=0,
        verbose_name="Kivont tételek száma"
    )

    # Performance metrics
    sync_duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Szinkronizálás időtartama (mp)"
    )
    api_calls_made = models.IntegerField(
        default=0,
        verbose_name="API hívások száma"
    )

    # Error tracking
    errors = models.TextField(
        blank=True,
        verbose_name="Hibák (JSON)",
        help_text="JSON array of errors"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='RUNNING',
        verbose_name="Státusz"
    )

    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Indítva"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Befejezve"
    )

    class Meta:
        verbose_name = "Billingo szinkronizálási napló"
        verbose_name_plural = "Billingo szinkronizálási naplók"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['company', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['sync_type']),
        ]

    def __str__(self):
        return f"Billingo szinkronizálás - {self.company.name} - {self.started_at}"


class BillingoSpending(TimestampedModel):
    """
    Billingo spending record from /spendings API endpoint.
    Company-scoped for multi-tenant isolation.
    Represents expenses/costs from suppliers.
    """
    # Billingo ID is the primary key (BigInteger from API response)
    id = models.BigIntegerField(primary_key=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='billingo_spendings',
        verbose_name="Cég"
    )

    organization_id = models.IntegerField(
        verbose_name="Billingo szervezet ID"
    )

    # Spending category
    CATEGORY_CHOICES = [
        ('advertisement', 'Hirdetés'),
        ('development', 'Fejlesztés'),
        ('education_and_training', 'Oktatás és képzés'),
        ('other', 'Egyéb'),
        ('overheads', 'Rezsiköltség'),
        ('service', 'Szolgáltatás'),
        ('stock', 'Készlet'),
        ('tangible_assets', 'Tárgyi eszköz'),
    ]
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        verbose_name="Kategória"
    )

    # Payment tracking
    paid_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Kiegyenlítés dátuma"
    )

    # Financial data
    fulfillment_date = models.DateField(
        verbose_name="Teljesítés dátuma"
    )
    invoice_number = models.CharField(
        max_length=100,
        verbose_name="Számla/Bizonylat száma"
    )
    currency = models.CharField(
        max_length=3,
        default='HUF',
        verbose_name="Deviza"
    )
    conversion_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1,
        verbose_name="Átváltási árfolyam"
    )
    total_gross = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg"
    )
    total_gross_local = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Bruttó összeg (HUF)"
    )
    total_vat_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="ÁFA összeg"
    )
    total_vat_amount_local = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="ÁFA összeg (HUF)"
    )

    # Dates
    invoice_date = models.DateField(
        verbose_name="Számla kelte"
    )
    due_date = models.DateField(
        verbose_name="Fizetési határidő"
    )

    # Payment method
    payment_method = models.CharField(
        max_length=30,
        verbose_name="Fizetési mód",
        help_text="wire_transfer, cash, card, stb."
    )

    # Partner information
    partner_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Partner ID"
    )
    partner_name = models.CharField(
        max_length=255,
        verbose_name="Partner neve"
    )
    partner_tax_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Partner adószáma"
    )
    partner_address = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Partner címe",
        help_text="Full address object from API"
    )
    partner_iban = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Partner IBAN"
    )
    partner_account_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Partner bankszámla"
    )

    # Additional information
    comment = models.TextField(
        blank=True,
        verbose_name="Megjegyzés"
    )
    is_created_by_nav = models.BooleanField(
        default=False,
        verbose_name="NAV által létrehozva",
        help_text="True if spending was created from NAV import"
    )

    class Meta:
        verbose_name = "Billingo költség"
        verbose_name_plural = "Billingo költségek"
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['company', 'invoice_date']),
            models.Index(fields=['company', 'category']),
            models.Index(fields=['company', 'paid_at']),
            models.Index(fields=['partner_tax_code']),
            models.Index(fields=['invoice_number']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.partner_name} ({self.total_gross_local} HUF)"

    @property
    def is_paid(self):
        """Check if spending has been paid"""
        return self.paid_at is not None


# BASE Tables (Alaptáblák) - Master Data Management

class SupplierCategory(CompanyOwnedTimestampedModel):
    """
    Beszállító kategória (Supplier Category) alaptábla - cost categories for suppliers.
    Multi-tenant isolated.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Kategória neve",
        help_text="Cost category name"
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name="Megjelenítési sorrend",
        help_text="Display order (lower numbers appear first)"
    )

    class Meta:
        verbose_name = "Beszállító kategória"
        verbose_name_plural = "Beszállító kategóriák"
        ordering = ['display_order', 'name']
        unique_together = [['company', 'name']]
        indexes = [
            models.Index(fields=['company', 'display_order']),
        ]

    def __str__(self):
        return self.name


class SupplierType(CompanyOwnedTimestampedModel):
    """
    Beszállító típus (Supplier Type) alaptábla - cost subcategories for suppliers.
    Multi-tenant isolated.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Típus neve",
        help_text="Cost subcategory name"
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name="Megjelenítési sorrend",
        help_text="Display order (lower numbers appear first)"
    )

    class Meta:
        verbose_name = "Beszállító típus"
        verbose_name_plural = "Beszállító típusok"
        ordering = ['display_order', 'name']
        unique_together = [['company', 'name']]
        indexes = [
            models.Index(fields=['company', 'display_order']),
        ]

    def __str__(self):
        return self.name


class Supplier(CompanyOwnedTimestampedModel):
    """
    Beszállító (Supplier) alaptábla - partner adatok kategóriával és típussal.
    Multi-tenant isolated, validity period managed.
    """
    partner_name = models.CharField(
        max_length=255,
        verbose_name="Partner neve"
    )
    category = models.ForeignKey(
        SupplierCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategória",
        help_text="Cost category",
        related_name='suppliers'
    )
    type = models.ForeignKey(
        SupplierType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Típus",
        help_text="Cost subcategory",
        related_name='suppliers'
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség kezdete",
        help_text="Start date of validity period"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség vége",
        help_text="End date of validity period (null = no expiry)"
    )

    class Meta:
        verbose_name = "Beszállító"
        verbose_name_plural = "Beszállítók"
        ordering = ['-id']
        indexes = [
            models.Index(fields=['company', 'valid_from', 'valid_to']),
            models.Index(fields=['partner_name']),
        ]

    def __str__(self):
        return self.partner_name

    def is_valid(self):
        """
        Check if this supplier record is currently valid.
        Valid means: today >= valid_from AND (valid_to is null OR today <= valid_to)
        """
        today = date.today()

        # If valid_from is set and today is before it, not valid
        if self.valid_from and today < self.valid_from:
            return False

        # If valid_to is set and today is after it, not valid
        if self.valid_to and today > self.valid_to:
            return False

        # Otherwise, it's valid
        return True


class Customer(CompanyOwnedTimestampedModel):
    """
    Vevő (Customer) alaptábla - customer data with cashflow adjustment.
    Multi-tenant isolated, validity period managed.
    """
    customer_name = models.CharField(
        max_length=255,
        verbose_name="Vevő neve"
    )
    cashflow_adjustment = models.IntegerField(
        default=0,
        verbose_name="Cashflow kiigazítás (nap)",
        help_text="Number of days to adjust cashflow calculations (can be negative)"
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség kezdete",
        help_text="Start date of validity period"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség vége",
        help_text="End date of validity period (null = no expiry)"
    )

    class Meta:
        verbose_name = "Vevő"
        verbose_name_plural = "Vevők"
        ordering = ['-id']
        indexes = [
            models.Index(fields=['company', 'valid_from', 'valid_to']),
            models.Index(fields=['customer_name']),
        ]

    def __str__(self):
        return self.customer_name

    def is_valid(self):
        """
        Check if this customer record is currently valid.
        Valid means: today >= valid_from AND (valid_to is null OR today <= valid_to)
        """
        today = date.today()

        # If valid_from is set and today is before it, not valid
        if self.valid_from and today < self.valid_from:
            return False

        # If valid_to is set and today is after it, not valid
        if self.valid_to and today > self.valid_to:
            return False

        # Otherwise, it's valid
        return True


class ProductPrice(CompanyOwnedTimestampedModel):
    """
    CONMED árak (Product Pricing) alaptábla - product pricing data with USD/HUF prices and markup.
    Multi-tenant isolated, validity period managed.
    """
    product_value = models.CharField(
        max_length=50,
        verbose_name="Termék kód",
        help_text="Product code/identifier"
    )
    product_description = models.CharField(
        max_length=500,
        verbose_name="Termék leírás",
        help_text="Product description"
    )
    uom = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="UOM (EN)",
        help_text="Unit of measure in English (e.g., 'EA')"
    )
    uom_hun = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="UOM (HU)",
        help_text="Unit of measure in Hungarian (e.g., 'db')"
    )
    purchase_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Beszerzési ár USD",
        help_text="Purchase price in USD"
    )
    purchase_price_huf = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Beszerzési ár HUF",
        help_text="Purchase price in HUF"
    )
    markup = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Markup (%)",
        help_text="Markup percentage"
    )
    sales_price_huf = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Eladási ár HUF",
        help_text="Sales price in HUF"
    )
    cap_disp = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cap/Disp",
        help_text="Capital or Disposable classification"
    )
    is_inventory_managed = models.BooleanField(
        default=False,
        verbose_name="Készletkezelt termék",
        help_text="Whether this product is inventory-managed (Készletkezelt termék = 'y')"
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség kezdete",
        help_text="Start date of validity period"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Érvényesség vége",
        help_text="End date of validity period (null = no expiry)"
    )

    class Meta:
        verbose_name = "CONMED ár"
        verbose_name_plural = "CONMED árak"
        ordering = ['-id']
        indexes = [
            models.Index(fields=['company', 'valid_from', 'valid_to']),
            models.Index(fields=['product_value']),
            models.Index(fields=['company', 'product_value']),
        ]

    def __str__(self):
        return f"{self.product_value} - {self.product_description[:50]}"

    def is_valid(self):
        """
        Check if this product price record is currently valid.
        Valid means: today >= valid_from AND (valid_to is null OR today <= valid_to)
        """
        today = date.today()

        # If valid_from is set and today is before it, not valid
        if self.valid_from and today < self.valid_from:
            return False

        # If valid_to is set and today is after it, not valid
        if self.valid_to and today > self.valid_to:
            return False

        # Otherwise, it's valid
        return True

