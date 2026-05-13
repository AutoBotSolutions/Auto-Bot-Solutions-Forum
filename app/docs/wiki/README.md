# AutoBot Solutions Forum

A self-hosted, futuristic sci-fi themed discussion forum for AutoBot Solutions GitHub repositories. Built with Flask, PostgreSQL, and Docker for easy deployment and scalability.

## Features

### Core Forum Features
- **Repository-Specific Discussions**: Link discussions to specific GitHub repositories
- **Voting System**: Upvote/downvote posts and comments with real-time counts
- **Categories**: Organize posts into categories with custom colors
- **Advanced Search**: Full-text search with Elasticsearch integration and intelligent ranking
- **Search Analytics**: Popular queries tracking and user behavior analysis
- **Search Suggestions**: Autocomplete and intelligent search suggestions
- **User Search Preferences**: Personalized search experience
- **Bookmarking**: Save posts for quick access
- **Markdown Support**: Rich text formatting with syntax highlighting

### User Features
- **User Authentication**: Secure login and registration with password hashing
- **Social Login**: OAuth2 integration with Google and GitHub
- **Advanced Session Management**: Redis-based session storage with security features
- **Two-Factor Authentication**: TOTP-based 2FA for enhanced security
- **Email Verification**: Email verification for account security
- **Password Reset**: Secure password reset with token-based recovery
- **User Profiles**: View user activity, posts, comments, and badges
- **Badges & Achievements**: Earn badges for contributions and milestones
- **Enhanced Security**: Device fingerprinting, IP-based controls, suspicious activity detection

### Real-time Features ⚡
- **Live Comment Notifications**: Instant updates when new comments are posted
- **Real-time Vote Updates**: Live vote count updates without page refresh
- **Online User Presence**: See which users are currently online
- **Typing Indicators**: Real-time display of users typing comments
- **Real-time Notifications**: Instant notification system for user interactions
- **WebSocket Infrastructure**: Flask-SocketIO with automatic reconnection
- **Room-based Communication**: Efficient real-time message distribution

### Communication Features
- **Notifications**: Get notified of comments on your posts
- **Private Messaging**: Send and receive private messages
- **Unread Counts**: Track unread notifications and messages
- **Message Search & Filtering**: Full-text search with advanced filtering and Boolean operators
- **Message Threading**: Conversation threading with hierarchical reply chains and participant management
- **Rich Text Formatting**: Markdown processing, emoji support, and message templates

### Enhanced Content Management Features
- **Draft Management**: Auto-save functionality with 30-second intervals
- **Version Control**: Complete version history with comparison and restore
- **Collaborative Editing**: User permissions (view, edit, admin) and collaborator management
- **Content Scheduling**: Schedule posts for future publication
- **Content Analytics**: View engagement metrics and performance data

### Admin Features
- **User Management**: View, edit, and manage user accounts
- **Content Moderation**: Approve, edit, or remove posts and comments
- **Category Management**: Create and manage forum categories
- **Badge System**: Create and assign achievement badges
- **Analytics Dashboard**: View forum statistics and user activity
- **Security Monitoring**: Track suspicious activities and security events

## Technology Stack

- **Backend**: Flask 3.0.0 with SQLAlchemy
- **Database**: PostgreSQL with Redis for caching
- **Frontend**: Bootstrap 5 with custom CSS
- **Real-time**: Flask-SocketIO with WebSocket support
- **Search**: Elasticsearch integration
- **Authentication**: JWT, OAuth2, TOTP 2FA
- **Deployment**: Docker with Docker Compose
- **Testing**: Comprehensive pytest suite

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run `docker-compose up -d`
4. Visit `http://localhost:5000`

## Documentation

- [Installation Guide](Installation-Guide.md)
- [Administrator Guide](Administrator-Guide.md)
- [Developer Guide](Developer-Guide.md)
- [API Documentation](API-System.md)
- [User Guide](User-Guide.md)

## Support

- [FAQ](FAQ.md)
- [Troubleshooting](Troubleshooting.md)
- [Support](Support.md)

## License

See [LICENSE](../../LICENSE) file for details.
