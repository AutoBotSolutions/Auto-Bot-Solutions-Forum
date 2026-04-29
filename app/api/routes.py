from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import Repository, Post
from app import db, limiter
import requests
from config import Config

api_bp = Blueprint('api', __name__)

@api_bp.route('/sync-repositories', methods=['POST'])
@limiter.limit("5 per hour")
def sync_repositories():
    """Sync repositories from GitHub"""
    try:
        org = Config.GITHUB_ORG
        url = f'https://api.github.com/orgs/{org}/repos'
        headers = {}
        if Config.GITHUB_TOKEN:
            headers['Authorization'] = f'token {Config.GITHUB_TOKEN}'
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        repos_data = response.json()
        
        synced_count = 0
        for repo_data in repos_data:
            existing = Repository.query.filter_by(github_url=repo_data['html_url']).first()
            if not existing:
                repo = Repository(
                    name=repo_data['name'],
                    description=repo_data.get('description', ''),
                    github_url=repo_data['html_url'],
                    stars=repo_data.get('stargazers_count', 0),
                    language=repo_data.get('language')
                )
                db.session.add(repo)
                synced_count += 1
            else:
                existing.stars = repo_data.get('stargazers_count', 0)
                existing.language = repo_data.get('language')
        
        db.session.commit()
        return jsonify({'success': True, 'synced': synced_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/repositories', methods=['GET'])
def get_repositories():
    repos = Repository.query.all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'description': r.description,
        'stars': r.stars,
        'language': r.language
    } for r in repos])

@api_bp.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'author': p.author.username,
        'created_at': p.created_at.isoformat(),
        'upvotes': p.upvotes,
        'downvotes': p.downvotes
    } for p in posts])
