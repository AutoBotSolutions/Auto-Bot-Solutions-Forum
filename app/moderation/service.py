"""
Automated Content Moderation Service Layer

This module contains service classes for the content moderation system,
including automated spam detection, content quality scoring, moderation queue management,
and automated moderation actions.
"""

from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import and_, or_, desc, asc, func
from app import db
from app.models import User, Post, Comment
from .models import (
    ModerationQueue, ContentAnalysis, ModerationAction, ModerationRule,
    SpamDetection, ContentQuality, ModerationPattern, ModerationHistory
)
import re
import hashlib
import json


class ModerationService:
    """Base service for moderation management"""
    
    def __init__(self):
        self.default_confidence_threshold = 0.7
        self.default_auto_apply = False
    
    def add_to_queue(self, content_type, content_id, content_data, priority='medium'):
        """Add content to moderation queue"""
        
        # Check if already in queue
        existing = ModerationQueue.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            status='pending'
        ).first()
        
        if existing:
            return existing
        
        # Create queue item
        queue_item = ModerationQueue(
            content_type=content_type,
            content_id=content_id,
            content_data=content_data,
            priority=priority,
            created_at=datetime.utcnow()
        )
        
        db.session.add(queue_item)
        db.session.commit()
        
        # Record history
        self._record_history(
            event_type='analysis',
            target_type=content_type,
            target_id=content_id,
            actor_type='system',
            event_description=f'Content added to moderation queue (priority: {priority})',
            event_data={'priority': priority}
        )
        
        return queue_item
    
    def get_queue_items(self, status='pending', limit=50, offset=0):
        """Get items from moderation queue"""
        
        query = ModerationQueue.query.filter_by(status=status)
        
        if status == 'pending':
            query = query.order_by(
                ModerationQueue.priority.desc(),
                ModerationQueue.created_at.asc()
            )
        else:
            query = query.order_by(ModerationQueue.updated_at.desc())
        
        items = query.offset(offset).limit(limit).all()
        
        return items
    
    def update_queue_status(self, queue_id, status, reviewer_id=None, notes=None):
        """Update queue item status"""
        
        queue_item = ModerationQueue.query.get(queue_id)
        if not queue_item:
            return None
        
        old_status = queue_item.status
        queue_item.status = status
        queue_item.reviewed_at = datetime.utcnow()
        
        if reviewer_id:
            queue_item.reviewer_id = reviewer_id
        
        if notes:
            queue_item.review_notes = notes
        
        db.session.commit()
        
        # Record history
        self._record_history(
            event_type='review',
            target_type=queue_item.content_type,
            target_id=queue_item.content_id,
            actor_type='moderator',
            actor_id=reviewer_id,
            event_description=f'Status changed from {old_status} to {status}',
            previous_state={'status': old_status},
            new_state={'status': status},
            related_queue_id=queue_id
        )
        
        return queue_item
    
    def get_queue_stats(self):
        """Get moderation queue statistics"""
        
        stats = {
            'total_pending': ModerationQueue.query.filter_by(status='pending').count(),
            'total_approved': ModerationQueue.query.filter_by(status='approved').count(),
            'total_rejected': ModerationQueue.query.filter_by(status='rejected').count(),
            'total_flagged': ModerationQueue.query.filter_by(status='flagged').count(),
            'high_priority_pending': ModerationQueue.query.filter_by(
                status='pending', priority='high'
            ).count(),
            'critical_priority_pending': ModerationQueue.query.filter_by(
                status='pending', priority='critical'
            ).count()
        }
        
        return stats
    
    def _record_history(self, event_type, target_type, target_id, actor_type, 
                      actor_id=None, event_description=None, event_data=None,
                      previous_state=None, new_state=None, automated=False):
        """Record moderation history event"""
        
        history = ModerationHistory(
            event_type=event_type,
            event_description=event_description,
            target_type=target_type,
            target_id=target_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_data=event_data,
            previous_state=previous_state,
            new_state=new_state,
            automated=automated,
            created_at=datetime.utcnow()
        )
        
        db.session.add(history)
        db.session.commit()


class ContentAnalysisService(ModerationService):
    """Service for content analysis"""
    
    def analyze_content(self, content_type, content_id, content_text, metadata=None):
        """Analyze content for quality and characteristics"""
        
        # Generate content hash
        content_hash = self._generate_content_hash(content_text)
        
        # Check if analysis already exists
        existing = ContentAnalysis.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            content_hash=content_hash
        ).first()
        
        if existing:
            return existing
        
        # Perform analysis
        analysis_data = self._perform_content_analysis(content_text, metadata)
        
        # Create analysis record
        analysis = ContentAnalysis(
            content_type=content_type,
            content_id=content_id,
            content_hash=content_hash,
            **analysis_data
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return analysis
    
    def _perform_content_analysis(self, content_text, metadata=None):
        """Perform detailed content analysis"""
        
        # Basic metrics
        words = content_text.split()
        sentences = re.split(r'[.!?]+', content_text)
        paragraphs = content_text.split('\n\n')
        
        word_count = len(words)
        character_count = len(content_text)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # Calculate averages
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()]) if sentences else 0
        
        # Readability score (simplified Flesch-Kincaid)
        readability_score = self._calculate_readability(content_text)
        
        # Sentiment analysis (simplified)
        sentiment_score = self._analyze_sentiment(content_text)
        sentiment_label = self._get_sentiment_label(sentiment_score)
        
        # Language detection (simplified)
        language_detected = self._detect_language(content_text)
        language_confidence = 0.8  # Simplified confidence
        
        # Topic analysis (simplified)
        topics = self._extract_topics(content_text)
        primary_topic = topics[0]['topic'] if topics else 'general'
        topic_confidence = topics[0]['confidence'] if topics else 0.5
        
        # Quality scores
        grammar_score = self._assess_grammar(content_text)
        spelling_score = self._assess_spelling(content_text)
        coherence_score = self._assess_coherence(content_text)
        
        return {
            'word_count': word_count,
            'character_count': character_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length,
            'readability_score': readability_score,
            'language_detected': language_detected,
            'language_confidence': language_confidence,
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'primary_topic': primary_topic,
            'topic_confidence': topic_confidence,
            'topics': topics,
            'keywords': self._extract_keywords(content_text),
            'entities': self._extract_entities(content_text),
            'grammar_score': grammar_score,
            'spelling_score': spelling_score,
            'coherence_score': coherence_score,
            'analysis_version': '1.0',
            'confidence_score': 0.8
        }
    
    def _generate_content_hash(self, content_text):
        """Generate hash for content"""
        return hashlib.sha256(content_text.encode()).hexdigest()
    
    def _calculate_readability(self, content_text):
        """Calculate simplified readability score"""
        words = content_text.split()
        sentences = re.split(r'[.!?]+', content_text)
        
        if not words or not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables = sum(self._count_syllables(word) for word in words) / len(words)
        
        # Simplified Flesch-Kincaid formula
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
        
        # Normalize to 0-1 scale
        return max(0.0, min(1.0, readability / 100))
    
    def _count_syllables(self, word):
        """Count syllables in a word (simplified)"""
        vowels = 'aeiouy'
        syllables = 0
        prev_char_was_vowel = False
        
        for char in word.lower():
            is_vowel = char in vowels
            if is_vowel and not prev_char_was_vowel:
                syllables += 1
            prev_char_was_vowel = is_vowel
        
        if syllables == 0:
            syllables = 1
        
        return syllables
    
    def _analyze_sentiment(self, content_text):
        """Analyze sentiment (simplified)"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'best', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst', 'disgusting', 'evil', 'worst']
        
        words = content_text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_sentiment_words
    
    def _get_sentiment_label(self, score):
        """Get sentiment label from score"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _detect_language(self, content_text):
        """Detect language (simplified)"""
        # This is a very simplified language detection
        # In production, use a proper language detection library
        common_english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with', 'for', 'as', 'on', 'be', 'at', 'by', 'this', 'have', 'from']
        words = content_text.lower().split()
        
        if len(words) == 0:
            return 'unknown'
        
        english_word_count = sum(1 for word in words if word in common_english_words)
        english_ratio = english_word_count / len(words)
        
        if english_ratio > 0.3:
            return 'en'
        else:
            return 'unknown'
    
    def _extract_topics(self, content_text):
        """Extract topics from content (simplified)"""
        topics = [
            {'topic': 'technology', 'confidence': 0.7, 'keywords': ['technology', 'software', 'computer', 'programming', 'code']},
            {'topic': 'business', 'confidence': 0.6, 'keywords': ['business', 'company', 'market', 'sales', 'profit']},
            {'topic': 'education', 'confidence': 0.6, 'keywords': ['education', 'learning', 'school', 'student', 'teacher']},
            {'topic': 'health', 'confidence': 0.6, 'keywords': ['health', 'medical', 'doctor', 'patient', 'treatment']},
            {'topic': 'entertainment', 'confidence': 0.5, 'keywords': ['entertainment', 'movie', 'music', 'game', 'fun']}
        ]
        
        content_lower = content_text.lower()
        scored_topics = []
        
        for topic in topics:
            keyword_count = sum(1 for keyword in topic['keywords'] if keyword in content_lower)
            if keyword_count > 0:
                confidence = min(1.0, topic['confidence'] * (keyword_count / len(topic['keywords'])))
                scored_topics.append({
                    'topic': topic['topic'],
                    'confidence': confidence,
                    'keywords_found': keyword_count
                })
        
        return sorted(scored_topics, key=lambda x: x['confidence'], reverse=True)
    
    def _extract_keywords(self, content_text):
        """Extract keywords from content (simplified)"""
        # Common words to exclude
        stop_words = {'the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with', 'for', 'as', 'on', 'be', 'at', 'by', 'this', 'have', 'from', 'or', 'an', 'will', 'not', 'can', 'but', 'they', 'their', 'you', 'we', 'our', 'your', 'his', 'her', 'its', 'which', 'who', 'what', 'when', 'where', 'why', 'how'}
        
        words = re.findall(r'\b\w+\b', content_text.lower())
        word_freq = {}
        
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords with scores
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [{'keyword': word, 'score': freq / len(words)} for word, freq in top_keywords]
    
    def _extract_entities(self, content_text):
        """Extract named entities (simplified)"""
        entities = []
        
        # Simple email detection
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content_text)
        for email in emails:
            entities.append({'type': 'email', 'value': email, 'confidence': 0.9})
        
        # Simple URL detection
        urls = re.findall(r'https?://[^\s]+', content_text)
        for url in urls:
            entities.append({'type': 'url', 'value': url, 'confidence': 0.9})
        
        # Simple phone number detection
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content_text)
        for phone in phones:
            entities.append({'type': 'phone', 'value': phone, 'confidence': 0.8})
        
        return entities
    
    def _assess_grammar(self, content_text):
        """Assess grammar quality (simplified)"""
        # Very simplified grammar assessment
        sentences = re.split(r'[.!?]+', content_text)
        valid_sentences = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and sentence[0].isupper() and sentence[-1] in '.!?':
                valid_sentences += 1
        
        if len(sentences) == 0:
            return 0.0
        
        return valid_sentences / len(sentences)
    
    def _assess_spelling(self, content_text):
        """Assess spelling quality (simplified)"""
        # Very simplified spelling assessment
        # In production, use a proper spell checker
        common_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with', 'for', 'as', 'on', 'be', 'at', 'by', 'this', 'have', 'from']
        words = re.findall(r'\b[a-zA-Z]+\b', content_text.lower())
        
        if len(words) == 0:
            return 1.0
        
        correct_words = sum(1 for word in words if word in common_words or len(word) > 3)
        return correct_words / len(words)
    
    def _assess_coherence(self, content_text):
        """Assess text coherence (simplified)"""
        # Very simplified coherence assessment
        sentences = re.split(r'[.!?]+', content_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return 0.5
        
        # Check for basic coherence indicators
        coherence_score = 0.5
        
        # Check sentence length variation
        sentence_lengths = [len(s.split()) for s in sentences]
        length_variance = max(sentence_lengths) - min(sentence_lengths)
        if length_variance < 10:  # Not too much variation
            coherence_score += 0.2
        
        # Check for transition words
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 'nevertheless']
        transition_count = sum(1 for s in sentences if any(word in s.lower() for word in transition_words))
        if transition_count > 0:
            coherence_score += 0.3
        
        return min(1.0, coherence_score)


class SpamDetectionService(ModerationService):
    """Service for spam detection"""
    
    def analyze_for_spam(self, content_type, content_id, content_text, user_id=None, metadata=None):
        """Analyze content for spam"""
        
        # Generate content hash
        content_hash = self._generate_content_hash(content_text)
        
        # Check if analysis already exists
        existing = SpamDetection.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            content_hash=content_hash
        ).first()
        
        if existing:
            return existing
        
        # Perform spam analysis
        spam_data = self._perform_spam_analysis(content_text, user_id, metadata)
        
        # Create spam detection record
        spam_detection = SpamDetection(
            content_type=content_type,
            content_id=content_id,
            content_hash=content_hash,
            **spam_data
        )
        
        db.session.add(spam_detection)
        db.session.commit()
        
        return spam_detection
    
    def _perform_spam_analysis(self, content_text, user_id=None, metadata=None):
        """Perform detailed spam analysis"""
        
        # Keyword analysis
        keyword_score, detected_keywords = self._analyze_spam_keywords(content_text)
        
        # Pattern analysis
        pattern_score, detected_patterns = self._analyze_spam_patterns(content_text)
        
        # Behavior analysis
        behavior_score, behavior_data = self._analyze_user_behavior(user_id, metadata)
        
        # Metadata analysis
        metadata_score, suspicious_metadata = self._analyze_metadata(metadata)
        
        # Calculate overall score
        overall_score = (keyword_score * 0.4 + pattern_score * 0.3 + 
                         behavior_score * 0.2 + metadata_score * 0.1)
        
        # Determine if spam
        is_spam = overall_score > 0.7
        confidence = overall_score if is_spam else (1.0 - overall_score)
        
        # Determine spam type
        spam_type = self._determine_spam_type(detected_keywords, detected_patterns)
        
        return {
            'overall_score': overall_score,
            'keyword_score': keyword_score,
            'pattern_score': pattern_score,
            'behavior_score': behavior_score,
            'metadata_score': metadata_score,
            'is_spam': is_spam,
            'confidence': confidence,
            'spam_type': spam_type,
            'detected_keywords': detected_keywords,
            'detected_patterns': detected_patterns,
            'suspicious_metadata': suspicious_metadata,
            'user_behavior_score': behavior_score,
            'posting_frequency': behavior_data.get('posting_frequency', 0.0),
            'account_age_risk': behavior_data.get('account_age_risk', 0.0),
            'detection_version': '1.0',
            'detection_time': 0.1
        }
    
    def _analyze_spam_keywords(self, content_text):
        """Analyze content for spam keywords"""
        
        spam_keywords = {
            'promotional': ['buy', 'sale', 'discount', 'offer', 'deal', 'free', 'cheap', 'price', 'money', 'cash', 'click', 'order', 'purchase', 'limited', 'urgent', 'act now', 'guaranteed', 'risk free'],
            'scam': ['winner', 'lottery', 'prize', 'congratulations', 'selected', 'claim', 'reward', 'inheritance', 'million', 'billion', 'transfer', 'bank', 'account', 'password', 'verify'],
            'phishing': ['verify', 'confirm', 'suspended', 'blocked', 'security', 'update', 'information', 'click here', 'login', 'sign in'],
            'adult': ['adult', 'xxx', 'sex', 'dating', 'escort', 'hot', 'sexy', 'nude', 'naked'],
            'medical': ['weight loss', 'diet', 'pill', 'medicine', 'cure', 'treatment', 'doctor', 'health', 'medical'],
            'financial': ['investment', 'profit', 'return', 'guarantee', 'stock', 'trading', 'forex', 'bitcoin', 'crypto', 'money']
        }
        
        content_lower = content_text.lower()
        detected_keywords = []
        category_scores = {}
        
        for category, keywords in spam_keywords.items():
            keyword_count = 0
            category_keywords = []
            
            for keyword in keywords:
                if keyword in content_lower:
                    keyword_count += 1
                    category_keywords.append(keyword)
            
            if category_keywords:
                detected_keywords.extend([f"{category}:{kw}" for kw in category_keywords])
                category_scores[category] = min(1.0, keyword_count / len(keywords))
        
        # Calculate overall keyword score
        if category_scores:
            keyword_score = sum(category_scores.values()) / len(category_scores)
        else:
            keyword_score = 0.0
        
        return keyword_score, detected_keywords
    
    def _analyze_spam_patterns(self, content_text):
        """Analyze content for spam patterns"""
        
        spam_patterns = {
            'excessive_caps': r'^[A-Z\s]{10,}$',
            'repeated_chars': r'(.)\1{4,}',
            'phone_number': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'email_spam': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url_spam': r'https?://[^\s]+',
            'exclamation_marks': r'!{3,}',
            'dollar_signs': r'\${2,}',
            'all_caps_words': r'\b[A-Z]{5,}\b',
            'suspicious_links': r'\b(bit\.ly|tinyurl\.com|goo\.gl)\b'
        }
        
        detected_patterns = []
        pattern_scores = {}
        
        for pattern_name, pattern in spam_patterns.items():
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                detected_patterns.extend([f"{pattern_name}:{match}" for match in matches])
                pattern_scores[pattern_name] = min(1.0, len(matches) / 5)
        
        # Calculate overall pattern score
        if pattern_scores:
            pattern_score = sum(pattern_scores.values()) / len(pattern_scores)
        else:
            pattern_score = 0.0
        
        return pattern_score, detected_patterns
    
    def _analyze_user_behavior(self, user_id, metadata=None):
        """Analyze user behavior for spam indicators"""
        
        behavior_score = 0.0
        behavior_data = {}
        
        if user_id:
            user = User.query.get(user_id)
            if user:
                # Account age risk
                account_age = datetime.utcnow() - user.created_at
                account_age_days = account_age.days
                
                if account_age_days < 1:
                    account_age_risk = 1.0
                elif account_age_days < 7:
                    account_age_risk = 0.7
                elif account_age_days < 30:
                    account_age_risk = 0.4
                else:
                    account_age_risk = 0.1
                
                behavior_data['account_age_risk'] = account_age_risk
                behavior_score += account_age_risk * 0.6
        
        # Posting frequency (simplified)
        if metadata and 'posting_frequency' in metadata:
            posting_frequency = metadata['posting_frequency']
            behavior_data['posting_frequency'] = posting_frequency
            
            if posting_frequency > 10:  # More than 10 posts per hour
                frequency_score = 1.0
            elif posting_frequency > 5:
                frequency_score = 0.6
            elif posting_frequency > 2:
                frequency_score = 0.3
            else:
                frequency_score = 0.0
            
            behavior_score += frequency_score * 0.4
        
        return behavior_score, behavior_data
    
    def _analyze_metadata(self, metadata):
        """Analyze metadata for spam indicators"""
        
        metadata_score = 0.0
        suspicious_metadata = []
        
        if not metadata:
            return metadata_score, suspicious_metadata
        
        # Check for suspicious IP addresses
        if 'ip_address' in metadata:
            ip = metadata['ip_address']
            if self._is_suspicious_ip(ip):
                suspicious_metadata.append(f"suspicious_ip:{ip}")
                metadata_score += 0.3
        
        # Check for suspicious user agent
        if 'user_agent' in metadata:
            ua = metadata['user_agent']
            if self._is_suspicious_user_agent(ua):
                suspicious_metadata.append(f"suspicious_user_agent:{ua}")
                metadata_score += 0.2
        
        # Check for suspicious referrer
        if 'referrer' in metadata:
            referrer = metadata['referrer']
            if self._is_suspicious_referrer(referrer):
                suspicious_metadata.append(f"suspicious_referrer:{referrer}")
                metadata_score += 0.2
        
        return min(1.0, metadata_score), suspicious_metadata
    
    def _is_suspicious_ip(self, ip):
        """Check if IP is suspicious (simplified)"""
        # In production, use a proper IP reputation service
        suspicious_ranges = ['0.0.0.0', '127.0.0.1']  # Example suspicious IPs
        return ip in suspicious_ranges
    
    def _is_suspicious_user_agent(self, user_agent):
        """Check if user agent is suspicious"""
        suspicious_patterns = ['bot', 'crawler', 'spider', 'scraper']
        return any(pattern in user_agent.lower() for pattern in suspicious_patterns)
    
    def _is_suspicious_referrer(self, referrer):
        """Check if referrer is suspicious"""
        suspicious_domains = ['spam.com', 'malware.net']  # Example suspicious domains
        return any(domain in referrer for domain in suspicious_domains)
    
    def _determine_spam_type(self, keywords, patterns):
        """Determine spam type based on detected indicators"""
        
        if not keywords and not patterns:
            return 'unknown'
        
        keyword_types = set()
        for kw in keywords:
            if ':' in kw:
                keyword_types.add(kw.split(':')[0])
        
        pattern_types = set()
        for pattern in patterns:
            if ':' in pattern:
                pattern_types.add(pattern.split(':')[0])
        
        # Determine primary type
        if 'promotional' in keyword_types:
            return 'promotional'
        elif 'scam' in keyword_types:
            return 'scam'
        elif 'phishing' in keyword_types:
            return 'phishing'
        elif 'adult' in keyword_types:
            return 'adult'
        elif 'medical' in keyword_types:
            return 'medical'
        elif 'financial' in keyword_types:
            return 'financial'
        elif 'email_spam' in pattern_types:
            return 'email_spam'
        elif 'url_spam' in pattern_types:
            return 'url_spam'
        else:
            return 'general'
    
    def _generate_content_hash(self, content_text):
        """Generate hash for content"""
        return hashlib.sha256(content_text.encode()).hexdigest()


class ContentQualityService(ModerationService):
    """Service for content quality assessment"""
    
    def assess_quality(self, content_type, content_id, content_text, metadata=None):
        """Assess content quality"""
        
        # Generate content hash
        content_hash = self._generate_content_hash(content_text)
        
        # Check if assessment already exists
        existing = ContentQuality.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            content_hash=content_hash
        ).first()
        
        if existing:
            return existing
        
        # Perform quality assessment
        quality_data = self._perform_quality_assessment(content_text, metadata)
        
        # Create quality record
        quality = ContentQuality(
            content_type=content_type,
            content_id=content_id,
            content_hash=content_hash,
            **quality_data
        )
        
        db.session.add(quality)
        db.session.commit()
        
        return quality
    
    def _perform_quality_assessment(self, content_text, metadata=None):
        """Perform detailed quality assessment"""
        
        # Content quality factors
        content_quality = self._assess_content_quality(content_text)
        presentation_quality = self._assess_presentation_quality(content_text)
        originality_score = self._assess_originality(content_text)
        engagement_potential = self._assess_engagement_potential(content_text)
        
        # Individual quality scores
        grammar_score = self._assess_grammar_quality(content_text)
        spelling_score = self._assess_spelling_quality(content_text)
        structure_score = self._assess_structure_quality(content_text)
        coherence_score = self._assess_coherence_quality(content_text)
        relevance_score = self._assess_relevance(content_text, metadata)
        
        # Calculate overall score
        overall_score = (
            content_quality * 0.3 +
            presentation_quality * 0.2 +
            originality_score * 0.2 +
            engagement_potential * 0.3
        )
        
        # Determine quality grade
        quality_grade = self._get_quality_grade(overall_score)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            content_text, grammar_score, spelling_score, structure_score, coherence_score
        )
        
        # Assess best practices
        best_practices_score = self._assess_best_practices(content_text)
        
        return {
            'overall_score': overall_score,
            'content_quality': content_quality,
            'presentation_quality': presentation_quality,
            'originality_score': originality_score,
            'engagement_potential': engagement_potential,
            'grammar_score': grammar_score,
            'spelling_score': spelling_score,
            'structure_score': structure_score,
            'coherence_score': coherence_score,
            'relevance_score': relevance_score,
            'word_count': len(content_text.split()),
            'readability_score': self._calculate_readability(content_text),
            'complexity_score': self._assess_complexity(content_text),
            'quality_grade': quality_grade,
            'improvement_suggestions': improvement_suggestions,
            'best_practices_score': best_practices_score,
            'assessment_version': '1.0',
            'assessment_time': 0.1,
            'confidence': 0.8
        }
    
    def _assess_content_quality(self, content_text):
        """Assess overall content quality"""
        
        factors = {
            'length': self._assess_length_quality(content_text),
            'clarity': self._assess_clarity(content_text),
            'depth': self._assess_depth(content_text),
            'accuracy': self._assess_accuracy(content_text)
        }
        
        return sum(factors.values()) / len(factors)
    
    def _assess_presentation_quality(self, content_text):
        """Assess presentation quality"""
        
        factors = {
            'formatting': self._assess_formatting(content_text),
            'organization': self._assess_organization(content_text),
            'readability': self._assess_readability(content_text)
        }
        
        return sum(factors.values()) / len(factors)
    
    def _assess_originality(self, content_text):
        """Assess content originality (simplified)"""
        
        # Very simplified originality assessment
        # In production, use proper plagiarism detection
        common_phrases = [
            'in conclusion', 'in summary', 'to summarize', 'in my opinion',
            'first of all', 'secondly', 'finally', 'in addition', 'furthermore'
        ]
        
        content_lower = content_text.lower()
        common_phrase_count = sum(1 for phrase in common_phrases if phrase in content_lower)
        
        # Less common phrases = more original
        originality_score = max(0.0, 1.0 - (common_phrase_count / len(common_phrases)))
        
        return originality_score
    
    def _assess_engagement_potential(self, content_text):
        """Assess engagement potential"""
        
        factors = {
            'emotional_impact': self._assess_emotional_impact(content_text),
            'interactivity': self._assess_interactivity(content_text),
            'novelty': self._assess_novelty(content_text),
            'practicality': self._assess_practicality(content_text)
        }
        
        return sum(factors.values()) / len(factors)
    
    def _assess_grammar_quality(self, content_text):
        """Assess grammar quality"""
        # Reuse from ContentAnalysisService
        analysis_service = ContentAnalysisService()
        return analysis_service._assess_grammar(content_text)
    
    def _assess_spelling_quality(self, content_text):
        """Assess spelling quality"""
        # Reuse from ContentAnalysisService
        analysis_service = ContentAnalysisService()
        return analysis_service._assess_spelling(content_text)
    
    def _assess_structure_quality(self, content_text):
        """Assess content structure"""
        
        paragraphs = content_text.split('\n\n')
        sentences = re.split(r'[.!?]+', content_text)
        
        # Check for proper structure
        structure_score = 0.0
        
        # Has multiple paragraphs
        if len(paragraphs) > 1:
            structure_score += 0.3
        
        # Has proper sentence structure
        valid_sentences = sum(1 for s in sentences if s.strip() and len(s.strip()) > 5)
        if valid_sentences > 0:
            structure_score += 0.4
        
        # Has logical flow (simplified)
        if len(sentences) > 1:
            structure_score += 0.3
        
        return structure_score
    
    def _assess_coherence_quality(self, content_text):
        """Assess content coherence"""
        # Reuse from ContentAnalysisService
        analysis_service = ContentAnalysisService()
        return analysis_service._assess_coherence(content_text)
    
    def _assess_relevance(self, content_text, metadata=None):
        """Assess content relevance"""
        
        # Very simplified relevance assessment
        # In production, use proper relevance analysis based on context
        relevance_score = 0.7  # Default moderate relevance
        
        if metadata and 'topic' in metadata:
            # Check if content matches expected topic
            topic_keywords = self._get_topic_keywords(metadata['topic'])
            content_lower = content_text.lower()
            
            keyword_matches = sum(1 for keyword in topic_keywords if keyword in content_lower)
            if keyword_matches > 0:
                relevance_score = min(1.0, 0.5 + (keyword_matches / len(topic_keywords)))
        
        return relevance_score
    
    def _get_topic_keywords(self, topic):
        """Get keywords for a topic"""
        topic_keywords = {
            'technology': ['technology', 'software', 'computer', 'programming', 'code', 'development'],
            'business': ['business', 'company', 'market', 'sales', 'profit', 'management'],
            'education': ['education', 'learning', 'school', 'student', 'teacher', 'knowledge'],
            'health': ['health', 'medical', 'doctor', 'patient', 'treatment', 'wellness'],
            'entertainment': ['entertainment', 'movie', 'music', 'game', 'fun', 'enjoy']
        }
        
        return topic_keywords.get(topic.lower(), [])
    
    def _calculate_readability(self, content_text):
        """Calculate readability score"""
        # Reuse from ContentAnalysisService
        analysis_service = ContentAnalysisService()
        return analysis_service._calculate_readability(content_text)
    
    def _assess_complexity(self, content_text):
        """Assess content complexity"""
        
        words = content_text.split()
        sentences = re.split(r'[.!?]+', content_text)
        
        if not words or not sentences:
            return 0.0
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Average sentence length
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
        
        # Complexity based on word and sentence length
        word_complexity = min(1.0, avg_word_length / 10)
        sentence_complexity = min(1.0, avg_sentence_length / 25)
        
        return (word_complexity + sentence_complexity) / 2
    
    def _get_quality_grade(self, score):
        """Get quality grade from score"""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def _generate_improvement_suggestions(self, content_text, grammar_score, spelling_score, structure_score, coherence_score):
        """Generate improvement suggestions"""
        
        suggestions = []
        
        if grammar_score < 0.7:
            suggestions.append({
                'type': 'grammar',
                'message': 'Improve grammar by checking sentence structure and punctuation',
                'priority': 'high'
            })
        
        if spelling_score < 0.7:
            suggestions.append({
                'type': 'spelling',
                'message': 'Check for spelling errors and typos',
                'priority': 'medium'
            })
        
        if structure_score < 0.7:
            suggestions.append({
                'type': 'structure',
                'message': 'Organize content into logical paragraphs and sections',
                'priority': 'medium'
            })
        
        if coherence_score < 0.7:
            suggestions.append({
                'type': 'coherence',
                'message': 'Improve flow and logical connections between ideas',
                'priority': 'high'
            })
        
        if len(content_text) < 100:
            suggestions.append({
                'type': 'length',
                'message': 'Consider adding more detail to your content',
                'priority': 'low'
            })
        
        return suggestions
    
    def _assess_best_practices(self, content_text):
        """Assess adherence to best practices"""
        
        practices = {
            'proper_capitalization': self._check_capitalization(content_text),
            'proper_punctuation': self._check_punctuation(content_text),
            'no_excessive_whitespace': self._check_whitespace(content_text),
            'logical_flow': self._check_logical_flow(content_text),
            'appropriate_tone': self._check_tone(content_text)
        }
        
        return sum(practices.values()) / len(practices)
    
    def _check_capitalization(self, content_text):
        """Check proper capitalization"""
        sentences = re.split(r'[.!?]+', content_text)
        valid_sentences = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence[0].isupper():
                valid_sentences += 1
        
        if len(sentences) == 0:
            return 1.0
        
        return valid_sentences / len(sentences)
    
    def _check_punctuation(self, content_text):
        """Check proper punctuation"""
        # Simplified punctuation check
        sentences = re.split(r'[.!?]+', content_text)
        valid_sentences = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                valid_sentences += 1
        
        if len(sentences) == 0:
            return 1.0
        
        return valid_sentences / len(sentences)
    
    def _check_whitespace(self, content_text):
        """Check for excessive whitespace"""
        # Check for multiple consecutive spaces
        if '  ' in content_text:
            return 0.8
        return 1.0
    
    def _check_logical_flow(self, content_text):
        """Check for logical flow"""
        # Simplified flow check
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently']
        content_lower = content_text.lower()
        
        transition_count = sum(1 for word in transition_words if word in content_lower)
        
        if len(content_text.split()) < 50:
            return 1.0  # Short content doesn't need transitions
        
        return min(1.0, transition_count / 3)
    
    def _check_tone(self, content_text):
        """Check for appropriate tone"""
        # Simplified tone check
        negative_words = ['hate', 'terrible', 'awful', 'disgusting', 'worst']
        content_lower = content_text.lower()
        
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if negative_count > len(content_text.split()) * 0.1:
            return 0.6  # Too negative
        
        return 1.0
    
    def _assess_length_quality(self, content_text):
        """Assess content length quality"""
        word_count = len(content_text.split())
        
        if word_count < 10:
            return 0.3  # Too short
        elif word_count < 50:
            return 0.7  # Short but acceptable
        elif word_count < 500:
            return 1.0  # Good length
        elif word_count < 1000:
            return 0.9  # Long but acceptable
        else:
            return 0.7  # Very long
    
    def _assess_clarity(self, content_text):
        """Assess content clarity"""
        # Simplified clarity check
        avg_sentence_length = sum(len(s.split()) for s in re.split(r'[.!?]+', content_text) if s.strip()) / len([s for s in re.split(r'[.!?]+', content_text) if s.strip()])
        
        if 10 <= avg_sentence_length <= 20:
            return 1.0  # Ideal sentence length
        elif 5 <= avg_sentence_length <= 30:
            return 0.8  # Acceptable
        else:
            return 0.6  # Too complex or too simple
    
    def _assess_depth(self, content_text):
        """Assess content depth"""
        # Simplified depth check
        technical_terms = ['algorithm', 'implementation', 'architecture', 'system', 'process', 'methodology']
        content_lower = content_text.lower()
        
        technical_count = sum(1 for term in technical_terms if term in content_lower)
        
        if technical_count > 5:
            return 1.0  # High technical depth
        elif technical_count > 2:
            return 0.8  # Good depth
        elif technical_count > 0:
            return 0.6  # Some depth
        else:
            return 0.4  # Limited depth
    
    def _assess_accuracy(self, content_text):
        """Assess content accuracy (simplified)"""
        # Very simplified accuracy assessment
        # In production, use fact-checking and verification
        return 0.8  # Default moderate accuracy
    
    def _assess_formatting(self, content_text):
        """Assess content formatting"""
        # Check for proper formatting
        has_paragraphs = '\n\n' in content_text
        has_sentences = any(c in content_text for c in '.!?')
        
        formatting_score = 0.0
        if has_sentences:
            formatting_score += 0.5
        if has_paragraphs:
            formatting_score += 0.5
        
        return formatting_score
    
    def _assess_organization(self, content_text):
        """Assess content organization"""
        # Simplified organization check
        paragraphs = content_text.split('\n\n')
        
        if len(paragraphs) > 1:
            return 0.8  # Multiple paragraphs show organization
        elif len(paragraphs) == 1:
            return 0.6  # Single paragraph
        else:
            return 0.4  # No paragraphs
    
    def _assess_readability(self, content_text):
        """Assess readability"""
        # Reuse from ContentAnalysisService
        analysis_service = ContentAnalysisService()
        return analysis_service._calculate_readability(content_text)
    
    def _assess_emotional_impact(self, content_text):
        """Assess emotional impact"""
        emotional_words = ['amazing', 'wonderful', 'terrible', 'horrible', 'love', 'hate', 'beautiful', 'ugly']
        content_lower = content_text.lower()
        
        emotional_count = sum(1 for word in emotional_words if word in content_lower)
        
        return min(1.0, emotional_count / 5)
    
    def _assess_interactivity(self, content_text):
        """Assess interactivity potential"""
        interactive_words = ['question', 'answer', 'discuss', 'share', 'comment', 'opinion', 'thought', 'feedback']
        content_lower = content_text.lower()
        
        interactive_count = sum(1 for word in interactive_words if word in content_lower)
        
        return min(1.0, interactive_count / 3)
    
    def _assess_novelty(self, content_text):
        """Assess content novelty"""
        # Simplified novelty assessment
        # In production, use proper plagiarism detection
        unique_words = set(content_text.lower().split())
        total_words = len(content_text.split())
        
        if total_words == 0:
            return 0.0
        
        novelty_score = len(unique_words) / total_words
        
        return min(1.0, novelty_score)
    
    def _assess_practicality(self, content_text):
        """Assess content practicality"""
        practical_words = ['how', 'step', 'guide', 'tutorial', 'solution', 'method', 'technique', 'approach']
        content_lower = content_text.lower()
        
        practical_count = sum(1 for word in practical_words if word in content_lower)
        
        return min(1.0, practical_count / 3)
    
    def _generate_content_hash(self, content_text):
        """Generate hash for content"""
        return hashlib.sha256(content_text.encode()).hexdigest()


class ModerationQueueService(ModerationService):
    """Service for moderation queue management"""
    
    def auto_process_queue(self):
        """Automatically process moderation queue"""
        
        # Get pending items with auto-apply rules
        pending_items = ModerationQueue.query.filter_by(status='pending').all()
        
        processed_count = 0
        for item in pending_items:
            if self._should_auto_process(item):
                result = self._auto_process_item(item)
                if result:
                    processed_count += 1
        
        return processed_count
    
    def _should_auto_process(self, queue_item):
        """Check if item should be auto-processed"""
        
        # Check if high confidence spam or quality score
        if queue_item.spam_score > 0.9:
            return True
        
        if queue_item.quality_score < 0.2:
            return True
        
        # Check for critical priority
        if queue_item.priority == 'critical':
            return True
        
        return False
    
    def _auto_process_item(self, queue_item):
        """Auto-process a queue item"""
        
        try:
            if queue_item.spam_score > 0.9:
                # Auto-reject spam
                return self._auto_reject(queue_item, 'High confidence spam detection')
            elif queue_item.quality_score < 0.2:
                # Auto-reject low quality
                return self._auto_reject(queue_item, 'Low content quality detected')
            else:
                # Auto-approve borderline cases
                return self._auto_approve(queue_item, 'Automated approval based on scores')
                
        except Exception as e:
            current_app.logger.error(f"Error auto-processing queue item {queue_item.id}: {str(e)}")
            return False
    
    def _auto_reject(self, queue_item, reason):
        """Auto-reject a queue item"""
        
        # Update queue item
        queue_item.status = 'rejected'
        queue_item.auto_action_taken = 'reject'
        queue_item.auto_action_confidence = 0.8
        queue_item.auto_action_reason = reason
        queue_item.auto_action_at = datetime.utcnow()
        
        # Create moderation action
        action = ModerationAction(
            action_type='reject',
            action_reason=reason,
            target_type=queue_item.content_type,
            target_id=queue_item.content_id,
            actor_type='system',
            automated=True,
            confidence=0.8
        )
        
        db.session.add(action)
        db.session.commit()
        
        # Record history
        self._record_history(
            event_type='action',
            target_type=queue_item.content_type,
            target_id=queue_item.content_id,
            actor_type='system',
            event_description=f'Auto-rejected: {reason}',
            automated=True,
            related_queue_id=queue_item.id,
            related_action_id=action.id
        )
        
        return True
    
    def _auto_approve(self, queue_item, reason):
        """Auto-approve a queue item"""
        
        # Update queue item
        queue_item.status = 'approved'
        queue_item.auto_action_taken = 'approve'
        queue_item.auto_action_confidence = 0.7
        queue_item.auto_action_reason = reason
        queue_item.auto_action_at = datetime.utcnow()
        
        # Create moderation action
        action = ModerationAction(
            action_type='approve',
            action_reason=reason,
            target_type=queue_item.content_type,
            target_id=queue_item.content_id,
            actor_type='system',
            automated=True,
            confidence=0.7
        )
        
        db.session.add(action)
        db.session.commit()
        
        # Record history
        self._record_history(
            event_type='action',
            target_type=queue_item.content_type,
            target_id=queue_item.content_id,
            actor_type='system',
            event_description=f'Auto-approved: {reason}',
            automated=True,
            related_queue_id=queue_item.id,
            related_action_id=action.id
        )
        
        return True


class ModerationRuleService(ModerationService):
    """Service for moderation rule management"""
    
    def create_rule(self, name, description, rule_type, conditions, action_type, 
                   action_parameters=None, priority=5, confidence_threshold=0.7, 
                   auto_apply=False, created_by=None):
        """Create a new moderation rule"""
        
        rule = ModerationRule(
            name=name,
            description=description,
            rule_type=rule_type,
            conditions=conditions,
            action_type=action_type,
            action_parameters=action_parameters or {},
            priority=priority,
            confidence_threshold=confidence_threshold,
            auto_apply=auto_apply,
            created_by=created_by
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return rule
    
    def apply_rules(self, content_type, content_id, content_data):
        """Apply moderation rules to content"""
        
        rules = ModerationRule.query.filter_by(is_active=True).order_by(
            ModerationRule.priority.desc()
        ).all()
        
        actions_taken = []
        
        for rule in rules:
            if self._should_apply_rule(rule, content_type, content_data):
                result = self._apply_rule(rule, content_type, content_id, content_data)
                if result:
                    actions_taken.append(result)
                    
                    # Update rule statistics
                    rule.total_matches += 1
                    rule.total_actions += 1
                    rule.last_triggered = datetime.utcnow()
        
        db.session.commit()
        
        return actions_taken
    
    def _should_apply_rule(self, rule, content_type, content_data):
        """Check if rule should be applied"""
        
        # Check content types
        if rule.content_types and content_type not in rule.content_types:
            return False
        
        # Check conditions
        if not self._evaluate_conditions(rule.conditions, content_data):
            return False
        
        return True
    
    def _evaluate_conditions(self, conditions, content_data):
        """Evaluate rule conditions"""
        
        # Simplified condition evaluation
        # In production, implement proper condition evaluation logic
        
        for condition in conditions:
            condition_type = condition.get('type')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if condition_type == 'spam_score':
                content_value = content_data.get('spam_score', 0)
                if not self._compare_values(content_value, operator, value):
                    return False
            elif condition_type == 'quality_score':
                content_value = content_data.get('quality_score', 1.0)
                if not self._compare_values(content_value, operator, value):
                    return False
            elif condition_type == 'word_count':
                content_value = len(content_data.get('content_text', '').split())
                if not self._compare_values(content_value, operator, value):
                    return False
        
        return True
    
    def _compare_values(self, content_value, operator, rule_value):
        """Compare values using operator"""
        
        if operator == 'gt':
            return content_value > rule_value
        elif operator == 'gte':
            return content_value >= rule_value
        elif operator == 'lt':
            return content_value < rule_value
        elif operator == 'lte':
            return content_value <= rule_value
        elif operator == 'eq':
            return content_value == rule_value
        elif operator == 'ne':
            return content_value != rule_value
        elif operator == 'contains':
            return str(rule_value) in str(content_value)
        
        return False
    
    def _apply_rule(self, rule, content_type, content_id, content_data):
        """Apply a moderation rule"""
        
        try:
            # Create moderation action
            action = ModerationAction(
                action_type=rule.action_type,
                action_reason=f'Rule: {rule.name}',
                target_type=content_type,
                target_id=content_id,
                actor_type='system',
                automated=True,
                confidence=rule.confidence_threshold,
                action_data={'rule_id': rule.id},
                previous_state=content_data
            )
            
            db.session.add(action)
            
            # Record history
            self._record_history(
                event_type='action',
                target_type=content_type,
                target_id=content_id,
                actor_type='system',
                event_description=f'Applied rule: {rule.name}',
                automated=True,
                related_action_id=action.id
            )
            
            return action
            
        except Exception as e:
            current_app.logger.error(f"Error applying rule {rule.name}: {str(e)}")
            return False


class AutomatedModerationService(ModerationService):
    """Service for automated moderation"""
    
    def moderate_content(self, content_type, content_id, content_text, user_id=None, metadata=None):
        """Perform automated moderation on content"""
        
        # Perform all analyses
        analysis = self._perform_content_analysis(content_type, content_id, content_text)
        spam_result = self._perform_spam_detection(content_type, content_id, content_text, user_id, metadata)
        quality_result = self._perform_quality_assessment(content_type, content_id, content_text)
        
        # Combine results
        moderation_result = self._combine_results(analysis, spam_result, quality_result)
        
        # Add to moderation queue if needed
        if moderation_result['requires_review']:
            self.add_to_queue(
                content_type=content_type,
                content_id=content_id,
                content_data={'text': content_text, 'user_id': user_id, 'metadata': metadata},
                priority=moderation_result['priority']
            )
        
        # Apply automated actions if confident
        if moderation_result['auto_action'] and moderation_result['confidence'] > 0.8:
            self._apply_automated_action(content_type, content_id, moderation_result)
        
        return moderation_result
    
    def _perform_content_analysis(self, content_type, content_id, content_text):
        """Perform content analysis"""
        
        analysis_service = ContentAnalysisService()
        return analysis_service.analyze_content(content_type, content_id, content_text)
    
    def _perform_spam_detection(self, content_type, content_id, content_text, user_id, metadata):
        """Perform spam detection"""
        
        spam_service = SpamDetectionService()
        return spam_service.analyze_for_spam(content_type, content_id, content_text, user_id, metadata)
    
    def _perform_quality_assessment(self, content_type, content_id, content_text):
        """Perform quality assessment"""
        
        quality_service = ContentQualityService()
        return quality_service.assess_quality(content_type, content_id, content_text)
    
    def _combine_results(self, analysis, spam_result, quality_result):
        """Combine analysis results"""
        
        combined = {
            'requires_review': False,
            'auto_action': False,
            'confidence': 0.0,
            'priority': 'medium',
            'spam_score': spam_result.overall_score,
            'quality_score': quality_result.overall_score,
            'analysis': analysis,
            'spam_detection': spam_result,
            'quality_assessment': quality_result
        }
        
        # Determine if review is required
        if spam_result.is_spam or quality_result.overall_score < 0.3:
            combined['requires_review'] = True
            combined['priority'] = 'high' if spam_result.is_spam else 'medium'
        
        # Determine if auto-action should be taken
        if spam_result.is_spam and spam_result.confidence > 0.9:
            combined['auto_action'] = True
            combined['confidence'] = spam_result.confidence
        elif quality_result.overall_score < 0.1 and quality_result.confidence > 0.8:
            combined['auto_action'] = True
            combined['confidence'] = quality_result.confidence
        
        # Set priority
        if spam_result.is_spam:
            combined['priority'] = 'critical' if spam_result.confidence > 0.95 else 'high'
        elif quality_result.overall_score < 0.2:
            combined['priority'] = 'high'
        
        return combined
    
    def _apply_automated_action(self, content_type, content_id, result):
        """Apply automated moderation action"""
        
        action_type = 'reject' if result['spam_detection'].is_spam else 'flag'
        action_reason = f"Automated {action_type}: spam_score={result['spam_score']:.2f}, quality_score={result['quality_score']:.2f}"
        
        action = ModerationAction(
            action_type=action_type,
            action_reason=action_reason,
            target_type=content_type,
            target_id=content_id,
            actor_type='system',
            automated=True,
            confidence=result['confidence'],
            action_data=result
        )
        
        db.session.add(action)
        db.session.commit()
        
        # Record history
        self._record_history(
            event_type='action',
            target_type=content_type,
            target_id=content_id,
            actor_type='system',
            event_description=f'Automated {action_type}: {action_reason}',
            automated=True,
            related_action_id=action.id
        )
        
        return action
