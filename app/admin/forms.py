from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description')
    color = StringField('Color (Hex)', validators=[Length(min=7, max=7)], default='#00f5ff')
    submit = SubmitField('Create Category')

class BadgeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description')
    icon = StringField('Icon', validators=[Length(max=32)], default='★')
    color = StringField('Color (Hex)', validators=[Length(min=7, max=7)], default='#ff00ff')
    submit = SubmitField('Create Badge')
