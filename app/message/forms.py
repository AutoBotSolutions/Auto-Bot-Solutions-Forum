from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class MessageForm(FlaskForm):
    receiver_id = SelectField('To', coerce=int, validators=[DataRequired()])
    content = TextAreaField('Message', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Send Message')
