# Markdown Processing

## Overview

Posts support Markdown formatting with syntax highlighting, tables, and code blocks. Processed with python-markdown and sanitized with bleach.

## Supported Markdown

- Headers (H1-H6)
- Bold, italic, code
- Code blocks with syntax highlighting
- Tables
- Lists (ordered, unordered)
- Blockquotes
- Links
- Horizontal rules

## Implementation

```python
markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])
bleach.clean(html, tags=allowed_tags)
```

## Security

HTML sanitization prevents XSS attacks by removing dangerous tags and attributes.
