from flask import Response, json, jsonify, render_template, request, current_app
from flask_login import login_required, current_user
from app.clientes.models import clientesModel, pasajerosModel, recargoVehiculosModel, tarifasModel
from . import clientes_bp
from .form import *
from datetime import datetime
from app.extensions import db

# @clientes_bp.before_request
# def before_request():
#     if not current_user.is_authenticated:
#         flash('Por favor, inicie sesión para acceder a esa página.', 'warning')
#         return redirect(url_for('login.login'))
        



@clientes_bp.route('/clientes', methods=['GET', 'POST', 'DELETE', 'PUT'])
# @login_required
def clientes():
    
    if not current_user.is_admin and request.method in ['DELETE', 'PUT']:
            return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.")

    form = clientesForm()
    
    cliente_data =  {**form.data}
    current_app.logger.info(f'Datos recibidos del formulario: {cliente_data}')

    # if 'ciudad' in cliente_data and cliente_data['ciudad']:
    #     cliente_data['ciudad'] = cliente_data['ciudad'].id

    if request.method == 'PUT' and form.validate_on_submit():
        
        current_app.logger.debug(f'Recibido datos de cliente para actualizar: {cliente_data}')
        
        if not cliente_data or 'id' not in cliente_data:
            return jsonify(success=False, mensaje='Datos de cliente inválidos.')

        cliente_id = cliente_data.get('id')
        cliente = clientesModel.query.get(cliente_id)
        
        if not cliente:
            return jsonify(success=False, mensaje='cliente no encontrado.')
        # Eliminar campos no relacionados con el modelo antes de actualizar
        
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id']:
            current_app.logger.debug(f'Campos eliminados: {field}')
            cliente_data.pop(field, None)
        
         # Convertir campos tipo <empleadosModel ...> a su id
        for key, value in cliente_data.items():
            if hasattr(value, 'id'):
                cliente_data[key] = value.id

        try:
            cliente.update(**cliente_data)
            current_app.logger.debug(f'Datos de cliente después de eliminar campos no relacionados: {cliente_data}')
            return jsonify(success=True, mensaje='cliente actualizado exitosamente.')
        
        except Exception as e:
            current_app.logger.debug(f'Error al actualizar cliente: {e}')
            return jsonify({
                'success': False,
                'mensaje': 'Error al actualizar el cliente.',
                'error': str(e)
            }), 500
            
            
    elif request.method == 'DELETE':
        cliente_id = request.get_json().get('id')
        current_app.logger.debug(f'Recibido ID de cliente para eliminar: {cliente_id}')
        
        if not cliente_id:
            return jsonify(success=False, mensaje='ID de cliente inválido.')

        cliente = clientesModel.query.get(cliente_id)
        
        if not cliente:
            return jsonify(success=False, mensaje='cliente no encontrado.')
        
        try:
            cliente.delete()
            return jsonify(success=True, mensaje='cliente eliminado exitosamente.')
        
       

      
        
        except Exception as e:
            current_app.logger.debug(f'Error al eliminar cliente: {e}')
            
            if '1452' in str(e).lower():
                mensaje='No se puede eliminar el cliente porque tiene registros relacionados.'

            return jsonify({
                'success': False,
                'mensaje': mensaje,
                'error': str(e)
            }), 500

    elif request.method == 'POST' and form.validate_on_submit():
        cliente = {**form.data}
        # Eliminar campos no relacionados con el modelo antes de crear el cliente
        for field in ['csrf_token',  'submit', 'id']:
            cliente.pop(field, None)
        nuevo_cliente = clientesModel(**cliente)
        try:
            existing = clientesModel.query.filter_by(codigo=nuevo_cliente.codigo).first()
            if existing:
                raise ValueError("El código ya existe.")
            
            db.session.add(nuevo_cliente)
            # crear_recargo_sedan(nuevo_cliente)  # Crear un vehículo tipo Sedan al registrar un cliente
            db.session.commit()
            return jsonify(success=True, mensaje='cliente registrado exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al registrar cliente: {e}')
            return jsonify(success=False, mensaje='Error al registrar el cliente.', errores=str(e))

    elif form.errors:
 
        first_field, first_errors = next(iter(form.errors.items()))
        error_messages = f"{first_field}: {first_errors[0]}"
        current_app.logger.debug(f'Errores en el formulario: {error_messages}')
        return jsonify(success=False, mensaje='Error al registrar el cliente.', errores=error_messages)

    return render_template('clientes.html', year=datetime.now().year, form=clientesForm(), User=current_user)

@clientes_bp.route('/clientes/get_data/<int:id>', methods=['GET'])
def get_cliente_data(id):
    current_app.logger.debug(f'Recibiendo solicitud para obtener datos del cliente con ID: {id}')
    try:
        cliente = clientesModel.query.get(id)
        
        if not cliente:
            return jsonify(success=False, mensaje='Cliente no encontrado.')

        response = cliente.serialize_form()
        current_app.logger.debug(f'Datos del cliente obtenidos: {response}')

        return jsonify(success=True, data=response, mensaje='Datos del cliente obtenidos exitosamente.')

    except Exception as e:
        current_app.logger.debug(f'Error al obtener datos del cliente: {e}')
        return jsonify(success=False, mensaje='Error al obtener datos del cliente.', errores=str(e))
    
    

@clientes_bp.route('clientes/all', defaults={'id': None}, methods=['GET'])
@clientes_bp.route('clientes/get/<int:id>', methods=['GET'])
# @login_required
def handle_clientes(id):
    current_app.logger.debug(f'ID recibido en handle_clientes: {id}')
    try:
        if not id:
            clientes = clientesModel.query.all()
        else:
            clientes = clientesModel.query.get(id)
            
        clientes = clientes if isinstance(clientes, list) else [clientes]
        clientes_serialized = [e.serialize() for e in clientes]
       
 
        
        response_data = {
            'success': True,
            'data': clientes_serialized,
            'mensaje': 'Consulta exitosa'
        }
        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')
     
    except Exception as e:
        error = str(e)
        if 'not found' in error.lower():
            return jsonify(success=False, mensaje='No se encontraron clientes.')
        elif 'database' in error.lower():
            return jsonify(success=False, mensaje='Error de base de datos.')
        elif 'connection' in error.lower():
            return jsonify(success=False, mensaje='Error de conexión a la base de datos.')
        elif 'timeout' in error.lower():
            return jsonify(success=False, mensaje='Tiempo de espera agotado al intentar acceder a la base de datos.')
        else:
            # current_app.logger.debug(f'Error desconocido: {error}')
            return jsonify(success=False, mensaje=error)

@staticmethod
def crear_recargo_sedan(nuevo_cliente):
    sedan_id = vehiculosModel.query.filter_by(codigo='SEDN').first().id
    
    if not sedan_id:
        raise ValueError("Vehículo tipo Sedan no encontrado. Asegúrese de que el vehículo exista en la base de datos.")

    try:
        recargo_sedan = recargoVehiculosModel(vehiculo=sedan_id, recargo=0.0, cliente=nuevo_cliente)
        recargo_sedan.save()
        return recargo_sedan
    except Exception as e:
        current_app.logger.debug(f'Error al crear recargo Sedan: {e}')
        raise ValueError(f'Error Inesperado al crear recargo para Sedan')

# PASAJEROS

@clientes_bp.route('/pasajeros', methods=['GET', 'POST', 'DELETE', 'PUT'])
def pasajeros():
    
    form = pasajerosForm()
    pasajero_data = request.get_json() if request.method in ['PUT', 'DELETE'] else form.data
    # current_app.logger.info(f'Datos recibidos del formulario: {pasajero_data}')

    # if 'ciudad' in pasajero_data and pasajero_data['ciudad']:
    #     pasajero_data['ciudad'] = pasajero_data['ciudad'].id

    if request.method == 'PUT' and form.validate_on_submit():

        current_app.logger.debug(f'Recibido datos de pasajero para actualizar: {pasajero_data}')
        if not pasajero_data or 'id' not in pasajero_data:
            return jsonify(success=False, mensaje='Datos de pasajero inválidos.')

        pasajero_id = pasajero_data.get('id')
        pasajero = pasajerosModel.query.get(pasajero_id)

        if not pasajero:
            return jsonify(success=False, mensaje='pasajero no encontrado.')
        # Eliminar campos no relacionados con el modelo antes de actualizar
        
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id']:
            pasajero_data.pop(field, None)

        pasajero_data['empresa_id'] = pasajero_data.get('empresa', pasajero.empresa)
        pasajero_data['ciudad_id'] = pasajero_data.get('ciudad', pasajero.ciudad)

        current_app.logger.info(f'Datos de pasajero después de eliminar campos no relacionados: {pasajero_data}')

        try:
            pasajero.update(**pasajero_data)
            return jsonify(success=True, mensaje='pasajero actualizado exitosamente.')

        except Exception as e:
            current_app.logger.debug(f'Error al actualizar pasajero: {e}')
            return jsonify({
                'success': False,
                'mensaje': 'Error al actualizar el pasajero.',
                'error': str(e)
            }), 500
            
            
    if request.method == 'DELETE':
            current_app.logger.debug('Recibida solicitud de eliminación de pasajero')
            pasajero_id = request.get_json().get('id')
            current_app.logger.debug(f'Recibido ID de pasajero para eliminar: {pasajero_id}')
            if not pasajero_id:
                return jsonify(success=False, mensaje='ID de pasajero inválido.')

            pasajero = pasajerosModel.query.get(pasajero_id)

            if not pasajero:
                return jsonify(success=False, mensaje='pasajero no encontrado.')

            try:
                pasajero.delete()
                return jsonify(success=True, mensaje='pasajero eliminado exitosamente.')

            except Exception as e:
                current_app.logger.debug(f'Error al eliminar cliente: {e}')
                return jsonify({
                    'success': False,
                    'mensaje': 'Error al eliminar el cliente.',
                    'error': str(e)
                }), 500
            
    elif form.validate_on_submit():
        cliente = {**form.data}
        # Eliminar campos no relacionados con el modelo antes de crear el cliente
        for field in ['csrf_token',  'submit', 'id']:
            cliente.pop(field, None)
        nuevo_cliente = pasajerosModel(**cliente)
        try:
            nuevo_cliente.save()
            return jsonify(success=True, mensaje='cliente registrado exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al registrar cliente: {e}')
            return jsonify(success=False, mensaje='Error al registrar el cliente.', errores=str(e))

    elif form.errors:
 
        first_field, first_errors = next(iter(form.errors.items()))
        error_messages = f"{first_field[0]}: {first_errors[0]}"
        current_app.logger.debug(f'Errores en el formulario: {error_messages}')
        return jsonify(success=False, mensaje='Error al registrar el cliente.', errores=error_messages)

    return render_template('pasajeros.html', year=datetime.now().year, form=pasajerosForm(), User=current_user)

@clientes_bp.route('/pasajeros/get_data/<int:id>', methods=['GET'])
def get_pasajero_data(id):
    current_app.logger.debug(f'Recibiendo solicitud para obtener datos del pasajero con ID: {id}')
    try:
        pasajero = pasajerosModel.query.get(id)
        
        if not pasajero:
            return jsonify(success=False, mensaje='Pasajero no encontrado.')

        response = pasajero.serialize_form()
        current_app.logger.debug(f'Datos del pasajero obtenidos: {response}')

        return jsonify(success=True, data=response, mensaje='Datos del pasajero obtenidos exitosamente.')

    except Exception as e:
        current_app.logger.debug(f'Error al obtener datos del pasajero: {e}')
        return jsonify(success=False, mensaje='Error al obtener datos del pasajero.', errores=str(e))


@clientes_bp.route('pasajeros/all', defaults={'id': None}, methods=['GET'])
@clientes_bp.route('pasajeros/get/<int:id>', methods=['GET'])
def handle_pasajeros(id):
    current_app.logger.debug(f'ID recibido en handle_pasajeros: {id}')
    try:
        if not id:
            pasajeros = pasajerosModel.query.all()
        else:
            pasajeros = pasajerosModel.query.get(id)

        pasajeros = pasajeros if isinstance(pasajeros, list) else [pasajeros]
        pasajeros_serialized = [e.serialize() for e in pasajeros]
       
        if not pasajeros_serialized:
            response_data = {
                'success': True,
                'data': [],
                'mensaje': 'No se encontraron pasajeros.'
            }
            current_app.logger.debug('No se encontraron pasajeros.')
        else:
            current_app.logger.debug(f'Pasajeros encontrados: {len(pasajeros_serialized)}')
            response_data = {
                'success': True,
            'data': pasajeros_serialized,
            'mensaje': 'Consulta exitosa'

        }
        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')
     
    except Exception as e:
        error = str(e)
        if 'not found' in error.lower():
            return jsonify(success=False, mensaje='No se encontraron pasajeros.')
        elif 'database' in error.lower():
            return jsonify(success=False, mensaje='Error de base de datos.')
        elif 'connection' in error.lower():
            return jsonify(success=False, mensaje='Error de conexión a la base de datos.')
        elif 'timeout' in error.lower():
            return jsonify(success=False, mensaje='Tiempo de espera agotado al intentar acceder a la base de datos.')
        else:
            # current_app.logger.debug(f'Error desconocido: {error}')
            return jsonify(success=False, mensaje=error)


@clientes_bp.route('/empresas/pasajeros', methods=['GET'])
def obtener_pasajeros():
    empresa_id = request.args.get('empresa', type=int)
    current_app.logger.debug(f'ID de empresa recibido: {empresa_id}')
    if not empresa_id:
        current_app.logger.debug('ID de empresa no proporcionado o inválido.')
        return jsonify(success=False, data=[], mensaje='ID de empresa no proporcionado o inválido.')

    try:
        pasajeros = pasajerosModel.query.filter_by(empresa=empresa_id).all()
        if not pasajeros:
            current_app.logger.debug(f'No se encontraron pasajeros para la empresa con ID {empresa_id}')
            return jsonify(success=False, mensaje='No se encontraron pasajeros para esta empresa.')
        current_app.logger.debug(f'Pasajeros encontrados para la empresa con ID {empresa_id}: {len(pasajeros)}')
        return jsonify(success=True, data=[p.serialize() for p in pasajeros])
    
    except Exception as e:
        current_app.logger.debug(f'Error al obtener pasajeros por empresa: {e}')
        return jsonify(success=False, mensaje='Error al obtener pasajeros por empresa.', error=str(e))


# TARIFAS

@clientes_bp.route('/tarifas', methods=['GET', 'POST', 'DELETE', 'PUT'])
def tarifas():
    
    form = tarifasForm()
    tarifa_data = request.get_json() if request.method in ['PUT', 'DELETE'] else form.data
    current_app.logger.debug(f'Datos recibidos del formulario: {tarifa_data}')

    # if 'ciudad' in pasajero_data and pasajero_data['ciudad']:
    #     pasajero_data['ciudad'] = pasajero_data['ciudad'].id

    if request.method == 'PUT' and form.validate_on_submit():

        current_app.logger.debug(f'Recibido datos de tarifa para actualizar: {tarifa_data}')
        if not tarifa_data or 'id' not in tarifa_data:
            return jsonify(success=False, mensaje='Datos de tarifa inválidos.')

        tarifa_id = tarifa_data.get('id')
        tarifa = tarifasModel.query.get(tarifa_id)

        if not tarifa:
            return jsonify(success=False, mensaje='tarifa no encontrada.')
        # Eliminar campos no relacionados con el modelo antes de actualizar
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id']:
            tarifa_data.pop(field, None)


        try:
            tarifa.update(**tarifa_data)
            return jsonify(success=True, mensaje='tarifa actualizado exitosamente.')

        except Exception as e:
            current_app.logger.debug(f'Error al actualizar tarifa: {e}')
            return jsonify({
                'success': False,
                'mensaje': 'Error al actualizar la tarifa.',
                'error': str(e)
            }), 500


    if request.method == 'DELETE':
            current_app.logger.debug('Recibida solicitud de eliminación de tarifa')
            tarifa_id = request.get_json().get('id')
            current_app.logger.debug(f'Recibido ID de tarifa para eliminar: {tarifa_id}')
            if not tarifa_id:
                return jsonify(success=False, mensaje='ID de tarifa inválido.')

            tarifa = tarifasModel.query.get(tarifa_id)

            if not tarifa:
                return jsonify(success=False, mensaje='tarifa no encontrada.')

            try:
                tarifa.delete()
                return jsonify(success=True, mensaje='tarifa eliminada exitosamente.')

            except Exception as e:
                # current_app.logger.debug(f'Error al eliminar cliente: {e}')
                return jsonify({
                    'success': False,
                    'mensaje': 'Error al eliminar la tarifa.',
                    'error': str(e)
                }), 500

    elif form.validate_on_submit():
        tarifa = {**form.data}
        # Eliminar campos no relacionados con el modelo antes de crear la tarifa
        for field in ['csrf_token',  'submit', 'id']:
            tarifa.pop(field, None)
        
        
        
        
        nuevo_tarifa = tarifasModel(**tarifa)
        try:
            nuevo_tarifa.save()
            return jsonify(success=True, mensaje='tarifa registrada exitosamente.')
        except Exception as e:
            # current_app.logger.debug(f'Error al registrar cliente: {e}')
            return jsonify(success=False, mensaje='Error al registrar la tarifa.', errores=str(e))

    elif form.errors:

        first_field, first_errors = next(iter(form.errors.items()))
        field_label = getattr(form, first_field).label.text
        error_messages = f"{first_errors[0]}"
        errores = f'{field_label}: {error_messages}'
        current_app.logger.debug(f'Errores en el formulario: {field_label}: {error_messages}')
        return jsonify(success=False, mensaje='Error al registrar la tarifa.', errores=errores)

    return render_template('tarifas.html', year=datetime.now().year, form=tarifasForm(), User=current_user)

@clientes_bp.route('/tarifas/get_data/<int:id>', methods=['GET'])
def get_tarifa_data(id):
    current_app.logger.debug(f'Recibiendo solicitud para obtener datos de la tarifa con ID: {id}')
    try:
        tarifa = tarifasModel.query.get(id)
        
        if not tarifa:
            return jsonify(success=False, mensaje='Tarifa no encontrada.')

        response = tarifa.serialize_form()
        current_app.logger.debug(f'Datos de la tarifa obtenidos: {response}')

        return jsonify(success=True, data=response, mensaje='Datos de la tarifa obtenidos exitosamente.')

    except Exception as e:
        current_app.logger.debug(f'Error al obtener datos de la tarifa: {e}')
        return jsonify(success=False, mensaje='Error al obtener datos de la tarifa.', errores=str(e))



@clientes_bp.route('tarifas/all',  methods=['GET'])
@clientes_bp.route('/get/tarifas', methods=['GET'])
def handle_tarifas():
    empresa_id = request.args.get('empresa', type=int)
    current_app.logger.debug(f'ID recibido en handle_tarifas: {empresa_id}')
    try:
        if not empresa_id:
            tarifas = tarifasModel.query.all()
        else:
            tarifas = tarifasModel.query.filter_by(empresa=empresa_id).all()

        tarifas = tarifas if isinstance(tarifas, list) else [tarifas]
        tarifas_serialized = [e.serialize() for e in tarifas]
        # current_app.logger.debug(f'Tarifas encontradas: {len(tarifas_serialized)}')
      

        response_data = {
            'success': True,
            'data': tarifas_serialized,
            'mensaje': 'Consulta exitosa'
        }
        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')

    except Exception as e:
        error = str(e)
        if 'not found' in error.lower():
            return jsonify(success=False, mensaje='No se encontraron tarifas.')
        elif 'database' in error.lower():
            return jsonify(success=False, mensaje='Error de base de datos.')
        elif 'connection' in error.lower():
            return jsonify(success=False, mensaje='Error de conexión a la base de datos.')
        elif 'timeout' in error.lower():
            return jsonify(success=False, mensaje='Tiempo de espera agotado al intentar acceder a la base de datos.')
        else:
            # current_app.logger.debug(f'Error desconocido: {error}')
            return jsonify(success=False, mensaje=error)


#RECARGO VEHÍCULOS

@clientes_bp.route('/recargoVehiculos', methods=['GET', 'POST', 'DELETE', 'PUT'])
def recargo_vehiculos():
    form = recargoVehiculosForm()
    formData = form.data
    current_app.logger.debug(f'Datos recibidos del formulario: {formData}')
    
    if request.method == 'GET':
        
        user = current_user
        return render_template('recargoVehiculos.html', year=datetime.now().year, form=form, User=user)
        
        pass
    elif request.method == 'POST' and form.validate_on_submit():
        # Lógica para crear un nuevo recargo de vehículo
        nuevo_recargo = recargoVehiculosModel(
            cliente=form.empresa.data.id,
            vehiculo=form.vehiculo.data.id,
            recargo=form.recargo.data
        )
        try:
            nuevo_recargo.save()
            return jsonify(success=True, mensaje='Recargo de vehículo registrado exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al registrar recargo de vehículo: {e}')
            return jsonify(success=False, mensaje='Error al registrar el recargo de vehículo.', errores="Falla al registrar el recargo de vehículo. Asegúrese de que el vehículo y la empresa existan en la base de datos.")
    elif request.method == 'DELETE':
        # Lógica para eliminar un recargo de vehículo
        recargo_id = request.get_json().get('id')
        current_app.logger.debug(f'Recibido ID de recargo para eliminar: {recargo_id}')
        if not recargo_id:
            return jsonify(success=False, mensaje='ID de recargo inválido.')

        recargo = recargoVehiculosModel.query.get(recargo_id)

        if not recargo:
            return jsonify(success=False, mensaje='Recargo no encontrado.')

        try:
            recargo.delete()
            return jsonify(success=True, mensaje='Recargo de vehículo eliminado exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al eliminar recargo de vehículo: {e}')
            return jsonify(success=False, mensaje='Error al eliminar el recargo de vehículo.', error=str(e))
        
    elif request.method == 'PUT':
        # Lógica para actualizar un recargo de vehículo
        pass

@clientes_bp.route('recargoVehiculos/all', defaults={'id': None}, methods=['GET'])
@clientes_bp.route('recargoVehiculos/get/<int:id>', methods=['GET'])
def handle_recargos(id):
    try:
        if not id:
            recargos = recargoVehiculosModel.query.all()
        else:
            recargos = recargoVehiculosModel.query.get(id)

        recargos = recargos if isinstance(recargos, list) else [recargos]
        recargos_serialized = [r.serialize() for r in recargos]

        response_data = {
            'success': True,
            'data': recargos_serialized,
            'mensaje': 'Consulta exitosa'
        }
        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')

    except Exception as e:
        error = str(e)
        if 'not found' in error.lower():
            return jsonify(success=False, mensaje='No se encontraron recargos.')
        elif 'database' in error.lower():
            return jsonify(success=False, mensaje='Error de base de datos.')
        elif 'connection' in error.lower():
            return jsonify(success=False, mensaje='Error de conexión a la base de datos.')
        elif 'timeout' in error.lower():
            return jsonify(success=False, mensaje='Tiempo de espera agotado al intentar acceder a la base de datos.')
        else:
            return jsonify(success=False, mensaje=error)

@clientes_bp.route('/vehiculos', methods=['GET'])
def vehiculos_empresa():
    empresa_id = request.args.get('empresa', type=int)
    current_app.logger.debug(f'ID de empresa recibido: {empresa_id}')
   
    if not empresa_id:
        current_app.logger.debug('ID de empresa no proporcionado o inválido.')
        return jsonify(success=False, data=[], mensaje='ID de empresa no proporcionado o inválido.')

    try:
        vehiculos_empresa = tarifasModel.query.filter_by(empresa=empresa_id).all()
        vehiculos_ids = [v.vehiculo for v in vehiculos_empresa]
        current_app.logger.debug(f'IDs de vehículos para la empresa {empresa_id}: {vehiculos_ids}')

        vehiculos = vehiculosModel.query.filter(vehiculosModel.id.in_(vehiculos_ids)).all()
        current_app.logger.debug(f'Vehículos encontrados: {len(vehiculos)}')
        
        if not vehiculos:
            current_app.logger.debug(f'No se encontraron vehículos para la empresa con ID {empresa_id}')
            return jsonify(success=False, mensaje='No se encontraron vehículos para esta empresa.')
        
        current_app.logger.debug(f'Vehículos encontrados para la empresa con ID {empresa_id}: {len(vehiculos)}')
        data = [v.serialize() for v in vehiculos]
        # data.sort(key=lambda x: x['vehiculo']['codigo'])  # Ordenar por código del vehículo
        current_app.logger.debug(f'Datos de vehículos serializados: {data}')
        
        return jsonify(success=True, data=data)

    except Exception as e:
        current_app.logger.debug(f'Error al obtener vehículos por empresa: {e}')
        return jsonify(success=False, mensaje='Error al obtener vehículos por empresa.', error=str(e))
