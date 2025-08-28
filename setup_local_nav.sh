#!/bin/bash
# Setup script for local NAV development environment

echo "🔧 Setting up local NAV development environment..."

# Set the fixed encryption key for local development
export NAV_ENCRYPTION_KEY=CwXdT2YfsLuEea1FciHRBuLCjLK_a19cWdJVtlhZTYE=

echo "✅ NAV_ENCRYPTION_KEY set for local development"
echo ""
echo "📝 Next steps:"
echo "1. Run Django server: python manage.py runserver"
echo "2. Go to Django admin: http://localhost:8000/admin/"
echo "3. Navigate to NAV Configuration"
echo "4. Re-enter NAV credentials (they will be encrypted with the fixed key)"
echo ""
echo "💡 For each terminal session, run:"
echo "   export NAV_ENCRYPTION_KEY=CwXdT2YfsLuEea1FciHRBuLCjLK_a19cWdJVtlhZTYE="
echo ""
echo "🚀 Or add this line to your ~/.bashrc or ~/.zshrc for permanent setup"