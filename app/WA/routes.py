import os
from . import wa_bp
from flask import jsonify, request, json
from pywa import WhatsApp


from app.auxiliares.logger_utils import get_logger

log = get_logger()

@wa_bp.route('/', methods=['GET'])
def wa():
    # Cargar variables de entorno directamente
    phone_id = os.environ.get('PHONE_ID')
    token = os.environ.get('TOKEN')
    
    log.debug(f"PHONE_ID: {phone_id}")
    log.debug(f"TOKEN: {token}")
    
    wa = WhatsApp(
            phone_id=phone_id,
            token=token
        )

    
    mensaje = "*PROGRAMACIÓN DE VIAJE*"
    
    try:
        response = wa.send_message(
                    to = '584120812115',
                    text = mensaje
        )
        # log.debug(response)
        return jsonify({'success': True, "mensaje":"Mensaje enviado correctamente"})

    except Exception as e:
        # print(f"❌ Error inesperado: {e}")
        log.error(f"Error al enviar mensaje: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Error al enviar mensaje"
        }), 500
    
@wa_bp.route('/send-programacion', methods=['POST'])
def send_programacion():
    data_str = request.data.decode("utf-8")
    # log.info(f"Datos recibidos: {data_str}")
    
    # Verificar si el string está vacío
    if not data_str.strip():
        log.error("Se recibió un cuerpo de solicitud vacío")
        return jsonify({
            "success": False,
            "error": "Cuerpo de solicitud vacío",
            "message": "Se esperaba un JSON válido en el cuerpo de la solicitud"
        }), 400
        
    try:
        data_dict = json.loads(data_str)
        # log.debug(f"Datos parseados: {data_dict}")
    
    except json.JSONDecodeError as e:
        log.error(f"Error decodificando JSON: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "JSON inválido",
            "message": f"El cuerpo de la solicitud no es un JSON válido: {str(e)}"
        }), 400
        
    fecha = data_dict.get('fecha_salida', 'No proporcionada')
    hora_salida = data_dict.get('hora_salida', 'No proporcionada')
    hora_retorno = data_dict.get('hora_retorno', 'No proporcionada')
    cliente = data_dict.get('empresa', 'No proporcionada')
    origen = data_dict.get('origen', 'No proporcionada')
    destino = data_dict.get('destino', 'No proporcionada')
    pasajeros = data_dict.get('pasajeros', 'No proporcionada')
    direccion_origen = data_dict.get('direccion_origen', 'No proporcionada')
    direccion_destino = data_dict.get('direccion_destino', 'No proporcionada')
    observaciones = data_dict.get('observaciones', 'No proporcionada')
    
    # Formatear direcciones: convertir de lista JSON a texto con saltos de línea
    def format_direccion(direccion):
        if direccion == 'No proporcionada':
            return direccion
        try:
            # Si es un string que contiene una lista JSON, parsearlo
            if isinstance(direccion, str) and direccion.startswith('['):
                direccion_list = json.loads(direccion)
            # Si ya es una lista, usarla directamente
            elif isinstance(direccion, list):
                direccion_list = direccion
            else:
                # Si no es ni lista ni JSON, devolverlo como está
                return str(direccion)
            
            # Unir los elementos con saltos de línea
            return '\n'.join(str(item) for item in direccion_list if item)
        except (json.JSONDecodeError, TypeError):
            # Si hay error al parsear, devolver como string
            return str(direccion)
    
    # Formatear pasajeros para mostrar información detallada
    def format_pasajeros(pasajeros_data, direccion_origen, direccion_destino):
        if not pasajeros_data or pasajeros_data == 'No proporcionada':
            return 'No proporcionados'
        
        try:
            # Parsear pasajeros si es string JSON
            if isinstance(pasajeros_data, str) and pasajeros_data.startswith('['):
                pasajeros_list = json.loads(pasajeros_data)
            elif isinstance(pasajeros_data, list):
                pasajeros_list = pasajeros_data
            else:
                return str(pasajeros_data)
            
            # Parsear direcciones
            direcciones_origen = []
            direcciones_destino = []
            
            if isinstance(direccion_origen, str) and direccion_origen.startswith('['):
                direcciones_origen = json.loads(direccion_origen)
            elif isinstance(direccion_origen, list):
                direcciones_origen = direccion_origen
            
            if isinstance(direccion_destino, str) and direccion_destino.startswith('['):
                direcciones_destino = json.loads(direccion_destino)
                log.debug(f"Direcciones destino if: {direcciones_destino}")
            elif isinstance(direccion_destino, list):
                direcciones_destino = direccion_destino
                log.debug(f"Direcciones destino else: {direcciones_destino}")
            
            # Si hay más de un pasajero, mostrar formato detallado
            if len(pasajeros_list) > 1:
                resultado = f"👤*Pasajeros ({len(pasajeros_list)}):*\n\n"
                for i, pasajero in enumerate(pasajeros_list):
                    resultado += f"*_Pasajero {i+1}_*\n"
                    
                    # Manejar si pasajero es objeto o string
                    if isinstance(pasajero, dict):
                        resultado += f"*Nombre:* {pasajero.get('nombre', 'No especificado')}\n"
                        if pasajero.get('telefono'):
                            resultado += f"*Teléfono:* {pasajero.get('telefono')}\n"
                    else:
                        resultado += f"*Nombre:* {pasajero}\n"

                    # Agregar direcciones si están disponibles
                    if i < len(direcciones_origen) and direcciones_origen[i]:
                        resultado += f"*Origen:* {direcciones_origen[i]}\n"
                    if i < len(direcciones_destino) and direcciones_destino[i]:
                        resultado += f"*Destino:* {direcciones_destino[i]}\n"
                    
                    resultado += "\n"
                
                return resultado.strip()
            else:
                # Un solo pasajero
                resultado = f"👤 *Pasajero ({len(pasajeros_list)}):*\n\n"
                pasajero = pasajeros_list[0]
                if isinstance(pasajero, dict):
                    resultado += f"*Nombre:* {pasajero.get('nombre', 'No especificado')}\n"
                    if pasajero.get('telefono'):
                        resultado += f"*Teléfono:* {pasajero.get('telefono')}\n"
                    if direcciones_origen and direcciones_origen[0]:
                        resultado += f"*Origen:* {direcciones_origen[0]}\n"
                    if direcciones_destino and direcciones_destino[0]:
                        resultado += f"*Destino:* {direcciones_destino[0]}\n"
                    resultado += "\n"
                    return resultado.strip()
                else:
                    return f"{pasajero}"
                    
        except (json.JSONDecodeError, TypeError):
            return str(pasajeros_data)
    
    # Determinar tipo de viaje
    icono_viaje = "⇆" if hora_retorno and hora_retorno != 'No proporcionada' else "→"
    tipo_viaje = "Ida y Vuelta" if hora_retorno and hora_retorno != 'No proporcionada' else "Solo Ida"
    
    # Formatear pasajeros
    pasajeros_formateados = format_pasajeros(pasajeros, direccion_origen, direccion_destino)
    
    # Construir mensaje profesional
    mensaje = f"""*PROGRAMACIÓN DE VIAJE*

🏦 *{cliente.upper()}*
{origen} {icono_viaje} {destino}



📅 *Fecha:* {fecha}
🕔 *Hora Salida:* {hora_salida}"""

    # Agregar hora de retorno solo si existe
    if hora_retorno and hora_retorno != 'No proporcionada':
        mensaje += f"\n🕔 *Hora Retorno:* {hora_retorno}"
    
    mensaje += f"""

{pasajeros_formateados}"""

    # Agregar observaciones si existen
    if observaciones and observaciones != 'No proporcionada':
        mensaje += f"""

🗒️ *OBSERVACIONES*
{observaciones}"""
    
    # mensaje += "\n\n━━━━━━━━━━━━━"
    
    log.debug(f"Mensaje a enviar: {mensaje}")
    
    # Cargar variables de entorno directamente
    phone_id = os.environ.get('PHONE_ID')
    token = os.environ.get('TOKEN')
    
    wa = WhatsApp(
            phone_id=phone_id,
            token=token
        )
    
    try:
        response = wa.send_message(
                    to = '584120812115',
                    text=mensaje)
                   
        # log.debug(response)
        log.info(f'{response}')
        return jsonify({'success': True, "mensaje":"Mensaje enviado correctamente"})

    except Exception as e:
        log.error(f"Error de WhatsApp API: {e.message}", exc_info=True)
        if "Error validating access token" in str(e):
            mensaje = "Token inválido o expirado. Por favor, contacta al administrador."
        else:
            mensaje = "Error en el envío del mensaje. Por favor, intenta nuevamente."
        return jsonify({
            "success": False,
            "error": "Mensaje no enviado",
            "mensaje": mensaje
        })
