# Architecture Documentation

## System Overview

The AutoBot Solutions Forum is a web-based discussion platform built with Flask, designed to facilitate conversations around GitHub repositories. The system follows a Model-View-Controller (MVC) architectural pattern.

## Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Form Handling**: Flask-WTF
- **Migrations**: Flask-Migrate
- **Rate Limiting**: Flask-Limiter
- **Markdown**: python-markdown
- **HTML Sanitization**: bleach

### Frontend
- **Templates**: Jinja2
- **CSS**: Custom CSS with CSS variables
- **Fonts**: Orbitron, Rajdhani (Google Fonts)
- **Icons**: Unicode emoji

### Deployment
- **Web Server**: Gunicorn
- **Reverse Proxy**: Nginx
- **Containerization**: Docker & Docker Compose
- **Process Manager**: Systemd (production)

## Project Structure

```
repo-forum/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models.py                # Database models
│   ├── template_filters.py      # Custom Jinja2 filters
│   ├── config.py                # Configuration
│   ├── static/                  # Static assets
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── script.js
│   │   └── uploads/             # User uploads
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── forum/
│   │   ├── admin/
│   │   ├── user/
│   │   ├── notification/
│   │   ├── message/
│   │   └── errors/
│   ├── auth/                    # Authentication module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── forum/                   # Forum module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── admin/                   # Admin module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── user/                    # User module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── notification/            # Notification module
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── message/                 # Messaging module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── api/                     # API module
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── main/                    # Main routes
│   │   ├── __init__.py
│   │   └── routes.py
│   └── errors/                  # Error handlers
│       ├── __init__.py
│       └── handlers.py
├── docs/                        # Documentation
│   ├── README.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── CONTRIBUTING.md
│   ├── LICENSE.md
│   ├── SECURITY.md
│   └── ARCHITECTURE.md
├── migrations/                  # Database migrations
├── config.py                    # Configuration
├── run.py                       # Development server
├── init_db.py                   # Database initialization
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Docker Compose configuration
├── nginx.conf                   # Nginx configuration
├── .env.example                 # Environment variables template
└── .gitignore
```

## Database Schema

### Core Tables

#### Users
```sql
- id (PK)
- username (unique)
- email (unique)
- password_hash
- is_admin
- is_verified
- verification_token
- reset_token
- reset_token_expiration
- created_at
```

#### Repositories
```sql
- id (PK)
- name
- description
- github_url (unique)
- stars
- language
- updated_at
```

#### Categories
```sql
- id (PK)
- name (unique)
- description
- color
```

#### Posts
```sql
- id (PK)
- title
- content
- user_id (FK -> users)
- repository_id (FK -> repositories)
- category_id (FK -> categories)
- attachment
- created_at
- updated_at
- upvotes
- downvotes
```

#### Comments
```sql
- id (PK)
- content
- user_id (FK -> users)
- post_id (FK -> posts)
- created_at
- upvotes
- downvotes
```

#### Votes
```sql
- id (PK)
- user_id (FK -> users)
- post_id (FK -> posts, nullable)
- comment_id (FK -> comments, nullable)
- value (1 or -1)
- created_at
```

#### Notifications
```sql
- id (PK)
- user_id (FK -> users)
- content
- link
- is_read
- created_at
```

#### Messages
```sql
- id (PK)
- sender_id (FK -> users)
- receiver_id (FK -> users)
- content
- is_read
- created_at
```

#### Bookmarks
```sql
- id (PK)
- user_id (FK -> users)
- post_id (FK -> posts)
- created_at
- UNIQUE(user_id, post_id)
```

#### Badges
```sql
- id (PK)
- name (unique)
- description
- icon
- color
```

#### User_Badges (Association Table)
```sql
- user_id (FK -> users, PK)
- badge_id (FK -> badges, PK)
```

## Request Flow

### Typical Request Lifecycle

1. **Request Reception**
   - Nginx receives HTTP request
   - Routes to Gunicorn based on URL
   - Gunicorn forwards to Flask application

2. **Flask Processing**
   - Flask matches URL to blueprint route
   - Before/after request hooks execute
   - Rate limiting check (if applicable)
   - Authentication check (if required)

3. **Business Logic**
   - Route handler executes
   - Database queries via SQLAlchemy
   - External API calls (GitHub)
   - Business logic validation

4. **Response Generation**
   - Template rendering (Jinja2)
   - Template filters applied (Markdown, etc.)
   - Response assembled

5. **Response Delivery**
   - Flask returns response
   - Gunicorn sends to Nginx
   - Nginx delivers to client

### Authentication Flow

1. User submits login form
2. Flask-WTF validates CSRF token
3. Route handler checks credentials
4. Flask-Login creates session
5. User redirected to protected page
6. Subsequent requests validated via session

## Design Patterns

### Blueprint Pattern
The application uses Flask blueprints to organize functionality into logical modules:
- `auth`: Authentication routes
- `forum`: Forum features
- `admin`: Admin panel
- `user`: User profiles
- `notification`: Notifications
- `message`: Private messaging
- `api`: RESTful API
- `main`: Main pages

### Repository Pattern
Database access is abstracted through SQLAlchemy ORM, providing:
- Query building
- Relationship management
- Migration support
- Connection pooling

### Factory Pattern
The `create_app()` function implements the application factory pattern:
- Enables multiple application instances
- Facilitates testing
- Supports different configurations
- Delayed initialization

## Security Architecture

### Multi-Layer Security

1. **Application Layer**
   - Input validation (WTForms)
   - CSRF protection (Flask-WTF)
   - Rate limiting (Flask-Limiter)
   - XSS protection (Jinja2 auto-escape)

2. **Authentication Layer**
   - Secure password hashing (Werkzeug)
   - Session management (Flask-Login)
   - Token-based verification
   - Password reset with expiration

3. **Data Layer**
   - Parameterized queries (SQLAlchemy)
   - SQL injection prevention
   - Data encryption at rest (PostgreSQL SSL)

4. **Network Layer**
   - HTTPS/TLS encryption
   - Nginx reverse proxy
   - Firewall rules
   - DDoS protection

## Performance Considerations

### Database Optimization
- Indexed columns (username, email, foreign keys)
- Query optimization with lazy loading
- Connection pooling
- Read replicas (future)

### Caching Strategy
- Static files served by Nginx
- Template caching (production)
- Session caching (Redis - future)
- CDN for static assets (future)

### Rate Limiting
- Prevents API abuse
- Protects against brute force
- Configurable per endpoint
- Redis-backed (future)

## Scalability

### Horizontal Scaling
- Stateless application design
- Session storage in Redis (future)
- Load balancing via Nginx
- Container orchestration (Kubernetes - future)

### Vertical Scaling
- Database connection pooling
- Gunicorn worker configuration
- Memory optimization
- CPU optimization

## Monitoring & Logging

### Application Logging
- Structured logging
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Log rotation
- Centralized logging (future)

### Error Tracking
- Custom error pages (404, 500)
- Exception handling
- Error reporting (Sentry - future)

### Performance Monitoring
- Response time tracking
- Database query logging
- Memory usage monitoring
- APM integration (New Relic - future)

## Future Architecture Improvements

### Planned Enhancements

1. **Microservices**
   - Separate authentication service
   - Notification service
   - File storage service
   - Search service (Elasticsearch)

2. **Event-Driven Architecture**
   - Message queue (RabbitMQ/Redis)
   - Async task processing (Celery)
   - Event sourcing
   - CQRS pattern

3. **Real-time Features**
   - WebSocket support
   - Live notifications
   - Real-time chat
   - Collaborative editing

4. **Advanced Search**
   - Elasticsearch integration
   - Full-text search
   - Faceted search
   - Search analytics

## Development Workflow

### Local Development
1. Virtual environment setup
2. Dependency installation
3. Database initialization
4. Development server (Flask)
5. Hot reload enabled

### Production Deployment
1. Docker containerization
2. Docker Compose orchestration
3. Nginx reverse proxy
4. Gunicorn WSGI server
5. PostgreSQL database
6. SSL/TLS termination

## Configuration Management

### Environment Variables
- Database credentials
- Secret keys
- GitHub API token
- Email configuration
- Rate limiting settings

### Configuration Files
- `config.py`: Base configuration
- `.env`: Local environment variables
- `docker-compose.yml`: Container configuration
- `nginx.conf`: Web server configuration

## Dependencies

### Core Dependencies
- Flask: Web framework
- SQLAlchemy: ORM
- Flask-Login: Authentication
- Flask-WTF: Forms
- Flask-Migrate: Migrations
- Flask-Limiter: Rate limiting

### Production Dependencies
- Gunicorn: WSGI server
- Nginx: Reverse proxy
- PostgreSQL: Database
- Redis: Cache/Session (future)

### Development Dependencies
- pytest: Testing
- pip-audit: Security scanning
- black: Code formatting
- flake8: Linting

## API Architecture

### RESTful Design
- Resource-based URLs
- HTTP methods (GET, POST, PUT, DELETE)
- JSON responses
- HTTP status codes
- Rate limiting

### Current Endpoints
- `GET /api/repositories` - List repositories
- `GET /api/posts` - List posts
- `GET /api/posts/<id>` - Get single post
- `POST /api/sync-repositories` - Sync GitHub repos

### Future API Features
- Authentication (JWT/OAuth2)
- CRUD operations for posts
- Comment management
- User management
- Real-time notifications

## Documentation

### Developer Documentation
- API documentation (API.md)
- Deployment guide (DEPLOYMENT.md)
- Contributing guidelines (CONTRIBUTING.md)
- Security policy (SECURITY.md)

### User Documentation
- User guide (future)
- Admin guide (future)
- FAQ (future)

## Support and Maintenance

### Regular Maintenance Tasks
- Dependency updates
- Security patches
- Database backups
- Log rotation
- Performance monitoring

### Issue Resolution
- Bug tracking via GitHub Issues
- Priority classification
- SLA for critical issues
- Regular release cycle
