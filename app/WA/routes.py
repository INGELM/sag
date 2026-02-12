# app/wa/routes.py

from flask import request, jsonify
from sqlalchemy import select
from app.helpers.logger_utils import format_error_simple, registrar_log
from app.programacion.models import programacionModel
from app.wa import wa_bp
from pywa import WhatsApp, types, handlers
from pywa.types import Template
from pywa.types.templates import *
import app.wa as wa_module
from app.clientes.models import clientesModel
from app.extensions import db, csrf
from app.extensions import socketio




@wa_bp.before_request
def bypass_csrf_for_whatsapp():
    if request.path == '/wa/webhook':
        setattr(request, '_csrf_exempt', True)

@wa_bp.route('/send-test', methods=['GET'])
def send_test_message():
    # data = request.json
    to = '584120812115'
    text = 'Mensaje de prueba desde Flask y pywa!'

    if not to:
        return jsonify({'error': 'El campo "to" es obligatorio.'}), 400

    if not wa_module.wa:
        return jsonify({'error': 'La instancia de WhatsApp no está configurada.'}), 500

    msg_id = wa_module.wa.send_message(to='584120812115', text=text)
    return jsonify({'status': 'Mensaje enviado correctamente!', 'message_id': str(msg_id)}), 200




@wa_bp.route('/send', methods=['POST'])
def send_message():
    data = request.form
    to = data.get('to')
    text = data.get('text')

    if not to or not text:
        return jsonify({'error': 'Los campos "to" y "text" son obligatorios.'}), 400

    if not wa_module.wa:
        return jsonify({'error': 'La instancia de WhatsApp no está configurada.'}), 500

    msg_id = wa_module.wa.send_message(to=to, text=text)
    return jsonify({'status': 'Mensaje enviado correctamente!', 'message_id': str(msg_id)}), 200


@wa_bp.route('/send-programacion', methods=['POST'])
def send_programacion_message():
    data = request.get_json()
    # print("DATA RECIBIDA EN FLASK:", data)
    
    operador = data.get('operador')
    to = operador[0]['telefono']
    
     #VALIDACIONES BÁSICAS
    if not to:
        return jsonify({'success': False, 'mensaje': f"No existe telefono asociado para operador: {operador[0]['nombre']}"})
    
    
    
    if not to.startswith('58'):
        to = to.replace("(", "").replace(")", "").replace("-", "")
        to = to.lstrip("0")  # Eliminar el cero inicial si existe
        to = "58" + to  # Agregar el código de país (Venezuela)
        
    if len(to) != 12 or not to.startswith('58'):
        return jsonify({'success': False, 'mensaje': f"El número de teléfono {to} es inválido."})
    
    template_name = 'programacion_viaje'
    language = TemplateLanguage.SPANISH
    
    icono = "→" if data.get('desplazamiento').lower() == "ida" else "⇆"
    empresa = data.get('empresa_rel')
    stmt = select(clientesModel.empresa).where(clientesModel.id == empresa)
    empresa = db.session.execute(stmt).scalar_one_or_none()
    fecha_salida = data.get('fecha_salida')
    hora_salida = data.get('hora_salida')
    hora_retorno = data.get('hora_retorno') if data.get('hora_retorno') else '--'
    ruta = f"{data.get('Ciudad_Origen')} {icono} {data.get('Ciudad_Destino')}"
    pasajeros = " / ".join([f"{p['nombre']} {p['telefono'].strip("()-")}" for p in data.get('pasajeros', [])])
    observaciones = data.get('observaciones') if data.get('observaciones') else '--'
   
    params = [
        BodyText.params(empresa=empresa, fecha=fecha_salida, hora_salida=hora_salida, ruta=ruta, pasajeros=pasajeros, hora_retorno=hora_retorno, observaciones=observaciones),
    ]
    
    try:
        response = wa_module.wa.send_template(
        to=to, name=template_name, language=language, params=params)
        msg_id = response.id
        prog_id = data.get('id')
        stmt = select(programacionModel).where(programacionModel.id == prog_id)
        programacion = db.session.execute(stmt).scalar_one_or_none()
        
        if programacion:
            programacion.wa_msg_id = str(msg_id)
            programacion.wa_status = 'sent'
            
            socketio.emit('message_status_update', {
                'msg_id': str(msg_id),
                'status': 'sent'
            })
            
            db.session.commit()
        else:
            registrar_log("ENVIAR WS", "WHATSAPP", f"No se encontró la programación con ID {prog_id} para actualizar el estado del mensaje.")
            return jsonify({'success':False, 'mensaje': "No se encontro la programación" })
            
        
        
    except Exception as e:
        error = format_error_simple(str(e))
        registrar_log("ENVIAR WS", "WHATSAPP", f"Error al enviar mensaje de programación a {to}: {error}")
        
        return jsonify({'success':False, 'mensaje': "Error Desconocido" })
    
    print(f"Mensaje de plantilla enviado a {to} con ID: {msg_id}")
    return jsonify({'success': True, 'mensaje': 'Mensaje enviado!', 'message_id': str(msg_id)}), 200
        

def register_wa_handlers(wa: WhatsApp):
    @wa.on_message()
    def on_message(_: WhatsApp, message: types.Message):
        print(f"MENSAJE RECIBIDO DE: {message.from_user.wa_id}")
        print(f"CONTENIDO: {message.text}")
        print("Mensaje ID:", message.id)
        message.reply("¡Conexión total!")


    @wa.on_message_status()
    def on_message_status_update(_: WhatsApp, status: types.MessageStatus):
        stmt = select(programacionModel).where(programacionModel.wa_msg_id == str(status.id))
        programacion = db.session.execute(stmt).scalar_one_or_none()
        
        if programacion:
            programacion.wa_status = status.status
            db.session.commit()
            
        socketio.emit('message_status_update', {
            'msg_id': str(status.id), 
            'status': status.status})
        
        print(f"ACTUALIZACIÓN DE ESTADO DE MENSAJE PARA: {status.id}")
        print(f"ESTADO NUEVO: {status.status}")
        if status.status == "failed":
            print(f"Motivo de falla: {getattr(status, 'error', 'No especificado')}")
            
