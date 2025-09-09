# FastAPI Application Deployment Guide

This guide will help you deploy your FastAPI application to an EC2 instance using GitHub Actions for automated deployments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [EC2 Instance Setup](#ec2-instance-setup)
3. [GitHub Actions Configuration](#github-actions-configuration)
4. [Manual Deployment](#manual-deployment)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- AWS EC2 instance (Ubuntu 20.04+ recommended)
- Domain name (app.cvcoverai.com configured)
- GitHub repository with your FastAPI application
- Basic knowledge of Linux commands and SSH

## EC2 Instance Setup

### 1. Launch EC2 Instance

1. Go to AWS EC2 Console
2. Launch a new instance with:
   - **AMI**: Ubuntu Server 20.04 LTS or newer
   - **Instance Type**: t3.micro (for testing) or t3.small+ (for production)
   - **Security Group**: Allow SSH (22), HTTP (80), and HTTPS (443)
   - **Key Pair**: Create or use existing key pair

### 2. Connect to Your Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### 3. Run the Setup Script

```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/your-username/your-repo/main/scripts/setup-ec2.sh
sudo bash setup-ec2.sh
```

Or manually run the setup commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install other dependencies
sudo apt install -y nginx postgresql-client build-essential libpq-dev git

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### 4. Clone Your Repository

```bash
cd /home/ubuntu
git clone https://github.com/your-username/your-repo.git fastapi-app
cd fastapi-app
```

### 5. Run Initial Deployment

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh deploy
```

## GitHub Actions Configuration

### 1. Generate SSH Key Pair

On your local machine or EC2 instance:

```bash
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions
```

### 2. Add Public Key to EC2

```bash
# On your EC2 instance
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 3. Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

- **EC2_HOST**: Your EC2 public IP address
- **EC2_USERNAME**: `ubuntu`
- **EC2_PORT**: `22`
- **EC2_SSH_KEY**: Content of your private key (`~/.ssh/github_actions`)

### 4. Test GitHub Actions

Push a change to your main branch:

```bash
git add .
git commit -m "Test deployment"
git push origin main
```

Check the Actions tab in your GitHub repository to see the deployment progress.

## Manual Deployment

### Using the Deployment Script

```bash
# Full deployment (first time)
./scripts/deploy.sh deploy

# Update existing deployment
./scripts/deploy.sh update

# Check status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs

# Restart application
./scripts/deploy.sh restart
```

### Manual Commands

```bash
# Navigate to app directory
cd /home/ubuntu/fastapi-app

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart fastapi-app

# Check status
sudo systemctl status fastapi-app
```

## SSL Certificate Setup

### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d app.cvcoverai.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### Update Nginx Configuration

After getting SSL certificate, update your Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/fastapi-app
```

Uncomment the HTTPS server block and update domain names.

## Monitoring and Maintenance

### System Monitoring

```bash
# Check application status
sudo systemctl status fastapi-app

# View application logs
sudo journalctl -u fastapi-app -f

# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/fastapi-app.access.log
sudo tail -f /var/log/nginx/fastapi-app.error.log

# System resources
htop
df -h
free -h
```

### Application Health Check

```bash
# Test health endpoint
curl http://app.cvcoverai.com/health

# Test API endpoint
curl http://app.cvcoverai.com/api/v1/users/
```

### Backup Strategy

```bash
# Backup application code
tar -czf fastapi-app-backup-$(date +%Y%m%d).tar.gz /home/ubuntu/fastapi-app

# Backup configuration files
sudo tar -czf config-backup-$(date +%Y%m%d).tar.gz /etc/nginx/sites-available/ /etc/systemd/system/fastapi-app.service
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check service status
sudo systemctl status fastapi-app

# Check logs
sudo journalctl -u fastapi-app -n 50

# Check if port is in use
sudo netstat -tlnp | grep :8000
```

#### 2. Nginx 502 Bad Gateway

```bash
# Check if FastAPI app is running
sudo systemctl status fastapi-app

# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

#### 3. Permission Issues

```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/fastapi-app

# Fix permissions
chmod +x scripts/deploy.sh
```

#### 4. Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>
```

### Performance Optimization

#### 1. Increase Workers

Edit the systemd service file:

```bash
sudo nano /etc/systemd/system/fastapi-app.service
```

Update the ExecStart line:

```ini
ExecStart=/home/ubuntu/fastapi-app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 2. Enable Gzip Compression

The Nginx configuration already includes gzip settings.

#### 3. Database Connection Pooling

If using a database, configure connection pooling in your application.

### Security Considerations

1. **Keep system updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Configure fail2ban**:
   ```bash
   sudo apt install -y fail2ban
   sudo systemctl enable fail2ban
   ```

3. **Regular security audits**:
   ```bash
   sudo apt install -y unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

4. **Monitor logs**:
   ```bash
   sudo tail -f /var/log/auth.log
   ```

## Production Checklist

- [ ] SSL certificate installed and configured
- [ ] Domain name pointing to EC2 instance
- [ ] Environment variables configured
- [ ] Database configured (if applicable)
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Security hardening completed
- [ ] Performance optimization applied
- [ ] Log rotation configured
- [ ] Health checks working

## Support

For issues and questions:

1. Check the application logs: `sudo journalctl -u fastapi-app -f`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Verify service status: `sudo systemctl status fastapi-app`
4. Test endpoints: `curl http://app.cvcoverai.com/health`

The configuration is now set up for app.cvcoverai.com domain with Cloudflare integration.
