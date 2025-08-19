# Local Development Setup

This guide explains how to set up the Transfer XML Generator application for local development while keeping the Railway production configuration intact.

## Prerequisites

1. **SQL Server** running on `localhost:1435` (for local development)
2. **Python 3.8+** and **Node.js 16+**
3. **Git** repository cloned locally

## Local Development Setup

### 1. Backend Setup (Django)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install local development dependencies
pip install -r requirements-local.txt

# Copy local environment variables
cp ../.env.local .env

# Run database migrations
python manage.py migrate --settings=transferXMLGenerator.settings_local

# Create superuser (optional)
python manage.py createsuperuser --settings=transferXMLGenerator.settings_local

# Run development server
python manage.py runserver --settings=transferXMLGenerator.settings_local
```

### 2. Frontend Setup (React)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

## Environment Configuration

### Local Development
- **Django settings**: `transferXMLGenerator.settings_local`
- **Database**: SQL Server (localhost:1435)
- **Environment file**: `.env.local`
- **Requirements**: `requirements-local.txt`

### Production (Railway)
- **Django settings**: `transferXMLGenerator.settings_production`
- **Database**: PostgreSQL (Railway)
- **Environment**: Railway dashboard
- **Requirements**: `requirements.txt`

## Key Differences

| Feature | Local Development | Production (Railway) |
|---------|------------------|---------------------|
| Database | SQL Server | PostgreSQL |
| Settings Module | `settings_local` | `settings_production` |
| Debug Mode | `True` | `False` |
| CORS | Permissive | Restricted |
| Static Files | Django dev server | WhiteNoise |
| Requirements | `requirements-local.txt` | `requirements.txt` |

## Running Local Development

### Start Backend (Terminal 1)
```bash
cd backend
source venv/bin/activate
python manage.py runserver --settings=transferXMLGenerator.settings_local
```

### Start Frontend (Terminal 2)
```bash
cd frontend
npm start
```

### Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Swagger Docs**: http://localhost:8000/swagger/
- **Admin Panel**: http://localhost:8000/admin/

## Database Management

### Local SQL Server
Your existing SQL Server database on `localhost:1435` remains unchanged. Use this for local development.

### Production PostgreSQL
When deploying to Railway, use the migration script:
```bash
# Export from local SQL Server
python migrate_to_postgresql.py --export-only

# Import to Railway PostgreSQL (after deployment)
python migrate_to_postgresql.py --import-only
```

## Development Workflow

1. **Local Development**: Work with SQL Server using `settings_local`
2. **Testing**: Ensure features work locally
3. **Production Deploy**: Push to Railway (automatically uses `settings_production`)
4. **Data Sync**: Use migration script when needed

## Switching Between Environments

### Force Local Settings
```bash
export DJANGO_SETTINGS_MODULE=transferXMLGenerator.settings_local
python manage.py runserver
```

### Force Production Settings (for testing)
```bash
export DJANGO_SETTINGS_MODULE=transferXMLGenerator.settings_production
python manage.py check --deploy
```

## Troubleshooting

### SQL Server Connection Issues
1. Verify SQL Server is running on port 1435
2. Check database name is 'administration'
3. Update password in `.env` file if needed

### CORS Issues
Local development uses permissive CORS settings in `settings_local.py`

### Import Errors
Make sure you're using the correct requirements file:
- Local: `requirements-local.txt`
- Production: `requirements.txt`

## File Structure

```
transferXMLGenerator/
├── backend/
│   ├── transferXMLGenerator/
│   │   ├── settings.py          # Base settings (original)
│   │   ├── settings_local.py    # Local development
│   │   └── settings_production.py # Railway production
│   ├── requirements.txt         # Production dependencies
│   ├── requirements-local.txt   # Local dependencies
│   └── Procfile                 # Railway process file
├── frontend/
│   ├── .env.production         # Production environment
│   └── Procfile                # Railway process file
├── .env.local                  # Local environment template
├── .env.example               # Production environment template
└── migrate_to_postgresql.py   # Database migration script
```

This setup allows you to develop locally with SQL Server while having a production-ready Railway deployment with PostgreSQL.