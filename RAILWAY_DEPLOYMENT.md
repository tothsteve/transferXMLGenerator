# Railway.app Deployment Guide

## Overview
This guide explains how to deploy the Transfer XML Generator application (Django + React) to Railway.app as **separate services**.

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

### 2. Deploy Backend Service (Django)

1. **Add Service** → "GitHub Repo" → Select your repository
2. **Configure backend service:**
   - **Root Directory**: `backend`
   - **Service Name**: `backend` or `api`
   - Railway will auto-detect Django using **Railpack** builder

### 3. Set Environment Variables (Backend)

In Railway backend service settings, add these variables:

```bash
# Required
SECRET_KEY=your-super-secret-key-min-50-chars-long
ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=transferXMLGenerator.settings_production
DATABASE_URL=[automatically provided by Railway PostgreSQL service]

# Optional
DEBUG=false
FRONTEND_URL=https://your-frontend-name.railway.app
CORS_ALLOW_ALL=false
SECURE_SSL_REDIRECT=true
DJANGO_LOG_LEVEL=INFO
```

### 4. Deploy Frontend Service (React)

1. **Add Service** → "GitHub Repo" → Select the **same repository**
2. **Configure frontend service:**
   - **Root Directory**: `frontend`
   - **Service Name**: `frontend` or `web`
   - Railway will auto-detect React automatically

### 5. Set Environment Variables (Frontend)

In Railway frontend service settings:

```bash
REACT_APP_BACKEND_URL=https://your-backend-name.railway.app
```

### 6. Connect Services and Update URLs

1. Both services should deploy automatically
2. Get the URLs from Railway dashboard
3. Update the frontend environment variable with the actual backend URL
4. Update backend CORS settings with the actual frontend URL

### 7. Import Your Data

Once backend is deployed and PostgreSQL is ready:

```bash
# Switch to production settings locally and run:
DJANGO_SETTINGS_MODULE=transferXMLGenerator.settings_production python migrate_to_postgresql.py --import-only
```


## Testing Deployment

- **Backend health**: `https://your-backend.railway.app/api/health/`
- **Frontend**: `https://your-frontend.railway.app`
- **API docs**: `https://your-backend.railway.app/swagger/`

## Optimized Monorepo Deployment

For optimal monorepo deployment with separate services, use watch paths to prevent unnecessary rebuilds:

### Backend Service Configuration
- Uses **root `railway.json`** with `"watchPaths": ["backend/**", "requirements.txt"]`
- Only rebuilds when backend code or requirements change

### Frontend Service Configuration
- Uses **`frontend/railway.json`** with `"watchPaths": ["frontend/**"]`
- Only rebuilds when frontend code changes

This ensures each service rebuilds independently based on actual code changes.

## Important Notes

1. **Separate Services**: Backend and frontend are deployed as completely separate Railway services
2. **Optimized Rebuilds**: Each service has its own `railway.json` with specific watch paths for monorepo efficiency
3. **Database**: PostgreSQL is shared between services via environment variables
4. **Static Files**: Backend serves its own static files, frontend is served by npm serve
5. **CORS**: Make sure to update CORS settings with actual deployment URLs

## Troubleshooting

- **Build failures**: Check Railway service configuration in the dashboard
- **Environment variables**: Ensure all required variables are set for each service
- **CORS issues**: Update `FRONTEND_URL` in backend settings
- **Database connection**: Verify `DATABASE_URL` is correctly provided by PostgreSQL service

## Production Checklist

- [ ] PostgreSQL database service created
- [ ] Data exported from SQL Server (`python migrate_to_postgresql.py --export-only`)
- [ ] Backend service deployed with correct environment variables
- [ ] Frontend service deployed with backend URL
- [ ] Frontend service configured with `frontend/railway.json` for optimized rebuilds
- [ ] Services can communicate (test API calls)
- [ ] Data imported to PostgreSQL (`python migrate_to_postgresql.py --import-only`)
- [ ] CORS settings updated with actual URLs
- [ ] SSL/HTTPS working correctly