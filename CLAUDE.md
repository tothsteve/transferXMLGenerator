# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Django + React application for generating XML and CSV files for bank transfers with **multi-company architecture**, **feature flags**, and **role-based access control**. The system manages beneficiaries, transfer templates, NAV invoice synchronization, and generates SEPA-compatible XML files and KH Bank CSV files for bulk bank transfers.

### Backend (Django)
- **Django REST API** with `bank_transfers` app and **multi-company architecture**
- **SQL Server database** connection (port 1435, database: 'administration')
- **Multi-tenant isolation** with company-scoped data and **feature flag system**
- **Role-based access control** with 4-level permissions (ADMIN, FINANCIAL, ACCOUNTANT, USER)
- **Key models**: Company, CompanyUser, FeatureTemplate, CompanyFeature, BankAccount, Beneficiary, TransferTemplate, Transfer, TransferBatch, TrustedPartner, ExchangeRate, ExchangeRateSyncLog
- **NAV integration** with invoice synchronization, XML storage, **payment status tracking**, and **trusted partners auto-payment system**
- **MNB Exchange Rate integration** with daily sync of USD/EUR rates from Magyar Nemzeti Bank official API
- **Export generation** via `utils.generate_xml()` and `kh_export.py` - creates HUF transaction XML files and KH Bank CSV files
- **Feature-gated functionality** with company-specific feature enablement
- **Excel import** functionality for bulk beneficiary creation
- **Template system** for recurring transfer patterns (e.g., monthly payroll)
- **Swagger API docs** available via drf_yasg

### Frontend (React + TypeScript)
- **Create React App** with TypeScript and Material-UI
- **Complete authentication system** with JWT tokens and multi-company support
- **Full API integration** with axios interceptors for automatic authentication
- **Multi-company architecture** with company context and role-based permissions
- **Responsive dashboard** with sidebar navigation and modern design
- **Complete CRUD operations** for beneficiaries, templates, transfers, and batches
- **Settings management** for default bank account configuration and trusted partners with full CRUD operations
- **React Query integration** for optimistic updates, caching, and error handling
- **Modern UI components** with form validation, loading states, and Hungarian localization
- **NAV invoice payment status management** with bulk update operations and flexible date selection
- **Trusted partners management** with automated NAV invoice payment processing

## ✅ IMPLEMENTED: Multi-Company Feature Flag System

### Company-Specific Feature Control
The system implements a sophisticated **two-layer permission architecture**:

1. **Company Feature Level**: Features must be enabled for the company
2. **User Role Level**: User's role must permit access to the feature

### Role-Based Access Control

#### User Roles (4 Levels)
- **ADMIN**: Full access to all enabled company features + user management
- **FINANCIAL**: Transfer operations, templates, SEPA XML exports
- **ACCOUNTANT**: Invoice/expense management (NAV integration)
- **USER**: Read-only access to basic features

#### Permission Matrix
| Feature Category | ADMIN | FINANCIAL | ACCOUNTANT | USER |
|------------------|-------|-----------|------------|------|
| **Beneficiaries** | Full CRUD | Full CRUD | View only | View only |
| **Transfers** | Full CRUD | Full CRUD | View only | View only |
| **Templates** | Full CRUD | Full CRUD | View only | View only |
| **Batches** | Full CRUD | View only | View only | View only |
| **NAV Invoices** | Full CRUD | View only | Full CRUD | View only |
| **Exports** | All formats | SEPA XML | None | None |
| **User Management** | Full | None | None | None |

### Active Features (15 Total)

#### 1. Export Features (3)
- **EXPORT_XML_SEPA**: Generate SEPA-compatible XML files
- **EXPORT_CSV_KH**: Generate KH Bank specific CSV format  
- **EXPORT_CSV_CUSTOM**: Custom CSV format exports

#### 2. Sync Features (1)
- **NAV_SYNC**: NAV invoice synchronization and import

#### 3. Tracking Features (6)
- **BENEFICIARY_MANAGEMENT**: Full CRUD operations on beneficiaries
- **BENEFICIARY_VIEW**: View beneficiaries only
- **TRANSFER_MANAGEMENT**: Full CRUD operations on transfers
- **TRANSFER_VIEW**: View transfers only
- **BATCH_MANAGEMENT**: Full CRUD operations on batches
- **BATCH_VIEW**: View batches only

#### 4. Reporting Features (2)
- **REPORTING_DASHBOARD**: Access to dashboard views
- **REPORTING_ANALYTICS**: Advanced analytics features

#### 5. Integration Features (2)
- **API_ACCESS**: REST API access for external integrations
- **WEBHOOK_NOTIFICATIONS**: Webhook notification system

#### 6. General Features (1)
- **BULK_OPERATIONS**: Bulk import/export operations

### Implementation Notes
- Features are cached at login for performance
- Permission checking happens at ViewSet level with custom permission classes
- Companies can enable/disable features independently
- Admin users can force logout other users for security
- Complete audit trail for feature enablement and user actions

## ✅ IMPLEMENTED: NAV Invoice Payment Status Tracking

### Payment Status Workflow
The system implements comprehensive **payment status tracking** for NAV invoices with automated status updates:

1. **UNPAID** (Fizetésre vár) - Default status for all invoices
2. **PREPARED** (Előkészítve) - When transfer is created from invoice
3. **PAID** (Kifizetve) - When batch is marked as "used in bank"

### Key Features

#### **Automated Status Updates**
- **Transfer Creation**: Invoice automatically marked as PREPARED when transfer is generated
- **Batch Processing**: Invoice automatically marked as PAID when batch is used in bank
- **Dynamic Overdue Detection**: No static OVERDUE status - calculated based on payment_due_date vs current date

#### **Bulk Payment Status Management**
- **Bulk Mark Unpaid**: Reset multiple invoices to "Fizetésre vár" status
- **Bulk Mark Prepared**: Mark multiple invoices as "Előkészítve" status
- **Bulk Mark Paid**: Mark multiple invoices as "Kifizetve" with flexible date options:
  - **Payment Due Date Option**: Use each invoice's individual payment_due_date
  - **Custom Date Option**: Set a single custom payment date for all selected invoices

#### **API Endpoints**
- `POST /api/nav-invoices/bulk_mark_unpaid/` - Bulk mark as unpaid
- `POST /api/nav-invoices/bulk_mark_prepared/` - Bulk mark as prepared  
- `POST /api/nav-invoices/bulk_mark_paid/` - Bulk mark as paid with flexible date options

#### **Frontend Features**
- **Visual Status Indicators**: Icons with tooltips showing payment status and date
- **Bulk Action Bar**: Appears when invoices are selected with status update buttons
- **Flexible Date Selection**: Checkbox to choose between payment due dates vs custom date
- **Hungarian Localization**: All UI elements in Hungarian with proper date formatting

### Database Implementation
- `payment_status` field with CHECK constraint for valid statuses
- `payment_status_date` for tracking when status was last changed
- `auto_marked_paid` flag to track automated vs manual status changes
- Indexed for efficient filtering by payment status

## ✅ IMPLEMENTED: Trusted Partners Auto-Payment System

### Business Logic
The **Trusted Partners** feature allows companies to designate specific suppliers as "trusted", enabling **automatic payment status updates** during NAV invoice synchronization. When a new invoice is received from a trusted partner, it is automatically marked as **PAID** instead of the default **UNPAID** status.

### Key Features

#### **Partner Management**
- **Company-scoped trusted partners** with name and tax number identification
- **Active/Inactive status control** to temporarily disable trusted partners
- **Auto-payment toggle** per partner for granular control
- **Statistics tracking**: invoice count and last invoice date per partner
- **Source integration**: Partners can be selected from existing NAV invoice suppliers

#### **Automated Payment Processing**
- **NAV Sync Integration**: During invoice synchronization, invoices from trusted partners are automatically marked as PAID
- **Flexible Tax Number Matching**: Supports multiple Hungarian tax number formats:
  - **8-digit format**: Base company tax number (e.g., "12345678")
  - **11-digit format**: Full tax number with check digits (e.g., "12345678-2-16")
  - **13-digit format**: Tax number with dashes (e.g., "12345678-2-16")
- **Smart Matching Algorithm**: Three-level matching approach for reliability:
  1. **Exact match**: Direct tax number comparison
  2. **Normalized match**: Remove dashes and spaces, compare full numbers
  3. **Base match**: Compare first 8 digits for cross-format compatibility

#### **User Interface**
- **Settings Integration**: Accessible through "Beállítások" (Settings) menu with tabbed interface
- **Dual Input Methods**: 
  - Manual partner entry with name and tax number
  - Selection from existing NAV invoice suppliers with search and sort
- **Advanced Search**: Case-insensitive search by partner name or tax number
- **Flexible Sorting**: Sortable by partner name, tax number, invoice count, or last invoice date
- **Toggle Controls**: Individual switches for active status and auto-payment functionality
- **Real-time Statistics**: Display invoice count and last invoice date per partner

### API Endpoints

#### **Trusted Partners Management**
- `GET /api/trusted-partners/` - List company's trusted partners with pagination and search
- `POST /api/trusted-partners/` - Create new trusted partner
- `PUT /api/trusted-partners/{id}/` - Update trusted partner details
- `DELETE /api/trusted-partners/{id}/` - Remove trusted partner
- `GET /api/trusted-partners/available_partners/` - Get available suppliers from NAV invoices with search and ordering

#### **Search and Filtering Parameters**
- `search` - Case-insensitive search by partner name or tax number
- `ordering` - Sort by: `partner_name`, `tax_number`, `invoice_count`, `-last_invoice_date` (default)
- `active` - Filter by active status (true/false)
- `auto_pay` - Filter by auto-payment status (true/false)

### Database Schema

#### **TrustedPartner Model**
```python
class TrustedPartner(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='trusted_partners')
    partner_name = models.CharField(max_length=200, verbose_name="Partner neve")
    tax_number = models.CharField(max_length=20, verbose_name="Adószám")
    is_active = models.BooleanField(default=True, verbose_name="Aktív")
    auto_pay = models.BooleanField(default=True, verbose_name="Automatikus fizetés")
    invoice_count = models.IntegerField(default=0, verbose_name="Számlák száma")
    last_invoice_date = models.DateField(null=True, blank=True, verbose_name="Utolsó számla dátuma")
    
    class Meta:
        unique_together = [['company', 'tax_number']]
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['company', 'auto_pay']),
            models.Index(fields=['company', '-last_invoice_date']),
        ]
```

### Technical Implementation

#### **Tax Number Normalization**
The system handles various Hungarian tax number formats through normalization:

```python
def _normalize_tax_number(self, tax_number: str) -> str:
    """Remove dashes and spaces, keeping only digits"""
    return ''.join(filter(str.isdigit, tax_number))

def _get_base_tax_number(self, tax_number: str) -> str:
    """Extract first 8 digits for base matching"""
    normalized = self._normalize_tax_number(tax_number)
    return normalized[:8] if len(normalized) >= 8 else normalized
```

#### **Auto-Payment Logic**
During NAV invoice synchronization (`invoice_sync_service.py`):

```python
# Check for trusted partners
trusted_partners = TrustedPartner.objects.filter(
    company=company,
    is_active=True,
    auto_pay=True
)

for partner in trusted_partners:
    # Three-level matching approach
    if (invoice_tax == partner.tax_number or  # Exact match
        normalized_invoice == normalized_partner or  # Normalized match  
        base_invoice == base_partner):  # Base match
        
        invoice.payment_status = 'PAID'
        invoice.payment_status_date = timezone.now().date()
        invoice.auto_marked_paid = True
        break
```

#### **Frontend Components**
- **`TrustedPartners.tsx`**: Main management interface with data table and controls
- **`AddPartnerDialog.tsx`**: Modal dialog with tabbed interface for adding partners
- **`Settings.tsx`**: Enhanced with tabbed interface for Bank Account and Trusted Partners
- **Search and Sort Integration**: Case-insensitive search with flexible column sorting

### Implementation Notes
- **Company Isolation**: All trusted partners are company-scoped with proper access control
- **Performance Optimization**: Database indexes on commonly filtered fields
- **Data Integrity**: Unique constraint prevents duplicate tax numbers per company
- **Hungarian Localization**: All UI elements and field labels in Hungarian
- **Error Handling**: Comprehensive validation for tax number formats and duplicate prevention
- **Statistics Maintenance**: Automatic tracking of invoice count and last invoice date per partner

## ✅ IMPLEMENTED: MNB Exchange Rate Integration

### Overview
The system integrates with the **Magyar Nemzeti Bank (MNB) official API** to retrieve and store USD and EUR exchange rates. This provides accurate, official exchange rates for currency conversion and financial calculations.

### Key Features

#### **Automatic Daily Synchronization**
- **GetCurrentExchangeRates**: Fetches today's official USD/EUR rates from MNB
- **GetExchangeRates**: Retrieves historical rates for date ranges
- **Scheduled Sync**: Can be configured to run multiple times daily (similar to NAV sync)
- **Performance**: Sync completes in ~2 seconds for 2 years of data (994 rates)

#### **Exchange Rate Storage**
- **Database Tables**: `ExchangeRate` and `ExchangeRateSyncLog`
- **Supported Currencies**: USD and EUR (expandable)
- **Decimal Precision**: 6 decimal places for accurate conversion
- **Historical Data**: Stores complete rate history with date indexing

#### **API Endpoints**
All endpoints accessible at `/api/exchange-rates/`:

- `GET /api/exchange-rates/` - List rates with filtering (currency, date_from, date_to)
- `GET /api/exchange-rates/current/` - Today's USD/EUR rates
- `GET /api/exchange-rates/latest/` - Most recent available rates
- `POST /api/exchange-rates/convert/` - Currency conversion to HUF
- `POST /api/exchange-rates/sync_current/` - Manual sync trigger (ADMIN only)
- `POST /api/exchange-rates/sync_historical/` - Historical backfill (ADMIN only)
- `GET /api/exchange-rates/sync_history/` - View sync logs
- `GET /api/exchange-rates/history/?currency=USD&days=30` - Rate history for charts

### Technical Implementation

#### **MNB SOAP Client** (`services/mnb_client.py`)
```python
class MNBClient:
    SOAP_URL = 'http://www.mnb.hu/arfolyamok.asmx'
    SOAP_NAMESPACE = 'http://www.mnb.hu/webservices/'

    def get_current_exchange_rates(currencies: List[str]) -> Dict[str, Decimal]
    def get_exchange_rates(start_date, end_date, currencies) -> Dict[str, Dict[str, Decimal]]
```

- **Direct HTTP SOAP requests** using `requests` library
- **XML parsing** with ElementTree
- **Decimal conversion**: Handles MNB comma-separated decimals (e.g., "331,16" → Decimal("331.16"))
- **Unit normalization**: Converts rates to per-1-unit format

#### **Sync Service** (`services/exchange_rate_sync_service.py`)
```python
class ExchangeRateSyncService:
    def sync_current_rates() -> ExchangeRateSyncLog
    def sync_historical_rates(days_back=730) -> ExchangeRateSyncLog

    @staticmethod
    def get_rate_for_date(date, currency) -> Decimal

    @staticmethod
    def convert_to_huf(amount, currency, conversion_date) -> Decimal
```

- **Transaction-wrapped** database operations
- **Upsert logic**: Creates or updates rates (prevents duplicates)
- **Audit logging**: Complete sync history with statistics
- **Smart fallback**: Returns latest available rate if exact date not found

#### **Database Schema**

**ExchangeRate Model:**
- `rate_date` - Date of the exchange rate
- `currency` - USD or EUR (expandable)
- `rate` - Exchange rate (Decimal 12,6)
- `unit` - Number of currency units (typically 1)
- `sync_date` - When fetched from MNB
- `source` - Always 'MNB' for official rates

**Unique Constraint:** `(rate_date, currency)`

**Indexes:**
- `(rate_date, currency)` - Fast lookups
- `(-rate_date)` - Latest rates queries
- `(currency)` - Currency filtering

**ExchangeRateSyncLog Model:**
- Complete audit trail of all sync operations
- Statistics: created count, updated count, duration
- Error tracking with status (SUCCESS/FAILED)

### Usage Examples

#### **Manual Sync (2 Years)**
```bash
curl -X POST http://localhost:8002/api/exchange-rates/sync_historical/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"days_back": 730, "currencies": ["USD", "EUR"]}'
```

#### **Get Current Rates**
```bash
curl http://localhost:8002/api/exchange-rates/current/ \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "USD": {"rate": "331.1600", "rate_date": "2025-10-01"},
  "EUR": {"rate": "389.0800", "rate_date": "2025-10-01"}
}
```

#### **Currency Conversion**
```bash
curl -X POST http://localhost:8002/api/exchange-rates/convert/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "amount": "100.00",
    "currency": "USD",
    "conversion_date": "2025-10-01"
  }'

# Response:
{
  "amount": "100.00",
  "currency": "USD",
  "conversion_date": "2025-10-01",
  "rate": "331.1600",
  "huf_amount": "33116.00"
}
```

### Scheduling Sync (Production)

**Automated Scheduler (Railway Production):**

The MNB exchange rate sync runs automatically on Railway using the same pattern as NAV sync:

- **Integration**: Django app startup via `BankTransfersConfig.ready()` in `apps.py`
- **Library**: APScheduler BackgroundScheduler with CronTrigger
- **Schedule**: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
- **Detection**: Only runs when `RAILWAY_ENVIRONMENT_NAME=production`
- **Logging**: Console output with 💱 emoji for easy monitoring

**Management Command:**

For manual sync or local testing:

```bash
# Sync current day rates
python manage.py sync_mnb_rates --current

# Sync historical rates (e.g., 90 days)
python manage.py sync_mnb_rates --days=90

# Sync specific currencies
python manage.py sync_mnb_rates --current --currencies=USD,EUR
```

**Monitoring on Railway:**

```bash
# Check scheduler logs
railway logs --filter="💱\|✅\|❌"

# Check sync results
railway run python manage.py shell -c "
from bank_transfers.models import ExchangeRateSyncLog
for log in ExchangeRateSyncLog.objects.order_by('-sync_start_time')[:5]:
    print(f'{log.sync_start_time}: {log.sync_status}, Created={log.rates_created}')
"
```

### Implementation Files

**Models & Migration:**
- `bank_transfers/models.py` - ExchangeRate and ExchangeRateSyncLog models
- `bank_transfers/migrations/0038_add_exchange_rate_models.py` - Database migration

**Services:**
- `bank_transfers/services/mnb_client.py` - MNB SOAP API client
- `bank_transfers/services/exchange_rate_sync_service.py` - Sync business logic

**API:**
- `bank_transfers/api_views.py` - ExchangeRateViewSet with 8 endpoints
- `bank_transfers/api_urls.py` - URL routing (`/api/exchange-rates/`)
- `bank_transfers/serializers.py` - ExchangeRateSerializer, ExchangeRateSyncLogSerializer, CurrencyConversionSerializer

**Management:**
- `bank_transfers/management/commands/sync_mnb_rates.py` - Manual sync command
- `bank_transfers/apps.py` - Automatic scheduler initialization (production)

**Admin:**
- `bank_transfers/admin.py` - Read-only admin interface with filtering

### Performance & Reliability

- **2-year historical sync**: 994 rates in 2.33 seconds
- **Daily sync**: < 0.1 seconds for 2 currencies
- **SOAP endpoint**: `http://www.mnb.hu/arfolyamok.asmx`
- **WSDL**: `https://www.mnb.hu/arfolyamok.asmx?wsdl`
- **Namespace prefix required**: Child elements must use `web:` prefix
- **Fallback logic**: Returns latest available rate if exact date missing

### Notes

- **Public API**: No authentication required for MNB API
- **Rate limits**: None documented (reasonable use expected)
- **Weekend/Holiday handling**: MNB returns last business day rate
- **Company isolation**: Exchange rates are global (not company-scoped)
- **Permissions**: All authenticated users can view rates, only ADMIN can trigger sync

### Currency Support & Limitations

#### **Current Limitation: USD and EUR Only**

The system is currently **restricted to USD and EUR** due to database model constraints:

```python
# bank_transfers/models.py - ExchangeRate model
CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
]
```

This constraint is enforced at three levels:
1. **Database Model**: `currency` field has `choices=CURRENCY_CHOICES`
2. **Service Default**: `DEFAULT_CURRENCIES = ['USD', 'EUR']`
3. **Command Default**: `--currencies=USD,EUR`

#### **MNB API Supports 33 Currencies**

The MNB API provides exchange rates for **33 currencies**, not just USD and EUR:

```
AUD (Australian Dollar), BGN (Bulgarian Lev), BRL (Brazilian Real),
CAD (Canadian Dollar), CHF (Swiss Franc), CNY (Chinese Yuan),
CZK (Czech Koruna), DKK (Danish Krone), EUR (Euro), GBP (British Pound),
HKD (Hong Kong Dollar), IDR (Indonesian Rupiah), ILS (Israeli Shekel),
INR (Indian Rupee), ISK (Icelandic Krona), JPY (Japanese Yen),
KRW (South Korean Won), MXN (Mexican Peso), MYR (Malaysian Ringgit),
NOK (Norwegian Krone), NZD (New Zealand Dollar), PHP (Philippine Peso),
PLN (Polish Zloty), RON (Romanian Leu), RSD (Serbian Dinar),
RUB (Russian Ruble), SEK (Swedish Krona), SGD (Singapore Dollar),
THB (Thai Baht), TRY (Turkish Lira), UAH (Ukrainian Hryvnia),
USD (US Dollar), ZAR (South African Rand)
```

#### **How to Add More Currencies**

**Step 1: Update Model**
```python
# bank_transfers/models.py
CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('CHF', 'Swiss Franc'),
    ('JPY', 'Japanese Yen'),
    # ... add more as needed
]

# OR remove constraint to accept any currency:
currency = models.CharField(
    max_length=3,
    # Remove choices parameter
    verbose_name="Deviza kód",
)
```

**Step 2: Create and Apply Migration**
```bash
python manage.py makemigrations bank_transfers -n add_currencies
python manage.py migrate
```

**Step 3: Update Service Defaults (Optional)**
```python
# bank_transfers/services/exchange_rate_sync_service.py
DEFAULT_CURRENCIES = ['USD', 'EUR', 'GBP', 'CHF']
```

**Step 4: Update Scheduler (Optional)**
```python
# bank_transfers/apps.py - start_mnb_scheduler()
call_command('sync_mnb_rates', '--current', '--currencies=USD,EUR,GBP,CHF')
```

#### **Manual Sync with Custom Currencies**

Once model constraints are updated, sync any supported currency:

```bash
# Sync specific currencies
python manage.py sync_mnb_rates --current --currencies=USD,EUR,GBP,CHF,JPY

# Historical sync with custom currencies
python manage.py sync_mnb_rates --days=730 --currencies=GBP,CHF

# Production (Railway)
railway run python manage.py sync_mnb_rates --current --currencies=USD,EUR,GBP
```

**Important**: The `--currencies` parameter works immediately for the MNB API call, but the **database will reject** currencies not in `CURRENCY_CHOICES`. Update the model first!

## ✅ IMPLEMENTED: Bank Statement Import and Transaction Matching

### Overview
The system implements a **multi-bank PDF statement import** feature with **sophisticated transaction matching** to NAV invoices and TransferBatch records. The implementation uses a **priority cascade** with **confidence-based scoring** and includes several enhancements beyond the original specification.

### Key Features

#### **Multi-Bank Statement Import**
- **Automatic Detection**: Factory pattern with adapter-based bank detection
- **Multiple Formats**: PDF, CSV, XML - each bank adapter handles its native format
- **Supported Banks** (4 total):
  1. **GRÁNIT Bank Nyrt.** (BIC: GNBAHUHB) - PDF format
  2. **Revolut Bank** (BIC: REVOLT21) - CSV format
  3. **MagNet Magyar Közösségi Bank** (BIC: MKKB) - XML (NetBankXML) format
  4. **K&H Bank Zrt.** (BIC: OKHBHUHB) - PDF format
- **Transaction Types**: AFR/SEPA transfers, POS/card purchases, bank fees, interest, corrections, currency exchanges
- **Duplicate Detection**: By SHA256 file hash + company + statement period
- **Automatic Matching**: Runs transparently during statement upload
- **Multi-Currency Support**: Exchange rates, original amounts, currency conversions

#### **Transaction Matching Engine**
The system implements **7 matching strategies** with **5 confidence levels** (0.60-1.00):

**Priority 1: TRANSFER_EXACT** (Confidence: 1.00)
- Matches bank transactions to executed TransferBatch transfers
- Only DEBIT transactions (outgoing payments)
- Exact amount + date match (±7 days) + beneficiary match
- **Auto-updates payment status**: ✅ YES

**Priority 2a: REFERENCE_EXACT** (Confidence: 1.00)
- Matches by invoice number or supplier tax number in transaction reference
- **Enhanced with direction checking** to prevent false positives
- Reference extraction with fallback: "Közlemény" → "Nem strukturált közlemény"
- **Auto-updates payment status**: ✅ YES

**Priority 2b: AMOUNT_IBAN** (Confidence: 0.95)
- Matches by exact amount + beneficiary IBAN
- Uses `invoice_gross_amount` (not `invoice_gross_amount_huf` which is frequently NULL)
- **Enhanced with direction checking**
- **Auto-updates payment status**: ✅ YES

**Priority 2c: FUZZY_NAME** (Confidence: 0.70-0.90)
- Matches by amount (±1%) + fuzzy name similarity (rapidfuzz library)
- Dynamic confidence: 0.70 + (similarity * 0.20)
- **Enhanced with direction checking**
- **Auto-updates payment status**: ❌ NO (requires manual review)

**Priority 2d: AMOUNT_DATE_ONLY** (Confidence: 0.60) ⚠️ **NEW**
- Fallback strategy for POS purchases with no merchant/beneficiary info
- Amount match (±1%) + date match + direction match only
- **No reference, No IBAN, No name verification**
- **Auto-updates payment status**: ❌ NO (LOW confidence, flagged for review)

**Priority 3: REIMBURSEMENT_PAIR** (Confidence: 0.70)
- Matches offsetting transactions (same amount, opposite signs)
- Within ±5 days, neither already matched
- Use case: Refunds, reversals, corrections
- **Auto-updates payment status**: ❌ NO (not invoice payment)

### Direction Compatibility Checking ⭐ **CRITICAL ENHANCEMENT**

The system prevents false positives by checking transaction direction compatibility:

```python
def _is_direction_compatible(transaction, invoice):
    if invoice.invoice_direction == 'OUTBOUND':  # We issued invoice
        return transaction.amount > 0  # Expect CREDIT (incoming payment)
    elif invoice.invoice_direction == 'INBOUND':  # We received invoice
        return transaction.amount < 0  # Expect DEBIT (outgoing payment)
```

**Impact**:
- ✅ Prevents 6 false NAV tax payment matches in test data
- ✅ All matches are directionally correct
- ✅ NAV tax payments (DEBIT with OUTBOUND invoice) correctly rejected

### Confidence Levels and Auto-Update Logic

| Confidence | Match Method | Auto-Update Payment Status | Manual Review Required |
|------------|--------------|----------------------------|------------------------|
| **1.00** | TRANSFER_EXACT | ✅ YES | ❌ No |
| **1.00** | REFERENCE_EXACT | ✅ YES | ❌ No |
| **0.95** | AMOUNT_IBAN | ✅ YES | ❌ No |
| **0.70-0.90** | FUZZY_NAME | ❌ NO | ✅ **Yes** |
| **0.70** | REIMBURSEMENT_PAIR | ❌ NO | ❌ No |
| **0.60** | AMOUNT_DATE_ONLY | ❌ NO | ✅ **Yes** (LOW) |

**Auto-Update Threshold**: `confidence >= 0.95`

### API Endpoints

#### **Bank Statement Management**
- `POST /api/bank-statements/upload/` - Upload and parse PDF statement
- `GET /api/bank-statements/` - List all statements with filtering
- `GET /api/bank-statements/{id}/` - Statement details
- `DELETE /api/bank-statements/{id}/` - Delete statement
- `POST /api/bank-statements/{id}/reparse/` - Reparse existing statement

#### **Bank Transaction Management**
- `GET /api/bank-transactions/` - List transactions with filtering
- `GET /api/bank-transactions/{id}/` - Transaction details
- `POST /api/bank-transactions/{id}/match_invoice/` - Manual invoice matching
- `POST /api/bank-transactions/{id}/categorize/` - Categorize as other cost

### Database Models

#### **BankStatement Model**
- Bank identification (bank_code, bank_name, bank_bic)
- Account details (account_number, account_iban)
- Statement period (statement_period_from, statement_period_to)
- Balances (opening_balance, closing_balance)
- File metadata (file_name, file_hash, file_size)
- Processing status (UPLOADED, PARSING, PARSED, ERROR)
- Statistics (total_transactions, matched_count, credit/debit counts)
- Company isolation with unique constraints

#### **BankTransaction Model**
- Transaction type (AFR_CREDIT, AFR_DEBIT, TRANSFER_CREDIT, TRANSFER_DEBIT, POS_PURCHASE, BANK_FEE, etc.)
- Dates (booking_date, value_date)
- Amount and currency
- AFR/Transfer fields (payment_id, payer/beneficiary name/IBAN, reference)
- POS/Card fields (card_number, merchant_name, merchant_location)
- **Matching fields**:
  - `matched_invoice` - ForeignKey to Invoice
  - `match_confidence` - Decimal (0.00 to 1.00)
  - `match_method` - Choice field with 7 methods
  - `matched_transfer` - ForeignKey to Transfer (for TRANSFER_EXACT)
  - `matched_reimbursement` - ForeignKey to self (for REIMBURSEMENT_PAIR)

### Test Results (January 2025 Statement)

**Before Enhancements**:
- Total transactions: 27
- Matched: 11/27 (40.7%)
- Problem: 7 false matches to same OUTBOUND invoice (NAV tax payments)

**After Direction Checking**:
- Total transactions: 27
- Matched: 5/27 (18.5%)
- False matches prevented: 6 NAV tax payments ✅

**After AMOUNT_DATE_ONLY Strategy**:
- Total transactions: 27
- **Matched: 15/27 (55.6%)** ✅
- Breakdown:
  - HIGH confidence (1.00): 3 matches → Auto-update
  - MEDIUM confidence (0.70-0.90): 1 match → Review
  - LOW confidence (0.60): 10 matches → Review
  - NOT MATCHED: 12 transactions (correct - no invoices exist)

**Quality Analysis**:
- ✅ All 15 matches are correct
- ✅ 6 false positives prevented
- ✅ Confidence levels accurately reflect match quality
- ✅ Low confidence matches flagged for manual review

### Implementation Files

**Models & Migration**:
- `bank_transfers/models.py` - BankStatement, BankTransaction, OtherCost models
- `bank_transfers/migrations/0039_add_bank_statement_models.py` - Database migration

**Services**:
- `bank_transfers/services/bank_statement_parser_service.py` - PDF parsing orchestration
- `bank_transfers/services/transaction_matching_service.py` - Matching engine with 7 strategies

**Bank Adapters**:
- `bank_transfers/bank_adapters/base.py` - Abstract adapter interface + NormalizedTransaction dataclass
- `bank_transfers/bank_adapters/factory.py` - BankAdapterFactory with automatic bank detection
- `bank_transfers/bank_adapters/granit_adapter.py` - GRÁNIT Bank PDF parser
- `bank_transfers/bank_adapters/revolut_adapter.py` - Revolut CSV parser
- `bank_transfers/bank_adapters/magnet_adapter.py` - MagNet XML parser (NetBankXML)
- `bank_transfers/bank_adapters/kh_adapter.py` - K&H Bank PDF parser
- `bank_transfers/bank_adapters/__init__.py` - Module exports

**API**:
- `bank_transfers/api_views.py` - BankStatementViewSet, BankTransactionViewSet
- `bank_transfers/serializers.py` - Serializers for statements and transactions

**Documentation**:
- `/BANK_STATEMENT_IMPORT_DOCUMENTATION.md` - Complete field mapping documentation (1200+ lines)
  - Covers all 4 banks with detailed field extraction patterns
  - Transaction type mapping for each bank
  - Special cases and workarounds documented
  - Test results and validation data

### Enhancements Beyond Original Specification

| Feature | Original Docs | Current Implementation | Status |
|---------|---------------|------------------------|--------|
| **REFERENCE_EXACT** | ✅ Planned | ✅ + Direction checking | **ENHANCED** |
| **AMOUNT_IBAN** | ✅ Planned | ✅ + Direction checking | **ENHANCED** |
| **FUZZY_NAME** | ✅ Planned | ✅ + Direction checking | **ENHANCED** |
| **MANUAL** | ✅ Planned | ✅ Implemented | ✅ AS SPEC |
| **TRANSFER_EXACT** | ❌ Not planned | ✅ Fully implemented | ⭐ **NEW** |
| **AMOUNT_DATE_ONLY** | ❌ Not planned | ✅ Fully implemented | ⭐ **NEW** |
| **REIMBURSEMENT_PAIR** | ❌ Not planned | ✅ Fully implemented | ⭐ **NEW** |
| **Direction checking** | ❌ Not planned | ✅ All strategies | ⭐ **NEW** |
| **Confidence levels** | ❌ Not specified | ✅ 5 levels (0.60-1.00) | ⭐ **NEW** |
| **Auto-update threshold** | ❌ Not specified | ✅ confidence ≥ 0.95 | ⭐ **NEW** |
| **Fallback reference** | ❌ Not planned | ✅ "Nem strukturált közlemény" | ⭐ **NEW** |
| **Amount field fix** | ❌ Not planned | ✅ Uses invoice_gross_amount | ⭐ **NEW** |

**Summary**:
- ✅ Original specification: **FULLY IMPLEMENTED**
- ⭐ **ENHANCED with 7 additional features**
- 🚀 Match rate: **55.6%** (15/27 matches)
- ✅ All matches directionally correct
- ✅ Low confidence matches flagged for review
- ✅ **Ready for production use**

### Notes

- **Bank format limitations**: AFR transactions in GRÁNIT Bank PDFs may not have "Közlemény" fields - this is the bank's PDF format, not a parser bug
- **Performance**: Matching uses indexed fields for fast filtering even with thousands of invoices
- **Company isolation**: All statements and transactions are company-scoped with proper access control
- **Feature flag**: BANK_STATEMENT_IMPORT feature must be enabled for company to access functionality
- **Permissions**: ADMIN and FINANCIAL roles can upload statements, all authenticated users can view

## Database Documentation

### 📋 DATABASE_DOCUMENTATION.md
**Location**: `/DATABASE_DOCUMENTATION.md`

This file contains the **single source of truth** for all database schema documentation including:
- Multi-company architecture tables
- Feature flag system tables  
- Role-based access control implementation
- NAV integration tables
- Complete table and column descriptions
- Performance indexes and constraints
- Troubleshooting guide for permissions

**⚠️ CRITICAL - DATABASE DOCUMENTATION REQUIREMENT**: 
**WHENEVER ANY DATABASE SCHEMA CHANGES ARE MADE, YOU MUST UPDATE ALL 3 FILES:**

1. **`/DATABASE_DOCUMENTATION.md`** - Master database schema documentation
2. **`/backend/sql/complete_database_comments_postgresql.sql`** - PostgreSQL comment script  
3. **`/backend/sql/complete_database_comments_sqlserver.sql`** - SQL Server comment script

**This includes:**
- New tables or columns
- Field modifications or renames  
- Model changes in `bank_transfers/models.py`
- Django migrations that affect database structure
- Any business logic changes that impact data meaning

**All 3 files must stay synchronized and complete. No exceptions.**

### Database Comment Scripts
**Locations**:
- **PostgreSQL (Production)**: `/backend/sql/complete_database_comments_postgresql.sql`
- **SQL Server (Development)**: `/backend/sql/complete_database_comments_sqlserver.sql`

These scripts add comprehensive table and column comments to the database schema:
- Generated from `DATABASE_DOCUMENTATION.md`
- Database-specific syntax (PostgreSQL `COMMENT ON` vs SQL Server extended properties)
- Complete coverage of all 16+ tables and hundreds of columns
- Verification queries to confirm comments were applied

**Usage**:
```bash
# PostgreSQL (Production)
psql -d your_database -f backend/sql/complete_database_comments_postgresql.sql

# SQL Server (Development)  
sqlcmd -S localhost,1435 -d administration -i backend/sql/complete_database_comments_sqlserver.sql
```

## Development Commands

### Backend
```bash
cd backend

# Install dependencies (first time)
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run development server on port 8002
python manage.py runserver 8002

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development server (bypasses CRACO/ESLint issues)
npx react-scripts start

# Run tests
npm test

# Build for production
npm run build
```

## Database Configuration

### ⚠️ CRITICAL: Settings Architecture

**DO NOT MODIFY** the environment detection system in `backend/transferXMLGenerator/settings.py`:

```python
# This structure is REQUIRED for Railway deployment
ENVIRONMENT = config('ENVIRONMENT', default='local')

if ENVIRONMENT == 'production':
    from .settings_production import *  # PostgreSQL with connection pooling
else:
    from .settings_local import *       # SQL Server for local development
```

**Why this matters:**
- Railway deployment **requires** `settings_production.py` for PostgreSQL connection pooling
- Local development uses `settings_local.py` for SQL Server 
- **Never put database config directly in main `settings.py`** - this breaks Railway deployment
- **Never set `DJANGO_SETTINGS_MODULE` in Railway** - let environment detection work

### Environment-Specific Database Config

**Local Development (SQL Server):**
- Host: localhost:1435
- Database: administration
- Uses `settings_local.py`
- Set `DB_PASSWORD` and `SECRET_KEY` in environment or `.env` file

**Production (Railway PostgreSQL):**
- Uses `settings_production.py` with connection pooling
- Railway provides `DATABASE_URL` automatically
- Requires `ENVIRONMENT=production` in Railway variables

## API Architecture

### Core ViewSets
- `AuthenticationViewSet`: User registration, login, company switching, profile management
- `BankAccountViewSet`: Manages originator accounts with default account functionality
- `BeneficiaryViewSet`: Handles beneficiary CRUD with filtering (frequent, active, search) - **Feature gated**
- `TransferTemplateViewSet`: Template management with beneficiary associations - **Feature gated**
- `TransferViewSet`: Individual transfers with bulk creation and XML/CSV export generation - **Feature gated**
- `TransferBatchViewSet`: Read-only batches created during XML/CSV export generation - **Feature gated**
- `TrustedPartnerViewSet`: Trusted partners management with automatic NAV invoice payment processing

### Authentication & Permission System
All ViewSets use **two-layer permission checking**:

1. **CompanyContextPermission**: Ensures user belongs to company and company is active
2. **Feature-specific permissions**: Check both company feature enablement AND user role permissions

**Example Permission Classes**:
- `RequiresBeneficiaryManagement`: Needs `BENEFICIARY_MANAGEMENT` feature + appropriate role
- `RequiresTransferManagement`: Needs `TRANSFER_MANAGEMENT` feature + appropriate role
- `RequiresExportGeneration`: Needs export features (`EXPORT_XML_SEPA`, `EXPORT_CSV_KH`) + appropriate role

### Key API Endpoints

#### Authentication & Company Management
- `POST /api/auth/register/`: User and company registration (simplified: username, email, names, password, company_name, company_tax_id) - automatically initializes default features
- `POST /api/auth/login/`: Login with JWT token + company context + enabled features
- `POST /api/auth/switch_company/`: Change active company context
- `GET /api/auth/profile/`: Get user profile and company memberships
- `GET /api/auth/features/`: Get enabled features for current company
- `POST /api/auth/force_logout/`: Admin force logout other users

#### Core Business Operations  
- `POST /api/transfers/bulk_create/`: Bulk transfer creation - **Requires TRANSFER_MANAGEMENT**
- `POST /api/transfers/generate_xml/`: XML file generation - **Requires EXPORT_XML_SEPA**
- `POST /api/transfers/generate_csv/`: CSV file generation - **Requires EXPORT_CSV_KH**
- `POST /api/templates/{id}/load_transfers/`: Generate transfers from template - **Requires TRANSFER_MANAGEMENT**
- `POST /api/import/excel/`: Import beneficiaries from Excel files - **Requires BULK_OPERATIONS**

#### Trusted Partners Management
- `GET /api/trusted-partners/`: List trusted partners with search and filtering
- `POST /api/trusted-partners/`: Create new trusted partner
- `PUT /api/trusted-partners/{id}/`: Update trusted partner details
- `DELETE /api/trusted-partners/{id}/`: Remove trusted partner
- `GET /api/trusted-partners/available_partners/`: Get available suppliers from NAV invoices

## Export Generation

### XML Export
The `utils.generate_xml()` function creates XML files with this structure:
- Root element: `<HUFTransactions>`
- Each transfer becomes a `<Transaction>` with Originator, Beneficiary, Amount, RequestedExecutionDate, and RemittanceInfo
- Supports HUF, EUR, USD currencies
- Unlimited transfers per batch
- Marks transfers as `is_processed=True` after XML generation

### CSV Export (KH Bank)
The `kh_export.py` module creates KH Bank CSV files:
- Hungarian "Egyszerűsített forintátutalás" format (.HUF.csv)
- Maximum 40 transfers per batch (KH Bank limitation)
- HUF currency only
- Marks transfers as `is_processed=True` after CSV generation

## Excel Import Format

Expected Excel structure (starting row 3):
- Column A: Comment (optional)
- Column B: Beneficiary name (required)
- Column C: Account number (required)  
- Column D: Amount (optional)
- Column E: Execution date (optional)
- Column F: Remittance info (optional)

## Template System

TransferTemplate allows for recurring transfer patterns:
- Templates contain multiple TemplateBeneficiary records
- Each template beneficiary has default amount and remittance info
- Templates can be loaded to pre-populate transfers for execution
- Useful for monthly payroll or recurring vendor payments

## Additional Tasks
# Transfer XML Generator - React Frontend Development

## Project Context
I have a **Django REST API backend** (100% complete) for a bank transfer XML generator system, and now need to build the **React TypeScript frontend**. The backend is running on `http://localhost:8002` with full Swagger documentation at `/swagger/`.

## Project Structure
```
transferXMLGenerator/          # Git repo root
├── backend/                   # Django REST API (COMPLETE)
│   ├── manage.py
│   ├── transferXMLGenerator/
│   ├── bank_transfers/
│   └── requirements.txt
└── frontend/                  # React TypeScript (TO BUILD)
    ├── src/
    ├── package.json
    └── public/
```

## Business Logic & User Workflow

### Core Use Case:
**Monthly transfer cycles for Hungarian bank payments**
1. **Setup (one-time)**: Import beneficiaries from Excel → build database
2. **Monthly routine**: Select template → load beneficiaries with default amounts → modify amounts/dates → generate XML for bank import
3. **Cycles**: "Month start payments", "VAT period", "Ad-hoc transfers"

### User Workflow:
1. Choose transfer template (e.g., "Monthly Payroll")
2. Template loads beneficiaries with default amounts
3. User modifies amounts, dates, remittance info
4. Add/remove beneficiaries as needed
5. Generate XML for bank system import

## Backend API (READY TO USE)

### Base URL: `http://localhost:8002/api/`

### Key Endpoints:
```typescript
// Beneficiaries
GET    /api/beneficiaries/              // List + filtering
POST   /api/beneficiaries/              // Create new
PUT    /api/beneficiaries/{id}/         // Update
DELETE /api/beneficiaries/{id}/         // Delete
GET    /api/beneficiaries/frequent/     // Frequent beneficiaries

// Templates  
GET    /api/templates/                  // Template list
POST   /api/templates/                  // Create template
POST   /api/templates/{id}/load_transfers/  // Load template → transfer data

// Transfers
POST   /api/transfers/bulk_create/      // Bulk create transfers
POST   /api/transfers/generate_xml/     // Generate XML

// Other
GET    /api/bank-accounts/default/      // Default account
POST   /api/upload/excel/               // Excel import
```

### Sample API Responses:
```json
// GET /api/beneficiaries/
{
  "results": [
    {
      "id": 1,
      "name": "NAV Personal Income Tax",
      "account_number": "10032000-06055950",
      "bank_name": "",
      "is_frequent": true,
      "is_active": true
    }
  ]
}

// POST /api/templates/1/load_transfers/
{
  "template": {
    "id": 1,
    "name": "Monthly Payroll",
    "beneficiary_count": 5
  },
  "transfers": [
    {
      "beneficiary": 1,
      "amount": "150000.00",
      "currency": "HUF",
      "execution_date": "2025-08-15",
      "remittance_info": "Monthly salary"
    }
  ]
}
```

## Frontend Requirements

### Tech Stack:
- **React 18** + **TypeScript**
- **TailwindCSS** for styling
- **React Query** for API state management
- **React Router** for navigation
- **Axios** for HTTP client
- **React Hook Form** for forms
- **Headless UI** for components

### Core Components to Build:

#### 1. **BeneficiaryManager** (Priority 1)
- CRUD table for beneficiaries
- Search, filter, pagination
- Inline editing capabilities
- Bulk operations
- Excel import functionality

#### 2. **TemplateBuilder** (Priority 2)  
- Create/edit transfer templates
- Add/remove beneficiaries to templates
- Set default amounts and remittance info
- Template management (activate/deactivate)

#### 3. **TransferWorkflow** (Priority 3 - MAIN FEATURE)
- Template selector dropdown
- Load template → populate transfer list
- Editable transfer list (amounts, dates, remittance)
- Add/remove transfers dynamically
- Real-time validation
- Export file generation and preview (XML/CSV)

#### 4. **ExportGenerator** (Priority 4)
- Export file preview with syntax highlighting (XML) or tabular format (CSV)
- Download generated export files (XML/CSV)
- Batch management
- Transfer history

#### 5. **Layout & Navigation**
- Modern sidebar navigation
- Responsive design
- Loading states and error handling
- Toast notifications

### UI/UX Requirements:
- **Modern, clean design** with Hungarian bank/finance feel
- **Responsive** - works on desktop and tablet
- **Fast interactions** - optimistic updates where possible
- **Clear visual hierarchy** - important actions stand out
- **Data-heavy tables** - good sorting, filtering, pagination
- **Form validation** - real-time feedback
- **Hungarian language** labels and text

### Key Features:
1. **Template-driven workflow** - core user journey
2. **Inline editing** - modify transfers without modal popups
3. **Bulk operations** - select multiple items for actions
4. **Real-time export preview** - see XML/CSV format as you build transfers
5. **Persistent state** - don't lose work on navigation
6. **Excel integration** - smooth import experience

## Development Approach:
1. **Setup** - Create React app, install dependencies, setup API client
2. **API Integration** - TypeScript interfaces, React Query hooks
3. **Core Layout** - Navigation, routing, basic structure
4. **BeneficiaryManager** - Full CRUD to validate API integration
5. **TransferWorkflow** - Main feature with template loading
6. **Polish** - Styling, error handling, edge cases

## Questions to Address:
- Should we use a specific component library (Mantine, Ant Design) or stick with Headless UI?
- How to handle optimistic updates for better UX?
- Any specific Hungarian banking UI conventions to follow?
- Preferred state management pattern (Context + useReducer vs React Query only)?

## Getting Started:
The backend is running and fully functional. Need to create the React frontend from scratch with the above requirements. Start with project setup and basic API integration, then build components incrementally.

## Expected XML Output Format

The system generates Hungarian bank-compatible XML for transfer imports. Here's the expected format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<HUFTransactions>
    <Transaction>
        <Originator>
            <Account>
                <AccountNumber>1210001119014874</AccountNumber>
            </Account>
        </Originator>
        <Beneficiary>
            <Name>Manninger Dániel ev.</Name>
            <Account>
                <AccountNumber>1177342500989949</AccountNumber>
            </Account>
        </Beneficiary>
        <Amount Currency="HUF">71600.00</Amount>
        <RequestedExecutionDate>2025-08-08</RequestedExecutionDate>
        <RemittanceInfo>
            <Text>2025-000052</Text>
        </RemittanceInfo>
    </Transaction>
    <Transaction>
        <Originator>
            <Account>
                <AccountNumber>1210001119014874</AccountNumber>
            </Account>
        </Originator>
        <Beneficiary>
            <Name>NAV Személyi jövedelemadó</Name>
            <Account>
                <AccountNumber>1003200006055950</AccountNumber>
            </Account>
        </Beneficiary>
        <Amount Currency="HUF">271000.00</Amount>
        <RequestedExecutionDate>2025-08-08</RequestedExecutionDate>
        <RemittanceInfo>
            <Text>28778367-2-16</Text>
        </RemittanceInfo>
    </Transaction>
</HUFTransactions>
```

### XML Structure Notes:
- **Clean account numbers** - no dashes or spaces (e.g., "10032000-06055950" → "1003200006055950")
- **Hungarian currency** - Always "HUF"
- **Date format** - ISO format "YYYY-MM-DD"
- **Encoding** - UTF-8 for Hungarian characters
- **Amount format** - Decimal with 2 places (e.g., "150000.00")

The backend `/api/transfers/generate_xml/` and `/api/transfers/generate_csv/` endpoints return XML and CSV formats respectively, and the frontend should display them with appropriate formatting for preview before download.

**Swagger documentation available at: http://localhost:8002/swagger/**
