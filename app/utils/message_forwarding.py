"""
Message Forwarding and Sharing Utilities

Provides comprehensive message forwarding functionality including:
- Message forwarding with tracking
- Message sharing options
- Message export capabilities
- Message quoting features
- Message citation system
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import current_app
from app import db
from app.models import Message, MessageForward, User


class MessageForwardingManager:
    """Advanced message forwarding manager with tracking and analytics"""
    
    def __init__(self):
        self.max_forward_chain_length = 10
        self.forward_note_max_length = 500
    
    def forward_message(self, original_message_id: int, forward_to_id: int, 
                       forward_by_id: int, forward_note: str = None) -> Tuple[bool, Dict]:
        """
        Forward a message to another user
        
        Args:
            original_message_id: ID of original message to forward
            forward_to_id: ID of user to forward to
            forward_by_id: ID of user forwarding the message
            forward_note: Optional note to include with forwarded message
            
        Returns:
            Tuple of (success, result)
        """
        result = {
            'success': False,
            'forwarded_message_id': None,
            'forward_id': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Get original message
            original_message = Message.query.get(original_message_id)
            if not original_message:
                result['errors'].append('Original message not found')
                return False, result
            
            # Check permissions
            if original_message.sender_id != forward_by_id and original_message.receiver_id != forward_by_id:
                result['errors'].append('You can only forward messages you are involved in')
                return False, result
            
            # Check forward chain length
            if self._get_forward_chain_length(original_message) >= self.max_forward_chain_length:
                result['warnings'].append('Message has been forwarded many times')
            
            # Validate forward note
            if forward_note and len(forward_note) > self.forward_note_max_length:
                result['errors'].append(f'Forward note too long (max {self.forward_note_max_length} characters)')
                return False, result
            
            # Check if user is trying to forward to themselves
            if forward_to_id == forward_by_id:
                result['errors'].append('Cannot forward message to yourself')
                return False, result
            
            # Create forwarded message
            forwarded_content = self._create_forwarded_content(original_message, forward_note)
            
            forwarded_message = Message(
                sender_id=forward_by_id,
                receiver_id=forward_to_id,
                content=forwarded_content['content'],
                content_html=forwarded_content.get('html'),
                content_format=forwarded_content.get('format', 'text'),
                is_rich_text=forwarded_content.get('is_rich_text', False),
                forwarded_from_id=original_message_id,
                priority=original_message.priority
            )
            
            db.session.add(forwarded_message)
            db.session.flush()  # Get the ID
            
            # Create forward record
            forward_record = MessageForward(
                original_message_id=original_message_id,
                forwarded_message_id=forwarded_message.id,
                forwarded_by_id=forward_by_id,
                forwarded_to_id=forward_to_id,
                forward_note=forward_note,
                forward_chain_length=self._get_forward_chain_length(original_message) + 1
            )
            
            db.session.add(forward_record)
            
            # Update original message forward count
            original_message.forwarded_count += 1
            
            db.session.commit()
            
            result['success'] = True
            result['forwarded_message_id'] = forwarded_message.id
            result['forward_id'] = forward_record.id
            
            return True, result
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error forwarding message: {e}")
            result['errors'].append(f'Forwarding failed: {str(e)}')
            return False, result
    
    def _create_forwarded_content(self, original_message: Message, forward_note: str = None) -> Dict:
        """
        Create content for forwarded message
        
        Args:
            original_message: Original message to forward
            forward_note: Optional forward note
            
        Returns:
            Dictionary with content information
        """
        # Build forwarded content
        content_parts = []
        
        # Add forward note if provided
        if forward_note:
            content_parts.append(f"Forward Note: {forward_note}")
            content_parts.append("---")
        
        # Add original message content with attribution
        original_sender = User.query.get(original_message.sender_id)
        sender_name = original_sender.username if original_sender else "Unknown"
        
        content_parts.append(f"--- Forwarded message from {sender_name} ---")
        content_parts.append(original_message.content)
        
        # Add original message info
        original_date = original_message.created_at.strftime("%Y-%m-%d %H:%M")
        content_parts.append(f"--- Original sent: {original_date} ---")
        
        content = "\n".join(content_parts)
        
        return {
            'content': content,
            'format': 'text',
            'is_rich_text': False
        }
    
    def _get_forward_chain_length(self, message: Message) -> int:
        """
        Get the length of the forward chain for a message
        
        Args:
            message: Message to check
            
        Returns:
            Length of forward chain
        """
        if message.forwarded_from_id:
            # Count forwards in chain
            chain_length = 1
            current_message = message
            
            while current_message.forwarded_from_id and chain_length < self.max_forward_chain_length:
                current_message = Message.query.get(current_message.forwarded_from_id)
                if not current_message:
                    break
                chain_length += 1
            
            return chain_length
        
        return 0
    
    def get_forward_history(self, message_id: int, user_id: int) -> List[Dict]:
        """
        Get forward history for a message
        
        Args:
            message_id: ID of message
            user_id: ID of user requesting history
            
        Returns:
            List of forward records
        """
        # Check if user has permission to view this message
        message = Message.query.get(message_id)
        if not message or (message.sender_id != user_id and message.receiver_id != user_id):
            return []
        
        # Get forward records
        forwards = MessageForward.query.filter_by(original_message_id=message_id).order_by(
            MessageForward.created_at.desc()
        ).all()
        
        forward_history = []
        for forward in forwards:
            forwarder = User.query.get(forward.forwarded_by_id)
            recipient = User.query.get(forward.forwarded_to_id)
            
            forward_history.append({
                'id': forward.id,
                'forwarded_by': forwarder.username if forwarder else "Unknown",
                'forwarded_to': recipient.username if recipient else "Unknown",
                'forward_note': forward.forward_note,
                'forward_chain_length': forward.forward_chain_length,
                'created_at': forward.created_at.isoformat()
            })
        
        return forward_history
    
    def get_user_forwards(self, user_id: int, page: int = 1, per_page: int = 20) -> Dict:
        """
        Get all forwards made by a user
        
        Args:
            user_id: ID of user
            page: Page number
            per_page: Results per page
            
        Returns:
            Dictionary with forwards and pagination info
        """
        forwards = MessageForward.query.filter_by(forwarded_by_id=user_id).order_by(
            MessageForward.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        forwards_data = []
        for forward in forwards.items:
            original_message = Message.query.get(forward.original_message_id)
            forwarded_message = Message.query.get(forward.forwarded_message_id)
            recipient = User.query.get(forward.forwarded_to_id)
            
            forwards_data.append({
                'id': forward.id,
                'original_message': {
                    'id': original_message.id,
                    'content': original_message.content[:100] + "..." if len(original_message.content) > 100 else original_message.content,
                    'sender_id': original_message.sender_id,
                    'created_at': original_message.created_at.isoformat()
                },
                'forwarded_to': recipient.username if recipient else "Unknown",
                'forward_note': forward.forward_note,
                'forward_chain_length': forward.forward_chain_length,
                'created_at': forward.created_at.isoformat()
            })
        
        return {
            'forwards': forwards_data,
            'total': forwards.total,
            'page': forwards.page,
            'per_page': per_page,
            'total_pages': forwards.pages
        }
    
    def get_user_received_forwards(self, user_id: int, page: int = 1, per_page: int = 20) -> Dict:
        """
        Get all forwards received by a user
        
        Args:
            user_id: ID of user
            page: Page number
            per_page: Results per page
            
        Returns:
            Dictionary with forwards and pagination info
        """
        forwards = MessageForward.query.filter_by(forwarded_to_id=user_id).order_by(
            MessageForward.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        forwards_data = []
        for forward in forwards.items:
            original_message = Message.query.get(forward.original_message_id)
            forwarded_message = Message.query.get(forward.forwarded_message_id)
            forwarder = User.query.get(forward.forwarded_by_id)
            
            forwards_data.append({
                'id': forward.id,
                'original_message': {
                    'id': original_message.id,
                    'content': original_message.content[:100] + "..." if len(original_message.content) > 100 else original_message.content,
                    'sender_id': original_message.sender_id,
                    'created_at': original_message.created_at.isoformat()
                },
                'forwarded_by': forwarder.username if forwarder else "Unknown",
                'forward_note': forward.forward_note,
                'forward_chain_length': forward.forward_chain_length,
                'created_at': forward.created_at.isoformat()
            })
        
        return {
            'forwards': forwards_data,
            'total': forwards.total,
            'page': forwards.page,
            'per_page': per_page,
            'total_pages': forwards.pages
        }
    
    def quote_message(self, message_id: int, user_id: int, quote_style: str = 'standard') -> Dict:
        """
        Create a quote from a message
        
        Args:
            message_id: ID of message to quote
            user_id: ID of user quoting the message
            quote_style: Style of quote ('standard', 'markdown', 'html')
            
        Returns:
            Dictionary with quote information
        """
        result = {
            'success': False,
            'quote': None,
            'errors': []
        }
        
        try:
            # Get message
            message = Message.query.get(message_id)
            if not message:
                result['errors'].append('Message not found')
                return result
            
            # Check permissions
            if message.sender_id != user_id and message.receiver_id != user_id:
                result['errors'].append('You can only quote messages you are involved in')
                return result
            
            # Get sender info
            sender = User.query.get(message.sender_id)
            sender_name = sender.username if sender else "Unknown"
            
            # Create quote based on style
            if quote_style == 'standard':
                quote = f"> {sender_name} wrote:\n> {message.content}"
            elif quote_style == 'markdown':
                quote = f"> **{sender_name} wrote:**\n> {message.content}"
            elif quote_style == 'html':
                quote = f"<blockquote><p><strong>{sender_name} wrote:</strong></p><p>{message.content}</p></blockquote>"
            else:
                quote = f"> {sender_name} wrote:\n> {message.content}"
            
            result['success'] = True
            result['quote'] = quote
            result['original_message_id'] = message_id
            result['sender_name'] = sender_name
            result['original_content'] = message.content
            result['created_at'] = message.created_at.isoformat()
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error creating quote: {e}")
            result['errors'].append(f'Quote creation failed: {str(e)}')
            return result
    
    def export_message(self, message_id: int, user_id: int, export_format: str = 'json') -> Dict:
        """
        Export a message in various formats
        
        Args:
            message_id: ID of message to export
            user_id: ID of user exporting the message
            export_format: Export format ('json', 'txt', 'html', 'markdown')
            
        Returns:
            Dictionary with export information
        """
        result = {
            'success': False,
            'export': None,
            'errors': []
        }
        
        try:
            # Get message
            message = Message.query.get(message_id)
            if not message:
                result['errors'].append('Message not found')
                return result
            
            # Check permissions
            if message.sender_id != user_id and message.receiver_id != user_id:
                result['errors'].append('You can only export messages you are involved in')
                return result
            
            # Get sender and receiver info
            sender = User.query.get(message.sender_id)
            receiver = User.query.get(message.receiver_id)
            
            # Create export based on format
            if export_format == 'json':
                export_data = {
                    'id': message.id,
                    'sender': sender.username if sender else "Unknown",
                    'receiver': receiver.username if receiver else "Unknown",
                    'content': message.content,
                    'content_html': message.content_html,
                    'content_format': message.content_format,
                    'created_at': message.created_at.isoformat(),
                    'is_read': message.is_read,
                    'priority': message.priority
                }
            elif export_format == 'txt':
                export_data = f"Message ID: {message.id}\n"
                export_data += f"From: {sender.username if sender else 'Unknown'}\n"
                export_data += f"To: {receiver.username if receiver else 'Unknown'}\n"
                export_data += f"Date: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                export_data += f"Priority: {message.priority}\n"
                export_data += f"Read: {'Yes' if message.is_read else 'No'}\n"
                export_data += f"\n{message.content}"
            elif export_format == 'html':
                export_data = f"<div class='message-export'>"
                export_data += f"<h3>Message from {sender.username if sender else 'Unknown'}</h3>"
                export_data += f"<p><strong>To:</strong> {receiver.username if receiver else 'Unknown'}</p>"
                export_data += f"<p><strong>Date:</strong> {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>"
                export_data += f"<p><strong>Priority:</strong> {message.priority}</p>"
                export_data += f"<div class='message-content'>"
                if message.content_html:
                    export_data += message.content_html
                else:
                    export_data += f"<p>{message.content}</p>"
                export_data += f"</div></div>"
            elif export_format == 'markdown':
                export_data = f"# Message from {sender.username if sender else 'Unknown'}\n\n"
                export_data += f"**To:** {receiver.username if receiver else 'Unknown'}  \n"
                export_data += f"**Date:** {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}  \n"
                export_data += f"**Priority:** {message.priority}  \n"
                export_data += f"**Read:** {'Yes' if message.is_read else 'No'}  \n\n"
                export_data += f"{message.content}"
            else:
                result['errors'].append('Invalid export format')
                return result
            
            result['success'] = True
            result['export'] = export_data
            result['format'] = export_format
            result['filename'] = f"message_{message_id}_{export_format}"
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error exporting message: {e}")
            result['errors'].append(f'Export failed: {str(e)}')
            return result
    
    def get_forwarding_analytics(self, user_id: int = None, days: int = 30) -> Dict:
        """
        Get forwarding analytics
        
        Args:
            user_id: User ID (None for all users)
            days: Number of days to analyze
            
        Returns:
            Analytics dictionary
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = MessageForward.query.filter(MessageForward.created_at >= start_date)
        
        if user_id:
            query = query.filter(
                (MessageForward.forwarded_by_id == user_id) |
                (MessageForward.forwarded_to_id == user_id)
            )
        
        forwards = query.all()
        
        # Calculate analytics
        total_forwards = len(forwards)
        forwards_by_user = {}
        forwards_by_chain_length = {}
        daily_forwards = {}
        
        for forward in forwards:
            # Count by user
            if user_id is None:
                forwarder_id = forward.forwarded_by_id
                forwards_by_user[forwarder_id] = forwards_by_user.get(forwarder_id, 0) + 1
            
            # Count by chain length
            chain_length = forward.forward_chain_length
            forwards_by_chain_length[chain_length] = forwards_by_chain_length.get(chain_length, 0) + 1
            
            # Count by day
            day_key = forward.created_at.strftime('%Y-%m-%d')
            daily_forwards[day_key] = daily_forwards.get(day_key, 0) + 1
        
        # Most forwarded messages
        most_forwarded = {}
        for forward in forwards:
            msg_id = forward.original_message_id
            most_forwarded[msg_id] = most_forwarded.get(msg_id, 0) + 1
        
        most_forwarded_list = sorted(most_forwarded.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_forwards': total_forwards,
            'forwards_by_user': forwards_by_user,
            'forwards_by_chain_length': forwards_by_chain_length,
            'daily_forwards': daily_forwards,
            'most_forwarded_messages': most_forwarded_list,
            'days_analyzed': days
        }


def forward_message(original_message_id: int, forward_to_id: int, forward_by_id: int, forward_note: str = None) -> Tuple[bool, Dict]:
    """
    Forward a message (convenience function)
    
    Args:
        original_message_id: ID of original message to forward
        forward_to_id: ID of user to forward to
        forward_by_id: ID of user forwarding the message
        forward_note: Optional forward note
        
    Returns:
        Tuple of (success, result)
    """
    manager = MessageForwardingManager()
    return manager.forward_message(original_message_id, forward_to_id, forward_by_id, forward_note)


def create_message_quote(message_id: int, user_id: int, quote_style: str = 'standard') -> Dict:
    """
    Create a quote from a message (convenience function)
    
    Args:
        message_id: ID of message to quote
        user_id: ID of user quoting the message
        quote_style: Style of quote
        
    Returns:
        Dictionary with quote information
    """
    manager = MessageForwardingManager()
    return manager.quote_message(message_id, user_id, quote_style)


def export_message(message_id: int, user_id: int, export_format: str = 'json') -> Dict:
    """
    Export a message (convenience function)
    
    Args:
        message_id: ID of message to export
        user_id: ID of user exporting the message
        export_format: Export format
        
    Returns:
        Dictionary with export information
    """
    manager = MessageForwardingManager()
    return manager.export_message(message_id, user_id, export_format)
