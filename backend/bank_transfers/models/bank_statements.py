"""
Bank statement and transaction models.

This module contains models for bank statement imports, transaction parsing,
and invoice matching across multiple bank formats (GRÁNIT, Revolut, MagNet, K&H).
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date
from ..base_models import CompanyOwnedTimestampedModel


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
    # DEPRECATED: Keep for backward compatibility during migration
    matched_invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transactions',
        verbose_name="Párosított számla",
        help_text="(DEPRECATED) Use matched_invoices instead - single invoice match"
    )

    # NEW: ManyToMany relationship for batch matching
    matched_invoices = models.ManyToManyField(
        'Invoice',
        through='BankTransactionInvoiceMatch',
        related_name='bank_transactions_many',
        blank=True,
        verbose_name='Párosított számlák',
        help_text='Multiple matched invoices (for batch payments)'
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
        ('SYSTEM_AUTO_CATEGORIZED', 'Automatikusan kategorizált (banki tranzakció)'),
        ('LEARNED_PATTERN', 'Ismétlődő minta alapján (tanult)'),
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

    # === Helper properties for batch matching ===

    @property
    def is_batch_match(self) -> bool:
        """Returns True if transaction is matched to multiple invoices"""
        return self.matched_invoices.count() > 1

    @property
    def total_matched_amount(self) -> Decimal:
        """Sum of all matched invoice amounts"""
        return sum(
            match.invoice.invoice_gross_amount
            for match in self.invoice_matches.all()
        )

    @property
    def matched_invoices_count(self) -> int:
        """Count of matched invoices (0 if unmatched)"""
        return self.matched_invoices.count()

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
        """
        Check if transaction is matched or categorized.

        Returns True if:
        - Matched to invoice (single or batch)
        - Matched to transfer
        - Matched to reimbursement
        - Auto-categorized as OtherCost (system transactions like BANK_FEE, INTEREST)
        """
        # Check old single-invoice match FK
        if self.matched_invoice is not None:
            return True

        # Check new many-to-many invoice matches
        if self.matched_invoices.exists():
            return True

        # Check transfer match
        if self.matched_transfer is not None:
            return True

        # Check reimbursement match
        if self.matched_reimbursement is not None:
            return True

        # Check if auto-categorized as OtherCost (system transactions)
        if hasattr(self, 'other_cost_detail') and self.other_cost_detail is not None:
            return True

        return False

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

