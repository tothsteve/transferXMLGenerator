# Billingo Invoice Synchronization - Automated Sync Setup Guide

**Feature**: Billingo API v3 Integration
**Purpose**: Configure automated synchronization
**Platforms**:
- **Railway.app** (Production - APScheduler, automatic)
- **Linux/macOS/VPS** (Traditional cron)
**Created**: 2025-10-27
**Updated**: 2025-10-27

## Table of Contents

1. [Overview](#overview)
2. [Railway.app Production Setup (Recommended)](#railwayapp-production-setup-recommended)
3. [Traditional Cron Setup (Local/VPS)](#traditional-cron-setup-localvps)
4. [Testing](#testing)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide explains how to configure automated invoice synchronization from Billingo. The management command `sync_billingo_invoices` can be scheduled to run automatically at regular intervals.

### Recommended Schedule

**Daily Sync** (Recommended):
- **Time**: 2:00 AM local time
- **Frequency**: Once per day
- **Reason**: Low server load, updated before business hours

**Alternative Schedules**:
- **Twice Daily**: 2:00 AM and 2:00 PM
- **Weekly**: Sunday 3:00 AM (for low-volume businesses)
- **Hourly**: Every hour during business hours (high-volume only)

---

## Railway.app Production Setup (Recommended)

### ✅ IMPORTANT: Railway Does NOT Use Traditional Cron

Railway.app **does not support traditional cron jobs** (crontab). Instead, this project uses **APScheduler** with automatic initialization via Django's app configuration.

### How It Works

The scheduler is **automatically started** when Django initializes in production:

**File**: `backend/bank_transfers/apps.py`

```python
def ready(self):
    # Only start schedulers on Railway (production)
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT_NAME')
    if railway_env == 'production' and os.environ.get('RUN_MAIN') != 'true':
        self.start_nav_scheduler()
        self.start_mnb_scheduler()
        self.start_billingo_scheduler()  # ← Billingo sync

def start_billingo_scheduler(self):
    """Start the Billingo invoice sync scheduler"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BackgroundScheduler()

    def sync_billingo_invoices():
        from django.core.management import call_command
        call_command('sync_billingo_invoices')

    # Schedule daily at 2:00 AM
    scheduler.add_job(
        func=sync_billingo_invoices,
        trigger=CronTrigger(hour=2, minute=0),
        id='billingo_sync_job',
        name='Billingo Invoice Sync',
        replace_existing=True
    )

    scheduler.start()
```

### Railway Production Deployment

**✅ Already Configured!** The Billingo sync scheduler will **automatically start** when you deploy to Railway production.

**No additional configuration needed** - it works out of the box!

### Environment Detection

The scheduler only runs when:
1. `RAILWAY_ENVIRONMENT_NAME=production` is set (Railway sets this automatically)
2. Django app initializes
3. Feature is enabled for the company
4. API key is configured

### Monitoring Railway Scheduler

**View Logs**:
```bash
# Via Railway CLI
railway logs

# Look for these messages:
# 🧾 Billingo scheduler started (daily at 2:00 AM)
# 🧾 Starting Billingo invoice sync...
# ✅ Billingo sync completed successfully
```

**Check Sync Status** via API:
```bash
curl -X GET https://your-app.railway.app/api/billingo-sync-logs/ \
  -H "Authorization: Bearer $TOKEN"
```

### Changing Schedule on Railway

To change the sync schedule (e.g., from daily to every 6 hours):

1. **Edit** `backend/bank_transfers/apps.py`:
```python
# Change from:
trigger=CronTrigger(hour=2, minute=0),  # Daily at 2:00 AM

# To:
trigger=CronTrigger(hour="*/6"),  # Every 6 hours
```

2. **Deploy** to Railway:
```bash
git add backend/bank_transfers/apps.py
git commit -m "Change Billingo sync to every 6 hours"
git push
```

3. **Verify** scheduler restarted with new schedule in Railway logs

### Railway vs Traditional Cron

| Feature | Railway (APScheduler) | Traditional Cron |
|---------|----------------------|------------------|
| **Setup Required** | None (automatic) | Manual crontab editing |
| **Supported On** | Railway.app | Linux/macOS/VPS |
| **Deployment** | Git push | SSH + crontab |
| **Logs** | Railway dashboard | Log files |
| **Schedule Changes** | Code change + deploy | SSH + crontab -e |
| **Multiple Schedulers** | Supported (NAV, MNB, Billingo) | Multiple cron entries |

---

## Traditional Cron Setup (Local/VPS)

**Use this section if you are deploying to:**
- Local development machine
- Linux VPS (DigitalOcean, AWS EC2, etc.)
- macOS server
- Any environment with traditional cron support

**⚠️ Skip this section if deploying to Railway.app** (see section above)

---

## Prerequisites

### 1. Feature Enabled

Ensure `BILLINGO_SYNC` feature is enabled for the company:

```python
# In Django shell
python manage.py shell

from bank_transfers.models import Company, FeatureTemplate
company = Company.objects.get(id=4)
feature = FeatureTemplate.objects.get(feature_code='BILLINGO_SYNC')
company.enable_feature(feature)
```

### 2. API Key Configured

Billingo API key must be set up via the admin interface or API:

```bash
# Via API (ADMIN role required)
curl -X POST http://localhost:8002/api/billingo-settings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"api_key_input\":\"YOUR_API_KEY\",\"is_active\":true}"
```

### 3. Management Command Available

Verify the management command exists:

```bash
cd /path/to/backend
python manage.py sync_billingo_invoices --help
```

Expected output:
```
usage: manage.py sync_billingo_invoices [-h] [--company-id COMPANY_ID] [--verbose]

Synchronize invoices from Billingo API for all active companies

optional arguments:
  -h, --help            show this help message and exit
  --company-id COMPANY_ID
                        Sync only a specific company by ID
  --verbose             Display detailed per-company results
```

---

## Cron Setup

### Step 1: Identify Python Environment

Find the correct Python interpreter and Django project path:

```bash
# For virtual environment
which python
# Output example: /path/to/venv/bin/python

# For system Python
which python3
# Output example: /usr/bin/python3

# Project directory
pwd
# Output example: /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend
```

### Step 2: Create Cron Entry

Edit the crontab:

```bash
crontab -e
```

### Step 3: Add Sync Job

Add one of these entries based on your needs:

#### Option A: Daily Sync at 2:00 AM (Recommended)

```bash
# Billingo Invoice Sync - Daily at 2:00 AM
0 2 * * * cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend && /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/venv/bin/python manage.py sync_billingo_invoices >> /var/log/billingo_sync.log 2>&1
```

#### Option B: Sync Specific Company

```bash
# Billingo Sync for Company ID 4 - Daily at 2:00 AM
0 2 * * * cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend && /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/venv/bin/python manage.py sync_billingo_invoices --company-id 4 >> /var/log/billingo_sync_company4.log 2>&1
```

#### Option C: Verbose Logging

```bash
# Billingo Sync with detailed output - Daily at 2:00 AM
0 2 * * * cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend && /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/venv/bin/python manage.py sync_billingo_invoices --verbose >> /var/log/billingo_sync_verbose.log 2>&1
```

#### Option D: Twice Daily

```bash
# Billingo Sync - Twice daily (2 AM and 2 PM)
0 2,14 * * * cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend && /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/venv/bin/python manage.py sync_billingo_invoices >> /var/log/billingo_sync.log 2>&1
```

#### Option E: Business Hours Only (Every 4 hours, 8 AM - 8 PM)

```bash
# Billingo Sync - Business hours every 4 hours
0 8,12,16,20 * * * cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend && /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/venv/bin/python manage.py sync_billingo_invoices >> /var/log/billingo_sync.log 2>&1
```

### Step 4: Save and Exit

- **vi/vim**: Press `ESC`, type `:wq`, press `ENTER`
- **nano**: Press `CTRL+X`, then `Y`, then `ENTER`

### Step 5: Verify Cron Entry

```bash
crontab -l | grep billingo
```

Should show your cron entry.

---

## Cron Syntax Reference

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Common Patterns

| Pattern | Meaning | Example Time |
|---------|---------|--------------|
| `0 2 * * *` | Daily at 2:00 AM | 02:00 every day |
| `0 */4 * * *` | Every 4 hours | 00:00, 04:00, 08:00... |
| `30 1 * * 0` | Weekly Sunday 1:30 AM | 01:30 every Sunday |
| `0 2 1 * *` | Monthly on 1st at 2:00 AM | 02:00 on 1st of month |
| `0 2,14 * * *` | Twice daily | 02:00 and 14:00 |

---

## Log File Setup

### Create Log Directory

```bash
# System-wide logs (requires sudo)
sudo mkdir -p /var/log/billingo
sudo chown $(whoami) /var/log/billingo

# User-specific logs (no sudo)
mkdir -p ~/logs/billingo
```

### Update Cron Entry with Log Path

```bash
# System log
0 2 * * * cd /path/to/backend && python manage.py sync_billingo_invoices >> /var/log/billingo/sync.log 2>&1

# User log
0 2 * * * cd /path/to/backend && python manage.py sync_billingo_invoices >> ~/logs/billingo/sync.log 2>&1
```

### Log Rotation

Create `/etc/logrotate.d/billingo`:

```bash
/var/log/billingo/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
}
```

---

## Testing

### Manual Test Before Cron

Run the command manually to verify it works:

```bash
cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend
source venv/bin/activate  # If using virtualenv
python manage.py sync_billingo_invoices --verbose
```

Expected output:
```
========================================
Billingo Invoice Synchronization
========================================
Found 1 companies with active Billingo settings

[1/1] IT Cardigan Kft. (ID: 4)
----------------------------------------
  Status: ✓ Success
  Processed: 282 invoices
  Created: 0
  Updated: 282
  Skipped: 0
  Items: 581
  Duration: 3 seconds
  Errors: 0

========================================
Summary
========================================
Total companies: 1
Successful: 1
Failed: 0
Total invoices: 282
Total duration: 3 seconds
```

### Test Cron Job

Run cron command manually:

```bash
cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend && /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend/venv/bin/python manage.py sync_billingo_invoices >> /tmp/billingo_test.log 2>&1

# Check log
cat /tmp/billingo_test.log
```

### Force Cron to Run Now

Edit crontab to run in next minute:

```bash
crontab -e

# Change to run in next minute (if current time is 14:25, set to 14:26)
26 14 * * * cd /path/to/backend && python manage.py sync_billingo_invoices >> /tmp/billingo_test.log 2>&1
```

Wait for the minute to pass, then check:

```bash
cat /tmp/billingo_test.log
```

Remember to change it back to desired time!

---

## Monitoring

### Check Cron Execution

View cron logs:

```bash
# macOS
log show --predicate 'process == "cron"' --info --last 1h

# Linux (systemd)
journalctl -u cron -n 50

# Linux (syslog)
grep CRON /var/log/syslog | tail -20
```

### Check Application Logs

```bash
# View last sync
tail -50 /var/log/billingo_sync.log

# Watch live
tail -f /var/log/billingo_sync.log

# Search for errors
grep -i error /var/log/billingo_sync.log

# Count successful syncs today
grep -c "Success" /var/log/billingo_sync.log
```

### Check Django Sync Logs

Via Django shell:

```python
python manage.py shell

from bank_transfers.models import BillingoSyncLog
from datetime import timedelta
from django.utils import timezone

# Last 10 syncs
logs = BillingoSyncLog.objects.order_by('-started_at')[:10]
for log in logs:
    print(f"{log.started_at} - {log.status} - {log.invoices_processed} invoices")

# Failed syncs in last 7 days
failed = BillingoSyncLog.objects.filter(
    started_at__gte=timezone.now() - timedelta(days=7),
    status__in=['FAILED', 'PARTIAL']
)
print(f"Failed syncs: {failed.count()}")
```

Via API:

```bash
read TOKEN < /tmp/clean_token.txt; curl -s -X GET http://localhost:8002/api/billingo-sync-logs/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## Troubleshooting

### Cron Job Not Running

**Issue**: No log entries created

**Solutions**:
1. **Check Cron Service**:
   ```bash
   # macOS
   sudo launchctl list | grep cron

   # Linux
   sudo systemctl status cron
   sudo systemctl start cron
   ```

2. **Verify Cron Syntax**:
   ```bash
   crontab -l
   ```

3. **Check Permissions**:
   ```bash
   ls -l /var/log/billingo_sync.log
   chmod 644 /var/log/billingo_sync.log
   ```

4. **Test Path**:
   ```bash
   cd /Users/tothi/Workspace/ITCardigan/git/transferXMLGenerator/backend && pwd
   ```

### Command Fails in Cron

**Issue**: Works manually but fails in cron

**Solutions**:
1. **Full Paths**: Use absolute paths for Python and manage.py
2. **Environment Variables**: Set in crontab:
   ```bash
   SHELL=/bin/bash
   PATH=/usr/local/bin:/usr/bin:/bin
   DB_PASSWORD=your_password
   SECRET_KEY=your_secret_key

   0 2 * * * cd /path/to/backend && python manage.py sync_billingo_invoices
   ```

3. **Load Virtual Environment**:
   ```bash
   0 2 * * * cd /path/to/backend && source venv/bin/activate && python manage.py sync_billingo_invoices
   ```

### Sync Failures

**Issue**: Cron runs but sync fails

**Check**:
1. **API Key Valid**: Test in Billingo dashboard
2. **Network Access**: Verify server can reach api.billingo.hu
3. **Database Connection**: Check DB credentials
4. **Logs**: Review detailed error messages

**Fix**:
```bash
# Run with verbose flag
python manage.py sync_billingo_invoices --verbose
```

### High Memory Usage

**Issue**: Sync consumes too much memory

**Solutions**:
1. **Reduce Page Size** (modify service code if needed)
2. **Sync Per Company**:
   ```bash
   # Stagger syncs for different companies
   0 2 * * * python manage.py sync_billingo_invoices --company-id 1
   30 2 * * * python manage.py sync_billingo_invoices --company-id 2
   0 3 * * * python manage.py sync_billingo_invoices --company-id 3
   ```

---

## Email Notifications (Optional)

### Send Email on Failure

Create wrapper script `/usr/local/bin/billingo-sync-with-email.sh`:

```bash
#!/bin/bash
LOG_FILE="/var/log/billingo_sync.log"
cd /path/to/backend
python manage.py sync_billingo_invoices >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    echo "Billingo sync failed at $(date)" | mail -s "Billingo Sync Failure" admin@example.com
fi
```

Make executable:
```bash
chmod +x /usr/local/bin/billingo-sync-with-email.sh
```

Update crontab:
```bash
0 2 * * * /usr/local/bin/billingo-sync-with-email.sh
```

---

## Best Practices

1. **Schedule During Low Activity**
   - Run during off-peak hours (2-4 AM)
   - Avoid business hours for large syncs

2. **Monitor Regularly**
   - Check logs weekly
   - Review sync metrics monthly
   - Set up alerts for failures

3. **Log Retention**
   - Rotate logs to prevent disk filling
   - Archive old logs for audit trail
   - Keep 30 days of recent logs

4. **Test Changes**
   - Always test manually before deploying cron
   - Use test company for validation
   - Monitor first few runs closely

5. **Documentation**
   - Document custom schedule reasons
   - Note any company-specific requirements
   - Keep crontab comments up to date

---

## Production Deployment

### Step-by-Step Checklist

- [ ] Feature enabled for company
- [ ] API key configured and tested
- [ ] Management command tested manually
- [ ] Log directory created with permissions
- [ ] Cron entry added and verified
- [ ] Log rotation configured
- [ ] Monitoring alerts set up
- [ ] Documentation updated
- [ ] Team notified of schedule
- [ ] First run monitored

### Rollback Plan

If issues occur:

1. **Disable Cron**: Comment out crontab entry
   ```bash
   crontab -e
   # Add # at start of line
   # 0 2 * * * cd /path...
   ```

2. **Investigate**: Check logs and sync history

3. **Fix Issues**: Resolve root cause

4. **Re-enable**: Remove # and save

---

## Support Contacts

- **Cron Issues**: System Administrator
- **Sync Failures**: Backend Team
- **Billingo API**: Billingo Support (support@billingo.hu)
- **Database Issues**: DBA Team

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Maintained By**: DevOps Team
