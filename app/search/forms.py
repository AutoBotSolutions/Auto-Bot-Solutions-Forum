"""
Search Forms

Forms for advanced search functionality including filters and validation.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from wtforms.widgets import TextArea
from datetime import datetime, date
from flask import current_app
from app.models import User, Category

class SearchForm(FlaskForm):
    """Main search form with basic and advanced options"""
    query = StringField('Search', validators=[
        DataRequired(message='Please enter a search query'),
        Length(min=1, max=255, message='Search query must be between 1 and 255 characters')
    ])
    
    # Content type filter
    content_type = SelectField('Content Type', choices=[
        ('', 'All Content'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user', 'Users')
    ], validators=[Optional()])
    
    # Sorting options
    sort_by = SelectField('Sort By', choices=[
        ('relevance', 'Relevance'),
        ('date', 'Date'),
        ('votes', 'Votes'),
        ('views', 'Views')
    ], default='relevance', validators=[Optional()])
    
    sort_order = SelectField('Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc', validators=[Optional()])
    
    # Results per page
    per_page = SelectField('Results per page', choices=[
        ('10', '10'),
        ('20', '20'),
        ('50', '50'),
        ('100', '100')
    ], default='20', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.per_page.choices = [
            (str(limit), str(limit)) for limit in 
            current_app.config.get('SEARCH_RESULTS_PER_PAGE_OPTIONS', [10, 20, 50, 100])
        ]

class AdvancedSearchForm(FlaskForm):
    """Advanced search form with comprehensive filters"""
    query = StringField('Search', validators=[
        DataRequired(message='Please enter a search query'),
        Length(min=1, max=255, message='Search query must be between 1 and 255 characters')
    ])
    
    # Content filters
    content_type = SelectField('Content Type', choices=[
        ('', 'All Content'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user', 'Users')
    ], validators=[Optional()])
    
    # Author filter
    author = StringField('Author', validators=[
        Length(max=64, message='Author name must be less than 64 characters')
    ])
    
    # Category filter
    category = SelectField('Category', coerce=int, validators=[Optional()])
    
    # Date range filters
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    # Tags filter
    tags = StringField('Tags', validators=[
        Length(max=255, message='Tags must be less than 255 characters')
    ])
    
    # Engagement filters
    min_votes = IntegerField('Minimum Votes', validators=[
        NumberRange(min=0, message='Minimum votes must be non-negative')
    ])
    
    max_votes = IntegerField('Maximum Votes', validators=[
        NumberRange(min=0, message='Maximum votes must be non-negative')
    ])
    
    min_views = IntegerField('Minimum Views', validators=[
        NumberRange(min=0, message='Minimum views must be non-negative')
    ])
    
    max_views = IntegerField('Maximum Views', validators=[
        NumberRange(min=0, message='Maximum views must be non-negative')
    ])
    
    # Sorting options
    sort_by = SelectField('Sort By', choices=[
        ('relevance', 'Relevance'),
        ('date', 'Date'),
        ('votes', 'Votes'),
        ('views', 'Views'),
        ('comments', 'Comments')
    ], default='relevance', validators=[Optional()])
    
    sort_order = SelectField('Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc', validators=[Optional()])
    
    # Results per page
    per_page = SelectField('Results per page', choices=[
        ('10', '10'),
        ('20', '20'),
        ('50', '50'),
        ('100', '100')
    ], default='20', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_choices()
    
    def _populate_choices(self):
        """Populate dynamic choices"""
        # Populate categories
        categories = Category.query.order_by(Category.name).all()
        self.category.choices = [(0, 'All Categories')] + [(c.id, c.name) for c in categories]
    
    def validate_date_from(self, field):
        """Validate date range"""
        if field.data and self.date_to.data:
            if field.data > self.date_to.data:
                raise ValidationError('From date must be before to date')
    
    def validate_date_to(self, field):
        """Validate date range"""
        if field.data and field.data > date.today():
            raise ValidationError('To date cannot be in the future')
    
    def validate_min_votes(self, field):
        """Validate vote range"""
        if field.data and self.max_votes.data:
            if field.data > self.max_votes.data:
                raise ValidationError('Minimum votes must be less than maximum votes')
    
    def validate_max_votes(self, field):
        """Validate vote range"""
        if field.data and self.min_votes.data:
            if field.data < self.min_votes.data:
                raise ValidationError('Maximum votes must be greater than minimum votes')
    
    def validate_min_views(self, field):
        """Validate view range"""
        if field.data and self.max_views.data:
            if field.data > self.max_views.data:
                raise ValidationError('Minimum views must be less than maximum views')
    
    def validate_max_views(self, field):
        """Validate view range"""
        if field.data and self.min_views.data:
            if field.data < self.min_views.data:
                raise ValidationError('Maximum views must be greater than minimum views')
    
    def get_search_filters(self):
        """Get filters as dictionary for search service"""
        filters = {}
        
        # Content type filter
        if self.content_type.data:
            filters['content_type'] = self.content_type.data
        
        # Author filter
        if self.author.data:
            author = User.query.filter(
                or_(
                    User.username.ilike(f'%{self.author.data}%'),
                    User.email.ilike(f'%{self.author.data}%')
                )
            ).first()
            if author:
                filters['author_id'] = author.id
        
        # Category filter
        if self.category.data and self.category.data > 0:
            filters['category_id'] = self.category.data
        
        # Date range filter
        if self.date_from.data:
            filters['date_from'] = datetime.combine(self.date_from.data, datetime.min.time())
        if self.date_to.data:
            filters['date_to'] = datetime.combine(self.date_to.data, datetime.max.time())
        
        # Tags filter
        if self.tags.data:
            tags = [tag.strip() for tag in self.tags.data.split(',') if tag.strip()]
            if tags:
                filters['tags'] = tags
        
        # Vote range filter
        if self.min_votes.data is not None:
            filters['min_votes'] = self.min_votes.data
        if self.max_votes.data is not None:
            filters['max_votes'] = self.max_votes.data
        
        # View range filter
        if self.min_views.data is not None:
            filters['min_views'] = self.min_views.data
        if self.max_views.data is not None:
            filters['max_views'] = self.max_views.data
        
        return filters

class SearchSuggestionForm(FlaskForm):
    """Form for search suggestions"""
    query = StringField('Query', validators=[
        DataRequired(message='Please enter a query'),
        Length(min=1, max=100, message='Query must be between 1 and 100 characters')
    ])
    limit = SelectField('Limit', choices=[
        ('5', '5'),
        ('10', '10'),
        ('20', '20'),
        ('50', '50')
    ], default='10', validators=[Optional()])

class SearchAnalyticsForm(FlaskForm):
    """Form for search analytics and reporting"""
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    # Analytics type
    analytics_type = SelectField('Analytics Type', choices=[
        ('popular', 'Popular Searches'),
        ('trending', 'Trending Topics'),
        ('user_activity', 'User Activity'),
        ('content_performance', 'Content Performance')
    ], default='popular', validators=[Optional()])
    
    # Group by
    group_by = SelectField('Group By', choices=[
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month')
    ], default='day', validators=[Optional()])
    
    # Time period
    days = SelectField('Time Period', choices=[
        ('1', 'Last 24 hours'),
        ('7', 'Last 7 days'),
        ('30', 'Last 30 days'),
        ('90', 'Last 90 days'),
        ('365', 'Last year')
    ], default='7', validators=[Optional()])
    
    # Export format
    export_format = SelectField('Export Format', choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('excel', 'Excel')
    ], default='json', validators=[Optional()])
    
    def validate_date_from(self, field):
        """Validate date range"""
        if field.data and self.date_to.data:
            if field.data > self.date_to.data:
                raise ValidationError('From date must be before to date')
    
    def validate_date_to(self, field):
        """Validate date range"""
        if field.data and field.data > date.today():
            raise ValidationError('To date cannot be in the future')

class SearchIndexForm(FlaskForm):
    """Form for search index management"""
    action = SelectField('Action', choices=[
        ('reindex', 'Reindex All Content'),
        ('update', 'Update Specific Content'),
        ('delete', 'Delete from Index'),
        ('optimize', 'Optimize Index')
    ], validators=[DataRequired()])
    
    content_type = SelectField('Content Type', choices=[
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user', 'Users')
    ], validators=[Optional()])
    
    content_id = IntegerField('Content ID', validators=[Optional()])
    
    confirm = BooleanField('Confirm Action', validators=[DataRequired()])
    
    def validate_content_id(self, field):
        """Validate content ID for specific actions"""
        if self.action.data in ['update', 'delete'] and not field.data:
            raise ValidationError('Content ID is required for update and delete actions')

class TagInputWidget(TextArea):
    """Custom widget for tag input"""
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class', 'form-control')
        kwargs.setdefault('rows', 2)
        kwargs.setdefault('placeholder', 'Enter tags separated by commas')
        return super().__call__(field, **kwargs)

class TagField(StringField):
    """Custom field for tag input with validation"""
    widget = TagInputWidget()
    
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = ', '.join([tag.strip() for tag in valuelist[0].split(',') if tag.strip()])
        else:
            self.data = ''
    
    def _value(self):
        return self.data or ''

class EnhancedSearchForm(AdvancedSearchForm):
    """Enhanced search form with additional features"""
    tags = TagField('Tags', validators=[Length(max=255, message='Tags must be less than 255 characters')])
    
    # Search scope
    search_scope = SelectField('Search Scope', choices=[
        ('all', 'All Content'),
        ('title', 'Titles Only'),
        ('content', 'Content Only'),
        ('tags', 'Tags Only')
    ], default='all', validators=[Optional()])
    
    # Time filter
    time_filter = SelectField('Time Period', choices=[
        ('', 'Any Time'),
        ('hour', 'Last Hour'),
        ('day', 'Last 24 Hours'),
        ('week', 'Last Week'),
        ('month', 'Last Month'),
        ('year', 'Last Year')
    ], validators=[Optional()])
    
    # Language filter
    language = SelectField('Language', choices=[
        ('', 'Any Language'),
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('zh', 'Chinese')
    ], validators=[Optional()])
    
    # Quality filter
    min_quality = SelectField('Minimum Quality', choices=[
        ('', 'Any Quality'),
        ('high', 'High Quality'),
        ('medium', 'Medium Quality'),
        ('low', 'Low Quality')
    ], validators=[Optional()])
    
    def get_search_filters(self):
        """Get enhanced filters for search service"""
        filters = super().get_search_filters()
        
        # Search scope filter
        if self.search_scope.data and self.search_scope.data != 'all':
            filters['search_scope'] = self.search_scope.data
        
        # Time filter
        if self.time_filter.data:
            now = datetime.utcnow()
            if self.time_filter.data == 'hour':
                filters['date_from'] = now - timedelta(hours=1)
            elif self.time_filter.data == 'day':
                filters['date_from'] = now - timedelta(days=1)
            elif self.time_filter.data == 'week':
                filters['date_from'] = now - timedelta(weeks=1)
            elif self.time_filter.data == 'month':
                filters['date_from'] = now - timedelta(days=30)
            elif self.time_filter.data == 'year':
                filters['date_from'] = now - timedelta(days=365)
        
        # Language filter
        if self.language.data:
            filters['language'] = self.language.data
        
        # Quality filter
        if self.min_quality.data:
            filters['min_quality'] = self.min_quality.data
        
        return filters

class SearchPreferencesForm(FlaskForm):
    """Form for user search preferences"""
    results_per_page = SelectField('Results per page', choices=[
        ('10', '10'),
        ('20', '20'),
        ('50', '50'),
        ('100', '100')
    ], default='20', validators=[Optional()])
    
    default_sort = SelectField('Default Sort', choices=[
        ('relevance', 'Relevance'),
        ('date', 'Date'),
        ('votes', 'Votes'),
        ('views', 'Views')
    ], default='relevance', validators=[Optional()])
    
    default_order = SelectField('Default Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc', validators=[Optional()])
    
    # Search options
    include_comments = BooleanField('Include Comments in Search')
    include_users = BooleanField('Include Users in Search')
    enable_highlights = BooleanField('Enable Search Highlights')
    show_suggestions = BooleanField('Show Search Suggestions')
    
    # Filter preferences
    auto_apply_filters = BooleanField('Auto-apply Common Filters')
    remember_filters = BooleanField('Remember Search Filters')
    
    # Privacy options
    save_search_history = BooleanField('Save Search History')
    anonymous_search = BooleanField('Anonymous Search')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results_per_page.choices = [
            (str(limit), str(limit)) for limit in 
            current_app.config.get('SEARCH_RESULTS_PER_PAGE_OPTIONS', [10, 20, 50, 100])
        ]
