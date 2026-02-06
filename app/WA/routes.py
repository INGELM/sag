# app/wa/routes.py

from flask import request, jsonify
from app.wa import wa_bp
from pywa import WhatsApp, types
from pywa.types import Template
from pywa.types.templates import *
import app.wa as wa_module


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


@wa_bp.route('/send-template', methods=['get'])
def send_template_message():
    # data = request.form
    to = '584120812115'
    template_name = 'programacion_viaje'
    language = TemplateLanguage.SPANISH
    data = request.form

    if not to or not template_name:
        return jsonify({'error': 'Los campos "to" y "template_name" son obligatorios.'}), 400

    if not wa_module.wa:
        return jsonify({'error': 'La instancia de WhatsApp no está configurada.'}), 500
    
    pasajeros = "Juan Pérez (04125845225) / María Gómez (04125845225) / Carlos López (04125845225)"
    
    pasajeros = pasajeros.strip()

    params = [
        BodyText.params(empresa="Transporte XYZ", fecha="25 de diciembre de 2024", hora_salida="10:00 AM", ruta="Ciudad A → Ciudad B", pasajeros=pasajeros, hora_retorno="5:00 PM", observaciones="--"),
    ]
    try:
        msg_id = wa_module.wa.send_template(
        to=to, name=template_name, language=language, params=params)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'Mensaje de plantilla enviado correctamente!', 'message_id': str(msg_id)}), 200





def register_wa_handlers(wa: WhatsApp):
    @wa.on_message()
    def on_message(_: WhatsApp, message: types.Message):
        print(f"MENSAJE RECIBIDO DE: {message.from_user.wa_id}")
        print(f"CONTENIDO: {message.text}")
        message.reply("¡Conexión total!")

    @wa.on_message_status()
    def on_message_status_update(_: WhatsApp, status: types.MessageStatus):
        print(f"ACTUALIZACIÓN DE ESTADO DE MENSAJE PARA: {status.id}")
        print(f"ESTADO NUEVO: {status.status}")
