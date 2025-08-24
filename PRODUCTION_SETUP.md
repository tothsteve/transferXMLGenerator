# Production Setup Guide

This guide covers the complete setup process for the Transfer XML Generator application in a production environment, including PostgreSQL database setup and NAV Online Invoice synchronization.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [PostgreSQL Database Setup](#postgresql-database-setup)
3. [Application Deployment](#application-deployment)
4. [NAV Invoice Sync Configuration](#nav-invoice-sync-configuration)
5. [Environment Variables](#environment-variables)
6. [Database Migrations](#database-migrations)
7. [Security Configuration](#security-configuration)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)

## System Requirements

### Server Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum, SSD recommended
- **Network**: Stable internet connection for NAV API communication

### Software Requirements
- **Python**: 3.9+
- **Node.js**: 18+
- **PostgreSQL**: 13+
- **Nginx**: Latest stable
- **Redis**: 6+ (for caching and background tasks)

## PostgreSQL Database Setup

### 1. Install PostgreSQL

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install PostgreSQL and contrib packages
sudo apt install postgresql postgresql-contrib postgresql-client

# Start and enable PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### CentOS/RHEL
```bash
# Install PostgreSQL repository
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Install PostgreSQL
sudo dnf install -y postgresql14-server postgresql14

# Initialize database
sudo /usr/pgsql-14/bin/postgresql-14-setup initdb

# Start and enable service
sudo systemctl enable --now postgresql-14
```

### 2. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE transfer_generator_prod;

# Create user with password
CREATE USER transfer_app WITH ENCRYPTED PASSWORD 'your_secure_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE transfer_generator_prod TO transfer_app;

# Grant schema permissions
\c transfer_generator_prod
GRANT ALL ON SCHEMA public TO transfer_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO transfer_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO transfer_app;

# Exit psql
\q
```

### 3. Configure PostgreSQL Security

Edit `/etc/postgresql/13/main/pg_hba.conf` (adjust version number as needed):

```bash
# Add this line for local application access
local   transfer_generator_prod   transfer_app                     md5
host    transfer_generator_prod   transfer_app   127.0.0.1/32      md5
```

Edit `/etc/postgresql/13/main/postgresql.conf`:
```bash
# Set listen addresses (for local connections only)
listen_addresses = 'localhost'

# Set max connections
max_connections = 100

# Enable logging
log_statement = 'all'
log_duration = on
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 4. Test Database Connection

```bash
# Test connection
psql -h localhost -U transfer_app -d transfer_generator_prod

# If successful, you should see the PostgreSQL prompt
# Exit with \q
```

## Application Deployment

### 1. Clone and Setup Application

```bash
# Clone repository
git clone https://github.com/tothsteve/transferXMLGenerator.git
cd transferXMLGenerator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Install Node.js dependencies
cd frontend
npm install
npm run build
cd ..
```

### 2. Configure Environment Variables

Create `/home/app/transferXMLGenerator/.env`:

```bash
# Database Configuration
DB_NAME=transfer_generator_prod
DB_USER=transfer_app
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
SECRET_KEY=your_super_secret_django_key_here_64_chars_minimum_recommended
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# NAV API Configuration (see NAV section below)
NAV_BASE_URL=https://api.onlineszamla.nav.gov.hu/invoiceService/v3
NAV_TEST_BASE_URL=https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3

# Security
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email Configuration (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# File Storage
STATIC_ROOT=/var/www/transferxml/static
MEDIA_ROOT=/var/www/transferxml/media
```

## NAV Invoice Sync Configuration

### 1. Understanding NAV Integration

The system integrates with Hungary's NAV (National Tax and Customs Administration) Online Invoice system to automatically synchronize invoice data. This requires:

1. **NAV Registration**: Your company must be registered with NAV for online invoicing
2. **Technical User**: A technical user account with API access
3. **Certificates**: Digital certificates for API authentication
4. **Environment Setup**: Configuration for test and/or production environments

### 2. NAV Account Setup

#### Step 1: Register Technical User
1. Log into NAV Online Invoice interface
2. Navigate to "Technical Users" section
3. Create a new technical user
4. Generate and download the required certificates:
   - **Signing Key**: For API request signing
   - **Exchange Key**: For data encryption

#### Step 2: Company Registration
1. Ensure your company is registered for online invoicing
2. Note your **Tax Number** (8-digit format)
3. Verify API access permissions

### 3. NAV Configuration in Application

#### Step 1: Access Admin Interface
1. Create a superuser account:
```bash
cd backend
python manage.py createsuperuser
```

2. Access admin at `https://yourdomain.com/admin/`
3. Navigate to **Bank Transfers** → **NAV Configurations**

#### Step 2: Create NAV Configuration

For each company in your system, create a NAV configuration:

**Basic Information:**
- **Company**: Select the company
- **Tax Number**: Company's 8-digit tax number
- **API Environment**: Choose "test" or "production"

**Credentials (will be automatically encrypted):**
- **Technical User Login**: Your NAV technical user login
- **Technical User Password**: Your NAV technical user password
- **Signing Key**: Content of your signing certificate
- **Exchange Key**: Content of your exchange certificate

**Sync Settings:**
- **Sync Enabled**: Enable/disable automatic synchronization
- **Sync Frequency Hours**: How often to sync (default: 12 hours)

#### Step 3: Test Configuration

```bash
# Test NAV connection
cd backend
python manage.py test_nav_connection --company-id=1

# Run initial sync (test mode)
python manage.py sync_nav_invoices --company-id=1 --dry-run

# Run actual sync
python manage.py sync_nav_invoices --company-id=1
```

### 4. Production NAV Setup Checklist

- [ ] **NAV Account Setup**
  - [ ] Technical user created and active
  - [ ] Signing and exchange certificates generated
  - [ ] Company registered for online invoicing
  - [ ] API access permissions verified

- [ ] **Application Configuration**
  - [ ] NAV configuration created for each company
  - [ ] Credentials properly encrypted and stored
  - [ ] Environment set to "production"
  - [ ] Sync frequency configured appropriately

- [ ] **Testing**
  - [ ] Connection test successful
  - [ ] Test sync completed without errors
  - [ ] Invoice data properly synchronized
  - [ ] Error handling working correctly

- [ ] **Monitoring**
  - [ ] Sync logs being generated
  - [ ] Error notifications configured
  - [ ] Performance monitoring in place

## Environment Variables Reference

Create `/home/app/transferXMLGenerator/.env` with all required variables:

```bash
# === DATABASE CONFIGURATION ===
DB_NAME=transfer_generator_prod
DB_USER=transfer_app  
DB_PASSWORD=your_secure_db_password
DB_HOST=localhost
DB_PORT=5432

# === DJANGO CORE SETTINGS ===
SECRET_KEY=your_64_character_secret_key_for_django_security
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,127.0.0.1

# === SECURITY SETTINGS ===
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# === NAV API CONFIGURATION ===
# Production NAV API
NAV_BASE_URL=https://api.onlineszamla.nav.gov.hu/invoiceService/v3
# Test NAV API (for development)
NAV_TEST_BASE_URL=https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3

# === EMAIL CONFIGURATION ===
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@company.com
EMAIL_HOST_PASSWORD=your_email_password

# === FILE STORAGE ===
STATIC_URL=/static/
STATIC_ROOT=/var/www/transferxml/static/
MEDIA_URL=/media/
MEDIA_ROOT=/var/www/transferxml/media/

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FILE=/var/log/transferxml/app.log

# === CACHING (OPTIONAL) ===
REDIS_URL=redis://localhost:6379/0
CACHE_TIMEOUT=300

# === BACKUP CONFIGURATION ===
BACKUP_DIR=/var/backups/transferxml/
BACKUP_RETENTION_DAYS=30
```

## Database Migrations

### 1. Apply Initial Migrations

```bash
cd backend
source ../venv/bin/activate

# Apply all migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Load initial data (if any)
# python manage.py loaddata initial_data.json
```

### 2. Setup Database Backup

Create backup script `/home/app/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/transferxml"
DB_NAME="transfer_generator_prod"
DB_USER="transfer_app"
DATE=$(date +"%Y%m%d_%H%M%S")

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

Add to crontab:
```bash
# Add daily backup at 2 AM
0 2 * * * /home/app/backup_db.sh
```

## Security Configuration

### 1. SSL/TLS Setup with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (usually set up automatically)
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Nginx Configuration

Create `/etc/nginx/sites-available/transferxml`:

```nginx
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static files
    location /static/ {
        alias /var/www/transferxml/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/transferxml/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Upload size limits
    client_max_body_size 50M;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/transferxml /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Firewall Setup

```bash
# Install and configure UFW
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH, HTTP, HTTPS
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Allow PostgreSQL only locally
sudo ufw allow from 127.0.0.1 to any port 5432

sudo ufw status
```

## Monitoring and Maintenance

### 1. Application Service Setup

Create systemd service `/etc/systemd/system/transferxml.service`:

```ini
[Unit]
Description=Transfer XML Generator Django App
After=network.target

[Service]
Type=exec
User=app
Group=app
WorkingDirectory=/home/app/transferXMLGenerator/backend
Environment=PATH=/home/app/transferXMLGenerator/venv/bin
ExecStart=/home/app/transferXMLGenerator/venv/bin/gunicorn transferXMLGenerator.wsgi:application --bind 127.0.0.1:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable transferxml
sudo systemctl start transferxml
sudo systemctl status transferxml
```

### 2. Log Rotation

Create `/etc/logrotate.d/transferxml`:

```
/var/log/transferxml/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        systemctl reload transferxml
    endscript
}
```

### 3. Monitoring Script

Create `/home/app/monitor.sh`:

```bash
#!/bin/bash

# Check if application is running
if ! systemctl is-active --quiet transferxml; then
    echo "Transfer XML service is down!" | mail -s "Service Alert" admin@company.com
    systemctl start transferxml
fi

# Check database connection
cd /home/app/transferXMLGenerator/backend
source ../venv/bin/activate
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transferXMLGenerator.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('Database connection OK')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"

# Check disk space
DISK_USAGE=$(df /home/app | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "Disk usage is at ${DISK_USAGE}%" | mail -s "Disk Space Alert" admin@company.com
fi
```

Add to crontab:
```bash
# Monitor every 15 minutes
*/15 * * * * /home/app/monitor.sh
```

### 4. NAV Sync Automation

Add NAV sync to crontab for automatic synchronization:

```bash
# Sync NAV invoices every 12 hours (adjust company-id as needed)
0 */12 * * * cd /home/app/transferXMLGenerator/backend && /home/app/transferXMLGenerator/venv/bin/python manage.py sync_nav_invoices --company-id=1 >> /var/log/transferxml/nav_sync.log 2>&1
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check PostgreSQL service
   sudo systemctl status postgresql
   
   # Check connection from application
   psql -h localhost -U transfer_app -d transfer_generator_prod
   ```

2. **NAV API Connection Issues**
   ```bash
   # Test NAV connection
   python manage.py test_nav_connection --company-id=1
   
   # Check NAV configuration
   python manage.py shell
   >>> from bank_transfers.models import NavConfiguration
   >>> config = NavConfiguration.objects.get(company_id=1)
   >>> print(config.tax_number, config.api_environment)
   ```

3. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R app:app /home/app/transferXMLGenerator
   sudo chmod -R 755 /home/app/transferXMLGenerator
   ```

### Log Locations

- **Application Logs**: `/var/log/transferxml/app.log`
- **NAV Sync Logs**: `/var/log/transferxml/nav_sync.log`
- **Nginx Logs**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL Logs**: `/var/log/postgresql/postgresql-13-main.log`

### Performance Tuning

1. **PostgreSQL Optimization**
   ```sql
   -- Analyze database statistics
   ANALYZE;
   
   -- Check slow queries
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

2. **Django Optimization**
   ```python
   # Add to settings.py for production
   DATABASES['default']['OPTIONS'] = {
       'MAX_CONNS': 20,
       'OPTIONS': {
           'MAX_CONNS': 20,
       }
   }
   ```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review application logs
   - Check NAV sync status
   - Monitor disk space and performance

2. **Monthly**
   - Update system packages
   - Review and rotate logs
   - Test backup restoration
   - Review NAV sync statistics

3. **Quarterly**
   - Update application dependencies
   - Review security configurations
   - Performance optimization review
   - Database maintenance (VACUUM, ANALYZE)

For additional support or questions, refer to the application documentation or contact the development team.