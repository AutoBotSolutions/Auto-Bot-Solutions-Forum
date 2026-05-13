# Troubleshooting Guide for New Features

## Overview

This guide provides comprehensive troubleshooting steps for the new authentication system features, including email integration and two-factor authentication (2FA) implementation.

## Table of Contents

1. [Email Integration Issues](#email-integration-issues)
2. [Two-Factor Authentication Issues](#two-factor-authentication-issues)
3. [Authentication Flow Issues](#authentication-flow-issues)
4. [Security Configuration Issues](#security-configuration-issues)
5. [Performance Issues](#performance-issues)
6. [Debug Commands](#debug-commands)
7. [Common Error Messages](#common-error-messages)

## Email Integration Issues

### Email Not Sending

#### Symptoms
- Users don't receive verification emails
- Password reset emails not delivered
- Welcome emails not sent
- Email queue shows growing backlog

#### Troubleshooting Steps

1. **Check SMTP Configuration**
   ```bash
   python -c "
   from app import create_app
   app = create_app()
   with app.app_context():
       print('SMTP Server:', app.config.get('MAIL_SERVER'))
       print('SMTP Port:', app.config.get('MAIL_PORT'))
       print('Use TLS:', app.config.get('MAIL_USE_TLS'))
       print('Username:', app.config.get('MAIL_USERNAME'))
       print('Password configured:', bool(app.config.get('MAIL_PASSWORD')))
   "
   ```

2. **Test SMTP Connection**
   ```bash
   python -c "
   import smtplib
   from app import create_app
   app = create_app()
   with app.app_context():
       server = smtplib.SMTP(app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT'))
       server.starttls()
       server.login(app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD'))
       print('SMTP connection successful')
       server.quit()
   "
   ```

3. **Check Email Queue Status**
   ```bash
   python -c "
   from app import create_app
   from app.email.queue import EmailQueueManager
   app = create_app()
   with app.app_context():
       stats = EmailQueueManager.get_queue_statistics()
       print('Queue Status:', stats)
   "
   ```

4. **Verify Redis Connection**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

5. **Check Email Templates**
   ```bash
   python -c "
   from app import create_app
   from app.email.queue import EmailQueueManager
   app = create_app()
   with app.app_context():
       try:
           preview = EmailQueueManager.preview_email('verification', {
               'user': {'username': 'test', 'email': 'test@example.com'},
               'verification_url': 'http://localhost:5000/verify/test'
           })
           print('Template rendered successfully, length:', len(preview))
       except Exception as e:
           print('Template error:', str(e))
   "
   ```

#### Common Solutions

- **Gmail Issues**: Use App Password instead of regular password
- **Firewall Issues**: Open port 587 for SMTP
- **Authentication Issues**: Verify email credentials
- **Queue Issues**: Restart Redis and application

### Email Template Rendering Issues

#### Symptoms
- Blank emails received
- Missing variables in emails
- Template syntax errors
- HTML rendering problems

#### Troubleshooting Steps

1. **Test Template Rendering**
   ```bash
   python -c "
   from app import create_app
   from app.email.queue import EmailQueueManager
   app = create_app()
   with app.app_context():
       templates = ['verification', 'password_reset', 'welcome']
       for template in templates:
           try:
               preview = EmailQueueManager.preview_email(template, {
                   'user': {'username': 'test', 'email': 'test@example.com'},
                   'verification_url': 'http://localhost:5000/verify/test',
                   'reset_url': 'http://localhost:5000/reset/test'
               })
               print(f'{template}: OK ({len(preview)} chars)')
           except Exception as e:
               print(f'{template}: ERROR - {str(e)}')
   "
   ```

2. **Check Template Variables**
   ```bash
   python -c "
   from app import create_app
   from jinja2 import Template
   app = create_app()
   with app.app_context():
       # Test template syntax
       template_str = '<h1>Hello {{ user.username }}</h1>'
       template = Template(template_str)
       result = template.render(user={'username': 'test'})
       print('Template test:', result)
   "
   ```

#### Common Solutions

- **Missing Variables**: Ensure all required variables are passed
- **Syntax Errors**: Check Jinja2 template syntax
- **File Paths**: Verify template file locations
- **Encoding Issues**: Check UTF-8 encoding

## Two-Factor Authentication Issues

### 2FA Setup Problems

#### Symptoms
- QR code not displaying
- TOTP secret not generating
- Backup codes not working
- 2FA setup failing

#### Troubleshooting Steps

1. **Test TOTP Generation**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor import two_fa_service
   app = create_app()
   with app.app_context():
       secret = two_fa_service.generate_totp_secret()
       print('TOTP Secret:', secret)
       print('Secret length:', len(secret))
   "
   ```

2. **Test QR Code Generation**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor import two_fa_service
   app = create_app()
   with app.app_context():
       try:
           qr_code = two_fa_service.generate_qr_code('test@example.com', 'JBSWY3DPEHPK3PXP')
           print('QR Code Generated:', len(qr_code), 'bytes')
           print('QR Code starts with:', qr_code[:50])
       except Exception as e:
           print('QR Code Error:', str(e))
   "
   ```

3. **Test TOTP Verification**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor import two_fa_service, verify_2fa_token
   import pyotp
   app = create_app()
   with app.app_context():
       secret = 'JBSWY3DPEHPK3PXP'
       totp = pyotp.TOTP(secret)
       token = totp.now()
       print('Generated Token:', token)
       print('Verification Result:', verify_2fa_token(secret, token))
   "
   ```

4. **Check 2FA Configuration**
   ```bash
   python -c "
   from app import create_app
   app = create_app()
   with app.app_context():
       print('2FA Enabled:', app.config.get('TWO_FA_ENABLED'))
       print('2FA Issuer:', app.config.get('TWO_FA_ISSUER'))
       print('Encryption Key Configured:', bool(app.config.get('TWO_FA_ENCRYPTION_KEY')))
   "
   ```

#### Common Solutions

- **Time Sync**: Ensure server time is synchronized
- **Encryption Key**: Generate and configure encryption key
- **QR Code Issues**: Check qrcode library installation
- **TOTP Issues**: Verify pyotp library installation

### 2FA Verification Issues

#### Symptoms
- TOTP tokens not verifying
- Backup codes not working
- Device remembering not working
- 2FA loop not completing

#### Troubleshooting Steps

1. **Test TOTP Verification with Time Window**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor import verify_2fa_token
   import pyotp
   import time
   app = create_app()
   with app.app_context():
       secret = 'JBSWY3DPEHPK3PXP'
       totp = pyotp.TOTP(secret)
       
       # Test current token
       current_token = totp.now()
       print('Current Token:', current_token)
       print('Current Time Valid:', verify_2fa_token(secret, current_token))
       
       # Test with time window
       print('With Time Window:', verify_2fa_token(secret, current_token, valid_window=1))
   "
   ```

2. **Test Backup Code System**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor import two_fa_service
   app = create_app()
   with app.app_context():
       # Generate backup codes
       codes = two_fa_service.generate_backup_codes(5)
       print('Generated Codes:', codes)
       
       # Test hashing and verification
       code = codes[0]
       hashed = two_fa_service.hash_backup_code(code)
       print('Hashed Code:', hashed)
       print('Verification Result:', two_fa_service.verify_backup_code(hashed, code))
   "
   ```

3. **Check User 2FA Status**
   ```bash
   python -c "
   from app import create_app
   from app.models import User
   app = create_app()
   with app.app_context():
       user = User.query.filter_by(username='admin').first()
       if user:
           print('User 2FA Enabled:', user.is_2fa_enabled)
           print('TOTP Secret Set:', bool(user.totp_secret))
           print('Backup Codes Set:', bool(user.backup_codes_hash))
           print('Unused Backup Codes:', user.get_unused_backup_codes_count())
       else:
           print('User not found')
   "
   ```

#### Common Solutions

- **Time Drift**: Use valid_window parameter for time tolerance
- **Backup Codes**: Regenerate backup codes if corrupted
- **Device Remembering**: Check cookie configuration
- **Session Issues**: Verify session configuration

## Authentication Flow Issues

### Login Problems

#### Symptoms
- Login not working after 2FA implementation
- Users stuck in 2FA verification loop
- Session not persisting
- Redirect loops during login

#### Troubleshooting Steps

1. **Test Login Flow**
   ```bash
   python -c "
   from app import create_app
   from app.models import User
   app = create_app()
   with app.app_context():
       user = User.query.filter_by(username='admin').first()
       if user:
           print('User exists:', bool(user))
           print('User can login:', user.can_login())
           print('User is active:', user.is_active)
           print('User is verified:', user.is_verified)
           print('User has 2FA:', user.is_2fa_enabled)
           print('Password check:', user.check_password('admin123'))
       else:
           print('User not found')
   "
   ```

2. **Check Session Configuration**
   ```bash
   python -c "
   from app import create_app
   app = create_app()
   with app.app_context():
       print('Session Cookie Secure:', app.config.get('SESSION_COOKIE_SECURE'))
       print('Session Cookie HttpOnly:', app.config.get('SESSION_COOKIE_HTTPONLY'))
       print('Session Cookie SameSite:', app.config.get('SESSION_COOKIE_SAMESITE'))
       print('Permanent Session Lifetime:', app.config.get('PERMANENT_SESSION_LIFETIME'))
   "
   ```

3. **Test 2FA Requirement Check**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor_routes import requires_2fa_verification
   from app.models import User
   app = create_app()
   with app.app_context():
       user = User.query.filter_by(username='admin').first()
       if user:
           print('2FA Required:', requires_2fa_verification(user))
       else:
           print('User not found')
   "
   ```

#### Common Solutions

- **Session Issues**: Check session configuration and cookies
- **2FA Integration**: Verify 2FA completion endpoint
- **User Model Issues**: Check user.can_login() method
- **Redirect Issues**: Verify URL configuration

### Registration Issues

#### Symptoms
- Registration not working
- Email verification not sent
- User not created properly
- 2FA setup failing after registration

#### Troubleshooting Steps

1. **Test Registration Flow**
   ```bash
   python -c "
   from app import create_app
   from app.models import User
   app = create_app()
   with app.app_context():
       # Test user creation
       user = User(
           username='testuser',
           email='test@example.com',
           is_active=True,
           is_verified=False
       )
       user.set_password('testpass123')
       print('User created successfully')
       print('User can login:', user.can_login())
       print('User needs verification:', not user.is_verified)
   "
   ```

2. **Test Email Verification Token**
   ```bash
   python -c "
   import secrets
   from app import create_app
   app = create_app()
   with app.app_context():
       token = secrets.token_urlsafe(32)
       print('Generated Token:', token)
       print('Token Length:', len(token))
   "
   ```

#### Common Solutions

- **User Creation**: Ensure all required fields are set
- **Email Verification**: Check email configuration
- **Password Issues**: Verify password hashing
- **Database Issues**: Check database connection

## Security Configuration Issues

### Encryption Key Problems

#### Symptoms
- 2FA secrets not encrypting
- Decryption errors
- Key generation failures
- Configuration errors

#### Troubleshooting Steps

1. **Test Encryption Key Generation**
   ```bash
   python -c "
   from cryptography.fernet import Fernet
   key = Fernet.generate_key()
   print('Generated Key:', key.decode())
   print('Key Length:', len(key))
   
   # Test encryption/decryption
   cipher = Fernet(key)
   test_data = b'secret message'
   encrypted = cipher.encrypt(test_data)
   decrypted = cipher.decrypt(encrypted)
   print('Encryption Test:', decrypted.decode() == test_data.decode())
   "
   ```

2. **Check 2FA Service Initialization**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor import two_fa_service
   app = create_app()
   with app.app_context():
       try:
           secret = two_fa_service.generate_totp_secret()
           encrypted = two_fa_service.encrypt_data(secret)
           decrypted = two_fa_service.decrypt_data(encrypted)
           print('2FA Service Working:', secret == decrypted)
       except Exception as e:
           print('2FA Service Error:', str(e))
   "
   ```

#### Common Solutions

- **Key Generation**: Generate new encryption key
- **Key Storage**: Store key securely in environment variable
- **Service Initialization**: Check service initialization
- **Library Issues**: Verify cryptography library installation

### Rate Limiting Issues

#### Symptoms
- Users getting rate limited too quickly
- Rate limiting not working
- Login attempts not being tracked
- Brute force protection not working

#### Troubleshooting Steps

1. **Test Rate Limiting Configuration**
   ```bash
   python -c "
   from app import create_app
   app = create_app()
   with app.app_context():
       from flask_limiter import Limiter
       limiter = app.extensions.get('limiter')
       print('Limiter configured:', bool(limiter))
       print('Default limits:', app.config.get('RATELIMIT_DEFAULT'))
   "
   ```

2. **Check Failed Login Tracking**
   ```bash
   python -c "
   from app import create_app
   from app.models import User
   app = create_app()
   with app.app_context():
       user = User.query.filter_by(username='admin').first()
       if user:
           print('Failed Login Attempts:', user.failed_login_attempts)
           print('Account Locked:', user.is_account_locked())
           print('Locked Until:', user.locked_until)
       else:
           print('User not found')
   "
   ```

#### Common Solutions

- **Configuration**: Check rate limiting configuration
- **Storage**: Verify Redis connection for rate limiting
- **User Model**: Check failed login tracking
- **Limits**: Adjust rate limiting limits

## Performance Issues

### Email Queue Performance

#### Symptoms
- Emails not sending promptly
- Queue backlog growing
- High memory usage
- Slow email processing

#### Troubleshooting Steps

1. **Check Queue Performance**
   ```bash
   python -c "
   from app import create_app
   from app.email.queue import EmailQueueManager
   import time
   app = create_app()
   with app.app_context():
       start_time = time.time()
       stats = EmailQueueManager.get_queue_statistics()
       end_time = time.time()
       print('Queue Stats:', stats)
       print('Query Time:', end_time - start_time)
   "
   ```

2. **Test Email Processing Speed**
   ```bash
   python -c "
   from app import create_app
   from app.email.service import email_service
   import time
   app = create_app()
   with app.app_context():
       start_time = time.time()
       # Test email processing
       processed = email_service.process_queue()
       end_time = time.time()
       print('Processed Emails:', processed)
       print('Processing Time:', end_time - start_time)
   "
   ```

#### Common Solutions

- **Redis Performance**: Optimize Redis configuration
- **Queue Processing**: Adjust queue processing frequency
- **Batch Processing**: Implement batch email processing
- **Memory Usage**: Optimize email template caching

### 2FA Performance

#### Symptoms
- Slow 2FA verification
- QR code generation taking too long
- TOTP verification delays
- High CPU usage during 2FA

#### Troubleshooting Steps

1. **Test 2FA Performance**
   ```bash
   python -c "
   from app import create_app
   from app.auth.two_factor import two_fa_service
   import time
   app = create_app()
   with app.app_context():
       # Test TOTP generation
       start_time = time.time()
       secret = two_fa_service.generate_totp_secret()
       end_time = time.time()
       print('TOTP Generation Time:', end_time - start_time)
       
       # Test QR code generation
       start_time = time.time()
       qr_code = two_fa_service.generate_qr_code('test@example.com', secret)
       end_time = time.time()
       print('QR Code Generation Time:', end_time - start_time)
   "
   ```

#### Common Solutions

- **Caching**: Cache QR codes and TOTP secrets
- **Optimization**: Optimize encryption/decryption
- **Library Performance**: Check library versions
- **Database**: Optimize database queries

## Debug Commands

### Comprehensive System Check

```bash
#!/bin/bash
echo "=== AutoBot Solutions Forum Debug Check ==="
echo ""

# Check Python Environment
echo "1. Python Environment:"
python --version
pip list | grep -E "(Flask|redis|pyotp|cryptography)"

# Check Application
echo ""
echo "2. Application Check:"
python -c "
from app import create_app
try:
    app = create_app()
    print('✅ Application created successfully')
except Exception as e:
    print('❌ Application creation failed:', str(e))
"

# Check Database
echo ""
echo "3. Database Check:"
python -c "
from app import create_app
from app.models import User
app = create_app()
with app.app_context():
    try:
        count = User.query.count()
        print(f'✅ Database connected: {count} users')
    except Exception as e:
        print('❌ Database connection failed:', str(e))
"

# Check Redis
echo ""
echo "4. Redis Check:"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis connected"
    else
        echo "❌ Redis not responding"
    fi
else
    echo "❌ Redis CLI not installed"
fi

# Check Email System
echo ""
echo "5. Email System Check:"
python -c "
from app import create_app
from app.email.queue import EmailQueueManager
app = create_app()
with app.app_context():
    try:
        stats = EmailQueueManager.get_queue_statistics()
        print('✅ Email system working')
        print('Queue Status:', stats)
    except Exception as e:
        print('❌ Email system failed:', str(e))
"

# Check 2FA System
echo ""
echo "6. 2FA System Check:"
python -c "
from app import create_app
from app.auth.two_factor import two_fa_service
app = create_app()
with app.app_context():
    try:
        secret = two_fa_service.generate_totp_secret()
        print('✅ 2FA system working')
        print('Generated secret:', secret[:10] + '...')
    except Exception as e:
        print('❌ 2FA system failed:', str(e))
"

echo ""
echo "=== Debug Check Complete ==="
```

### Email System Debug

```bash
#!/bin/bash
echo "=== Email System Debug ==="
echo ""

# Test SMTP Connection
echo "1. SMTP Connection Test:"
python -c "
from app import create_app
import smtplib
app = create_app()
with app.app_context():
    try:
        server = smtplib.SMTP(app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT'))
        server.starttls()
        server.login(app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD'))
        print('✅ SMTP connection successful')
        server.quit()
    except Exception as e:
        print('❌ SMTP connection failed:', str(e))
"

# Test Email Templates
echo ""
echo "2. Email Templates Test:"
python -c "
from app import create_app
from app.email.queue import EmailQueueManager
app = create_app()
with app.app_context():
    templates = ['verification', 'password_reset', 'welcome']
    for template in templates:
        try:
            preview = EmailQueueManager.preview_email(template, {
                'user': {'username': 'test', 'email': 'test@example.com'},
                'verification_url': 'http://localhost:5000/verify/test',
                'reset_url': 'http://localhost:5000/reset/test',
                'login_url': 'http://localhost:5000/login'
            })
            print(f'✅ {template}: {len(preview)} chars')
        except Exception as e:
            print(f'❌ {template}: {str(e)}')
"

# Test Email Queue
echo ""
echo "3. Email Queue Test:"
python -c "
from app import create_app
from app.email.queue import EmailQueueManager
app = create_app()
with app.app_context():
    try:
        stats = EmailQueueManager.get_queue_statistics()
        print('✅ Queue status retrieved')
        print('Queue stats:', stats)
    except Exception as e:
        print('❌ Queue status failed:', str(e))
"

echo ""
echo "=== Email System Debug Complete ==="
```

### 2FA System Debug

```bash
#!/bin/bash
echo "=== 2FA System Debug ==="
echo ""

# Test TOTP Generation
echo "1. TOTP Generation Test:"
python -c "
from app import create_app
from app.auth.two_factor import two_fa_service
app = create_app()
with app.app_context():
    try:
        secret = two_fa_service.generate_totp_secret()
        print('✅ TOTP secret generated:', secret)
        print('Secret length:', len(secret))
    except Exception as e:
        print('❌ TOTP generation failed:', str(e))
"

# Test QR Code Generation
echo ""
echo "2. QR Code Generation Test:"
python -c "
from app import create_app
from app.auth.two_factor import two_fa_service
app = create_app()
with app.app_context():
    try:
        qr_code = two_fa_service.generate_qr_code('test@example.com', 'JBSWY3DPEHPK3PXP')
        print('✅ QR code generated:', len(qr_code), 'bytes')
        print('QR code type:', type(qr_code))
    except Exception as e:
        print('❌ QR code generation failed:', str(e))
"

# Test TOTP Verification
echo ""
echo "3. TOTP Verification Test:"
python -c "
from app import create_app
from app.auth.two_factor import verify_2fa_token
import pyotp
app = create_app()
with app.app_context():
    try:
        secret = 'JBSWY3DPEHPK3PXP'
        totp = pyotp.TOTP(secret)
        token = totp.now()
        result = verify_2fa_token(secret, token)
        print('✅ TOTP verification:', result)
        print('Token:', token)
    except Exception as e:
        print('❌ TOTP verification failed:', str(e))
"

# Test Backup Codes
echo ""
echo "4. Backup Codes Test:"
python -c "
from app import create_app
from app.auth.two_factor import two_fa_service
app = create_app()
with app.app_context():
    try:
        codes = two_fa_service.generate_backup_codes(5)
        print('✅ Backup codes generated:', codes)
        
        # Test hashing and verification
        code = codes[0]
        hashed = two_fa_service.hash_backup_code(code)
        result = two_fa_service.verify_backup_code(hashed, code)
        print('✅ Backup code verification:', result)
    except Exception as e:
        print('❌ Backup codes failed:', str(e))
"

# Test Encryption
echo ""
echo "5. Encryption Test:"
python -c "
from app import create_app
from app.auth.two_factor import two_fa_service
app = create_app()
with app.app_context():
    try:
        test_data = 'secret message'
        encrypted = two_fa_service.encrypt_data(test_data)
        decrypted = two_fa_service.decrypt_data(encrypted)
        result = test_data == decrypted
        print('✅ Encryption test:', result)
    except Exception as e:
        print('❌ Encryption test failed:', str(e))
"

echo ""
echo "=== 2FA System Debug Complete ==="
```

## Common Error Messages

### Email System Errors

#### "Failed to connect to Redis for email queue"
**Cause**: Redis not running or not configured
**Solution**: Start Redis server and check configuration

#### "SMTP send failed: Authentication failed"
**Cause**: Invalid email credentials
**Solution**: Verify email username and password

#### "Template not found: verification"
**Cause**: Missing email template file
**Solution**: Check template file paths

### 2FA System Errors

#### "No TWO_FA_ENCRYPTION_KEY configured"
**Cause**: Missing encryption key in configuration
**Solution**: Generate and configure encryption key

#### "Invalid authentication code"
**Cause**: TOTP token expired or incorrect
**Solution**: Check time synchronization and token validity

#### "Backup code verification failed"
**Cause**: Invalid or used backup code
**Solution**: Regenerate backup codes or use unused code

### Authentication Errors

#### "User account is locked"
**Cause**: Too many failed login attempts
**Solution**: Wait for lockout to expire or reset manually

#### "2FA verification required"
**Cause**: User has 2FA enabled
**Solution**: Complete 2FA verification process

#### "Session expired"
**Cause**: Session timeout or invalid session
**Solution**: Login again

## Support Resources

### Documentation
- [Authentication System Documentation](AUTHENTICATION_SYSTEM.md)
- [Email Integration Documentation](EMAIL_INTEGRATION.md)
- [2FA Implementation Documentation](TWO_FACTOR_AUTHENTICATION.md)
- [Security Implementation Guide](SECURITY_IMPLEMENTATION.md)

### Community Support
- GitHub Issues: Report bugs and request features
- Forums: Get help from community members
- Wiki: Find additional documentation and guides

### Emergency Support
For critical security issues:
1. Check system logs
2. Review security configuration
3. Contact development team
4. Review incident response procedures

---

**Version**: 2.0.0  
**Last Updated**: May 11, 2026  
**Status**: Production Ready
