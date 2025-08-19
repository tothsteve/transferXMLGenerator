# Transfer Generator - Multi-Company Banking Solution

A comprehensive Django + React application for generating SEPA-compatible XML files for Hungarian bank transfers with full multi-company support and enterprise-grade authentication.

## 🏢 Multi-Company Architecture

This system supports multiple companies with complete data isolation, role-based access control, and enterprise-grade security features.

### Key Features

- **🔐 JWT Authentication** - Secure login with automatic token refresh
- **🏢 Multi-Tenant Architecture** - Complete company data isolation
- **👥 User Management** - Role-based access (Admin/User) with invitation system
- **🔄 Company Switching** - Users can belong to multiple companies
- **📊 Bank Transfer Management** - Full SEPA XML generation workflow
- **🇭🇺 Hungarian Localization** - Complete Hungarian language support

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- SQL Server (localhost:1435)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/swagger/

## 📋 Product Requirements (PRPs)

- [PRP-001: Multi-Company Authentication System](./PRP-001-Multi-Company-Authentication.md)

## 🏗️ Architecture Overview

### Backend (Django)
```
backend/
├── bank_transfers/           # Main application
│   ├── models.py            # Company-scoped data models
│   ├── api_views.py         # REST API endpoints
│   ├── authentication.py   # JWT auth system
│   ├── middleware.py        # Company context middleware
│   └── permissions.py       # Role-based permissions
├── transferXMLGenerator/    # Django project settings
└── requirements.txt         # Python dependencies
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/
│   │   ├── Auth/           # Authentication components
│   │   ├── Layout/         # App layout and navigation
│   │   ├── UserManagement/ # User/company management
│   │   └── [Business]/     # Core business features
│   ├── contexts/           # React contexts (Auth, etc.)
│   ├── hooks/              # Custom React hooks
│   └── services/           # API service layer
└── package.json            # Node dependencies
```

## 🔑 Authentication Flow

### User Registration
1. User creates account with company information
2. User becomes company admin automatically
3. Company data space created and isolated
4. Automatic login after registration

### User Management
1. Company admins can invite users via email
2. Role assignment (Admin/User)
3. Multi-company membership support
4. Company switching interface

### Security Features
- JWT tokens with automatic refresh
- Company context middleware
- Role-based API permissions
- Protected React routes

## 📊 Database Schema

### Core Models
- **Company** - Company information and settings
- **CompanyUser** - User-company relationships with roles
- **UserProfile** - Extended user information
- **BankAccount** - Company-scoped bank accounts
- **Beneficiary** - Company-scoped beneficiaries
- **TransferTemplate** - Company-scoped transfer templates
- **Transfer** - Individual transfers
- **TransferBatch** - XML generation batches

### Data Isolation
All business data models include `company` foreign key ensuring complete data separation between companies.

## 🔧 API Endpoints

### Authentication
```
POST /api/auth/login/          # User login
POST /api/auth/register/       # User registration
POST /api/auth/refresh/        # Token refresh
POST /api/auth/logout/         # User logout
POST /api/auth/switch_company/ # Company switching
```

### Business Operations
```
GET  /api/beneficiaries/       # List company beneficiaries
POST /api/beneficiaries/       # Create beneficiary
GET  /api/templates/           # List company templates
POST /api/transfers/bulk_create/ # Bulk transfer creation
POST /api/transfers/generate_xml/ # XML generation
```

### User Management (Admin Only)
```
GET  /api/company/users/       # List company users
POST /api/company/invite/      # Invite new user
PUT  /api/company/users/{id}/  # Update user role
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
python manage.py test
```

### Frontend Testing
```bash
cd frontend
npm test
```

### Manual Testing Checklist
- [ ] User registration and login
- [ ] Company data isolation
- [ ] Role-based permissions
- [ ] Multi-company switching
- [ ] XML generation workflow

## 🚀 Deployment

### Production Environment Variables
```bash
# Backend (.env)
SECRET_KEY=your-secret-key
DB_PASSWORD=your-db-password
ALLOWED_HOSTS=your-domain.com
DEBUG=False

# Frontend
REACT_APP_API_BASE_URL=https://api.your-domain.com
```

### Docker Deployment
```bash
# Backend
docker build -t transfer-generator-backend ./backend
docker run -p 8000:8000 transfer-generator-backend

# Frontend
docker build -t transfer-generator-frontend ./frontend
docker run -p 3000:3000 transfer-generator-frontend
```

## 📈 Performance Considerations

- **Database Indexing** - Company foreign keys indexed for fast filtering
- **API Optimization** - Company context middleware reduces query overhead
- **Frontend Caching** - React Query for efficient data caching
- **Token Management** - Automatic refresh prevents authentication interruptions

## 🔒 Security

### Authentication Security
- JWT tokens with reasonable expiration times
- Automatic token refresh mechanism
- Secure token storage in localStorage
- CSRF protection on all forms

### Data Security
- Company-based data isolation
- Role-based access control
- Input validation and sanitization
- SQL injection prevention

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is proprietary software developed by ITCardigan for Hungarian banking solutions.

## 📞 Support

For technical support or questions:
- **Email**: support@itcardigan.com
- **Documentation**: See `/docs` folder
- **Issues**: Use GitHub issue tracker

---

**Version**: 2.0.0 (Multi-Company)  
**Last Updated**: 2025-08-17  
**Developed by**: ITCardigan Development Team