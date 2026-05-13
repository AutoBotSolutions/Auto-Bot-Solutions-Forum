"""
Message Threading Utilities

Provides comprehensive conversation threading functionality including:
- Thread creation and management
- Message reply chains
- Thread statistics and analytics
- Thread archiving and cleanup
- Thread notifications
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from flask import current_app
from sqlalchemy import text, or_, and_, func, desc
from app import db
from app.models import Message, MessageThread, User


class MessageThreadingEngine:
    """Advanced message threading engine with conversation management"""
    
    def __init__(self):
        self.max_thread_depth = 10  # Maximum nesting level for threads
        self.thread_archive_days = 365  # Auto-archive threads older than this
    
    def create_thread(
        self,
        subject: str,
        participant_ids: List[int],
        creator_id: int,
        thread_type: str = 'private',
        priority: str = 'normal'
    ) -> MessageThread:
        """
        Create a new message thread
        
        Args:
            subject: Thread subject
            participant_ids: List of participant user IDs
            creator_id: User ID creating the thread
            thread_type: Type of thread ('private', 'group', 'system')
            priority: Thread priority ('low', 'normal', 'high', 'urgent')
        
        Returns:
            Created MessageThread object
        """
        # Validate participants
        if creator_id not in participant_ids:
            participant_ids.append(creator_id)
        
        # Create thread
        thread = MessageThread(
            subject=subject,
            thread_type=thread_type,
            priority=priority
        )
        thread.set_participants(participant_ids)
        
        db.session.add(thread)
        db.session.commit()
        
        return thread
    
    def add_message_to_thread(
        self,
        message: Message,
        thread_id: Optional[int] = None,
        parent_message_id: Optional[int] = None
    ) -> Message:
        """
        Add a message to a thread with proper threading relationships
        
        Args:
            message: Message object to add
            thread_id: Thread ID (optional, will infer from parent if not provided)
            parent_message_id: Parent message ID for replies
        
        Returns:
            Updated message object
        """
        if parent_message_id:
            # This is a reply to an existing message
            parent_message = Message.query.get(parent_message_id)
            if not parent_message:
                raise ValueError("Parent message not found")
            
            # Set thread from parent
            thread_id = parent_message.thread_id
            
            # Calculate thread level
            thread_level = parent_message.thread_level + 1
            if thread_level > self.max_thread_depth:
                thread_level = self.max_thread_depth
            
            message.parent_message_id = parent_message_id
            message.thread_level = thread_level
        elif thread_id:
            # Direct thread assignment
            thread_level = 0
        else:
            # No thread specified, create new thread
            thread = self.create_thread(
                subject=message.content[:100] + "..." if len(message.content) > 100 else message.content,
                participant_ids=[message.sender_id, message.receiver_id],
                creator_id=message.sender_id
            )
            thread_id = thread.id
            thread_level = 0
        
        # Set thread and level
        message.thread_id = thread_id
        message.thread_level = thread_level
        
        # Update thread statistics
        self._update_thread_statistics(thread_id)
        
        return message
    
    def get_thread_messages(
        self,
        thread_id: int,
        user_id: int,
        include_deleted: bool = False,
        sort_by: str = 'created_at',
        sort_order: str = 'asc'
    ) -> List[Message]:
        """
        Get all messages in a thread for a user
        
        Args:
            thread_id: Thread ID
            user_id: User ID requesting messages
            include_deleted: Include deleted messages
            sort_by: Sort field ('created_at', 'thread_level', 'sender')
            sort_order: Sort order ('asc', 'desc')
        
        Returns:
            List of Message objects
        """
        # Verify user is participant in thread
        thread = MessageThread.query.get(thread_id)
        if not thread:
            raise ValueError("Thread not found")
        
        if user_id not in thread.get_participants():
            raise ValueError("User not authorized to view this thread")
        
        # Build query
        query = Message.query.filter(
            Message.thread_id == thread_id,
            Message.sender_id == user_id,
            Message.receiver_id == user_id
        )
        
        if not include_deleted:
            query = query.filter(Message.is_deleted == False)
        
        # Apply sorting
        if sort_by == 'thread_level':
            order_column = Message.thread_level
        elif sort_by == 'sender':
            order_column = Message.sender_id
        else:
            order_column = Message.created_at
        
        if sort_order == 'desc':
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
        
        return query.all()
    
    def get_thread_tree(
        self,
        thread_id: int,
        user_id: int,
        max_depth: Optional[int] = None
    ) -> Dict:
        """
        Get thread as a hierarchical tree structure
        
        Args:
            thread_id: Thread ID
            user_id: User ID requesting thread
            max_depth: Maximum depth to traverse
        
        Returns:
            Thread tree structure
        """
        messages = self.get_thread_messages(thread_id, user_id, sort_by='created_at')
        
        if not messages:
            return {}
        
        # Build message tree
        root_messages = []
        message_dict = {msg.id: msg for msg in messages}
        
        for message in messages:
            if message.parent_message_id is None:
                root_messages.append(message)
            else:
                parent = message_dict.get(message.parent_message_id)
                if parent:
                    if not hasattr(parent, 'replies'):
                        parent.replies = []
                    parent.replies.append(message)
        
        # Build tree structure
        def build_tree_node(message, depth=0):
            if max_depth and depth >= max_depth:
                return None
            
            node = {
                'id': message.id,
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read,
                'thread_level': message.thread_level,
                'replies': []
            }
            
            if hasattr(message, 'replies'):
                for reply in message.replies:
                    child_node = build_tree_node(reply, depth + 1)
                    if child_node:
                        node['replies'].append(child_node)
            
            return node
        
        tree = [build_tree_node(msg) for msg in root_messages]
        
        return {
            'thread_id': thread_id,
            'messages': tree,
            'total_messages': len(messages)
        }
    
    def get_user_threads(
        self,
        user_id: int,
        include_archived: bool = False,
        thread_type: Optional[str] = None,
        sort_by: str = 'last_message_at',
        sort_order: str = 'desc',
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """
        Get all threads for a user with pagination
        
        Args:
            user_id: User ID
            include_archived: Include archived threads
            thread_type: Filter by thread type
            sort_by: Sort field
            sort_order: Sort order
            page: Page number
            per_page: Results per page
        
        Returns:
            Dictionary with thread list and pagination info
        """
        # Build base query
        query = MessageThread.query.filter(
            MessageThread.participant_ids.like(f'%{user_id}%')
        )
        
        if not include_archived:
            query = query.filter(MessageThread.is_archived == False)
        
        if thread_type:
            query = query.filter(MessageThread.thread_type == thread_type)
        
        # Count total
        total = query.count()
        
        # Apply sorting
        if sort_by == 'message_count':
            order_column = MessageThread.message_count
        elif sort_by == 'created_at':
            order_column = MessageThread.created_at
        else:
            order_column = MessageThread.last_message_at
        
        if sort_order == 'desc':
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
        
        # Apply pagination
        threads = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Process threads
        processed_threads = []
        for thread in threads:
            participants = thread.get_participants()
            unread_count = self._get_unread_count(thread.id, user_id)
            
            processed_thread = {
                'id': thread.id,
                'subject': thread.subject,
                'thread_type': thread.thread_type,
                'priority': thread.priority,
                'message_count': thread.message_count,
                'unread_count': unread_count,
                'participants': participants,
                'last_message_at': thread.last_message_at.isoformat(),
                'created_at': thread.created_at.isoformat(),
                'is_archived': thread.is_archived,
                'is_pinned': thread.is_pinned,
                'is_muted': thread.is_muted
            }
            processed_threads.append(processed_thread)
        
        return {
            'threads': processed_threads,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    
    def update_thread_participants(
        self,
        thread_id: int,
        participant_ids: List[int],
        user_id: int
    ) -> MessageThread:
        """
        Update thread participants
        
        Args:
            thread_id: Thread ID
            participant_ids: New list of participant IDs
            user_id: User making the change
        
        Returns:
            Updated thread object
        """
        thread = MessageThread.query.get(thread_id)
        if not thread:
            raise ValueError("Thread not found")
        
        # Check if user is authorized
        current_participants = thread.get_participants()
        if user_id not in current_participants:
            raise ValueError("User not authorized to modify this thread")
        
        # Update participants
        thread.set_participants(participant_ids)
        db.session.commit()
        
        return thread
    
    def archive_thread(self, thread_id: int, user_id: int) -> bool:
        """
        Archive a thread for a user
        
        Args:
            thread_id: Thread ID
            user_id: User ID
        
        Returns:
            Success status
        """
        thread = MessageThread.query.get(thread_id)
        if not thread:
            return False
        
        # Check if user is participant
        participants = thread.get_participants()
        if user_id not in participants:
            return False
        
        thread.is_archived = True
        db.session.commit()
        
        return True
    
    def pin_thread(self, thread_id: int, user_id: int, pin: bool = True) -> bool:
        """
        Pin or unpin a thread
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            pin: True to pin, False to unpin
        
        Returns:
            Success status
        """
        thread = MessageThread.query.get(thread_id)
        if not thread:
            return False
        
        # Check if user is participant
        participants = thread.get_participants()
        if user_id not in participants:
            return False
        
        thread.is_pinned = pin
        db.session.commit()
        
        return True
    
    def mute_thread(self, thread_id: int, user_id: int, mute: bool = True) -> bool:
        """
        Mute or unmute a thread
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            mute: True to mute, False to unmute
        
        Returns:
            Success status
        """
        thread = MessageThread.query.get(thread_id)
        if not thread:
            return False
        
        # Check if user is participant
        participants = thread.get_participants()
        if user_id not in participants:
            return False
        
        thread.is_muted = mute
        db.session.commit()
        
        return True
    
    def get_thread_statistics(self, thread_id: int) -> Dict:
        """
        Get comprehensive statistics for a thread
        
        Args:
            thread_id: Thread ID
        
        Returns:
            Thread statistics dictionary
        """
        thread = MessageThread.query.get(thread_id)
        if not thread:
            return {}
        
        # Get message statistics
        messages = Message.query.filter(Message.thread_id == thread_id).all()
        
        # Participant statistics
        participants = thread.get_participants()
        participant_stats = {}
        
        for participant_id in participants:
            user_messages = [msg for msg in messages if msg.sender_id == participant_id]
            participant_stats[participant_id] = {
                'message_count': len(user_messages),
                'first_message': min(user_messages, key=lambda x: x.created_at).created_at.isoformat() if user_messages else None,
                'last_message': max(user_messages, key=lambda x: x.created_at).created_at.isoformat() if user_messages else None
            }
        
        # Thread depth analysis
        max_depth = max([msg.thread_level for msg in messages]) if messages else 0
        depth_distribution = {}
        
        for message in messages:
            depth = message.thread_level
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
        
        # Time-based statistics
        if messages:
            first_message = min(messages, key=lambda x: x.created_at)
            last_message = max(messages, key=lambda x: x.created_at)
            thread_duration = last_message.created_at - first_message.created_at
            
            # Messages per day
            if thread_duration.days > 0:
                messages_per_day = len(messages) / thread_duration.days
            else:
                messages_per_day = len(messages)
        else:
            thread_duration = timedelta(0)
            messages_per_day = 0
        
        return {
            'thread_id': thread_id,
            'subject': thread.subject,
            'total_messages': len(messages),
            'participant_count': len(participants),
            'participants': participant_stats,
            'max_thread_depth': max_depth,
            'depth_distribution': depth_distribution,
            'thread_duration_days': thread_duration.days,
            'messages_per_day': round(messages_per_day, 2),
            'created_at': thread.created_at.isoformat(),
            'last_message_at': thread.last_message_at.isoformat(),
            'is_archived': thread.is_archived,
            'is_pinned': thread.is_pinned,
            'is_muted': thread.is_muted
        }
    
    def cleanup_old_threads(self, days: Optional[int] = None) -> int:
        """
        Archive old threads automatically
        
        Args:
            days: Number of days before archiving (uses default if not provided)
        
        Returns:
            Number of threads archived
        """
        if days is None:
            days = self.thread_archive_days
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find inactive threads
        inactive_threads = MessageThread.query.filter(
            MessageThread.last_message_at < cutoff_date,
            MessageThread.is_archived == False
        ).all()
        
        archived_count = 0
        for thread in inactive_threads:
            thread.is_archived = True
            archived_count += 1
        
        db.session.commit()
        
        return archived_count
    
    def _update_thread_statistics(self, thread_id: int):
        """Update thread statistics after message addition"""
        thread = MessageThread.query.get(thread_id)
        if not thread:
            return
        
        # Update message count
        thread.message_count = Message.query.filter(Message.thread_id == thread_id).count()
        
        # Update last message time
        last_message = Message.query.filter(Message.thread_id == thread_id).order_by(Message.created_at.desc()).first()
        if last_message:
            thread.last_message_at = last_message.created_at
        
        # Update unread count (simplified - would need per-user tracking in real implementation)
        thread.unread_count = 0
        
        db.session.commit()
    
    def _get_unread_count(self, thread_id: int, user_id: int) -> int:
        """Get unread message count for a user in a thread"""
        return Message.query.filter(
            Message.thread_id == thread_id,
            Message.receiver_id == user_id,
            Message.is_read == False,
            Message.is_deleted == False
        ).count()


def find_reply_chain(message_id: int, max_depth: int = 10) -> List[Message]:
    """
    Find the complete reply chain for a message
    
    Args:
        message_id: Starting message ID
        max_depth: Maximum depth to traverse
    
    Returns:
        List of messages in reply chain (oldest to newest)
    """
    chain = []
    current_message = Message.query.get(message_id)
    
    if not current_message:
        return chain
    
    # Traverse up the chain to find the root
    while current_message and len(chain) < max_depth:
        chain.insert(0, current_message)  # Insert at beginning for chronological order
        
        if current_message.parent_message_id:
            current_message = Message.query.get(current_message.parent_message_id)
        else:
            break
    
    return chain


def get_thread_participant_names(thread_id: int) -> Dict[int, str]:
    """
    Get participant names for a thread
    
    Args:
        thread_id: Thread ID
    
    Returns:
        Dictionary mapping user IDs to usernames
    """
    thread = MessageThread.query.get(thread_id)
    if not thread:
        return {}
    
    participant_ids = thread.get_participants()
    users = User.query.filter(User.id.in_(participant_ids)).all()
    
    return {user.id: user.username for user in users}


def suggest_thread_participants(user_id: int, query: str, limit: int = 10) -> List[Dict]:
    """
    Suggest participants for a new thread based on username search
    
    Args:
        user_id: Current user ID (excluded from results)
        query: Search query
        limit: Maximum results
    
    Returns:
        List of user suggestions
    """
    users = User.query.filter(
        User.id != user_id,
        User.username.ilike(f'%{query}%'),
        User.is_active == True
    ).limit(limit).all()
    
    return [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        for user in users
    ]


def get_thread_activity_summary(thread_id: int, days: int = 30) -> Dict:
    """
    Get activity summary for a thread over specified period
    
    Args:
        thread_id: Thread ID
        days: Number of days to analyze
    
    Returns:
        Activity summary dictionary
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    messages = Message.query.filter(
        Message.thread_id == thread_id,
        Message.created_at >= start_date
    ).all()
    
    if not messages:
        return {
            'thread_id': thread_id,
            'days_analyzed': days,
            'total_messages': 0,
            'active_participants': [],
            'daily_activity': {}
        }
    
    # Daily activity
    daily_activity = {}
    for message in messages:
        date_key = message.created_at.strftime('%Y-%m-%d')
        daily_activity[date_key] = daily_activity.get(date_key, 0) + 1
    
    # Active participants
    active_participants = list(set([msg.sender_id for msg in messages]))
    
    return {
        'thread_id': thread_id,
        'days_analyzed': days,
        'total_messages': len(messages),
        'active_participants': active_participants,
        'daily_activity': daily_activity,
        'messages_per_day': round(len(messages) / days, 2)
    }
