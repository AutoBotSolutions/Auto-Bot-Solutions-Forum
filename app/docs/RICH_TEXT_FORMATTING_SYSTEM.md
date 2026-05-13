# Rich Text Formatting System

## Overview

The Rich Text Formatting System provides comprehensive text processing capabilities for private messages, including WYSIWYG editor support, HTML sanitization, Markdown processing, emoji support, and message templates. This system enables users to create rich, formatted messages with security and performance optimization.

## Features

### 📝 **Text Processing**
- **Markdown processing** with syntax highlighting
- **HTML sanitization** with security filtering
- **Rich text editing** with WYSIWYG support
- **Content validation** and format detection
- **Text-to-HTML conversion** with URL linking
- **Plain text extraction** from HTML content

### 😊 **Emoji and Stickers**
- **Emoji shortcode conversion** (e.g., `:smile:` → 😊)
- **Emoji suggestions** with search functionality
- **30+ emoji shortcodes** supported
- **Unicode emoji support** for modern devices
- **Emoji preview** in message composition

### 📋 **Message Templates**
- **Template creation** with variable substitution
- **Template management** (create, edit, delete)
- **Public/private templates** with sharing options
- **Template variables** with system integration
- **Template usage analytics** and statistics

### 🔒 **Security and Performance**
- **HTML sanitization** with bleach library
- **Content validation** and security filtering
- **XSS protection** and safe HTML rendering
- **Performance optimization** with caching
- **Content preview** with truncation

## Architecture

### Core Components

#### **RichTextProcessor** (`app/utils/rich_text.py`)
```python
class RichTextProcessor:
    """Advanced rich text processor with security and formatting capabilities"""
    
    def process_rich_text(self, content, content_format='html', sanitize=True)
    def _process_markdown(self, content)
    def _text_to_html(self, content)
    def _sanitize_html(self, content)
    def _convert_emoji(self, content)
    def _html_to_text(self, content)
    def generate_preview(self, content, max_length=200, content_format='html')
    def validate_formatting(self, content, content_format='text')
```

#### **MessageTemplateManager** (`app/utils/rich_text.py`)
```python
class MessageTemplateManager:
    """Message template management system"""
    
    def create_template(self, name, content, user_id, category='general')
    def get_template(self, template_id, user_id)
    def get_user_templates(self, user_id, category=None, include_public=True)
    def render_template(self, template_id, user_id, variables=None)
    def update_template(self, template_id, user_id, **updates)
    def delete_template(self, template_id, user_id)
```

#### **MessageTemplate** (Database Model)
```python
class MessageTemplate(db.Model):
    """Model for message templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(50), default='general')
    variables = db.Column(db.Text)  # JSON array of variables
    is_public = db.Column(db.Boolean, default=False)
    
    # Usage statistics
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
```

#### **Message Model Enhancements**
```python
class Message(db.Model):
    # ... existing fields ...
    
    # Rich text fields
    content_html = db.Column(db.Text)
    content_format = db.Column(db.String(20), default='text')
    is_rich_text = db.Column(db.Boolean, default=False)
```

## API Endpoints

### Rich Text Routes

#### **POST `/messages/compose`**
**Enhanced message composition with rich text support**

**Request Body:**
```json
{
    "receiver_id": 2,
    "content": "Hello **world**! This is a **test** message.",
    "content_format": "markdown",
    "priority": "normal",
    "create_thread": false,
    "thread_subject": "",
    "use_template": 0
}
```

**Response:**
```json
{
    "success": true,
    "message": "Message sent successfully!",
    "message_id": 123
}
```

#### **GET `/messages/templates`**
**List message templates for the current user**

**Parameters:**
- `category` (string): Filter by template category
- `public` (boolean): Include public templates

**Response:**
```json
{
    "templates": [
        {
            "id": 1,
            "name": "Welcome Message",
            "content": "Hello {{username}}, welcome to {{forum_name}}!",
            "category": "welcome",
            "variables": ["username", "forum_name"],
            "is_public": true,
            "is_owner": false,
            "created_at": "2024-01-01T10:00:00"
        }
    ]
}
```

#### **POST `/messages/templates/create`**
**Create a new message template**

**Request Body:**
```json
{
    "name": "Project Update",
    "content": "Hi {{username}},\n\nThe project status: {{status}}\n\nBest regards,\n{{sender}}",
    "category": "project",
    "variables": "username, status, sender",
    "is_public": false
}
```

#### **POST `/messages/templates/<int:template_id>/edit`**
**Edit an existing template**

#### **POST `/messages/templates/<int:template_id>/delete`**
**Delete a template**

#### **GET `/messages/templates/<int:template_id>/preview`**
**Preview a template**

**Response:**
```json
{
    "name": "Welcome Message",
    "preview": "Hello john_doe, welcome to Auto Bot Solutions Forum!",
    "variables": ["username", "forum_name"]
}
```

#### **POST `/messages/templates/<int:template_id>/render`**
**Render a template with variables**

**Request Body:**
```json
{
    "variables": {
        "username": "john_doe",
        "forum_name": "Auto Bot Solutions Forum"
    }
}
```

**Response:**
```json
{
    "html": "<p>Hello john_doe, welcome to Auto Bot Solutions Forum!</p>",
    "text": "Hello john_doe, welcome to Auto Bot Solutions Forum!"
}
```

#### **POST `/messages/rich-text/preview`**
**Preview rich text content**

**Request Body:**
```json
{
    "content": "Hello **world**! This is a test.",
    "format": "markdown",
    "max_length": 100
}
```

**Response:**
```json
{
    "preview": "Hello world! This is a test."
}
```

#### **POST `/messages/rich-text/validate`**
**Validate rich text content**

**Request Body:**
```json
{
    "content": "Hello **world**!",
    "format": "markdown"
}
```

**Response:**
```json
{
    "valid": true,
    "errors": [],
    "warnings": [],
    "stats": {
        "character_count": 14,
        "word_count": 2,
        "line_count": 1,
        "has_links": false,
        "has_images": false,
        "has_code": false
    }
}
```

#### **POST `/messages/rich-text/format`**
**Format rich text content**

**Request Body:**
```json
{
    "content": "Hello **world**!",
    "format": "markdown",
    "sanitize": true,
    "enable_emoji": true,
    "enable_markdown": true
}
```

**Response:**
```json
{
    "html": "<p>Hello <strong>world</strong>!</p>",
    "text": "Hello world!"
}
```

#### **GET `/messages/emoji/suggestions`**
**Get emoji suggestions**

**Parameters:**
- `q` (string): Search query
- `limit` (integer): Maximum suggestions (default: 20)

**Response:**
```json
{
    "suggestions": [
        {
            "shortcode": ":smile:",
            "emoji": "😊",
            "description": "Smile"
        },
        {
            "shortcode": ":heart:",
            "emoji": "❤️",
            "description": "Heart"
        }
    ]
}
```

## Content Formats

### **Text Format**
Plain text with automatic URL linking and basic formatting.

**Example:**
```
Hello world! Check out https://example.com for more info.
```

**Output:**
```html
Hello world! Check out <a href="https://example.com" target="_blank">https://example.com</a> for more info.
```

### **Markdown Format**
Full Markdown support with syntax highlighting.

**Example:**
```markdown
# Hello World

This is **bold** and *italic* text.

## Code Example

```python
def hello():
    print("Hello, World!")
```

### Lists
- Item 1
- Item 2
- Item 3

### Links
[Example](https://example.com)
```

**Output:**
```html
<h1>Hello World</h1>
<p>This is <strong>bold</strong> and <em>italic</em> text.</p>
<h2>Code Example</h2>
<div class="highlight"><pre><code><span class="k">def</span> <span class="nf">hello</span><span class="p">():</span>
    <span class="nb">print</span><span class="p">(</span><span class="s2">"Hello, World!"</span><span class="p">)</span></code></pre></div>
<h3>Lists</h3>
<ul>
<li>Item 1</li>
<li>Item 2</li>
<li>Item 3</li>
</ul>
<h3>Links</h3>
<p><a href="https://example.com">Example</a></p>
```

### **HTML Format**
Direct HTML with security sanitization.

**Allowed Tags:**
- Text formatting: `p`, `br`, `strong`, `em`, `u`, `i`, `b`, `span`, `div`
- Headings: `h1`, `h2`, `h3`, `h4`, `h5`, `h6`
- Lists: `ul`, `ol`, `li`, `dl`, `dt`, `dd`
- Code: `pre`, `code`
- Links: `a`
- Images: `img`
- Tables: `table`, `thead`, `tbody`, `tr`, `th`, `td`
- Other: `hr`, `sub`, `sup`, `small`, `del`, `ins`

## Emoji Support

### **Supported Shortcodes**
```text
:smile: 😊
:laugh: 😂
:heart: ❤️
:thumbsup: 👍
:thumbsdown: 👎
:fire: 🔥
:star: ⭐
:check: ✅
:x: ❌
:warning: ⚠️
:info: ℹ️
:question: ❓
:exclamation: ❗
:thinking: 🤔
:ok: 👌
:wave: 👋
:pray: 🙏
:clap: 👏
:party: 🎉
:gift: 🎁
:rocket: 🚀
:bulb: 💡
:coffee: ☕
:pizza: 🍕
:beer: 🍺
:cake: 🎂
:heart_eyes: 😍
:cry: 😢
:angry: 😠
:cool: 😎
:sleepy: 😴
:sick: 🤒
:happy: 😄
:sad: 😢
:love: 😍
:hate: 😠
```

### **Usage Examples**
```text
Hello :smile: world! :thumbsup:
I'm :thinking: about this :fire: project.
:party: Time to celebrate! :cake:
```

**Output:**
```html
Hello 😊 world! 👍
I'm 🤔 about this 🔥 project.
🎉 Time to celebrate! 🎂
```

## Message Templates

### **Template Variables**
Templates support variable substitution with the following syntax:

```text
{{variable_name}}
```

### **System Variables**
Built-in variables available in all templates:

```text
{{username}}        - Current user's username
{{user_email}}      - Current user's email
{{current_date}}    - Current date (YYYY-MM-DD)
{{current_time}}    - Current time (HH:MM:SS)
{{forum_name}}      - Forum name
{{site_url}}        - Site URL
```

### **Template Categories**
- **general** - General purpose templates
- **welcome** - Welcome messages
- **support** - Customer support responses
- **project** - Project updates
- **announcement** - System announcements
- **personal** - Personal message templates

### **Template Examples**

#### **Welcome Template**
```text
Hello {{username}},

Welcome to {{forum_name}}! We're excited to have you join our community.

If you have any questions, feel free to reach out.

Best regards,
The {{forum_name}} Team
```

#### **Project Update Template**
```text
Hi {{username}},

Project Update: {{project_name}}

Status: {{status}}
Progress: {{progress}}%

{{details}}

Next steps: {{next_steps}}

Best regards,
{{sender}}
```

#### **Support Response Template**
```text
Hello {{username}},

Thank you for contacting support regarding: {{issue}}

I understand that you're experiencing {{problem_description}}.

{{solution}}

If you need further assistance, please don't hesitate to contact us.

Best regards,
Support Team
```

## Database Schema

### **Message Model Enhancements**
```sql
ALTER TABLE message ADD COLUMN content_html TEXT;
ALTER TABLE message ADD COLUMN content_format VARCHAR(20) DEFAULT 'text';
ALTER TABLE message ADD COLUMN is_rich_text BOOLEAN DEFAULT FALSE;
```

### **MessageTemplate Table**
```sql
CREATE TABLE message_template (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER REFERENCES user(id),
    category VARCHAR(50) DEFAULT 'general',
    variables TEXT,  -- JSON array of variables
    is_public BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    last_used DATETIME
);
```

## Utility Functions

### **Rich Text Utilities** (`app/utils/rich_text.py`)

#### **format_message_content(content, content_format='text', ...)**
Format message content based on format type.

```python
html_content, plain_text = format_message_content(
    content="Hello **world**!",
    content_format="markdown",
    sanitize=True,
    enable_emoji=True,
    enable_markdown=True
)
```

#### **generate_message_preview(content, max_length=200, content_format='text')**
Generate a preview of message content.

```python
preview = generate_message_preview(
    content="This is a long message for preview testing...",
    max_length=50,
    content_format="html"
)
```

#### **validate_message_content(content, content_format='text')**
Validate message content and return statistics.

```python
validation = validate_message_content(
    content="Hello **world**!",
    content_format="markdown"
)
```

#### **get_emoji_suggestions(query='', limit=20)**
Get emoji suggestions based on query.

```python
suggestions = get_emoji_suggestions(query="smile", limit=10)
```

#### **convert_text_to_emoji(text)**
Convert text with emoji shortcodes to actual emojis.

```python
converted = convert_text_to_emoji("Hello :smile: world!")
# Returns: "Hello 😊 world!"
```

## Security Considerations

### **HTML Sanitization**
- **Bleach library** for XSS protection
- **Whitelist approach** for allowed tags and attributes
- **Style filtering** for CSS security
- **Compatibility fallback** for older bleach versions

### **Content Validation**
- **Input length limits** for message content
- **Format validation** for content types
- **Malicious content detection**
- **Template variable validation**

### **Access Control**
- **Template ownership** validation
- **Public template** access control
- **User-specific content** isolation
- **Permission-based template** sharing

## Performance Optimization

### **Content Processing**
- **Markdown caching** for frequently used content
- **Emoji conversion** optimization
- **HTML sanitization** efficiency
- **Template rendering** caching

### **Database Optimization**
- **Template indexing** for fast retrieval
- **Usage statistics** optimization
- **Content storage** efficiency
- **Query optimization** for template lists

### **Caching Strategy**
- **Rendered content** caching
- **Template compilation** caching
- **Emoji mapping** caching
- **Validation results** caching

## Usage Examples

### **Basic Rich Text Processing**
```python
from app.utils.rich_text import format_message_content

# Process Markdown content
html_content, plain_text = format_message_content(
    content="Hello **world**! This is a test.",
    content_format="markdown",
    sanitize=True,
    enable_emoji=True
)

print(f"HTML: {html_content}")
print(f"Plain: {plain_text}")
```

### **Template Management**
```python
from app.utils.rich_text import MessageTemplateManager

template_manager = MessageTemplateManager()

# Create template
template = template_manager.create_template(
    name="Welcome Message",
    content="Hello {{username}}, welcome to {{forum_name}}!",
    user_id=current_user.id,
    category="welcome",
    variables=["username", "forum_name"],
    is_public=True
)

# Render template
rendered = template_manager.render_template(
    template_id=template.id,
    user_id=current_user.id,
    variables={
        "username": "john_doe",
        "forum_name": "Auto Bot Solutions Forum"
    }
)
```

### **Emoji Conversion**
```python
from app.utils.rich_text import convert_text_to_emoji, get_emoji_suggestions

# Convert emoji shortcodes
text = "Hello :smile: world! :thumbsup:"
converted = convert_text_to_emoji(text)
# Returns: "Hello 😊 world! 👍"

# Get emoji suggestions
suggestions = get_emoji_suggestions(query="smile", limit=5)
```

### **Content Validation**
```python
from app.utils.rich_text import validate_message_content

validation = validate_message_content(
    content="Hello **world**!",
    content_format="markdown"
)

if validation['valid']:
    print("Content is valid")
    print(f"Character count: {validation['stats']['character_count']}")
    print(f"Word count: {validation['stats']['word_count']}")
else:
    print("Content validation failed:")
    for error in validation['errors']:
        print(f"- {error}")
```

### **Message Preview**
```python
from app.utils.rich_text import generate_message_preview

preview = generate_message_preview(
    content="This is a very long message that needs to be truncated for preview purposes...",
    max_length=100,
    content_format="html"
)

print(f"Preview: {preview}")
```

## Troubleshooting

### **Common Issues**

#### **HTML Sanitization Not Working**
- Check bleach library version compatibility
- Verify allowed tags and attributes configuration
- Ensure content is properly encoded before sanitization

#### **Emoji Conversion Not Working**
- Verify emoji shortcode mapping is correct
- Check if emoji shortcodes are properly formatted
- Ensure emoji conversion is enabled in processing

#### **Template Variables Not Replacing**
- Check variable syntax ({{variable_name}})
- Verify template variables are properly defined
- Ensure all required variables are provided in rendering

#### **Markdown Processing Issues**
- Verify markdown extensions are properly loaded
- Check for syntax errors in markdown content
- Ensure content format is correctly specified

### **Debug Mode**
Enable debug logging for rich text operations:

```python
import logging
logging.getLogger('app.utils.rich_text').setLevel(logging.DEBUG)
```

## Migration Guide

### **Database Migration**
Run the migration script to add rich text fields:

```bash
python migrate_message_system.py
```

### **Existing Message Migration**
Migrate existing messages to rich text format:

```python
from app.utils.rich_text import format_message_content
from app.models import Message

messages = Message.query.filter(Message.content_html.is_(None)).all()
for message in messages:
    # Process existing content
    html_content, plain_text = format_message_content(
        content=message.content,
        content_format="text",
        sanitize=True,
        enable_emoji=True
    )
    
    # Update message with rich text fields
    message.content_html = html_content
    message.content_format = "text"
    message.is_rich_text = False
    
    db.session.commit()
```

## Future Enhancements

### **Planned Features**
- **WYSIWYG Editor** integration with real-time preview
- **Advanced Emoji** support with custom emojis
- **Template Sharing** between users
- **Content Templates** for different message types
- **Rich Text Export** to various formats

### **Performance Improvements**
- **Real-time Processing** with WebSocket
- **Advanced Caching** with Redis
- **Content Optimization** for mobile devices
- **Lazy Loading** for large content

### **Security Enhancements**
- **Advanced Sanitization** with custom rules
- **Content Scanning** for malicious content
- **Template Validation** with security checks
- **Rate Limiting** for content processing

---

**Documentation Version:** 1.0  
**Last Updated:** May 12, 2026  
**System:** Auto Bot Solutions Forum - Rich Text Formatting System
