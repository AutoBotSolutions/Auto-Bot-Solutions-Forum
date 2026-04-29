# Email System

## Overview

Email system handles verification emails and password reset. Currently, tokens are displayed in flash messages for testing. Production requires SMTP configuration.

## Email Types

### Verification Email
- Sent on registration
- Contains verification token
- Token expires in 1 hour
- Link to verification endpoint

### Password Reset Email
- Sent on password reset request
- Contains reset token
- Token expires in 1 hour
- Link to reset page

## Configuration (Future)

```python
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'user@example.com'
app.config['MAIL_PASSWORD'] = 'password'
```

## Testing

Tokens are currently displayed in flash messages for development and testing.
