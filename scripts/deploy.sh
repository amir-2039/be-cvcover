#!/bin/bash

# FastAPI Application Deployment Script
# This script handles the deployment of the FastAPI application on EC2

set -e  # Exit on any error

# Configuration
APP_NAME="be-cvcover"
APP_DIR="/home/ubuntu/be-cvcover"
SERVICE_NAME="be-cvcover"
NGINX_CONFIG="/etc/nginx/sites-available/be-cvcover"
NGINX_ENABLED="/etc/nginx/sites-enabled/be-cvcover"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
}

# Install required system packages
install_dependencies() {
    log "Installing system dependencies..."
    sudo apt install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        nginx \
        git \
        curl \
        build-essential \
        libpq-dev \
        postgresql-client
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."
    
    if [ ! -d "$APP_DIR" ]; then
        mkdir -p "$APP_DIR"
        log "Created application directory: $APP_DIR"
    fi
    
    # Navigate to application directory
    cd "$APP_DIR" || error "Failed to navigate to application directory: $APP_DIR"
    
    # Verify we're in the right directory
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt not found in $APP_DIR. Make sure you're running this script from the correct location."
    fi
    
    log "Working directory: $(pwd)"
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
        log "Created virtual environment"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    log "Virtual environment activated"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    log "Python dependencies installed"
}

# Create systemd service file
create_systemd_service() {
    log "Creating systemd service..."
    
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=${APP_DIR}
Environment=PATH=${APP_DIR}/venv/bin
ExecStart=${APP_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    log "Systemd service created and enabled"
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    # Create Nginx configuration
    sudo tee $NGINX_CONFIG > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

    # Enable the site
    sudo ln -sf $NGINX_CONFIG $NGINX_ENABLED
    
    # Remove default site if it exists
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    sudo nginx -t
    
    # Restart Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log "Nginx configured and started"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    sudo ufw allow ssh
    sudo ufw allow 'Nginx Full'
    sudo ufw --force enable
    
    log "Firewall configured"
}

# Start the application
start_application() {
    log "Starting the application..."
    
    sudo systemctl start ${SERVICE_NAME}
    sudo systemctl status ${SERVICE_NAME} --no-pager
    
    log "Application started successfully"
}

# Main deployment function
deploy() {
    log "Starting deployment process..."
    
    # Check if we're in the right directory (should contain requirements.txt)
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt not found. Please run this script from the project root directory."
    fi
    
    check_root
    update_system
    install_dependencies
    setup_app_directory
    setup_venv
    install_python_deps
    create_systemd_service
    configure_nginx
    setup_firewall
    start_application
    
    log "Deployment completed successfully!"
    log "Application is running at: http://$(curl -s ifconfig.me)"
    log "Health check: http://$(curl -s ifconfig.me)/health"
}

# Update function for existing deployments
update() {
    log "Updating application..."
    
    # Navigate to application directory
    cd "$APP_DIR" || error "Failed to navigate to application directory: $APP_DIR"
    
    # Verify we're in the right directory
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt not found in $APP_DIR"
    fi
    
    # Pull latest changes
    git pull origin main
    
    # Update dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Restart service
    sudo systemctl restart ${SERVICE_NAME}
    
    log "Application updated successfully!"
}

# Show usage
usage() {
    echo "Usage: $0 {deploy|update|status|logs|restart}"
    echo ""
    echo "Commands:"
    echo "  deploy  - Full deployment (first time setup)"
    echo "  update  - Update existing deployment"
    echo "  status  - Show application status"
    echo "  logs    - Show application logs"
    echo "  restart - Restart the application"
}

# Show status
show_status() {
    log "Application Status:"
    sudo systemctl status ${SERVICE_NAME} --no-pager
    echo ""
    log "Nginx Status:"
    sudo systemctl status nginx --no-pager
}

# Show logs
show_logs() {
    log "Application Logs:"
    sudo journalctl -u ${SERVICE_NAME} -f
}

# Restart application
restart_app() {
    log "Restarting application..."
    sudo systemctl restart ${SERVICE_NAME}
    log "Application restarted"
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    update)
        update
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    restart)
        restart_app
        ;;
    *)
        usage
        exit 1
        ;;
esac
