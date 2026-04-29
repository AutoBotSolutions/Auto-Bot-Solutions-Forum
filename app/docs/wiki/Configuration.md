# Configuration

## Environment Variables

### Required Variables
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: PostgreSQL connection string

### Optional Variables
- `GITHUB_ORG`: GitHub organization name
- `GITHUB_TOKEN`: GitHub API token (optional)

## Example .env

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/forumdb
GITHUB_ORG=AutoBotSolutions
GITHUB_TOKEN=ghp_your_token_here
```

## Flask Configuration

- Debug mode (development only)
- Session configuration
- Upload folder
- Secret key
- Database URI
