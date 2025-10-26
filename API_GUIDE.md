# API Guide

This document contains API endpoint documentation and testing guidelines for the Transfer XML Generator system.

## Table of Contents
- [API Architecture](#api-architecture)
- [Authentication & Company Management](#authentication--company-management)
- [Core Business Operations](#core-business-operations)
- [Export Generation](#export-generation)
- [API Testing with curl](#api-testing-with-curl)
- [Frontend Development Guide](#frontend-development-guide)

---

## API Architecture

### Base URL
- **Development**: `http://localhost:8002/api/`
- **Swagger Docs**: `http://localhost:8002/swagger/`

### Core ViewSets
- `AuthenticationViewSet`: User registration, login, company switching, profile management
- `BankAccountViewSet`: Manages originator accounts with default account functionality
- `BeneficiaryViewSet`: Handles beneficiary CRUD with filtering - **Feature gated**
- `TransferTemplateViewSet`: Template management with beneficiary associations - **Feature gated**
- `TransferViewSet`: Individual transfers with bulk creation and XML/CSV export - **Feature gated**
- `TransferBatchViewSet`: Read-only batches created during XML/CSV export - **Feature gated**
- `TrustedPartnerViewSet`: Trusted partners management with automatic NAV invoice payment
- `ExchangeRateViewSet`: Exchange rate management and currency conversion
- `BankStatementViewSet`: Bank statement upload and parsing
- `BankTransactionViewSet`: Transaction management and matching

### Authentication & Permission System
All ViewSets use **two-layer permission checking**:

1. **CompanyContextPermission**: Ensures user belongs to company and company is active
2. **Feature-specific permissions**: Check both company feature enablement AND user role permissions

**Example Permission Classes**:
- `RequiresBeneficiaryManagement`: Needs `BENEFICIARY_MANAGEMENT` feature + appropriate role
- `RequiresTransferManagement`: Needs `TRANSFER_MANAGEMENT` feature + appropriate role
- `RequiresExportGeneration`: Needs export features (`EXPORT_XML_SEPA`, `EXPORT_CSV_KH`) + appropriate role

---

## Authentication & Company Management

### User Registration
```bash
POST /api/auth/register/

# Request Body
{
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123!",
  "company_name": "Example Corp",
  "company_tax_id": "12345678-2-16"
}

# Response
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "company": {
    "id": 1,
    "name": "Example Corp",
    "tax_id": "12345678-2-16"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1Q...",
    "refresh": "eyJ0eXAiOiJKV1Q..."
  }
}
```

### User Login
```bash
POST /api/auth/login/

# Request Body
{
  "username": "johndoe",
  "password": "SecurePass123!"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "company": {
    "id": 1,
    "name": "Example Corp",
    "tax_id": "12345678-2-16"
  },
  "enabled_features": [
    "BENEFICIARY_MANAGEMENT",
    "TRANSFER_MANAGEMENT",
    "EXPORT_XML_SEPA"
  ]
}
```

### Other Authentication Endpoints
- `POST /api/auth/switch_company/` - Change active company context
- `GET /api/auth/profile/` - Get user profile and company memberships
- `GET /api/auth/features/` - Get enabled features for current company
- `POST /api/auth/force_logout/` - Admin force logout other users

---

## Core Business Operations

### Beneficiaries
```bash
# List beneficiaries
GET /api/beneficiaries/?search=NAV&is_active=true

# Create beneficiary
POST /api/beneficiaries/
{
  "name": "NAV Personal Income Tax",
  "account_number": "10032000-06055950",
  "bank_name": "",
  "is_frequent": true,
  "is_active": true
}

# Update beneficiary
PUT /api/beneficiaries/{id}/

# Delete beneficiary
DELETE /api/beneficiaries/{id}/

# Get frequent beneficiaries
GET /api/beneficiaries/frequent/
```

### Transfer Templates
```bash
# List templates
GET /api/templates/

# Create template
POST /api/templates/
{
  "name": "Monthly Payroll",
  "description": "Recurring monthly salary payments",
  "is_active": true
}

# Load template to generate transfers
POST /api/templates/{id}/load_transfers/

# Response
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

### Transfers
```bash
# Bulk create transfers
POST /api/transfers/bulk_create/
{
  "transfers": [
    {
      "beneficiary_id": 1,
      "amount": "150000.00",
      "currency": "HUF",
      "execution_date": "2025-08-15",
      "remittance_info": "Monthly salary"
    }
  ]
}

# Generate XML export
POST /api/transfers/generate_xml/
{
  "transfer_ids": [1, 2, 3]
}

# Generate CSV export (KH Bank)
POST /api/transfers/generate_csv/
{
  "transfer_ids": [1, 2, 3]
}
```

### Trusted Partners
```bash
# List trusted partners
GET /api/trusted-partners/?search=ACME&ordering=-last_invoice_date

# Create trusted partner
POST /api/trusted-partners/
{
  "partner_name": "ACME Corporation",
  "tax_number": "12345678-2-16",
  "is_active": true,
  "auto_pay": true
}

# Update trusted partner
PUT /api/trusted-partners/{id}/

# Delete trusted partner
DELETE /api/trusted-partners/{id}/

# Get available partners from NAV invoices
GET /api/trusted-partners/available_partners/?search=ACME&ordering=partner_name
```

### Exchange Rates
```bash
# Get current rates
GET /api/exchange-rates/current/

# Response
{
  "USD": {"rate": "331.1600", "rate_date": "2025-10-01"},
  "EUR": {"rate": "389.0800", "rate_date": "2025-10-01"}
}

# Get latest rates
GET /api/exchange-rates/latest/

# Currency conversion
POST /api/exchange-rates/convert/
{
  "amount": "100.00",
  "currency": "USD",
  "conversion_date": "2025-10-01"
}

# Response
{
  "amount": "100.00",
  "currency": "USD",
  "conversion_date": "2025-10-01",
  "rate": "331.1600",
  "huf_amount": "33116.00"
}

# Manual sync (ADMIN only)
POST /api/exchange-rates/sync_current/
POST /api/exchange-rates/sync_historical/
{
  "days_back": 730,
  "currencies": ["USD", "EUR"]
}

# View sync history
GET /api/exchange-rates/sync_history/

# Get rate history for charts
GET /api/exchange-rates/history/?currency=USD&days=30
```

### Bank Statements
```bash
# Upload and parse bank statement
POST /api/bank-statements/upload/
Content-Type: multipart/form-data

file: [PDF/CSV/XML file]

# List statements
GET /api/bank-statements/?bank_code=GNBAHUHB

# Get statement details
GET /api/bank-statements/{id}/

# Delete statement
DELETE /api/bank-statements/{id}/

# Reparse statement
POST /api/bank-statements/{id}/reparse/
```

### Bank Transactions
```bash
# List transactions
GET /api/bank-transactions/?statement_id=1&matched=true

# Get transaction details
GET /api/bank-transactions/{id}/

# Manual invoice matching
POST /api/bank-transactions/{id}/match_invoice/
{
  "invoice_id": 123
}

# Categorize as other cost
POST /api/bank-transactions/{id}/categorize/
{
  "cost_category": "office_supplies",
  "notes": "Monthly stationery"
}
```

### Excel Import
```bash
# Import beneficiaries from Excel
POST /api/import/excel/
Content-Type: multipart/form-data

file: [Excel file]

# Expected Excel structure (starting row 3):
# Column A: Comment (optional)
# Column B: Beneficiary name (required)
# Column C: Account number (required)
# Column D: Amount (optional)
# Column E: Execution date (optional)
# Column F: Remittance info (optional)
```

---

## Export Generation

### XML Export Format
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
</HUFTransactions>
```

### XML Structure Notes
- **Clean account numbers** - no dashes or spaces (e.g., "10032000-06055950" → "1003200006055950")
- **Hungarian currency** - Always "HUF"
- **Date format** - ISO format "YYYY-MM-DD"
- **Encoding** - UTF-8 for Hungarian characters
- **Amount format** - Decimal with 2 places (e.g., "150000.00")
- **Unlimited transfers** per batch
- Marks transfers as `is_processed=True` after XML generation

### CSV Export (KH Bank)
- Hungarian "Egyszerűsített forintátutalás" format (.HUF.csv)
- **Maximum 40 transfers** per batch (KH Bank limitation)
- **HUF currency only**
- Marks transfers as `is_processed=True` after CSV generation

---

## API Testing with curl

### Step 1: Login and Extract Token

```bash
# Login and save response
curl -s -X POST http://localhost:8002/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"tothi","password":"Almafa+123"}' \
  -o /tmp/login.json

# Extract token using grep and cut
TOKEN=$(grep -o '"access":"[^"]*"' /tmp/login.json | cut -d'"' -f4)

# Save token to file for reuse
echo $TOKEN > /tmp/tok.txt
```

### Step 2: Use Token for API Calls

```bash
# Example: Upload bank statement
curl -s -X POST http://localhost:8002/api/bank-statements/upload/ \
  -H "Authorization: Bearer $(cat /tmp/tok.txt)" \
  -F 'file=@path/to/statement.pdf'

# Example: GET request
curl -s -X GET http://localhost:8002/api/bank-statements/ \
  -H "Authorization: Bearer $(cat /tmp/tok.txt)"

# Example: POST request with JSON
curl -s -X POST http://localhost:8002/api/exchange-rates/convert/ \
  -H "Authorization: Bearer $(cat /tmp/tok.txt)" \
  -H 'Content-Type: application/json' \
  -d '{"amount":"100.00","currency":"USD","conversion_date":"2025-10-01"}'
```

### Key Points for curl Usage
- **Always use single quotes** around JSON data in `-d` parameter
- **Save token to file** to avoid shell escaping issues with subshells
- **Use `grep` and `cut`** instead of Python/jq for token extraction (more reliable in zsh)
- **Save response to file** (`-o /tmp/file.json`) before processing
- **Never pipe directly to Python** - it causes eval errors in zsh

---

## Frontend Development Guide

### Project Context
The backend is a **Django REST API** (100% complete) running on `http://localhost:8002` with full Swagger documentation at `/swagger/`.

### Business Logic & User Workflow

#### Core Use Case
**Monthly transfer cycles for Hungarian bank payments**:
1. **Setup (one-time)**: Import beneficiaries from Excel → build database
2. **Monthly routine**: Select template → load beneficiaries with default amounts → modify amounts/dates → generate XML for bank import
3. **Cycles**: "Month start payments", "VAT period", "Ad-hoc transfers"

#### User Workflow
1. Choose transfer template (e.g., "Monthly Payroll")
2. Template loads beneficiaries with default amounts
3. User modifies amounts, dates, remittance info
4. Add/remove beneficiaries as needed
5. Generate XML for bank system import

### Frontend Tech Stack
- **React 18** + **TypeScript**
- **Material-UI** for components
- **React Query** for API state management
- **React Router** for navigation
- **Axios** for HTTP client
- **React Hook Form** for forms

### Core Components Implemented

#### 1. **BeneficiaryManager**
- CRUD table for beneficiaries
- Search, filter, pagination
- Inline editing capabilities
- Bulk operations
- Excel import functionality

#### 2. **TemplateBuilder**
- Create/edit transfer templates
- Add/remove beneficiaries to templates
- Set default amounts and remittance info
- Template management (activate/deactivate)

#### 3. **TransferWorkflow**
- Template selector dropdown
- Load template → populate transfer list
- Editable transfer list (amounts, dates, remittance)
- Add/remove transfers dynamically
- Real-time validation
- Export file generation and preview (XML/CSV)

#### 4. **ExportGenerator**
- Export file preview with syntax highlighting (XML) or tabular format (CSV)
- Download generated export files (XML/CSV)
- Batch management
- Transfer history

#### 5. **Settings Management**
- Default bank account configuration
- Trusted partners management with full CRUD operations
- Tabbed interface for better organization

#### 6. **NAV Invoice Management**
- Payment status tracking and bulk updates
- Invoice list with filtering and search
- Payment status visualization

#### 7. **Bank Statement Import**
- Multi-bank statement upload (PDF/CSV/XML)
- Transaction matching visualization
- Match confidence indicators
- Manual matching capabilities

### UI/UX Features
- **Modern, clean design** with Hungarian bank/finance feel
- **Responsive** - works on desktop and tablet
- **Fast interactions** - optimistic updates with React Query
- **Clear visual hierarchy** - important actions stand out
- **Data-heavy tables** - good sorting, filtering, pagination
- **Form validation** - real-time feedback
- **Hungarian language** labels and text
- **Toast notifications** for user feedback
- **Loading states** and error handling
