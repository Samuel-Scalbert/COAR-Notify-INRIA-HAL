# Nginx Reverse Proxy Configuration

This guide covers configuring Nginx as a reverse proxy for the COAR Notify INRIA HAL service, ensuring proper URL handling and header forwarding when deploying behind a web server.

## Overview

When deploying the COAR Notify service behind a reverse proxy like Nginx, proper configuration is essential for:

- **URL Generation**: Ensuring Flask generates correct URLs when behind a proxy
- **Header Forwarding**: Passing along important client and request information
- **Path Rewriting**: Handling application deployment under a URL prefix
- **Security**: Adding SSL termination and security headers

## Basic Nginx Configuration

### Direct Proxy (No Prefix)

This configuration proxies the service at the root domain:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Optional: Redirect to HTTPS
    # return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Proxy Configuration
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
```

### Proxy with URL Prefix

This configuration deploys the service under a URL prefix (e.g., `/coar`):

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Proxy with prefix
    location /coar {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /coar;

        # Remove prefix for Flask app
        rewrite ^/coar(.*)$ $1 break;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Handle static files directly (optional)
    location /coar/static {
        alias /path/to/COAR-Notify-INRIA-HAL/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Docker Compose Integration

### Option 1: Nginx as Additional Service

Add Nginx to your `docker-compose.yml`:

```yaml
services:
  arangodb:
    # ... existing configuration

  app:
    # ... existing configuration
    # Remove direct port mapping as Nginx will handle it
    # ports:
    #   - "${FLASK_PORT:-5000}:5000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./app/static:/usr/share/nginx/html/static:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  arangodb_data:
  arangodb_apps:
```

### Option 2: Host Nginx with Docker Backend

Install Nginx on the host system and use the above configuration, pointing to the Docker container:

```nginx
# In your Nginx configuration
location /coar {
    proxy_pass http://127.0.0.1:5000;
    # ... rest of configuration
}
```

Make sure your Docker Compose exposes the port only to the host:

```yaml
services:
  app:
    # ... existing configuration
    ports:
      - "127.0.0.1:${FLASK_PORT:-5000}:5000"  # Only bind to localhost
```

## Flask Application Configuration

The Flask application is configured to work with reverse proxies through the following changes made to `app/app.py`:

```python
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure ProxyFix for reverse proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
```

### ProxyFix Parameters

- **x_for=1**: Trust one X-Forwarded-For header (set by your reverse proxy)
- **x_proto=1**: Trust one X-Forwarded-Proto header (http/https scheme)
- **x_host=1**: Trust one X-Forwarded-Host header (original host requested by client)
- **x_prefix=1**: Trust one X-Forwarded-Prefix header (URL prefix if app under subdirectory)

## Environment Variables for Reverse Proxy

Add these variables to your `.env` file or Docker Compose environment:

```bash
# Forwarded protocol (usually https when behind proxy)
FORWARDED_FOR_PROTO=https

# Script name/prefix (empty if at root, or "/coar" for subdirectory)
SCRIPT_NAME=""

# Force Flask to trust proxy headers
FLASK_ENV=production
```

## Common Configurations

### University/Research Infrastructure

```nginx
server {
    listen 443 ssl;
    server_name coar-notify.inria.fr;

    # Institution SSL certificates
    ssl_certificate /etc/ssl/certs/inria-wildcard.pem;
    ssl_certificate_key /etc/ssl/private/inria-wildcard.key;

    location /coar-notify {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /coar-notify;
        rewrite ^/coar-notify(.*)$ $1 break;
    }
}
```

### Development with Self-Signed Cert

```nginx
server {
    listen 443 ssl;
    server_name localhost;

    # Self-signed certificate for development
    ssl_certificate /path/to/server.crt;
    ssl_certificate_key /path/to/server.key;

    # Skip certificate verification for dev
    ssl_verify_client off;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Health Check Configuration

Nginx can also perform health checks on the Flask application:

```nginx
upstream flask_app {
    server 127.0.0.1:5000;
    # Health check endpoint
    check interval=3000 rise=2 fall=5 timeout=1000 type=http;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx http_3xx;
}

server {
    # ... server configuration

    location / {
        proxy_pass http://flask_app;
        # ... proxy headers
    }
}
```

## Troubleshooting

### Common Issues

1. **Incorrect URLs in responses**: Ensure `X-Forwarded-*` headers are properly set
2. **Static files not loading**: Check alias paths and permissions
3. **API returning 404s**: Verify `X-Forwarded-Prefix` is set correctly for subdirectory deployments
4. **SSL certificate errors**: Ensure proper certificate chain and key permissions

### Debug Headers

Add this to your Nginx config to debug headers:

```nginx
location /debug {
    proxy_pass http://127.0.0.1:5000/health;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /coar;

    # Debug headers (remove in production)
    add_header X-Debug-Host "$host";
    add_header X-Debug-URI "$request_uri";
    add_header X-Debug-Proxy-Host "$proxy_host";
}
```

### Testing Configuration

Test your Nginx configuration before reloading:

```bash
# Test configuration syntax
nginx -t

# Reload configuration
nginx -s reload

# Check Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Test with curl

```bash
# Test basic proxy
curl -I http://localhost/health

# Test with headers
curl -H "X-Forwarded-Proto: https" \
     -H "X-Forwarded-Host: example.com" \
     -H "X-Forwarded-Prefix: /coar" \
     http://localhost:5000/health

# Test through Nginx
curl -I https://your-domain.com/coar/health
```

## Performance Optimization

### Caching

```nginx
# Cache static files
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    proxy_pass http://127.0.0.1:5000;
}

# Cache API responses (careful with auth)
location /api {
    proxy_pass http://127.0.0.1:5000;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

### Rate Limiting

```nginx
# Rate limit API endpoints
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://127.0.0.1:5000;
}
```

## Security Considerations

1. **SSL/TLS**: Always use HTTPS in production
2. **Headers**: Add security headers as shown in examples
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Access Control**: Consider IP whitelisting for admin endpoints
5. **Logging**: Enable access and error logging for monitoring

## Monitoring

Set up monitoring for your Nginx proxy:

```nginx
# Enable status page for monitoring
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

Monitor key metrics:
- Request rates and response times
- Error rates (4xx, 5xx responses)
- SSL certificate expiration
- Backend health check status