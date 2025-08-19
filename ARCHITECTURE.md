# Transfer Generator - System Architecture

## Overview

Transfer Generator is a multi-tenant Django + React application designed for Hungarian banking institutions to generate SEPA-compatible XML files for bank transfers. The system implements enterprise-grade multi-company architecture with complete data isolation and role-based access control.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Client  │    │  Django API     │    │  SQL Server     │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Auth Context │ │◄──►│ │JWT Auth     │ │    │ │Company Data │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Company      │ │◄──►│ │Company      │ │◄──►│ │User Data    │ │
│ │Context      │ │    │ │Middleware   │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ │Transfer     │ │
│ │Business     │ │◄──►│ │Business     │ │◄──►│ │Data         │ │
│ │Components   │ │    │ │Logic        │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    └─────────────────┘
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

```python
# Role-based permissions
- IsAuthenticated: All authenticated endpoints
- IsCompanyAdmin: User management, company settings
- IsCompanyMember: Company-scoped data access
- HasCompanyAccess: Validates company membership
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
│   └── useAuth.ts          # Authentication hooks
├── services/               # API service layer
│   └── api.ts              # API client
└── utils/                  # Utility functions
    └── tokenManager.ts     # JWT token management
```

### State Management

#### Authentication Context
```typescript
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