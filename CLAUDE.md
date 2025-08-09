# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Django + React application for generating XML files for bank transfers. The system manages beneficiaries, transfer templates, and generates SEPA-compatible XML files for bulk bank transfers.

### Backend (Django)
- **Django REST API** with `bank_transfers` app
- **SQL Server database** connection (port 1435, database: 'administration')  
- **Key models**: BankAccount, Beneficiary, TransferTemplate, Transfer, TransferBatch
- **XML generation** via `utils.generate_xml()` - creates HUF transaction XML files
- **Excel import** functionality for bulk beneficiary creation
- **Template system** for recurring transfer patterns (e.g., monthly payroll)
- **Swagger API docs** available via drf_yasg

### Frontend (React + TypeScript)
- **Create React App** with TypeScript
- Currently contains only default React starter template
- API integration not yet implemented

## Development Commands

### Backend
```bash
cd backend

# Install dependencies (first time)
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run development server
python manage.py runserver

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

# Run development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Database Configuration

The backend connects to SQL Server:
- Host: localhost:1435
- Database: administration
- Uses `python-decouple` for environment variables
- Set `DB_PASSWORD` and `SECRET_KEY` in environment or `.env` file

## API Architecture

### Core ViewSets
- `BankAccountViewSet`: Manages originator accounts with default account functionality
- `BeneficiaryViewSet`: Handles beneficiary CRUD with filtering (frequent, active, search)
- `TransferTemplateViewSet`: Template management with beneficiary associations
- `TransferViewSet`: Individual transfers with bulk creation and XML generation
- `TransferBatchViewSet`: Read-only batches created during XML generation

### Key API Endpoints
- `POST /api/transfers/bulk_create/`: Bulk transfer creation
- `POST /api/transfers/generate_xml/`: XML file generation from transfer IDs
- `POST /api/templates/{id}/load_transfers/`: Generate transfers from template
- `POST /api/import/excel/`: Import beneficiaries from Excel files

## XML Generation

The `utils.generate_xml()` function creates XML files with this structure:
- Root element: `<HUFTransactions>`
- Each transfer becomes a `<Transaction>` with Originator, Beneficiary, Amount, RequestedExecutionDate, and RemittanceInfo
- Supports HUF, EUR, USD currencies
- Marks transfers as `is_processed=True` after XML generation

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
I have a **Django REST API backend** (100% complete) for a bank transfer XML generator system, and now need to build the **React TypeScript frontend**. The backend is running on `http://localhost:8000` with full Swagger documentation at `/swagger/`.

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

### Base URL: `http://localhost:8000/api/`

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
- XML generation and preview

#### 4. **XMLGenerator** (Priority 4)
- XML preview with syntax highlighting
- Download generated XML
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
4. **Real-time XML preview** - see XML as you build transfers
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

The backend `/api/transfers/generate_xml/` endpoint returns this XML format, and the frontend should display it with syntax highlighting for preview before download.

**Swagger documentation available at: http://localhost:8000/swagger/**
