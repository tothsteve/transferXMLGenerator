# Transfer Generator - System Architecture

## Overview

Transfer Generator is a multi-tenant Django + React application designed for Hungarian banking institutions to generate SEPA-compatible XML files for bank transfers. The system implements enterprise-grade multi-company architecture with complete data isolation and role-based access control.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Client  │    │  Django API     │    │  PostgreSQL     │    │ NAV Online API  │
│                 │    │                 │    │   (Railway)     │    │   (Hungary)     │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Auth Context │ │◄──►│ │JWT Auth     │ │    │ │Company Data │ │    │ │Invoice API  │ │
│ │+ Features   │ │    │ │+ Features   │ │    │ │+ Permissions│ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ │Tax Authority│ │
│ │Permission   │ │◄──►│ │Permission   │ │◄──►│ │User Roles   │ │    │ │Integration  │ │
│ │System       │ │    │ │Middleware   │ │    │ └─────────────┘ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │ ┌─────────────┐ │    └─────────────────┘
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ │Transfer     │ │             ▲
│ │Business     │ │◄──►│ │Business     │ │◄──►│ │Data         │ │             │
│ │Components   │ │    │ │Logic        │ │    │ └─────────────┘ │             │
│ └─────────────┘ │    │ └─────────────┘ │    │ ┌─────────────┐ │             │
│                 │    │ ┌─────────────┐ │    │ │NAV Invoice  │ │             │
│                 │    │ │NAV Scheduler│ │◄───┤ │Data         │ │─────────────┘
│                 │    │ │(APScheduler)│ │    │ └─────────────┘ │
│                 │    │ └─────────────┘ │    └─────────────────┘
└─────────────────┘    └─────────────────┘
```

## Backend Architecture (Django)

### Application Structure

```
backend/
├── transferXMLGenerator/     # Django project settings
│   ├── settings.py          # Configuration
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI application
├── bank_transfers/          # Main Django app
│   ├── models.py            # Data models
│   ├── api_views.py         # REST API views
│   ├── authentication.py   # JWT authentication
│   ├── middleware.py        # Company context middleware
│   ├── permissions.py       # Role-based permissions
│   ├── serializers.py       # API serializers
│   └── utils.py             # Business logic utilities
└── requirements.txt         # Python dependencies
```

### Data Models

#### Core Authentication Models
```python
# Company-based multi-tenancy
Company(name, tax_id, address, phone, email, is_active)
CompanyUser(user, company, role, is_active, joined_at)
UserProfile(user, phone, preferred_language, timezone, last_active_company)
```

#### Business Models
```python
# All business models include company FK for isolation
BankAccount(company, account_number, bank_name, is_default)
Beneficiary(company, name, account_number, bank_name, is_frequent, is_active)
TransferTemplate(company, name, is_active)
TemplateBeneficiary(template, beneficiary, default_amount, default_remittance_info)
Transfer(company, beneficiary, amount, currency, execution_date, remittance_info)
TransferBatch(company, created_at, xml_content, file_name)
```

### Authentication Flow

```
1. User Login/Register
   ├── JWT Token Generation
   ├── Company Association Check
   └── User Profile Creation

2. Request Processing
   ├── JWT Token Validation
   ├── Company Context Middleware
   ├── Permission Checking
   └── Company-Scoped Queries

3. Company Switching
   ├── Validate User-Company Membership
   ├── Update Active Company Context
   └── Refresh Company-Scoped Data
```

### API Architecture

#### Authentication Endpoints
- `POST /api/auth/login/` - User authentication
- `POST /api/auth/register/` - User registration with company creation
- `POST /api/auth/refresh/` - JWT token refresh
- `POST /api/auth/switch_company/` - Company context switching

#### Business Endpoints
- `GET /api/beneficiaries/` - Company-scoped beneficiary list
- `POST /api/transfers/bulk_create/` - Bulk transfer creation
- `POST /api/transfers/generate_xml/` - XML file generation
- `GET /api/company/users/` - Company user management (admin only)

### Middleware Stack

```python
# Request Processing Order
1. SecurityMiddleware
2. SessionMiddleware  
3. CommonMiddleware
4. CsrfViewMiddleware
5. AuthenticationMiddleware
6. CompanyContextMiddleware  # Custom - adds company context
7. MessageMiddleware
```

### Permission System

#### Two-Layer Architecture
The system implements **feature-based permissions** combined with **role-based access control**:

```python
# Layer 1: Company Feature Enablement
- FeatureTemplate: Master catalog of available features (15 features)
- CompanyFeature: Which features are enabled per company
- Categories: EXPORT, SYNC, TRACKING, REPORTING, INTEGRATION, GENERAL

# Layer 2: Role-Based Access Control  
- ADMIN: Full access to all enabled company features
- FINANCIAL: Transfer operations, beneficiary management, exports
- ACCOUNTANT: Invoice/expense management (NAV integration)
- USER: Read-only access to basic features
```

#### Permission Classes
```python
# Feature-Based Permissions (New)
- RequireTransferAndTemplateManagement: Transfers, templates, PDF imports
- RequireBeneficiaryManagement: Full beneficiary CRUD operations
- RequireBatchManagement: Transfer batch operations (admin only)
- RequireNavSync: NAV invoice synchronization
- RequireExportFeatures: XML/CSV export generation

# Legacy Permissions (Still Used)
- IsAuthenticated: All authenticated endpoints
- IsCompanyAdmin: User management, force logout
- IsCompanyMember: Company-scoped data access validation
```

#### Current Active Features
```python
# Auto-enabled for new companies (7 features)
EXPORT_XML_SEPA             # SEPA XML generation
EXPORT_CSV_KH               # KH Bank CSV export
BENEFICIARY_MANAGEMENT      # Full beneficiary CRUD
BENEFICIARY_VIEW           # Read-only beneficiary access
TRANSFER_AND_TEMPLATE_MANAGEMENT  # Transfers + templates + PDF import
TRANSFER_VIEW              # Read-only transfer access
BATCH_MANAGEMENT           # Transfer batch operations
BATCH_VIEW                 # Read-only batch access

# Manual activation required (8 features)
NAV_SYNC                   # Requires NAV API credentials
EXPORT_CSV_CUSTOM          # Custom CSV formats
EXPENSE_TRACKING           # Business expense management (planned)
INVOICE_MANAGEMENT         # Manual invoice entries (planned)
BANK_STATEMENT_IMPORT      # Bank reconciliation (planned)
MULTI_CURRENCY             # USD/EUR support (planned)
REPORTING                  # Advanced reports (planned)
API_ACCESS                 # External API access (planned)
WEBHOOK_NOTIFICATIONS      # Webhook system (planned)
BULK_OPERATIONS           # Bulk import/export (planned)
```

## Frontend Architecture (React + TypeScript)

### Component Structure

```
src/
├── components/
│   ├── Auth/                # Authentication components
│   │   ├── AuthPage.tsx     # Login/Register container
│   │   ├── LoginForm.tsx    # Login form
│   │   ├── SimpleRegisterForm.tsx # Registration form
│   │   └── ProtectedRoute.tsx # Route protection
│   ├── Layout/              # Application layout
│   │   ├── Layout.tsx       # Main layout container
│   │   ├── Header.tsx       # Top navigation
│   │   └── Sidebar.tsx      # Side navigation
│   ├── UserManagement/      # User/company management
│   │   └── UserManagement.tsx # Admin user interface
│   └── [Business]/          # Core business components
├── contexts/                # React contexts
│   └── AuthContext.tsx      # Authentication state
├── hooks/                   # Custom React hooks
│   ├── useAuth.ts          # Authentication hooks
│   └── usePermissions.ts   # Feature-based permission checks
├── services/               # API service layer
│   └── api.ts              # API client
└── utils/                  # Utility functions
    └── tokenManager.ts     # JWT token management
```

### State Management

#### Authentication Context (Updated)
```typescript
interface Company {
  id: number;
  name: string;
  tax_id: string;
  user_role: 'ADMIN' | 'FINANCIAL' | 'ACCOUNTANT' | 'USER';
  enabled_features: string[];  // New: Features enabled for this company
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  companies: Company[];
  currentCompany: Company | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
}
```

#### Frontend Permission System (New)
```typescript
// usePermissions Hook - Two-layer permission checking
const usePermissions = () => {
  const enabledFeatures = currentCompany?.enabled_features || [];
  const userRole = currentCompany?.user_role || 'USER';
  
  return {
    // Feature checks
    hasFeature: (code: string) => enabledFeatures.includes(code),
    
    // Permission checks (feature + role)
    canViewBeneficiaries: hasFeature('BENEFICIARY_VIEW') || hasFeature('BENEFICIARY_MANAGEMENT'),
    canManageBeneficiaries: hasPermission('BENEFICIARY_MANAGEMENT', 'manage'),
    canViewTransfers: hasFeature('TRANSFER_VIEW') || hasFeature('TRANSFER_AND_TEMPLATE_MANAGEMENT'),
    canManageTransfers: hasPermission('TRANSFER_AND_TEMPLATE_MANAGEMENT', 'manage'),
    canAccessPDFImport: hasPermission('TRANSFER_AND_TEMPLATE_MANAGEMENT', 'manage'),
    
    // User context
    userRole,
    enabledFeatures,
    isAdmin: userRole === 'ADMIN'
  };
};

// Usage in components
const permissions = usePermissions();

// Menu visibility (Sidebar.tsx)
navigation.filter(item => {
  if (!item.requiredPermission) return true;
  return permissions[item.requiredPermission] === true;
});

// Action button visibility (Planned)
{permissions.canManageBeneficiaries && (
  <Button startIcon={<AddIcon />}>Új kedvezményezett</Button>
)}
```

#### Component Flow
```
App.tsx
├── AuthProvider (Context)
│   ├── ProtectedRoute (Auth Guard)
│   │   └── Layout (Main Container)
│   │       ├── Header (Navigation + User Menu)
│   │       ├── Sidebar (Company Navigation)
│   │       └── Routes (Business Components)
│   └── AuthPage (Login/Register)
```

### Authentication Flow

```typescript
// Login Process
1. User submits credentials
2. API call to /api/auth/login/
3. Store JWT tokens in localStorage
4. Update AuthContext state
5. Redirect to dashboard

// Token Management
1. Axios interceptors add Authorization header
2. Automatic token refresh on 401 responses
3. Company context header (X-Company-ID)
4. Logout on refresh failure
```

## Database Architecture

### Multi-Tenancy Strategy

**Shared Database, Shared Schema with Tenant Isolation**
- All tables include `company_id` foreign key
- Application-level filtering ensures data isolation
- Company context middleware automatically filters queries
- Database constraints prevent cross-company data access

### Key Design Patterns

#### 1. Company Scoping
```sql
-- All business queries automatically filtered
SELECT * FROM beneficiaries WHERE company_id = :current_company_id;
```

#### 2. Role-Based Access
```python
# Django ORM with company filtering
def get_queryset(self):
    return self.model.objects.filter(company=self.request.company)
```

#### 3. Data Migration Strategy
```python
# Existing data assigned to default company
def migrate_existing_data():
    default_company = Company.objects.get_or_create(
        name="Default Company",
        tax_id="00000000-0-00"
    )
    # Migrate all existing records
```

## Security Architecture

### Authentication Security
- **JWT Tokens**: Stateless authentication with reasonable expiration
- **Token Refresh**: Automatic refresh prevents session interruption
- **Role Validation**: Server-side permission checking
- **Company Validation**: User-company membership verification

### Data Security
- **Input Validation**: All inputs validated and sanitized
- **SQL Injection Prevention**: Django ORM and parameterized queries
- **XSS Protection**: React automatic escaping and CSP headers
- **Company Isolation**: Application-level data filtering

### API Security
```python
# Example security implementation
@permission_classes([IsAuthenticated, IsCompanyMember])
def api_endpoint(request):
    # Company context automatically applied
    queryset = Model.objects.filter(company=request.company)
    return Response(serializer.data)
```

## Performance Considerations

### Database Optimization
- **Indexes**: Company foreign keys indexed for fast filtering
- **Query Optimization**: Company context reduces query scope
- **Connection Pooling**: Efficient database connection management

### Frontend Optimization
- **React Query**: Efficient data caching and synchronization
- **Code Splitting**: Lazy loading of non-critical components
- **Bundle Optimization**: Tree shaking and minification

### API Optimization
- **Pagination**: Large datasets paginated by default
- **Field Selection**: Sparse fieldsets to reduce payload size
- **Compression**: GZIP compression for API responses

## Deployment Architecture

### Development Environment
```
localhost:3000 (React Dev Server)
     ↓
localhost:8000 (Django Dev Server)
     ↓
localhost:1435 (SQL Server)
```

### Production Environment
```
Load Balancer
     ↓
Web Server (Nginx)
     ↓
WSGI Server (Gunicorn)
     ↓
Django Application
     ↓
Database Server (SQL Server)
```

### Monitoring & Logging
- **Application Logs**: Structured logging with company context
- **Performance Monitoring**: Request timing and database query analysis
- **Error Tracking**: Centralized error reporting
- **Security Auditing**: Authentication and permission logs

## Scalability Considerations

### Horizontal Scaling
- **Stateless Design**: JWT tokens enable horizontal scaling
- **Database Sharding**: Company-based sharding strategy ready
- **Load Balancing**: Sticky sessions not required

### Vertical Scaling
- **Database Optimization**: Query optimization and indexing
- **Caching Strategy**: Redis for session and query caching
- **Resource Monitoring**: CPU, memory, and I/O monitoring

---

**Document Version**: 1.0  
**Last Updated**: 2025-08-17  
**Architecture Review**: Quarterly