# Bank Statement Import - Field Mapping Documentation

**Last Updated**: 2026-01-01
**System**: transferXMLGenerator - Multi-Bank Statement Import System

---

## Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [Supported Banks](#supported-banks)
4. [Field Mapping](#field-mapping)
   - [GRÁNIT Bank (PDF)](#gránit-bank-pdf)
   - [Revolut Bank (CSV)](#revolut-bank-csv)
   - [MagNet Bank (XML)](#magnet-bank-xml)
   - [K&H Bank (PDF)](#kh-bank-pdf)
   - [Raiffeisen Bank (PDF)](#raiffeisen-bank-pdf)
5. [Import Process](#import-process)
6. [Transaction Matching](#transaction-matching)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The bank statement import system supports multiple Hungarian and international banks with automatic detection, parsing, and transaction matching.

### Key Features

- **Multi-bank support** with automatic bank detection
- **Duplicate prevention** using SHA256 file hashing
- **Company isolation** - each company sees only their statements
- **Automatic transaction matching** to NAV invoices and executed transfers
- **Exchange rate tracking** for multi-currency transactions
- **Fee capture** for bank charges

### Architecture

```
Upload File (PDF/CSV/XLS)
    ↓
Calculate SHA256 Hash
    ↓
Check for Duplicates (by hash + company)
    ↓
Auto-Detect Bank (BankAdapterFactory)
    ↓
Parse Statement Metadata
    ↓
Parse All Transactions
    ↓
Save to Database (BankStatement + BankTransaction)
    ↓
Run Automatic Matching (Invoices, Transfers, Reimbursements)
```

---

## Database Schema

### BankStatement Model

Represents a single uploaded bank statement file.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `id` | BigAutoField | **Primary key** - unique file identifier | Auto-generated |
| `company` | ForeignKey | Company owner | Authenticated user's company |
| `bank_code` | CharField(20) | Bank identifier (e.g., 'GRANIT', 'REVOLUT') | Adapter detection |
| `bank_name` | CharField(200) | Bank display name | Adapter constant |
| `bank_bic` | CharField(11) | Bank BIC/SWIFT code | Adapter constant |
| `account_number` | CharField(50) | Account number from statement | Parsed from file |
| `account_iban` | CharField(34) | IBAN from statement | Parsed from file |
| `statement_number` | CharField(100) | Statement reference number | Parsed from file |
| `statement_period_from` | DateField | Statement start date | Parsed from file |
| `statement_period_to` | DateField | Statement end date | Parsed from file |
| `opening_balance` | Decimal(15,2) | Opening balance | Parsed from file |
| `closing_balance` | Decimal(15,2) | Closing balance | Parsed from file |
| `file_name` | CharField(255) | Original filename | Upload metadata |
| `file_hash` | CharField(64) | **SHA256 hash for duplicate check** | Calculated on upload |
| `file_size` | Integer | File size in bytes | Upload metadata |
| `file_path` | CharField(500) | Storage path | Generated |
| `uploaded_by` | ForeignKey(User) | User who uploaded | Authenticated user |
| `uploaded_at` | DateTimeField | Upload timestamp | Server time |
| `status` | CharField(20) | 'UPLOADED', 'PARSING', 'COMPLETED', 'ERROR' | Processing status |
| `total_transactions` | Integer | Number of transactions | Counted after parsing |
| `credit_count` | Integer | Number of credits | Calculated |
| `debit_count` | Integer | Number of debits | Calculated |
| `total_credits` | Decimal(15,2) | Sum of credits | Calculated |
| `total_debits` | Decimal(15,2) | Sum of debits | Calculated |
| `matched_count` | Integer | Successfully matched transactions | Matching result |
| `parse_error` | TextField | Error message if parsing failed | Error handling |
| `parse_warnings` | JSONField | Non-fatal warnings | Parser output |
| `raw_metadata` | JSONField | Bank-specific extra metadata | Parser output |

**Unique Constraint**: `(company_id, file_hash)` - prevents same file uploaded twice per company

---

### BankTransaction Model

Represents a single transaction from a bank statement.

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `id` | BigAutoField | **Primary key** - unique transaction ID | Auto-generated |
| `bank_statement` | ForeignKey | **Link to parent statement file** | CASCADE delete |
| `transaction_type` | CharField(20) | 'TRANSFER', 'POS', 'FEE', 'INTEREST', 'CORRECTION', 'OTHER' | Mapped from bank type |
| `booking_date` | DateField | **When bank processed transaction** | Critical for matching |
| `value_date` | DateField | **When amount was settled** | For interest calculations |
| `amount` | Decimal(15,2) | **Final amount (negative=debit, positive=credit)** | INCLUDES fees |
| `currency` | CharField(3) | Currency code (HUF, USD, EUR, etc.) | ISO 4217 |
| `description` | TextField | **Full transaction description** | For matching |
| `short_description` | CharField(200) | Brief description | For display |

#### Transfer-Specific Fields

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| `payment_id` | CharField(100) | Payment reference ID | GRÁNIT AFR |
| `transaction_id` | CharField(100) | Bank transaction ID | GRÁNIT, Revolut |
| `payer_name` | CharField(200) | **Who paid** (indexed) | Matching |
| `payer_iban` | CharField(34) | Payer's IBAN | Matching |
| `payer_account_number` | CharField(50) | Payer's account | Matching |
| `payer_bic` | CharField(11) | Payer's BIC | Verification |
| `beneficiary_name` | CharField(200) | **Who received** (indexed) | Matching |
| `beneficiary_iban` | CharField(34) | Beneficiary's IBAN | Matching |
| `beneficiary_account_number` | CharField(50) | Beneficiary's account | Matching |
| `beneficiary_bic` | CharField(11) | Beneficiary's BIC | Verification |
| `reference` | CharField(500) | **Common reference / Közlemény** | CRITICAL for invoice matching |
| `partner_id` | CharField(100) | End-to-end ID | Optional |
| `transaction_type_code` | CharField(20) | Bank-specific type code | Debugging |
| `fee_amount` | Decimal(15,2) | Transaction fee (positive) | Fee tracking |

#### POS/Card Payment Fields

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| `card_number` | CharField(20) | Masked card number | GRÁNIT, Revolut |
| `merchant_name` | CharField(200) | **Merchant/store name** | Matching |
| `merchant_location` | CharField(200) | Merchant location/code | GRÁNIT |
| `original_amount` | Decimal(15,2) | **Amount before FX conversion** | Multi-currency |
| `original_currency` | CharField(3) | **Currency before conversion** | Multi-currency |
| `exchange_rate` | Decimal(15,6) | **Exchange rate for conversion** | Multi-currency |

#### Matching Fields

| Field | Type | Description | Values |
|-------|------|-------------|--------|
| `matched_invoice` | ForeignKey(Invoice) | Matched NAV invoice | Null if no match |
| `matched_transfer` | ForeignKey(Transfer) | Matched transfer from batch | Null if no match |
| `matched_reimbursement` | ForeignKey(self) | Paired offsetting transaction | Null if no match |
| `match_confidence` | Decimal(3,2) | Confidence score (0.00 to 1.00) | 1.00 = exact |
| `match_method` | CharField(50) | How it was matched | See choices below |
| `match_notes` | TextField | Matching details | Audit trail |
| `matched_at` | DateTimeField | When matched | Timestamp |
| `matched_by` | ForeignKey(User) | Who matched (null = auto) | User or null |

**Match Methods**:
- `REFERENCE_EXACT` - Exact reference/közlemény match
- `AMOUNT_IBAN` - Amount + IBAN match
- `FUZZY_NAME` - Amount + name similarity ≥80%
- `TRANSFER_EXACT` - Matched to executed TransferBatch
- `REIMBURSEMENT_PAIR` - Offsetting transaction pair
- `MANUAL` - Manually matched by user

#### Metadata

| Field | Type | Description |
|-------|------|-------------|
| `raw_data` | JSONField | **Bank-specific extra data** |
| `created_at` | DateTimeField | Record creation time |
| `updated_at` | DateTimeField | Last modification time |

---

## Supported Banks

### 1. GRÁNIT Bank Nyrt.

- **Bank Code**: `GRANIT`
- **BIC**: `GNBAHUHB`
- **Format**: PDF
- **Detection**: Looks for "GRÁNIT Bank" or "GRANIT Bank" and BIC in PDF text
- **Status**: ✅ Production-ready

### 2. Revolut Bank

- **Bank Code**: `REVOLUT`
- **BIC**: `REVOLT21`
- **Format**: CSV
- **Detection**: Checks for CSV headers: "Date started (UTC)", "Date completed (UTC)", "Type", "State"
- **Status**: ✅ Production-ready

### 3. MagNet Magyar Közösségi Bank

- **Bank Code**: `MAGNET`
- **BIC**: `MKKB`
- **Format**: XML (NetBankXML)
- **Detection**: Checks for `<NetBankXML>` root element and "MagNet" or "MAGNET" in bank name
- **Status**: ✅ Production-ready

### 4. K&H Bank Zrt.

- **Bank Code**: `KH`
- **BIC**: `OKHBHUHB`
- **Format**: PDF
- **Detection**: Looks for "K&H Bank Zrt." and "BANKSZÁMLAKIVONAT" in PDF text
- **Status**: ✅ Production-ready

### 5. Raiffeisen Bank Zrt.

- **Bank Code**: `RAIFFEISEN`
- **BIC**: `UBRTHUHB`
- **Format**: PDF
- **Detection**: Checks for "RAIFFEISEN" and "UBRTHUHB" in PDF text with statement header "BANKSZ"
- **PDF Library**: PyPDF2 (preserves word spacing for all-caps names)
- **Character Encoding**: Custom CHAR_FIXES dictionary for Hungarian characters
- **Special Features**:
  - Multi-line company name handling with intelligent joining
  - CamelCase spacing (e.g., "ITCardigan" → "IT Cardigan")
  - Card merchant name extraction from line after "Referencia:"
  - Merchant name populated in `reference` field for UI display consistency
- **Status**: ✅ Production-ready

---

## Field Mapping

### Summary: PDF Parsers by Bank

Different banks require different PDF parsing libraries based on their PDF structure and encoding:

| Bank | Format | PDF Library | Why This Library? |
|------|--------|-------------|-------------------|
| **GRÁNIT Bank** | PDF | **pdfplumber** | Standard PDF format, works well for GRÁNIT's structure |
| **Revolut Bank** | CSV | N/A (CSV parser) | CSV format, no PDF parsing needed |
| **MagNet Bank** | XML | N/A (XML parser) | NetBankXML format, no PDF parsing needed |
| **K&H Bank** | PDF | **pdfplumber** | Standard PDF format, reliable text extraction |
| **Raiffeisen Bank** | PDF | **PyPDF2** | Preserves word spacing in all-caps names (pdfplumber doesn't) |

**Why different libraries?**

- **pdfplumber**: Works well for most Hungarian bank PDFs (GRÁNIT, K&H)
- **PyPDF2**: Required for Raiffeisen because:
  - Preserves word boundaries in uppercase company names ("DANUBIUS EXPERT ZRT." not "DANUBIUSEXPERTZRT.")
  - Better handling of Raiffeisen's specific PDF encoding
  - Maintains spacing in multi-word all-caps text

This is **NOT inconsistency** - it's adaptive engineering. Each bank's PDF format has different characteristics, and we use the best tool for each job.

---

### GRÁNIT Bank (PDF)

**Parser**: `GranitBankAdapter` (`bank_adapters/granit_adapter.py`)
**PDF Library**: pdfplumber
**Strategy**: Multi-line block parsing with regex extraction

#### Statement Metadata

| PDF Source | Field | Extraction Pattern |
|------------|-------|-------------------|
| Header: "GRÁNIT Bank" | `bank_name` | Constant |
| Header: BIC code | `bank_bic` | Regex: `\bGNBAHUHB\b` |
| Header: Account number | `account_number` | Regex: `Számlaszám:\s*([0-9\s-]+)` |
| Header: IBAN | `account_iban` | Regex: `IBAN:\s*(HU\d{2}\s?[\d\s]+)` |
| Header: Statement number | `statement_number` | Regex: `Kivonat:\s*(\d+)` |
| Header: Period | `period_from`, `period_to` | Regex: `Kivonat.*?(\d{4}\.\d{2}\.\d{2})\s*-\s*(\d{4}\.\d{2}\.\d{2})` |
| First balance line | `opening_balance` | Regex: `Nyitó egyenleg.*?([-\d\s]+)` |
| Last balance line | `closing_balance` | Regex: `Záró egyenleg.*?([-\d\s]+)` |

#### Transaction Fields

**Transaction Block Pattern**: Date line starts transaction, continues until next date line

| PDF Source | Field | Extraction Notes |
|------------|-------|-----------------|
| First line: `2025.01.31` | `booking_date` | Regex: `^\d{4}\.\d{2}\.\d{2}` |
| "Érték:" line | `value_date` | Regex: `Érték:\s*(\d{4}\.\d{2}\.\d{2})` |
| Amount line (terhelés/jóváírás) | `amount` | Negative for debit, positive for credit |
| "Terhelés/Jóváírás" | `currency` | Always HUF for GRÁNIT |
| Multi-line text | `description` | Full block text after cleaning |
| First line after date | `short_description` | Truncated to 200 chars |

**Transaction Type Detection**:

| Pattern in Description | `transaction_type` | Notes |
|------------------------|-------------------|-------|
| "Vásárlás POS terminálon" | `POS` | Card purchase |
| "Vásárlás belföld" | `POS` | Domestic card |
| "Vásárlás külföld" | `POS` | Foreign card |
| "Készp.kivét ATM-ből" | `POS` | ATM withdrawal |
| "AFR" | `TRANSFER` | SEPA transfer |
| "Átutalás" (IG2/IB/IG2) | `TRANSFER` | Bank transfer |
| "Jutalék" or "Díj" | `FEE` | Bank fee |
| "Kamat" | `INTEREST` | Interest |
| "Korrekció" | `CORRECTION` | Correction |
| Default | `OTHER` | Unknown type |

**POS Transaction Fields**:

| PDF Source | Field | Pattern |
|------------|-------|---------|
| "Kártyaszám:" | `card_number` | Regex: `Kártyaszám:\s*(\d+)` |
| "Hely:" | `merchant_location` | Regex: `Hely:\s*([^\n]+)` - Full capture, smart split on `:` |
| Merchant part of "Hely:" | `merchant_name` | After first `:` if no space after it |

**Special Logic for "Hely:" field**:
```
Example: "Hely: 00227731:AMZN Mktp DE*MK1FV4U15"
- merchant_location = "00227731:AMZN Mktp DE*MK1FV4U15" (full string)
- merchant_name = "AMZN Mktp DE*MK1FV4U15" (used for matching)
- reference = "AMZN Mktp DE*MK1FV4U15" (for better matching)

Logic: Split on ':' ONLY if space after it
"Hely: Shop Name" → merchant_location = "Shop Name"
"Hely: 123:Amazon" → merchant_location = "123:Amazon", merchant_name = "Amazon"
```

**AFR Transfer Fields**:

| PDF Source | Field | Pattern |
|------------|-------|---------|
| "Azonosítószám:" | `payment_id` | Regex: `Azonosítószám:\s*([^\n]+)` |
| "Tranzakció azonosító:" | `transaction_id` | Regex: `Tranzakció azonosító:\s*([^\n]+)` |
| "Kedvezményezett:" | `beneficiary_name` | Regex: `Kedvezményezett:\s*([^\n]+)` |
| "Számlaszám:" (in beneficiary block) | `beneficiary_account_number` | Regex after beneficiary |
| "IBAN:" (in beneficiary block) | `beneficiary_iban` | Regex: `IBAN:\s*(HU\d{2}[^\n]+)` |
| "BIC:" | `beneficiary_bic` | Regex: `BIC:\s*([A-Z]{6}[A-Z0-9]{2}[A-Z0-9]{3}?)` |
| "Nem strukturált közlemény:" | `reference` | Regex: `Nem strukturált közlemény:\s*([^\n]+)` |
| "Partnerek közti azonosító:" | `partner_id` | Regex: `Partnerek közti azonosító:\s*([^\n]+)` |
| "Tranzakció típus:" | `transaction_type_code` | Regex: `Tranzakció típus:\s*([^\n]+)` |

**Átutalás (IG2/IB) Transfer Fields**:

| PDF Source | Field | Pattern |
|------------|-------|---------|
| Line with "Név:" | `beneficiary_name` | Regex: `Név:\s*([^\n]+)` |
| "Számlaszám:" | `beneficiary_account_number` | Regex: `Számlaszám:\s*([^\n]+)` |
| "IBAN:" | `beneficiary_iban` | Regex: `IBAN:\s*(HU\d{2}[^\n]+)` |
| "BIC:" | `beneficiary_bic` | Regex: `BIC:\s*([A-Z0-9]+)` |
| "Közlemény:" | `reference` | Regex: `Közlemény:\s*([^\n]+)` |

**Fee Capture**:

Fees are usually on separate line with:
```
Pattern: "Előjegyzett jutalék" or "Díj"
Action: Create separate FEE transaction OR add to fee_amount of main transaction
```

---

### Revolut Bank (CSV)

**Parser**: `RevolutAdapter` (`bank_adapters/revolut_adapter.py`)
**Strategy**: CSV DictReader with column-based mapping

#### Statement Metadata

Revolut CSV has no header section, metadata is derived from transactions:

| CSV Source | Field | Logic |
|------------|-------|-------|
| Constant | `bank_name` | "Revolut Bank" |
| Constant | `bank_code` | "REVOLUT" |
| Constant | `bank_bic` | "REVOLT21" |
| First row: "Account" | `account_number` | e.g., "USD Main", "HUF Main" |
| Derived | `account_iban` | Empty (Revolut doesn't provide in CSV) |
| Generated | `statement_number` | Format: `REVOLUT_YYYYMMDD_YYYYMMDD` |
| Last row: "Date completed (UTC)" | `period_from` | Earliest date (CSV is newest-first) |
| First row: "Date completed (UTC)" | `period_to` | Latest date |
| Calculated | `opening_balance` | Last row balance - last row amount |
| First row: "Balance" | `closing_balance` | Latest balance |

#### Transaction Fields

**CSV Format**: 28 columns, header row, comma-separated

| CSV Column | Field | Transformation |
|------------|-------|----------------|
| `Date completed (UTC)` | `booking_date` | Parse ISO date (YYYY-MM-DD) |
| `Date completed (UTC)` | `value_date` | Same as booking_date |
| **`Total amount`** | `amount` | **USE THIS** (includes fees) |
| `Amount` | Stored in `raw_data` | Base amount without fees |
| `Payment currency` | `currency` | 3-letter code (USD, EUR, HUF) |
| `Type` | `transaction_type_code` | TRANSFER, CARD_PAYMENT, TOPUP, EXCHANGE, FEE |
| `Type` (mapped) | `transaction_type` | See mapping table below |
| `Description` | `description` | Full description |
| `Description` | `short_description` | Format: "{Type}: {Description}" |
| `ID` | `transaction_id` | Revolut's UUID |
| `Reference` | `reference` | Payment reference for matching |
| `State` | Filter | Only process "COMPLETED" |

**CRITICAL - Amount Field Selection**:

```
❌ WRONG: amount = row['Amount']
✅ CORRECT: amount = row['Total amount']

Why?
- Amount = transaction only (12362.60)
- Fee = fee charged (-24.73)
- Total amount = Amount + Fee (12387.33) ← ACTUAL account impact
```

**Transaction Type Mapping**:

| CSV Type | `transaction_type` | Notes |
|----------|-------------------|-------|
| `TRANSFER` | `TRANSFER` | Incoming/outgoing transfers |
| `CARD_PAYMENT` | `POS` | Card purchases at merchants |
| `TOPUP` | `TRANSFER` | Incoming deposits |
| `EXCHANGE` | `OTHER` | Currency exchanges |
| `FEE` | `FEE` | Bank fees |
| `ATM` | `POS` | ATM withdrawals |

**Fee Handling**:

| CSV Column | Field | Logic |
|------------|-------|-------|
| `Fee` | `fee_amount` | Always store as positive: `abs(fee)` |
| `Fee currency` | Stored in `raw_data` | Usually same as Payment currency |

**Original Amount - ALWAYS Populated**:

| CSV Column | Field | Logic |
|------------|-------|-------|
| `Orig currency` | `original_currency` | **ALWAYS populated** - Revolut provides for ALL transactions |
| `Orig amount` | `original_amount` | **ALWAYS populated** - Use CSV value as-is |

**Important**: Revolut provides `Orig currency` and `Orig amount` for **EVERY transaction**, not just currency conversions:
- For same-currency transactions (USD→USD): `Orig amount` = base transaction amount before fees
- For currency exchanges (EUR→USD): `Orig amount` = amount in original currency (with sign)
- `Orig amount` in CSV is **already signed correctly** (positive/negative) - use as-is

**Example**:
```
Transfer: -12362.60 USD (transaction) + -24.73 USD (fee) = -12387.33 USD (total)
- Amount:          -12387.33 USD  (total impact on account)
- Original Amount:  12362.60 USD  (base transaction amount, unsigned)
- Fee:              24.73 USD     (fee amount, always positive)

Exchange: HUF → USD
- Amount:          13000.00 USD   (what you received)
- Original Amount: -4299612.75 HUF (what you paid, signed)
```

**Exchange Rate**:

| CSV Column | Field | Notes |
|------------|-------|-------|
| `Exchange rate` | `exchange_rate` | Decimal(15,6) - stored in database field |
| `Exchange rate` | `raw_data['exchange_rate']` | Also in raw_data for debugging |
| `Amount` | `raw_data['base_amount_without_fee']` | Base amount without fees (for reconciliation) |

**Transfer-Specific Fields**:

| CSV Column | Field | Logic |
|------------|-------|-------|
| `Payer` | `payer_name` | For all transactions |
| `Description` (if amount < 0) | `beneficiary_name` | Extract after "To " |
| `Description` (if amount > 0) | `payer_name` | Extract after "From " |
| `Beneficiary account number` | `beneficiary_account_number` | Outgoing transfers only |
| `Beneficiary IBAN` | `beneficiary_iban` | Outgoing transfers |
| `Beneficiary BIC` | `beneficiary_bic` | Outgoing transfers |

**Card Payment Fields**:

| CSV Column | Field | Notes |
|------------|-------|-------|
| `Card number` | `card_number` | Masked format: 516760******9201 |
| `Description` | `merchant_name` | Merchant/store name |
| `MCC` | `raw_data['mcc']` | Merchant Category Code |
| `Payer` | `payer_name` | Cardholder name |

---

### MagNet Bank (XML)

**Parser**: `MagnetBankAdapter` (`bank_adapters/magnet_adapter.py`)
**Format**: XML (NetBankXML standard)
**Strategy**: XML element parsing with ElementTree

#### XML Structure

```xml
<NetBankXML>
  <FEJLEC>
    <KIBOCSATO>
      <Nev>MagNet Magyar Közösségi Bank Zrt.</Nev>
      <BIC>MKKB</BIC>
    </KIBOCSATO>
    <Bizonylat>
      <AlCim>2025-09</AlCim>
      <AlCimBiz>2025/0015/70009007</AlCimBiz>
    </Bizonylat>
  </FEJLEC>
  <SzamlaInfo>
    <Szamlaszam>16200151-18581773</Szamlaszam>
    <IBAN>HU1620015118581773</IBAN>
    <Tulajdonos>Company Name</Tulajdonos>
  </SzamlaInfo>
  <EgyenlegInfo>
    <NyitoEgyenleg Devizanem="HUF">1451017.00</NyitoEgyenleg>
    <ZaroEgyenleg Devizanem="HUF">5084547.00</ZaroEgyenleg>
  </EgyenlegInfo>
  <Tranzakcio NBID="169166462">
    <Tranzakcioszam>169166462</Tranzakcioszam>
    <Ellenpartner>Counterparty Name</Ellenpartner>
    <Ellenszamla>HU30 1201 1375 0184 9142 0010 0000</Ellenszamla>
    <Osszeg Devizanem="HUF">-57786.00</Osszeg>
    <Kozlemeny>Reference text</Kozlemeny>
    <Terhelesnap>2025.09.02.</Terhelesnap>
    <Ertekezes>2025.09.02.</Ertekezes>
    <Tipus>Transaction Type</Tipus>
    <TranzakcioKiegeszito>
      <KartyaKiegeszito>
        <Kartyaszam>558301******7539</Kartyaszam>
      </KartyaKiegeszito>
      <JutalekKiegeszito>
        <Osszeg Devizanem="HUF">970.00</Osszeg>
      </JutalekKiegeszito>
    </TranzakcioKiegeszito>
  </Tranzakcio>
</NetBankXML>
```

#### Statement Metadata

| XML Path | Field | Extraction |
|----------|-------|------------|
| `FEJLEC/KIBOCSATO/Nev` | `bank_name` | "MagNet Magyar Közösségi Bank" |
| `FEJLEC/KIBOCSATO/BIC` | `bank_bic` | "MKKB" |
| Constant | `bank_code` | "MAGNET" |
| `SzamlaInfo/Szamlaszam` | `account_number` | "16200151-18581773" |
| `SzamlaInfo/IBAN` | `account_iban` | "HU1620015118581773" |
| `FEJLEC/Bizonylat/AlCimBiz` | `statement_number` | "2025/0015/70009007" |
| `FEJLEC/Bizonylat/AlCim` | `period_from`, `period_to` | Parse "2025-09" → first/last day of month |
| `EgyenlegInfo/NyitoEgyenleg` | `opening_balance` | Decimal from text + @Devizanem attribute |
| `EgyenlegInfo/ZaroEgyenleg` | `closing_balance` | Decimal from text + @Devizanem attribute |

#### Transaction Fields

**Core Transaction Elements**:

| XML Path | Field | Notes |
|----------|-------|-------|
| `Tranzakcio/@NBID` | `transaction_id` | Unique bank transaction ID |
| `Tranzakcioszam` | `payment_id` | Transaction number |
| `Terhelesnap` | `booking_date` | Format: "2025.09.02." |
| `Ertekezes` | `value_date` | Format: "2025.09.02." |
| `Osszeg` | `amount` | Negative = debit, positive = credit |
| `Osszeg/@Devizanem` | `currency` | "HUF" |
| `Tipus` | `transaction_type_code` | Bank-specific type (max 100 chars) |
| `Kozlemeny` | `reference` | Payment reference/memo |
| `Ellenpartner` | counterparty name | Used for payer/beneficiary based on amount sign |
| `Ellenszamla` | counterparty account | IBAN format with spaces |

**Payer/Beneficiary Logic**:

```
If amount < 0 (debit):
  - payer_name = account holder (from SzamlaInfo/Tulajdonos)
  - beneficiary_name = Ellenpartner
  - beneficiary_iban = Ellenszamla (with spaces)
  - beneficiary_account_number = IBAN → account number conversion

If amount > 0 (credit):
  - payer_name = Ellenpartner
  - payer_iban = Ellenszamla (with spaces)
  - payer_account_number = IBAN → account number conversion
  - beneficiary_name = account holder
```

**IBAN to Account Number Conversion**:

MagNet provides IBANs in format: `HU30 1201 1375 0184 9142 0010 0000`

Conversion logic:
- Remove "HU" prefix and all spaces: `30120113750184914200100000`
- Extract bank code (3 digits): `301` → `30` (normalize)
- Extract first account part (8 digits): `12011375`
- Extract second account part (8 digits): `01849142`
- Result: `12011375-01849142`

**Transaction Type Detection**:

| Pattern in `Tipus` | `transaction_type` | Notes |
|--------------------|-------------------|-------|
| "bankkártya" | `POS` | Card transactions |
| "átutalás" or "afr" or "AFR" | `TRANSFER` | Bank transfers |
| "költség" or "díj" | `FEE` | Bank fees |
| Default | `OTHER` | Unknown types |

**Card Transaction Fields**:

| XML Path | Field | Notes |
|----------|-------|-------|
| `TranzakcioKiegeszito/KartyaKiegeszito/Kartyaszam` | `card_number` | Masked: "558301******7539" |
| `Ellenpartner` | `merchant_name` | Merchant name |
| `Kozlemeny` | `reference` | Card transaction details |

**Fee Fields**:

| XML Path | Field | Notes |
|----------|-------|-------|
| `TranzakcioKiegeszito/JutalekKiegeszito/Osszeg` | `fee_amount` | Transaction fee (always positive) |
| `TranzakcioKiegeszito/JutalekKiegeszito/Osszeg/@Devizanem` | Currency | Fee currency (usually HUF) |

**Description Format**:

MagNet descriptions are built from multiple fields:
```
"{Tipus} | Ellenpartner: {Ellenpartner} | Közlemény: {Kozlemeny}"

Examples:
- "Érkezett bankkártya terhelés | Ellenpartner: FEDEX EXPRESS HUNGARY | Közlemény: 558301******7539 ..."
- "AFR jóváírás bankon kívül | Ellenpartner: SZENT MAGDOLNA MAGÁNKÓRHÁZ | Közlemény: INV-2025-133"
```

**Transaction Type Code Examples**:

MagNet uses long, descriptive Hungarian transaction types (max 40 chars observed):
- `Érkezett bankkártya terhelés` (28 chars)
- `Érkezett bankkártya díj terhelés` (32 chars)
- `AFR terhelés átvezetés bankszla-k között` (40 chars)
- `Átutalás fogadás (IB/bankon belül)` (34 chars)
- `Átutalás (IB/IG2)` (17 chars)
- `AFR jóváírás bankon kívül` (24 chars)
- `AFR jóváírás bankon belül` (24 chars)

**Raw Data**:

Complete XML element is stored in `raw_data` field for debugging and future enhancements.

---

### K&H Bank (PDF)

**Parser**: `KHBankAdapter` (`bank_adapters/kh_adapter.py`)
**PDF Library**: pdfplumber
**Format**: PDF (BANKSZÁMLAKIVONAT)
**Strategy**: Multi-line block parsing with regex extraction

#### PDF Structure

K&H statements have a clean structure:
- **Page 1**: Cover page with legal disclaimers
- **Page 2+**: Transaction pages with header and table format
- **Last page**: Summary with opening/closing balances and totals

#### Statement Metadata

| PDF Source | Field | Extraction Pattern |
|------------|-------|-------------------|
| Page 2 header | `bank_name` | "K&H Bank Zrt." |
| Constant | `bank_code` | "KH" |
| Constant | `bank_bic` | "OKHBHUHB" |
| "Számlaszám:" | `account_number` | Regex: `Számlaszám:\s*([\d-]+)` |
| "Nemzetközi számlaszám (IBAN):" | `account_iban` | Regex: `Nemzetközi számlaszám \(IBAN\):\s*(HU\d{2}[\d\s]+)` |
| "Időszak:" | `period_from`, `period_to` | Regex: `Időszak:\s*(\d{4}\.\d{2}\.\d{2})-(\d{4}\.\d{2}\.\d{2})` |
| "Kivonat sorszám:" | `statement_number` | Regex: `Kivonat sorszám:\s*(\S+)` |
| Last page: "Könyvelt nyitóegyenleg:" | `opening_balance` | Regex: `Könyvelt nyitóegyenleg:\s*([\d\s-]+)` |
| Last page: "Könyvelt záróegyenleg:" | `closing_balance` | **Note**: Often corrupted in PDF extraction - calculated from totals |

**Closing Balance Calculation**:

K&H PDFs have a known issue where the closing balance is sometimes corrupted during text extraction (e.g., "2 445 589" extracted as "22 444455 558899"). The parser detects this and calculates the correct balance:

```
closing_balance = opening_balance + total_credits + total_debits
```

Where:
- `total_credits` from "Jóváírás összesen:"
- `total_debits` from "Terhelés összesen:"

#### Transaction Fields

**Transaction Format (Multi-line)**:

```
2025.09.03 2025.09.03 Azonnali Forint átutalás bankon kívül - 212 309
Ref.: BNK25246BJHLCKHJ Szla.:
HU60117200012248254300000000, ITMAN Számítástechnikai
Szolgáltató Kft. Közl.: SZA00456/2025 Hiv.:
00000000000000000000000000000000053
```

**First Line Pattern**: `booking_date value_date transaction_type [- debit_amount | credit_amount]`

| PDF Source | Field | Notes |
|------------|-------|-------|
| First column | `booking_date` | Format: "2025.09.03" |
| Second column | `value_date` | Format: "2025.09.03" |
| Transaction type text | `transaction_type_code` | Full K&H transaction type description |
| Last column | `amount` | Negative = debit (with "-" sign), Positive = credit |
| Constant | `currency` | "HUF" (default for K&H) |

**Additional Transaction Details**:

| PDF Pattern | Field | Notes |
|-------------|-------|-------|
| `Ref.: BNK...` | `transaction_id` | Bank reference ID |
| `Szla.: HU... Name` | `beneficiary_iban`, `beneficiary_name` (outgoing) | IBAN and name (may span multiple lines) |
| `Szla.: HU... Name` | `payer_iban`, `payer_name` (incoming) | Direction determined by amount sign |
| `Közl.: ...` | `reference` | Payment reference/memo (CRITICAL for matching) |
| `Hiv.: ...` | `payment_id` | Payment reference number |
| `Tr. azon.: ...` | `partner_id` | Transaction reference ID |
| `Árf.: 395.33 HUF/EUR` | `exchange_rate` | Exchange rate for foreign currency |
| `Eredeti összeg: 14100.00 EUR` | `original_amount`, `original_currency` | Original amount before conversion |

**Payer/Beneficiary Logic**:

```
If amount < 0 (debit/outgoing):
  - We are the payer
  - Extract beneficiary from "Szla.:" field
  - beneficiary_name, beneficiary_iban, beneficiary_account_number

If amount > 0 (credit/incoming):
  - We are the beneficiary
  - Extract payer from "Szla.:" field
  - payer_name, payer_iban, payer_account_number
```

**IBAN to Account Number Conversion**:

K&H provides Hungarian IBANs which are converted to account number format:

```
HU28 1041 0400 0000 0190 0489 4827
→
10410400-00000190-04894827

Format: 8 digits - 8 digits - 8 digits
```

**Transaction Type Detection**:

| Pattern in Type Text | `transaction_type` | Notes |
|----------------------|-------------------|-------|
| "díj" or "költség" | `FEE` | Bank fees and charges |
| "kamat" | `INTEREST` | Interest payments |
| "átutalás" or "sepa" or "nemzetközi" | `TRANSFER` | All transfer types |
| Default | `OTHER` | Unknown types |

**Transaction Type Examples**:

K&H uses descriptive Hungarian transaction types:
- `Forint átutalás elektronikus bankon kívül` - Regular transfer (outgoing)
- `Forint átutalás jóváírás` - Transfer credit (incoming)
- `Azonnali Forint átutalás bankon kívül` - Instant transfer (outgoing)
- `Azonnali Forint átutalás bankon belül` - Instant transfer (within K&H)
- `SEPA átutalás elektronikus` - SEPA transfer
- `Nemzetközi átutalás elektronikus` - International transfer
- `Forint átutalás díj elektronikus bankon kívül` - Transfer fee
- `Azonnali Forint átutalás díj bankon kívül` - Instant transfer fee
- `Deviza átutalás díj elektronikus` - Foreign currency transfer fee
- `Könyvelési díj` - Accounting fee
- `Számlavezetési díj` - Account maintenance fee
- `Kamat` - Interest

**Multi-Currency Transactions**:

For SEPA and international transfers with currency conversion:

```
2025.09.05 2025.09.05 SEPA átutalás elektronikus - 5 574 153
...
Árf.: 395.33 HUF/EUR Eredeti összeg: 14100.00 EUR
```

Fields populated:
- `amount`: -5574153 (HUF equivalent including fees)
- `currency`: "HUF"
- `original_amount`: -14100.00 (signed based on HUF amount)
- `original_currency`: "EUR"
- `exchange_rate`: 395.33

**Multi-Line Name Handling**:

Beneficiary/payer names often span multiple lines:

```
Szla.:
HU60117200012248254300000000, ITMAN Számítástechnikai
Szolgáltató Kft. Közl.: ...
```

Parser uses regex with `re.DOTALL` to capture multi-line names and concatenates them with spaces removed.

**Raw Data**:

Complete transaction block lines stored in `raw_data` field for debugging.

---

### Raiffeisen Bank (PDF)

**Parser**: `RaiffeisenBankAdapter` (`bank_adapters/raiffeisen_adapter.py`)
**PDF Library**: PyPDF2 (preserves word spacing, unlike pdfplumber)
**Strategy**: Transaction block parsing with PyPDF2 text extraction and character encoding cleanup

#### Key Technical Differences

**Why PyPDF2 instead of pdfplumber?**

Raiffeisen PDF statements require PyPDF2 because:
1. **Word spacing preservation**: "DANUBIUS EXPERT ZRT." extracted correctly (not "DANUBIUSEXPERTZRT.")
2. **All-caps company names**: PyPDF2 preserves word boundaries in uppercase text
3. **Clean text extraction**: Better handling of Raiffeisen's specific PDF encoding

**Character Encoding Issues**:

Raiffeisen PDFs use special encoding that mangles Hungarian characters. The adapter uses a `CHAR_FIXES` dictionary:

| Corrupted | Correct | Example |
|-----------|---------|---------|
| `£` | `á` | K**£**rtyatranzakci**©** → K**á**rtyatranzakci**ó** |
| `©` | `é` | K**©**zlem**©**ny → K**é**zlem**é**ny |
| `é` | `ö` | Sch**é**nherz → Sch**ö**nherz |
| `ë` | `ó` | **ë**sszeg → **ó**sszeg |
| `›` | `ő` | **›**sszes → **ő**sszes |
| `¶` | `Á` | **¶**tutalás → **Á**tutalás |
| `½` | `É` | **½**rt**©**k → **É**rt**é**k |
| `ï` | `ü` | **ï**zenet → **ü**zenet |
| `û` | `ű` | kí**û**tő → kí**ű**tő |

**Multi-line Company Name Handling**:

Raiffeisen company names often span multiple lines with intelligent joining:

```
Example: "Danubius Expert Consulting Z\nrt."

Logic:
- If next line starts with lowercase → Join WITHOUT space
  "Z" + "rt." → "Zrt." ✅ (not "Z rt.")
- If next line starts with uppercase → Join WITH space
  "Danubius" + "Expert" → "Danubius Expert" ✅
```

**CamelCase Spacing**:

```
Input: "ITCardiganKft."

Step 1: Handle acronyms - "ITCardigan" → "IT Cardigan"
  Pattern: ([A-Z]+)([A-Z][a-z]) → \1 \2

Step 2: Handle camelCase - "Cardigan" (already handled)
  Pattern: ([a-z])([A-Z]) → \1 \2

Output: "IT Cardigan Kft." ✅
```

#### Statement Metadata

| PDF Source | Field | Extraction Pattern |
|------------|-------|-------------------|
| Header | `bank_name` | "Raiffeisen Bank Zrt." (constant) |
| Constant | `bank_code` | "RAIFFEISEN" |
| Header | `bank_bic` | "UBRTHUHB" |
| "Számlaszám:" | `account_number` | Regex: `Számlaszám:\s*([\d-]+)` |
| "IBAN:" | `account_iban` | Regex: `IBAN:\s*(HU\d{2}[\d\s]+)` |
| "A kivonat időszaka:" | `period_from`, `period_to` | Regex: `(\d{4}\.\d{2}\.\d{2})\. - (\d{4}\.\d{2}\.\d{2})\.` |
| "A kivonat sorszáma:" | `statement_number` | Regex: `A kivonat sorszáma:\s*(\S+)` |
| "Nyitó egyenleg" | `opening_balance` | Regex: `Nyitó egyenleg\s+([\d\s.,]+)\s+HUF` |
| "Záró egyenleg" | `closing_balance` | Regex: `Záró egyenleg\s+([\d\s.,]+)\s+HUF` |

**Date Format**: "2025.12.31." (with trailing dot)

**Amount Format**: European with dots as thousand separators (e.g., "1.080.000,00")

#### Transaction Fields

**Transaction Block Pattern**:

Raiffeisen transactions start with a 10-digit ID and continue until next ID:

```
5411545603 2025.12.31. Kamat 8,31
2025.12.31.

5411545547 2025.12.31. Elektronikus forint átutalás -1.080.000,00
2025.12.22. Referencia: AFK25L0001950742
Kedvezményezett neve: Danubius Expert Consulting Zrt.
Kedvezményezett számlaszáma:
HU70167400152063900000000000
Közlemény: 20241231
Előjegyzett díj: 390,00 HUF Forgalmi jutalék
```

**First Line Pattern**: `transaction_id booking_date transaction_type amount`

| PDF Source | Field | Notes |
|------------|-------|-------|
| 10-digit ID | `transaction_id` | E.g., "5411545603" |
| After ID | `booking_date` | Format: "2025.12.31." (with dot) |
| Second line | `value_date` | Same format as booking date |
| Transaction type text | `transaction_type_code` | Full Raiffeisen description |
| Last column on first line | `amount` | European format, signed |
| Constant | `currency` | "HUF" |

**Additional Transaction Details**:

| PDF Pattern | Field | Character Cleanup |
|-------------|-------|-------------------|
| `Referencia: AFK...` | `payment_id` | ✅ Yes (applied to all extracted text) |
| `Közlemény: ...` | `reference` | ✅ Yes - **CRITICAL for invoice matching** |
| `Átutaló neve: ...` | `payer_name` (incoming) | ✅ Yes + CamelCase spacing + multi-line |
| `Átutaló számlaszáma: HU...` | `payer_iban`, `payer_account_number` | ✅ Yes |
| `Kedvezményezett neve: ...` | `beneficiary_name` (outgoing) | ✅ Yes + CamelCase spacing + multi-line |
| `Kedvezményezett számlaszáma: HU...` | `beneficiary_iban`, `beneficiary_account_number` | ✅ Yes |
| `Előjegyzett díj: ...` | `fee_amount` | ✅ Yes |

#### Card Transaction Handling

**Detection**: Card transactions have a masked card number pattern `\d{6}X+\d{4}`

**Merchant Name Extraction**:

```
Example:
Referencia:
BARIONP BARION.COM/GUE BUDAPEST  ← This line is the merchant name
Országkód: HU
```

**Card Transaction Fields**:

| PDF Pattern | Field | UI Display |
|-------------|-------|------------|
| `402115XXXXXX1446` | `card_number` | Masked card number |
| Line after "Referencia:" | `merchant_name` | Full merchant string |
| Line after "Referencia:" | `payer_name` | Same as merchant_name |
| **Line after "Referencia:"** | **`reference`** | **CRITICAL: Used for UI display** |
| `Országkód: HU` | `merchant_location` | Country code |

**Why merchant name goes in `reference` field?**

For UI display consistency with GRÁNIT Bank, which shows merchant names in the `reference` field for card transactions. This ensures the transaction table displays merchant information uniformly across all banks.

#### Transaction Type Detection

Raiffeisen uses detailed Hungarian transaction type descriptions:

| Pattern in Type Text | `transaction_type` | Direction | Notes |
|----------------------|-------------------|-----------|-------|
| "Kártyatranzakció" | `POS_PURCHASE` | Debit | Card purchase |
| "Kamat" + amount > 0 | `INTEREST_CREDIT` | Credit | Interest earned |
| "Kamat" + amount < 0 | `INTEREST_DEBIT` | Debit | Interest charged |
| "átutalás" + amount > 0 | `TRANSFER_CREDIT` | Credit | Incoming transfer |
| "átutalás" + amount < 0 | `TRANSFER_DEBIT` | Debit | Outgoing transfer |
| Default | `OTHER` | - | Unknown type |

**Directional Type Mapping**:

Unlike other adapters, Raiffeisen must add direction suffix to transaction types:

```python
if base_type == 'TRANSFER':
    return 'TRANSFER_CREDIT' if amount > 0 else 'TRANSFER_DEBIT'
elif base_type == 'INTEREST':
    return 'INTEREST_CREDIT' if amount > 0 else 'INTEREST_DEBIT'
```

This is required for BankTransaction model validation.

#### Transaction Type Examples

- `Elektronikus forint átutalás` - Electronic HUF transfer
- `Kártyatranzakció` - Card transaction
- `Kamat` - Interest
- `Azonnali átutalás` - Instant transfer
- `Készpénzfelvétel` - Cash withdrawal

#### Balance Validation

The adapter validates that transactions balance correctly:

```
opening_balance + sum(all transaction amounts) = closing_balance

Example from test statement:
Opening: 0.00
Total credits: +4,788,408.31
Total debits: -2,418,670.00
Net change: +2,369,738.31
Closing: 2,369,738.31 ✅ Matches!
```

#### Special Cases and Workarounds

**1. Multi-line Beneficiary Names**

Problem: Company names span multiple lines in PDF
```
Kedvezményezett neve: Danubius Expert Consulting Z
rt.
```

Solution: Join lines intelligently based on capitalization:
```python
if line.startswith_lowercase():
    join_without_space()  # "Zrt." not "Z rt."
else:
    join_with_space()     # "Expert Consulting"
```

**2. CamelCase Company Names**

Problem: PDF extraction merges words
```
ITCardiganKft.
```

Solution: Insert spaces using regex patterns:
```python
# Step 1: IT + Cardigan → "IT Cardigan"
re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)

# Step 2: Cardigan + Kft → "Cardigan Kft."
re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
```

**3. All-Uppercase Names**

Problem: pdfplumber loses word spacing in all-caps text
```
"DANUBIUSEXPERTZRT."  ❌ Wrong
```

Solution: Use PyPDF2 instead
```
"DANUBIUS EXPERT ZRT."  ✅ Correct
```

**4. Hungarian Character Corruption**

Problem: PDF encoding mangles Hungarian characters
```
"K£rtyatranzakci©"  ❌ Wrong (£=á corruption, ©=é corruption)
```

Solution: CHAR_FIXES dictionary cleanup
```
"Kártyatranzakció"  ✅ Correct
```

**5. Card Transaction Merchant Display**

Problem: UI shows empty reference for card transactions

Solution: Populate `reference` field with merchant name:
```python
if card_transaction:
    details['kozlemeny'] = merchant_name  # Used for reference field
```

This ensures UI displays merchant name consistently across all banks.

#### Test Coverage

The adapter has comprehensive test coverage (16 tests):

**Detection Tests (3)**:
- Valid Raiffeisen PDF detection ✅
- Invalid PDF rejection ✅
- Other bank PDF rejection ✅

**Parsing Tests (7)**:
- Metadata extraction (account, IBAN, period, balances) ✅
- Transaction count verification ✅
- Transfer transaction parsing ✅
- Card transaction parsing (with merchant extraction) ✅
- Interest transaction parsing ✅
- Transaction type enum validation ✅
- Balance calculation validation ✅

**Character Encoding Tests (2)**:
- Hungarian character cleanup ✅
- Normal text preservation ✅

**Name Formatting Tests (2)**:
- CamelCase spacing ("ITCardigan" → "IT Cardigan") ✅
- Multi-line company name joining ✅

**PyPDF2 Integration Tests (2)**:
- PyPDF2 library usage verification ✅
- All-caps name spacing validation ✅

Run tests: `pytest bank_transfers/tests/test_raiffeisen_adapter.py -v`

---

## Import Process

### 1. File Upload

```python
# API Endpoint: POST /api/bank-statements/upload/
# Service: BankStatementParserService.parse_and_save()

1. Read file bytes
2. Calculate SHA256 hash
3. Check for duplicate: BankStatement.objects.filter(company=company, file_hash=hash)
   - If exists → Reject with error "Ez a fájl már fel lett töltve korábban"
   - If new → Continue
4. Create BankStatement record with status='UPLOADED'
```

### 2. Bank Detection

```python
# Factory: BankAdapterFactory.get_adapter(file_bytes, filename)

For each registered adapter:
    if adapter.detect(file_bytes, filename):
        return adapter()

If no adapter matches:
    raise BankStatementParseError("Unsupported bank statement format")
```

### 3. Statement Parsing

```python
# Adapter: adapter.parse(file_bytes) → {metadata, transactions}

1. Update BankStatement with status='PARSING'
2. Extract statement metadata
3. Parse all transactions
4. Update BankStatement:
   - period_from, period_to
   - opening_balance, closing_balance
   - account_number, account_iban
   - total_transactions, credit_count, debit_count
   - status='COMPLETED'
```

### 4. Transaction Creation

```python
# For each parsed transaction:

1. Map to BankTransaction model
2. Set bank_statement = statement
3. Save to database
4. Update statement statistics
```

### 5. Automatic Matching

```python
# Service: TransactionMatchingService.match_all_transactions(statement)

For each transaction:
    1. Try TRANSFER_EXACT match (from executed TransferBatch)
    2. Try INVOICE match (NAV invoices)
       - REFERENCE_EXACT (közlemény exact match)
       - AMOUNT_IBAN (amount + IBAN match)
       - FUZZY_NAME (amount + name similarity ≥80%)
       - AMOUNT_DATE_ONLY (amount + date ±14 days, LOW confidence)
    3. Try REIMBURSEMENT_PAIR match (offsetting transactions)
    4. Save match results with confidence score
```

---

## Transaction Matching

### Matching Priority Order

1. **TRANSFER_EXACT** (confidence: 1.00)
   - Match bank transactions to executed TransferBatch transfers
   - Only checks batches with `used_in_bank=True`
   - Date window: ±14 days (bank processing delays)
   - Matching criteria:
     - Amount match (exact)
     - Currency match
     - Beneficiary name OR IBAN OR merchant name (≥80% similarity)

2. **REFERENCE_EXACT** (confidence: 1.00)
   - NAV invoice number in transaction reference
   - Pattern: Invoice number appears in `reference` field
   - Most reliable for invoice matching

3. **AMOUNT_IBAN** (confidence: 0.95)
   - Invoice amount + supplier IBAN match
   - Within ±7 days of invoice payment due date

4. **FUZZY_NAME** (confidence: 0.85)
   - Invoice amount + supplier name similarity ≥80%
   - Within ±7 days of invoice payment due date
   - Uses rapidfuzz for name matching

5. **AMOUNT_DATE_ONLY** (confidence: 0.60) ⚠️
   - Amount match only (within ±14 days)
   - **LOW CONFIDENCE** - requires manual review
   - Used as last resort

6. **REIMBURSEMENT_PAIR** (confidence: 0.70) ⚠️
   - Offsetting transactions (same amount, opposite signs)
   - Within ±30 days
   - **Requires manual review**

### Match Metadata

All matches populate these fields:

```python
transaction.matched_at = timezone.now()          # When matched
transaction.matched_by = user or None            # User (manual) or None (auto)
transaction.match_method = 'REFERENCE_EXACT'     # Method used
transaction.match_confidence = Decimal('1.00')   # Confidence score
transaction.match_notes = "Detailed explanation" # Audit trail
```

---

## Troubleshooting

### Common Issues

#### 1. Duplicate File Upload

**Error**: "Ez a fájl már fel lett töltve korábban"

**Cause**: File with same SHA256 hash already uploaded for this company

**Solution**:
- Check existing statements in database
- If needed, delete old statement first
- If file was modified, it will have different hash and upload successfully

#### 2. Unsupported Bank Format

**Error**: "Unsupported bank statement format"

**Cause**: No adapter can detect the bank from file content

**Solution**:
- Verify file is not corrupted
- Check if bank is supported (see Supported Banks section)
- If new bank, implement new adapter

#### 3. Parsing Errors

**Error**: Stored in `BankStatement.parse_error`

**Common causes**:
- PDF structure changed (bank updated format)
- Encoding issues
- Missing required fields

**Solution**:
- Check `parse_error` and `parse_warnings` fields
- Review adapter regex patterns
- Update adapter for new format

#### 4. Transaction Not Matching

**Symptoms**: Transaction has `matched_invoice=null`, `matched_transfer=null`

**Causes**:
- Reference/közlemény doesn't contain invoice number
- Name/IBAN doesn't match closely enough
- Date outside matching window
- Amount doesn't match exactly

**Solution**:
- Check match_notes for attempted matches
- Verify invoice data (amount, due date, supplier IBAN)
- Manually match if needed

#### 5. Wrong Amount Imported

**For Revolut specifically**:

**Symptom**: Amount doesn't match bank account movement

**Cause**: Using `Amount` column instead of `Total amount`

**Correct**:
```python
# ✅ CORRECT
amount = row['Total amount']  # Includes fees

# ❌ WRONG
amount = row['Amount']  # Excludes fees
```

#### 6. Missing Original Amount

**For Revolut imports**:

**Expected**: ALL transactions should have `original_amount` populated (100%)

**If NULL**:
- Check CSV file has "Orig amount" column populated
- Verify adapter version (old versions only populated for currency exchanges)
- Reimport with latest adapter code

#### 7. Exchange Rate Display

**Query exchange rates**:

```sql
SELECT
    id,
    booking_date,
    amount,
    currency,
    original_amount,
    original_currency,
    exchange_rate,
    raw_data->>'exchange_rate' as raw_rate
FROM bank_transfers_banktransaction
WHERE exchange_rate IS NOT NULL;
```

**Expected**: All EXCHANGE type transactions have `exchange_rate` populated

---

## Raw Data Storage

Both adapters store bank-specific extra data in `raw_data` JSON field:

### GRÁNIT Raw Data

```json
{
  "full_block_text": "Multi-line transaction text from PDF",
  "line_number": 123,
  "page_number": 2
}
```

### Revolut Raw Data

```json
{
  "Date started (UTC)": "2025-09-20",
  "Card label": "Standard",
  "Card state": "BLOCKED",
  "MCC": "5311",
  "exchange_rate": "1.167376",
  "base_amount_without_fee": "12362.60",
  "Related transaction id": "",
  "Spend program": ""
}
```

---

## Adding New Bank Support

### Step 1: Create Adapter

Create `bank_adapters/{bank_name}_adapter.py`:

```python
from .base import BankStatementAdapter, NormalizedTransaction, StatementMetadata

class NewBankAdapter(BankStatementAdapter):
    BANK_CODE = 'NEWBANK'
    BANK_NAME = 'New Bank Name'
    BANK_BIC = 'NEWBKHUH'

    @classmethod
    def detect(cls, file_bytes: bytes, filename: str) -> bool:
        # Return True if this adapter can handle the file
        pass

    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        # Return {'metadata': StatementMetadata, 'transactions': List[NormalizedTransaction]}
        pass
```

### Step 2: Register Adapter

Update `bank_adapters/__init__.py`:
```python
from .new_bank_adapter import NewBankAdapter

__all__ = [..., 'NewBankAdapter']
```

Update `bank_adapters/factory.py`:
```python
from .new_bank_adapter import NewBankAdapter

class BankAdapterFactory:
    _adapters = [
        GranitBankAdapter,
        RevolutAdapter,
        NewBankAdapter,  # Add here
    ]
```

### Step 3: Update Documentation

Add field mapping to this document!

---

## Database Queries

### Get all transactions from a specific file

```sql
SELECT bt.*
FROM bank_transfers_banktransaction bt
WHERE bt.bank_statement_id = 34;
```

### Get matched transactions with invoice details

```sql
SELECT
    bt.id,
    bt.booking_date,
    bt.amount,
    bt.description,
    bt.match_method,
    bt.match_confidence,
    i.nav_invoice_number,
    i.supplier_name,
    i.invoice_gross_amount
FROM bank_transfers_banktransaction bt
LEFT JOIN bank_transfers_invoice i ON bt.matched_invoice_id = i.id
WHERE bt.bank_statement_id = 34
  AND bt.matched_invoice_id IS NOT NULL;
```

### Find unmatched transactions

```sql
SELECT *
FROM bank_transfers_banktransaction
WHERE bank_statement_id = 34
  AND matched_invoice_id IS NULL
  AND matched_transfer_id IS NULL
  AND matched_reimbursement_id IS NULL;
```

### Get exchange rate data from Revolut

```sql
SELECT
    id,
    booking_date,
    amount,
    currency,
    original_amount,
    original_currency,
    raw_data->>'exchange_rate' as exchange_rate,
    raw_data->>'base_amount_without_fee' as base_amount,
    description
FROM bank_transfers_banktransaction
WHERE bank_statement_id = 35
  AND transaction_type_code = 'EXCHANGE';
```

---

## Changelog

### 2025-10-21 - Initial Documentation
- Created comprehensive field mapping for GRÁNIT and Revolut
- Documented all database fields and their sources
- Added import process flow
- Added troubleshooting section

### 2025-10-21 - Revolut Fixes (v3 - FINAL)
- **CRITICAL FIX**: Changed from `Amount` to `Total amount` to include fees
- **FIX**: **ALL transactions now have original_amount populated** (100%, not just exchanges)
- **FIX**: Use CSV Orig amount as-is (already signed correctly)
- **NEW FIELD**: Added `exchange_rate` field to BankTransaction model (Decimal 15,6)
- **FIX**: Exchange rate now stored in both `exchange_rate` field AND `raw_data`
- **FIX**: Raw data from CSV now properly stored for all transactions
- **FIX**: Fixed opening/closing balance calculation (CSV is newest-first)

**Migration**: Run `python manage.py migrate` to add exchange_rate field

**Reimport Note**: If you imported Revolut statements before 2025-10-21, delete and reimport to get:
- original_amount for all transactions (100%)
- exchange_rate for EXCHANGE transactions
- Complete raw_data storage

### 2025-10-21 - MagNet Bank XML Support
- **NEW BANK**: Added MagNet Magyar Közösségi Bank support
- **FORMAT**: NetBankXML format with ElementTree parsing
- **FEATURES**:
  - Full statement metadata extraction (account, IBAN, balances, period)
  - 45 transactions parsed successfully from test file
  - Card transaction support with card numbers
  - IBAN to account number conversion
  - Fee extraction from `JutalekKiegeszito` element
  - Transaction type mapping (POS, TRANSFER, FEE, OTHER)
- **FIELD FIX**: Increased `transaction_type_code` from 20 to 100 chars (MagNet uses long descriptive types)
- **VALIDATION**: Balance verification passes ✓

**Migration**: Run `python manage.py migrate` to increase transaction_type_code field size

**Test Results**:
- 45/45 transactions imported successfully
- 13 card transactions with card numbers
- 13 transfers with IBAN details
- 13 transactions with fees (total 29,041 HUF)
- Balance match verified: Opening 1,451,017 + Changes 3,633,530 = Closing 5,084,547 ✓

### 2025-10-22 - K&H Bank PDF Support
- **NEW BANK**: Added K&H Bank Zrt. support
- **FORMAT**: PDF (BANKSZÁMLAKIVONAT) with multi-line transaction parsing
- **FEATURES**:
  - Complete statement metadata extraction
  - Multi-line beneficiary/payer name handling
  - IBAN to account number conversion
  - Multi-currency transaction support (SEPA, international)
  - Exchange rate and original amount extraction
  - Intelligent closing balance calculation (handles PDF extraction corruption)
- **PDF WORKAROUND**: K&H PDFs have corrupted closing balance extraction - parser calculates from totals automatically
- **VALIDATION**: Balance verification passes ✓

**Test Results**:
- 31/31 transactions imported successfully
- Beneficiary names correctly parsed across multiple lines
- Multi-currency SEPA transactions with exchange rates
- Closing balance calculated correctly: Opening 290,065 + Credits 16,970,904 + Debits -14,815,380 = Closing 2,445,589 ✓
- 3 transactions auto-matched (9.7% match rate)

---

**End of Documentation**
