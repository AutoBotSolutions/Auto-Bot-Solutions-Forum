# AutoBot Solutions Forum - Wiki

Welcome to the AutoBot Solutions Forum wiki. This comprehensive documentation covers all systems, components, and features of the forum application.

## Quick Links

### Core Systems
- [Authentication System](Authentication-System.md)
- [Forum System](Forum-System.md)
- [User System](User-System.md)
- [Admin System](Admin-System.md)
- [Database System](Database-System.md)

### Features
- [Notification System](Notification-System.md)
- [Messaging System](Messaging-System.md)
- [GitHub Integration](GitHub-Integration.md)
- [File Upload System](File-Upload-System.md)
- [Category/Tag System](Category-Tag-System.md)
- [Bookmarking System](Bookmarking-System.md)
- [Voting System](Voting-System.md)
- [Badge/Achievement System](Badge-Achievement-System.md)

### Technical
- [API System](API-System.md)
- [Security System](Security-System.md)
- [Rate Limiting](Rate-Limiting.md)
- [Markdown Processing](Markdown-Processing.md)
- [Email System](Email-System.md)

### Getting Started
- [Installation Guide](Installation-Guide.md)
- [Configuration](Configuration.md)
- [Deployment](Deployment.md)
- [Troubleshooting](Troubleshooting.md)

## Overview

The AutoBot Solutions Forum is a self-hosted discussion platform built with Flask, designed for GitHub repository discussions. It features a futuristic sci-fi theme and comprehensive functionality including user authentication, posts, comments, voting, notifications, private messaging, and admin management.

## Technology Stack

- **Backend**: Flask 3.0.0, SQLAlchemy, PostgreSQL
- **Frontend**: Jinja2 templates, custom CSS
- **Authentication**: Flask-Login, secure password hashing
- **Deployment**: Docker, Nginx, Gunicorn
- **Security**: CSRF protection, rate limiting, input validation

## System Architecture

The forum follows a modular architecture with Flask blueprints for each major system:
- `auth` - Authentication and user management
- `forum` - Forum posts, comments, voting
- `admin` - Administrative functions
- `user` - User profiles
- `notification` - Notification system
- `message` - Private messaging
- `api` - RESTful API
- `main` - Main pages and navigation

## Database Schema

The database uses PostgreSQL with the following core tables:
- Users
- Repositories
- Categories
- Posts
- Comments
- Votes
- Notifications
- Messages
- Bookmarks
- Badges

See [Database System](Database-System.md) for detailed schema information.

## Security

The forum implements multiple security measures:
- Password hashing with Werkzeug
- CSRF protection on all forms
- Rate limiting on sensitive endpoints
- SQL injection prevention
- XSS protection via auto-escaping
- Email verification tokens
- Password reset with expiration

See [Security System](Security-System.md) for detailed security information.

## Contributing to the Wiki

To improve the wiki documentation:
1. Fork the repository
2. Create a new wiki page or edit an existing one
3. Follow the wiki formatting guidelines
4. Submit a pull request

## Support

For questions or issues:
- Check the main documentation in the docs/ folder
- Open an issue on GitHub
- Join our Discord community
- Email support@autobotsolutions.com

## Recent Changes

- Added private messaging system
- Implemented notification system
- Added file upload support
- Created user badges/achievements
- Enhanced security with rate limiting
- Fixed CSS loading issues

## Roadmap

Upcoming features:
- Real-time notifications via WebSockets
- Advanced search with Elasticsearch
- API authentication (JWT/OAuth2)
- Two-factor authentication
- Email notification system
- Mobile app development

---

**Last Updated**: 2024-01-15
