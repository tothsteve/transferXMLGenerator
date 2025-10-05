# Transfer XML Generator - Frontend

React TypeScript frontend for the Hungarian bank transfer XML/CSV generation system.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Environment Variables](#environment-variables)
- [Available Scripts](#available-scripts)
- [Architecture Overview](#architecture-overview)
- [Troubleshooting](#troubleshooting)
- [Code Quality](#code-quality)

---

## 🚀 Development Setup

### Prerequisites

- **Node.js**: v18.20.5 (specified in `.nvmrc`)
- **npm**: v9+ (comes with Node.js)
- **Backend API**: Django backend running on `http://localhost:8002`

### Initial Setup

1. **Clone the repository** (if not already done):

   ```bash
   git clone <repository-url>
   cd transferXMLGenerator/frontend
   ```

2. **Use the correct Node.js version** (if using nvm):

   ```bash
   nvm use
   ```

   If you don't have this version installed:

   ```bash
   nvm install 18.20.5
   nvm use
   ```

3. **Install dependencies**:

   ```bash
   npm install
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

   **Alternative** (if `npm start` fails with CRACO errors):
   ```bash
   npx react-scripts start
   ```

The app will open at [http://localhost:3000](http://localhost:3000).

> **Note**: The project uses CRACO (Create React App Configuration Override), but it may have compatibility issues with React 19. If you encounter CRACO errors, use `npx react-scripts start` instead.

### Backend Connection

The frontend expects the Django backend API to be running on `http://localhost:8002`.

To start the backend:

```bash
cd ../backend
source bin/activate  # Activate Python virtual environment
python manage.py runserver 8002
```

---

## 🔧 Environment Variables

This project uses Create React App's built-in environment variable system.

### Configuration

Create a `.env.local` file in the frontend root directory (this file is gitignored):

```bash
# API Base URL
REACT_APP_API_URL=http://localhost:8002

# Optional: Enable debug mode
REACT_APP_DEBUG=true
```

### Available Environment Variables

| Variable              | Default                   | Description                      |
| --------------------- | ------------------------- | -------------------------------- |
| `REACT_APP_API_URL`   | `http://localhost:8002`   | Backend API base URL             |
| `REACT_APP_DEBUG`     | `false`                   | Enable debug logging in console  |
| `NODE_ENV`            | `development`/`production`| Build environment (auto-managed) |

### Environment Files

- `.env.local` - Local development overrides (gitignored, create manually)
- `.env.development` - Development defaults
- `.env.production` - Production defaults

**Important**: All custom environment variables must be prefixed with `REACT_APP_` to be accessible in the app.

---

## 📜 Available Scripts

### Development

#### `npm start`

Runs the app in development mode using CRACO (Create React App Configuration Override).

- Opens [http://localhost:3000](http://localhost:3000)
- Hot reloading enabled
- Lint errors shown in console

#### `npm test`

Launches the test runner in interactive watch mode.

- Press `a` to run all tests
- Press `p` to filter by filename pattern
- Press `t` to filter by test name pattern
- Press `q` to quit watch mode

### Building

#### `npm run build`

Creates an optimized production build in the `build/` folder.

- Minified and optimized
- Source maps disabled (`GENERATE_SOURCEMAP=false`)
- ESLint disabled during build (`DISABLE_ESLINT_PLUGIN=true`)

#### `npm run build:fast`

Fast build for development testing (skips type checking and ignores errors).

- No source maps
- No ESLint
- TypeScript errors don't block build (`TSC_COMPILE_ON_ERROR=true`)
- CI mode disabled for faster builds

#### `npm run build:ultra`

Ultra-fast build with maximum optimizations disabled (for emergency deployments).

- All optimizations from `build:fast`
- Inline runtime chunk disabled
- Image inlining disabled
- Increased memory limit (2GB)

**Warning**: Only use `build:ultra` for testing or emergency situations. Production should use `npm run build`.

### Deployment

#### `npm run serve`

Serves the production build locally for testing.

```bash
npm run build
npm run serve
```

Opens at [http://localhost:3000](http://localhost:3000) (or `PORT` environment variable if set).

### Code Quality

#### `npm run format`

Formats all TypeScript files using Prettier.

```bash
npm run format
```

Runs: `prettier --write "src/**/*.{ts,tsx}"`

---

## 🏗️ Architecture Overview

### Tech Stack

- **React 19.1.1** - UI framework
- **TypeScript 4.9.5** - Type safety
- **Material-UI v7** - Component library
- **TanStack Query** (React Query) - API state management
- **React Router v7** - Navigation
- **React Hook Form** - Form handling
- **Zod v3.25.76** - Schema validation
- **Axios** - HTTP client
- **date-fns** - Date utilities
- **@dnd-kit** - Drag and drop functionality

### Project Structure

```
src/
├── components/          # React components
│   ├── BeneficiaryManager/   # Beneficiary CRUD
│   ├── TemplateBuilder/      # Transfer templates
│   ├── TransferWorkflow/     # Main transfer workflow
│   ├── NAVInvoices/          # NAV invoice integration
│   ├── BatchManager/         # Batch management
│   ├── Settings/             # Application settings
│   └── TrustedPartners/      # Trusted partners management
├── hooks/               # Custom React hooks
│   └── api.ts           # React Query hooks for API
├── schemas/             # Zod validation schemas
│   └── api.schemas.ts   # API response schemas
├── services/            # API client services
│   └── api.ts           # Axios API client
├── types/               # TypeScript type definitions
│   └── api.ts           # API response types
├── utils/               # Utility functions
│   ├── bankAccountValidation.ts  # Hungarian account validation
│   └── stringValidation.ts       # String utilities
├── App.tsx              # Main app component
└── index.tsx            # App entry point
```

### Key Features

1. **Multi-Company Architecture**

   - Company context with role-based permissions
   - 4-level user roles (ADMIN, FINANCIAL, ACCOUNTANT, USER)
   - Feature-gated functionality

2. **NAV Invoice Integration**

   - Payment status tracking (UNPAID, PREPARED, PAID)
   - Bulk payment status updates
   - Trusted partners auto-payment
   - STORNO invoice auto-payment

3. **Transfer Workflow**

   - Template-driven transfer creation
   - NAV invoice selection
   - Drag-and-drop ordering
   - XML/CSV export generation

4. **Data Validation**

   - Zod schemas for all API responses
   - Hungarian bank account validation
   - Real-time form validation with React Hook Form

5. **API State Management**
   - React Query for caching and optimistic updates
   - Automatic refetching on window focus
   - Error handling with retry logic

### API Integration

The frontend communicates with the Django backend via REST API at `http://localhost:8002/api/`.

**Key API Endpoints**:

- `/api/auth/` - Authentication and company management
- `/api/beneficiaries/` - Beneficiary CRUD
- `/api/templates/` - Transfer templates
- `/api/transfers/` - Transfer management and XML/CSV generation
- `/api/batches/` - Transfer batches
- `/api/nav-invoices/` - NAV invoice management
- `/api/trusted-partners/` - Trusted partners management
- `/api/bank-accounts/` - Bank account settings

**Swagger Documentation**: [http://localhost:8002/swagger/](http://localhost:8002/swagger/)

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. CRACO Start Fails (React 19 Compatibility)

**Error**: `npm start` fails with CRACO errors or React version incompatibility

**Solution**:

```bash
# Use react-scripts directly instead of CRACO
npx react-scripts start
```

**Why this happens**: CRACO (Create React App Configuration Override) has compatibility issues with React 19. The workaround bypasses CRACO and uses react-scripts directly.

#### 2. Port 3000 Already in Use

**Error**: `Something is already running on port 3000`

**Solution**:

```bash
# Find and kill the process using port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
PORT=3001 npm start
# Or with the workaround:
PORT=3001 npx react-scripts start
```

#### 3. Node Version Mismatch

**Error**: `The engine "node" is incompatible with this module`

**Solution**:

```bash
# Use the correct Node.js version
nvm use 18.20.5

# Or install it first
nvm install 18.20.5
nvm use
```

#### 4. Backend API Not Running

**Error**: `Network Error` or `ECONNREFUSED` in browser console

**Solution**:

```bash
# Start the Django backend
cd ../backend
source bin/activate  # Activate Python virtual environment
python manage.py runserver 8002
```

#### 5. CORS Issues

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**: Check backend `settings.py` has `http://localhost:3000` in `CORS_ALLOWED_ORIGINS`

#### 6. Missing Dependencies

**Error**: `Cannot find module '<package-name>'`

**Solution**:

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

#### 7. TypeScript Errors After `git pull`

**Error**: `Type error: Cannot find module` or similar

**Solution**:

```bash
# Restart TypeScript server (VS Code)
Cmd+Shift+P → "TypeScript: Restart TS Server"

# Or rebuild
npm run build
```

#### 8. Build Fails with Out of Memory

**Error**: `JavaScript heap out of memory`

**Solution**:

```bash
# Use the ultra-fast build (increased memory limit)
npm run build:ultra

# Or increase Node.js memory manually
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

#### 9. Prettier Formatting Issues

**Error**: Code not formatting or conflicts with ESLint

**Solution**:

```bash
# Format all files manually
npm run format

# Or format specific file
npx prettier --write src/path/to/file.tsx
```

#### 10. Authentication Token Expired

**Error**: `401 Unauthorized` after some time

**Solution**: Re-login in the application. JWT tokens expire after 24 hours.

#### 11. React Query Stale Data

**Error**: UI not updating after API changes

**Solution**:

```bash
# Hard refresh in browser
Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)

# Or clear React Query cache (in React DevTools)
```

### Development Tips

#### Enable Verbose Logging

```bash
# Set debug mode
echo "REACT_APP_DEBUG=true" >> .env.local
npm start
```

#### Clear Cache and Restart

```bash
# Full clean restart
rm -rf node_modules build .cache
npm install
npm start
```

#### Check Backend API Health

```bash
# Test backend connection
curl http://localhost:8002/api/auth/profile/

# Or open Swagger docs
open http://localhost:8002/swagger/
```

#### VS Code Extensions

Recommended extensions for development:

- ESLint
- Prettier - Code formatter
- TypeScript Vue Plugin (Volar)
- Auto Rename Tag
- Path Intellisense

---

## ✅ Code Quality

### Linting and Formatting

This project uses:

- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting

```bash
# Format code
npm run format

# Run ESLint manually
npx eslint "src/**/*.{ts,tsx}"

# Auto-fix ESLint issues
npx eslint --fix "src/**/*.{ts,tsx}"
```

### TypeScript

TypeScript strict mode is planned but not yet enabled. Current configuration:

```json
{
  "strict": false,
  "strictNullChecks": false,
  "noImplicitAny": false
}
```

See `ROADMAP.md` for the TypeScript strict mode migration plan.

### Testing

Testing infrastructure is planned for Phase 2 (Weeks 4-6). Target:

- 80% code coverage
- Vitest or Jest
- React Testing Library
- MSW for API mocking

### Quality Roadmap

See `ROADMAP.md` for the complete 12-week quality improvement plan:

- **Phase 0**: ✅ Zod Validation (Complete)
- **Phase 1**: Foundation & Critical Fixes (Weeks 1-3)
- **Phase 2**: Testing Infrastructure (Weeks 4-6)
- **Phase 3**: Documentation & Quality (Weeks 7-9)
- **Phase 4**: Performance & Polish (Weeks 10-12)

---

## 📚 Additional Resources

- **Backend Documentation**: See `../backend/README.md`
- **Project Documentation**: See `../CLAUDE.md`
- **Database Schema**: See `../DATABASE_DOCUMENTATION.md`
- **API Documentation**: [http://localhost:8002/swagger/](http://localhost:8002/swagger/)

---

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Format code: `npm run format`
4. Run tests: `npm test` (when available)
5. Create a pull request

### Commit Message Format

Follow conventional commits format:

```
type(scope): subject

Examples:
feat(transfers): add NAV invoice selection modal
fix(beneficiaries): fix account number validation
docs(readme): update development setup
```

---

## 📄 License

Internal project - IT Cardigan Kft.

---

**Last Updated**: 2025-01-04
**Node Version**: v18.20.5
**React Version**: 19.1.1
**Status**: Active Development
