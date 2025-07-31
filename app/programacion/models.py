from flask import current_app
from app.extensions import db
from sqlalchemy import JSON as JSONType
import json

programacion_pasajeros = db.Table('programacion_pasajeros',
    db.Column('programacion', db.Integer, db.ForeignKey('programacion.id')),
    db.Column('pasajero', db.Integer, db.ForeignKey('pasajeros.id'))
)

class programacionModel(db.Model):
    __tablename__ = "programacion"
    id = db.Column(db.Integer, primary_key=True)
    workflow = db.Column(db.String(50), nullable=True)
    guia = db.Column(db.String(50), nullable=True)
    direccion_origen = db.Column(JSONType, nullable=True)
    origen = db.Column(db.Integer, db.ForeignKey('ciudades.id'), nullable=False)
    direccion_destino = db.Column(db.String(255), nullable=True)
    destino = db.Column(db.Integer, db.ForeignKey('ciudades.id'), nullable=False)
    fecha_salida = db.Column(db.Date, nullable=False)
    hora_salida = db.Column(db.Time, nullable=False)
    hora_retorno = db.Column(db.Time, nullable=True)
    turno = db.Column(db.String(15))
    desplazamiento = db.Column(db.String(50))
    tiempo_espera = db.Column(db.Integer, nullable=True)
    desvios = db.Column(db.Integer, nullable=True)
    operador = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=True)
    vehiculo = db.Column(db.Integer, db.ForeignKey('vehiculos.id'), nullable=False)
    retorno = db.Column(db.Boolean, default=False)
    distancia = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=True)
    observaciones = db.Column(db.String(255), nullable=True)
    # Relaciones

    pasajeros = db.relationship('pasajerosModel', secondary=programacion_pasajeros, backref='programaciones')
    origen_rel = db.relationship('ciudadesModel', foreign_keys=[origen])
    destino_rel = db.relationship('ciudadesModel', foreign_keys=[destino])
    operador_rel = db.relationship('empleadosModel', foreign_keys=[operador])
    vehiculo_rel = db.relationship('vehiculosModel', foreign_keys=[vehiculo])

    def __init__(self, status, guia, direccion_origen, direccion_destino, origen, destino, fecha_salida, workflow, hora_salida, distancia, hora_retorno=None, tiempo_espera=None, desvios=None, operador=None, vehiculo=None,  retorno=None, observaciones=None):
        self.guia = guia if guia is not None else None
        self.workflow = workflow if workflow is not None else None
        self.direccion_origen = direccion_origen if direccion_origen is not None else None
        self.origen = origen.id if origen else None
        self.direccion_destino = direccion_destino if direccion_destino is not None else None
        self.destino = destino.id if destino else None
        self.fecha_salida = fecha_salida
        self.hora_salida = hora_salida
        self.distancia = distancia
        self.hora_retorno = hora_retorno
        self.tiempo_espera = tiempo_espera
        self.desvios = desvios
        self.operador = operador.id if operador else None
        self.vehiculo = vehiculo.id if vehiculo else None
        self.retorno = retorno
        self.status = status
        self.turno = self.f_turno()
        self.desplazamiento = self.f_desplazamiento()
        self.observaciones = observaciones
        self.status = status
        
    @property
    def codigo_tarifa(self):
        if self.pasajeros:
            codigo_tarifa = f"{self.pasajeros[0].cliente.codigo.upper()}{self.origen_rel.codigo}{self.destino_rel.codigo}"
            return codigo_tarifa
    
    @property
    def codigo_desc(self):
        if self.pasajeros:
            codigo_desc = f"{self.pasajeros[0].cliente.codigo.upper()}{self.origen_rel.codigo}{self.destino_rel.codigo}-{self.vehiculo_rel.codigo}-{self.desplazamiento}-{self.turno}".upper()
            return codigo_desc

    def f_desplazamiento(self):
        if self.retorno:
            return "idav"
        return "ida"

    def f_turno(self):
        if 6 <= self.hora_salida.hour < 18:
            return "D"
        else:
            return "E"

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except db.IntegrityError as e:  
            db.session.rollback()
            current_app.logger.error(f"Error de integridad al guardar la programación: {str(e)}")
            raise ValueError("Error de integridad al guardar la programación. Verifique los datos ingresados.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al guardar la programación: {str(e)}")
            raise

    def actualizar(self, **kwargs):
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
            'fecha_salida': self.fecha_salida.strftime('%d-%m-%Y') if self.fecha_salida else None,
            'fecha_salida_rel': self.fecha_salida.isoformat() if self.fecha_salida else None,
            'empresa': self.pasajeros[0].cliente.codigo.upper() if self.pasajeros else None,
            'empresa_rel': self.pasajeros[0].cliente.id if self.pasajeros else None,
            'workflow': self.workflow,
            'guia': self.guia,
            'pasajeros': [{'id': p.id, 'nombre': p.nombres.title(), 'telefono': p.telefono} for p in self.pasajeros] if self.pasajeros else [],
            'pasajeros_rel': [p.id for p in self.pasajeros] if self.pasajeros else [],
            'hora_salida': self.hora_salida.strftime('%H:%M') if self.hora_salida else None,
            'hora_retorno': self.hora_retorno.strftime('%H:%M') if self.hora_retorno else None,
            'direccion_origen': self.direccion_origen,
            'origen': self.origen_rel.nombre,
            'origen_rel': self.origen,
            'destino': self.destino_rel.nombre if self.destino_rel else None,
            'destino_rel': self.destino,
            'distancia': self.distancia,
            'operador': self.operador_rel.nombres if self.operador_rel else None,
            'operador_rel': self.operador,
            'vehiculo': self.vehiculo_rel.tipo if self.vehiculo_rel else None,
            'vehiculo_rel': self.vehiculo if self.vehiculo_rel else None,
            'horario': "Diurno" if self.turno == "D" else "Especial",
            'desplazamiento': "Ida y Vuelta" if self.desplazamiento == "idav" else "Ida",
            'tiempo_espera': self.tiempo_espera,
            'desvios': self.desvios,
            'status': self.status,
        }