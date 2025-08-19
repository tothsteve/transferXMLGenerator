# Railway.app Deployment Guide

## Overview
This guide explains how to deploy the Transfer XML Generator application (Django + React) to Railway.app.

## Prerequisites
1. Railway account (railway.app)
2. GitHub repository connected to Railway
3. PostgreSQL database service on Railway

## Deployment Steps

### 1. Database Migration from SQL Server to PostgreSQL

**Important**: The current application uses SQL Server, but Railway uses PostgreSQL. You'll need to:

1. **Export existing data** from your SQL Server database
2. **Create a PostgreSQL service** in Railway
3. **Update your models** if needed for PostgreSQL compatibility
4. **Import your data** to the new PostgreSQL database

### 2. Environment Variables Setup

In your Railway project dashboard, set these environment variables:

```bash
# Required
SECRET_KEY=your-super-secret-key-here-min-50-chars
DATABASE_URL=postgresql://... (provided by Railway PostgreSQL service)
DJANGO_SETTINGS_MODULE=transferXMLGenerator.settings_production

# Optional
DEBUG=false
FRONTEND_URL=https://your-frontend-domain.railway.app
CORS_ALLOW_ALL=false
SECURE_SSL_REDIRECT=true
DJANGO_LOG_LEVEL=INFO
```

### 3. Deploy Backend (Django)

1. **Create a new Railway service** from your GitHub repository
2. **Set the root directory** to `backend` in Railway service settings
3. **Configure build command**:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput
   ```
4. **Configure start command**:
   ```bash
   python manage.py migrate && gunicorn transferXMLGenerator.wsgi:application --bind 0.0.0.0:$PORT
   ```

### 4. Deploy Frontend (React)

1. **Create another Railway service** for the frontend
2. **Set the root directory** to `frontend`
3. **Configure build command**:
   ```bash
   npm install && npm run build
   ```
4. **Configure start command**:
   ```bash
   npx serve -s build -l $PORT
   ```

### 5. Update Frontend API Configuration

Update your React app to use the Railway backend URL:

```typescript
// In frontend/src/services/api.ts
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-backend-domain.railway.app/api'
  : 'http://localhost:8000/api';
```

## Database Migration Script

Here's a sample script to help migrate from SQL Server to PostgreSQL:

```python
# migration_script.py
import os
import django
from django.core.management import execute_from_command_line

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings_production')
django.setup()

# Your migration logic here
# 1. Export data from SQL Server
# 2. Transform data for PostgreSQL
# 3. Import to PostgreSQL
```

## Updated Requirements

Add these to your `backend/requirements.txt`:

```
gunicorn==21.2.0
whitenoise==6.6.0
dj-database-url==2.1.0
psycopg2-binary==2.9.7
```

## Important Notes

1. **Database Change**: You must migrate from SQL Server to PostgreSQL
2. **Static Files**: Configured with WhiteNoise for production
3. **Security**: Production settings include HTTPS redirects and security headers
4. **CORS**: Configured for cross-origin requests between frontend and backend
5. **Environment Variables**: All sensitive data moved to environment variables

## Testing Deployment

1. **Check backend health**: `https://your-backend.railway.app/api/`
2. **Check frontend**: `https://your-frontend.railway.app`
3. **Test API connectivity**: Verify frontend can communicate with backend
4. **Test database**: Ensure data migration was successful

## Troubleshooting

- **500 errors**: Check Railway logs for Django errors
- **Database connection**: Verify DATABASE_URL environment variable
- **Static files**: Ensure collectstatic runs successfully during build
- **CORS issues**: Check CORS_ALLOWED_ORIGINS in production settings

## Production Checklist

- [ ] PostgreSQL database service created
- [ ] Data migrated from SQL Server
- [ ] Environment variables configured
- [ ] Backend service deployed and healthy
- [ ] Frontend service deployed and accessible
- [ ] API connectivity working
- [ ] Static files serving correctly
- [ ] HTTPS redirects working
- [ ] Admin panel accessible (if needed)