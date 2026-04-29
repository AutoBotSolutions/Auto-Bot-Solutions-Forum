# File Upload System

## Overview

Users can attach files to posts. Files are validated by type and stored in the uploads directory.

## Supported File Types

- Images: PNG, JPG, JPEG, GIF
- Documents: PDF, TXT, MD

## Upload Process

1. User selects file in post form
2. File type validated
3. Filename sanitized
4. Timestamp added for uniqueness
5. Saved to `app/static/uploads/`
6. Filename stored in database
7. Displayed in post with download link

## Security

- File type whitelist
- Filename sanitization
- Unique filenames
- No size limit (add in production)
- Served from static folder
