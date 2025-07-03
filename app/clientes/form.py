from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField, SelectField, FloatField, DecimalField
from wtforms_sqlalchemy.fields import QuerySelectField
from app.auxiliares.models import ciudadesModel, vehiculosModel
from wtforms.validators import DataRequired

from app.clientes.models import clientesModel
from wtforms.fields import SelectField

def get_ciudades():
    ciudades = ciudadesModel.query.all()
    if not ciudades:   
        # Si no hay ciudades, mostrar un mensaje en el input
        # Retornar una lista con una opción que muestre el mensaje
        return []
    return ciudades


class clientesForm(FlaskForm):
    id = StringField('ID', render_kw={"placeholder": "ID del cliente", "class": "form-control", "type": ""})
    codigo = StringField('Código', validators=[DataRequired(message='El código es obligatorio.')],  render_kw={"placeholder": "CÓDIGO DEL CLIENTE", "class": "form-control", "style": "text-transform:uppercase;"})
    empresa = StringField('Empresa', validators=[DataRequired(message='La empresa es obligatoria.')], render_kw={"placeholder": "Empresa del cliente", "class": "form-control", "style": "text-transform:uppercase;"})
    direccion = StringField('Dirección', render_kw={"placeholder": "Dirección del cliente", "class": "form-control"})
    ciudad = QuerySelectField('Ciudad', query_factory=get_ciudades, get_label='nombre', allow_blank=True, blank_text='Seleccione una ciudad', render_kw={"placeholder": "Ciudad del cliente", "class": "form-control"})
    email = StringField('Email', render_kw={"placeholder": "Email del cliente", "autocomplete": "off", "class": "form-control", "style": "text-transform:lowercase;"})
    telefono = StringField('Teléfono', render_kw={"id": "telefono-clientes", "class": "telefono form-control", "placeholder": "(04XX)-XXX-XXXX"})
    submit = SubmitField('Guardar')

class pasajerosForm(FlaskForm):
    id = StringField('ID', render_kw={"class": "form-control", "type": ""})
    nombres = StringField('Nombre', validators=[DataRequired(message='El nombre es obligatorio.')], render_kw={"placeholder": "Nombre del pasajero", "class": "form-control"})
    empresa = QuerySelectField('Empresa', query_factory=lambda: clientesModel.query.all(), get_label='empresa', allow_blank=True, blank_text='Seleccione una empresa', render_kw={"placeholder": "Empresa del pasajero", "class": "form-control"})
    ciudad = QuerySelectField('Ciudad', query_factory=lambda: ciudadesModel.query.all(), get_label='nombre', allow_blank=True, blank_text='Seleccione una ciudad', render_kw={"placeholder": "Ciudad del pasajero", "class": "form-control"})
    direccion = StringField('Dirección', render_kw={"placeholder": "Dirección del pasajero", "class": "form-control"})
    email = StringField('Email', render_kw={"placeholder": "Email del pasajero", "autocomplete": "off", "class": "form-control", "style": "text-transform:lowercase;"})
    telefono = StringField('Teléfono', render_kw={"id": "telefono-pasajeros", "class": "telefono form-control", "placeholder": "(04XX)-XXX-XXXX"})
    submit = SubmitField('Guardar')

class tarifasForm(FlaskForm):
    id = StringField('ID', render_kw={"placeholder": "ID de la tarifa", "class": "form-control", "type": "hidden"})
    empresa = QuerySelectField(
        'Empresa',
        query_factory=lambda: clientesModel.query.all(),
        get_label='empresa',
        allow_blank=True,
        blank_text='Seleccione una empresa',
        validators=[DataRequired(message='La empresa es obligatoria.')],
        render_kw={"placeholder": "Empresa de la tarifa", "class": "form-control"}
    )
    origen = QuerySelectField(
        'Origen',
        query_factory=lambda: ciudadesModel.query.all(),
        get_label='nombre',
        allow_blank=True,
        blank_text='Seleccione una ciudad de origen',
        validators=[DataRequired(message='El origen es obligatorio.')],
        render_kw={"placeholder": "Ciudad de origen", "class": "form-control"}
    )
    destino = QuerySelectField(
        'Destino',
        query_factory=lambda: ciudadesModel.query.all(),
        get_label='nombre',
        allow_blank=True,
        blank_text='Seleccione una ciudad de destino',
        validators=[DataRequired(message='El destino es obligatorio.')],
        render_kw={"placeholder": "Ciudad de destino", "class": "form-control"}
    )
    espera = IntegerField('Tarifa de Espera', validators=[DataRequired(message='La tarifa de espera es obligatoria.')], render_kw={"placeholder": "Tarifa de espera", "class": "form-control"})
    desvios = IntegerField('Tarifa de Desvíos', validators=[DataRequired(message='La tarifa de desvíos es obligatoria.')], render_kw={"placeholder": "Tarifa de desvíos", "class": "form-control"})
    especial = IntegerField('Tarifa Especial', render_kw={"placeholder": "Tarifa especial", "class": "form-control"})
    tarifa_km = DecimalField('Tarifa por KM', render_kw={"placeholder": "Tarifa por KM", "class": "form-control"}, default=0.0)
    base = DecimalField('Tarifa Base', render_kw={"placeholder": "Tarifa base", "class": "form-control"}, default=0.0)
    submit = SubmitField('Guardar')


class recargoVehiculosForm(FlaskForm):
    id = StringField('ID', render_kw={"placeholder": "ID del recargo", "class": "form-control", "type": "hidden"})
    empresa = QuerySelectField('Empresa', query_factory=lambda: clientesModel.query.all(), get_label='empresa', allow_blank=True, blank_text='Seleccione una empresa', render_kw={"placeholder": "Empresa del recargo", "class": "form-control"})
    vehiculo = QuerySelectField('Vehículo', query_factory=lambda: vehiculosModel.query.filter(vehiculosModel.tipo != 'Sedan').all(), get_label='tipo', allow_blank=True, blank_text='Seleccione un vehículo', render_kw={"placeholder": "Vehículo", "class": "form-control"})
    recargo = DecimalField('Recargo', validators=[DataRequired(message='El recargo es obligatorio.')], render_kw={"placeholder": "Recargo del vehículo", "class": "form-control"})
    submit = SubmitField('Guardar')