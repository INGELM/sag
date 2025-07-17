from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, StringField, SubmitField, SelectField, MultipleFileField, FloatField, SelectMultipleField, TimeField, BooleanField
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, Optional
from app.auxiliares.models import ciudadesModel, vehiculosModel
from app.clientes.models import clientesModel, pasajerosModel
from app.empleados.models import empleadosModel

def get_empresas():
    return clientesModel.query.all()

def get_ciudades():
    return ciudadesModel.query.all()

def get_vehiculos():
    return vehiculosModel.query.all()

def get_pasajeros():
    return pasajerosModel.query.all()

def get_operadores():
    return empleadosModel.query.filter_by(rol='Operador').all()

    
class programacionForm(FlaskForm):
    id = IntegerField('ID', render_kw={"placeholder": "ID", "class": "form-control", "id": ""}, validators=[Optional()])
    retorno = BooleanField('Retorno', render_kw={"placeholder": "Retorno", "class": "form-check-input", "type": "Checkbox", "id": "retorno-form"}, default=False)
    guia = StringField('Guía', render_kw={"placeholder": "Guía", "class": "form-control"})
    fecha_salida = DateField('Fecha de Salida', validators=[DataRequired(message='La fecha de salida es obligatoria.')], render_kw={"class": "form-control", "id": "fecha_salida", "placeholder": "Fecha de Salida"})
    hora_salida = TimeField('Hora de Salida', render_kw={"class": "form-control"})
    hora_retorno = TimeField('Hora de Retorno', validators=[Optional()], render_kw={"class": "form-control", "id": "hora-retorno-form"})
    empresa = QuerySelectField('Empresa', query_factory=get_empresas, allow_blank=True, blank_text="Seleccione Empresa", get_label='empresa', validators=[DataRequired(message='La empresa es obligatoria.')], render_kw={"class": "form-control ", "id": "empresa-select"})
    pasajeros = QuerySelectMultipleField(
        'Pasajeros',
        query_factory=get_pasajeros,
        allow_blank=True,
        blank_text="Seleccione Pasajeros",
        get_label='nombres',
        validators=[DataRequired(message='Debe seleccionar al menos un pasajero.')],
        render_kw={"class": "form-control pasajero-select", "id": "pasajeros-select", "multiple": True}
    )
    operador = QuerySelectField('Operador', query_factory=get_operadores, allow_blank=True, blank_text="Seleccione Operador", get_label='nombres',render_kw={"class": "form-control operador-select", "id": "operador-select"})
    origen = QuerySelectField('Ciudad Origen', query_factory=get_ciudades, allow_blank=True, blank_text="Seleccione Ciudad", get_label='nombre', validators=[DataRequired(message='La ciudad de origen es obligatoria.')], render_kw={"class": "form-control origen-select", "id": "ciudad-origen-select"})
    destino = QuerySelectField('Ciudad Destino', query_factory=get_ciudades, allow_blank=True, blank_text="Seleccione Ciudad", get_label='nombre', validators=[DataRequired(message='La ciudad de destino es obligatoria.')], render_kw={"class": "form-control destino-select", "id": "ciudad-destino-select"})
    vehiculo = QuerySelectField('Vehículo', query_factory=get_vehiculos, allow_blank=True, blank_text="Seleccione Vehículo", get_label='tipo', render_kw={"class": "form-control vehiculo-select"})
    distancia = FloatField('Distancia', render_kw={"placeholder": "Distancia", "class": "form-control"}, validators=[Optional()], default=0.0)
    tiempo_espera = IntegerField('Tiempo de Espera', render_kw={"placeholder": "Tiempo de Espera", "class": "form-control"}, validators=[Optional()], default=0)
    desvios = IntegerField('Desvíos', render_kw={"placeholder": "Desvíos", "class": "form-control"}, validators=[Optional()], default=0)
    status = SelectField('Status', choices=['Pendiente', 'Programado', 'Finalizado'], render_kw={"class": "form-control", "id": "status"})
    observaciones = StringField('Observaciones', render_kw={"placeholder": "Observaciones", "class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "btn btn-primary w-100"})
