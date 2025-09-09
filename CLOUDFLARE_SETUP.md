# Cloudflare Setup for app.cvcoverai.com

This guide helps you configure Cloudflare for your FastAPI application deployed on EC2.

## Cloudflare Configuration

### 1. DNS Settings

In your Cloudflare dashboard:

1. **Add A Record:**
   - **Type**: A
   - **Name**: app
   - **IPv4 address**: Your EC2 public IP address
   - **Proxy status**: Proxied (orange cloud) ✅

2. **Optional CNAME Record:**
   - **Type**: CNAME
   - **Name**: www.app
   - **Target**: app.cvcoverai.com
   - **Proxy status**: Proxied (orange cloud) ✅

### 2. SSL/TLS Settings

1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode to **"Full (strict)"**
3. Enable **"Always Use HTTPS"**

### 3. Page Rules (Optional)

Create page rules for better performance:

1. **Cache Everything:**
   - URL: `app.cvcoverai.com/static/*`
   - Settings: Cache Level = Cache Everything, Edge Cache TTL = 1 month

2. **Bypass Cache for API:**
   - URL: `app.cvcoverai.com/api/*`
   - Settings: Cache Level = Bypass

### 4. Security Settings

1. **Security Level**: Medium
2. **Bot Fight Mode**: On
3. **DDoS Protection**: On
4. **WAF**: Enable if available

### 5. Performance Settings

1. **Auto Minify**: Enable for HTML, CSS, JS
2. **Brotli Compression**: On
3. **HTTP/2**: On
4. **HTTP/3 (with QUIC)**: On

## Benefits of Cloudflare

- **DDoS Protection**: Automatic protection against attacks
- **Global CDN**: Faster loading times worldwide
- **SSL Certificate**: Free SSL certificate management
- **Caching**: Reduced server load
- **Security**: WAF and bot protection
- **Analytics**: Detailed traffic insights

## Important Notes

1. **SSL Certificate**: With Cloudflare, you can use their SSL certificate instead of Let's Encrypt
2. **Real IP**: Cloudflare passes the real visitor IP in headers
3. **Caching**: Be careful with API endpoints - they shouldn't be cached
4. **Health Checks**: Use Cloudflare health checks for monitoring

## Testing Your Setup

```bash
# Test from your server
curl -H "Host: app.cvcoverai.com" http://localhost/health

# Test from external
curl https://app.cvcoverai.com/health

# Check SSL certificate
openssl s_client -connect app.cvcoverai.com:443 -servername app.cvcoverai.com
```

## Troubleshooting

### If SSL doesn't work:
1. Check Cloudflare SSL/TLS settings
2. Verify DNS is pointing to your EC2 IP
3. Ensure Nginx is listening on port 80

### If site is slow:
1. Check Cloudflare caching settings
2. Verify CDN is enabled
3. Check for any page rules blocking content

### If API calls fail:
1. Ensure API endpoints are not cached
2. Check CORS settings in your FastAPI app
3. Verify Cloudflare security settings aren't blocking requests
