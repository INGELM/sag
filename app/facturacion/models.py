from app.extensions import db



class facturasClientesModel(db.Model):
    __tablename__ = "facturas_clientes"
    id = db.Column(db.Integer, primary_key=True)
    programacion = db.Column(db.Integer, db.ForeignKey('programacion.id'), nullable=False)
    tarifas_cliente = db.Column(db.Integer, db.ForeignKey("tarifas.id"), nullable=False)
    costo_desvios = db.Column(db.Float, nullable=True)
    costo_espera = db.Column(db.Float, nullable=True)
    costo_distancia = db.Column(db.Float, nullable=True)
    costo_base = db.Column(db.Float, nullable=True)
    total_desvios = db.Column(db.Float, nullable=True)
    total_espera = db.Column(db.Float, nullable=True)
    total_distancia = db.Column(db.Float, nullable=True)
    costo_total = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=True, default='Por facturar')

    programacion_rel = db.relationship('programacionModel', foreign_keys=[programacion], backref='facturas_clientes')
    tarifas_cliente_rel = db.relationship('tarifasModel', foreign_keys=[tarifas_cliente], backref='facturas_clientes')
  

    def __init__(self, programacion, tarifas_cliente, status, costo_desvios = 0.0, costo_espera = 0.0, costo_distancia = 0.0, costo_base = 0.0, total_desvios = 0.0, total_espera = 0.0, total_distancia = 0.0, costo_total = 0.0):
        self.programacion = programacion
        self.tarifas_cliente = tarifas_cliente
        self.status = status
        self.costo_desvios = costo_desvios
        self.costo_espera = costo_espera
        self.costo_distancia = costo_distancia
        self.costo_base = costo_base
        self.total_desvios = total_desvios
        self.total_espera = total_espera
        self.total_distancia = total_distancia
        self.costo_total = costo_total
    
    def __repr__(self):
        return f"<Facturacion {self.id} - Programacion: {self.programacion}, Costo Total: {self.costo_total}>"
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def serialize(self):
        
        return {
            "id": self.id,
            "fecha": self.programacion_rel.fecha_salida.strftime('%d-%m-%Y') if self.programacion_rel else None,
            "cliente": self.programacion_rel.pasajeros[0].cliente.codigo.upper() if self.programacion_rel else None,
            "pasajeros": [{'id': p.id, 'nombre': p.nombres.title(), 'telefono': p.telefono} for p in self.programacion_rel.pasajeros] if self.programacion_rel and self.programacion_rel.pasajeros else [],
            "guia": self.programacion_rel.guia if self.programacion_rel else None,
            "hora_salida": self.programacion_rel.hora_salida.strftime('%H:%M') if self.programacion_rel else None,
            "hora_retorno": self.programacion_rel.hora_retorno.strftime('%H:%M') if self.programacion_rel.hora_retorno else "--",
            "horario": self.programacion_rel.turno if self.programacion_rel else None,
            "desplazamiento": self.programacion_rel.desplazamiento if self.programacion_rel else None,
            "origen": self.programacion_rel.origen_rel.nombre if self.programacion_rel else None,
            "destino": self.programacion_rel.destino_rel.nombre if self.programacion_rel else None,
            "distancia": self.programacion_rel.distancia if self.programacion_rel.distancia else "--",
            # "Costo km": self.tarifas_cliente_rel.tarifa_km if self.tarifas_cliente_rel.tarifa_km else "--",
            "total_distancia": self.total_distancia if self.total_distancia else "--",
            "tiempo_espera": self.programacion_rel.tiempo_espera if self.programacion_rel.tiempo_espera else "--",
            # "Costo espera": self.tarifas_cliente_rel.espera if self.tarifas_cliente_rel.espera else "--",
            "total_espera": self.total_espera if self.total_espera else "--",
            "desvíos": self.programacion_rel.desvios if self.programacion_rel.desvios else "--",
            # "Costo Desvíos": self.tarifas_cliente_rel.desvios if self.tarifas_cliente_rel.desvios else "--",
            "total_desvios": self.total_desvios if self.total_desvios else "--",
            "costo_base": self.costo_base if self.costo_base else "--",
            "total_": self.costo_total if self.costo_total else "--",
            "status": self.status if self.status else "--",
        }

class pagosOperadoresModel(db.Model):
    __tablename__ = "facturas_operadores"
    id = db.Column(db.Integer, primary_key=True)
    programacion = db.Column(db.Integer, db.ForeignKey('programacion.id'), nullable=False)
    tarifas_operador = db.Column(db.Integer, db.ForeignKey("tarifas_operadores.id"), nullable=False)
    # recargo_vehiculo = db.Column(db.Integer, db.ForeignKey("recargos_vehiculos.id"), nullable=False)
    costo_desvios = db.Column(db.Float, nullable=True)
    costo_espera = db.Column(db.Float, nullable=True)
    costo_base = db.Column(db.Float, nullable=True)
    costo_total = db.Column(db.Float, nullable=True)
    
    programacion_rel = db.relationship('programacionModel', foreign_keys=[programacion], backref='facturas_operadores')
    tarifas_operador_rel = db.relationship('tarifasOperadoresModel', foreign_keys=[tarifas_operador], backref='facturas_operadores')
    # recargo_vehiculo_rel = db.relationship('recargoVehiculosModel', foreign_keys=[recargo_vehiculo], backref='facturas_operadores')

    def __init__(self, programacion, tarifas_operador, costo_desvios, costo_espera, costo_base, costo_total=0.0):
        self.programacion = programacion
        self.tarifas_operador = tarifas_operador
        self.costo_desvios = costo_desvios
        self.costo_espera = costo_espera
        self.costo_base = costo_base
        self.costo_total = costo_total

    def __repr__(self):
        return f"<Facturacion {self.id} - Programacion: {self.programacion}, Costo Base: {self.costo_base}>"

    def serialize(self):
       
        
        
        return {
            "id": self.id,
            "fecha": self.programacion_rel.fecha_salida.strftime('%d-%m-%Y') if self.programacion_rel else None,
            "Operador": self.programacion_rel.operador_rel.nombres.title(),
            "cliente": self.programacion_rel.pasajeros[0].cliente.codigo.upper() if self.programacion_rel else None,
            "pasajeros": [{'id': p.id, 'nombre': p.nombres.title(), 'telefono': p.telefono} for p in self.programacion_rel.pasajeros] if self.programacion_rel and self.programacion_rel.pasajeros else [],
            "guia": self.programacion_rel.guia if self.programacion_rel else None,
            "hora_salida": self.programacion_rel.hora_salida.strftime('%H:%M') if self.programacion_rel else None,
            "hora_retorno": self.programacion_rel.hora_retorno.strftime('%H:%M') if self.programacion_rel.hora_retorno else "--",
            "horario": self.programacion_rel.turno if self.programacion_rel else None,
            "desplazamiento": self.programacion_rel.desplazamiento if self.programacion_rel else None,
            "origen": self.programacion_rel.origen_rel.nombre if self.programacion_rel else None,
            "destino": self.programacion_rel.destino_rel.nombre if self.programacion_rel else None,
            "distancia": self.programacion_rel.distancia if self.programacion_rel.distancia else "--",
            # "Costo km": self.tarifas_cliente_rel.tarifa_km if self.tarifas_cliente_rel.tarifa_km else "--",
            # "total distancia": self.total_distancia if self.total_distancia else "--",
            "tiempo_espera": self.programacion_rel.tiempo_espera if self.programacion_rel.tiempo_espera else "--",
            # "Costo espera": self.tarifas_cliente_rel.espera if self.tarifas_cliente_rel.espera else "--",
            "total_espera": "--" if self.costo_espera * self.programacion_rel.tiempo_espera == 0 else self.costo_espera * self.programacion_rel.tiempo_espera,
            "desvíos": self.programacion_rel.desvios if self.programacion_rel.desvios else "--",
            # "Costo Desvíos": self.tarifas_cliente_rel.desvios if self.tarifas_cliente_rel.desvios else "--",
            "total_desvios": "--" if self.costo_desvios * self.programacion_rel.desvios == 0 else self.costo_desvios * self.programacion_rel.desvios,
            "costo_base": self.costo_base if self.costo_base else "--",
            "total_": self.costo_total if self.costo_total else "--",
        }