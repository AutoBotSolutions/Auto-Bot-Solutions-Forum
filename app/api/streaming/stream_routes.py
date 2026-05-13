"""
Streaming API Routes

Flask routes for real-time streaming management and monitoring.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# This would be initialized in the main app
streaming_bp = Blueprint('streaming', __name__, url_prefix='/api/streaming')

def init_streaming_routes(stream_handlers):
    """Initialize streaming routes with handlers"""
    
    @streaming_bp.route('/streams', methods=['GET'])
    def get_streams():
        """Get all available streams"""
        try:
            stream_type = request.args.get('type')
            
            streams = []
            if stream_type:
                from .stream_manager import StreamType
                try:
                    stream_type_enum = StreamType(stream_type)
                    streams = stream_handlers.stream_manager.get_streams_by_type(stream_type_enum)
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid stream type',
                        'message': f'No stream type found: {stream_type}'
                    }), 400
            else:
                streams = list(stream_handlers.stream_manager.streams.values())
            
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
                    'created_at': stream_info['created_at'],
                    'requires_auth': stream.config.requires_auth,
                    'max_subscribers': stream.config.max_subscribers
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'streams': stream_data,
                    'total': len(stream_data),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting streams: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/streams/<stream_id>', methods=['GET'])
    def get_stream_details(stream_id: str):
        """Get details for specific stream"""
        try:
            stream_stats = stream_handlers.stream_manager.get_stream_stats(stream_id)
            
            if not stream_stats:
                return jsonify({
                    'success': False,
                    'error': 'Stream not found',
                    'message': f'Stream {stream_id} does not exist'
                }), 404
            
            return jsonify({
                'success': True,
                'data': stream_stats
            })
        except Exception as e:
            logger.error(f"Error getting stream details: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/streams/<stream_id>/buffer', methods=['GET'])
    def get_stream_buffer(stream_id: str):
        """Get stream buffer data"""
        try:
            limit = request.args.get('limit', 50, type=int)
            
            buffer_data = stream_handlers.stream_manager.get_stream_buffer(stream_id, limit)
            
            return jsonify({
                'success': True,
                'data': {
                    'stream_id': stream_id,
                    'buffer': buffer_data,
                    'count': len(buffer_data),
                    'limit': limit,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting stream buffer: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/streams/<stream_id>/pause', methods=['POST'])
    def pause_stream(stream_id: str):
        """Pause a stream"""
        try:
            success = stream_handlers.stream_manager.pause_stream(stream_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'stream_id': stream_id,
                        'status': 'paused',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to pause stream',
                    'message': f'Could not pause stream {stream_id}'
                }), 400
        except Exception as e:
            logger.error(f"Error pausing stream: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/streams/<stream_id>/resume', methods=['POST'])
    def resume_stream(stream_id: str):
        """Resume a stream"""
        try:
            success = stream_handlers.stream_manager.resume_stream(stream_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'stream_id': stream_id,
                        'status': 'active',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to resume stream',
                    'message': f'Could not resume stream {stream_id}'
                }), 400
        except Exception as e:
            logger.error(f"Error resuming stream: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/streams/<stream_id>/stop', methods=['POST'])
    def stop_stream(stream_id: str):
        """Stop a stream"""
        try:
            success = stream_handlers.stream_manager.stop_stream(stream_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'stream_id': stream_id,
                        'status': 'stopped',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to stop stream',
                    'message': f'Could not stop stream {stream_id}'
                }), 400
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/streams/<stream_id>/broadcast', methods=['POST'])
    def broadcast_to_stream(stream_id: str):
        """Broadcast message to stream"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            message = data.get('message')
            event_type = data.get('event_type', 'update')
            metadata = data.get('metadata', {})
            
            if not message:
                return jsonify({
                    'success': False,
                    'error': 'Message is required'
                }), 400
            
            # Broadcast to stream
            delivered_count = stream_handlers.stream_manager.broadcast_to_stream(
                stream_id, message, event_type, metadata
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'stream_id': stream_id,
                    'delivered_count': delivered_count,
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting to stream: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/broadcast', methods=['POST'])
    def broadcast_to_all():
        """Broadcast message to all streams"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            message = data.get('message')
            event_type = data.get('event_type', 'update')
            metadata = data.get('metadata', {})
            
            if not message:
                return jsonify({
                    'success': False,
                    'error': 'Message is required'
                }), 400
            
            # Broadcast to all streams
            delivered_count = stream_handlers.stream_manager.broadcast_to_all(
                message, event_type, metadata
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'delivered_count': delivered_count,
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting to all streams: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/stats', methods=['GET'])
    def get_streaming_stats():
        """Get streaming system statistics"""
        try:
            stats = stream_handlers.get_stats()
            
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"Error getting streaming stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/health', methods=['GET'])
    def streaming_health():
        """Get streaming system health status"""
        try:
            stats = stream_handlers.get_stats()
            streaming_stats = stats.get('streaming', {}).get('global_stats', {})
            
            # Calculate health metrics
            active_streams = streaming_stats.get('active_streams', 0)
            total_subscribers = streaming_stats.get('total_subscribers', 0)
            total_messages = streaming_stats.get('total_messages', 0)
            
            health_status = 'healthy'
            issues = []
            warnings = []
            
            # Check for issues
            if active_streams == 0:
                health_status = 'warning'
                warnings.append("No active streams")
            
            if total_subscribers > 5000:
                health_status = 'warning'
                warnings.append(f"High number of subscribers: {total_subscribers}")
            
            if total_messages > 100000:
                health_status = 'warning'
                warnings.append(f"High message volume: {total_messages}")
            
            # Check subscription stats
            subscription_stats = stats.get('subscriptions', {}).get('subscription_stats', {})
            avg_delivery_rate = subscription_stats.get('avg_delivery_rate', 1.0)
            
            if avg_delivery_rate < 0.9:
                health_status = 'critical'
                issues.append(f"Low delivery rate: {avg_delivery_rate:.2%}")
            
            return jsonify({
                'success': True,
                'data': {
                    'health_status': health_status,
                    'metrics': {
                        'active_streams': active_streams,
                        'total_subscribers': total_subscribers,
                        'total_messages': total_messages,
                        'avg_delivery_rate': avg_delivery_rate
                    },
                    'issues': issues,
                    'warnings': warnings,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting streaming health: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/cleanup', methods=['POST'])
    def cleanup_streams():
        """Clean up inactive streams and subscribers"""
        try:
            data = request.get_json() or {}
            max_inactive_hours = data.get('max_inactive_hours', 24)
            max_inactive_minutes = data.get('max_inactive_minutes', 30)
            
            # Clean up streams
            cleaned_streams = stream_handlers.stream_manager.cleanup_inactive_streams(max_inactive_hours)
            
            # Clean up subscribers
            cleaned_subscribers = stream_handlers.stream_manager.cleanup_inactive_subscribers(max_inactive_minutes)
            
            # Clean up subscriptions
            cleaned_subscriptions = stream_handlers.subscription_manager.cleanup_expired_subscriptions()
            
            return jsonify({
                'success': True,
                'data': {
                    'cleaned_streams': cleaned_streams,
                    'cleaned_subscribers': cleaned_subscribers,
                    'cleaned_subscriptions': cleaned_subscriptions,
                    'max_inactive_hours': max_inactive_hours,
                    'max_inactive_minutes': max_inactive_minutes,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error cleaning up streams: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/subscriptions', methods=['GET'])
    def get_subscriptions():
        """Get all subscriptions"""
        try:
            user_id = request.args.get('user_id')
            
            if not user_id:
                return jsonify({
                    'success': False,
                    'error': 'User ID is required'
                }), 400
            
            subscriptions = stream_handlers.subscription_manager.get_user_subscriptions(int(user_id))
            
            subscription_data = []
            for subscription in subscriptions:
                subscription_data.append(subscription.to_dict())
            
            return jsonify({
                'success': True,
                'data': {
                    'user_id': user_id,
                    'subscriptions': subscription_data,
                    'total': len(subscription_data),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting subscriptions: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/subscriptions', methods=['POST'])
    def create_subscription():
        """Create new subscription"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({
                    'success': False,
                    'error': 'User ID is required'
                }), 400
            
            # Create subscription
            subscription_id = stream_handlers.subscription_manager.create_subscription_from_request(user_id, data)
            
            return jsonify({
                'success': True,
                'data': {
                    'subscription_id': subscription_id,
                    'user_id': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/subscriptions/<subscription_id>', methods=['GET'])
    def get_subscription_details(subscription_id: str):
        """Get subscription details"""
        try:
            subscription_stats = stream_handlers.subscription_manager.get_subscription_stats(subscription_id)
            
            if not subscription_stats:
                return jsonify({
                    'success': False,
                    'error': 'Subscription not found',
                    'message': f'Subscription {subscription_id} does not exist'
                }), 404
            
            return jsonify({
                'success': True,
                'data': subscription_stats
            })
        except Exception as e:
            logger.error(f"Error getting subscription details: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/subscriptions/<subscription_id>', methods=['PUT'])
    def update_subscription(subscription_id: str):
        """Update subscription"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            updates = data.get('updates', {})
            if not updates:
                return jsonify({
                    'success': False,
                    'error': 'Updates are required'
                }), 400
            
            success = stream_handlers.subscription_manager.update_subscription(subscription_id, updates)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'subscription_id': subscription_id,
                        'updates': updates,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update subscription',
                    'message': f'Could not update subscription {subscription_id}'
                }), 400
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/subscriptions/<subscription_id>', methods=['DELETE'])
    def cancel_subscription(subscription_id: str):
        """Cancel subscription"""
        try:
            success = stream_handlers.subscription_manager.cancel_subscription(subscription_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'subscription_id': subscription_id,
                        'status': 'cancelled',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to cancel subscription',
                    'message': f'Could not cancel subscription {subscription_id}'
                }), 400
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/config', methods=['GET'])
    def get_streaming_config():
        """Get streaming configuration"""
        try:
            config = {
                'streaming': {
                    'max_streams': 100,
                    'max_subscribers_per_stream': 1000,
                    'buffer_size': 100,
                    'cleanup_interval_hours': 24
                },
                'subscriptions': {
                    'max_subscriptions_per_user': 50,
                    'max_events_per_hour': 1000,
                    'auto_renew': True,
                    'cleanup_interval_hours': 1
                },
                'websocket': {
                    'heartbeat_interval': 30,
                    'max_connection_time': 3600,
                    'compression_enabled': True
                },
                'data_sources': {
                    'posts': 'Database query for recent posts',
                    'comments': 'Database query for recent comments',
                    'users': 'Database query for user activity',
                    'analytics': 'Analytics service data',
                    'notifications': 'Notification service data'
                }
            }
            
            return jsonify({
                'success': True,
                'data': config
            })
        except Exception as e:
            logger.error(f"Error getting streaming config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @streaming_bp.route('/events', methods=['GET'])
    def get_stream_events():
        """Get stream events"""
        try:
            stream_id = request.args.get('stream_id')
            event_type = request.args.get('event_type')
            limit = request.args.get('limit', 100, type=int)
            
            # Parse event type
            from .stream_events import StreamEventType
            event_type_enum = None
            if event_type:
                try:
                    event_type_enum = StreamEventType(event_type)
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid event type',
                        'message': f'No event type found: {event_type}'
                    }), 400
            
            events = stream_handlers.stream_events.get_stream_events(
                stream_id, event_type_enum, limit
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'events': events,
                    'count': len(events),
                    'limit': limit,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting stream events: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
