from flask import current_app
from app.empleados.models import tarifasOperadoresModel
from app.extensions import db


class clientesModel(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(4), unique=True, nullable=False)
    empresa = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=True)
    ciudad = db.Column(db.Integer, db.ForeignKey('ciudades.id'), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    telefono = db.Column(db.String(20), nullable=True)

    # Relaciones mejoradas con nombres más descriptivos
    # Línea modificada: nombre más claro
    ciudad_rel = db.relationship('ciudadesModel', back_populates='clientes')
    pasajeros = db.relationship(
        'pasajerosModel', back_populates='cliente', cascade="all, delete-orphan")
    tarifas = db.relationship(
        'tarifasModel', back_populates='cliente', cascade="all, delete-orphan")
    recargos_vehiculos = db.relationship('recargoVehiculosModel', back_populates='cliente_rel',
                                         cascade="all, delete-orphan")  # Línea modificada: nombre coherente

    def __init__(self, codigo, empresa, direccion=None, ciudad=None, email=None, telefono=None):
        self.codigo = codigo.upper() if codigo else None
        self.empresa = empresa.title() if empresa else None
        self.direccion = direccion.title() if direccion else None
        self.ciudad = ciudad.id if ciudad else None
        self.email = email.lower() if email else None
        self.telefono = telefono if telefono else None

    def save(self):
        existing = clientesModel.query.filter_by(codigo=self.codigo).first()
        if existing:
            raise ValueError("El código ya existe.")
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.debug(f'Error al guardar cliente: {e}')
            raise ValueError("Error inesperado al guardar el cliente.")

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value.strip() if isinstance(
                    value, str) and key != 'email' else value)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.debug(f'Error al actualizar cliente: {e}')
            raise ValueError("Error inesperado al actualizar el cliente.")

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        return {
            'id': self.id,
            'codigo': self.codigo.upper() if self.codigo else None,
            'empresa': self.empresa,
            'direccion': self.direccion,
            'ciudad': self.ciudad_rel.nombre if self.ciudad_rel else None,
            'ciudad_rel': self.ciudad,
            'email': self.email,
            'telefono': self.telefono
        }


class pasajerosModel(db.Model):
    __tablename__ = 'pasajeros'
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.Integer, db.ForeignKey(
        'clientes.id'), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.Integer, db.ForeignKey('ciudades.id'), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)

    cliente = db.relationship('clientesModel', back_populates='pasajeros')
    ciudad_rel = db.relationship('ciudadesModel', back_populates='pasajeros')

    def __init__(self, empresa, nombres, email=None, telefono=None, ciudad=None, direccion=None):
        self.empresa = empresa.id if hasattr(empresa, 'id') else empresa
        self.nombres = nombres.title() if nombres else None
        self.email = email.lower() if email else None
        self.telefono = telefono if telefono else None
        self.ciudad = ciudad.id if hasattr(ciudad, 'id') else ciudad
        self.direccion = direccion.title() if direccion else None

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value.strip() if isinstance(
                    value, str) and key != 'email' else value)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        return {
            'id': self.id,
            'empresa': self.cliente.empresa if self.cliente else None,
            'empresa_rel': self.empresa,
            'nombres': self.nombres,
            'ciudad': self.ciudad_rel.nombre if self.ciudad_rel else None,
            'ciudad_rel': self.ciudad,
            'direccion': self.direccion,
            'email': self.email,
            'telefono': self.telefono
        }


class tarifasModel(db.Model):
    __tablename__ = 'tarifas'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    empresa = db.Column(db.Integer, db.ForeignKey(
        'clientes.id'), nullable=False)
    origen = db.Column(db.Integer, db.ForeignKey(
        'ciudades.id'), nullable=False)
    destino = db.Column(db.Integer, db.ForeignKey(
        'ciudades.id'), nullable=False)
    espera = db.Column(db.Integer, nullable=True, default=0)
    desvios = db.Column(db.Integer, nullable=True, default=0)
    especial = db.Column(db.Integer, nullable=True, default=0)
    tarifa_km = db.Column(db.Float, nullable=True, default=0.0)
    base = db.Column(db.Float, nullable=True, default=0.0)

    cliente = db.relationship('clientesModel', back_populates='tarifas')
    origen_rel = db.relationship('ciudadesModel', foreign_keys=[
                                 origen], back_populates='tarifas_origen')
    destino_rel = db.relationship('ciudadesModel', foreign_keys=[
                                  destino], back_populates='tarifas_destino')
    tarifas_operadores = db.relationship(
        'tarifasOperadoresModel', back_populates='codigo_rel', lazy=True)

    def __init__(self, empresa, origen, destino, espera=0, desvios=0, base=0.0, tarifa_km=0.0, especial=0):
        self.empresa = empresa.id if hasattr(empresa, 'id') else empresa
        self.origen = origen.id if hasattr(origen, 'id') else origen
        self.destino = destino.id if hasattr(destino, 'id') else destino
        self.espera = espera
        self.desvios = desvios
        self.base = base
        self.codigo = f"{empresa.codigo}{origen.codigo}{destino.codigo}".upper()
        self.tarifa_km = tarifa_km
        self.especial = especial

    def save(self):
        existing = tarifasModel.query.filter_by(codigo=self.codigo).first()
        if existing:
            raise ValueError("El código de tarifa ya existe.")
        db.session.add(self)
        db.session.commit()

    def update(self, **kwargs):
        # Actualiza los atributos antes de recalcular el código
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        # Obtiene los objetos relacionados si es necesario
        empresa_obj = self.cliente if hasattr(self, 'cliente') and self.cliente else None
        origen_obj = self.origen_rel if hasattr(self, 'origen_rel') and self.origen_rel else None
        destino_obj = self.destino_rel if hasattr(self, 'destino_rel') and self.destino_rel else None
        # Recalcula el código si los objetos existen
        if empresa_obj and origen_obj and destino_obj:
            self.codigo = f"{empresa_obj.codigo}{origen_obj.codigo}{destino_obj.codigo}".upper()
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def color_code(self):
        try:
            tarifas_operadores = (
                tarifasOperadoresModel.query
                .join(tarifasOperadoresModel.codigo_rel)  # Usa la relación
                # Filtra por el código de tarifasModel
                .filter(tarifasModel.codigo == self.codigo)
                .all()
            )

            if len(tarifas_operadores) == 0:
                color = 'red'
            elif len(tarifas_operadores) == 1:
                color = 'orange'
            elif len(tarifas_operadores) > 1:
                color = 'green'
        except Exception as e:
            current_app.logger.debug(f'Error al obtener color de tarifa: {e}')
            color = 'gray'  
            raise ValueError("Error inesperado al obtener el color de la tarifa.")
        return color

    def serialize(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'empresa': self.cliente.empresa if self.cliente else None,
            'empresa_rel': self.empresa,
            'origen': self.origen_rel.nombre if self.origen_rel else None,
            'origen_rel': self.origen,
            'destino': self.destino_rel.nombre if self.destino_rel else None,
            'destino_rel': self.destino,
            'espera': self.espera,
            'desvios': self.desvios,
            'base': self.base,
            'tarifa_km': self.tarifa_km,
            'especial': self.especial,
            'color_rel': self.color_code()
        }


class recargoVehiculosModel(db.Model):
    __tablename__ = 'recargos_vehiculos'
    id = db.Column(db.Integer, primary_key=True)
    vehiculo = db.Column(db.Integer, db.ForeignKey(
        'vehiculos.id'), nullable=False)  # Clave foránea clara
    recargo = db.Column(db.Float, nullable=False, default=0.0)
    cliente = db.Column(db.Integer, db.ForeignKey(
        'clientes.id'), nullable=False)  # Clave foránea clara

    # Relaciones mejoradas con nombres más descriptivos
    # Línea modificada: nombre coherente
    vehiculo_rel = db.relationship(
        'vehiculosModel', back_populates='recargos_vehiculos')
    # Línea modificada: nombre coherente
    cliente_rel = db.relationship(
        'clientesModel', back_populates='recargos_vehiculos')

    def __init__(self, vehiculo, cliente, recargo=0.0):
        self.vehiculo = vehiculo
        self.cliente = cliente.id if hasattr(cliente, 'id') else cliente
        self.recargo = recargo

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
            'vehiculo': self.vehiculo_rel.tipo if self.vehiculo_rel else None,
            'vehiculo_rel': self.vehiculo,
            'cliente': self.cliente_rel.empresa if self.cliente_rel else None,
            'cliente_rel': self.cliente,
            'recargo': self.recargo
        }
