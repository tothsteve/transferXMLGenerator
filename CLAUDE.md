# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Django + React application for generating XML and CSV files for bank transfers with **multi-company architecture**, **feature flags**, and **role-based access control**. The system manages beneficiaries, transfer templates, NAV invoice synchronization, and generates SEPA-compatible XML files and KH Bank CSV files for bulk bank transfers.

### Backend (Django)
- **Django REST API** with `bank_transfers` app and **multi-company architecture**
- **SQL Server database** connection (port 1435, database: 'administration')
- **Multi-tenant isolation** with company-scoped data and **feature flag system**
- **Role-based access control** with 4-level permissions (ADMIN, FINANCIAL, ACCOUNTANT, USER)
- **Key models**: Company, CompanyUser, FeatureTemplate, CompanyFeature, BankAccount, Beneficiary, TransferTemplate, Transfer, TransferBatch, TrustedPartner, ExchangeRate, BankStatement, BankTransaction
- **NAV integration** with invoice synchronization, XML storage, payment status tracking, and trusted partners auto-payment
- **MNB Exchange Rate integration** with daily sync of USD/EUR rates from Magyar Nemzeti Bank official API
- **Bank Statement Import** with multi-bank support (GRÁNIT, Revolut, MagNet, K&H) and sophisticated transaction matching
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
- **Bank statement import** with transaction matching visualization

## 📚 Documentation Files

For detailed information, refer to these documentation files:

### Development Guidelines

#### Backend: CLAUDE-PYTHON-BASIC.md
**Location**: `/backend/CLAUDE-PYTHON-BASIC.md`

Python and Django development best practices:
- Core Development Philosophy (KISS, YAGNI, Design Principles)
- Django Project Structure and Architecture
- Django Models with Validation Examples
- Django REST Framework (ViewSets, Serializers, Permissions)
- Database Migrations (Creating, Applying, Data Migrations)
- Testing Strategy (Unit Tests, API Tests)
- Common Patterns (Service Layer, Repository, Signals)
- Debugging Tools and Techniques
- Management Commands

#### Frontend: CLAUDE-REACT.md
**Location**: `/frontend/CLAUDE-REACT.md`

React 19 and TypeScript development guidelines:
- React 19 Key Features (Compiler, Actions API, use() API)
- Project Structure (Vertical Slice Architecture)
- Strict TypeScript Configuration Requirements
- Data Validation with Zod (MANDATORY for external data)
- Testing Strategy with Vitest (80% coverage requirement)
- Component Guidelines with JSDoc Documentation
- State Management Hierarchy (useState, Context, TanStack Query, Zustand)
- Security Requirements (Input Validation, XSS Prevention)
- Performance Guidelines and Bundle Optimization

#### Security: SECURITY.md
**Location**: `/frontend/SECURITY.md`

Security audit and production deployment checklist:
- NPM Vulnerability Status (21 vulnerabilities in dev dependencies only)
- XSS Prevention Audit (ZERO dangerouslySetInnerHTML usage)
- File Upload Security (Type validation, size limits, MIME verification)
- Code Quality Security (Console logging audit)
- Production Deployment Checklist (Critical and recommended items)
- Regular Maintenance Schedule (Weekly, Monthly, Quarterly)

### Feature Documentation

#### FEATURES.md
**Location**: `/FEATURES.md`

Contains detailed implementation information for all major features:
- Multi-Company Feature Flag System (16 features, 4 role levels)
- NAV Invoice Payment Status Tracking (3 statuses with automated updates)
- Trusted Partners Auto-Payment System (flexible tax number matching)
- MNB Exchange Rate Integration (USD/EUR with 33 currencies available)
- Bank Statement Import and Transaction Matching (7 matching strategies, 5 confidence levels)
- Base Tables Import System (manual CSV import for suppliers, customers, product prices)

#### API_GUIDE.md
**Location**: `/API_GUIDE.md`

Complete API endpoint documentation and testing guidelines:
- API Architecture and ViewSets
- Authentication & Company Management
- Core Business Operations (Beneficiaries, Templates, Transfers, Trusted Partners, Exchange Rates, Bank Statements)
- Export Generation (XML/CSV formats)
- API Testing with curl (token extraction and usage patterns)
- Frontend Development Guide (tech stack, components, workflow)

### Database Documentation

#### DATABASE_DOCUMENTATION.md
**Location**: `/DATABASE_DOCUMENTATION.md`

Single source of truth for all database schema documentation:
- Multi-company architecture tables
- Feature flag system tables
- Role-based access control implementation
- NAV integration tables
- Bank statement import tables
- Complete table and column descriptions
- Performance indexes and constraints
- Troubleshooting guide for permissions

#### BANK_STATEMENT_IMPORT_DOCUMENTATION.md
**Location**: `/BANK_STATEMENT_IMPORT_DOCUMENTATION.md`

Comprehensive bank statement import documentation (1200+ lines):
- Field mapping for all 4 supported banks (GRÁNIT, Revolut, MagNet, K&H)
- Transaction type mapping for each bank
- Special cases and workarounds
- Test results and validation data

## ⚠️ CRITICAL: Database Documentation Requirement

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

## Git Commit Guidelines

**IMPORTANT: DO NOT include Claude Code attribution in commit messages**
- Never add "🤖 Generated with [Claude Code](https://claude.com/claude-code)" to commits
- Never add "Co-Authored-By: Claude <noreply@anthropic.com>" to commits
- Keep commit messages clean and professional without AI tool attribution

## Development Commands

### Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run development server on port 8002
python manage.py runserver 8002

# Create superuser
python manage.py createsuperuser

# Import base tables (Suppliers, Customers, Product Prices)
# See FEATURES.md for detailed documentation
python manage.py import_base_tables --company-id=<ID> --csv-type=suppliers --csv-path=<PATH>
python manage.py import_base_tables --company-id=<ID> --csv-type=customers --csv-path=<PATH>
python manage.py import_base_tables --company-id=<ID> --csv-type=prices --csv-path=<PATH>

# ⚠️ IMPORTANT: Running Tests
# ALWAYS activate the virtual environment first from the backend directory
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest bank_transfers/tests/test_transaction_matching_service.py -v

# Run tests with coverage report
pytest --cov=bank_transfers --cov-report=term --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development server (bypasses CRACO/ESLint issues)
npx react-scripts start

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

## Quick Reference

### Key API Endpoints
- **Base URL**: `http://localhost:8002/api/`
- **Swagger Docs**: `http://localhost:8002/swagger/`

#### Authentication
- `POST /api/auth/register/` - User and company registration
- `POST /api/auth/login/` - Login with JWT token + company context + enabled features
- `POST /api/auth/switch_company/` - Change active company context
- `GET /api/auth/profile/` - Get user profile and company memberships
- `GET /api/auth/features/` - Get enabled features for current company

#### Core Operations
- `GET /api/beneficiaries/` - List beneficiaries with filtering
- `GET /api/templates/` - List transfer templates
- `POST /api/templates/{id}/load_transfers/` - Load template to generate transfers
- `POST /api/transfers/bulk_create/` - Bulk create transfers
- `POST /api/transfers/generate_xml/` - Generate SEPA XML export
- `POST /api/transfers/generate_csv/` - Generate KH Bank CSV export

#### Trusted Partners
- `GET /api/trusted-partners/` - List trusted partners
- `POST /api/trusted-partners/` - Create new trusted partner
- `GET /api/trusted-partners/available_partners/` - Get available suppliers from NAV invoices

#### Exchange Rates
- `GET /api/exchange-rates/current/` - Today's USD/EUR rates
- `POST /api/exchange-rates/convert/` - Currency conversion to HUF
- `POST /api/exchange-rates/sync_current/` - Manual sync trigger (ADMIN only)

#### Bank Statements
- `POST /api/bank-statements/upload/` - Upload and parse bank statement
- `GET /api/bank-statements/` - List all statements with filtering
- `GET /api/bank-transactions/` - List transactions with filtering
- `POST /api/bank-transactions/{id}/match_invoice/` - Manual invoice matching

### Excel Import Format

Expected Excel structure (starting row 3):
- Column A: Comment (optional)
- Column B: Beneficiary name (required)
- Column C: Account number (required)
- Column D: Amount (optional)
- Column E: Execution date (optional)
- Column F: Remittance info (optional)

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

**Notes**:
- Clean account numbers (no dashes/spaces)
- ISO date format (YYYY-MM-DD)
- UTF-8 encoding for Hungarian characters
- Decimal with 2 places for amounts

## Template System

TransferTemplate allows for recurring transfer patterns:
- Templates contain multiple TemplateBeneficiary records
- Each template beneficiary has default amount and remittance info
- Templates can be loaded to pre-populate transfers for execution
- Useful for monthly payroll or recurring vendor payments

## Export Limitations

### XML Export
- Supports HUF, EUR, USD currencies
- Unlimited transfers per batch
- Marks transfers as `is_processed=True` after generation

### CSV Export (KH Bank)
- Hungarian "Egyszerűsített forintátutalás" format (.HUF.csv)
- **Maximum 40 transfers** per batch (KH Bank limitation)
- **HUF currency only**
- Marks transfers as `is_processed=True` after generation
