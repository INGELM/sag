from flask_wtf import FlaskForm
from wtforms import StringField,  SubmitField, DecimalField



class facturasClientesForm(FlaskForm):
    id = StringField('ID', render_kw={"placeholder": "ID de la facturación", "class": "form-control", "type": ""})
    guia = StringField('Guía', render_kw={"placeholder": "Guía de la facturación", "class": "form-control", "readonly": True})
    cliente = StringField('Empresa', render_kw={"placeholder": "Empresa de la facturación", "class": "form-control", "readonly": True})
    costo_total = DecimalField('Costo Total', render_kw={"placeholder": "Costo total", "class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "form-control"})


class pagosOperadoresForm(FlaskForm):
    id = StringField('ID', render_kw={"placeholder": "ID de la facturación", "class": "form-control", "type": "", "readonly": True})
    guia = StringField('Guía', render_kw={"placeholder": "Guía de la facturación", "class": "form-control", "readonly": True})
    cliente = StringField('Empresa', render_kw={"placeholder": "Empresa de la facturación", "class": "form-control", "readonly": True})
    costo_total = DecimalField('Costo Total', render_kw={"placeholder": "Costo total", "class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "form-control"})