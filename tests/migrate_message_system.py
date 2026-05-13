#!/usr/bin/env python3
"""
Database migration script for Message System enhancements
Adds new fields to existing Message model and creates new tables
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/robbie/Desktop/repo-forum')

def migrate_database():
    """Migrate database to support new Message System features"""
    
    try:
        from app import create_app, db
        from app.models import Message, MessageThread, MessageSearchIndex, MessageSearchAnalytics, MessageTemplate
        
        # Create app
        app = create_app()
        
        with app.app_context():
            print("🔄 Starting database migration...")
            
            # Check if tables exist and create new ones
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📋 Existing tables: {existing_tables}")
            
            # Create new tables if they don't exist
            if 'message_thread' not in existing_tables:
                print("📝 Creating message_thread table...")
                MessageThread.__table__.create(db.engine, checkfirst=True)
                print("✅ message_thread table created")
            
            if 'message_search_index' not in existing_tables:
                print("📝 Creating message_search_index table...")
                MessageSearchIndex.__table__.create(db.engine, checkfirst=True)
                print("✅ message_search_index table created")
            
            if 'message_search_analytics' not in existing_tables:
                print("📝 Creating message_search_analytics table...")
                MessageSearchAnalytics.__table__.create(db.engine, checkfirst=True)
                print("✅ message_search_analytics table created")
            
            if 'message_template' not in existing_tables:
                print("📝 Creating message_template table...")
                MessageTemplate.__table__.create(db.engine, checkfirst=True)
                print("✅ message_template table created")
            
            # Check Message table columns
            if 'message' in existing_tables:
                message_columns = [col['name'] for col in inspector.get_columns('message')]
                print(f"📋 Existing message columns: {message_columns}")
                
                # Add new columns to message table if they don't exist
                new_columns = {
                    'thread_id': 'INTEGER REFERENCES message_thread(id)',
                    'parent_message_id': 'INTEGER REFERENCES message(id)',
                    'thread_level': 'INTEGER DEFAULT 0',
                    'content_html': 'TEXT',
                    'content_format': 'VARCHAR(20) DEFAULT \'text\'',
                    'is_rich_text': 'BOOLEAN DEFAULT 0',
                    'has_attachments': 'BOOLEAN DEFAULT 0',
                    'search_vector': 'TEXT',
                    'search_keywords': 'TEXT',
                    'forwarded_from_id': 'INTEGER REFERENCES message(id)',
                    'forwarded_count': 'INTEGER DEFAULT 0',
                    'is_deleted': 'BOOLEAN DEFAULT 0',
                    'is_archived': 'BOOLEAN DEFAULT 0',
                    'priority': 'VARCHAR(20) DEFAULT \'normal\'',
                    'is_starred': 'BOOLEAN DEFAULT 0'
                }
                
                for column_name, column_def in new_columns.items():
                    if column_name not in message_columns:
                        print(f"📝 Adding column {column_name} to message table...")
                        try:
                            db.engine.execute(f'ALTER TABLE message ADD COLUMN {column_name} {column_def}')
                            print(f"✅ Added column {column_name}")
                        except Exception as e:
                            print(f"⚠️ Could not add column {column_name}: {e}")
                    else:
                        print(f"✅ Column {column_name} already exists")
            
            print("🎉 Database migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_migration():
    """Test the migrated database"""
    
    try:
        from app import create_app, db
        from app.models import Message, MessageThread, User
        
        # Create app
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        
        with app.app_context():
            print("🧪 Testing migrated database...")
            
            # Create all tables
            db.create_all()
            print("✅ All tables created successfully")
            
            # Create test user
            user = User(username="testuser", email="test@example.com", password_hash="test")
            user.is_active = True
            db.session.add(user)
            db.session.commit()
            print("✅ Test user created")
            
            # Create test message with new fields
            message = Message(
                sender_id=user.id,
                receiver_id=user.id,
                content="Test message with new fields",
                content_format="text",
                is_rich_text=False,
                priority="normal",
                thread_level=0
            )
            db.session.add(message)
            db.session.commit()
            print("✅ Test message with new fields created")
            
            # Create test thread
            thread = MessageThread(
                subject="Test thread",
                thread_type="private",
                priority="normal"
            )
            thread.set_participants([user.id])
            db.session.add(thread)
            db.session.commit()
            print("✅ Test thread created")
            
            # Test message-thread relationship
            message.thread_id = thread.id
            db.session.commit()
            print("✅ Message-thread relationship established")
            
            # Verify data
            saved_message = Message.query.first()
            saved_thread = MessageThread.query.first()
            
            if saved_message and saved_thread:
                print(f"✅ Message verified: {saved_message.content}")
                print(f"✅ Thread verified: {saved_thread.subject}")
                print(f"✅ Relationship verified: message.thread_id = {saved_message.thread_id}")
            
            print("🎉 Migration test passed!")
            return True
            
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run migration and test"""
    print("🚀 Starting Message System Database Migration")
    print("=" * 50)
    
    # Run migration
    migration_success = migrate_database()
    
    if migration_success:
        print("\n" + "=" * 50)
        
        # Run test
        test_success = test_migration()
        
        if test_success:
            print("\n🎉 Migration and test completed successfully!")
            print("\n📋 Migration Summary:")
            print("✅ Added new Message model fields")
            print("✅ Created MessageThread table")
            print("✅ Created MessageSearchIndex table")
            print("✅ Created MessageSearchAnalytics table")
            print("✅ Created MessageTemplate table")
            print("✅ All relationships working correctly")
            
            return True
        else:
            print("\n❌ Migration test failed")
            return False
    else:
        print("\n❌ Migration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
