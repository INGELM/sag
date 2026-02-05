from functools import wraps
import json
from flask import current_app, request
from flask_login import current_user
import sys
import os

def registrar_log(accion, entidad, detalle):
    """
    Estandariza el registro de acciones en el log de la aplicación.
    Acciones: 'CREAR', 'EDITAR', 'ELIMINAR', 'LOGIN'
    """
    usuario = current_user.usuario if current_user.is_authenticated else "Anonimo"
    ip = request.remote_addr
    
    mensaje = (
        f"| ACCION: {accion:<10} "
        f"| ENTIDAD: {entidad:<15} "
        f"| USUARIO: {usuario:<15} "
        f"| DETALLE: {detalle}"
    )
    
    current_app.logger.info(mensaje)
    



def format_error_simple(e):
    """Retorna un mensaje corto: 'TipoError: mensaje [archivo.py:linea]'"""
    exc_type, exc_obj, exc_tb = sys.exc_info()
    if exc_tb:
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return f"{type(e).__name__}: {str(e)} [{fname}:{exc_tb.tb_lineno}]"
    return str(e)



def log_action(action, entity):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            if response.status_code == 200:
                try:
                    data = json.loads(response.get_data(as_text=True))
                    success = data.get('success', False)
                    usuario = current_user.usuario if current_user.is_authenticated else "Anonimo"
                    
                    # CAPTURA MANUAL DEL ORIGEN
                    # f.__code__.co_filename nos da la ruta del archivo de la ruta
                    # f.__name__ nos da el nombre de la función (ej: editar_factura)
                    archivo_origen = os.path.basename(f.__code__.co_filename)
                    nombre_funcion = f.__name__
                    origen_exacto = f"{archivo_origen}:{nombre_funcion}"
                    
                    log_level = "AUDIT" if success else "REJECTED"
                    msg_final = data.get('log') or data.get('mensaje') or 'Sin detalle'
                    
                    mensaje = (
                        f" [{log_level}] "
                        f"| ORIGEN: {origen_exacto:<30} "
                        f"| ACCION: {action:<10} "
                        f"| ENTIDAD: {entity:<15} "
                        f"| USUARIO: {usuario:<15} "
                        f"| MSG: {msg_final} "
                    )
                    
                    if success:
                        current_app.logger.info(mensaje)
                    else:
                        current_app.logger.warning(mensaje)
                        
                except Exception as e:
                    current_app.logger.error(f"Error en decorador: {str(e)}")
                    
            return response
        return decorated_function
    return decorator