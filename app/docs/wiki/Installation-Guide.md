# Installation Guide

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Docker & Docker Compose (recommended)
- Git

## Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/AutoBotSolutions/repo-forum.git
cd repo-forum

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy
docker-compose up -d

# Initialize database
docker-compose exec app python init_db.py

# Access
http://localhost:5000
```

## Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Initialize database
python init_db.py

# Run development server
python run.py
```

## Database Setup

```bash
# Create PostgreSQL database
createdb forumdb

# Set DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/forumdb
```

## Troubleshooting

See [SUPPORT.md](../SUPPORT.md) for common issues and solutions.
