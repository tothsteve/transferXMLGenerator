# NAV Invoice Query UI - Deployment Guide

## Overview
This guide covers deploying the new NAV Invoice Query UI feature that includes:
- Complete invoice management interface
- STORNO invoice filtering with relationship tracking
- Table header transparency fixes
- Database migrations for invoice cancellation relationships

## Prerequisites
- Existing transferXMLGenerator application running
- Database access (SQL Server or PostgreSQL)
- Python 3.11+ environment
- Node.js 16+ for frontend

## 🔄 Database Migrations

### ✅ Current Status
All migrations are **ALREADY APPLIED** in the development environment:
- `0022_invoice_storno_of.py` - Adds ForeignKey relationship for STORNO invoices
- `0023_populate_storno_relationships.py` - Populates existing STORNO relationships (10 relationships populated)

### For Fresh Deployments
If deploying to a new environment, run:

```bash
cd backend
python manage.py migrate
```

### 🚀 Production Deployment (Railway)
For the production environment on Railway:

1. **Automatic Migration**: Migrations run automatically during deployment
2. **Verify Migration Status**: Check logs to ensure migrations complete successfully
3. **Data Migration**: The populate migration will analyze existing invoice data and create STORNO relationships

### Migration Details
- **0022_invoice_storno_of**: Adds `storno_of` ForeignKey field to Invoice model
- **0023_populate_storno_relationships**: Data migration that automatically links existing STORNO invoices to their original invoices based on `original_invoice_number`

## 🖥️ Backend Deployment

### 1. Environment Variables
Ensure these environment variables are set:

**Development:**
```bash
SECRET_KEY=your_secret_key
DB_PASSWORD=your_db_password
NAV_ENCRYPTION_KEY=your_nav_encryption_key  # Generated automatically

# Database configuration (SQL Server)
DB_HOST=localhost
DB_PORT=1435
DB_NAME=administration
```

**Production (Railway):**
```bash
SECRET_KEY=${{secrets.SECRET_KEY}}
DATABASE_URL=${{DATABASE_URL}}  # PostgreSQL connection
NAV_ENCRYPTION_KEY=${{secrets.NAV_ENCRYPTION_KEY}}
DEBUG=False
ALLOWED_HOSTS=transferxmlgenerator-production.up.railway.app
```

### 2. Dependencies
All required dependencies are in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Static Files (Production)
```bash
python manage.py collectstatic --noinput
```

### 4. API Endpoints Verification
Test these new endpoints after deployment:
```bash
# NAV Invoices API
GET /api/nav/invoices/                    # List with filtering
GET /api/nav/invoices/{id}/               # Detail view
GET /api/nav/invoices/stats/              # Statistics

# STORNO Filtering
GET /api/nav/invoices/?hide_storno_invoices=true   # Hide canceled invoices (default)
GET /api/nav/invoices/?hide_storno_invoices=false  # Show all invoices
```

## 🌐 Frontend Deployment

### Development
```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

### Production Deployment

#### Option 1: Railway (Recommended)
1. **Automatic Build**: Railway builds the React app automatically
2. **Environment Variables**: Set in Railway dashboard:
   ```
   REACT_APP_BACKEND_URL=https://transferxmlgenerator-production.up.railway.app
   ```
3. **Deployment**: Push to main branch triggers automatic deployment

#### Option 2: Manual Build & Deploy
```bash
cd frontend
npm install
npm run build

# Deploy build/ directory to your hosting provider
# Ensure REACT_APP_BACKEND_URL is set correctly
```

### 4. New Routes Added
The following routes are now available:
- `/nav-invoices` - Main NAV invoice management page

### 5. Production URL
After deployment, the NAV Invoice UI will be available at:
- **Development**: http://localhost:3000/nav-invoices
- **Production**: https://your-frontend-domain.com/nav-invoices

## 🧪 Testing Checklist

### Backend API Testing
- [ ] `GET /api/nav/invoices/` returns paginated results (20 per page)
- [ ] Search functionality works: `?search=invoice_number`
- [ ] Direction filtering: `?direction=INBOUND` or `?direction=OUTBOUND`
- [ ] Currency filtering: `?currency=HUF`
- [ ] STORNO filtering excludes both STORNO invoices and canceled originals
- [ ] Invoice detail endpoint returns complete invoice data with line items
- [ ] Statistics endpoint returns proper counts

### Frontend UI Testing
- [ ] NAV Számlák menu item appears in sidebar navigation
- [ ] Invoice table loads with proper pagination
- [ ] Search box filters invoices in real-time
- [ ] Direction and currency filters work correctly
- [ ] STORNO filtering checkbox toggles invoice visibility
- [ ] "Sztornó" column appears only when showing canceled invoices
- [ ] Invoice detail dialog opens with complete information
- [ ] Table headers remain opaque when scrolling (no transparency issues)
- [ ] Responsive design works on mobile/tablet

### Database Testing
- [ ] STORNO relationships are properly populated
- [ ] Filtering queries perform efficiently (check query logs)
- [ ] No database errors in application logs

## 🔧 Configuration Changes

### Backend Settings Updates
Key changes made to `settings.py`:
```python
# Fixed pagination configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # ... other settings
}
```

### Database Model Changes
New field added to Invoice model:
```python
storno_of = models.ForeignKey(
    'self', 
    null=True, 
    blank=True, 
    on_delete=models.CASCADE,
    related_name='storno_invoices',
    verbose_name="Eredeti számla (amit ez a storno érvénytelenít)",
    help_text="A STORNO számla által érvénytelenített eredeti számla"
)
```

## 🐛 Common Issues & Solutions

### 1. Migration Issues
**Problem**: Migration fails on fresh database
**Solution**: Ensure NAV invoice data exists before running data migration

### 2. API 404 Errors
**Problem**: `/api/nav/invoices/` returns 404
**Solution**: Verify URL patterns are properly included and server restarted

### 3. Empty Results
**Problem**: API returns empty results despite having data
**Solution**: Check `hide_storno_invoices=false` parameter to see all invoices

### 4. Table Header Transparency
**Problem**: Content visible behind table headers when scrolling
**Solution**: Ensure all `TableCell` headers have `backgroundColor: 'background.paper'`

### 5. Performance Issues
**Problem**: Slow query performance with large datasets
**Solution**: Consider adding database indexes on frequently filtered fields:
```sql
-- Add these indexes for better performance
CREATE INDEX idx_invoice_direction ON bank_transfers_invoice(invoice_direction);
CREATE INDEX idx_invoice_operation ON bank_transfers_invoice(invoice_operation);
CREATE INDEX idx_invoice_storno_of ON bank_transfers_invoice(storno_of_id);
```

## 📊 Performance Considerations

### Database Optimization
- STORNO filtering uses complex queries - monitor performance
- Consider indexes on `invoice_operation` and `storno_of_id` fields
- Pagination limits results to 20 items per page

### Frontend Optimization
- Invoice list uses Material-UI's virtualization for large datasets
- Search is debounced to prevent excessive API calls
- Conditional rendering minimizes DOM updates

## 🔐 Security Notes

- All API endpoints respect existing authentication requirements
- STORNO filtering doesn't expose sensitive data
- Invoice detail modal shows data only for authorized company users

## 🚀 Production Deployment Checklist

### Pre-Deployment (Development Environment)
- [x] All migrations applied successfully
- [x] STORNO relationships populated (10 relationships)
- [x] API endpoints tested and working
- [x] Frontend UI tested across different screen sizes
- [x] Pull request created and reviewed
- [x] No console errors or warnings

### Production Deployment Steps

#### 1. Merge to Main Branch
```bash
# After PR approval, merge to main
git checkout main
git pull origin main
# Railway automatically deploys from main branch
```

#### 2. Monitor Railway Deployment
1. **Check Build Logs**: Ensure no build errors
2. **Verify Migrations**: Confirm migrations run successfully
3. **Check Application Start**: Verify server starts without errors

#### 3. Post-Deployment Verification
- [ ] Backend API accessible at production URL
- [ ] Database migrations completed successfully  
- [ ] NAV invoice API endpoints return data
- [ ] Frontend builds and deploys successfully
- [ ] NAV Számlák menu appears in production UI
- [ ] Invoice table loads with real production data
- [ ] STORNO filtering works correctly
- [ ] No JavaScript errors in browser console

#### 4. Production Environment Testing
- [ ] Test with production dataset (24,610+ invoices)
- [ ] Verify pagination performance with large dataset
- [ ] Test STORNO filtering with real STORNO invoices
- [ ] Confirm table header opacity fixes work
- [ ] Test mobile/responsive design on production

### Post-Deployment Monitoring

#### Performance Metrics to Watch
- API response times for `/api/nav/invoices/`
- Database query performance for STORNO filtering
- Frontend bundle size and load times
- Memory usage with large datasets

#### Error Monitoring
- Django application logs for API errors
- Browser console errors for frontend issues
- Database slow query logs
- 404 errors on new routes

## 📝 Next Steps / Future Enhancements

### Immediate TODOs
- [ ] Add database indexes for better query performance
- [ ] Implement export functionality for filtered invoice lists
- [ ] Add bulk operations (mark multiple invoices)

### Future Features
- [ ] Invoice PDF generation and download
- [ ] Advanced date range filtering
- [ ] Integration with transfer XML generation
- [ ] Email notifications for STORNO invoices

## 🎯 Rollback Plan

If issues occur, rollback steps:
1. **Frontend**: Deploy previous build or disable NAV menu item
2. **Backend**: Revert to previous commit, migrations will remain (safe)
3. **Database**: STORNO relationships can be cleared with: `Invoice.objects.filter(storno_of__isnull=False).update(storno_of=None)`

---

**Pull Request**: [#6](https://github.com/tothsteve/transferXMLGenerator/pull/6)
**Commit**: `4557558` - Add NAV Invoice Query UI with STORNO filtering and table header fixes