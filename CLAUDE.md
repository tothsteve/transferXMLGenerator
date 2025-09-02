# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Django + React application for generating XML and CSV files for bank transfers with **multi-company architecture**, **feature flags**, and **role-based access control**. The system manages beneficiaries, transfer templates, NAV invoice synchronization, and generates SEPA-compatible XML files and KH Bank CSV files for bulk bank transfers.

### Backend (Django)
- **Django REST API** with `bank_transfers` app and **multi-company architecture**
- **SQL Server database** connection (port 1435, database: 'administration')  
- **Multi-tenant isolation** with company-scoped data and **feature flag system**
- **Role-based access control** with 4-level permissions (ADMIN, FINANCIAL, ACCOUNTANT, USER)
- **Key models**: Company, CompanyUser, FeatureTemplate, CompanyFeature, BankAccount, Beneficiary, TransferTemplate, Transfer, TransferBatch
- **NAV integration** with invoice synchronization and XML storage
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
- **Settings management** for default bank account configuration with full CRUD operations
- **React Query integration** for optimistic updates, caching, and error handling
- **Modern UI components** with form validation, loading states, and Hungarian localization

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
- **TRANSFER_AND_TEMPLATE_MANAGEMENT**: Full CRUD operations on transfers, templates, and PDF imports
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

### Frontend Permission System

The frontend implements comprehensive permission-based UI rendering using the `usePermissions` hook:

#### Permission Hook (`frontend/src/hooks/usePermissions.ts`)
```typescript
export const usePermissions = () => {
  const { state } = useAuth();
  const enabledFeatures = state.currentCompany?.enabled_features || [];
  const userRole = state.currentCompany?.user_role || 'USER';
  
  const hasFeature = (featureCode: string): boolean => {
    return enabledFeatures.includes(featureCode);
  };
  
  const hasPermission = (featureCode: string, action: 'view' | 'manage' = 'view'): boolean => {
    if (!hasFeature(featureCode)) return false;
    if (userRole === 'ADMIN') return true;
    
    if (action === 'manage') {
      switch (featureCode) {
        case 'TRANSFER_AND_TEMPLATE_MANAGEMENT':
          return ['ADMIN', 'FINANCIAL'].includes(userRole);
        case 'BENEFICIARY_MANAGEMENT':
          return ['ADMIN', 'FINANCIAL'].includes(userRole);
        case 'BATCH_MANAGEMENT':
          return userRole === 'ADMIN';
        // ... more role checks
      }
    }
    return true; // View access allowed if feature enabled
  };
  
  return {
    // Convenience methods for UI components
    canViewBeneficiaries: hasFeature('BENEFICIARY_VIEW') || hasFeature('BENEFICIARY_MANAGEMENT'),
    canManageBeneficiaries: hasPermission('BENEFICIARY_MANAGEMENT', 'manage'),
    canViewTransfers: hasFeature('TRANSFER_VIEW') || hasFeature('TRANSFER_AND_TEMPLATE_MANAGEMENT'),
    canManageTransfers: hasPermission('TRANSFER_AND_TEMPLATE_MANAGEMENT', 'manage'),
    canAccessPDFImport: hasPermission('TRANSFER_AND_TEMPLATE_MANAGEMENT', 'manage'),
    // ... more permission checks
  };
};
```

#### Menu-Level Security (Sidebar.tsx)
Navigation items are filtered based on user permissions:
```typescript
navigation.filter(item => {
  if (!item.requiredPermission) return true;
  return permissions[item.requiredPermission] === true;
})
```

#### Action Button Security (Implementation Pattern)
Components should conditionally render action buttons based on permissions:
```typescript
const permissions = usePermissions();

// Only show Add button if user can manage beneficiaries
{permissions.canManageBeneficiaries && (
  <Button startIcon={<AddIcon />}>Add Beneficiary</Button>
)}

// Show edit/delete actions only for management permissions
{permissions.canManageBeneficiaries ? (
  <IconButton onClick={handleEdit}><EditIcon /></IconButton>
) : null}
```

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

# IMPORTANT: Always activate virtual environment before running Python commands
source venv/bin/activate

# Database migrations
source venv/bin/activate && python manage.py makemigrations
source venv/bin/activate && python manage.py migrate

# Run development server on port 8002
source venv/bin/activate && python manage.py runserver 8002

# Create superuser
source venv/bin/activate && python manage.py createsuperuser

# Collect static files
source venv/bin/activate && python manage.py collectstatic
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

### Authentication & Permission System
All ViewSets use **two-layer permission checking**:

1. **CompanyContextPermission**: Ensures user belongs to company and company is active
2. **Feature-specific permissions**: Check both company feature enablement AND user role permissions

**Example Permission Classes**:
- `RequiresBeneficiaryManagement`: Needs `BENEFICIARY_MANAGEMENT` feature + appropriate role
- `RequiresTransferAndTemplateManagement`: Needs `TRANSFER_AND_TEMPLATE_MANAGEMENT` feature + appropriate role
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
- `POST /api/transfers/bulk_create/`: Bulk transfer creation - **Requires TRANSFER_AND_TEMPLATE_MANAGEMENT**
- `POST /api/transfers/generate_xml/`: XML file generation - **Requires EXPORT_XML_SEPA**
- `POST /api/transfers/generate_csv/`: CSV file generation - **Requires EXPORT_CSV_KH**
- `POST /api/templates/{id}/load_transfers/`: Generate transfers from template - **Requires TRANSFER_AND_TEMPLATE_MANAGEMENT**
- `POST /api/import/excel/`: Import beneficiaries from Excel files - **Requires TRANSFER_AND_TEMPLATE_MANAGEMENT**

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
