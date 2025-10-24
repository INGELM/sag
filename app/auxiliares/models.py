from app.extensions import db
from datetime import date

class ciudadesModel(db.Model):
    __tablename__ = 'ciudades'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(4), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)

    clientes = db.relationship('clientesModel', back_populates='ciudad_rel')
    pasajeros = db.relationship('pasajerosModel', back_populates='ciudad_rel')
    tarifas_origen = db.relationship('tarifasModel', foreign_keys='tarifasModel.origen', back_populates='origen_rel')
    tarifas_destino = db.relationship('tarifasModel', foreign_keys='tarifasModel.destino', back_populates='destino_rel')

    def __init__(self, codigo, nombre):
        if not codigo or not nombre:
            raise ValueError("Código y nombre son obligatorios.")
        self.codigo = codigo.upper()
        self.nombre = nombre.title()

    def save(self):
        existing = ciudadesModel.query.filter_by(codigo=self.codigo).first()
        if existing:
            raise ValueError("El código ya existe.")
        db.session.add(self)
        db.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value.strip() if isinstance(value, str) else value)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre
        }


class vehiculosModel(db.Model):
    __tablename__ = 'vehiculos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(4), unique=True, nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    
    # Relación corregida para mantener consistencia
    recargos_vehiculos = db.relationship('recargoVehiculosModel', back_populates='vehiculo_rel', cascade="all, delete-orphan")
    tarifas = db.relationship('tarifasModel', back_populates='vehiculo_rel', cascade="all, delete-orphan")


    def __init__(self, codigo, tipo):
        self.codigo = codigo.upper() if codigo else None
        self.tipo = tipo.title() if tipo else None

    def save(self):
        try:
            existing = vehiculosModel.query.filter_by(codigo=self.codigo).first()
            if existing:
                raise ValueError("El código ya existe.")
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value.strip() if isinstance(value, str) else value)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'tipo': self.tipo
        }
        
class tasaModel(db.Model):
    __tablename__ = 'tasa_cambio'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    tasa = db.Column(db.Float, nullable=False)

    def __init__(self, tasa):
        self.fecha = date.today()
        self.tasa = tasa

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        return {
            'id': self.id,
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'tasa': self.tasa
        }