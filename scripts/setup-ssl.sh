#!/bin/bash

# SSL Setup Script for app.cvcover.ai
# This script sets up Let's Encrypt SSL certificate

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

# Install Certbot
install_certbot() {
    log "Installing Certbot..."
    
    # Update package list
    apt update
    
    # Install Certbot and Nginx plugin
    apt install -y certbot python3-certbot-nginx
    
    log "Certbot installed successfully"
}

# Check domain resolution
check_domain() {
    log "Checking domain resolution..."
    
    DOMAIN="app.cvcoverai.com"
    
    # Check if domain resolves to this server
    RESOLVED_IP=$(dig +short $DOMAIN)
    SERVER_IP=$(curl -s ifconfig.me)
    
    if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
        warning "Domain $DOMAIN resolves to $RESOLVED_IP but this server IP is $SERVER_IP"
        warning "Make sure your DNS is pointing to this server before continuing"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Aborted. Please fix DNS first."
        fi
    else
        log "Domain resolution looks good: $DOMAIN -> $RESOLVED_IP"
    fi
}

# Get SSL certificate
get_certificate() {
    log "Getting SSL certificate for app.cvcoverai.com..."
    
    # Run Certbot
    certbot --nginx -d app.cvcoverai.com --non-interactive --agree-tos --email admin@cvcoverai.com
    
    log "SSL certificate obtained successfully"
}

# Test certificate renewal
test_renewal() {
    log "Testing certificate renewal..."
    
    certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        log "Certificate renewal test successful"
    else
        warning "Certificate renewal test failed"
    fi
}

# Check certificate status
check_certificate() {
    log "Checking certificate status..."
    
    certbot certificates
    
    # Test HTTPS
    log "Testing HTTPS connection..."
    if curl -s -o /dev/null -w "%{http_code}" https://app.cvcoverai.com/health | grep -q "200"; then
        log "HTTPS is working correctly"
    else
        warning "HTTPS test failed"
    fi
}

# Update Nginx configuration
update_nginx_config() {
    log "Updating Nginx configuration..."
    
    # Copy the updated configuration
    cp /home/ubuntu/be-cvcover/nginx/be-cvcover.conf /etc/nginx/sites-available/be-cvcover
    
    # Test configuration
    nginx -t
    
    # Reload Nginx
    systemctl reload nginx
    
    log "Nginx configuration updated"
}

# Main setup function
main() {
    log "Starting SSL setup for app.cvcoverai.com..."
    
    check_root
    install_certbot
    check_domain
    get_certificate
    test_renewal
    update_nginx_config
    check_certificate
    
    log "SSL setup completed successfully!"
    
    echo ""
    info "Your site is now available at:"
    info "https://app.cvcoverai.com"
    info "https://app.cvcoverai.com/health"
    info "https://app.cvcoverai.com/docs"
    
    echo ""
    info "Certificate will auto-renew every 90 days"
    info "Check renewal status: sudo certbot certificates"
    info "Test renewal: sudo certbot renew --dry-run"
}

# Show usage
usage() {
    echo "Usage: $0 {setup|renew|status|test}"
    echo ""
    echo "Commands:"
    echo "  setup  - Full SSL setup (first time)"
    echo "  renew  - Test certificate renewal"
    echo "  status - Show certificate status"
    echo "  test   - Test HTTPS connection"
}

# Show certificate status
show_status() {
    log "Certificate Status:"
    certbot certificates
}

# Test renewal
test_renew() {
    log "Testing certificate renewal..."
    certbot renew --dry-run
}

# Test HTTPS
test_https() {
    log "Testing HTTPS connection..."
    curl -I https://app.cvcoverai.com/health
}

# Main script logic
case "$1" in
    setup)
        main
        ;;
    renew)
        test_renew
        ;;
    status)
        show_status
        ;;
    test)
        test_https
        ;;
    *)
        usage
        exit 1
        ;;
esac
