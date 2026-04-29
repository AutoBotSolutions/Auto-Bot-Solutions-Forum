# Rate Limiting

## Overview

Rate limiting prevents abuse and protects against brute force attacks. Implemented using Flask-Limiter with IP-based limiting.

## Current Limits

- Login: 10 requests per minute
- Register: 3 requests per hour
- Create post: 5 requests per hour
- Add comment: 20 requests per hour
- Vote: 30 requests per minute
- API sync: 5 requests per hour

## Implementation

```python
@limiter.limit("10 per minute")
def login():
    # route handler
```

## Response Headers

- `X-RateLimit-Limit`: Maximum requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp
