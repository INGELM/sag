from flask import current_app
from flask_login import UserMixin
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user


class empleadosModel(db.Model, UserMixin):
    __tablename__ = 'empleados'
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    # cargo = db.Column(db.String(20), nullable=True)
    tipo = db.Column(db.String(20), nullable=True)
    rol = db.Column(db.String(20), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, nombres, usuario, contrasena, email=None, telefono=None, tipo=None, rol=None):
        self.nombres = nombres.title() if nombres else None
        self.usuario = usuario.lower() if usuario else None
        self.contrasena = self.hash_password(contrasena) if contrasena else None
        self.email = email.lower() if email else None
        self.telefono = telefono if telefono else None
        self.tipo = tipo if tipo else None
        self.rol = rol if rol else None
        self.is_admin = self.check_admin()

    def check_admin(self):
        return True if self.rol == 'Admin' else False

    # def __repr__(self):
    #     return f'<Empleado {self.nombres}>'

    @staticmethod
    def hash_password(contrasena):
        return generate_password_hash(contrasena)

    def get_id(self):
       return str(self.id)
    
    def check_password(self, contrasena):
        approved = check_password_hash(self.contrasena, contrasena) 
        # current_app.logger.debug(f'Contraseña: {self.contrasena}, Ingreso: {contrasena}, Aprobado: {approved}')
        current_app.logger.debug(f'Contraseña verificada para {self.usuario}: {approved}')
        return approved

    def save(self):
        try:
            existing_user = empleadosModel.query.filter_by(usuario=self.usuario).first()
            if existing_user:
                raise ValueError("El usuario ya existe.")
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update(self, **kwargs):
      
            
        if kwargs['rol'] == 'Admin' and not current_user.is_admin:
            raise ValueError("No tienes permisos para asignar el rol de Administrador")
        
        if 'contrasena' in kwargs and kwargs['contrasena']:
            kwargs['contrasena'] = self.hash_password(kwargs['contrasena'])
        
        if 'rol' in kwargs and kwargs['rol']:
            kwargs['is_admin'] = True if kwargs['rol'] == 'Admin' else False
        
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value if value != "" else None)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

            raise ValueError("No tienes permisos para asignar el rol de Administrador")
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value if value != "" else None)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def serialize(self):
        return {
            'id': self.id,
            'nombres': self.nombres.title() if self.nombres else "",
            'usuario': self.usuario.lower(),
            'email': self.email.lower() if self.email else "",
            'telefono': self.telefono,
            'rol': self.rol.title(),
            'tipo': self.tipo.title()
        }
    
    def serialize_form(self):
        return {
            'id': self.id,
            'nombres': self.nombres,
            'usuario': self.usuario,
            'email': self.email,
            'telefono': self.telefono,
            'rol': self.rol,
            'tipo': self.tipo
        }

class tarifasOperadoresModel(db.Model):
    __tablename__ = 'tarifas_operadores'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.ForeignKey('tarifas.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    desvios = db.Column(db.Float, nullable=False)
    espera = db.Column(db.Float, nullable=False)
    base = db.Column(db.Float, nullable=False)

    codigo_rel = db.relationship('tarifasModel', back_populates='tarifas_operadores', lazy=True)

    def __init__(self, codigo, tipo, desvios, espera, base):
        self.codigo = codigo.id
        self.tipo = tipo
        self.desvios = desvios
        self.espera = espera
        self.base = base
        
    @property
    def codigo_to(self):
        return self.codigo+"-"+self.tipo

    def __repr__(self):
        return f'<TarifasOperador {self.codigo}>'

    def save(self):
        
        tarifa_existente = tarifasOperadoresModel.query.filter_by(codigo=self.codigo, tipo=self.tipo).first()
        if tarifa_existente:
            raise ValueError("La tarifa ya existe con el mismo tipo.")
        
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        
    def update(self, **kwargs):
        try:
            for key, value in kwargs.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, value)
                    current_app.logger.debug(f"Actualizando {key} a {value}")
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        
    def serialize(self):
        return {
            'id': self.id,
            'codigo': self.codigo_rel.codigo if self.codigo_rel else None,
            'codigo_rel': self.codigo,
            'empresa': self.codigo_rel.cliente.empresa.title() if self.codigo_rel else None,
            'empresa_rel': self.codigo_rel.cliente.id if self.codigo_rel else None,
            # 'codigo': self.codigo_rel.codigo_desc if self.codigo_rel else None,
            'origen': self.codigo_rel.origen_rel.nombre.title() if self.codigo_rel else None,
            'destino': self.codigo_rel.destino_rel.nombre.title() if self.codigo_rel else None,
            'vehiculo': self.codigo_rel.vehiculo_rel.tipo.title() if self.codigo_rel else None,
            'desplazamiento': "Ida y Vuelta" if self.codigo_rel.desplazamiento.lower()== 'idav' else "Ida",
            'tipo': self.tipo.title(),
            'desvios': self.desvios,
            'espera': self.espera,
            'base': self.base
  
        }
    
    def serialize_form(self):
        return {
            'id': self.id,
            'empresa': self.codigo_rel.cliente.id if self.codigo_rel else None,
            'codigo': self.codigo_rel.codigo if self.codigo_rel else None,
            'codigo_rel': self.codigo if self.codigo else None,
            'origen': self.codigo_rel.origen_rel.nombre if self.codigo_rel else None,
            'destino': self.codigo_rel.destino_rel.nombre if self.codigo_rel else None, 
            'desplazamiento': self.codigo_rel.desplazamiento if self.codigo_rel else None,
            'tipo': self.tipo,
            'desvios': self.desvios,
            'espera': self.espera,
            'base': self.base
        }