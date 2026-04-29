from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Repository, Post
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    repositories = Repository.query.all()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template('index.html', repositories=repositories, posts=recent_posts)

@main_bp.route('/about')
def about():
    return render_template('about.html')
