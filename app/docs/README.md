# AutoBot Solutions Forum

A self-hosted, futuristic sci-fi themed discussion forum for AutoBot Solutions GitHub repositories. Built with Flask, PostgreSQL, and Docker for easy deployment and scalability.

## Features

### Core Forum Features
- **Repository-Specific Discussions**: Link discussions to specific GitHub repositories
- **Voting System**: Upvote/downvote posts and comments with real-time counts
- **Categories**: Organize posts into categories with custom colors
- **Search**: Search posts and comments by content
- **Bookmarking**: Save posts for quick access
- **Markdown Support**: Rich text formatting with syntax highlighting

### User Features
- **User Authentication**: Secure login and registration with password hashing
- **Email Verification**: Email verification for account security
- **Password Reset**: Secure password reset with token-based recovery
- **User Profiles**: View user activity, posts, comments, and badges
- **Badges & Achievements**: Earn badges for contributions and milestones

### Communication Features
- **Notifications**: Get notified of comments on your posts
- **Private Messaging**: Send and receive private messages
- **Unread Counts**: Track unread notifications and messages

### Content Features
- **File Uploads**: Attach files to posts (images, PDFs, documents)
- **Comments**: Threaded comments on posts
- **Markdown Rendering**: Beautiful formatted content with code highlighting

### Admin Features
- **Admin Panel**: Comprehensive admin dashboard
- **User Management**: Manage users, promote admins
- **Content Moderation**: Manage posts and comments
- **Category Management**: Create and manage forum categories
- **Badge Management**: Create and award badges
- **Repository Management**: Sync and manage GitHub repositories

### Security Features
- **CSRF Protection**: All forms protected against CSRF attacks
- **Rate Limiting**: Rate limiting on sensitive endpoints
- **XSS Protection**: Input sanitization and auto-escaping
- **SQL Injection Prevention**: Parameterized queries
- **Secure Password Hashing**: PBKDF2 with SHA-256

### GitHub Integration
- **Repository Sync**: Automatically sync repositories from GitHub organization
- **Repository Metadata**: Display stars, language, and other metadata
- **Repository-Linked Posts**: Link posts to specific repositories

### UI/UX Features
- **Futuristic UI**: Sci-fi themed interface with neon colors and glowing effects
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Theme**: Easy on the eyes with high contrast
- **Custom Fonts**: Orbitron and Rajdhani fonts for sci-fi aesthetic

### Technical Features
- **REST API**: API endpoints for programmatic access
- **Scalable Architecture**: Modular blueprint-based architecture
- **Database Migrations**: Flask-Migrate for database versioning
- **Development Ready**: Easy local development setup

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Deployment**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **Frontend**: HTML/CSS/JavaScript with custom sci-fi theme

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Git (for cloning)
- At least 2GB RAM available
- 1GB free disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd repo-forum
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```
   
   This will:
   - Create database tables
   - Create default admin user (username: admin, password: admin123)
   - Add initial categories (5 categories)
   - Add initial badges (5 badges)

5. **Start the forum**
   ```bash
   python run.py
   ```

6. **Access the forum**
   - Open your browser to `http://localhost:5000`
   - Login with admin credentials (admin/admin123)
   - **IMPORTANT:** Change the admin password after first login

## Manual Deployment

### System Requirements

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.11+
- PostgreSQL 15+
- Nginx (for reverse proxy)
- SSL certificate (for production)

### Step-by-Step Deployment

1. **Install system dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx
   ```

2. **Create PostgreSQL database**
   ```bash
   sudo -u postgres psql
   ```
   ```sql
   CREATE USER forum_user WITH PASSWORD 'secure_password';
   CREATE DATABASE forum_db OWNER forum_user;
   \q
   ```

3. **Set up Python environment**
   ```bash
   cd /path/to/repo-forum
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

6. **Configure Nginx**
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/forum
   sudo ln -s /etc/nginx/sites-available/forum /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

7. **Set up systemd service**
   ```bash
   sudo nano /etc/systemd/system/forum.service
   ```
   ```
   [Unit]
   Description=AutoBot Forum
   After=network.target postgresql.service

   [Service]
   User=your-user
   WorkingDirectory=/path/to/repo-forum
   Environment="PATH=/path/to/repo-forum/venv/bin"
   ExecStart=/path/to/repo-forum/venv/bin/gunicorn --workers 4 --bind unix:forum.sock run:app

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl start forum
   sudo systemctl enable forum
   ```

8. **Configure SSL (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## Security Considerations

### Production Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Use strong, random SECRET_KEY (minimum 32 characters)
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall (ufw) to allow only necessary ports
- [ ] Regularly update system packages
- [ ] Enable PostgreSQL SSL connections
- [ ] Set up database backups
- [ ] Configure fail2ban for brute-force protection
- [ ] Use environment variables for sensitive data
- [ ] Never commit `.env` file to version control

### Firewall Configuration

```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### Database Security

- Use strong database passwords
- Restrict PostgreSQL to localhost
- Regular backups: `pg_dump forum_db > backup.sql`
- Consider using connection pooling (PgBouncer)

## Scaling

### Horizontal Scaling

To scale horizontally:

1. **Load Balancer**: Use HAProxy or cloud load balancer
2. **Multiple App Instances**: Run multiple app containers behind load balancer
3. **Shared Database**: All instances connect to the same PostgreSQL
4. **Redis for Sessions**: Add Redis for session storage (future enhancement)
5. **CDN for Static Files**: Serve static files via CDN

### Vertical Scaling

Increase resources:
- More CPU cores for Gunicorn workers
- More RAM for database caching
- Faster storage (SSD) for database

## Maintenance

### Database Backups

```bash
# Manual backup
docker-compose exec db pg_dump -U forum_user forum_db > backup.sql

# Automated backup (add to crontab)
0 2 * * * docker-compose exec db pg_dump -U forum_user forum_db > /backups/forum_$(date +\%Y\%m\%d).sql
```

### Updating Repositories

```bash
# Sync GitHub repositories
curl -X POST http://localhost:5000/api/sync-repositories
```

### Log Management

```bash
# View logs
docker-compose logs -f app
docker-compose logs -f db

# Rotate logs (configure in docker-compose or use logrotate)
```

## Troubleshooting

### Common Issues

**Database connection error**
- Check PostgreSQL is running: `docker-compose ps db`
- Verify DATABASE_URL in `.env`
- Check database credentials

**Container won't start**
- Check logs: `docker-compose logs`
- Verify port 5000 is not in use
- Check disk space

**GitHub sync fails**
- Verify GITHUB_TOKEN is valid
- Check rate limits on GitHub API
- Verify organization name in config.py

**Jinja2 template errors**
- Ensure all template filters are properly registered
- Check for missing `|safe` filter on HTML content
- Verify template syntax and variable names

**Comment submission errors**
- Check that Post model uses `user_id` not `author_id`
- Verify form validation and CSRF tokens
- Ensure database relationships are properly defined

**Markdown rendering issues**
- Check that markdown filter is registered in app initialization
- Verify `|safe` filter is used for HTML output
- Check markdown package installation and extensions

## Development

### Running in Development Mode

```bash
# Without Docker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=development
python run.py
```

### Adding New Features

1. Create feature branch
2. Make changes in `app/` directory
3. Test thoroughly
4. Update documentation
5. Submit pull request

## API Endpoints

### Sync Repositories
```
POST /api/sync-repositories
```
Syncs repositories from GitHub organization.

### Get Repositories
```
GET /api/repositories
```
Returns list of all repositories.

### Get Posts
```
GET /api/posts
```
Returns list of all posts.

## License

This project is part of AutoBot Solutions. See LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [your-repo-url]/issues
- Documentation: See DEPLOYMENT.md for detailed deployment guide

## Future Enhancements

- Real-time notifications via WebSockets
- Email notification system (SMTP configuration)
- Advanced search with Elasticsearch
- Two-factor authentication
- API authentication (JWT/OAuth2)
- Threaded/nested comments
- Post editing and history
- Rich text editor with live preview
- Mobile app development
- Analytics dashboard
- Content reporting system
- Spam detection and auto-moderation
