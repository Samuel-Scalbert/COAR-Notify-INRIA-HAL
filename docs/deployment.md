# Production Deployment

[← Back to README](../README.md)

## Nginx Reverse Proxy

For production deployments, it's recommended to run the COAR Notify service behind an Nginx reverse proxy. This provides
SSL termination, proper header forwarding, and security headers.

For complete Nginx configuration examples, see the [Nginx Reverse Proxy Documentation](nginx.md).

### Quick Nginx Setup

1. **Install Nginx**:
   ```bash
   # Ubuntu/Debian
   sudo apt install nginx
   # CentOS/RHEL
   sudo yum install nginx
   ```

2. **Create Nginx configuration** (`/etc/nginx/sites-available/coar-notify`):
   ```nginx
   server {
       listen 443 ssl http2;
       server_name your-domain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location /coar {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header X-Forwarded-Prefix /coar;
           rewrite ^/coar(.*)$ $1 break;
       }
   }
   ```

3. **Enable the site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/coar-notify /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Docker Compose with Nginx

Add Nginx to your `docker-compose.yml`:

```yaml
services:
  app:
  # Remove direct port mapping
  # ports:
  #   - "5000:5000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app
```
