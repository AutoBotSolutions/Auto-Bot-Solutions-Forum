# Frequently Asked Questions

## General Questions

### What is the AutoBot Solutions Forum?

The AutoBot Solutions Forum is a self-hosted discussion platform designed specifically for GitHub repositories. It allows developers and users to discuss code, report issues, share ideas, and collaborate on projects within a futuristic sci-fi themed interface.

### Is it free to use?

Yes! The forum is open-source and released under the MIT License. You can use, modify, and distribute it freely.

### Do I need to use GitHub?

No, GitHub integration is optional. The forum works perfectly as a standalone discussion platform. However, if you want to sync repositories from GitHub, you'll need a GitHub account and API token.

### Can I use this for my own organization?

Absolutely! The forum is designed to be customizable. You can change the organization name, branding, and features to match your needs.

## Installation & Setup

### What are the system requirements?

- Python 3.8 or higher
- PostgreSQL 12 or higher
- 2GB RAM minimum (4GB recommended)
- 10GB disk space minimum
- Docker and Docker Compose (for containerized deployment)

### Can I install without Docker?

Yes, but Docker is recommended for easier deployment. You can install directly by following the manual setup instructions in DEPLOYMENT.md.

### How do I migrate from another forum?

Currently, there's no automated migration tool. You would need to manually export/import data or write a custom migration script. We're planning to add migration tools in future releases.

### Can I use SQLite instead of PostgreSQL?

For development and testing, SQLite works fine. However, for production, PostgreSQL is strongly recommended for better performance, concurrency, and reliability.

## Features

### What features does the forum have?

- User authentication with email verification
- Password reset functionality
- Posts and comments with Markdown support
- Upvote/downvote system
- Search functionality
- Categories/tags
- Bookmarks
- Private messaging
- Notifications
- User profiles
- Badges/achievements
- File uploads
- GitHub repository integration
- Admin panel
- RESTful API

### Is there a mobile app?

Not yet, but the forum is fully responsive and works well on mobile browsers. A native mobile app is planned for future development.

### Can users delete their own posts?

Yes, users can delete their own posts and comments. Admins can delete any content.

### Is there a rich text editor?

The forum supports Markdown, which allows for rich text formatting including code blocks, tables, links, and more. A WYSIWYG editor is planned for future releases.

### Can I attach files to posts?

Yes, users can attach files to their posts. Supported file types include images (PNG, JPG, GIF), PDF, and text files.

### How does the voting system work?

Users can upvote or downvote posts and comments. The total score is displayed next to each item. Users can change their vote or remove it entirely.

## Security

### Is the forum secure?

Yes, the forum implements multiple security measures:
- CSRF protection on all forms
- Rate limiting to prevent abuse
- Secure password hashing
- SQL injection prevention
- XSS protection
- Email verification
- Password reset with expiring tokens

### Should I use HTTPS in production?

Absolutely! HTTPS is essential for security. The Nginx configuration includes SSL setup instructions. You'll need a valid SSL certificate from a provider like Let's Encrypt.

### How are passwords stored?

Passwords are hashed using Werkzeug's secure password hashing (PBKDF2 with SHA-256). The plain text passwords are never stored.

### What happens if I forget my password?

You can use the password reset feature. A secure token will be generated and sent to your registered email address. The token expires after 1 hour.

## Customization

### Can I change the theme?

Yes! The theme is fully customizable through CSS. All colors and styles are defined in `app/static/css/style.css` using CSS custom properties (variables).

### Can I add custom fields to posts?

Yes, you would need to modify the database model and the corresponding forms and templates. See the ARCHITECTURE.md documentation for guidance.

### Can I integrate with other services?

The forum has a RESTful API for integration. You can also add custom integrations by modifying the code or creating new modules.

### Can I change the rate limits?

Yes, rate limits are configurable in the route decorators. See the forum routes file for current limits and adjust as needed.

## Performance

### How many users can the forum support?

With proper scaling (PostgreSQL, Nginx, Redis), the forum can support thousands of concurrent users. See ARCHITECTURE.md for scaling strategies.

### Is caching enabled?

Static files are cached by Nginx. For application-level caching, you can integrate Redis for session storage and query caching.

### How do I optimize performance?

- Use PostgreSQL instead of SQLite
- Enable Nginx gzip compression
- Use Redis for caching
- Optimize database queries
- Use a CDN for static assets
- Enable Gunicorn workers

## GitHub Integration

### What GitHub features are supported?

- Automatic repository syncing from an organization
- Repository-linked discussions
- Display of repository metadata (stars, language, etc.)
- Manual sync via API endpoint

### Do I need a GitHub token?

For syncing repositories from a private organization or to avoid rate limits, yes. For public organizations, you can sync without a token, but you'll be subject to GitHub's rate limits.

### How often are repositories synced?

Repositories are synced manually via the API endpoint or through the admin panel. Automatic periodic syncing can be added as a scheduled task.

### Can I sync from multiple organizations?

Currently, the forum is configured for a single organization. You could modify the code to support multiple organizations.

## Admin Panel

### What can admins do?

- Manage users (delete, promote to admin)
- Manage posts (delete)
- Manage comments (delete)
- Manage repositories (sync, delete)
- Manage categories (create, delete)
- Manage badges (create, delete, assign to users)
- View dashboard statistics

### How do I create an admin user?

Admin users are created through the database initialization script (`init_db.py`) or by promoting existing users in the admin panel.

### Can I have multiple admins?

Yes, you can have as many admins as you need. Each admin has full access to the admin panel.

## API

### Is there a REST API?

Yes, the forum provides a RESTful API for programmatic access. See API.md for documentation.

### Does the API require authentication?

Currently, read operations don't require authentication. Write operations should be protected in production. JWT authentication is planned for future releases.

### What API endpoints are available?

- `GET /api/repositories` - List repositories
- `GET /api/posts` - List posts
- `GET /api/posts/<id>` - Get single post
- `POST /api/sync-repositories` - Sync repositories

See API.md for full documentation.

## Troubleshooting

### CSS styles not loading

This was fixed in the latest version. Ensure you have the latest code and clear your browser cache.

### Database connection errors

Check that:
- PostgreSQL is running
- Database credentials in `.env` are correct
- The database exists and is accessible

### Emails not sending

Email functionality is configured but not fully implemented in the current version. Tokens are displayed in flash messages for testing. To enable actual email sending, you'll need to configure SMTP settings.

### File uploads not working

Check that:
- The `app/static/uploads` directory exists and is writable
- The file type is allowed (PNG, JPG, JPEG, GIF, PDF, TXT, MD)
- The file size is within limits

## Development

### How can I contribute?

See CONTRIBUTING.md for detailed guidelines on contributing to the project.

### What's the tech stack?

- Backend: Flask (Python)
- Database: PostgreSQL
- ORM: SQLAlchemy
- Frontend: Jinja2 templates with custom CSS
- Deployment: Docker, Nginx, Gunicorn

### How do I run tests?

```bash
pytest
```

### What's the development workflow?

See CONTRIBUTING.md for the complete development workflow, including branching strategy, commit conventions, and pull request process.

## License

### What license is the forum released under?

MIT License. See LICENSE.md for the full text.

### Can I use this commercially?

Yes, the MIT License allows commercial use, modification, and distribution.

### Do I need to attribute the original project?

The MIT License requires you to include the original copyright notice and license in any substantial derivative work.

## Future Features

### What's planned for future releases?

- Real-time notifications via WebSockets
- Advanced search with Elasticsearch
- API authentication (JWT/OAuth2)
- Two-factor authentication
- Email notification system
- File virus scanning
- Content moderation AI
- Mobile app
- Integration with other platforms
- Analytics dashboard

### When will feature X be released?

Check the project roadmap on GitHub for estimated release dates. We release updates regularly based on community feedback and priorities.

## Support

### Where can I get help?

- Documentation: See the docs/ folder
- GitHub Issues: Report bugs and feature requests
- Discord: Join our community for real-time help
- Email: support@autobotsolutions.com

### Is professional support available?

For enterprise support, custom development, or SLAs, contact enterprise@autobotsolutions.com.

## Still Have Questions?

If your question isn't answered here, please:
1. Check the other documentation files in the docs/ folder
2. Search existing GitHub issues
3. Create a new issue on GitHub
4. Join our Discord community
5. Email support@autobotsolutions.com
