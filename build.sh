#!/bin/bash

# Railway build script for Django + React application

echo "🚀 Starting build process..."

# Build backend
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

echo "🔧 Installing additional production dependencies..."
pip install gunicorn whitenoise dj-database-url psycopg2-binary

echo "📊 Collecting static files..."
python manage.py collectstatic --noinput --settings=transferXMLGenerator.settings_production

# Build frontend
echo "⚛️ Building React frontend..."
cd ../frontend
npm install
npm run build

# Copy React build to Django static
echo "📋 Copying React build to Django static directory..."
mkdir -p ../backend/static/react
cp -r build/* ../backend/static/react/

echo "✅ Build complete!"