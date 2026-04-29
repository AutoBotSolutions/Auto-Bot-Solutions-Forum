# Auto Bot Solutions Forum

<div align="center">

![Auto Bot Solutions Forum](https://img.shields.io/badge/AutoBot-Forum-blue?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-2.3+-green?style=for-the-badge&logo=flask)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)
![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)

**A self-hosted, futuristic sci-fi themed discussion forum for AutoBot Solutions GitHub repositories**

[Live Demo](https://autobotsolutions.github.io/Auto-Bot-Solutions-Forum/) • [Documentation](app/docs/) • [Report Issue](https://github.com/AutoBotSolutions/Auto-Bot-Solutions-Forum/issues)

</div>

---

## 🚀 Overview

Auto Bot Solutions Forum is a comprehensive, feature-rich discussion platform built with Flask, PostgreSQL, and Docker. Designed with a futuristic sci-fi aesthetic, it provides a modern, engaging space for developers to discuss AutoBot Solutions projects, share knowledge, and collaborate effectively.

### ✨ Key Features

- **🔗 GitHub Integration** - Seamlessly link discussions to specific repositories
- **🗳️ Voting System** - Upvote/downvote posts and comments with real-time counts
- **📂 Categories & Tags** - Organize content with custom categories and tagging
- **🔍 Advanced Search** - Full-text search across posts and comments
- **🔖 Bookmarking** - Save important posts for quick access
- **✍️ Markdown Support** - Rich text formatting with syntax highlighting
- **👤 User Profiles** - Comprehensive profiles with activity tracking
- **🏆 Badges & Achievements** - Gamification system to recognize contributions
- **🔔 Notifications** - Real-time notifications for important updates
- **💬 Private Messaging** - Direct communication between users
- **📎 File Uploads** - Attach images, PDFs, and documents to posts
- **🛡️ Security** - CSRF protection, rate limiting, XSS protection, and more
- **🎨 Futuristic UI** - Sci-fi themed interface with neon colors and glowing effects

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Flask (Python 3.8+) |
| **Database** | PostgreSQL 15+ |
| **ORM** | SQLAlchemy |
| **Authentication** | Flask-Login |
| **Deployment** | Docker & Docker Compose |
| **Reverse Proxy** | Nginx |
| **Frontend** | HTML/CSS/JavaScript (Custom Sci-Fi Theme) |

---

## 📦 Quick Start

### Prerequisites

- Python 3.8 or higher
- Git
- Docker and Docker Compose (optional)
- At least 2GB RAM available
- 1GB free disk space

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/AutoBotSolutions/Auto-Bot-Solutions-Forum.git
cd Auto-Bot-Solutions-Forum

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start with Docker Compose
docker-compose up -d

# Initialize the database
docker-compose exec app python init_db.py
```

#### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/AutoBotSolutions/Auto-Bot-Solutions-Forum.git
cd Auto-Bot-Solutions-Forum

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python init_db.py

# Start the forum
python run.py
```

### Access the Forum

- Open your browser to `http://localhost:5000`
- Default admin credentials: `admin` / `admin123`
- **⚠️ Important:** Change the admin password immediately after first login

---

## 🏗️ Project Structure

```
repo-forum/
├── app/
│   ├── admin/          # Admin panel routes and forms
│   ├── api/            # REST API endpoints
│   ├── auth/           # Authentication routes and forms
│   ├── docs/           # Comprehensive documentation
│   ├── errors/         # Error handlers
│   ├── forum/          # Forum routes and forms
│   ├── main/           # Main routes
│   ├── message/        # Private messaging system
│   ├── notification/   # Notification system
│   ├── static/         # Static assets (CSS, JS, images)
│   ├── templates/      # HTML templates
│   ├── user/           # User profile management
│   ├── __init__.py     # Flask application factory
│   ├── models.py       # Database models
│   └── template_filters.py  # Custom Jinja filters
├── instance/           # Instance-specific data (database)
├── site/               # GitHub Pages website
├── .github/            # GitHub Actions workflows
├── config.py           # Application configuration
├── init_db.py          # Database initialization script
├── run.py              # Application entry point
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image configuration
├── docker-compose.yml  # Docker Compose configuration
└── nginx.conf          # Nginx configuration
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=0

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/forum_db

# GitHub Configuration
GITHUB_TOKEN=your-github-token
GITHUB_ORGANIZATION=AutoBotSolutions

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Manual Deployment

For production deployment without Docker, see the [Deployment Guide](app/docs/DEPLOYMENT.md) in the documentation.

### Security Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Use a strong, random `SECRET_KEY` (minimum 32 characters)
- [ ] Enable HTTPS with a valid SSL certificate
- [ ] Configure firewall to allow only necessary ports
- [ ] Set up regular database backups
- [ ] Enable PostgreSQL SSL connections
- [ ] Configure fail2ban for brute-force protection
- [ ] Never commit `.env` file to version control

---

## 📚 Documentation

Comprehensive documentation is available in the `app/docs/` directory:

- [API Documentation](app/docs/API.md) - REST API endpoints and usage
- [Architecture](app/docs/ARCHITECTURE.md) - System architecture and design
- [Deployment Guide](app/docs/DEPLOYMENT.md) - Detailed deployment instructions
- [Security](app/docs/SECURITY.md) - Security best practices
- [Contributing](app/docs/CONTRIBUTING.md) - How to contribute to the project
- [FAQ](app/docs/FAQ.md) - Frequently asked questions

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

See [CONTRIBUTING.md](app/docs/CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

This project is proprietary software owned by Auto Bot Solutions (Software Customs). All rights reserved.

**Owner:** Robert Trenaman  
**Company:** Auto Bot Solution (Software Customs)  
**Email:** autobotsolution@gmail.com  
**Location:** Flushing, MI

---

## 🆘 Support

For issues, questions, or support:

- **GitHub Issues:** [Report a bug or request a feature](https://github.com/AutoBotSolutions/Auto-Bot-Solutions-Forum/issues)
- **Email:** autobotsolution@gmail.com
- **Documentation:** See the [app/docs/](app/docs/) directory

---

## 🔮 Roadmap

Future enhancements planned:

- [ ] Real-time notifications via WebSockets
- [ ] Email notification system with SMTP
- [ ] Advanced search with Elasticsearch
- [ ] Two-factor authentication
- [ ] API authentication (JWT/OAuth2)
- [ ] Threaded/nested comments
- [ ] Post editing and history
- [ ] Rich text editor with live preview
- [ ] Mobile app development
- [ ] Analytics dashboard
- [ ] Content reporting system
- [ ] Spam detection and auto-moderation

---

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Database powered by [PostgreSQL](https://www.postgresql.org/)
- Styled with custom CSS inspired by sci-fi aesthetics
- Icons and fonts from [Google Fonts](https://fonts.google.com/)

---

<div align="center">

**Built with ❤️ by Auto Bot Solutions**

[Website](https://autobotsolutions.github.io/Auto-Bot-Solutions-Forum/) • [GitHub](https://github.com/AutoBotSolutions) • [Contact](mailto:autobotsolution@gmail.com)

</div>
