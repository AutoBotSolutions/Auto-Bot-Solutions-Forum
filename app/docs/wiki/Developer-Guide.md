# Developer Guide

## Overview

Complete guide for developers contributing to the AutoBot Solutions Forum.

## Development Environment Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git
- Virtual environment tool

### Setup Steps

1. **Clone Repository**
```bash
git clone https://github.com/AutoBotSolutions/repo-forum.git
cd repo-forum
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize Database**
```bash
python init_db.py
```

6. **Run Development Server**
```bash
python run.py
```

Access at `http://localhost:5000`

## Project Structure

```
repo-forum/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── template_filters.py  # Custom Jinja2 filters
│   ├── static/              # Static assets
│   ├── templates/           # Jinja2 templates
│   ├── auth/                # Authentication module
│   ├── forum/               # Forum module
│   ├── admin/               # Admin module
│   ├── user/                # User module
│   ├── notification/        # Notification module
│   ├── message/             # Messaging module
│   ├── api/                 # API module
│   └── main/                # Main routes
├── migrations/              # Database migrations
├── docs/                    # Documentation
├── config.py                # Configuration
├── run.py                   # Development server
├── init_db.py               # Database initialization
└── requirements.txt         # Python dependencies
```

## Code Style

### Python Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused
- Maximum line length: 100 characters

### HTML/Jinja2 Style
- Use meaningful template names
- Keep templates modular
- Use template inheritance
- Add comments for complex logic

### CSS Style
- Use CSS custom properties
- Organize by component
- Use BEM naming convention
- Ensure responsive design

## Development Workflow

### Branching Strategy
- `main` - Production code
- `develop` - Development branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches

### Creating a Feature Branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Committing Changes
```bash
git add .
git commit -m "feat: description of your feature"
```

### Commit Message Convention
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style
- `refactor:` - Refactoring
- `test:` - Tests
- `chore:` - Maintenance

## Database Migrations

### Creating a Migration
```bash
flask db migrate -m "description"
```

### Applying Migrations
```bash
flask db upgrade
```

### Rolling Back
```bash
flask db downgrade
```

## Testing

### Running Tests
```bash
pytest
```

### Writing Tests
- Write unit tests for functions
- Write integration tests for routes
- Aim for >80% coverage
- Use descriptive test names

## Common Development Tasks

### Adding a New Route
1. Add route function in appropriate blueprint
2. Create template if needed
3. Add form if needed
4. Update models if needed
5. Add authentication/decorators
6. Add rate limiting
7. Test the route

### Adding a New Model
1. Add model to `models.py`
2. Create migration
3. Apply migration
4. Add relationships
5. Create admin routes (if needed)
6. Update templates

### Adding a New Form
1. Create form class in `forms.py`
2. Add validators
3. Add CSRF protection
4. Create template with form
5. Handle form submission
6. Add flash messages

### Adding a New Blueprint
1. Create blueprint directory
2. Add `__init__.py`
3. Create `routes.py`
4. Create `forms.py` (if needed)
5. Register blueprint in `app/__init__.py`
6. Create templates directory

## Debugging

### Enabling Debug Mode
```python
app.run(debug=True)
```

### Viewing Logs
```bash
tail -f logs/app.log
```

### Database Queries
```python
from flask_sqlalchemy import get_debug_queries
for query in get_debug_queries():
    print(query.statement, query.parameters, query.duration)
```

### Common Issues

**Import Errors**
- Check virtual environment is activated
- Verify dependencies are installed
- Check Python path

**Database Errors**
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database exists

**Template Errors**
- Check template path
- Verify template syntax
- Check context variables

## Performance Optimization

### Database Optimization
- Use indexed columns
- Optimize queries
- Use lazy loading
- Add query limits

### Caching (Future)
- Implement Redis caching
- Cache query results
- Cache static assets
- Use CDN

### Frontend Optimization
- Minify CSS/JS
- Optimize images
- Use lazy loading
- Enable compression

## Security Best Practices

### Input Validation
- Validate all user input
- Sanitize data
- Use parameterized queries
- Never trust user input

### Authentication
- Use secure password hashing
- Implement CSRF protection
- Use rate limiting
- Secure session cookies

### Data Protection
- Hash passwords
- Encrypt sensitive data
- Use HTTPS in production
- Secure environment variables

## Contributing

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Make your changes
4. Write tests
5. Update documentation
6. Submit pull request

### Pull Request Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Commit messages follow convention

## Resources

### Documentation
- [Architecture-System.md](Architecture-System.md)
- [Database-System.md](Database-System.md)
- [API-System.md](API-System.md)
- [Security-System.md](Security-System.md)

### External Resources
- Flask Documentation
- SQLAlchemy Documentation
- Jinja2 Documentation
- PostgreSQL Documentation

## Getting Help

- Check existing documentation
- Search GitHub issues
- Join Discord community
- Email dev@autobotsolutions.com
