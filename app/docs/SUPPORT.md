# Support

## Getting Help

If you're having trouble with the AutoBot Solutions Forum, there are several ways to get help.

## Documentation

First, check our comprehensive documentation:

- **[README.md](README.md)** - Project overview and quick start guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
- **[API.md](API.md)** - API documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[SECURITY.md](SECURITY.md)** - Security information
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute

## Common Issues

### Installation Problems

**Problem:** Dependencies won't install
**Solution:** Ensure you're using Python 3.8 or higher. Try creating a fresh virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Problem:** Database connection errors
**Solution:** Check that PostgreSQL is running and your `.env` file has the correct database credentials.

### Docker Issues

**Problem:** Container won't start
**Solution:** Check that Docker and Docker Compose are installed. Run:
```bash
docker --version
docker-compose --version
```

**Problem:** Database migration fails
**Solution:** Remove the container and volume, then start fresh:
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec app python init_db.py
```

### CSS Not Loading

**Problem:** Styles are not being applied
**Solution:** The static folder configuration has been fixed. Ensure you're using the latest version of the code. Clear your browser cache and reload.

## Reporting Bugs

If you encounter a bug not covered in the documentation:

1. **Search existing issues** - Check if someone has already reported it
2. **Create a new issue** - Use the GitHub issue tracker
3. **Provide details** - Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (Python version, OS, etc.)
   - Error messages or logs

## Feature Requests

We welcome feature requests! When submitting a request:

- Describe the feature clearly
- Explain why it would be useful
- Provide use cases or examples
- Consider if you could contribute it yourself

## Community Support

### Discord Server

Join our Discord community for real-time help:
- [Discord Invite Link](https://discord.gg/autobotsolutions)

### GitHub Discussions

Use GitHub Discussions for:
- General questions
- Feature discussions
- Show and tell
- Ideas and proposals

### Email

For security issues or private matters:
- Security: security@autobotsolutions.com
- General: support@autobotsolutions.com

## Professional Support

For enterprise support, SLAs, and custom development:
- Contact: enterprise@autobotsolutions.com

## Troubleshooting Guide

### Database Issues

**Problem:** "OperationalError: no such table"
**Solution:** Run database migrations:
```bash
flask db upgrade
```

**Problem:** "OperationalError: database is locked"
**Solution:** This can happen if multiple processes access SQLite. Use PostgreSQL for production.

### Authentication Issues

**Problem:** Can't log in after registration
**Solution:** Check if email verification is required. The verification token is displayed in flash messages for testing.

**Problem:** Password reset not working
**Solution:** Ensure the reset token hasn't expired (1 hour). Request a new reset link.

### Performance Issues

**Problem:** Slow page loads
**Solution:**
- Check database connection
- Enable caching (Redis)
- Use PostgreSQL instead of SQLite
- Enable Nginx gzip compression

### GitHub Integration Issues

**Problem:** Repositories won't sync
**Solution:**
- Check your GitHub token in `.env`
- Verify the organization name is correct
- Check your GitHub API rate limits

## Development Support

For developers:

### Setting Up Development Environment

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup instructions.

### Running Tests

```bash
pytest
```

### Code Style

We use Black for code formatting:
```bash
black app/
```

And flake8 for linting:
```bash
flake8 app/
```

## FAQ

### General Questions

**Q: Can I use this forum for commercial purposes?**
A: Yes, the forum is released under the MIT License, which allows commercial use.

**Q: Do I need to use GitHub?**
A: No, the GitHub integration is optional. You can use the forum without it.

**Q: Can I customize the theme?**
A: Yes, the CSS is fully customizable. See the `app/static/css/style.css` file.

**Q: Is there a mobile app?**
A: Not yet, but the forum is responsive and works well on mobile browsers.

**Q: Can I import existing data?**
A: Not currently, but we're planning to add import/export functionality.

### Technical Questions

**Q: What Python version is required?**
A: Python 3.8 or higher.

**Q: Can I use MySQL instead of PostgreSQL?**
A: The forum is designed for PostgreSQL, but SQLAlchemy supports MySQL. You would need to modify the connection string.

**Q: How do I scale the forum?**
A: The forum can be scaled horizontally using Docker and a load balancer. See ARCHITECTURE.md for details.

**Q: Is there a REST API?**
A: Yes, see API.md for documentation.

**Q: Can I use this with other authentication providers?**
A: Currently, only local authentication is supported. OAuth integration is planned for future releases.

## Getting Involved

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started.

## Acknowledgments

Thanks to all our contributors and community members who help make this project better!

## Contact

For any questions not covered here, please:
- Open an issue on GitHub
- Join our Discord server
- Email support@autobotsolutions.com
