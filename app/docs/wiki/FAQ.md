# FAQ

## General Questions

### What is the AutoBot Solutions Forum?

A self-hosted discussion platform for GitHub repositories with a futuristic sci-fi theme.

### Is it free to use?

Yes, it's open-source under the MIT License.

### Do I need GitHub?

No, GitHub integration is optional.

### Can I customize the theme?

Yes, the CSS is fully customizable.

## Installation & Setup

### What are the system requirements?

Python 3.8+, PostgreSQL 12+, 2GB RAM minimum.

### Can I use SQLite instead of PostgreSQL?

For development, yes. For production, PostgreSQL is recommended.

### How do I reset the database?

```bash
docker-compose down -v
docker-compose up -d
docker-compose exec app python init_db.py
```

## Features

### Does it support Markdown?

Yes, with syntax highlighting and tables.

### Can users delete their own posts?

Yes, users can delete their own posts and comments.

### Is there a mobile app?

Not yet, but it's responsive and works on mobile browsers.

### Can I attach files to posts?

Yes, images, PDFs, and text files are supported.

## Security

### Is the forum secure?

Yes, with CSRF protection, rate limiting, password hashing, and more.

### Should I use HTTPS?

Absolutely, HTTPS is essential for security.

### How are passwords stored?

Hashed with PBKDF2 and SHA-256.

## Authentication

### I forgot my password, what do I do?

Use the password reset feature on the login page.

### Can I change my username?

Yes, via your profile settings.

### Why is email verification required?

To prevent fake accounts and ensure valid email addresses.

## GitHub Integration

### Do I need a GitHub token?

For private organizations or to avoid rate limits, yes.

### How often are repositories synced?

Manually via the admin panel or API endpoint.

### Can I sync from multiple organizations?

Currently one organization, but can be modified.

## Admin

### How do I become an admin?

Admins are created during initialization or promoted by existing admins.

### Can admins see private messages?

Currently no, but audit logging is planned.

### How do I delete a user?

Via the admin panel. This cascades to all user data.

## Troubleshooting

### CSS not loading?

This was fixed in the latest version. Clear your browser cache.

### Database connection errors?

Check PostgreSQL is running and DATABASE_URL is correct.

### Emails not sending?

Tokens are displayed in flash messages for testing. Configure SMTP for production.

## Development

### How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md).

### What's the tech stack?

Flask, SQLAlchemy, PostgreSQL, Jinja2, Docker.

### How do I run tests?

```bash
pytest
```

## Support

### Where can I get help?

- Check documentation in docs/
- Search GitHub issues
- Join Discord community
- Email support@autobotsolutions.com

### Is professional support available?

Yes, contact enterprise@autobotsolutions.com.
