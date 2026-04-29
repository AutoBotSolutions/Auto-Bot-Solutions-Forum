# Contributing to AutoBot Solutions Forum

Thank you for your interest in contributing to the AutoBot Solutions Forum! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git
- Docker and Docker Compose (for containerized development)

### Setting Up the Development Environment

1. Clone the repository:
```bash
git clone https://github.com/AutoBotSolutions/repo-forum.git
cd repo-forum
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the development server:
```bash
python run.py
```

The forum will be available at `http://localhost:5000`

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Development branch for integration
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Critical hotfixes for production

### Creating a Feature Branch

1. Create a new branch from `develop`:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Commit your changes:
```bash
git add .
git commit -m "feat: description of your feature"
```

4. Push to your fork:
```bash
git push origin feature/your-feature-name
```

5. Create a Pull Request

### Commit Message Convention

Follow the Conventional Commits specification:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Example: `feat: add user profile page with activity history`

## Coding Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and under 50 lines when possible
- Maximum line length: 100 characters

### HTML/Jinja2 Templates

- Use meaningful template names
- Keep templates modular and reusable
- Use template inheritance with `base.html`
- Add comments for complex template logic

### CSS

- Use CSS custom properties (variables) for theming
- Keep CSS organized by component
- Use BEM naming convention for classes
- Ensure responsive design for all components

## Testing

### Running Tests

```bash
pytest
```

### Writing Tests

- Write unit tests for all new functions
- Write integration tests for API endpoints
- Aim for >80% code coverage
- Use descriptive test names

## Pull Request Guidelines

### Before Submitting a PR

- Ensure all tests pass
- Update documentation if needed
- Add tests for new features
- Follow the commit message convention
- Squash related commits into a single commit

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested the changes

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Code Review Process

1. Automated checks (CI/CD) must pass
2. At least one maintainer approval required
3. Address all review comments
4. Update PR description if scope changes

## Reporting Issues

### Bug Reports

Use the issue tracker and include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (Python version, OS, etc.)

### Feature Requests

Use the issue tracker and include:
- Description of the feature
- Use case/why it's needed
- Possible implementation approach
- Any relevant mockups or examples

## Security Issues

For security vulnerabilities, please email security@autobotsolutions.com instead of using the issue tracker.

## Getting Help

- Join our Discord server: [Link]
- Check existing documentation in `/app/docs/`
- Search existing issues before creating new ones

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards

- Use inclusive language
- Respect differing viewpoints
- Accept constructive criticism
- Focus on what is best for the community

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks
- Public or private harassment
- Publishing others' private information

### Enforcement

Project maintainers have the right and responsibility to remove, edit, or reject comments and contributions that do not align with this Code of Conduct.

## Recognition

Contributors will be recognized in the CONTRIBUTORS.md file. Thank you for your contributions!
