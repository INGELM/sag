from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Usuario', render_kw={'placeholder': 'Ingrese su usuario'}, validators=[DataRequired(message='El usuario es obligatorio')])
    password = PasswordField('Contraseña', render_kw={'placeholder': 'Ingrese su contraseña'}, validators=[DataRequired(message='La contraseña es obligatoria')])
    remember = BooleanField('Recordarme', default=False, render_kw={'class': 'form-check-input'})
    submit = SubmitField('Iniciar Sesión')