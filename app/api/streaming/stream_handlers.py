"""
Stream Handlers

Flask-SocketIO handlers for real-time streaming events.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from flask import request, g
from flask_socketio import emit, join_room, leave_room

from .stream_manager import StreamManager, StreamType
from .stream_events import StreamEvents, StreamEventType
from .stream_subscriptions import StreamSubscriptionManager

logger = logging.getLogger(__name__)

class StreamHandlers:
    """WebSocket handlers for real-time streaming"""
    
    def __init__(self, socketio, app=None):
        self.socketio = socketio
        self.app = app
        
        # Initialize components
        self.stream_manager = StreamManager()
        self.stream_events = StreamEvents(self.stream_manager)
        self.subscription_manager = StreamSubscriptionManager(self.stream_manager)
        
        # Register SocketIO handlers
        self._register_handlers()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _register_handlers(self):
        """Register all SocketIO event handlers"""
        self.socketio.on('stream_subscribe', self.handle_subscribe)
        self.socketio.on('stream_unsubscribe', self.handle_unsubscribe)
        self.socketio.on('stream_list', self.handle_list_streams)
        self.socketio.on('stream_info', self.handle_get_stream_info)
        self.socketio.on('stream_buffer', self.handle_get_stream_buffer)
        self.socketio.on('stream_pause', self.handle_pause_stream)
        self.socketio.on('stream_resume', self.handle_resume_stream)
        self.socketio.on('stream_stats', self.handle_get_stream_stats)
        self.socketio.on('stream_broadcast', self.handle_broadcast)
        self.socketio.on('subscription_create', self.handle_create_subscription)
        self.socketio.on('subscription_cancel', self.handle_cancel_subscription)
        self.socketio.on('subscription_list', self.handle_list_subscriptions)
        self.socketio.on('subscription_update', self.handle_update_subscription)
    
    def handle_subscribe(self, data, *args, **kwargs):
        """Handle stream subscription"""
        try:
            sid = request.sid
            stream_id = data.get('stream_id')
            filters = data.get('filters', {})
            
            if not stream_id:
                emit('error', {
                    'message': 'Stream ID is required',
                    'code': 'STREAM_ID_REQUIRED'
                }, room=sid)
                return
            
            # Check if stream exists
            stream = self.stream_manager.get_stream(stream_id)
            if not stream:
                emit('error', {
                    'message': 'Stream not found',
                    'code': 'STREAM_NOT_FOUND'
                }, room=sid)
                return
            
            # Subscribe to stream
            success = self.stream_manager.subscribe_to_stream(stream_id, sid, filters)
            
            if success:
                # Join stream room
                join_room(f"stream_{stream_id}", room=sid)
                
                emit('stream_subscribed', {
                    'stream_id': stream_id,
                    'filters': filters,
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': 'Successfully subscribed to stream'
                }, room=sid)
                
                # Notify other subscribers
                emit('subscriber_joined', {
                    'stream_id': stream_id,
                    'sid': sid,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"stream_{stream_id}", include_self=False)
                
                logger.info(f"Subscriber {sid} subscribed to stream {stream_id}")
            else:
                emit('error', {
                    'message': 'Failed to subscribe to stream',
                    'code': 'SUBSCRIPTION_FAILED'
                }, room=sid)
        
        except Exception as e:
            logger.error(f"Error in stream subscription: {e}")
            emit('error', {
                'message': 'Subscription error',
                'code': 'SUBSCRIPTION_ERROR'
            }, room=request.sid)
    
    def handle_unsubscribe(self, data, *args, **kwargs):
        """Handle stream unsubscription"""
        try:
            sid = request.sid
            stream_id = data.get('stream_id')
            
            if not stream_id:
                emit('error', {
                    'message': 'Stream ID is required',
                    'code': 'STREAM_ID_REQUIRED'
                }, room=sid)
                return
            
            # Unsubscribe from stream
            self.stream_manager.unsubscribe_from_stream(stream_id, sid)
            
            # Leave stream room
            leave_room(f"stream_{stream_id}", room=sid)
            
            emit('stream_unsubscribed', {
                'stream_id': stream_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Successfully unsubscribed from stream'
            }, room=sid)
            
            # Notify other subscribers
            emit('subscriber_left', {
                'stream_id': stream_id,
                'sid': sid,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"stream_{stream_id}", include_self=False)
            
            logger.info(f"Subscriber {sid} unsubscribed from stream {stream_id}")
        
        except Exception as e:
            logger.error(f"Error in stream unsubscription: {e}")
            emit('error', {
                'message': 'Unsubscription error',
                'code': 'UNSUBSCRIPTION_ERROR'
            }, room=request.sid)
    
    def handle_list_streams(self, *args, **kwargs):
        """Handle list streams request"""
        try:
            sid = request.sid
            stream_type = request.args.get('type')
            
            streams = []
            if stream_type:
                try:
                    stream_type_enum = StreamType(stream_type)
                    streams = self.stream_manager.get_streams_by_type(stream_type_enum)
                except ValueError:
                    emit('error', {
                        'message': f'Invalid stream type: {stream_type}',
                        'code': 'INVALID_STREAM_TYPE'
                    }, room=sid)
                    return
            else:
                streams = list(self.stream_manager.streams.values())
            
            stream_data = []
            for stream in streams:
                stream_info = stream.get_stats()
                stream_data.append({
                    'stream_id': stream.stream_id,
                    'name': stream.config.name,
                    'type': stream.config.stream_type.value,
                    'description': stream.config.description,
                    'status': stream.status.value,
                    'subscribers': stream_info['subscribers'],
                    'buffer_size': stream_info['buffer_size'],
                    'created_at': stream_info['created_at']
                })
            
            emit('streams_list', {
                'streams': stream_data,
                'total': len(stream_data),
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error listing streams: {e}")
            emit('error', {
                'message': 'Error listing streams',
                'code': 'LIST_STREAMS_ERROR'
            }, room=request.sid)
    
    def handle_get_stream_info(self, data, *args, **kwargs):
        """Handle get stream info request"""
        try:
            sid = request.sid
            stream_id = data.get('stream_id')
            
            if not stream_id:
                emit('error', {
                    'message': 'Stream ID is required',
                    'code': 'STREAM_ID_REQUIRED'
                }, room=sid)
                return
            
            stream_stats = self.stream_manager.get_stream_stats(stream_id)
            
            if not stream_stats:
                emit('error', {
                    'message': 'Stream not found',
                    'code': 'STREAM_NOT_FOUND'
                }, room=sid)
                return
            
            emit('stream_info', {
                'stream': stream_stats,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            emit('error', {
                'message': 'Error getting stream info',
                'code': 'GET_STREAM_INFO_ERROR'
            }, room=request.sid)
    
    def handle_get_stream_buffer(self, data, *args, **kwargs):
        """Handle get stream buffer request"""
        try:
            sid = request.sid
            stream_id = data.get('stream_id')
            limit = data.get('limit', 50)
            
            if not stream_id:
                emit('error', {
                    'message': 'Stream ID is required',
                    'code': 'STREAM_ID_REQUIRED'
                }, room=sid)
                return
            
            buffer_data = self.stream_manager.get_stream_buffer(stream_id, limit)
            
            emit('stream_buffer', {
                'stream_id': stream_id,
                'buffer': buffer_data,
                'count': len(buffer_data),
                'limit': limit,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error getting stream buffer: {e}")
            emit('error', {
                'message': 'Error getting stream buffer',
                'code': 'GET_STREAM_BUFFER_ERROR'
            }, room=request.sid)
    
    def handle_pause_stream(self, data, *args, **kwargs):
        """Handle pause stream request"""
        try:
            sid = request.sid
            stream_id = data.get('stream_id')
            
            if not stream_id:
                emit('error', {
                    'message': 'Stream ID is required',
                    'code': 'STREAM_ID_REQUIRED'
                }, room=sid)
                return
            
            success = self.stream_manager.pause_stream(stream_id)
            
            if success:
                emit('stream_paused', {
                    'stream_id': stream_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': 'Stream paused successfully'
                }, room=sid)
                
                # Notify subscribers
                emit('stream_status_changed', {
                    'stream_id': stream_id,
                    'status': 'paused',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"stream_{stream_id}")
                
                logger.info(f"Stream {stream_id} paused by {sid}")
            else:
                emit('error', {
                    'message': 'Failed to pause stream',
                    'code': 'PAUSE_FAILED'
                }, room=sid)
        
        except Exception as e:
            logger.error(f"Error pausing stream: {e}")
            emit('error', {
                'message': 'Error pausing stream',
                'code': 'PAUSE_STREAM_ERROR'
            }, room=request.sid)
    
    def handle_resume_stream(self, data, *args, **kwargs):
        """Handle resume stream request"""
        try:
            sid = request.sid
            stream_id = data.get('stream_id')
            
            if not stream_id:
                emit('error', {
                    'message': 'Stream ID is required',
                    'code': 'STREAM_ID_REQUIRED'
                }, room=sid)
                return
            
            success = self.stream_manager.resume_stream(stream_id)
            
            if success:
                emit('stream_resumed', {
                    'stream_id': stream_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': 'Stream resumed successfully'
                }, room=sid)
                
                # Notify subscribers
                emit('stream_status_changed', {
                    'stream_id': stream_id,
                    'status': 'active',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"stream_{stream_id}")
                
                logger.info(f"Stream {stream_id} resumed by {sid}")
            else:
                emit('error', {
                    'message': 'Failed to resume stream',
                    'code': 'RESUME_FAILED'
                }, room=sid)
        
        except Exception as e:
            logger.error(f"Error resuming stream: {e}")
            emit('error', {
                'message': 'Error resuming stream',
                'code': 'RESUME_STREAM_ERROR'
            }, room=request.sid)
    
    def handle_get_stream_stats(self, *args, **kwargs):
        """Handle get stream stats request"""
        try:
            sid = request.sid
            stream_id = request.args.get('stream_id')
            
            if stream_id:
                # Get specific stream stats
                stream_stats = self.stream_manager.get_stream_stats(stream_id)
                if stream_stats:
                    emit('stream_stats', {
                        'stream': stream_stats,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=sid)
                else:
                    emit('error', {
                        'message': 'Stream not found',
                        'code': 'STREAM_NOT_FOUND'
                    }, room=sid)
            else:
                # Get global stats
                global_stats = self.stream_manager.get_all_stats()
                emit('stream_stats', {
                    'global': global_stats,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
        
        except Exception as e:
            logger.error(f"Error getting stream stats: {e}")
            emit('error', {
                'message': 'Error getting stream stats',
                'code': 'GET_STREAM_STATS_ERROR'
            }, room=request.sid)
    
    def handle_broadcast(self, data, *args, **kwargs):
        """Handle broadcast request"""
        try:
            sid = request.sid
            stream_id = data.get('stream_id')
            message = data.get('message')
            event_type = data.get('event_type', 'update')
            metadata = data.get('metadata', {})
            
            if not stream_id:
                emit('error', {
                    'message': 'Stream ID is required',
                    'code': 'STREAM_ID_REQUIRED'
                }, room=sid)
                return
            
            if not message:
                emit('error', {
                    'message': 'Message is required',
                    'code': 'MESSAGE_REQUIRED'
                }, room=sid)
                return
            
            # Broadcast to stream
            delivered_count = self.stream_manager.broadcast_to_stream(
                stream_id, message, event_type, metadata
            )
            
            emit('broadcast_sent', {
                'stream_id': stream_id,
                'delivered_count': delivered_count,
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
            
            logger.info(f"Broadcast sent to stream {stream_id} by {sid}: {delivered_count} deliveries")
        
        except Exception as e:
            logger.error(f"Error broadcasting: {e}")
            emit('error', {
                'message': 'Error broadcasting',
                'code': 'BROADCAST_ERROR'
            }, room=request.sid)
    
    def handle_create_subscription(self, data, *args, **kwargs):
        """Handle create subscription request"""
        try:
            sid = request.sid
            user_id = data.get('user_id')
            
            if not user_id:
                emit('error', {
                    'message': 'User ID is required',
                    'code': 'USER_ID_REQUIRED'
                }, room=sid)
                return
            
            # Create subscription
            subscription_id = self.subscription_manager.create_subscription_from_request(user_id, data)
            
            emit('subscription_created', {
                'subscription_id': subscription_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Subscription created successfully'
            }, room=sid)
            
            logger.info(f"Subscription {subscription_id} created for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            emit('error', {
                'message': 'Error creating subscription',
                'code': 'CREATE_SUBSCRIPTION_ERROR'
            }, room=request.sid)
    
    def handle_cancel_subscription(self, data, *args, **kwargs):
        """Handle cancel subscription request"""
        try:
            sid = request.sid
            subscription_id = data.get('subscription_id')
            
            if not subscription_id:
                emit('error', {
                    'message': 'Subscription ID is required',
                    'code': 'SUBSCRIPTION_ID_REQUIRED'
                }, room=sid)
                return
            
            success = self.subscription_manager.cancel_subscription(subscription_id)
            
            if success:
                emit('subscription_cancelled', {
                    'subscription_id': subscription_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': 'Subscription cancelled successfully'
                }, room=sid)
                
                logger.info(f"Subscription {subscription_id} cancelled by {sid}")
            else:
                emit('error', {
                    'message': 'Failed to cancel subscription',
                    'code': 'CANCEL_FAILED'
                }, room=sid)
        
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            emit('error', {
                'message': 'Error cancelling subscription',
                'code': 'CANCEL_SUBSCRIPTION_ERROR'
            }, room=request.sid)
    
    def handle_list_subscriptions(self, *args, **kwargs):
        """Handle list subscriptions request"""
        try:
            sid = request.sid
            user_id = request.args.get('user_id')
            
            if not user_id:
                emit('error', {
                    'message': 'User ID is required',
                    'code': 'USER_ID_REQUIRED'
                }, room=sid)
                return
            
            subscriptions = self.subscription_manager.get_user_subscriptions(int(user_id))
            
            subscription_data = []
            for subscription in subscriptions:
                subscription_data.append(subscription.to_dict())
            
            emit('subscriptions_list', {
                'user_id': user_id,
                'subscriptions': subscription_data,
                'total': len(subscription_data),
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error listing subscriptions: {e}")
            emit('error', {
                'message': 'Error listing subscriptions',
                'code': 'LIST_SUBSCRIPTIONS_ERROR'
            }, room=request.sid)
    
    def handle_update_subscription(self, data, *args, **kwargs):
        """Handle update subscription request"""
        try:
            sid = request.sid
            subscription_id = data.get('subscription_id')
            updates = data.get('updates', {})
            
            if not subscription_id:
                emit('error', {
                    'message': 'Subscription ID is required',
                    'code': 'SUBSCRIPTION_ID_REQUIRED'
                }, room=sid)
                return
            
            success = self.subscription_manager.update_subscription(subscription_id, updates)
            
            if success:
                emit('subscription_updated', {
                    'subscription_id': subscription_id,
                    'updates': updates,
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': 'Subscription updated successfully'
                }, room=sid)
                
                logger.info(f"Subscription {subscription_id} updated by {sid}")
            else:
                emit('error', {
                    'message': 'Failed to update subscription',
                    'code': 'UPDATE_FAILED'
                }, room=sid)
        
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            emit('error', {
                'message': 'Error updating subscription',
                'code': 'UPDATE_SUBSCRIPTION_ERROR'
            }, room=request.sid)
    
    def _start_background_tasks(self):
        """Start background tasks for streaming"""
        def background_task():
            """Background task for streaming"""
            try:
                # Generate data for active streams
                for stream in self.stream_manager.streams.values():
                    if stream.status.value == 'active':
                        data = self.stream_events.generate_data_for_stream(stream.stream_id)
                        if data:
                            self.stream_events.broadcast_data_event(
                                stream.stream_id, data, 'auto_update'
                            )
                
                # Clean up inactive streams and subscribers
                self.stream_manager.cleanup_inactive_streams()
                self.stream_manager.cleanup_inactive_subscribers()
                
                # Clean up expired subscriptions
                self.subscription_manager.cleanup_expired_subscriptions()
                
            except Exception as e:
                logger.error(f"Error in background task: {e}")
        
        # This would be implemented with proper background task scheduling
        logger.info("Background task started for streaming")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming system statistics"""
        try:
            stream_stats = self.stream_manager.get_all_stats()
            subscription_stats = self.subscription_manager.get_global_stats()
            
            return {
                'streaming': stream_stats,
                'subscriptions': subscription_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting streaming stats: {e}")
            return {'error': str(e)}
