"""
Reputation and Voting Service

This module provides the core business logic for the enhanced voting and reputation system,
including reputation calculations, weighted voting, voting analytics, and pattern detection.
"""

from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, desc, asc
from flask import current_app
import math
import json
from typing import Dict, List, Optional, Tuple

from app import db
from app.models import User, Post, Comment
from .models import UserReputation, VoteHistory, VotingPattern, ReputationLevel

class ReputationService:
    """Service for managing user reputation calculations and levels"""
    
    def __init__(self):
        self.reputation_factors = {
            'post_upvote': 10,
            'post_downvote': -5,
            'comment_upvote': 5,
            'comment_downvote': -2,
            'post_creation': 2,
            'comment_creation': 1,
            'daily_activity': 1,
            'streak_bonus': 5,
            'quality_bonus': 15,
            'controversy_penalty': -3,
            'spam_penalty': -50
        }
        
        self.decay_factors = {
            'daily': 0.98,
            'weekly': 0.9,
            'monthly': 0.7
        }
    
    def get_user_reputation(self, user_id: int) -> Optional[UserReputation]:
        """Get or create user reputation record"""
        reputation = UserReputation.query.filter_by(user_id=user_id).first()
        if not reputation:
            reputation = UserReputation(user_id=user_id)
            db.session.add(reputation)
            db.session.commit()
        return reputation
    
    def calculate_reputation(self, user_id: int, recalculate: bool = False) -> Dict:
        """Calculate comprehensive reputation score for a user"""
        reputation = self.get_user_reputation(user_id)
        
        if not recalculate and reputation.last_calculated > datetime.utcnow() - timedelta(hours=1):
            return reputation.to_dict()
        
        # Get user's voting history and content
        vote_history = VoteHistory.query.filter_by(user_id=user_id).all()
        user_posts = Post.query.filter_by(user_id=user_id).all()
        user_comments = Comment.query.filter_by(user_id=user_id).all()
        
        # Calculate base reputation from votes received
        base_reputation = self._calculate_base_reputation(vote_history)
        
        # Calculate activity score
        activity_score = self._calculate_activity_score(user_posts, user_comments)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(vote_history, user_posts, user_comments)
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(user_id)
        
        # Apply time decay
        time_decay = self._calculate_time_decay(user_id)
        
        # Calculate final reputation
        final_reputation = int((base_reputation + activity_score + quality_score + consistency_score) * time_decay)
        
        # Update reputation record
        reputation.reputation_score = max(-1000, min(10000, final_reputation))
        reputation.voting_power = self._calculate_voting_power(reputation.reputation_score)
        reputation.trust_score = self._calculate_trust_score(reputation)
        reputation.total_votes_cast = len(vote_history)
        reputation.upvotes_given = len([v for v in vote_history if v.vote_type == 'upvote'])
        reputation.downvotes_given = len([v for v in vote_history if v.vote_type == 'downvote'])
        reputation.votes_received = len([v for v in vote_history if v.target_type in ['post', 'comment']])
        reputation.helpful_votes_received = len([v for v in vote_history if v.reason_category == 'helpful'])
        reputation.controversial_votes = len([v for v in vote_history if v.reason_category == 'controversial'])
        reputation.posts_created = len(user_posts)
        reputation.comments_created = len(user_comments)
        reputation.last_calculated = datetime.utcnow()
        
        # Update reputation level
        self._update_reputation_level(reputation)
        
        db.session.commit()
        
        return reputation.to_dict()
    
    def _calculate_base_reputation(self, vote_history: List[VoteHistory]) -> int:
        """Calculate base reputation from votes received"""
        score = 0
        
        for vote in vote_history:
            if vote.target_type in ['post', 'comment']:
                # This is a vote received on user's content
                if vote.vote_type == 'upvote':
                    if vote.target_type == 'post':
                        score += self.reputation_factors['post_upvote']
                    else:
                        score += self.reputation_factors['comment_upvote']
                else:
                    if vote.target_type == 'post':
                        score += self.reputation_factors['post_downvote']
                    else:
                        score += self.reputation_factors['comment_downvote']
        
        return score
    
    def _calculate_activity_score(self, posts: List[Post], comments: List[Comment]) -> int:
        """Calculate activity score from content creation"""
        score = 0
        
        # Points for posts and comments
        score += len(posts) * self.reputation_factors['post_creation']
        score += len(comments) * self.reputation_factors['comment_creation']
        
        # Daily activity bonus
        active_days = len(set(
            p.created_at.date() for p in posts + comments
        ))
        score += active_days * self.reputation_factors['daily_activity']
        
        return score
    
    def _calculate_quality_score(self, vote_history: List[VoteHistory], 
                              posts: List[Post], comments: List[Comment]) -> int:
        """Calculate quality score based on content quality"""
        score = 0
        
        # Quality bonuses for helpful votes
        helpful_votes = len([v for v in vote_history if v.reason_category == 'helpful'])
        score += helpful_votes * self.reputation_factors['quality_bonus']
        
        # Controversy penalties
        controversial_votes = len([v for v in vote_history if v.reason_category == 'controversial'])
        score += controversial_votes * self.reputation_factors['controversy_penalty']
        
        # Content length and quality indicators
        for post in posts:
            if len(post.content) > 500:  # Long, thoughtful posts
                score += 2
            if post.upvotes > post.downvotes * 2:  # Well-received posts
                score += 3
        
        for comment in comments:
            if len(comment.content) > 100:  # Substantial comments
                score += 1
            if comment.upvotes > comment.downvotes * 2:  # Well-received comments
                score += 2
        
        return score
    
    def _calculate_consistency_score(self, user_id: int) -> int:
        """Calculate consistency score based on activity patterns"""
        # Get last 30 days of activity
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_activity = VoteHistory.query.filter(
            VoteHistory.user_id == user_id,
            VoteHistory.created_at >= thirty_days_ago
        ).all()
        
        if not recent_activity:
            return 0
        
        # Calculate activity consistency
        activity_days = len(set(v.created_at.date() for v in recent_activity))
        consistency_ratio = activity_days / 30.0
        
        # Streak calculation
        current_streak = self._calculate_current_streak(user_id)
        
        score = int(consistency_ratio * 10) + (current_streak * self.reputation_factors['streak_bonus'])
        
        return score
    
    def _calculate_current_streak(self, user_id: int) -> int:
        """Calculate current activity streak"""
        reputation = self.get_user_reputation(user_id)
        
        # Check if user was active today
        today = date.today()
        if reputation.last_activity_date == today:
            return reputation.current_streak
        elif reputation.last_activity_date == today - timedelta(days=1):
            return reputation.current_streak
        else:
            # Streak broken
            reputation.current_streak = 0
            reputation.last_activity_date = today
            db.session.commit()
            return 0
    
    def _calculate_time_decay(self, user_id: int) -> float:
        """Calculate time decay factor for reputation"""
        # Get user's last activity
        last_activity = db.session.query(
            func.max(VoteHistory.created_at)
        ).filter_by(user_id=user_id).scalar()
        
        if not last_activity:
            return 1.0
        
        days_inactive = (datetime.utcnow() - last_activity).days
        
        if days_inactive <= 7:
            return self.decay_factors['daily'] ** days_inactive
        elif days_inactive <= 30:
            return self.decay_factors['weekly'] ** (days_inactive // 7)
        else:
            return self.decay_factors['monthly'] ** (days_inactive // 30)
    
    def _calculate_voting_power(self, reputation_score: int) -> float:
        """Calculate voting power based on reputation score"""
        # Base voting power ranges from 0.1 to 10.0
        if reputation_score < 0:
            return 0.1
        elif reputation_score < 100:
            return 0.5 + (reputation_score / 100) * 0.5
        elif reputation_score < 500:
            return 1.0 + ((reputation_score - 100) / 400) * 1.0
        elif reputation_score < 1000:
            return 2.0 + ((reputation_score - 500) / 500) * 1.0
        elif reputation_score < 2500:
            return 3.0 + ((reputation_score - 1000) / 1500) * 2.0
        else:
            return 5.0 + min(5.0, (reputation_score - 2500) / 1000)
    
    def _calculate_trust_score(self, reputation: UserReputation) -> float:
        """Calculate trust score based on various factors"""
        # Base trust score from reputation level
        level_multiplier = {
            'Newcomer': 0.1,
            'Member': 0.3,
            'Trusted': 0.6,
            'Expert': 0.8,
            'Master': 0.9,
            'Legend': 1.0
        }
        
        base_trust = level_multiplier.get(reputation.current_level, 0.1)
        
        # Adjust based on voting patterns
        if reputation.total_votes_cast > 0:
            consensus_ratio = reputation.consensus_votes / reputation.total_votes_cast
            base_trust *= (0.5 + 0.5 * consensus_ratio)
        
        # Adjust based on controversy
        if reputation.total_votes_cast > 0:
            controversy_ratio = reputation.controversial_votes / reputation.total_votes_cast
            base_trust *= (1.0 - 0.3 * controversy_ratio)
        
        # Adjust based on penalties
        if reputation.penalty_points > 0:
            penalty_factor = max(0.1, 1.0 - (reputation.penalty_points / 100))
            base_trust *= penalty_factor
        
        return max(0.0, min(1.0, base_trust))
    
    def _update_reputation_level(self, reputation: UserReputation):
        """Update user's reputation level based on score"""
        level = ReputationLevel.get_level_for_reputation(reputation.reputation_score)
        
        if level and level.level_name != reputation.current_level:
            reputation.current_level = level.level_name
            reputation.voting_power *= level.voting_power_multiplier
            
            # Calculate progress to next level
            if level.max_reputation < 10000:  # Not the highest level
                next_level = ReputationLevel.query.filter(
                    ReputationLevel.min_reputation == level.max_reputation + 1
                ).first()
                if next_level:
                    progress = (reputation.reputation_score - level.min_reputation) / (level.max_reputation - level.min_reputation)
                    reputation.level_progress = max(0.0, min(1.0, progress))
            else:
                reputation.level_progress = 1.0

class VotingService:
    """Service for handling voting operations and analytics"""
    
    def __init__(self):
        self.reason_categories = [
            'helpful', 'informative', 'well_written', 'accurate', 'comprehensive',
            'controversial', 'offensive', 'spam', 'duplicate', 'off_topic',
            'unclear', 'incomplete', 'outdated', 'biased', 'low_quality'
        ]
    
    def cast_vote(self, user_id: int, target_type: str, target_id: int, 
                  vote_type: str, reason: str = None, reason_category: str = None) -> Dict:
        """Cast a vote and update reputation"""
        # Validate input
        if vote_type not in ['upvote', 'downvote']:
            return {'success': False, 'error': 'Invalid vote type'}
        
        if target_type not in ['post', 'comment']:
            return {'success': False, 'error': 'Invalid target type'}
        
        # Get target object
        target = self._get_target_object(target_type, target_id)
        if not target:
            return {'success': False, 'error': 'Target not found'}
        
        # Check if user can vote
        can_vote, error = self._can_user_vote(user_id, target_type, target_id)
        if not can_vote:
            return {'success': False, 'error': error}
        
        # Get user reputation for weighted voting
        reputation_service = ReputationService()
        user_reputation = reputation_service.get_user_reputation(user_id)
        vote_weight = user_reputation.voting_power
        
        # Check for existing vote
        existing_vote = VoteHistory.query.filter_by(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            revoked_at=None
        ).first()
        
        if existing_vote:
            # Update existing vote
            if existing_vote.vote_type == vote_type:
                return {'success': False, 'error': 'Already voted this way'}
            
            # Change vote
            old_vote_type = existing_vote.vote_type
            existing_vote.vote_type = vote_type
            existing_vote.reason = reason
            existing_vote.reason_category = reason_category
            existing_vote.vote_weight = vote_weight
            existing_vote.modified_at = datetime.utcnow()
            
            # Update target vote counts
            if old_vote_type == 'upvote':
                target.upvotes -= 1
            else:
                target.downvotes -= 1
            
            if vote_type == 'upvote':
                target.upvotes += 1
            else:
                target.downvotes += 1
            
            # Update target author reputation
            self._update_target_author_reputation(target, vote_type, old_vote_type, vote_weight)
            
        else:
            # Create new vote
            vote = VoteHistory(
                user_id=user_id,
                vote_type=vote_type,
                target_type=target_type,
                target_id=target_id,
                reason=reason,
                reason_category=reason_category,
                vote_weight=vote_weight,
                reputation_impact=self._calculate_reputation_impact(vote_type, vote_weight)
            )
            
            db.session.add(vote)
            
            # Update target vote counts
            if vote_type == 'upvote':
                target.upvotes += 1
            else:
                target.downvotes += 1
            
            # Update target author reputation
            self._update_target_author_reputation(target, vote_type, None, vote_weight)
        
        db.session.commit()
        
        # Recalculate voter reputation
        reputation_service.calculate_reputation(user_id, recalculate=True)
        
        return {
            'success': True,
            'vote_type': vote_type,
            'vote_weight': vote_weight,
            'target_upvotes': target.upvotes,
            'target_downvotes': target.downvotes
        }
    
    def _get_target_object(self, target_type: str, target_id: int):
        """Get the target object for voting"""
        if target_type == 'post':
            return Post.query.get(target_id)
        elif target_type == 'comment':
            return Comment.query.get(target_id)
        return None
    
    def _can_user_vote(self, user_id: int, target_type: str, target_id: int) -> Tuple[bool, str]:
        """Check if user can vote on target"""
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found'
        
        # Get target object
        target = self._get_target_object(target_type, target_id)
        if not target:
            return False, 'Target not found'
        
        # Check if user is voting on their own content
        if target.user_id == user_id:
            return False, 'Cannot vote on your own content'
        
        # Check daily vote limit
        reputation_service = ReputationService()
        user_reputation = reputation_service.get_user_reputation(user_id)
        level = ReputationLevel.get_level_for_reputation(user_reputation.reputation_score)
        
        if level:
            today_votes = VoteHistory.query.filter(
                VoteHistory.user_id == user_id,
                VoteHistory.created_at >= datetime.utcnow().date()
            ).count()
            
            if today_votes >= level.daily_vote_limit:
                return False, 'Daily vote limit exceeded'
        
        return True, ''
    
    def _calculate_reputation_impact(self, vote_type: str, vote_weight: float) -> float:
        """Calculate reputation impact of a vote"""
        base_impact = 10.0 if vote_type == 'upvote' else -5.0
        return base_impact * vote_weight
    
    def _update_target_author_reputation(self, target, new_vote_type: str, 
                                        old_vote_type: str, vote_weight: float):
        """Update target author's reputation"""
        if old_vote_type:
            # Remove old vote impact
            old_impact = self._calculate_reputation_impact(old_vote_type, vote_weight)
            self._adjust_author_reputation(target.user_id, -old_impact)
        
        # Add new vote impact
        new_impact = self._calculate_reputation_impact(new_vote_type, vote_weight)
        self._adjust_author_reputation(target.user_id, new_impact)
    
    def _adjust_author_reputation(self, author_id: int, impact: float):
        """Adjust author's reputation by impact amount"""
        reputation = ReputationService().get_user_reputation(author_id)
        reputation.reputation_score = max(-1000, min(10000, reputation.reputation_score + int(impact)))
        reputation.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_voting_analytics(self, user_id: int, days: int = 30) -> Dict:
        """Get voting analytics for a user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        votes = VoteHistory.query.filter(
            VoteHistory.user_id == user_id,
            VoteHistory.created_at >= start_date
        ).all()
        
        if not votes:
            return {
                'total_votes': 0,
                'upvotes': 0,
                'downvotes': 0,
                'vote_weight_avg': 0.0,
                'most_voted_day': None,
                'reason_categories': {},
                'voting_patterns': {}
            }
        
        # Basic statistics
        total_votes = len(votes)
        upvotes = len([v for v in votes if v.vote_type == 'upvote'])
        downvotes = len([v for v in votes if v.vote_type == 'downvote'])
        vote_weight_avg = sum(v.vote_weight for v in votes) / total_votes
        
        # Voting by day
        votes_by_day = {}
        for vote in votes:
            day = vote.created_at.date()
            votes_by_day[day] = votes_by_day.get(day, 0) + 1
        
        most_voted_day = max(votes_by_day.items(), key=lambda x: x[1])[0] if votes_by_day else None
        
        # Reason categories
        reason_categories = {}
        for vote in votes:
            category = vote.reason_category or 'unspecified'
            reason_categories[category] = reason_categories.get(category, 0) + 1
        
        return {
            'total_votes': total_votes,
            'upvotes': upvotes,
            'downvotes': downvotes,
            'vote_weight_avg': round(vote_weight_avg, 2),
            'most_voted_day': most_voted_day.isoformat() if most_voted_day else None,
            'reason_categories': reason_categories,
            'votes_by_day': {k.isoformat(): v for k, v in votes_by_day.items()}
        }
    
    def detect_voting_patterns(self, user_id: int) -> Dict:
        """Detect and analyze voting patterns for a user"""
        patterns = {}
        
        # Consistency pattern
        patterns['consistency'] = self._detect_consistency_pattern(user_id)
        
        # Bias pattern
        patterns['bias'] = self._detect_bias_pattern(user_id)
        
        # Timing pattern
        patterns['timing'] = self._detect_timing_pattern(user_id)
        
        # Quality pattern
        patterns['quality'] = self._detect_quality_pattern(user_id)
        
        return patterns
    
    def _detect_consistency_pattern(self, user_id: int) -> Dict:
        """Detect voting consistency pattern"""
        # Get last 100 votes
        votes = VoteHistory.query.filter_by(user_id=user_id).order_by(
            desc(VoteHistory.created_at)
        ).limit(100).all()
        
        if len(votes) < 20:
            return {'pattern_value': 0.0, 'description': 'Insufficient data'}
        
        # Calculate vote type consistency
        upvote_ratio = len([v for v in votes if v.vote_type == 'upvote']) / len(votes)
        consistency = 1.0 - abs(0.5 - upvote_ratio) * 2  # 0 = random, 1 = consistent
        
        description = 'Highly consistent' if consistency > 0.8 else \
                     'Moderately consistent' if consistency > 0.5 else 'Inconsistent'
        
        return {
            'pattern_value': consistency,
            'description': description,
            'upvote_ratio': round(upvote_ratio, 2),
            'sample_size': len(votes)
        }
    
    def _detect_bias_pattern(self, user_id: int) -> Dict:
        """Detect voting bias pattern"""
        votes = VoteHistory.query.filter_by(user_id=user_id).all()
        
        if len(votes) < 20:
            return {'pattern_value': 0.0, 'description': 'Insufficient data'}
        
        # Check for bias towards specific users or content types
        target_users = {}
        for vote in votes:
            target = self._get_target_object(vote.target_type, vote.target_id)
            if target:
                target_users[target.user_id] = target_users.get(target.user_id, 0) + 1
        
        if len(target_users) < 2:
            return {'pattern_value': 0.0, 'description': 'Insufficient target variety'}
        
        # Calculate bias (how concentrated voting is on few targets)
        max_votes = max(target_users.values())
        total_votes = len(votes)
        bias = max_votes / total_votes
        
        description = 'Highly biased' if bias > 0.5 else \
                     'Moderately biased' if bias > 0.2 else 'Low bias'
        
        return {
            'pattern_value': bias,
            'description': description,
            'unique_targets': len(target_users),
            'most_voted_target': max(target_users, key=target_users.get)
        }
    
    def _detect_timing_pattern(self, user_id: int) -> Dict:
        """Detect voting timing pattern"""
        votes = VoteHistory.query.filter_by(user_id=user_id).all()
        
        if len(votes) < 20:
            return {'pattern_value': 0.0, 'description': 'Insufficient data'}
        
        # Analyze voting times
        hours = [v.created_at.hour for v in votes]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Calculate concentration (how concentrated voting is in certain hours)
        max_hour_votes = max(hour_counts.values())
        total_votes = len(votes)
        concentration = max_hour_votes / total_votes
        
        # Determine if user votes during business hours (9-17)
        business_hours_votes = len([h for h in hours if 9 <= h <= 17])
        business_ratio = business_hours_votes / total_votes
        
        description = 'Business hours voter' if business_ratio > 0.7 else \
                     'Evening voter' if business_ratio < 0.3 else 'Flexible voter'
        
        return {
            'pattern_value': concentration,
            'description': description,
            'business_hours_ratio': round(business_ratio, 2),
            'peak_hour': max(hour_counts, key=hour_counts.get)
        }
    
    def _detect_quality_pattern(self, user_id: int) -> Dict:
        """Detect voting quality pattern"""
        votes = VoteHistory.query.filter_by(user_id=user_id).all()
        
        if len(votes) < 20:
            return {'pattern_value': 0.0, 'description': 'Insufficient data'}
        
        # Analyze reason categories
        reason_votes = [v for v in votes if v.reason_category]
        if len(reason_votes) < 10:
            return {'pattern_value': 0.0, 'description': 'Insufficient reason data'}
        
        # Quality indicators
        helpful_votes = len([v for v in reason_votes if v.reason_category == 'helpful'])
        quality_votes = len([v for v in reason_votes if v.reason_category in ['well_written', 'accurate', 'comprehensive']])
        negative_votes = len([v for v in reason_votes if v.reason_category in ['spam', 'offensive', 'low_quality']])
        
        total_reason_votes = len(reason_votes)
        quality_ratio = (helpful_votes + quality_votes) / total_reason_votes
        negative_ratio = negative_votes / total_reason_votes
        
        # Calculate quality score
        quality_score = quality_ratio - negative_ratio
        
        description = 'Quality voter' if quality_score > 0.5 else \
                     'Mixed voter' if quality_score > 0 else 'Critical voter'
        
        return {
            'pattern_value': max(-1.0, min(1.0, quality_score)),
            'description': description,
            'quality_ratio': round(quality_ratio, 2),
            'negative_ratio': round(negative_ratio, 2),
            'reasons_provided': total_reason_votes
        }
