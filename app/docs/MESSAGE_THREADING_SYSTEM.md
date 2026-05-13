# Message Threading System

## Overview

The Message Threading System provides comprehensive conversation threading capabilities for private messages, enabling users to organize discussions into logical conversation threads with hierarchical reply chains, participant management, and advanced thread analytics.

## Features

### 🧵 **Threading Capabilities**
- **Conversation threading** with automatic thread creation
- **Hierarchical reply chains** with parent-child relationships
- **Thread tree visualization** with depth analysis
- **Thread participant management** with dynamic addition/removal
- **Thread statistics** with comprehensive metrics
- **Thread archiving** and cleanup automation

### 📊 **Thread Management**
- **Thread creation** with subject and participants
- **Thread editing** with participant updates
- **Thread pinning** for important conversations
- **Thread muting** to suppress notifications
- **Thread archiving** for organization
- **Thread statistics** and activity tracking

### 👥 **Participant Features**
- **Dynamic participant management** (add/remove users)
- **Participant suggestions** based on user relationships
- **Thread permissions** and access control
- **Participant activity** tracking
- **Thread type support** (private, group, system)

## Architecture

### Core Components

#### **MessageThreadingEngine** (`app/utils/message_threading.py`)
```python
class MessageThreadingEngine:
    """Advanced message threading engine with conversation management"""
    
    def create_thread(self, subject, participant_ids, creator_id, thread_type='private')
    def add_message_to_thread(self, message, thread_id=None, parent_message_id=None)
    def get_thread_messages(self, thread_id, user_id, include_deleted=False)
    def get_thread_tree(self, thread_id, user_id, max_depth=None)
    def get_user_threads(self, user_id, include_archived=False, thread_type=None)
    def update_thread_participants(self, thread_id, participant_ids, user_id)
    def get_thread_statistics(self, thread_id)
    def archive_thread(self, thread_id, user_id)
    def pin_thread(self, thread_id, user_id, pin=True)
    def mute_thread(self, thread_id, user_id, mute=True)
```

#### **MessageThread** (Database Model)
```python
class MessageThread(db.Model):
    """Model for conversation threading"""
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255))
    participant_ids = db.Column(db.Text)  # JSON array of user IDs
    last_message_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    # Thread statistics
    message_count = db.Column(db.Integer, default=0)
    unread_count = db.Column(db.Integer, default=0)
    
    # Thread settings
    is_archived = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_muted = db.Column(db.Boolean, default=False)
    
    # Thread metadata
    thread_type = db.Column(db.String(20), default='private')
    priority = db.Column(db.String(20), default='normal')
```

#### **Message Model Enhancements**
```python
class Message(db.Model):
    # ... existing fields ...
    
    # Threading fields
    thread_id = db.Column(db.Integer, db.ForeignKey('message_thread.id'))
    parent_message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    thread_level = db.Column(db.Integer, default=0)
    
    # Self-referential relationships
    parent_message = db.relationship('Message', remote_side=[id])
    thread = db.relationship('MessageThread', backref='messages')
```

## API Endpoints

### Thread Routes

#### **GET `/messages/threads`**
**List all threads for the current user**

**Parameters:**
- `type` (string): Filter by thread type ('private', 'group', 'system')
- `archived` (boolean): Include archived threads
- `sort` (string): Sort method ('last_message_at', 'message_count', 'created_at')
- `order` (string): Sort order ('asc', 'desc')
- `page` (integer): Page number
- `per_page` (integer): Results per page

**Response:**
```json
{
    "threads": [
        {
            "id": 1,
            "subject": "Project Discussion",
            "thread_type": "private",
            "priority": "normal",
            "message_count": 15,
            "unread_count": 3,
            "participants": [1, 2, 3],
            "last_message_at": "2024-01-01T12:00:00",
            "created_at": "2024-01-01T10:00:00",
            "is_archived": false,
            "is_pinned": false,
            "is_muted": false
        }
    ],
    "total": 25,
    "page": 1,
    "per_page": 20,
    "total_pages": 2
}
```

#### **GET `/messages/threads/<int:thread_id>`**
**View a specific thread with all messages**

**Response:**
```json
{
    "thread_tree": {
        "thread_id": 1,
        "messages": [
            {
                "id": 1,
                "sender_id": 1,
                "receiver_id": 2,
                "content": "Hello everyone!",
                "created_at": "2024-01-01T10:00:00",
                "is_read": true,
                "thread_level": 0,
                "replies": [
                    {
                        "id": 2,
                        "sender_id": 2,
                        "receiver_id": 1,
                        "content": "Hi there!",
                        "created_at": "2024-01-01T10:05:00",
                        "is_read": true,
                        "thread_level": 1,
                        "replies": []
                    }
                ]
            }
        ],
        "total_messages": 15
    },
    "thread_stats": {
        "thread_id": 1,
        "total_messages": 15,
        "participant_count": 3,
        "max_thread_depth": 4,
        "thread_duration_days": 5,
        "messages_per_day": 3.0
    },
    "participant_names": {
        "1": "john_doe",
        "2": "jane_smith",
        "3": "bob_wilson"
    }
}
```

#### **POST `/messages/threads/create`**
**Create a new message thread**

**Request Body:**
```json
{
    "subject": "New Project Discussion",
    "participants": [2, 3, 4],
    "thread_type": "private",
    "priority": "normal"
}
```

#### **POST `/messages/threads/<int:thread_id>/reply`**
**Reply to a message in a thread**

**Request Body:**
```json
{
    "receiver_id": 2,
    "content": "Thanks for the update!",
    "parent_message_id": 5
}
```

#### **POST `/messages/threads/<int:thread_id>/edit`**
**Edit thread settings and participants**

**Request Body:**
```json
{
    "subject": "Updated Thread Subject",
    "participants": [2, 3, 4, 5],
    "thread_type": "group",
    "priority": "high"
}
```

#### **GET `/messages/threads/<int:thread_id>/archive`**
**Archive or unarchive a thread**

#### **GET `/messages/threads/<int:thread_id>/pin`**
**Pin or unpin a thread**

#### **GET `/messages/threads/<int:thread_id>/mute`**
**Mute or unmute a thread**

#### **GET `/messages/threads/<int:thread_id>/statistics`**
**View detailed statistics for a thread**

**Response:**
```json
{
    "thread_stats": {
        "thread_id": 1,
        "subject": "Project Discussion",
        "total_messages": 15,
        "participant_count": 3,
        "participants": {
            "1": {
                "message_count": 8,
                "first_message": "2024-01-01T10:00:00",
                "last_message": "2024-01-01T15:00:00"
            },
            "2": {
                "message_count": 5,
                "first_message": "2024-01-01T10:05:00",
                "last_message": "2024-01-01T14:30:00"
            }
        },
        "max_thread_depth": 4,
        "depth_distribution": {
            "0": 3,
            "1": 7,
            "2": 4,
            "3": 1
        },
        "thread_duration_days": 5,
        "messages_per_day": 3.0
    },
    "activity_summary": {
        "thread_id": 1,
        "days_analyzed": 30,
        "total_messages": 15,
        "active_participants": [1, 2],
        "daily_activity": {
            "2024-01-01": 8,
            "2024-01-02": 5,
            "2024-01-03": 2
        },
        "messages_per_day": 0.5
    }
}
```

#### **GET `/messages/threads/suggestions`**
**Get participant suggestions for thread creation**

**Parameters:**
- `q` (string): Search query for usernames
- `limit` (integer): Maximum suggestions (default: 10)

**Response:**
```json
{
    "suggestions": [
        {
            "id": 2,
            "username": "jane_smith",
            "email": "jane@example.com"
        },
        {
            "id": 3,
            "username": "bob_wilson",
            "email": "bob@example.com"
        }
    ]
}
```

## Thread Types

### **Private Threads**
- One-on-one conversations between two users
- Automatically created when sending first message
- Limited to original participants

### **Group Threads**
- Conversations with three or more participants
- Manual creation with subject and participants
- Dynamic participant management

### **System Threads**
- System-generated notifications and announcements
- Read-only for most users
- Managed by administrators

## Thread Operations

### **Creating Threads**
```python
from app.utils.message_threading import MessageThreadingEngine

threading_engine = MessageThreadingEngine()
thread = threading_engine.create_thread(
    subject="Project Discussion",
    participant_ids=[1, 2, 3],
    creator_id=1,
    thread_type="group",
    priority="normal"
)
```

### **Adding Messages to Threads**
```python
# Add new message to thread
message = Message(
    sender_id=1,
    receiver_id=2,
    content="Hello everyone!"
)

threading_engine.add_message_to_thread(message, thread_id=1)

# Reply to specific message
threading_engine.add_message_to_thread(
    message, 
    thread_id=1, 
    parent_message_id=5
)
```

### **Managing Participants**
```python
# Add participant to thread
threading_engine.update_thread_participants(
    thread_id=1,
    participant_ids=[1, 2, 3, 4],  # New participant list
    user_id=1
)

# Get thread participants
participants = thread.get_participants()
```

### **Thread Statistics**
```python
# Get comprehensive thread statistics
stats = threading_engine.get_thread_statistics(thread_id=1)

print(f"Total messages: {stats['total_messages']}")
print(f"Participant count: {stats['participant_count']}")
print(f"Max thread depth: {stats['max_thread_depth']}")
print(f"Messages per day: {stats['messages_per_day']}")
```

## Thread Tree Structure

### **Hierarchical Organization**
Messages in threads are organized hierarchically based on reply relationships:

```
Thread: Project Discussion
├── Message 1 (Level 0) - "Hello everyone!"
│   ├── Message 2 (Level 1) - "Hi there!"
│   │   └── Message 4 (Level 2) - "Thanks!"
│   └── Message 3 (Level 1) - "Welcome!"
└── Message 5 (Level 0) - "Project update"
    └── Message 6 (Level 1) - "Sounds good!"
```

### **Thread Levels**
- **Level 0**: Root messages (start new conversation branches)
- **Level 1**: Direct replies to root messages
- **Level 2+**: Nested replies (maximum depth: 10)

## Database Schema

### **Message Model Enhancements**
```sql
ALTER TABLE message ADD COLUMN thread_id INTEGER REFERENCES message_thread(id);
ALTER TABLE message ADD COLUMN parent_message_id INTEGER REFERENCES message(id);
ALTER TABLE message ADD COLUMN thread_level INTEGER DEFAULT 0;
```

### **MessageThread Table**
```sql
CREATE TABLE message_thread (
    id INTEGER PRIMARY KEY,
    subject VARCHAR(255),
    participant_ids TEXT NOT NULL,  -- JSON array of user IDs
    last_message_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Thread statistics
    message_count INTEGER DEFAULT 0,
    unread_count INTEGER DEFAULT 0,
    
    -- Thread settings
    is_archived BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_muted BOOLEAN DEFAULT FALSE,
    
    -- Thread metadata
    thread_type VARCHAR(20) DEFAULT 'private',
    priority VARCHAR(20) DEFAULT 'normal'
);
```

## Utility Functions

### **Threading Utilities** (`app/utils/message_threading.py`)

#### **find_reply_chain(message_id, max_depth=10)**
Find the complete reply chain for a message.

```python
chain = find_reply_chain(message_id=5, max_depth=10)
# Returns list of messages from root to specified message
```

#### **get_thread_participant_names(thread_id)**
Get participant names for a thread.

```python
names = get_thread_participant_names(thread_id=1)
# Returns: {1: 'john_doe', 2: 'jane_smith'}
```

#### **suggest_thread_participants(user_id, query, limit=10)**
Suggest participants for thread creation.

```python
suggestions = suggest_thread_participants(
    user_id=1, 
    query="john", 
    limit=5
)
# Returns list of user suggestions matching query
```

#### **get_thread_activity_summary(thread_id, days=30)**
Get activity summary for a thread.

```python
activity = get_thread_activity_summary(thread_id=1, days=30)
# Returns daily activity statistics
```

## Performance Optimization

### **Thread Caching**
- Thread statistics caching for frequently accessed threads
- Participant list caching for large threads
- Thread tree structure caching for complex hierarchies

### **Database Optimization**
- Proper indexing on thread_id and parent_message_id
- Optimized queries for thread statistics
- Efficient participant management with JSON storage

### **Query Optimization**
- Lazy loading of thread messages
- Pagination for large thread lists
- Efficient thread tree building algorithms

## Security Considerations

### **Access Control**
- User-specific thread access (only participants can view threads)
- Thread permission validation for all operations
- Secure participant management (only thread creators can modify)

### **Data Privacy**
- Thread content isolation between users
- Secure participant data storage
- Thread analytics privacy protection

### **Input Validation**
- Thread subject validation and sanitization
- Participant ID validation
- Thread type and priority validation

## Usage Examples

### **Creating a Group Thread**
```python
from app.utils.message_threading import MessageThreadingEngine

threading_engine = MessageThreadingEngine()

# Create group thread
thread = threading_engine.create_thread(
    subject="Q1 Planning Meeting",
    participant_ids=[1, 2, 3, 4, 5],
    creator_id=1,
    thread_type="group",
    priority="high"
)

print(f"Thread created with ID: {thread.id}")
```

### **Replying in a Thread**
```python
# Create reply message
reply = Message(
    sender_id=2,
    receiver_id=1,
    content="I'll attend the meeting"
)

# Add reply to thread
threading_engine.add_message_to_thread(
    reply,
    thread_id=thread.id,
    parent_message_id=original_message.id
)
```

### **Getting Thread Tree**
```python
# Get hierarchical thread structure
thread_tree = threading_engine.get_thread_tree(
    thread_id=1,
    user_id=1,
    max_depth=5
)

print(f"Thread has {thread_tree['total_messages']} messages")
```

### **Managing Thread Participants**
```python
# Add new participant
current_participants = thread.get_participants()
current_participants.append(6)  # Add user 6

threading_engine.update_thread_participants(
    thread_id=1,
    participant_ids=current_participants,
    user_id=1  # Thread creator
)
```

### **Thread Analytics**
```python
# Get thread statistics
stats = threading_engine.get_thread_statistics(thread_id=1)

print(f"Messages per day: {stats['messages_per_day']}")
print(f"Thread depth: {stats['max_thread_depth']}")
print(f"Active participants: {len(stats['participants'])}")
```

## Troubleshooting

### **Common Issues**

#### **Thread Not Found**
- Verify thread ID exists
- Check user permissions for thread access
- Ensure thread is not archived

#### **Participant Management Issues**
- Verify user IDs are valid
- Check if user is already a participant
- Ensure thread creator permissions

#### **Thread Tree Issues**
- Check for circular references in parent_message_id
- Verify thread depth limits (max 10 levels)
- Ensure proper message ordering

### **Debug Mode**
Enable debug logging for threading operations:

```python
import logging
logging.getLogger('app.utils.message_threading').setLevel(logging.DEBUG)
```

## Migration Guide

### **Database Migration**
Run the migration script to add threading fields:

```bash
python migrate_message_system.py
```

### **Existing Message Migration**
Migrate existing messages to threads:

```python
from app.utils.message_threading import MessageThreadingEngine

threading_engine = MessageThreadingEngine()

# Create threads for existing message pairs
messages = Message.query.filter(Message.thread_id.is_(None)).all()
for message in messages:
    # Create thread for message pair
    thread = threading_engine.create_thread(
        subject=f"Conversation with {message.receiver.username}",
        participant_ids=[message.sender_id, message.receiver_id],
        creator_id=message.sender_id
    )
    
    # Add message to thread
    threading_engine.add_message_to_thread(message, thread.id)
```

## Future Enhancements

### **Planned Features**
- **Thread Templates** for common conversation types
- **Thread Categories** for better organization
- **Thread Search** within thread content
- **Thread Notifications** with customizable preferences
- **Thread Export** functionality

### **Performance Improvements**
- **Thread Preloading** for faster access
- **Real-time Thread Updates** with WebSocket
- **Thread Analytics Dashboard** with visualization
- **Smart Thread Suggestions** based on user behavior

---

**Documentation Version:** 1.0  
**Last Updated:** May 12, 2026  
**System:** Auto Bot Solutions Forum - Message Threading System
