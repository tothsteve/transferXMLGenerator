#!/bin/bash

# Transfer XML Generator - Production Installation Script
# This script automates the installation of the Transfer XML Generator application
# for production use with PostgreSQL and NAV integration.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="app"
APP_DIR="/home/$APP_USER/transferXMLGenerator"
VENV_DIR="$APP_DIR/venv"
DB_NAME="transfer_generator_prod"
DB_USER="transfer_app"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
}

# Check OS compatibility
check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ $ID == "ubuntu" ]] || [[ $ID == "debian" ]]; then
            print_status "Detected $PRETTY_NAME - compatible OS"
            PACKAGE_MANAGER="apt"
        elif [[ $ID == "centos" ]] || [[ $ID == "rhel" ]] || [[ $ID == "fedora" ]]; then
            print_status "Detected $PRETTY_NAME - compatible OS"
            PACKAGE_MANAGER="yum"
        else
            print_error "Unsupported operating system: $PRETTY_NAME"
            exit 1
        fi
    else
        print_error "Cannot determine operating system"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    
    if [[ $PACKAGE_MANAGER == "apt" ]]; then
        sudo apt update
        sudo apt install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            postgresql \
            postgresql-contrib \
            postgresql-client \
            postgresql-server-dev-all \
            nginx \
            curl \
            git \
            build-essential \
            libpq-dev \
            nodejs \
            npm
    elif [[ $PACKAGE_MANAGER == "yum" ]]; then
        sudo yum update -y
        sudo yum install -y \
            python3 \
            python3-pip \
            python3-devel \
            postgresql-server \
            postgresql-devel \
            postgresql-contrib \
            nginx \
            curl \
            git \
            gcc \
            gcc-c++ \
            make \
            nodejs \
            npm
            
        # Initialize PostgreSQL on CentOS/RHEL
        if [[ ! -d "/var/lib/pgsql/data/postgresql.conf" ]]; then
            sudo postgresql-setup --initdb
        fi
    fi
    
    print_success "System dependencies installed"
}

# Create application user
create_app_user() {
    if ! id "$APP_USER" &>/dev/null; then
        print_status "Creating application user: $APP_USER"
        sudo useradd -m -s /bin/bash $APP_USER
        print_success "Application user created"
    else
        print_status "Application user $APP_USER already exists"
    fi
}

# Setup PostgreSQL
setup_postgresql() {
    print_status "Setting up PostgreSQL..."
    
    # Start and enable PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Generate random password for database user
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || print_warning "Database $DB_NAME may already exist"
    sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER;"
    sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
    sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
    
    # Store password for later use
    echo "$DB_PASSWORD" > /tmp/db_password
    
    print_success "PostgreSQL setup completed"
}

# Clone and setup application
setup_application() {
    print_status "Setting up application..."
    
    # Switch to app user for remaining operations
    sudo -u $APP_USER bash << EOF
set -e

# Create directory and clone repository
if [[ ! -d "$APP_DIR" ]]; then
    git clone https://github.com/tothsteve/transferXMLGenerator.git $APP_DIR
fi

cd $APP_DIR

# Create virtual environment
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install Python dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies and build frontend
cd ../frontend
npm install
npm run build

print_success "Application setup completed"
EOF
}

# Generate environment configuration
generate_env_config() {
    print_status "Generating environment configuration..."
    
    # Generate Django secret key
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    DB_PASSWORD=$(cat /tmp/db_password)
    
    # Create .env file
    sudo -u $APP_USER bash << EOF
cat > $APP_DIR/.env << 'ENVEOF'
# Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# NAV API Configuration
NAV_BASE_URL=https://api.onlineszamla.nav.gov.hu/invoiceService/v3
NAV_TEST_BASE_URL=https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3

# Security
CSRF_TRUSTED_ORIGINS=http://localhost,https://localhost
CORS_ALLOWED_ORIGINS=http://localhost,https://localhost

# File Storage
STATIC_ROOT=/var/www/transferxml/static
MEDIA_ROOT=/var/www/transferxml/media

# Logging
LOG_LEVEL=INFO
ENVEOF
EOF

    # Clean up password file
    rm -f /tmp/db_password
    
    print_success "Environment configuration generated"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    sudo -u $APP_USER bash << EOF
cd $APP_DIR/backend
source $VENV_DIR/bin/activate

# Run migrations
python manage.py migrate

# Create static files directory
sudo mkdir -p /var/www/transferxml/static
sudo mkdir -p /var/www/transferxml/media
sudo chown -R $APP_USER:$APP_USER /var/www/transferxml

# Collect static files
python manage.py collectstatic --noinput
EOF

    print_success "Database migrations completed"
}

# Setup systemd service
setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/transferxml.service > /dev/null << EOF
[Unit]
Description=Transfer XML Generator Django App
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$VENV_DIR/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn transferXMLGenerator.wsgi:application --bind 127.0.0.1:8000
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable transferxml
    
    print_success "Systemd service configured"
}

# Setup nginx
setup_nginx() {
    print_status "Setting up Nginx..."
    
    sudo tee /etc/nginx/sites-available/transferxml > /dev/null << 'EOF'
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    server_name _;

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

    client_max_body_size 50M;
}
EOF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/transferxml /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    sudo nginx -t
    
    print_success "Nginx configured"
}

# Start services
start_services() {
    print_status "Starting services..."
    
    sudo systemctl start transferxml
    sudo systemctl start nginx
    
    # Check if services are running
    sleep 5
    
    if sudo systemctl is-active --quiet transferxml; then
        print_success "Transfer XML service is running"
    else
        print_error "Transfer XML service failed to start"
        sudo systemctl status transferxml --no-pager
    fi
    
    if sudo systemctl is-active --quiet nginx; then
        print_success "Nginx service is running"
    else
        print_error "Nginx service failed to start"
        sudo systemctl status nginx --no-pager
    fi
}

# Create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    
    echo ""
    echo "Please create a superuser account for the Django admin:"
    echo ""
    
    sudo -u $APP_USER bash << EOF
cd $APP_DIR/backend
source $VENV_DIR/bin/activate
python manage.py createsuperuser
EOF
    
    print_success "Superuser created"
}

# Setup firewall
setup_firewall() {
    print_status "Setting up firewall..."
    
    # Install UFW if not present
    if ! command -v ufw &> /dev/null; then
        if [[ $PACKAGE_MANAGER == "apt" ]]; then
            sudo apt install -y ufw
        fi
    fi
    
    if command -v ufw &> /dev/null; then
        sudo ufw --force enable
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow http
        sudo ufw allow https
        
        print_success "Firewall configured"
    else
        print_warning "UFW not available, please configure firewall manually"
    fi
}

# Print final information
print_final_info() {
    echo ""
    echo "================================================="
    echo "🎉 Installation completed successfully!"
    echo "================================================="
    echo ""
    echo "Application Information:"
    echo "  - Application URL: http://$(hostname -I | awk '{print $1}')"
    echo "  - Admin URL: http://$(hostname -I | awk '{print $1}')/admin/"
    echo "  - Application directory: $APP_DIR"
    echo "  - Configuration file: $APP_DIR/.env"
    echo ""
    echo "Service Management:"
    echo "  - Start: sudo systemctl start transferxml"
    echo "  - Stop: sudo systemctl stop transferxml"
    echo "  - Restart: sudo systemctl restart transferxml"
    echo "  - Status: sudo systemctl status transferxml"
    echo ""
    echo "Next Steps:"
    echo "  1. Access the admin interface to configure NAV settings"
    echo "  2. Create company records and NAV configurations"
    echo "  3. Configure SSL/TLS with Let's Encrypt (see PRODUCTION_SETUP.md)"
    echo "  4. Set up regular backups and monitoring"
    echo ""
    echo "Documentation:"
    echo "  - Full setup guide: $APP_DIR/PRODUCTION_SETUP.md"
    echo "  - NAV configuration: Admin > Bank Transfers > NAV Configurations"
    echo ""
    echo "⚠️  Important: Review and update the .env file with your specific configuration!"
    echo "================================================="
}

# Main installation flow
main() {
    echo "================================================="
    echo "Transfer XML Generator - Installation Script"
    echo "================================================="
    
    check_root
    check_os
    
    print_status "Starting installation process..."
    
    install_dependencies
    create_app_user
    setup_postgresql
    setup_application
    generate_env_config
    run_migrations
    setup_systemd_service
    setup_nginx
    start_services
    create_superuser
    setup_firewall
    
    print_final_info
}

# Run main function
main "$@"