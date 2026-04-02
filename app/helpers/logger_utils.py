from functools import wraps
import json
from flask import current_app, request, make_response
from flask_login import current_user
import sys
import os

def registrar_log(accion, entidad, detalle, programacion_id=None):
    """
    Estandariza el registro de acciones en el log de la aplicación.
    Acciones: 'CREAR', 'EDITAR', 'ELIMINAR', 'LOGIN'
    """
    usuario = current_user.usuario if current_user.is_authenticated else "Anonimo"
    programacion_info = f"| PROGRAMACION_ID: {str(programacion_id if programacion_id is not None else 'N/A'):<10} "

    mensaje = (
        f"| ACCION: {accion:<10} "
        f"| ENTIDAD: {entidad:<15} "
        f"{programacion_info}"
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



def _action_from_method(action):
    if action and action.upper() not in ("CRUD", "AUTO"):
        return action.upper()

    method_map = {
        "POST": "CREAR",
        "PUT": "EDITAR",
        "PATCH": "EDITAR",
        "DELETE": "ELIMINAR",
        "GET": "CONSULTAR",
    }
    return method_map.get(request.method, action or "ACCION")


def log_action(action, entity):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)

            # Solo auditar operaciones de escritura para CRUD.
            if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
                return response

            try:
                response_obj = make_response(response)
                data = response_obj.get_json(silent=True)

                if data is None:
                    raw = response_obj.get_data(as_text=True)
                    data = json.loads(raw) if raw else {}

                status_code = response_obj.status_code
                success = bool(data.get("success")) if isinstance(data, dict) and "success" in data else status_code < 400
                usuario = current_user.usuario if current_user.is_authenticated else "Anonimo"
                archivo_origen = os.path.basename(f.__code__.co_filename)
                nombre_funcion = f.__name__
                origen_exacto = f"{archivo_origen}:{nombre_funcion}"
                accion_final = _action_from_method(action)
                log_level = "AUDIT" if success else "REJECTED"

                if isinstance(data, dict):
                    msg_final = data.get("log") or data.get("mensaje") or data.get("error") or data.get("errores") or "Sin detalle"
                else:
                    msg_final = "Sin detalle"

                mensaje = (
                    f" [{log_level}] "
                    f"| ORIGEN: {origen_exacto:<30} "
                    f"| ACCION: {accion_final:<10} "
                    f"| ENTIDAD: {entity:<15} "
                    f"| USUARIO: {usuario:<15} "
                    f"| HTTP: {request.method:<6} "
                    f"| STATUS: {status_code:<3} "
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