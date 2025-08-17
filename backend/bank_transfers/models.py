from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Company(models.Model):
    """Cég entitás multi-tenant architektúrához"""
    name = models.CharField(max_length=200, verbose_name="Cég neve")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="Adószám")
    address = models.TextField(blank=True, verbose_name="Cím")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cég"
        verbose_name_plural = "Cégek"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CompanyUser(models.Model):
    """Felhasználó-cég kapcsolat szerepkörrel"""
    ROLE_CHOICES = [
        ('ADMIN', 'Cég adminisztrátor'),
        ('USER', 'Felhasználó'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER', verbose_name="Szerepkör")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cég felhasználó"
        verbose_name_plural = "Cég felhasználók"
        unique_together = ['user', 'company']
        ordering = ['company__name', 'user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.company.name} ({self.role})"

class UserProfile(models.Model):
    """Felhasználói profil kiegészítő adatokkal"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    preferred_language = models.CharField(max_length=10, default='hu', verbose_name="Nyelv")
    timezone = models.CharField(max_length=50, default='Europe/Budapest', verbose_name="Időzóna")
    last_active_company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, 
                                          verbose_name="Utoljára aktív cég")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Felhasználói profil"
        verbose_name_plural = "Felhasználói profilok"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} profil"

class BankAccount(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Számla neve")
    account_number = models.CharField(max_length=50, verbose_name="Számlaszám")
    bank_name = models.CharField(max_length=200, blank=True, verbose_name="Bank neve")
    is_default = models.BooleanField(default=False, verbose_name="Alapértelmezett")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bank számla"
        verbose_name_plural = "Bank számlák"
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.account_number})"
    
    def clean_account_number(self):
        return self.account_number.replace('-', '').replace(' ', '')

class Beneficiary(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='beneficiaries', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Kedvezményezett neve")
    account_number = models.CharField(max_length=50, verbose_name="Számlaszám")
    description = models.CharField(max_length=200, blank=True, verbose_name="Leírás", 
                                 help_text="További információk a kedvezményezettről (bank neve, szervezet adatai, stb.)")
    is_frequent = models.BooleanField(default=False, verbose_name="Gyakori kedvezményezett")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    remittance_information = models.TextField(blank=True, verbose_name="Utalási információ",
                                            help_text="Alapértelmezett fizetési hivatkozások, számlaszámok vagy egyéb tranzakció-specifikus információk")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Kedvezményezett"
        verbose_name_plural = "Kedvezményezettek"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_frequent']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.account_number})"
    
    def clean_account_number(self):
        return self.account_number.replace('-', '').replace(' ', '')

class TransferTemplate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='transfer_templates', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Sablon neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Utalási sablon"
        verbose_name_plural = "Utalási sablonok"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TemplateBeneficiary(models.Model):
    template = models.ForeignKey(TransferTemplate, on_delete=models.CASCADE, related_name='template_beneficiaries')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    default_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    default_remittance = models.CharField(max_length=500, blank=True)
    default_execution_date = models.DateField(null=True, blank=True, verbose_name="Alapértelmezett teljesítési dátum")
    order = models.IntegerField(default=0, verbose_name="Sorrend")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Sablon kedvezményezett"
        verbose_name_plural = "Sablon kedvezményezettek"
        ordering = ['order', 'beneficiary__name']
        unique_together = ['template', 'beneficiary']

class Transfer(models.Model):
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
    order = models.IntegerField(default=0, verbose_name="Sorrend", help_text="Átutalások sorrendje XML generáláskor")
    is_processed = models.BooleanField(default=False, verbose_name="Feldolgozva")
    notes = models.TextField(blank=True, verbose_name="Megjegyzések")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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

class TransferBatch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='transfer_batches', verbose_name="Cég", null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Köteg neve")
    description = models.TextField(blank=True, verbose_name="Leírás")
    transfers = models.ManyToManyField(Transfer, verbose_name="Utalások")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Összeg")
    used_in_bank = models.BooleanField(default=False, verbose_name="Felhasználva a bankban", help_text="Jelzi, hogy az XML fájl fel lett-e töltve az internetbankba")
    bank_usage_date = models.DateTimeField(null=True, blank=True, verbose_name="Bank felhasználás dátuma")
    order = models.IntegerField(default=0, verbose_name="Sorrend", help_text="Kötegek sorrendje a listázáshoz és letöltéshez")
    created_at = models.DateTimeField(auto_now_add=True)
    xml_generated_at = models.DateTimeField(null=True, blank=True, verbose_name="XML generálás ideje")
    
    class Meta:
        verbose_name = "Utalási köteg"
        verbose_name_plural = "Utalási kötegek"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.transfers.count()} utalás)"
    
    @property
    def xml_filename(self):
        """Generate XML filename based on batch name and date"""
        if self.xml_generated_at:
            date_str = self.xml_generated_at.strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c for c in self.name if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_name = safe_name.replace(' ', '_')
            return f"{safe_name}_{date_str}.xml"
        return f"{self.name.replace(' ', '_')}.xml"

