 Plan: Multi-Bank PDF Statement Import with Full Transaction Coverage                                                           │
     │                                                                                                                                │
     │ Revised Scope Based on Feedback                                                                                                │
     │                                                                                                                                │
     │ ✅ MUST HAVE                                                                                                                    │
     │                                                                                                                                │
     │ 1. Import ALL transactions from PDF (not just AFR transfers)                                                                   │
     │   - AFR transfers (credits/debits)                                                                                             │
     │   - POS purchases (card transactions)                                                                                          │
     │   - Bank fees (Előjegyzett jutalék)                                                                                            │
     │   - Interest charges                                                                                                           │
     │   - Any other transaction types                                                                                                │
     │ 2. Multi-bank architecture from day 1                                                                                          │
     │   - Abstract BankAdapter interface                                                                                             │
     │   - Factory pattern for bank detection                                                                                         │
     │   - GRÁNIT Bank adapter as first implementation                                                                                │
     │   - Easy to add OTP, K&H, CIB, Erste, Raiffeisen later                                                                         │
     │   - Critical for multi-company (each company may use different bank)                                                           │
     │ 3. Transaction type classification                                                                                             │
     │   - Categorize every transaction by type                                                                                       │
     │   - Enable filtering and reporting                                                                                             │
     │   - Support future matching logic per type                                                                                     │
     │                                                                                                                                │
     │ Architecture: Multi-Bank Design                                                                                                │
     │                                                                                                                                │
     │ Bank Adapter Pattern (Strategy Pattern)                                                                                        │
     │                                                                                                                                │
     │ BankStatementAdapter (Abstract Base Class)                                                                                     │
     │     ↓                                                                                                                          │
     │     ├── GranitBankAdapter (implemented first)                                                                                  │
     │     ├── OTPBankAdapter (future)                                                                                                │
     │     ├── KHBankAdapter (future)                                                                                                 │
     │     ├── CIBBankAdapter (future)                                                                                                │
     │     └── ErsteBankAdapter (future)                                                                                              │
     │                                                                                                                                │
     │ BankAdapterFactory                                                                                                             │
     │     - detect_bank(pdf_bytes, filename) → BankAdapter                                                                           │
     │     - get_adapter(bank_code) → BankAdapter                                                                                     │
     │     - list_supported_banks() → List[str]                                                                                       │
     │                                                                                                                                │
     │ Transaction Type Taxonomy                                                                                                      │
     │                                                                                                                                │
     │ Based on GRÁNIT Bank statement analysis:                                                                                       │
     │                                                                                                                                │
     │ TRANSACTION_TYPES = [                                                                                                          │
     │     # Transfers                                                                                                                │
     │     ('AFR_CREDIT', 'AFR jóváírás (Incoming instant payment)'),                                                                 │
     │     ('AFR_DEBIT', 'AFR terhelés (Outgoing instant payment)'),                                                                  │
     │     ('TRANSFER_CREDIT', 'Átutalás jóváírás (Incoming transfer)'),                                                              │
     │     ('TRANSFER_DEBIT', 'Átutalás terhelés (Outgoing transfer)'),                                                               │
     │                                                                                                                                │
     │     # Card transactions                                                                                                        │
     │     ('POS_PURCHASE', 'POS vásárlás (Card purchase)'),                                                                          │
     │     ('ATM_WITHDRAWAL', 'ATM készpénzfelvétel'),                                                                                │
     │                                                                                                                                │
     │     # Bank charges                                                                                                             │
     │     ('BANK_FEE', 'Banki jutalék/költség'),                                                                                     │
     │     ('INTEREST_CREDIT', 'Kamatjóváírás'),                                                                                      │
     │     ('INTEREST_DEBIT', 'Kamatköltség'),                                                                                        │
     │                                                                                                                                │
     │     # Other                                                                                                                    │
     │     ('CORRECTION', 'Helyesbítés/sztornó'),                                                                                     │
     │     ('OTHER', 'Egyéb tranzakció'),                                                                                             │
     │ ]                                                                                                                              │
     │                                                                                                                                │
     │ Data Model - Enhanced for All Transactions                                                                                     │
     │                                                                                                                                │
     │ BankStatement Model                                                                                                            │
     │                                                                                                                                │
     │ class BankStatement(CompanyOwnedTimestampedModel):                                                                             │
     │     """                                                                                                                        │
     │     Represents a single bank statement file (PDF).                                                                             │
     │     Multi-bank support: each company can have statements from different banks.                                                 │
     │     """                                                                                                                        │
     │                                                                                                                                │
     │     # Bank identification                                                                                                      │
     │     bank_code = models.CharField(max_length=20, db_index=True)  # 'GRANIT', 'OTP', 'KH', 'CIB'                                 │
     │     bank_name = models.CharField(max_length=100)  # 'GRÁNIT Bank Nyrt.'                                                        │
     │     bank_bic = models.CharField(max_length=11, blank=True)  # 'GNBAHUHB'                                                       │
     │                                                                                                                                │
     │     # Account details                                                                                                          │
     │     account_number = models.CharField(max_length=50, db_index=True)  # '12100011-19014874'                                     │
     │     account_iban = models.CharField(max_length=34, blank=True)  # 'HU62121000111901487400000000'                               │
     │                                                                                                                                │
     │     # Statement period                                                                                                         │
     │     statement_period_from = models.DateField()  # 2025-01-01                                                                   │
     │     statement_period_to = models.DateField()    # 2025-01-31                                                                   │
     │     statement_number = models.CharField(max_length=50, blank=True)  # '1/2025'                                                 │
     │                                                                                                                                │
     │     # Balances                                                                                                                 │
     │     opening_balance = models.DecimalField(max_digits=15, decimal_places=2)                                                     │
     │     closing_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)                              │
     │                                                                                                                                │
     │     # File metadata                                                                                                            │
     │     file_name = models.CharField(max_length=255)                                                                               │
     │     file_hash = models.CharField(max_length=64, db_index=True)  # SHA256                                                       │
     │     file_size = models.IntegerField()                                                                                          │
     │     file_path = models.CharField(max_length=500)  # Local path or S3/storage key                                               │
     │                                                                                                                                │
     │     # Upload tracking                                                                                                          │
     │     uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_statements')            │
     │     uploaded_at = models.DateTimeField(auto_now_add=True)                                                                      │
     │                                                                                                                                │
     │     # Processing status                                                                                                        │
     │     status = models.CharField(max_length=20, choices=[                                                                         │
     │         ('UPLOADED', 'Feltöltve'),                                                                                             │
     │         ('PARSING', 'Feldolgozás alatt'),                                                                                      │
     │         ('PARSED', 'Feldolgozva'),                                                                                             │
     │         ('ERROR', 'Hiba')                                                                                                      │
     │     ], default='UPLOADED', db_index=True)                                                                                      │
     │                                                                                                                                │
     │     # Statistics                                                                                                               │
     │     total_transactions = models.IntegerField(default=0)                                                                        │
     │     credit_count = models.IntegerField(default=0)  # Jóváírások száma                                                          │
     │     debit_count = models.IntegerField(default=0)   # Terhelések száma                                                          │
     │     total_credits = models.DecimalField(max_digits=15, decimal_places=2, default=0)                                            │
     │     total_debits = models.DecimalField(max_digits=15, decimal_places=2, default=0)                                             │
     │     matched_count = models.IntegerField(default=0)  # Matched to invoices                                                      │
     │                                                                                                                                │
     │     # Error handling                                                                                                           │
     │     parse_error = models.TextField(null=True, blank=True)                                                                      │
     │     parse_warnings = models.JSONField(default=list, blank=True)  # Non-fatal warnings                                          │
     │                                                                                                                                │
     │     # Metadata                                                                                                                 │
     │     raw_metadata = models.JSONField(default=dict, blank=True)  # Bank-specific metadata                                        │
     │                                                                                                                                │
     │     class Meta:                                                                                                                │
     │         verbose_name = "Bankszámlakivonat"                                                                                     │
     │         verbose_name_plural = "Bankszámlakivonatok"                                                                            │
     │         unique_together = [                                                                                                    │
     │             ('company', 'file_hash'),  # Prevent exact duplicate uploads                                                       │
     │             ('company', 'bank_code', 'account_number', 'statement_period_from', 'statement_period_to')  # Prevent period       │
     │ overlap                                                                                                                        │
     │         ]                                                                                                                      │
     │         indexes = [                                                                                                            │
     │             models.Index(fields=['company', 'bank_code', 'account_number']),                                                   │
     │             models.Index(fields=['company', 'status']),                                                                        │
     │             models.Index(fields=['company', 'statement_period_to']),                                                           │
     │             models.Index(fields=['uploaded_at']),                                                                              │
     │         ]                                                                                                                      │
     │         ordering = ['-statement_period_to', '-uploaded_at']                                                                    │
     │                                                                                                                                │
     │ BankTransaction Model - ALL Transaction Types                                                                                  │
     │                                                                                                                                │
     │ class BankTransaction(CompanyOwnedTimestampedModel):                                                                           │
     │     """                                                                                                                        │
     │     Individual transaction line from bank statement.                                                                           │
     │     Supports ALL transaction types (transfers, POS, fees, interest, etc.)                                                      │
     │     """                                                                                                                        │
     │                                                                                                                                │
     │     # Statement reference                                                                                                      │
     │     bank_statement = models.ForeignKey(                                                                                        │
     │         BankStatement,                                                                                                         │
     │         on_delete=models.CASCADE,                                                                                              │
     │         related_name='transactions'                                                                                            │
     │     )                                                                                                                          │
     │                                                                                                                                │
     │     # Transaction identification                                                                                               │
     │     transaction_type = models.CharField(                                                                                       │
     │         max_length=30,                                                                                                         │
     │         choices=TRANSACTION_TYPES,                                                                                             │
     │         db_index=True                                                                                                          │
     │     )                                                                                                                          │
     │                                                                                                                                │
     │     # Dates                                                                                                                    │
     │     booking_date = models.DateField(db_index=True)  # Könyvelés dátuma                                                         │
     │     value_date = models.DateField(db_index=True)    # Értéknap                                                                 │
     │                                                                                                                                │
     │     # Amount                                                                                                                   │
     │     amount = models.DecimalField(max_digits=15, decimal_places=2, db_index=True)  # Negative for debit                         │
     │     currency = models.CharField(max_length=3, default='HUF')                                                                   │
     │                                                                                                                                │
     │     # Transaction description                                                                                                  │
     │     description = models.TextField()  # Full transaction description                                                           │
     │     short_description = models.CharField(max_length=200, blank=True)  # Cleaned/normalized                                     │
     │                                                                                                                                │
     │     # === AFR Transfer specific fields ===                                                                                     │
     │     payment_id = models.CharField(max_length=100, blank=True, db_index=True)  # 'J0057M8Y6XGLKAAC'                             │
     │     transaction_id = models.CharField(max_length=100, blank=True)                                                              │
     │                                                                                                                                │
     │     payer_name = models.CharField(max_length=200, blank=True, db_index=True)                                                   │
     │     payer_iban = models.CharField(max_length=34, blank=True)                                                                   │
     │     payer_account_number = models.CharField(max_length=50, blank=True)                                                         │
     │     payer_bic = models.CharField(max_length=11, blank=True)                                                                    │
     │                                                                                                                                │
     │     beneficiary_name = models.CharField(max_length=200, blank=True, db_index=True)                                             │
     │     beneficiary_iban = models.CharField(max_length=34, blank=True)                                                             │
     │     beneficiary_account_number = models.CharField(max_length=50, blank=True)                                                   │
     │                                                                                                                                │
     │     reference = models.TextField(blank=True)  # "Nem strukturált közlemény" - CRITICAL for invoice matching                    │
     │                                                                                                                                │
     │     # === POS Purchase specific fields ===                                                                                     │
     │     card_number = models.CharField(max_length=20, blank=True)  # Masked: '558644******5059'                                    │
     │     merchant_name = models.CharField(max_length=200, blank=True)                                                               │
     │     merchant_location = models.CharField(max_length=100, blank=True)                                                           │
     │     original_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # FX transactions           │
     │     original_currency = models.CharField(max_length=3, blank=True)                                                             │
     │                                                                                                                                │
     │     # === Matching to NAV invoices ===                                                                                         │
     │     matched_invoice = models.ForeignKey(                                                                                       │
     │         'Invoice',                                                                                                             │
     │         on_delete=models.SET_NULL,                                                                                             │
     │         null=True,                                                                                                             │
     │         blank=True,                                                                                                            │
     │         related_name='bank_transactions'                                                                                       │
     │     )                                                                                                                          │
     │     match_confidence = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)  # 0.00 to 1.00                        │
     │     match_method = models.CharField(max_length=50, blank=True)  # 'REFERENCE_EXACT', 'AMOUNT_IBAN', 'FUZZY_NAME'               │
     │     match_notes = models.TextField(blank=True)                                                                                 │
     │     matched_at = models.DateTimeField(null=True, blank=True)                                                                   │
     │     matched_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,                                     │
     │ related_name='matched_transactions')                                                                                           │
     │                                                                                                                                │
     │     # === Extra cost categorization ===                                                                                        │
     │     is_extra_cost = models.BooleanField(default=False, db_index=True)  # True for fees, POS, etc.                              │
     │     extra_cost_category = models.CharField(max_length=50, blank=True, choices=[                                                │
     │         ('BANK_FEE', 'Banki költség'),                                                                                         │
     │         ('CARD_PURCHASE', 'Kártyás vásárlás'),                                                                                 │
     │         ('INTEREST', 'Kamat'),                                                                                                 │
     │         ('TAX_DUTY', 'Adó/illeték'),                                                                                           │
     │         ('CASH_WITHDRAWAL', 'Készpénzfelvétel'),                                                                               │
     │         ('OTHER', 'Egyéb költség'),                                                                                            │
     │     ])                                                                                                                         │
     │                                                                                                                                │
     │     # Raw data storage                                                                                                         │
     │     raw_data = models.JSONField(default=dict, blank=True)  # Complete parsed data from PDF                                     │
     │                                                                                                                                │
     │     class Meta:                                                                                                                │
     │         verbose_name = "Banki tranzakció"                                                                                      │
     │         verbose_name_plural = "Banki tranzakciók"                                                                              │
     │         indexes = [                                                                                                            │
     │             models.Index(fields=['bank_statement', 'booking_date']),                                                           │
     │             models.Index(fields=['company', 'booking_date']),                                                                  │
     │             models.Index(fields=['company', 'transaction_type', 'booking_date']),                                              │
     │             models.Index(fields=['amount', 'currency']),                                                                       │
     │             models.Index(fields=['matched_invoice']),                                                                          │
     │             models.Index(fields=['payment_id']),                                                                               │
     │             models.Index(fields=['reference']),  # Critical for invoice matching                                               │
     │             models.Index(fields=['is_extra_cost', 'extra_cost_category']),                                                     │
     │         ]                                                                                                                      │
     │         ordering = ['-booking_date', '-value_date']                                                                            │
     │                                                                                                                                │
     │ ExtraCost Model (unchanged)                                                                                                    │
     │                                                                                                                                │
     │ class ExtraCost(CompanyOwnedTimestampedModel):                                                                                 │
     │     """                                                                                                                        │
     │     Extra costs derived from bank transactions (fees, purchases, etc.)                                                         │
     │     Allows additional categorization and notes beyond BankTransaction.                                                         │
     │     """                                                                                                                        │
     │     bank_transaction = models.OneToOneField(                                                                                   │
     │         BankTransaction,                                                                                                       │
     │         on_delete=models.CASCADE,                                                                                              │
     │         null=True,                                                                                                             │
     │         blank=True,                                                                                                            │
     │         related_name='extra_cost_detail'                                                                                       │
     │     )                                                                                                                          │
     │                                                                                                                                │
     │     category = models.CharField(max_length=50, choices=[                                                                       │
     │         ('BANK_FEE', 'Banki költség'),                                                                                         │
     │         ('CARD_PURCHASE', 'Kártyás vásárlás'),                                                                                 │
     │         ('INTEREST', 'Kamat'),                                                                                                 │
     │         ('TAX_DUTY', 'Adó/illeték'),                                                                                           │
     │         ('CASH_WITHDRAWAL', 'Készpénzfelvétel'),                                                                               │
     │         ('SUBSCRIPTION', 'Előfizetés'),                                                                                        │
     │         ('UTILITY', 'Közüzem'),                                                                                                │
     │         ('OTHER', 'Egyéb'),                                                                                                    │
     │     ])                                                                                                                         │
     │                                                                                                                                │
     │     amount = models.DecimalField(max_digits=15, decimal_places=2)                                                              │
     │     currency = models.CharField(max_length=3, default='HUF')                                                                   │
     │     date = models.DateField()                                                                                                  │
     │                                                                                                                                │
     │     description = models.TextField()                                                                                           │
     │     notes = models.TextField(blank=True)                                                                                       │
     │     tags = models.JSONField(default=list, blank=True)  # ['fuel', 'travel', 'office']                                          │
     │                                                                                                                                │
     │     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)                                                 │
     │                                                                                                                                │
     │     class Meta:                                                                                                                │
     │         verbose_name = "Extra költség"                                                                                         │
     │         verbose_name_plural = "Extra költségek"                                                                                │
     │         ordering = ['-date']                                                                                                   │
     │                                                                                                                                │
     │ Parser Architecture - Multi-Bank Support                                                                                       │
     │                                                                                                                                │
     │ Abstract Base Class                                                                                                            │
     │                                                                                                                                │
     │ from abc import ABC, abstractmethod                                                                                            │
     │ from typing import Dict, List, Any, Optional                                                                                   │
     │ from dataclasses import dataclass                                                                                              │
     │ from decimal import Decimal                                                                                                    │
     │ from datetime import date                                                                                                      │
     │                                                                                                                                │
     │ @dataclass                                                                                                                     │
     │ class NormalizedTransaction:                                                                                                   │
     │     """                                                                                                                        │
     │     Normalized transaction data model.                                                                                         │
     │     All bank adapters must return this format.                                                                                 │
     │     """                                                                                                                        │
     │     transaction_type: str  # One of TRANSACTION_TYPES                                                                          │
     │     booking_date: date                                                                                                         │
     │     value_date: date                                                                                                           │
     │     amount: Decimal                                                                                                            │
     │     currency: str                                                                                                              │
     │     description: str                                                                                                           │
     │                                                                                                                                │
     │     # Optional fields (populated based on transaction type)                                                                    │
     │     payment_id: Optional[str] = None                                                                                           │
     │     transaction_id: Optional[str] = None                                                                                       │
     │                                                                                                                                │
     │     payer_name: Optional[str] = None                                                                                           │
     │     payer_iban: Optional[str] = None                                                                                           │
     │     payer_account_number: Optional[str] = None                                                                                 │
     │                                                                                                                                │
     │     beneficiary_name: Optional[str] = None                                                                                     │
     │     beneficiary_iban: Optional[str] = None                                                                                     │
     │     beneficiary_account_number: Optional[str] = None                                                                           │
     │                                                                                                                                │
     │     reference: Optional[str] = None                                                                                            │
     │                                                                                                                                │
     │     card_number: Optional[str] = None                                                                                          │
     │     merchant_name: Optional[str] = None                                                                                        │
     │     merchant_location: Optional[str] = None                                                                                    │
     │                                                                                                                                │
     │     raw_data: Dict[str, Any] = None  # Full parsed data                                                                        │
     │                                                                                                                                │
     │                                                                                                                                │
     │ @dataclass                                                                                                                     │
     │ class StatementMetadata:                                                                                                       │
     │     """Statement-level metadata"""                                                                                             │
     │     bank_code: str                                                                                                             │
     │     bank_name: str                                                                                                             │
     │     bank_bic: str                                                                                                              │
     │                                                                                                                                │
     │     account_number: str                                                                                                        │
     │     account_iban: str                                                                                                          │
     │                                                                                                                                │
     │     period_from: date                                                                                                          │
     │     period_to: date                                                                                                            │
     │     statement_number: str                                                                                                      │
     │                                                                                                                                │
     │     opening_balance: Decimal                                                                                                   │
     │     closing_balance: Optional[Decimal] = None                                                                                  │
     │                                                                                                                                │
     │     raw_metadata: Dict[str, Any] = None                                                                                        │
     │                                                                                                                                │
     │                                                                                                                                │
     │ class BankStatementAdapter(ABC):                                                                                               │
     │     """                                                                                                                        │
     │     Abstract base class for bank statement parsers.                                                                            │
     │     Each bank must implement this interface.                                                                                   │
     │     """                                                                                                                        │
     │                                                                                                                                │
     │     BANK_CODE: str = None  # e.g., 'GRANIT', 'OTP', 'KH'                                                                       │
     │     BANK_NAME: str = None  # e.g., 'GRÁNIT Bank Nyrt.'                                                                         │
     │     BANK_BIC: str = None   # e.g., 'GNBAHUHB'                                                                                  │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     @abstractmethod                                                                                                            │
     │     def detect(cls, pdf_bytes: bytes, filename: str) -> bool:                                                                  │
     │         """                                                                                                                    │
     │         Detect if this adapter can parse the given PDF.                                                                        │
     │                                                                                                                                │
     │         Args:                                                                                                                  │
     │             pdf_bytes: Raw PDF file bytes                                                                                      │
     │             filename: Original filename                                                                                        │
     │                                                                                                                                │
     │         Returns:                                                                                                               │
     │             True if this adapter can handle the PDF                                                                            │
     │         """                                                                                                                    │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @abstractmethod                                                                                                            │
     │     def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:                                                                       │
     │         """                                                                                                                    │
     │         Parse bank statement PDF and extract all transactions.                                                                 │
     │                                                                                                                                │
     │         Args:                                                                                                                  │
     │             pdf_bytes: Raw PDF file bytes                                                                                      │
     │                                                                                                                                │
     │         Returns:                                                                                                               │
     │             {                                                                                                                  │
     │                 'metadata': StatementMetadata,                                                                                 │
     │                 'transactions': List[NormalizedTransaction]                                                                    │
     │             }                                                                                                                  │
     │                                                                                                                                │
     │         Raises:                                                                                                                │
     │             BankStatementParseError: If parsing fails                                                                          │
     │         """                                                                                                                    │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     def get_bank_code(cls) -> str:                                                                                             │
     │         """Return bank identifier code"""                                                                                      │
     │         return cls.BANK_CODE                                                                                                   │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     def get_bank_name(cls) -> str:                                                                                             │
     │         """Return bank display name"""                                                                                         │
     │         return cls.BANK_NAME                                                                                                   │
     │                                                                                                                                │
     │ GRÁNIT Bank Adapter - Full Implementation                                                                                      │
     │                                                                                                                                │
     │ class GranitBankAdapter(BankStatementAdapter):                                                                                 │
     │     """                                                                                                                        │
     │     GRÁNIT Bank Nyrt. statement parser.                                                                                        │
     │                                                                                                                                │
     │     Handles:                                                                                                                   │
     │     - AFR jóváírás/terhelés (instant payments)                                                                                 │
     │     - POS vásárlás (card purchases)                                                                                            │
     │     - Bank fees (Előjegyzett jutalék)                                                                                          │
     │     - Interest charges                                                                                                         │
     │     - All other transaction types                                                                                              │
     │     """                                                                                                                        │
     │                                                                                                                                │
     │     BANK_CODE = 'GRANIT'                                                                                                       │
     │     BANK_NAME = 'GRÁNIT Bank Nyrt.'                                                                                            │
     │     BANK_BIC = 'GNBAHUHB'                                                                                                      │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     def detect(cls, pdf_bytes: bytes, filename: str) -> bool:                                                                  │
     │         """Detect GRÁNIT Bank PDF"""                                                                                           │
     │         try:                                                                                                                   │
     │             with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:                                                                   │
     │                 first_page = pdf.pages[0].extract_text()                                                                       │
     │                 return ('GRÁNIT Bank' in first_page and                                                                        │
     │                         'GNBAHUHB' in first_page)                                                                              │
     │         except:                                                                                                                │
     │             return False                                                                                                       │
     │                                                                                                                                │
     │     def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:                                                                       │
     │         """Parse GRÁNIT Bank statement - ALL transactions"""                                                                   │
     │                                                                                                                                │
     │         with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:                                                                       │
     │             # Extract all text from all pages                                                                                  │
     │             full_text = ""                                                                                                     │
     │             for page in pdf.pages:                                                                                             │
     │                 full_text += page.extract_text() + "\n"                                                                        │
     │                                                                                                                                │
     │             # Parse metadata                                                                                                   │
     │             metadata = self._parse_metadata(full_text)                                                                         │
     │                                                                                                                                │
     │             # Parse ALL transactions (multi-pass approach)                                                                     │
     │             transactions = self._parse_all_transactions(full_text)                                                             │
     │                                                                                                                                │
     │             return {                                                                                                           │
     │                 'metadata': metadata,                                                                                          │
     │                 'transactions': transactions                                                                                   │
     │             }                                                                                                                  │
     │                                                                                                                                │
     │     def _parse_metadata(self, text: str) -> StatementMetadata:                                                                 │
     │         """Extract statement metadata from header"""                                                                           │
     │         # ... implementation                                                                                                   │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     def _parse_all_transactions(self, text: str) -> List[NormalizedTransaction]:                                               │
     │         """                                                                                                                    │
     │         Parse ALL transaction types from statement.                                                                            │
     │                                                                                                                                │
     │         Strategy:                                                                                                              │
     │         1. Split text into lines                                                                                               │
     │         2. State machine to detect transaction boundaries                                                                      │
     │         3. Multi-line parsing for complex transactions (AFR)                                                                   │
     │         4. Single-line parsing for simple transactions (fees, POS)                                                             │
     │         5. Classify each transaction by type                                                                                   │
     │         """                                                                                                                    │
     │         transactions = []                                                                                                      │
     │         lines = text.split('\n')                                                                                               │
     │         i = 0                                                                                                                  │
     │                                                                                                                                │
     │         while i < len(lines):                                                                                                  │
     │             line = lines[i].strip()                                                                                            │
     │                                                                                                                                │
     │             # Check for AFR transfer (multi-line)                                                                              │
     │             if 'AFR' in line and ('jóváírás' in line or 'terhelés' in line):                                                   │
     │                 txn, lines_consumed = self._parse_afr_transfer(lines, i)                                                       │
     │                 transactions.append(txn)                                                                                       │
     │                 i += lines_consumed                                                                                            │
     │                 continue                                                                                                       │
     │                                                                                                                                │
     │             # Check for POS purchase (multi-line)                                                                              │
     │             if 'POS vásárlás' in line:                                                                                         │
     │                 txn, lines_consumed = self._parse_pos_purchase(lines, i)                                                       │
     │                 transactions.append(txn)                                                                                       │
     │                 i += lines_consumed                                                                                            │
     │                 continue                                                                                                       │
     │                                                                                                                                │
     │             # Check for bank fee (single-line)                                                                                 │
     │             if 'jutalék' in line or 'költség' in line:                                                                         │
     │                 txn = self._parse_bank_fee(line)                                                                               │
     │                 if txn:                                                                                                        │
     │                     transactions.append(txn)                                                                                   │
     │                 i += 1                                                                                                         │
     │                 continue                                                                                                       │
     │                                                                                                                                │
     │             # Check for interest                                                                                               │
     │             if 'kamat' in line.lower():                                                                                        │
     │                 txn = self._parse_interest(line)                                                                               │
     │                 if txn:                                                                                                        │
     │                     transactions.append(txn)                                                                                   │
     │                 i += 1                                                                                                         │
     │                 continue                                                                                                       │
     │                                                                                                                                │
     │             # Check for other transfer types                                                                                   │
     │             if 'átutalás' in line.lower():                                                                                     │
     │                 txn, lines_consumed = self._parse_transfer(lines, i)                                                           │
     │                 if txn:                                                                                                        │
     │                     transactions.append(txn)                                                                                   │
     │                     i += lines_consumed                                                                                        │
     │                     continue                                                                                                   │
     │                                                                                                                                │
     │             i += 1                                                                                                             │
     │                                                                                                                                │
     │         return transactions                                                                                                    │
     │                                                                                                                                │
     │     def _parse_afr_transfer(self, lines: List[str], start_idx: int) -> Tuple[NormalizedTransaction, int]:                      │
     │         """                                                                                                                    │
     │         Parse AFR transfer (multi-line format).                                                                                │
     │                                                                                                                                │
     │         Returns:                                                                                                               │
     │             (NormalizedTransaction, lines_consumed)                                                                            │
     │         """                                                                                                                    │
     │         # Extract booking date and amount from first line                                                                      │
     │         # Pattern: "2025.04.01 AFR jóváírás bankon kívül                    4 675 505"                                         │
     │         # ... implementation                                                                                                   │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     def _parse_pos_purchase(self, lines: List[str], start_idx: int) -> Tuple[NormalizedTransaction, int]:                      │
     │         """Parse POS card purchase (multi-line)"""                                                                             │
     │         # ... implementation                                                                                                   │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     def _parse_bank_fee(self, line: str) -> Optional[NormalizedTransaction]:                                                   │
     │         """Parse bank fee (single-line)"""                                                                                     │
     │         # ... implementation                                                                                                   │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     def _parse_interest(self, line: str) -> Optional[NormalizedTransaction]:                                                   │
     │         """Parse interest charge/credit"""                                                                                     │
     │         # ... implementation                                                                                                   │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     def _parse_transfer(self, lines: List[str], start_idx: int) -> Tuple[Optional[NormalizedTransaction], int]:                │
     │         """Parse regular bank transfer"""                                                                                      │
     │         # ... implementation                                                                                                   │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │ Bank Adapter Factory                                                                                                           │
     │                                                                                                                                │
     │ class BankAdapterFactory:                                                                                                      │
     │     """                                                                                                                        │
     │     Factory for bank statement adapters.                                                                                       │
     │     Handles bank detection and adapter instantiation.                                                                          │
     │     """                                                                                                                        │
     │                                                                                                                                │
     │     _adapters: List[Type[BankStatementAdapter]] = [                                                                            │
     │         GranitBankAdapter,                                                                                                     │
     │         # OTPBankAdapter,  # Future                                                                                            │
     │         # KHBankAdapter,   # Future                                                                                            │
     │         # CIBBankAdapter,  # Future                                                                                            │
     │     ]                                                                                                                          │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     def detect_bank(cls, pdf_bytes: bytes, filename: str) -> Optional[Type[BankStatementAdapter]]:                             │
     │         """                                                                                                                    │
     │         Detect which bank issued this statement.                                                                               │
     │                                                                                                                                │
     │         Returns:                                                                                                               │
     │             Adapter class if detected, None otherwise                                                                          │
     │         """                                                                                                                    │
     │         for adapter_class in cls._adapters:                                                                                    │
     │             try:                                                                                                               │
     │                 if adapter_class.detect(pdf_bytes, filename):                                                                  │
     │                     return adapter_class                                                                                       │
     │             except Exception as e:                                                                                             │
     │                 logger.warning(f"Error detecting bank with {adapter_class.__name__}: {e}")                                     │
     │                                                                                                                                │
     │         return None                                                                                                            │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     def get_adapter(cls, bank_code: str) -> Optional[BankStatementAdapter]:                                                    │
     │         """Get adapter by bank code"""                                                                                         │
     │         for adapter_class in cls._adapters:                                                                                    │
     │             if adapter_class.BANK_CODE == bank_code:                                                                           │
     │                 return adapter_class()                                                                                         │
     │         return None                                                                                                            │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     def list_supported_banks(cls) -> List[Dict[str, str]]:                                                                     │
     │         """List all supported banks"""                                                                                         │
     │         return [                                                                                                               │
     │             {                                                                                                                  │
     │                 'code': adapter.BANK_CODE,                                                                                     │
     │                 'name': adapter.BANK_NAME,                                                                                     │
     │                 'bic': adapter.BANK_BIC                                                                                        │
     │             }                                                                                                                  │
     │             for adapter in cls._adapters                                                                                       │
     │         ]                                                                                                                      │
     │                                                                                                                                │
     │     @classmethod                                                                                                               │
     │     def register_adapter(cls, adapter_class: Type[BankStatementAdapter]):                                                      │
     │         """Register new bank adapter (for plugins/extensions)"""                                                               │
     │         if adapter_class not in cls._adapters:                                                                                 │
     │             cls._adapters.append(adapter_class)                                                                                │
     │                                                                                                                                │
     │ API Endpoints - Complete                                                                                                       │
     │                                                                                                                                │
     │ class BankStatementViewSet(viewsets.ModelViewSet):                                                                             │
     │     """                                                                                                                        │
     │     Bank statement management with multi-bank support.                                                                         │
     │                                                                                                                                │
     │     Permissions: BANK_STATEMENT_IMPORT feature required                                                                        │
     │     """                                                                                                                        │
     │     serializer_class = BankStatementSerializer                                                                                 │
     │     permission_classes = [IsAuthenticated, IsCompanyMember, RequireBankStatementImport]                                        │
     │                                                                                                                                │
     │     @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])                                                  │
     │     def upload(self, request):                                                                                                 │
     │         """                                                                                                                    │
     │         Upload bank statement PDF.                                                                                             │
     │                                                                                                                                │
     │         Steps:                                                                                                                 │
     │         1. Validate file (PDF, size limit)                                                                                     │
     │         2. Detect bank using BankAdapterFactory                                                                                │
     │         3. Compute file hash                                                                                                   │
     │         4. Check for duplicates                                                                                                │
     │         5. Parse PDF                                                                                                           │
     │         6. Create BankStatement + BankTransaction records                                                                      │
     │         7. Run matching engine                                                                                                 │
     │         8. Return results                                                                                                      │
     │         """                                                                                                                    │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @action(detail=False, methods=['get'])                                                                                     │
     │     def supported_banks(self, request):                                                                                        │
     │         """List supported banks"""                                                                                             │
     │         banks = BankAdapterFactory.list_supported_banks()                                                                      │
     │         return Response(banks)                                                                                                 │
     │                                                                                                                                │
     │     @action(detail=True, methods=['post'])                                                                                     │
     │     def reparse(self, request, pk=None):                                                                                       │
     │         """Re-parse existing statement (admin only)"""                                                                         │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @action(detail=True, methods=['get'])                                                                                      │
     │     def transactions(self, request, pk=None):                                                                                  │
     │         """                                                                                                                    │
     │         List transactions for statement.                                                                                       │
     │                                                                                                                                │
     │         Filters:                                                                                                               │
     │         - transaction_type                                                                                                     │
     │         - matched (true/false)                                                                                                 │
     │         - is_extra_cost (true/false)                                                                                           │
     │         - date_from, date_to                                                                                                   │
     │         """                                                                                                                    │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @action(detail=True, methods=['get'])                                                                                      │
     │     def summary(self, request, pk=None):                                                                                       │
     │         """                                                                                                                    │
     │         Statement summary with statistics.                                                                                     │
     │                                                                                                                                │
     │         Returns:                                                                                                               │
     │         - Total credits/debits                                                                                                 │
     │         - Transaction type breakdown                                                                                           │
     │         - Match rate                                                                                                           │
     │         - Extra costs total                                                                                                    │
     │         """                                                                                                                    │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │                                                                                                                                │
     │ class BankTransactionViewSet(viewsets.ModelViewSet):                                                                           │
     │     """Bank transaction management"""                                                                                          │
     │                                                                                                                                │
     │     @action(detail=True, methods=['post'])                                                                                     │
     │     def match_invoice(self, request, pk=None):                                                                                 │
     │         """Manual match to invoice"""                                                                                          │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @action(detail=True, methods=['post'])                                                                                     │
     │     def unmatch(self, request, pk=None):                                                                                       │
     │         """Remove invoice match"""                                                                                             │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @action(detail=True, methods=['post'])                                                                                     │
     │     def categorize_extra_cost(self, request, pk=None):                                                                         │
     │         """Categorize as extra cost"""                                                                                         │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │     @action(detail=False, methods=['post'])                                                                                    │
     │     def bulk_categorize(self, request):                                                                                        │
     │         """Bulk categorize by keywords or rules"""                                                                             │
     │         pass                                                                                                                   │
     │                                                                                                                                │
     │ Matching Engine - Enhanced for All Transaction Types                                                                           │
     │                                                                                                                                │
     │ class TransactionMatchingService:                                                                                              │
     │     """                                                                                                                        │
     │     Match bank transactions to NAV invoices.                                                                                   │
     │                                                                                                                                │
     │     Focus on AFR transfers and regular transfers (ignore POS, fees).                                                           │
     │     """                                                                                                                        │
     │                                                                                                                                │
     │     def match_transactions(self, statement: BankStatement) -> Dict[str, Any]:                                                  │
     │         """                                                                                                                    │
     │         Run matching engine on all transactions in statement.                                                                  │
     │                                                                                                                                │
     │         Returns statistics about matches.                                                                                      │
     │         """                                                                                                                    │
     │         results = {                                                                                                            │
     │             'total_checked': 0,                                                                                                │
     │             'high_confidence': 0,  # >= 0.9                                                                                    │
     │             'medium_confidence': 0,  # 0.5-0.89                                                                                │
     │             'no_match': 0,  # < 0.5                                                                                            │
     │             'skipped': 0,  # POS, fees, etc.                                                                                   │
     │         }                                                                                                                      │
     │                                                                                                                                │
     │         # Only match transfer-type transactions                                                                                │
     │         matchable_types = [                                                                                                    │
     │             'AFR_CREDIT', 'AFR_DEBIT',                                                                                         │
     │             'TRANSFER_CREDIT', 'TRANSFER_DEBIT'                                                                                │
     │         ]                                                                                                                      │
     │                                                                                                                                │
     │         transactions = statement.transactions.filter(                                                                          │
     │             transaction_type__in=matchable_types                                                                               │
     │         )                                                                                                                      │
     │                                                                                                                                │
     │         for txn in transactions:                                                                                               │
     │             match_result = self._match_single_transaction(txn)                                                                 │
     │                                                                                                                                │
     │             if match_result:                                                                                                   │
     │                 txn.matched_invoice = match_result['invoice']                                                                  │
     │                 txn.match_confidence = match_result['confidence']                                                              │
     │                 txn.match_method = match_result['method']                                                                      │
     │                 txn.save()                                                                                                     │
     │                                                                                                                                │
     │                 # Auto-update invoice if high confidence                                                                       │
     │                 if match_result['confidence'] >= Decimal('0.90'):                                                              │
     │                     self._auto_mark_invoice_paid(match_result['invoice'], txn)                                                 │
     │                     results['high_confidence'] += 1                                                                            │
     │                 elif match_result['confidence'] >= Decimal('0.50'):                                                            │
     │                     results['medium_confidence'] += 1                                                                          │
     │             else:                                                                                                              │
     │                 results['no_match'] += 1                                                                                       │
     │                                                                                                                                │
     │             results['total_checked'] += 1                                                                                      │
     │                                                                                                                                │
     │         # Update statement statistics                                                                                          │
     │         statement.matched_count = results['high_confidence'] + results['medium_confidence']                                    │
     │         statement.save()                                                                                                       │
     │                                                                                                                                │
     │         return results                                                                                                         │
     │                                                                                                                                │
     │     def _match_single_transaction(self, txn: BankTransaction) -> Optional[Dict]:                                               │
     │         """                                                                                                                    │
     │         Match single transaction to invoice.                                                                                   │
     │                                                                                                                                │
     │         Strategies (in order of priority):                                                                                     │
     │         1. Reference code exact match (confidence: 1.0)                                                                        │
     │         2. Amount + IBAN match (confidence: 0.95)                                                                              │
     │         3. Amount + beneficiary name fuzzy (confidence: 0.7-0.9)                                                               │
     │         """                                                                                                                    │
     │         # Strategy 1: Reference exact match                                                                                    │
     │         if txn.reference:                                                                                                      │
     │             invoice = self._match_by_reference(txn.reference)                                                                  │
     │             if invoice:                                                                                                        │
     │                 return {                                                                                                       │
     │                     'invoice': invoice,                                                                                        │
     │                     'confidence': Decimal('1.00'),                                                                             │
     │                     'method': 'REFERENCE_EXACT'                                                                                │
     │                 }                                                                                                              │
     │                                                                                                                                │
     │         # Strategy 2: Amount + IBAN                                                                                            │
     │         if txn.payer_iban or txn.beneficiary_iban:                                                                             │
     │             invoice = self._match_by_amount_iban(txn)                                                                          │
     │             if invoice:                                                                                                        │
     │                 return {                                                                                                       │
     │                     'invoice': invoice,                                                                                        │
     │                     'confidence': Decimal('0.95'),                                                                             │
     │                     'method': 'AMOUNT_IBAN'                                                                                    │
     │                 }                                                                                                              │
     │                                                                                                                                │
     │         # Strategy 3: Fuzzy name match                                                                                         │
     │         invoice, confidence = self._match_by_fuzzy_name(txn)                                                                   │
     │         if invoice and confidence >= Decimal('0.70'):                                                                          │
     │             return {                                                                                                           │
     │                 'invoice': invoice,                                                                                            │
     │                 'confidence': confidence,                                                                                      │
     │                 'method': 'FUZZY_NAME'                                                                                         │
     │             }                                                                                                                  │
     │                                                                                                                                │
     │         return None                                                                                                            │
     │                                                                                                                                │
     │ Implementation TODO - 22 Items                                                                                                 │
     │                                                                                                                                │
     │ Phase 1: Data Models & Migration (3 days)                                                                                      │
     │                                                                                                                                │
     │ 1. Create 3 Django models (BankStatement, BankTransaction, ExtraCost)                                                          │
     │ 2. Add transaction type choices and all field definitions                                                                      │
     │ 3. Create Django migration with indexes and unique constraints                                                                 │
     │ 4. Add BANK_STATEMENT_IMPORT feature to FeatureTemplate                                                                        │
     │ 5. Test migration on dev database (PostgreSQL + SQL Server)                                                                    │
     │ 6. Update DATABASE_DOCUMENTATION.md with complete table schemas                                                                │
     │ 7. Generate SQL comment scripts (PostgreSQL + SQL Server)                                                                      │
     │                                                                                                                                │
     │ Phase 2: Parser Architecture (4 days)                                                                                          │
     │                                                                                                                                │
     │ 8. Implement BankStatementAdapter abstract base class                                                                          │
     │ 9. Implement NormalizedTransaction and StatementMetadata dataclasses                                                           │
     │ 10. Implement BankAdapterFactory with detection logic                                                                          │
     │ 11. Implement GranitBankAdapter._parse_metadata()                                                                              │
     │ 12. Implement GranitBankAdapter._parse_afr_transfer() (multi-line)                                                             │
     │ 13. Implement GranitBankAdapter._parse_pos_purchase() (multi-line)                                                             │
     │ 14. Implement GranitBankAdapter._parse_bank_fee() (single-line)                                                                │
     │ 15. Implement parsing for all other transaction types                                                                          │
     │                                                                                                                                │
     │ Phase 3: Testing & Validation (2 days)                                                                                         │
     │                                                                                                                                │
     │ 16. Write unit tests for each transaction type parser                                                                          │
     │ 17. Test parser with all 9 example PDFs                                                                                        │
     │ 18. Validate transaction counts match manual review                                                                            │
     │ 19. Test duplicate detection (same file, same period different file)                                                           │
     │                                                                                                                                │
     │ Phase 4: API & Service Layer (3 days)                                                                                          │
     │                                                                                                                                │
     │ 20. Create BankStatementViewSet with upload endpoint                                                                           │
     │ 21. Implement file storage (local or S3)                                                                                       │
     │ 22. Create BankTransactionViewSet with filtering                                                                               │
     │ 23. Implement TransactionMatchingService with 3 strategies                                                                     │
     │ 24. Add serializers (BankStatementSerializer, BankTransactionSerializer)                                                       │
     │ 25. Add Swagger documentation                                                                                                  │
     │                                                                                                                                │
     │ Phase 5: Frontend (3 days)                                                                                                     │
     │                                                                                                                                │
     │ 26. React upload component with drag-drop                                                                                      │
     │ 27. Statement list with bank logo, statistics                                                                                  │
     │ 28. Transaction table with filtering by type                                                                                   │
     │ 29. Match review UI with confidence badges                                                                                     │
     │ 30. Extra cost categorization interface                                                                                        │
     │                                                                                                                                │
     │ Phase 6: Deployment (1 day)                                                                                                    │
     │                                                                                                                                │
     │ 31. Feature flag deployment                                                                                                    │
     │ 32. Documentation for users                                                                                                    │
     │ 33. Railway deployment                                                                                                         │
     │                                                                                                                                │
     │ Key Design Decisions                                                                                                           │
     │                                                                                                                                │
     │ ✅ Import ALL transactions (not just AFR)                                                                                       │
     │ ✅ Multi-bank architecture from day 1 (Factory pattern)                                                                         │
     │ ✅ Extensible parser system (easy to add OTP, K&H, etc.)                                                                        │
     │ ✅ Transaction type taxonomy (10 types defined)                                                                                 │
     │ ✅ Duplicate detection (by hash + period)                                                                                       │
     │ ✅ Auto-matching for high confidence (>= 0.9)                                                                                   │
     │ ✅ Extra cost auto-flagging (POS, fees)                                                                                         │
     │ ✅ Multi-company support (each company can use different banks)                                                                 │
     │ ✅ Synchronous processing for MVP (no background workers)                                                                       │
     │ ✅ GRÁNIT Bank first (with 9 real PDFs for testing)                                                                             │