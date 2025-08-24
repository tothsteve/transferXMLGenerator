# Railway Production Deployment Guide

This guide covers deploying the Transfer XML Generator application to Railway with PostgreSQL and NAV integration.

## Table of Contents

1. [Railway Setup](#railway-setup)
2. [Database Configuration](#database-configuration)
3. [Environment Variables](#environment-variables)
4. [NAV Configuration](#nav-configuration)
5. [Deployment](#deployment)
6. [Post-Deployment Setup](#post-deployment-setup)

## Railway Setup

### 1. Prerequisites

- Railway account ([https://railway.app](https://railway.app))
- GitHub repository with the application code
- NAV Online Invoice account and certificates

### 2. Create New Railway Project

1. **Login to Railway**
   - Go to [https://railway.app](https://railway.app)
   - Sign in with your GitHub account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `transferXMLGenerator` repository
   - Railway will automatically detect the application

3. **Add PostgreSQL Database**
   - In your Railway dashboard, click "New Service"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically provision a PostgreSQL instance

## Database Configuration

The PostgreSQL service will be automatically configured by Railway with the following environment variables:

- `DATABASE_URL` - Complete database connection string
- `PGHOST` - Database host
- `PGPORT` - Database port (default: 5432)
- `PGUSER` - Database username
- `PGPASSWORD` - Database password
- `PGDATABASE` - Database name

## Environment Variables

In your Railway project dashboard, go to **Variables** tab and add the following environment variables:

### Required Variables

```bash
# Django Configuration
SECRET_KEY=your_64_character_secret_key_for_django_security
DEBUG=False
ALLOWED_HOSTS=your-app-name.railway.app,your-custom-domain.com
DJANGO_SETTINGS_MODULE=transferXMLGenerator.settings

# Database (Railway automatically provides DATABASE_URL)
# No need to set individual DB variables when using DATABASE_URL

# Security
CSRF_TRUSTED_ORIGINS=https://your-app-name.railway.app,https://your-custom-domain.com
CORS_ALLOWED_ORIGINS=https://your-app-name.railway.app,https://your-custom-domain.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000

# NAV API Configuration
NAV_BASE_URL=https://api.onlineszamla.nav.gov.hu/invoiceService/v3
NAV_TEST_BASE_URL=https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3

# Static Files
STATIC_URL=/static/
WHITENOISE_USE_FINDERS=True

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Generate Secret Key

Use this command to generate a secure Django secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## NAV Configuration

### 1. Prepare NAV Certificates

Before deployment, you need to prepare your NAV certificates:

1. **Convert P12 certificates to PEM format:**

   ```bash
   # Convert signing certificate
   openssl pkcs12 -in signing-cert.p12 -nocerts -nodes -out signing-key.pem
   openssl pkcs12 -in signing-cert.p12 -clcerts -nokeys -out signing-cert.pem
   cat signing-key.pem signing-cert.pem > signing-combined.pem
   
   # Convert exchange certificate
   openssl pkcs12 -in exchange-cert.p12 -nocerts -nodes -out exchange-key.pem
   openssl pkcs12 -in exchange-cert.p12 -clcerts -nokeys -out exchange-cert.pem
   cat exchange-key.pem exchange-cert.pem > exchange-combined.pem
   ```

2. **Store certificate contents as Railway environment variables:**

   Add these variables in Railway dashboard:
   
   ```bash
   # Base64 encode the certificate files for safe storage
   NAV_SIGNING_KEY_BASE64=$(base64 -w 0 signing-combined.pem)
   NAV_EXCHANGE_KEY_BASE64=$(base64 -w 0 exchange-combined.pem)
   ```

   Or store them directly as multiline variables in Railway:
   ```bash
   NAV_SIGNING_KEY=-----BEGIN PRIVATE KEY-----
   [certificate content here]
   -----END CERTIFICATE-----
   
   NAV_EXCHANGE_KEY=-----BEGIN PRIVATE KEY-----
   [certificate content here]
   -----END CERTIFICATE-----
   ```

## Deployment

### 1. Automatic Deployment

Railway will automatically deploy when you:
- Push to the main branch
- Make changes to environment variables
- Manually trigger a deployment

### 2. Deployment Configuration Files

The repository includes these Railway configuration files:

- **`railway.json`** - Railway project configuration
- **`Procfile`** - Process definition for web server
- **`nixpacks.toml`** - Build configuration with Node.js and Python

### 3. Build Process

Railway will automatically:
1. Install Node.js dependencies
2. Build the React frontend
3. Install Python dependencies
4. Collect Django static files
5. Run database migrations
6. Start the Gunicorn web server

### 4. Monitor Deployment

1. **Deployment Logs**
   - Go to your Railway project dashboard
   - Click on the service
   - View the "Deployments" tab to see build and runtime logs

2. **Service Logs**
   - Click "View Logs" to see real-time application logs
   - Monitor for any errors during startup

## Post-Deployment Setup

### 1. Create Superuser

After successful deployment, create a Django superuser:

1. **Access Railway CLI**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Connect to your project
   railway link
   ```

2. **Create Superuser**
   ```bash
   # Run Django management command
   railway run python backend/manage.py createsuperuser
   ```

   Follow the prompts to create your admin user.

### 2. Configure NAV Integration

1. **Access Admin Interface**
   - Go to `https://your-app-name.railway.app/admin/`
   - Login with your superuser credentials

2. **Create Company Records**
   - Navigate to **Bank Transfers** → **Companies**
   - Create your company record with tax number and details

3. **Setup NAV Configuration**
   - Go to **Bank Transfers** → **NAV Configurations**
   - Click "Add NAV Configuration"
   - Fill in the required fields:
     - **Company**: Select your company
     - **Tax Number**: 8-digit tax number
     - **API Environment**: Choose "production" or "test"
     - **Technical User Login**: Your NAV technical user
     - **Technical User Password**: Your NAV technical user password
     - **Signing Key**: Paste the content of `signing-combined.pem`
     - **Exchange Key**: Paste the content of `exchange-combined.pem`
     - **Sync Enabled**: Check to enable automatic sync
     - **Sync Frequency Hours**: Set to 12 (default)

### 3. Test NAV Connection

1. **Using Railway CLI:**
   ```bash
   # Test NAV connection (replace 1 with your company ID)
   railway run python backend/manage.py test_nav_connection --company-id=1
   
   # Run test sync
   railway run python backend/manage.py sync_nav_invoices --company-id=1 --dry-run
   ```

2. **Expected Output:**
   ```
   NAV connection test successful for company: Your Company Name
   - Tax number: 12345678
   - Environment: production
   - API endpoint reachable: ✓
   - Authentication successful: ✓
   ```

### 4. Setup Automated NAV Sync

Railway doesn't have built-in cron jobs, but you can use Railway's cron service or external services:

#### Option 1: Railway Cron Service

1. **Create new service in Railway:**
   - Add a new service to your project
   - Deploy the same repository
   - Set environment variable: `RAILWAY_SERVICE_TYPE=cron`

2. **Update settings for cron service:**
   ```python
   # In settings.py, add cron-specific configuration
   if os.environ.get('RAILWAY_SERVICE_TYPE') == 'cron':
       # Disable web server for cron service
       ALLOWED_HOSTS = ['*']
   ```

3. **Create cron script:**
   ```bash
   # Create cron.py in backend directory
   import os
   import django
   import schedule
   import time
   
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
   django.setup()
   
   from django.core.management import call_command
   
   def sync_nav_invoices():
       # Add company IDs that need syncing
       company_ids = [1, 2, 3]  # Replace with actual company IDs
       for company_id in company_ids:
           call_command('sync_nav_invoices', company_id=company_id)
   
   # Schedule sync every 12 hours
   schedule.every(12).hours.do(sync_nav_invoices)
   
   if __name__ == '__main__':
       while True:
           schedule.run_pending()
           time.sleep(1)
   ```

#### Option 2: External Cron Service

Use services like:
- **GitHub Actions** with scheduled workflows
- **Render Cron Jobs**
- **Cron-job.org** to call your sync endpoint

Example GitHub Action (`.github/workflows/nav-sync.yml`):
```yaml
name: NAV Invoice Sync
on:
  schedule:
    - cron: '0 */12 * * *'  # Every 12 hours
  workflow_dispatch:  # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Sync NAV Invoices
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          curl -X POST \
            -H "Authorization: Bearer $RAILWAY_TOKEN" \
            "https://backboard.railway.app/graphql" \
            -d '{"query":"mutation { serviceInstanceCommand(environmentId: \"$ENVIRONMENT_ID\", serviceId: \"$SERVICE_ID\", command: \"python manage.py sync_nav_invoices --company-id=1\") { success } }"}'
```

## Domain Configuration

### 1. Custom Domain (Optional)

1. **Add Custom Domain in Railway:**
   - Go to your service settings
   - Click "Domains"
   - Add your custom domain
   - Follow Railway's DNS configuration instructions

2. **Update Environment Variables:**
   ```bash
   ALLOWED_HOSTS=your-app-name.railway.app,yourdomain.com,www.yourdomain.com
   CSRF_TRUSTED_ORIGINS=https://your-app-name.railway.app,https://yourdomain.com,https://www.yourdomain.com
   CORS_ALLOWED_ORIGINS=https://your-app-name.railway.app,https://yourdomain.com,https://www.yourdomain.com
   ```

## Monitoring and Maintenance

### 1. Application Monitoring

1. **Railway Metrics:**
   - CPU and memory usage
   - Request metrics
   - Error rates
   - Response times

2. **Log Monitoring:**
   ```bash
   # View live logs
   railway logs --follow
   
   # Search logs
   railway logs --filter "ERROR"
   ```

### 2. Database Monitoring

1. **PostgreSQL Metrics:**
   - Connection count
   - Query performance
   - Storage usage
   - Backup status

2. **Database Maintenance:**
   ```bash
   # Connect to database
   railway connect postgres
   
   # Run maintenance queries
   VACUUM ANALYZE;
   ```

### 3. Backup Strategy

1. **Railway automatically backs up PostgreSQL**
   - Point-in-time recovery available
   - Daily snapshots retained

2. **Manual Backup:**
   ```bash
   # Export database
   railway run pg_dump $DATABASE_URL > backup.sql
   ```

## Troubleshooting

### Common Issues

1. **Build Failures:**
   - Check deployment logs in Railway dashboard
   - Verify all dependencies in requirements.txt
   - Ensure Node.js and Python versions are compatible

2. **Database Connection Issues:**
   - Verify DATABASE_URL is properly set
   - Check PostgreSQL service is running
   - Review connection logs

3. **Static Files Not Loading:**
   - Ensure `collectstatic` runs during build
   - Verify WhiteNoise configuration
   - Check STATIC_URL and STATIC_ROOT settings

4. **NAV API Issues:**
   - Verify certificate format and content
   - Check technical user credentials
   - Test with NAV test environment first

### Debug Commands

```bash
# Check service status
railway status

# View detailed logs
railway logs --follow

# Run Django shell
railway run python backend/manage.py shell

# Run database migrations manually
railway run python backend/manage.py migrate

# Test NAV connection
railway run python backend/manage.py test_nav_connection --company-id=1
```

## Security Considerations

1. **Environment Variables:**
   - Never commit sensitive data to repository
   - Use Railway's secure environment variable storage
   - Regularly rotate secrets and certificates

2. **Database Security:**
   - Railway PostgreSQL includes SSL by default
   - Access restricted to your Railway services
   - Regular security updates applied automatically

3. **Application Security:**
   - HTTPS enforced by default
   - Security headers configured
   - CSRF and CORS protection enabled

## Scaling

Railway automatically handles:
- **Horizontal Scaling**: Multiple instances based on traffic
- **Vertical Scaling**: CPU and memory allocation
- **Database Scaling**: Storage and performance optimization

Monitor usage and adjust Railway plan as needed for your traffic requirements.

---

This Railway deployment provides a fully managed, scalable solution for the Transfer XML Generator with integrated PostgreSQL and NAV invoice synchronization capabilities.