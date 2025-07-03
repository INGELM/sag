from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import EqualTo
from wtforms.validators import DataRequired
from app.clientes.models import tarifasModel 
from app.clientes.models import clientesModel


def get_empresas():
    empresas = clientesModel.query.all()
    if not empresas:
        return []
    return empresas

class empleadosForm(FlaskForm):
    id = StringField('ID', render_kw={"placeholder": "ID del empleado", "class": "form-control", "type": ""})
    nombres = StringField('Nombres', validators=[DataRequired(message='El nombre es obligatorio.')],  render_kw={"placeholder": "Nombres del empleado", "class": "form-control", "style": "text-transform:capitalize;"})
    usuario = StringField('Usuario', validators=[DataRequired(message='El usuario es obligatorio.')], render_kw={"placeholder": "Usuario del empleado", "class": "form-control", "style": "text-transform:lowercase;"})
    email = StringField('Email', render_kw={"placeholder": "Email del empleado", "autocomplete": "off", "class": "form-control", "style": "text-transform:lowercase;"})
    contrasena = PasswordField('Contraseña',  validators=[ EqualTo('validar_contrasena', message='Las contraseñas no coinciden.')], render_kw={"placeholder": "Contraseña del empleado", "autocomplete": "new-password", "class": "form-control"})
    validar_contrasena = PasswordField('Validar Contraseña', render_kw={"placeholder": "Validar contraseña del empleado", "autocomplete": "off", "class": "form-control"})
    telefono = StringField('Teléfono', render_kw={"id": "telefono", "class": "form-control telefono", "placeholder": "(04XX)-XXX-XXXX"})
    cargo = SelectField('Cargo', choices=[('Analista', 'Analista'), ('Operador', 'Operador')], render_kw={"class": "form-control"})
    tipo = SelectField('Tipo', choices=[('Directo', 'Directo'), ('Indirecto', 'Indirecto')], render_kw={"class": "form-control"})
    rol = SelectField('Rol', choices=[('Usuario', 'Usuario'), ('Admin', 'Admin')], render_kw={"class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "form-control"})
    
class tarifasOperadoresForm(FlaskForm):
    id = StringField('ID', render_kw={"placeholder": "ID de la tarifa", "class": "form-control", "type": ""})
    empresa = QuerySelectField('Empresa', query_factory=lambda: get_empresas(), get_label='empresa', allow_blank=True, blank_text='Seleccione una empresa', render_kw={"placeholder": "Empresa de la tarifa", "class": "form-control", "id": "empresa-tarifa"})
    codigo = QuerySelectField(
        'Código',
        query_factory=lambda: tarifasModel.query.all(),
        get_label='codigo',
        allow_blank=True,
        blank_text='Seleccione un código',
        render_kw={"class": "form-control", "id": "codigo-tarifa"},
        validators=[DataRequired(message='El código es obligatorio.')]
    )
    tipo = SelectField('Tipo', choices=[('Directo', 'Directo'), ('Indirecto', 'Indirecto')], render_kw={"class": "form-control"})
    espera = StringField('Espera', render_kw={"placeholder": "Tiempo de espera en minutos", "class": "form-control"})
    desvios = StringField('Desvios', render_kw={"placeholder": "Número de desvíos permitidos", "class": "form-control"})
    base = StringField('Base', render_kw={"placeholder": "Tarifa base en USD", "class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "form-control"})