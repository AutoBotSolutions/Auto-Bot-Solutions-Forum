# Messaging System

## Overview

The messaging system provides private communication between users through direct messages. It includes inbox management, sent messages, and message composition with read status tracking.

## Components

### Models

**Message Model** (`app/models.py`)
```python
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
```

### Forms

**MessageForm** (`app/message/forms.py`)
- Receiver selection (dropdown)
- Content field
- Submit button

### Routes

**Inbox Route** (`/messages`)
- Requires authentication
- Lists received messages
- Shows unread count
- Displays sender information
- Message preview
- Read/unread styling
- Actions: Read, Delete

**Sent Route** (`/messages/sent`)
- Requires authentication
- Lists sent messages
- Shows recipient information
- Message preview
- Actions: Delete

**New Message Route** (`/messages/new`)
- Requires authentication
- Method: GET, POST
- Receiver selection dropdown
- Message composition
- Creates message
- Flash confirmation

**Read Message Route** (`/messages/<message_id>/read`)
- Requires authentication
- Marks message as read
- Redirects to inbox
- Only receiver can mark as read

**Delete Message Route** (`/messages/<message_id>/delete`)
- Requires authentication
- Deletes message
- Sender or receiver can delete
- Flash confirmation
- Redirects to inbox

## Message Features

### Inbox
- Lists all received messages
- Shows unread count
- Sender information with profile link
- Message preview (200 characters)
- Timestamp
- Read/unread visual distinction
- Actions: Read, Delete

### Sent Messages
- Lists all sent messages
- Shows recipient information
- Message preview
- Timestamp
- Actions: Delete

### Message Composition
- Select recipient from dropdown
- All users except self
- Message content
- No character limit
- Instant delivery

### Read Status
- Boolean flag
- Default: false (unread)
- Set to true when opened
- Used for unread count
- Only receiver can mark as read

## Message Metadata

### Sender
- Foreign key to User
- Relationship: sent_messages
- Cannot send to self
- Profile link displayed

### Receiver
- Foreign key to User
- Relationship: received_messages
- Can receive from anyone
- Profile link displayed

### Content
- Plain text content
- No Markdown processing
- No character limit
- No HTML allowed

### Timestamp
- Creation time
- Displayed in notifications
- Used for sorting

## Unread Count

### Calculation
```python
unread_count = current_user.received_messages.filter_by(is_read=False).count()
```

### Display
- Shown in navbar
- Envelope icon
- Magenta color badge
- Glowing effect
- Hidden when zero unread

## Templates

### Inbox Template (`message/inbox.html`)
- Hero section with unread count
- New message button
- Sent messages button
- Message list
- Read/unread styling
- Action links

### Sent Template (`message/sent.html`)
- Hero section
- Inbox button
- New message button
- Message list
- Message metadata
- Delete action

### New Message Template (`message/new_message.html`)
- Message composition form
- Receiver dropdown
- Content textarea
- Submit button
- Cancel link

## CSS Styling

### Message Item
- Dark card background
- Border glow
- Unread: Cyan border with glow
- Hover effects
- Smooth transitions

### Message Sender
- Magenta color
- Profile link
- Hover effect to cyan
- Text shadow on hover

### Message Content
- Primary text color
- Preview (200 chars)
- Truncation indicator
- Readable font

### Message Actions
- Cyan color for read
- Red color for delete
- Hover effects
- Transition animations

## Security Considerations

### Access Control
- Authentication required
- Users can only see their own messages
- Cannot send to self
- Sender/receiver validation

### Privacy
- Private between sender and receiver
- No public visibility
- Admin can view all messages (future audit)
- Message deletion is permanent

### Abuse Prevention
- Rate limiting (future)
- Spam detection (future)
- Block user feature (future)
- Report message feature (future)

## Integration Points

### Notification System (Future)
- New message notification
- Unread message count in notifications
- Push notifications

### User System
- Sender profile links
- Receiver profile links
- User dropdown for composition

## Performance Considerations

### Database Queries
- Filter by user_id (sent or received)
- Filter by is_read
- Order by created_at DESC
- Lazy loading for efficiency

### Future Optimizations
- Pagination for large lists
- Message archiving
- Indexed fields (sender_id, receiver_id, is_read)
- Message search
- Conversation threading

## Best Practices

### Message Content
- Be respectful and professional
- Keep messages concise
- Use clear subject lines (future)
- Avoid spam

### Message Management
- Regularly check inbox
- Delete old messages
- Mark important messages as unread (future)
- Archive important conversations (future)

### Privacy
- Don't share sensitive information
- Remember messages can be deleted
- Admin may audit messages (future)
- Report inappropriate messages (future)

## Future Enhancements

### Message Features
- Message threads/conversations
- Message search
- Message archiving
- Star/favorite messages
- Message drafts
- Rich text editing
- File attachments
- Message forwarding
- Reply quoting
- Message encryption
- Message expiration
- Message scheduling

### Communication Features
- Block user
- Mute user
- Report message
- Spam detection
- Auto-moderation
- Message analytics
- Typing indicators
- Read receipts
- Message delivery status
- Group messaging
- Broadcast messages (admin)

### Integration
- Email notifications
- Push notifications
- SMS notifications
- Desktop notifications
- Mobile app integration
