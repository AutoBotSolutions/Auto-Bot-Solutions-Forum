# Voting System

## Overview

Users can upvote or downvote posts and comments. Voting is tracked per user to prevent duplicate votes.

## Components

### Vote Model
```python
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    value = db.Column(db.Integer)  # 1 or -1
```

## Features

- Upvote and downvote
- One vote per user per item
- Change vote by voting again
- Remove vote by voting same value
- Real-time count updates
- Rate limited (30/min)

## Vote Logic

- If no vote exists: create new vote
- If vote exists with same value: remove vote
- If vote exists with different value: change vote
- Update post/comment counts accordingly
