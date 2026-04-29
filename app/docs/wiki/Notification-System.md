# Notification System

## Overview

The notification system alerts users about important events such as comments on their posts. It provides real-time feedback through the UI with unread counts and notification lists.

## Components

### Models

**Notification Model** (`app/models.py`)
```python
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(256))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='notifications')
```

### Routes

**Notifications Route** (`/notifications`)
- Requires authentication
- Lists all notifications for current user
- Shows unread count
- Displays notification content
- Links to related content
- Read/unread styling

**Mark Read Route** (`/notifications/<notification_id>/read`)
- Requires authentication
- Marks notification as read
- Redirects to notification link (if exists)
- Redirects to notifications page (if no link)

**Mark All Read Route** (`/notifications/read_all`)
- Requires authentication
- Marks all notifications as read
- Bulk update for efficiency
- Flash confirmation
- Redirects to notifications page

## Notification Types

### Comment Notification
- Triggered when someone comments on your post
- Content: "{username} commented on your post '{post_title}'"
- Link: Links to the post
- Not sent if commenter is post author

### Future Notification Types (Planned)
- Like on your post
- Reply to your comment
- New badge awarded
- User mentioned you
- New message received
- Repository synced
- Admin action on your content

## Notification Creation

### Automatic Notifications

**Comment Addition** (`app/forum/routes.py`)
```python
if post.author_id != current_user.id:
    notification = Notification(
        user_id=post.author_id,
        content=f'{current_user.username} commented on your post "{post.title}"',
        link=url_for('forum.post', post_id=post.id)
    )
    db.session.add(notification)
```

### Manual Notifications (Future)
- Admin can create notifications
- System notifications
- Mass notifications

## Notification Display

### Navbar Badge
- Bell icon in navbar
- Shows unread count
- Magenta color badge
- Glowing effect
- Hidden when zero unread

### Notification List
- Chronological order (newest first)
- Read/unread styling
- Content display
- Action links
- Timestamp

### Read/Unread Styling
- Unread: Cyan border, glow effect
- Read: Normal border
- Hover effects
- Transition animations

## Notification Metadata

### Content
- Human-readable message
- Contextual information
- Action-oriented

### Link
- Optional link to related content
- URL to relevant page
- Used for "View" action

### Read Status
- Boolean flag
- Default: false (unread)
- Set to true when marked read
- Used for unread count

### Timestamp
- Creation time
- Displayed in notifications
- Used for sorting

## Unread Count

### Calculation
```python
unread_count = current_user.notifications.filter_by(is_read=False).count()
```

### Display
- Shown in navbar
- Shown on notifications page
- Updated in real-time
- Badge disappears when zero

## Templates

### Notifications Template (`notification/notifications.html`)
- Hero section with count
- Mark all read button
- Notification list
- Individual notification items
- Read/unread styling
- Action links

## CSS Styling

### Notification Badge
- Magenta background
- White text
- Small font size
- Rounded corners
- Glow effect

### Notification Item
- Dark card background
- Border glow
- Unread: Cyan border with glow
- Hover effects
- Smooth transitions

### Notification Content
- Primary text color
- Readable font size
- Clear hierarchy

### Notification Actions
- Cyan color for links
- Hover glow effects
- Delete action: red hover

## Integration Points

### Forum System
- Comments on posts trigger notifications
- Future: Likes, replies, mentions

### Messaging System (Future)
- New message notifications
- Unread message count

### Admin System (Future)
- Admin action notifications
- System notifications

## Performance Considerations

### Database Queries
- Filter by user_id
- Filter by is_read
- Order by created_at DESC
- Lazy loading for efficiency

### Bulk Operations
- Mark all read uses bulk update
- Efficient for many notifications
- Single database query

### Future Optimizations
- Pagination for large lists
- Notification archiving
- Indexed fields (user_id, is_read)
- Redis caching for counts

## Best Practices

### Notification Content
- Be clear and concise
- Include relevant context
- Use action-oriented language
- Include usernames for personalization

### Notification Links
- Always provide relevant link
- Link to specific content
- Make links actionable

### Notification Volume
- Don't overwhelm users
- Group similar notifications
- Allow notification preferences (future)
- Provide digest option (future)

## Future Enhancements

### Notification Preferences
- Email notifications
- Push notifications (mobile)
- Notification frequency settings
- Per-type preferences
- Quiet hours

### Notification Types
- Like notifications
- Reply notifications
- Mention notifications
- Badge awarded notifications
- Message notifications
- System notifications
- Admin notifications

### Notification Features
- Notification grouping
- Notification digest
- Notification history
- Notification search
- Notification filtering
- Notification archiving
- Notification analytics
- Real-time push (WebSockets)
- Mobile push notifications
