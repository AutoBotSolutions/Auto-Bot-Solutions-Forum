from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Length

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=256)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=10)])
    repository_id = SelectField('Repository (Optional)', coerce=int, validators=[Length(min=0)])
    category_id = SelectField('Category (Optional)', coerce=int, validators=[Length(min=0)])
    attachment = FileField('Attachment (Optional)')
    submit = SubmitField('Create Post')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Post Comment')
