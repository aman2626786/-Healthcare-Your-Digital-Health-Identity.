# Deployment Checklist

Use this checklist to ensure your deployment is complete and secure.

## Pre-Deployment

### Code Preparation
- [ ] All code is committed to version control
- [ ] Code has been tested locally
- [ ] No debug statements or test data in production code
- [ ] All sensitive data is removed from code

### Dependencies
- [ ] `requirements.txt` is up to date
- [ ] All dependencies are production-ready versions
- [ ] No development-only packages in requirements.txt

### Configuration
- [ ] `.env` file is created from `env.example`
- [ ] `SECRET_KEY` is set to a strong random value
- [ ] `FLASK_ENV=production` is set
- [ ] `FLASK_DEBUG=0` is set
- [ ] `FIREBASE_WEB_API_KEY` is configured (if using Firebase)
- [ ] Firebase service account JSON is in place (if using full Firebase features)

### Database
- [ ] Database schema is up to date
- [ ] Database migrations are tested
- [ ] Database backup strategy is in place
- [ ] Database file permissions are correct

### Files and Directories
- [ ] `backend/uploads/` directory exists and is writable
- [ ] `frontend/static/qr/` directory exists and is writable
- [ ] ML model files (`.pkl`) are in `backend/pkl/`
- [ ] All necessary directories have proper permissions

## Security

### Environment Variables
- [ ] `.env` file is NOT committed to version control
- [ ] `.env` is in `.gitignore`
- [ ] All secrets are in environment variables, not hardcoded
- [ ] Production secrets are different from development

### Firebase
- [ ] Firebase credentials are NOT committed to version control
- [ ] Firebase service account JSON is secured
- [ ] Firebase Web API Key is set in environment variables

### Application Security
- [ ] `SECRET_KEY` is strong and unique
- [ ] HTTPS is enabled (SSL/TLS certificate)
- [ ] Session cookies are secure (`SESSION_COOKIE_SECURE=True`)
- [ ] CORS is configured (if needed)
- [ ] File upload limits are set
- [ ] Input validation is in place

### Server Security
- [ ] Firewall rules are configured
- [ ] SSH keys are used (not passwords)
- [ ] Unnecessary ports are closed
- [ ] Regular security updates are scheduled

## Server Setup

### Python Environment
- [ ] Python 3.11+ is installed
- [ ] Virtual environment is created (if not using Docker)
- [ ] Dependencies are installed: `pip install -r requirements.txt`

### WSGI Server
- [ ] Gunicorn or uWSGI is installed
- [ ] WSGI configuration is tested
- [ ] Worker processes are configured appropriately
- [ ] Logging is configured

### Reverse Proxy (Nginx)
- [ ] Nginx is installed and configured
- [ ] SSL certificate is installed (Let's Encrypt)
- [ ] Static files are served efficiently
- [ ] Proxy settings are correct
- [ ] Nginx configuration is tested: `nginx -t`

### Process Management
- [ ] Systemd service is created (if applicable)
- [ ] Service auto-starts on boot
- [ ] Service is enabled: `systemctl enable swasthya-sampark`
- [ ] Service is running: `systemctl status swasthya-sampark`

## Docker Deployment (If Applicable)

### Docker Setup
- [ ] Docker is installed
- [ ] Docker Compose is installed (if using)
- [ ] Docker image builds successfully: `docker build -t swasthya-sampark .`
- [ ] Docker container runs: `docker-compose up -d`

### Docker Configuration
- [ ] Volumes are mounted correctly
- [ ] Environment variables are set in docker-compose.yml
- [ ] Ports are exposed correctly
- [ ] Health checks are configured

## Testing

### Functionality Tests
- [ ] User registration works
- [ ] User login works (password and OTP)
- [ ] Doctor login works
- [ ] Hospital login works
- [ ] Medical record creation works
- [ ] Emergency request works
- [ ] ML model predictions work
- [ ] File uploads work
- [ ] QR code generation works

### Performance Tests
- [ ] Application loads quickly
- [ ] Database queries are optimized
- [ ] Static files are cached
- [ ] No memory leaks

### Security Tests
- [ ] HTTPS redirect works
- [ ] Session management works
- [ ] File upload restrictions work
- [ ] SQL injection protection is in place
- [ ] XSS protection is in place

## Monitoring and Logging

### Logging
- [ ] Application logs are configured
- [ ] Error logs are captured
- [ ] Access logs are configured (if using Nginx)
- [ ] Log rotation is set up

### Monitoring
- [ ] Health check endpoint works: `/health`
- [ ] Monitoring tool is configured (optional)
- [ ] Alerting is set up (optional)
- [ ] Uptime monitoring is configured (optional)

## Backup and Recovery

### Database Backup
- [ ] Automated database backups are scheduled
- [ ] Backup restoration is tested
- [ ] Backup storage is secure

### File Backup
- [ ] Uploaded files are backed up
- [ ] QR codes are backed up (if needed)
- [ ] Backup restoration is tested

## Documentation

### Deployment Documentation
- [ ] Deployment process is documented
- [ ] Environment variables are documented
- [ ] Configuration changes are documented
- [ ] Troubleshooting guide is available

### User Documentation
- [ ] User guide is available (if applicable)
- [ ] API documentation is available (if applicable)

## Post-Deployment

### Verification
- [ ] Application is accessible via domain
- [ ] All features work as expected
- [ ] Performance is acceptable
- [ ] No errors in logs

### Maintenance
- [ ] Update schedule is planned
- [ ] Backup verification schedule is planned
- [ ] Security update schedule is planned
- [ ] Monitoring alerts are configured

## Rollback Plan

- [ ] Previous version is backed up
- [ ] Rollback procedure is documented
- [ ] Rollback is tested (if possible)

## Sign-Off

- [ ] All checklist items are completed
- [ ] Deployment is approved
- [ ] Team is notified
- [ ] Users are notified (if applicable)

---

**Deployment Date**: _______________

**Deployed By**: _______________

**Approved By**: _______________

**Notes**:
_________________________________________________
_________________________________________________
_________________________________________________

