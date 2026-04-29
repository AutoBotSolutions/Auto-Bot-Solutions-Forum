# GitHub Integration

## Overview

Syncs repositories from GitHub organization AutoBotSolutions and links them to forum discussions.

## Features

- Automatic repository sync
- Repository metadata display
- Repository-linked discussions
- Manual sync via API
- Admin management

## Configuration

```python
GITHUB_ORG = 'AutoBotSolutions'
GITHUB_TOKEN = 'your_token'  # Optional
```

## API Endpoint

- `POST /api/sync-repositories`
- Fetches from GitHub API
- Updates or creates records
- Returns synced repositories

## Repository Data

- Name
- Description
- GitHub URL
- Stars
- Language
- Updated timestamp
