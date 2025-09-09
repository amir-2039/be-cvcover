#!/bin/bash

# EC2 Server Setup Script for FastAPI Application
# This script prepares a fresh Ubuntu EC2 instance for deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Update system
update_system() {
    log "Updating system packages..."
    apt update && apt upgrade -y
    apt install -y curl wget git unzip
}

# Install Python 3.11
install_python() {
    log "Installing Python 3.11..."
    
    # Add deadsnakes PPA for Python 3.11
    apt install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa
    apt update
    
    # Install Python 3.11 and related packages
    apt install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3.11-distutils \
        python3-pip
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    apt install -y \
        nginx \
        postgresql-client \
        build-essential \
        libpq-dev \
        pkg-config \
        libssl-dev \
        libffi-dev \
        python3-dev \
        supervisor \
        htop \
        vim \
        tree
}

# Configure firewall
setup_firewall() {
    log "Configuring firewall..."
    
    # Install UFW if not present
    apt install -y ufw
    
    # Configure firewall rules
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw allow 8000/tcp  # For direct access if needed
    
    # Enable firewall
    ufw --force enable
    
    log "Firewall configured successfully"
}

# Create application user
create_app_user() {
    log "Creating application user..."
    
    # Create user if it doesn't exist
    if ! id "ubuntu" &>/dev/null; then
        useradd -m -s /bin/bash ubuntu
        usermod -aG sudo ubuntu
        log "Created ubuntu user"
    else
        log "ubuntu user already exists"
    fi
    
    # Create application directory
    mkdir -p /home/ubuntu/be-cvcover
    chown ubuntu:ubuntu /home/ubuntu/be-cvcover
}

# Setup SSH key for GitHub Actions
setup_ssh_key() {
    log "Setting up SSH for GitHub Actions..."
    
    # Create .ssh directory for ubuntu user
    mkdir -p /home/ubuntu/.ssh
    chmod 700 /home/ubuntu/.ssh
    chown ubuntu:ubuntu /home/ubuntu/.ssh
    
    info "To enable GitHub Actions deployment:"
    info "1. Generate an SSH key pair: ssh-keygen -t rsa -b 4096 -C 'github-actions'"
    info "2. Add the public key to /home/ubuntu/.ssh/authorized_keys"
    info "3. Add the private key to GitHub Secrets as EC2_SSH_KEY"
    info "4. Add these secrets to your GitHub repository:"
    info "   - EC2_HOST: Your EC2 public IP"
    info "   - EC2_USERNAME: ubuntu"
    info "   - EC2_PORT: 22"
    info "   - EC2_SSH_KEY: Your private SSH key"
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Create basic configuration
    cat > /etc/nginx/sites-available/be-cvcover << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

    # Enable the site
    ln -sf /etc/nginx/sites-available/be-cvcover /etc/nginx/sites-enabled/
    
    # Test configuration
    nginx -t
    
    # Start and enable Nginx
    systemctl start nginx
    systemctl enable nginx
    
    log "Nginx configured successfully"
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/be-cvcover << 'EOF'
/var/log/be-cvcover/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload be-cvcover
    endscript
}
EOF
}

# Create deployment script
create_deployment_script() {
    log "Creating deployment script..."
    
    # Copy deployment script to server
    cat > /home/ubuntu/deploy.sh << 'EOF'
#!/bin/bash
# This script will be replaced by the actual deployment script from the repository
echo "Deployment script will be available after cloning the repository"
EOF
    
    chmod +x /home/ubuntu/deploy.sh
    chown ubuntu:ubuntu /home/ubuntu/deploy.sh
}

# Setup monitoring
setup_monitoring() {
    log "Setting up basic monitoring..."
    
    # Install htop for system monitoring
    apt install -y htop iotop nethogs
    
    # Create a simple monitoring script
    cat > /home/ubuntu/monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Memory Usage:"
free -h
echo "Disk Usage:"
df -h
    echo "FastAPI Service Status:"
    systemctl status be-cvcover --no-pager
echo "Nginx Status:"
systemctl status nginx --no-pager
EOF
    
    chmod +x /home/ubuntu/monitor.sh
    chown ubuntu:ubuntu /home/ubuntu/monitor.sh
}

# Main setup function
main() {
    log "Starting EC2 server setup for FastAPI application..."
    
    check_root
    update_system
    install_python
    install_system_deps
    setup_firewall
    create_app_user
    configure_nginx
    setup_log_rotation
    create_deployment_script
    setup_monitoring
    
    log "EC2 server setup completed successfully!"
    
    echo ""
    info "Next steps:"
    info "1. Clone your repository: git clone <your-repo-url> /home/ubuntu/be-cvcover"
    info "2. Run the deployment script: cd /home/ubuntu/be-cvcover && ./scripts/deploy.sh deploy"
    info "3. Setup GitHub Actions secrets for automated deployment"
    info "4. Configure SSL certificate (recommended for production)"
    
    echo ""
    info "Useful commands:"
    info "- Monitor system: /home/ubuntu/monitor.sh"
    info "- Check logs: journalctl -u be-cvcover -f"
    info "- Restart app: systemctl restart be-cvcover"
    info "- Check status: systemctl status be-cvcover"
}

# Run main function
main "$@"
