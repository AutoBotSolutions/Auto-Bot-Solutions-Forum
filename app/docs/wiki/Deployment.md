# Deployment

## Docker Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

## Production Deployment

### Nginx Configuration
- Reverse proxy setup
- SSL/TLS termination
- Static file serving
- Gunicorn proxying

### Gunicorn Configuration
- Worker processes
- Worker threads
- Timeout settings
- Bind address

### SSL Setup
- Let's Encrypt certificates
- HTTPS redirect
- HSTS header
- Secure cipher suites

## See Also

See [DEPLOYMENT.md](../DEPLOYMENT.md) for detailed deployment instructions.
