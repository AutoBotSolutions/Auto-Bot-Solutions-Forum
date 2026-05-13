# Enhanced Voting and Reputation System API Reference

**Version:** 1.0.0  
**Last Updated:** May 11, 2026  
**Base URL:** `/reputation/api`  

---

## 📋 Overview

The Enhanced Voting and Reputation System provides comprehensive REST API endpoints for accessing reputation data, voting analytics, pattern analysis, and voting operations. All endpoints require authentication and return JSON responses.

### Authentication
All API endpoints require user authentication. Include session cookie or authentication token in requests.

### Response Format
All endpoints return JSON responses with the following structure:
```json
{
    "success": true,
    "data": {},
    "message": "Success",
    "timestamp": "2026-05-11T23:00:00Z"
}
```

---

## 🏆 Reputation Data Endpoints

### Get User Reputation

**Endpoint:** `GET /reputation/api/reputation/<user_id>`

**Description:** Retrieve comprehensive reputation data for a specific user.

**Parameters:**
- `user_id` (path, required): User ID to retrieve reputation for

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "reputation_score": 250,
        "voting_power": 1.5,
        "trust_score": 0.8,
        "current_level": "Trusted",
        "level_progress": 0.25,
        "total_votes_cast": 150,
        "upvotes_given": 120,
        "downvotes_given": 30,
        "votes_received": 85,
        "helpful_votes_received": 65,
        "controversial_votes": 8,
        "consensus_votes": 12,
        "posts_created": 25,
        "comments_created": 45,
        "days_active": 180,
        "current_streak": 7,
        "longest_streak": 15,
        "last_activity_date": "2026-05-11",
        "penalty_points": 0,
        "bonus_points": 25,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-05-11T23:00:00Z",
        "last_calculated": "2026-05-11T23:00:00Z"
    },
    "message": "Reputation data retrieved successfully"
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:5000/reputation/api/reputation/1" \
     -H "Cookie: session=your_session_cookie"
```

---

### Get Multiple User Reputations

**Endpoint:** `POST /reputation/api/reputations/bulk`

**Description:** Retrieve reputation data for multiple users in a single request.

**Request Body:**
```json
{
    "user_ids": [1, 2, 3, 4, 5]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "reputations": [
            {
                "user_id": 1,
                "reputation_score": 250,
                "voting_power": 1.5,
                "current_level": "Trusted"
            },
            {
                "user_id": 2,
                "reputation_score": 75,
                "voting_power": 1.0,
                "current_level": "Member"
            }
        ]
    },
    "message": "Bulk reputation data retrieved successfully"
}
```

---

## 📊 Voting Analytics Endpoints

### Get Voting Analytics

**Endpoint:** `GET /reputation/api/voting_analytics/<user_id>`

**Description:** Retrieve comprehensive voting analytics for a user.

**Parameters:**
- `user_id` (path, required): User ID to analyze
- `days` (query, optional): Number of days to analyze (default: 30)

**Response:**
```json
{
    "success": true,
    "data": {
        "period_days": 30,
        "total_votes": 45,
        "upvotes": 35,
        "downvotes": 10,
        "vote_weight_avg": 1.2,
        "most_voted_day": "2026-05-10",
        "most_voted_hour": 14,
        "reason_categories": {
            "helpful": 15,
            "informative": 10,
            "well_written": 8,
            "unclear": 5,
            "off_topic": 7
        },
        "votes_by_day": {
            "2026-05-10": 12,
            "2026-05-11": 8,
            "2026-05-12": 15,
            "2026-05-13": 10
        },
        "votes_by_hour": {
            "9": 3,
            "10": 5,
            "11": 4,
            "12": 6,
            "13": 8,
            "14": 9,
            "15": 10
        },
        "target_distribution": {
            "posts": 30,
            "comments": 15
        },
        "reputation_impact": {
            "positive_impact": 125.5,
            "negative_impact": -15.0,
            "net_impact": 110.5
        }
    },
    "message": "Voting analytics retrieved successfully"
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:5000/reputation/api/voting_analytics/1?days=30" \
     -H "Cookie: session=your_session_cookie"
```

---

### Get Voting Statistics

**Endpoint:** `GET /reputation/api/voting_statistics`

**Description:** Retrieve system-wide voting statistics.

**Parameters:**
- `period` (query, optional): Analysis period (day, week, month, year)
- `start_date` (query, optional): Start date (YYYY-MM-DD)
- `end_date` (query, optional): End date (YYYY-MM-DD)

**Response:**
```json
{
    "success": true,
    "data": {
        "period": "month",
        "total_votes": 15420,
        "upvotes": 12350,
        "downvotes": 3070,
        "unique_voters": 892,
        "unique_targets": 2341,
        "most_active_voter": {
            "user_id": 42,
            "votes_cast": 156
        },
        "most_voted_content": {
            "target_type": "post",
            "target_id": 1234,
            "total_votes": 89
        },
        "top_reason_categories": {
            "helpful": 4521,
            "informative": 3120,
            "well_written": 2156,
            "unclear": 892,
            "off_topic": 756
        },
        "voting_trends": {
            "daily_averages": [514, 498, 523, 487, 531],
            "growth_rate": 0.12
        }
    },
    "message": "Voting statistics retrieved successfully"
}
```

---

## 🔍 Pattern Analysis Endpoints

### Get Voting Patterns

**Endpoint:** `GET /reputation/api/voting_patterns/<user_id>`

**Description:** Retrieve voting pattern analysis for a user.

**Parameters:**
- `user_id` (path, required): User ID to analyze
- `period_days` (query, optional): Analysis period in days (default: 90)

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "analysis_period_days": 90,
        "sample_size": 156,
        "patterns": {
            "consistency": {
                "pattern_value": 0.85,
                "description": "Highly consistent",
                "upvote_ratio": 0.78,
                "sample_size": 156,
                "confidence_score": 0.92,
                "statistical_significance": 0.88
            },
            "bias": {
                "pattern_value": 0.25,
                "description": "Low bias",
                "unique_targets": 89,
                "most_voted_target": 3,
                "target_concentration": 0.03,
                "sample_size": 156,
                "confidence_score": 0.75,
                "statistical_significance": 0.72
            },
            "timing": {
                "pattern_value": 0.70,
                "description": "Business hours voter",
                "business_hours_ratio": 0.82,
                "peak_hour": 14,
                "weekend_ratio": 0.15,
                "sample_size": 156,
                "confidence_score": 0.85,
                "statistical_significance": 0.81
            },
            "quality": {
                "pattern_value": 0.65,
                "description": "Quality voter",
                "quality_ratio": 0.75,
                "negative_ratio": 0.10,
                "reasons_provided": 140,
                "sample_size": 156,
                "confidence_score": 0.78,
                "statistical_significance": 0.74
            }
        },
        "overall_score": 0.71,
        "last_analyzed": "2026-05-11T23:00:00Z"
    },
    "message": "Voting patterns retrieved successfully"
}
```

---

### Get System Pattern Analysis

**Endpoint:** `GET /reputation/api/system_patterns`

**Description:** Retrieve system-wide voting pattern analysis.

**Parameters:**
- `pattern_type` (query, optional): Specific pattern type (consistency, bias, timing, quality)
- `period_days` (query, optional): Analysis period in days (default: 30)

**Response:**
```json
{
    "success": true,
    "data": {
        "period_days": 30,
        "total_analyzed_users": 892,
        "system_patterns": {
            "consistency": {
                "average_score": 0.72,
                "distribution": {
                    "high": 0.35,
                    "medium": 0.45,
                    "low": 0.20
                },
                "trends": {
                    "improving": 0.58,
                    "stable": 0.32,
                    "declining": 0.10
                }
            },
            "bias": {
                "average_score": 0.31,
                "distribution": {
                    "low_bias": 0.65,
                    "moderate_bias": 0.25,
                    "high_bias": 0.10
                }
            },
            "timing": {
                "average_score": 0.68,
                "peak_hours": [14, 15, 16],
                "business_hours_ratio": 0.76
            },
            "quality": {
                "average_score": 0.71,
                "reason_provision_rate": 0.82,
                "quality_ratio": 0.78
            }
        }
    },
    "message": "System patterns retrieved successfully"
}
```

---

## 🏆 Leaderboard Endpoints

### Get Leaderboard

**Endpoint:** `GET /reputation/api/leaderboard`

**Description:** Retrieve reputation leaderboard data.

**Parameters:**
- `type` (query, required): Leaderboard type
  - `reputation`: Sort by reputation score
  - `voting_power`: Sort by voting power
  - `trust_score`: Sort by trust score
  - `most_votes`: Sort by total votes cast
  - `most_upvotes`: Sort by upvotes given
- `limit` (query, optional): Number of results (default: 50, max: 100)
- `offset` (query, optional): Pagination offset (default: 0)
- `level` (query, optional): Filter by reputation level
- `min_reputation` (query, optional): Minimum reputation score

**Response:**
```json
{
    "success": true,
    "data": {
        "leaderboard_type": "reputation",
        "total_users": 892,
        "page_info": {
            "limit": 50,
            "offset": 0,
            "has_next": true,
            "has_previous": false
        },
        "rankings": [
            {
                "rank": 1,
                "user_id": 42,
                "username": "expert_user",
                "reputation_score": 2847,
                "voting_power": 3.0,
                "trust_score": 0.95,
                "current_level": "Master",
                "total_votes_cast": 523,
                "posts_created": 89,
                "comments_created": 234,
                "current_streak": 45
            },
            {
                "rank": 2,
                "user_id": 17,
                "username": "trusted_member",
                "reputation_score": 2156,
                "voting_power": 2.0,
                "trust_score": 0.88,
                "current_level": "Expert",
                "total_votes_cast": 412,
                "posts_created": 67,
                "comments_created": 189,
                "current_streak": 23
            }
        ]
    },
    "message": "Leaderboard retrieved successfully"
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:5000/reputation/api/leaderboard?type=reputation&limit=10" \
     -H "Cookie: session=your_session_cookie"
```

---

### Get User Rank

**Endpoint:** `GET /reputation/api/user_rank/<user_id>`

**Description:** Get a user's rank across different leaderboards.

**Parameters:**
- `user_id` (path, required): User ID to get rank for

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 42,
        "ranks": {
            "reputation": {
                "rank": 1,
                "total_users": 892,
                "percentile": 99.9
            },
            "voting_power": {
                "rank": 3,
                "total_users": 892,
                "percentile": 99.7
            },
            "trust_score": {
                "rank": 5,
                "total_users": 892,
                "percentile": 99.4
            },
            "most_votes": {
                "rank": 8,
                "total_users": 892,
                "percentile": 99.1
            }
        },
        "best_rank": 1,
        "best_category": "reputation"
    },
    "message": "User rank retrieved successfully"
}
```

---

## 🗳️ Voting Operations Endpoints

### Cast Vote

**Endpoint:** `POST /reputation/api/vote`

**Description:** Cast a vote on content with optional reason.

**Request Body:**
```json
{
    "vote_type": "upvote",
    "target_type": "post",
    "target_id": 1234,
    "reason_category": "helpful",
    "reason": "This answer really helped me solve my problem"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "vote_id": 123456,
        "vote_type": "upvote",
        "target_type": "post",
        "target_id": 1234,
        "vote_weight": 1.5,
        "reputation_impact": 15.0,
        "target_upvotes": 25,
        "target_downvotes": 3,
        "user_reputation_change": 2.5,
        "user_voting_power": 1.5,
        "created_at": "2026-05-11T23:00:00Z"
    },
    "message": "Vote cast successfully"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/reputation/api/vote" \
     -H "Content-Type: application/json" \
     -H "Cookie: session=your_session_cookie" \
     -d '{
         "vote_type": "upvote",
         "target_type": "post",
         "target_id": 1234,
         "reason_category": "helpful",
         "reason": "Great content!"
     }'
```

---

### Get Vote History

**Endpoint:** `GET /reputation/api/vote_history/<user_id>`

**Description:** Get voting history for a user.

**Parameters:**
- `user_id` (path, required): User ID to get history for
- `limit` (query, optional): Number of results (default: 50, max: 100)
- `offset` (query, optional): Pagination offset (default: 0)
- `target_type` (query, optional): Filter by target type (post, comment)
- `vote_type` (query, optional): Filter by vote type (upvote, downvote)
- `start_date` (query, optional): Start date (YYYY-MM-DD)
- `end_date` (query, optional): End date (YYYY-MM-DD)

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "total_votes": 156,
        "page_info": {
            "limit": 50,
            "offset": 0,
            "has_next": true,
            "has_previous": false
        },
        "votes": [
            {
                "vote_id": 123456,
                "vote_type": "upvote",
                "target_type": "post",
                "target_id": 1234,
                "target_title": "How to implement weighted voting",
                "reason_category": "helpful",
                "reason": "Comprehensive explanation with examples",
                "vote_weight": 1.5,
                "reputation_impact": 15.0,
                "created_at": "2026-05-11T14:30:00Z"
            },
            {
                "vote_id": 123455,
                "vote_type": "downvote",
                "target_type": "comment",
                "target_id": 5678,
                "target_content": "This doesn't seem right...",
                "reason_category": "inaccurate",
                "reason": "Information is outdated and incorrect",
                "vote_weight": 1.5,
                "reputation_impact": -3.0,
                "created_at": "2026-05-11T13:15:00Z"
            }
        ]
    },
    "message": "Vote history retrieved successfully"
}
```

---

### Revoke Vote

**Endpoint:** `DELETE /reputation/api/vote/<target_type>/<target_id>`

**Description:** Revoke a previously cast vote.

**Parameters:**
- `target_type` (path, required): Target type (post, comment)
- `target_id` (path, required): Target ID

**Response:**
```json
{
    "success": true,
    "data": {
        "revoked_vote_id": 123456,
        "target_type": "post",
        "target_id": 1234,
        "reputation_impact_reverted": -15.0,
        "target_upvotes": 24,
        "target_downvotes": 3,
        "revoked_at": "2026-05-11T23:05:00Z"
    },
    "message": "Vote revoked successfully"
}
```

---

## 📈 Analytics Endpoints

### Get Reputation Trends

**Endpoint:** `GET /reputation/api/reputation_trends/<user_id>`

**Description:** Get reputation score trends over time.

**Parameters:**
- `user_id` (path, required): User ID to analyze
- `period_days` (query, optional): Analysis period (default: 90)
- `granularity` (query, optional): Data granularity (daily, weekly, monthly)

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "period_days": 90,
        "granularity": "daily",
        "trends": [
            {
                "date": "2026-02-10",
                "reputation_score": 185,
                "level": "Member",
                "votes_cast": 2,
                "reputation_change": 5.0
            },
            {
                "date": "2026-02-11",
                "reputation_score": 192,
                "level": "Member",
                "votes_cast": 3,
                "reputation_change": 7.0
            }
        ],
        "summary": {
            "starting_score": 150,
            "ending_score": 250,
            "net_change": 100,
            "average_daily_change": 1.11,
            "best_day": "2026-04-15",
            "worst_day": "2026-03-22"
        }
    },
    "message": "Reputation trends retrieved successfully"
}
```

---

### Get System Analytics

**Endpoint:** `GET /reputation/api/system_analytics`

**Description:** Get system-wide reputation and voting analytics.

**Parameters:**
- `period_days` (query, optional): Analysis period (default: 30)

**Response:**
```json
{
    "success": true,
    "data": {
        "period_days": 30,
        "total_users": 892,
        "active_users": 456,
        "total_votes_cast": 15420,
        "reputation_distribution": {
            "Newcomer": 234,
            "Member": 345,
            "Trusted": 189,
            "Expert": 98,
            "Master": 23,
            "Legend": 3
        },
        "voting_activity": {
            "daily_average": 514,
            "peak_day": "2026-05-10",
            "least_active_day": "2026-05-03"
        },
        "reputation_metrics": {
            "average_reputation": 156.7,
            "median_reputation": 89.0,
            "highest_reputation": 2847,
            "reputation_growth_rate": 0.08
        },
        "quality_metrics": {
            "reason_provision_rate": 0.82,
            "average_vote_weight": 1.24,
            "pattern_consistency_avg": 0.72
        }
    },
    "message": "System analytics retrieved successfully"
}
```

---

## 🎯 Search and Filter Endpoints

### Search Users by Reputation

**Endpoint:** `POST /reputation/api/search_users`

**Description:** Search for users based on reputation criteria.

**Request Body:**
```json
{
    "filters": {
        "min_reputation": 100,
        "max_reputation": 1000,
        "level": ["Member", "Trusted"],
        "min_voting_power": 1.0,
        "min_trust_score": 0.5
    },
    "sort": {
        "field": "reputation_score",
        "order": "desc"
    },
    "pagination": {
        "limit": 20,
        "offset": 0
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "total_results": 156,
        "page_info": {
            "limit": 20,
            "offset": 0,
            "has_next": true,
            "has_previous": false
        },
        "users": [
            {
                "user_id": 42,
                "username": "expert_user",
                "reputation_score": 856,
                "voting_power": 2.0,
                "trust_score": 0.92,
                "current_level": "Expert",
                "total_votes_cast": 234,
                "posts_created": 45,
                "comments_created": 123
            }
        ]
    },
    "message": "User search completed successfully"
}
```

---

## 🔧 Configuration Endpoints

### Get Reason Categories

**Endpoint:** `GET /reputation/api/reason_categories`

**Description:** Get all available voting reason categories.

**Response:**
```json
{
    "success": true,
    "data": {
        "categories": {
            "positive": [
                {
                    "id": "helpful",
                    "name": "Helpful",
                    "description": "Content provides value and helps solve problems",
                    "weight": 1.0
                },
                {
                    "id": "informative",
                    "name": "Informative",
                    "description": "Content educates or provides useful information",
                    "weight": 1.0
                }
            ],
            "negative": [
                {
                    "id": "controversial",
                    "name": "Controversial",
                    "description": "Content may be divisive or debatable",
                    "weight": -0.5
                },
                {
                    "id": "spam",
                    "name": "Spam",
                    "description": "Low-value or repetitive content",
                    "weight": -1.0
                }
            ]
        }
    },
    "message": "Reason categories retrieved successfully"
}
```

---

### Get Reputation Levels

**Endpoint:** `GET /reputation/api/reputation_levels`

**Description:** Get all reputation levels and their requirements.

**Response:**
```json
{
    "success": true,
    "data": {
        "levels": [
            {
                "level_name": "Newcomer",
                "level_order": 1,
                "min_reputation": 0,
                "max_reputation": 49,
                "voting_power_multiplier": 0.5,
                "daily_vote_limit": 5,
                "badge_color": "secondary",
                "badge_icon": "fa-user",
                "description": "New community member",
                "is_active": true
            },
            {
                "level_name": "Member",
                "level_order": 2,
                "min_reputation": 50,
                "max_reputation": 199,
                "voting_power_multiplier": 1.0,
                "daily_vote_limit": 10,
                "badge_color": "primary",
                "badge_icon": "fa-user-check",
                "description": "Active community member",
                "is_active": true
            }
        ]
    },
    "message": "Reputation levels retrieved successfully"
}
```

---

## ⚠️ Error Responses

### Standard Error Format

All error responses follow this format:
```json
{
    "success": false,
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "User not found",
        "details": "User with ID 999 does not exist"
    },
    "timestamp": "2026-05-11T23:00:00Z"
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `USER_NOT_FOUND` | 404 | User ID not found |
| `INVALID_TARGET` | 400 | Invalid target type or ID |
| `VOTE_NOT_FOUND` | 404 | Vote to revoke not found |
| `ALREADY_VOTED` | 409 | User already voted on target |
| `RATE_LIMITED` | 429 | Too many voting requests |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `INVALID_PARAMETERS` | 400 | Invalid request parameters |
| `INTERNAL_ERROR` | 500 | Server internal error |

### Rate Limiting

API endpoints are rate-limited to prevent abuse:
- **Voting Operations**: 100 requests per hour per user
- **Analytics Endpoints**: 1000 requests per hour per user
- **Search Endpoints**: 500 requests per hour per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1620748800
```

---

## 🔑 Authentication

### Session Authentication

Most endpoints use session-based authentication:
```bash
curl -X GET "http://localhost:5000/reputation/api/reputation/1" \
     -H "Cookie: session=your_session_cookie"
```

### API Token Authentication

For programmatic access, use API tokens:
```bash
curl -X GET "http://localhost:5000/reputation/api/reputation/1" \
     -H "Authorization: Bearer your_api_token"
```

### Getting API Tokens

Users can generate API tokens through the web interface or API:
```bash
curl -X POST "http://localhost:5000/api/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"description": "Reputation API access"}'
```

---

## 📝 Usage Examples

### Python Example

```python
import requests

# Configuration
BASE_URL = "http://localhost:5000/reputation/api"
SESSION_COOKIE = "your_session_cookie"

headers = {
    "Cookie": f"session={SESSION_COOKIE}",
    "Content-Type": "application/json"
}

# Get user reputation
def get_user_reputation(user_id):
    response = requests.get(f"{BASE_URL}/reputation/{user_id}", headers=headers)
    return response.json()

# Cast a vote
def cast_vote(target_type, target_id, vote_type, reason_category, reason):
    data = {
        "vote_type": vote_type,
        "target_type": target_type,
        "target_id": target_id,
        "reason_category": reason_category,
        "reason": reason
    }
    response = requests.post(f"{BASE_URL}/vote", headers=headers, json=data)
    return response.json()

# Get voting analytics
def get_voting_analytics(user_id, days=30):
    params = {"days": days}
    response = requests.get(f"{BASE_URL}/voting_analytics/{user_id}", 
                          headers=headers, params=params)
    return response.json()

# Get leaderboard
def get_leaderboard(leaderboard_type="reputation", limit=10):
    params = {"type": leaderboard_type, "limit": limit}
    response = requests.get(f"{BASE_URL}/leaderboard", headers=headers, params=params)
    return response.json()

# Usage example
if __name__ == "__main__":
    # Get reputation for user 1
    reputation = get_user_reputation(1)
    print(f"User reputation: {reputation['data']['reputation_score']}")
    
    # Cast an upvote
    vote_result = cast_vote("post", 1234, "upvote", "helpful", "Great content!")
    print(f"Vote cast: {vote_result['success']}")
    
    # Get analytics
    analytics = get_voting_analytics(1, days=30)
    print(f"Total votes: {analytics['data']['total_votes']}")
    
    # Get leaderboard
    leaderboard = get_leaderboard("reputation", limit=5)
    print(f"Top user: {leaderboard['data']['rankings'][0]['username']}")
```

### JavaScript Example

```javascript
// Configuration
const BASE_URL = 'http://localhost:5000/reputation/api';

// Get user reputation
async function getUserReputation(userId) {
    const response = await fetch(`${BASE_URL}/reputation/${userId}`, {
        credentials: 'include'
    });
    return response.json();
}

// Cast a vote
async function castVote(targetType, targetId, voteType, reasonCategory, reason) {
    const response = await fetch(`${BASE_URL}/vote`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            vote_type: voteType,
            target_type: targetType,
            target_id: targetId,
            reason_category: reasonCategory,
            reason: reason
        })
    });
    return response.json();
}

// Get voting analytics
async function getVotingAnalytics(userId, days = 30) {
    const response = await fetch(`${BASE_URL}/voting_analytics/${userId}?days=${days}`, {
        credentials: 'include'
    });
    return response.json();
}

// Get leaderboard
async function getLeaderboard(type = 'reputation', limit = 10) {
    const response = await fetch(`${BASE_URL}/leaderboard?type=${type}&limit=${limit}`, {
        credentials: 'include'
    });
    return response.json();
}

// Usage example
(async () => {
    try {
        // Get reputation for user 1
        const reputation = await getUserReputation(1);
        console.log(`User reputation: ${reputation.data.reputation_score}`);
        
        // Cast an upvote
        const voteResult = await castVote('post', 1234, 'upvote', 'helpful', 'Great content!');
        console.log(`Vote cast: ${voteResult.success}`);
        
        // Get analytics
        const analytics = await getVotingAnalytics(1, 30);
        console.log(`Total votes: ${analytics.data.total_votes}`);
        
        // Get leaderboard
        const leaderboard = await getLeaderboard('reputation', 5);
        console.log(`Top user: ${leaderboard.data.rankings[0].username}`);
    } catch (error) {
        console.error('API Error:', error);
    }
})();
```

---

## 📚 SDK and Libraries

### Python SDK

A Python SDK is available for easy integration:

```python
# Install the SDK
pip install forum-reputation-sdk

# Usage
from forum_reputation import ReputationClient

client = ReputationClient(
    base_url="http://localhost:5000",
    session_cookie="your_session"
)

# Get reputation
reputation = client.get_user_reputation(1)

# Cast vote
result = client.cast_vote(
    target_type="post",
    target_id=1234,
    vote_type="upvote",
    reason_category="helpful",
    reason="Great content!"
)
```

### JavaScript SDK

A JavaScript/Node.js SDK is available:

```javascript
// Install the SDK
npm install forum-reputation-sdk

// Usage
const { ReputationClient } = require('forum-reputation-sdk');

const client = new ReputationClient({
    baseUrl: 'http://localhost:5000',
    sessionCookie: 'your_session'
});

// Get reputation
const reputation = await client.getUserReputation(1);

// Cast vote
const result = await client.castVote({
    targetType: 'post',
    targetId: 1234,
    voteType: 'upvote',
    reasonCategory: 'helpful',
    reason: 'Great content!'
});
```

---

## 🔄 Webhooks

### Vote Webhook

Configure webhooks to receive real-time notifications about voting activity:

```json
{
    "event": "vote_cast",
    "data": {
        "vote_id": 123456,
        "user_id": 1,
        "vote_type": "upvote",
        "target_type": "post",
        "target_id": 1234,
        "vote_weight": 1.5,
        "timestamp": "2026-05-11T23:00:00Z"
    }
}
```

### Reputation Change Webhook

```json
{
    "event": "reputation_changed",
    "data": {
        "user_id": 1,
        "old_reputation": 150,
        "new_reputation": 165,
        "change": 15,
        "reason": "vote_received",
        "timestamp": "2026-05-11T23:00:00Z"
    }
}
```

---

## 📞 Support

For API support and questions:
- **Documentation**: [ENHANCED_VOTING_REPUTATION.md](ENHANCED_VOTING_REPUTATION.md)
- **Issues**: Report bugs on GitHub
- **Community**: Post questions in the forum
- **Email**: support@autobotsolutions.com

---

**API Version:** 1.0.0  
**Last Updated:** May 11, 2026  
**Base URL:** `/reputation/api`  
**Authentication Required**: Yes
