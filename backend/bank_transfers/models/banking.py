"""
Banking and transfer management models.

This module contains models for bank accounts, beneficiaries, transfer templates,
and transfer batch management.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from ..base_models import (
    TimestampedModel, ActiveModel,
    CompanyOwnedTimestampedModel, CompanyOwnedTimestampedActiveModel
)


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
