# Quick Start Guide

## Overview

Get up and running with the AutoBot Solutions Forum in minutes.

## For Users

### Step 1: Register
1. Click "Register" in the navbar
2. Choose a username (4-64 characters)
3. Enter your email address
4. Choose a strong password (8+ characters)
5. Click "Register"

### Step 2: Verify Email
- Check your email for verification link
- Click the link to verify your account
- Or use the token displayed for testing

### Step 3: Login
- Click "Login" in the navbar
- Enter your username and password
- Click "Login"
- Optional: Check "Remember Me"

### Step 4: Create Your First Post
1. Click "New Post" in the navbar
2. Enter a title (5+ characters)
3. Write your content (supports Markdown)
4. Optionally select a category
5. Optionally select a repository
6. Optionally attach a file
7. Click "Create Post"

### Step 5: Explore
- Browse the forum index
- Search for topics
- View user profiles
- Bookmark interesting posts
- Vote on content

## For Administrators

### Step 1: Deploy
```bash
git clone https://github.com/AutoBotSolutions/repo-forum.git
cd repo-forum
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
docker-compose exec app python init_db.py
```

### Step 2: Access Admin Panel
- Login with admin account (created by init_db.py)
- Click "Admin" in the navbar
- Access dashboard and management tools

### Step 3: Configure
- Sync GitHub repositories
- Create categories
- Create badges
- Review user accounts

## For Developers

### Step 1: Set Up Development Environment
```bash
git clone https://github.com/AutoBotSolutions/repo-forum.git
cd repo-forum
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python init_db.py
python run.py
```

### Step 2: Contribute
- See [CONTRIBUTING.md](../CONTRIBUTING.md)
- Create a feature branch
- Make your changes
- Submit a pull request

## Common First Steps

### Change Your Profile
1. Click "Profile" in navbar
2. Click "Edit Profile"
3. Update username or email
4. Click "Save"

### Send a Message
1. Click the envelope icon in navbar
2. Click "New Message"
3. Select recipient
4. Write your message
5. Click "Send Message"

### Bookmark a Post
1. Navigate to any post
2. Click "★ Bookmark"
3. View bookmarks via navbar

### View Notifications
1. Click the bell icon in navbar
2. View unread notifications
3. Click "View" to navigate to content
4. Click "Mark All Read" to clear

## Next Steps

- Read the [User Guide](User-Guide.md) for detailed features
- Check the [Administrator Guide](Administrator-Guide.md) for admin tasks
- See the [Developer Guide](Developer-Guide.md) for development

## Need Help?

- Check [FAQ](FAQ.md)
- Visit [Support](Support.md)
- Join our Discord community
- Email support@autobotsolutions.com
