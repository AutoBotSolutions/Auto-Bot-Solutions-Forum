# Authentication System

## Overview

The authentication system handles user registration, login, logout, password reset, and email verification. It uses Flask-Login for session management and Werkzeug for secure password hashing.

## Components

### Models

**User Model** (`app/models.py`)
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(256))
    reset_token = db.Column(db.String(256))
    reset_token_expiration = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Forms

**LoginForm** (`app/auth/forms.py`)
- Username field
- Password field
- Remember me checkbox
- Submit button

**RegistrationForm** (`app/auth/forms.py`)
- Username field (min 4, max 64 characters)
- Email field with validation
- Password field (min 8 characters)
- Password confirmation field
- Submit button

**ResetPasswordRequestForm** (`app/auth/forms.py`)
- Email field
- Submit button

**ResetPasswordForm** (`app/auth/forms.py`)
- Password field (min 8 characters)
- Password confirmation field
- Submit button

### Routes

**Login Route** (`/auth/login`)
- Method: GET, POST
- Rate limit: 10 requests per minute
- Validates credentials
- Creates session with Flask-Login
- Supports "Remember Me" functionality

**Registration Route** (`/auth/register`)
- Method: GET, POST
- Rate limit: 3 requests per hour
- Creates new user account
- Generates verification token
- Sends verification email (token displayed for testing)
- Password is hashed before storage

**Logout Route** (`/auth/logout`)
- Destroys session
- Redirects to home page

**Password Reset Request** (`/auth/reset_password_request`)
- Method: GET, POST
- Rate limit: 3 requests per hour
- Generates secure reset token
- Token expires after 1 hour
- Sends email with reset link (token displayed for testing)

**Password Reset** (`/auth/reset_password/<token>`)
- Method: GET, POST
- Rate limit: 5 requests per hour
- Validates token and expiration
- Updates password
- Clears reset token

**Email Verification** (`/auth/verify/<token>`)
- Validates verification token
- Marks user as verified
- Clears verification token

**Resend Verification** (`/auth/resend_verification`)
- Method: GET, POST
- Rate limit: 3 requests per hour
- Regenerates verification token
- Sends verification email

## Security Features

### Password Hashing
- Uses Werkzeug's `generate_password_hash()`
- PBKDF2 with SHA-256 algorithm
- Salt is automatically generated
- Hashes are one-way (cannot be reversed)

### Session Management
- Flask-Login handles session creation
- Sessions are secure with HttpOnly flag
- Session timeout can be configured
- "Remember Me" extends session duration

### CSRF Protection
- All forms include CSRF tokens
- Tokens are validated on submission
- Prevents cross-site request forgery

### Rate Limiting
- Login: 10 requests per minute
- Registration: 3 requests per hour
- Password reset: 3 requests per hour
- Prevents brute force attacks

### Token Security
- Verification tokens: 32-byte URL-safe random strings
- Reset tokens: 32-byte URL-safe random strings
- Tokens expire after 1 hour
- Tokens are single-use

## Email Verification Flow

1. User registers account
2. System generates verification token
3. Token is stored in user record
4. Email sent with verification link (token displayed for testing)
5. User clicks verification link
6. System validates token
7. User marked as verified
8. Token cleared from database

## Password Reset Flow

1. User requests password reset
2. System validates email exists
3. Generates reset token with 1-hour expiration
4. Email sent with reset link (token displayed for testing)
5. User clicks reset link
6. System validates token and expiration
7. User enters new password
8. Password is hashed and updated
9. Token cleared from database

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for session encryption
- `SECURITY_PASSWORD_SALT`: Salt for password hashing (optional)

### Session Configuration
- Session lifetime: configurable via Flask settings
- Cookie security: HttpOnly, Secure flags (production)

## Best Practices

### For Users
- Use strong, unique passwords
- Enable email verification
- Use password reset when needed
- Keep email address current

### For Administrators
- Monitor failed login attempts
- Enforce password complexity
- Regular security audits
- Keep Flask secret key secure
- Use HTTPS in production

## Troubleshooting

### Login Issues
- **Problem**: "Invalid username or password"
  - Check credentials are correct
  - Verify email is verified
  - Ensure account exists

- **Problem**: Session expires too quickly
  - Check session configuration
  - Enable "Remember Me" option
  - Increase session timeout

### Registration Issues
- **Problem**: Email already registered
  - Use password reset instead
  - Contact admin for account recovery

- **Problem**: Username taken
  - Choose a different username
  - Username is case-insensitive

### Password Reset Issues
- **Problem**: Invalid or expired token
  - Request a new reset link
  - Token expires after 1 hour

- **Problem**: Email not received
  - Check spam folder
  - Verify email address is correct
  - Token is displayed in flash message for testing

## Future Enhancements

- Two-factor authentication (2FA)
- OAuth2 integration (Google, GitHub)
- Social login support
- Password strength meter
- Account lockout after failed attempts
- IP-based access control
- Session management UI for users
