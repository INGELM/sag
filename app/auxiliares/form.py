from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField
from wtforms.validators import EqualTo, Length
from wtforms.validators import DataRequired


class ciudadesForm(FlaskForm):
    id = StringField('ID', render_kw={"class": "form-control", "readonly": True})
    codigo = StringField('Código', validators=[DataRequired(), Length(max=4)], render_kw={"style": "text-transform:uppercase;", "class": "form-control"})
    nombre = StringField('Ciudad', validators=[DataRequired()], render_kw={"style": "text-transform:capitalize;", "class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "form-control"})

class vehiculosForm(FlaskForm):
    id = StringField('ID', render_kw={"class": "form-control", "readonly": True})
    codigo = StringField('Código', validators=[DataRequired(), Length(max=4)], render_kw={"style": "text-transform:uppercase;", "class": "form-control"})
    tipo = StringField('Tipo', validators=[DataRequired()], render_kw={"style": "text-transform:capitalize;", "class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "form-control"})

class tasaForm(FlaskForm):
    id = StringField('ID', render_kw={"class": "form-control", "readonly": True})
    tasa = FloatField('Tasa', validators=[DataRequired(message="El campo Tasa es obligatorio.")], render_kw={"class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "form-control"})