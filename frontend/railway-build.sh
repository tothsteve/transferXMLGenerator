#!/bin/bash
set -e

echo "🚀 Starting Railway build process..."

# Install dependencies quickly
echo "📦 Installing dependencies..."
npm ci --prefer-offline --no-audit --silent --no-fund --no-optional

# Pre-built approach: Check if we can skip build
if [ -d "build" ] && [ "$(ls -A build)" ]; then
    echo "✅ Build directory exists, using cached build"
    exit 0
fi

# Environment optimizations
export NODE_ENV=production
export GENERATE_SOURCEMAP=false
export CI=false
export DISABLE_ESLINT_PLUGIN=true
export TSC_COMPILE_ON_ERROR=true
export SKIP_PREFLIGHT_CHECK=true
export NODE_OPTIONS="--max-old-space-size=1024"

# Quick build
echo "🔨 Building application..."
npm run build

echo "✅ Build complete!"