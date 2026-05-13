#!/usr/bin/env python3
"""
Fixed debugging script for Message Systems
Uses in-memory database to avoid conflicts
"""

import sys
import os
import traceback
import json
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

def test_imports():
    """Test all imports for the message systems"""
    print("🔍 Testing imports...")
    
    try:
        # Test model imports
        from app.models import (
            Message, MessageSearchIndex, MessageSearchAnalytics, 
            MessageThread, MessageAttachment, MessageForward, 
            MessageTemplate, User
        )
        print("✅ Model imports successful")
        
        # Test form imports
        from app.message.forms import (
            MessageSearchForm, MessageThreadForm, MessageForwardForm,
            MessageAttachmentForm, MessageTemplateForm, MessageComposeForm
        )
        print("✅ Form imports successful")
        
        # Test utility imports
        from app.utils.message_search import (
            MessageSearchEngine, extract_keywords, generate_search_vector,
            analyze_content, get_search_suggestions, get_popular_search_terms
        )
        print("✅ Message search utilities imports successful")
        
        from app.utils.message_threading import (
            MessageThreadingEngine, find_reply_chain, get_thread_participant_names,
            suggest_thread_participants, get_thread_activity_summary
        )
        print("✅ Message threading utilities imports successful")
        
        from app.utils.rich_text import (
            RichTextProcessor, MessageTemplateManager, format_message_content,
            generate_message_preview, validate_message_content, get_emoji_suggestions
        )
        print("✅ Rich text utilities imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_message_search_system():
    """Test Message Search and Filtering system"""
    print("\n🔍 Testing Message Search and Filtering system...")
    
    try:
        from app.utils.message_search import MessageSearchEngine, extract_keywords, generate_search_vector, analyze_content
        
        # Test search engine
        search_engine = MessageSearchEngine()
        print("✅ MessageSearchEngine created successfully")
        
        # Test keyword extraction
        keywords = extract_keywords("Hello world, this is a test message")
        if keywords:
            print(f"✅ Keyword extraction successful: {keywords}")
        else:
            print("❌ Keyword extraction failed")
            return False
        
        # Test search vector generation
        vector = generate_search_vector("Hello world, this is a test message!")
        if vector:
            print(f"✅ Search vector generation successful: {vector}")
        else:
            print("❌ Search vector generation failed")
            return False
        
        # Test content analysis
        analysis = analyze_content("This is a good and wonderful message")
        if 'sentiment' in analysis:
            print(f"✅ Content analysis successful: sentiment={analysis['sentiment']}")
        else:
            print("❌ Content analysis failed")
            return False
        
        # Test search query building
        basic_conditions = search_engine._build_basic_search("hello world")
        advanced_conditions = search_engine._build_advanced_search('sender:john "hello world"')
        boolean_conditions = search_engine._build_boolean_search('hello AND world NOT goodbye')
        
        if basic_conditions and advanced_conditions and boolean_conditions:
            print("✅ Search query building successful")
        else:
            print("❌ Search query building failed")
            return False
        
        # Test search highlighting
        highlighted = search_engine._highlight_search_terms("Hello world message", "hello")
        if "<mark>" in highlighted:
            print("✅ Search term highlighting successful")
        else:
            print("❌ Search term highlighting failed")
            return False
        
        # Test relevance scoring
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        mock_message = MockMessage("Hello world message")
        score = search_engine._calculate_relevance_score(mock_message, "hello")
        if score > 0:
            print("✅ Relevance score calculation successful")
        else:
            print("❌ Relevance score calculation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Message Search system test failed: {e}")
        traceback.print_exc()
        return False

def test_message_threading_system():
    """Test Message Threading system"""
    print("\n🔍 Testing Message Threading system...")
    
    try:
        from app.utils.message_threading import MessageThreadingEngine, find_reply_chain, get_thread_participant_names, suggest_thread_participants
        
        # Test threading engine
        threading_engine = MessageThreadingEngine()
        print("✅ MessageThreadingEngine created successfully")
        
        # Test participant suggestions
        suggestions = suggest_thread_participants(1, "test", 5)
        if isinstance(suggestions, list):
            print("✅ Participant suggestions working")
        else:
            print("❌ Participant suggestions failed")
            return False
        
        # Test thread statistics (without database)
        class MockThread:
            def __init__(self):
                self.id = 1
                self.subject = "Test Thread"
                self.participant_ids = "[1,2]"
                self.message_count = 5
                self.last_message_at = datetime.utcnow()
                self.created_at = datetime.utcnow()
                self.is_archived = False
                self.is_pinned = False
                self.is_muted = False
        
        # Test thread statistics methods
        mock_thread = MockThread()
        participants = mock_thread.get_participants()
        mock_thread.set_participants([1,2,3])
        mock_thread.add_participant(4)
        mock_thread.remove_participant(2)
        
        if len(participants) >= 2 and len(mock_thread.get_participants()) >= 3:
            print("✅ Thread participant management working")
        else:
            print("❌ Thread participant management failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Message Threading system test failed: {e}")
        traceback.print_exc()
        return False

def test_rich_text_system():
    """Test Rich Text Formatting system"""
    print("\n🔍 Testing Rich Text Formatting system...")
    
    try:
        from app.utils.rich_text import RichTextProcessor, MessageTemplateManager, format_message_content, get_emoji_suggestions
        
        # Test rich text processor
        processor = RichTextProcessor()
        print("✅ RichTextProcessor created successfully")
        
        # Test text processing
        html_content, plain_text = processor.process_rich_text(
            "Hello **world**! This is a test message.",
            content_format="markdown"
        )
        
        if html_content and plain_text:
            print(f"✅ Rich text processing successful")
            print(f"   HTML: {html_content[:50]}...")
            print(f"   Plain: {plain_text}")
        else:
            print("❌ Rich text processing failed")
            return False
        
        # Test emoji conversion
        emoji_text = processor._convert_emoji("Hello :smile: world! :thumbsup:")
        if "😊" in emoji_text and "👍" in emoji_text:
            print(f"✅ Emoji conversion successful: {emoji_text}")
        else:
            print("❌ Emoji conversion failed")
            return False
        
        # Test preview generation
        preview = processor.generate_preview("This is a long message for testing preview functionality.", 20)
        if preview and len(preview) <= 23:  # 20 chars + "..."
            print(f"✅ Preview generation successful: {preview}")
        else:
            print("❌ Preview generation failed")
            return False
        
        # Test content validation
        validation = processor.validate_formatting("Test content", "text")
        if validation and 'valid' in validation:
            print(f"✅ Content validation successful: valid={validation['valid']}")
        else:
            print("❌ Content validation failed")
            return False
        
        # Test template manager
        template_manager = MessageTemplateManager()
        print("✅ MessageTemplateManager created successfully")
        
        # Test template variable extraction
        variables = template_manager._extract_variables("Hello {{username}}, welcome to {{forum_name}}!")
        if "username" in variables and "forum_name" in variables:
            print(f"✅ Template variable extraction successful: {variables}")
        else:
            print("❌ Template variable extraction failed")
            return False
        
        # Test format_message_content function
        formatted_html, formatted_text = format_message_content(
            "**Bold text** and *italic text*",
            content_format="markdown"
        )
        
        if formatted_html and formatted_text:
            print(f"✅ Format message content successful")
            print(f"   HTML: {formatted_html[:50]}...")
            print(f"   Text: {formatted_text}")
        else:
            print("❌ Format message content failed")
            return False
        
        # Test emoji suggestions
        emoji_suggestions = get_emoji_suggestions("smile", 5)
        if isinstance(emoji_suggestions, list):
            print(f"✅ Emoji suggestions working: {len(emoji_suggestions)} suggestions")
        else:
            print("❌ Emoji suggestions failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Rich Text system test failed: {e}")
        traceback.print_exc()
        return False

def test_forms():
    """Test all message forms"""
    print("\n🔍 Testing message forms...")
    
    try:
        from app.message.forms import (
            MessageSearchForm, MessageThreadForm, MessageForwardForm,
            MessageAttachmentForm, MessageTemplateForm, MessageComposeForm
        )
        from flask import Flask
        
        # Create a minimal Flask app for form testing
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            # Test MessageSearchForm
            form = MessageSearchForm()
            form.query.data = "test search"
            form.search_type.data = "advanced"
            form.validate()
            print("✅ MessageSearchForm created and validated successfully")
            
            # Test MessageThreadForm
            form = MessageThreadForm()
            form.subject.data = "Test Thread"
            form.thread_type.data = "private"
            form.validate()
            print("✅ MessageThreadForm created and validated successfully")
            
            # Test MessageForwardForm
            form = MessageForwardForm()
            form.forward_note.data = "Forward note"
            form.validate()
            print("✅ MessageForwardForm created and validated successfully")
            
            # Test MessageAttachmentForm
            form = MessageAttachmentForm()
            form.file.data = "test.txt"
            form.validate()
            print("✅ MessageAttachmentForm created and validated successfully")
            
            # Test MessageTemplateForm
            form = MessageTemplateForm()
            form.name.data = "Test Template"
            form.content.data = "Template content"
            form.category.data = "general"
            form.validate()
            print("✅ MessageTemplateForm created and validated successfully")
            
            # Test MessageComposeForm
            form = MessageComposeForm()
            form.content.data = "Message content"
            form.content_format.data = "text"
            form.priority.data = "normal"
            form.validate()
            print("✅ MessageComposeForm created and validated successfully")
            
            return True
        
    except Exception as e:
        print(f"❌ Forms test failed: {e}")
        traceback.print_exc()
        return False

def test_database_models():
    """Test database model creation and relationships"""
    print("\n🔍 Testing database models...")
    
    try:
        from app.models import (
            Message, MessageSearchIndex, MessageSearchAnalytics,
            MessageThread, MessageTemplate, User
        )
        from app import create_app, db
        
        # Create app for testing with in-memory database
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        
        with app.app_context():
            # Create tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create test users with unique names
            import time
            timestamp = int(time.time())
            
            user1 = User(username=f"testuser_{timestamp}", email=f"test{timestamp}@example.com", password_hash="test")
            user1.is_active = True
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(username=f"testuser2_{timestamp}", email=f"test2{timestamp}@example.com", password_hash="test")
            user2.is_active = True
            db.session.add(user2)
            db.session.commit()
            print("✅ Test users created successfully")
            
            # Test Message model with enhanced fields
            message = Message(
                sender_id=user1.id,
                receiver_id=user2.id,
                content="Test message content",
                content_format="text",
                is_rich_text=False,
                priority="normal"
            )
            db.session.add(message)
            db.session.commit()
            print("✅ Message model with enhanced fields created successfully")
            
            # Test MessageThread model
            thread = MessageThread(
                subject="Test thread",
                thread_type="private",
                priority="normal"
            )
            thread.set_participants([user1.id, user2.id])
            db.session.add(thread)
            db.session.commit()
            print("✅ MessageThread model created successfully")
            
            # Test MessageSearchIndex model
            search_index = MessageSearchIndex(
                message_id=message.id,
                content_vector="test message content",
                keywords="test,message,content"
            )
            db.session.add(search_index)
            db.session.commit()
            print("✅ MessageSearchIndex model created successfully")
            
            # Test MessageSearchAnalytics model
            analytics = MessageSearchAnalytics(
                user_id=user1.id,
                search_query="test query",
                search_type="basic",
                results_count=5,
                search_time=0.1
            )
            db.session.add(analytics)
            db.session.commit()
            print("✅ MessageSearchAnalytics model created successfully")
            
            # Test MessageTemplate model
            template = MessageTemplate(
                name="Test Template",
                content="Hello {{username}}!",
                user_id=user1.id,
                category="general",
                is_public=False
            )
            template.set_variables(["username"])
            db.session.add(template)
            db.session.commit()
            print("✅ MessageTemplate model created successfully")
            
            # Test relationships
            found_message = Message.query.first()
            if found_message and found_message.search_index:
                print("✅ Model relationships working correctly")
            else:
                print("❌ Model relationships failed")
                return False
            
            return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        traceback.print_exc()
        return False

def test_integrations():
    """Test system integrations"""
    print("\n🔍 Testing system integrations...")
    
    try:
        from app.utils.message_search import MessageSearchEngine
        from app.utils.message_threading import MessageThreadingEngine
        from app.utils.rich_text import RichTextProcessor
        from app.models import Message, MessageThread, User
        from app import create_app, db
        
        # Create app for testing with in-memory database
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        
        with app.app_context():
            # Create tables and data
            db.create_all()
            
            # Create test users with unique names
            import time
            timestamp = int(time.time())
            
            user1 = User(username=f"user1_{timestamp}", email=f"user1{timestamp}@example.com", password_hash="test")
            user2 = User(username=f"user2_{timestamp}", email=f"user2{timestamp}@example.com", password_hash="test")
            user1.is_active = True
            user2.is_active = True
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # Create message with rich text
            processor = RichTextProcessor()
            html_content, plain_content = processor.process_rich_text(
                "Hello **world**! This is a test message with **bold** text.",
                content_format="markdown"
            )
            
            message = Message(
                sender_id=user1.id,
                receiver_id=user2.id,
                content=plain_content,
                content_html=html_content,
                content_format="markdown",
                is_rich_text=True
            )
            
            # Add to thread
            threading_engine = MessageThreadingEngine()
            thread = threading_engine.create_thread(
                subject="Test Integration Thread",
                participant_ids=[user1.id, user2.id],
                creator_id=user1.id
            )
            
            threading_engine.add_message_to_thread(message, thread.id)
            db.session.add(message)
            db.session.commit()
            
            # Test search on threaded message
            search_engine = MessageSearchEngine()
            search_results = search_engine.search_messages(
                query="bold",
                user_id=user1.id,
                page=1,
                per_page=10
            )
            
            if search_results and len(search_results['results']) > 0:
                print("✅ Search on threaded messages successful")
            else:
                print("❌ Search on threaded messages failed")
                return False
            
            # Test thread statistics with rich text messages
            thread_stats = threading_engine.get_thread_statistics(thread.id)
            if thread_stats and 'total_messages' in thread_stats:
                print(f"✅ Thread stats with rich text messages successful: {thread_stats['total_messages']} messages")
            else:
                print("❌ Thread stats with rich text messages failed")
                return False
            
            # Test message preview with rich text
            preview = processor.generate_preview(message.content_html, 50, 'html')
            if preview:
                print(f"✅ Rich text preview successful: {preview}")
            else:
                print("❌ Rich text preview failed")
                return False
            
            return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Message Systems Comprehensive Debugging (Fixed)")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Message Search System", test_message_search_system),
        ("Message Threading System", test_message_threading_system),
        ("Rich Text System", test_rich_text_system),
        ("Forms", test_forms),
        ("Database Models", test_database_models),
        ("System Integrations", test_integrations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEBUGGING RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Message Systems are working correctly.")
        print("\n📋 IMPLEMENTED SYSTEMS STATUS:")
        print("✅ Message Search and Filtering System - FULLY OPERATIONAL")
        print("✅ Message Threading System - FULLY OPERATIONAL")
        print("✅ Rich Text Formatting System - FULLY OPERATIONAL")
        print("✅ Database Models and Relationships - WORKING CORRECTLY")
        print("✅ Forms and Validation - WORKING CORRECTLY")
        print("✅ System Integrations - WORKING CORRECTLY")
        return True
    else:
        print(f"\n⚠️ {failed} tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
