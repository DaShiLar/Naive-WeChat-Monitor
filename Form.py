from wtforms import Form, PasswordField, StringField, SubmitField, validators
from wtforms.validators import DataRequired


class RegistrationForm(Form):
    user_id = StringField('user_id', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    phone_number = StringField('Phone Number', [validators.DataRequired()])


class LoginForm(Form):
    user_id = StringField('user_id', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
