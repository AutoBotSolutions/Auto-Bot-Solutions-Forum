# User System

## Overview

The user system manages user profiles, profile editing, and user activity tracking. It provides users with a personal space to view their activity, manage their account, and display badges and achievements.

## Components

### Models

**User Model** (`app/models.py`)
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(256))
    reset_token = db.Column(db.String(256))
    reset_token_expiration = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    badges = db.relationship('Badge', secondary='user_badges', backref='users')
```

### Forms

**EditProfileForm** (`app/user/forms.py`)
- Username field with validation
- Email field with validation
- Submit button
- Validates against existing usernames/emails

### Routes

**Profile Route** (`/user/profile/<username>`)
- Displays user profile page
- Shows user metadata
- Displays recent posts (last 10)
- Displays recent comments (last 10)
- Shows activity statistics
- Displays user badges
- Edit profile button (for own profile)

**Edit Profile Route** (`/user/profile/edit`)
- Requires authentication
- Method: GET, POST
- Updates username and email
- Validates against existing users
- Flash confirmation

## Profile Page Features

### User Information
- Username
- Email
- Join date
- Avatar placeholder (first letter of username)

### Statistics
- Total posts count
- Total comments count
- Join date

### Recent Activity
- Recent posts (last 10)
- Recent comments (last 10)
- Activity timestamps
- Links to full content

### Badges/Achievements
- Display all user badges
- Badge icon and name
- Badge color
- Badge description (tooltip)

### Profile Editing
- Only available for own profile
- Update username
- Update email
- Form validation
- Confirmation message

## Relationships

### Posts Relationship
- One-to-many relationship
- User has many posts
- Post belongs to one user
- Lazy loading for efficiency

### Comments Relationship
- One-to-many relationship
- User has many comments
- Comment belongs to one user
- Lazy loading for efficiency

### Badges Relationship
- Many-to-many relationship
- User can have many badges
- Badge can have many users
- Association table: user_badges

## Profile Templates

### Profile Template (`user/profile.html`)
- User header with avatar
- Profile statistics
- Recent posts section
- Recent comments section
- Badges display
- Edit profile button (if own profile)

### Edit Profile Template (`user/edit_profile.html`)
- Profile editing form
- Username field
- Email field
- Cancel link
- Form validation errors

## Badge Display

### Badge Component
- Icon (emoji)
- Name
- Color (customizable)
- Background color with opacity
- Border matching badge color
- Hover effects

### Badge Styling
- Flex layout for badge list
- Responsive design
- Sci-fi themed colors
- Glow effects on hover

## Activity Tracking

### Posts Activity
- Shows last 10 posts
- Displays post title
- Shows post creation date
- Links to full post
- Shows vote counts

### Comments Activity
- Shows last 10 comments
- Displays comment preview
- Shows comment creation date
- Links to parent post
- Shows vote counts

## Profile Editing

### Validation
- Username uniqueness check
- Email uniqueness check
- Length constraints
- Email format validation
- Prevents changing to existing username/email

### Update Process
1. User submits form
2. Form validation
3. Database update
4. Session update (if username changed)
5. Flash confirmation
6. Redirect to profile

## Profile Links

### Author Links
- Post author links to profile
- Comment author links to profile
- Search result author links
- Badge page author links
- Message sender/receiver links

### Link Styling
- Neon magenta color
- Hover effect with cyan
- Text shadow on hover
- Consistent across all pages

## Security Considerations

### Profile Access
- Public profile viewing
- Private profile editing
- Authentication required for editing
- CSRF protection on forms

### Username/Email Changes
- Validates against existing users
- Prevents account takeover
- Email change requires re-verification (future)
- Username change updates session

### Privacy
- Email visible on profile (consider hiding)
- Join date visible
- Activity history visible
- Consider privacy settings (future)

## Future Enhancements

- Privacy settings (public/private profile)
- Profile picture upload
- Bio/about section
- Social media links
- Custom profile themes
- User reputation/karma
- Follow system
- Activity feed
- User statistics dashboard
- Export user data
- Account deletion
- Profile analytics
- Signature for posts
