from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional

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

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Admin Privileges')
    is_active = BooleanField('Account Active')
    is_verified = BooleanField('Email Verified')
    bio = TextAreaField('Bio')
    location = StringField('Location', validators=[Optional(), Length(max=128)])
    website = StringField('Website', validators=[Optional(), Length(max=256)])
    change_password = BooleanField('Change Password')
    password = PasswordField('New Password', validators=[Optional(), Length(min=6, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[
        Optional(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Update User')

class UserSuspendForm(FlaskForm):
    reason = TextAreaField('Suspension Reason', validators=[DataRequired()])
    duration_days = StringField('Duration (days)', validators=[Optional()], 
                               description='Leave empty for indefinite suspension')
    submit = SubmitField('Suspend User')

class UserBanForm(FlaskForm):
    reason = TextAreaField('Ban Reason', validators=[DataRequired()])
    submit = SubmitField('Ban User')

class UserBulkActionForm(FlaskForm):
    action = StringField('Action', validators=[DataRequired()])
    user_ids = StringField('User IDs', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[Optional()])
    submit = SubmitField('Execute Bulk Action')
