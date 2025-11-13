from flask import Response, current_app, flash, json, jsonify, render_template, request, session
from flask_login import login_required, current_user
import requests
from app.auxiliares.models import ciudadesModel, tasaModel
from app.clientes.models import clientesModel, tarifasModel
from app.empleados.models import tarifasOperadoresModel
from . import ciudades_bp, vehiculos_bp, tasa_bp
from .form import *
from app.auxiliares.form import ciudadesForm, vehiculosForm
from app.auxiliares.models import ciudadesModel, vehiculosModel, tasaModel
from datetime import datetime
from app.extensions import db




@ciudades_bp.route('/', methods=['GET', 'POST', 'DELETE', 'PUT'])
# @login_required
def ciudades():
    form = ciudadesForm()

    if request.method == 'PUT' and form.validate_on_submit():
        ciudad_json = request.get_json()
        
        ciudad_data = {
            'id': ciudad_json.get('id'),
            'codigo': ciudad_json.get('codigo', '').upper(),
            'nombre': ciudad_json.get('nombre', '').title()
        }
        
        current_app.logger.debug(f'Recibido datos de ciudad para actualizar: {ciudad_data}')
        if not ciudad_data or 'id' not in ciudad_data:
            return jsonify(success=False, mensaje='Datos de ciudad inválidos.')

        ciudad_id = ciudad_data.get('id')
        ciudad = ciudadesModel.query.get(ciudad_id)

        if not ciudad:
            return jsonify(success=False, mensaje='Ciudad no encontrada.')
        # Eliminar campos no relacionados con el modelo antes de actualizar
        for field in ['csrf_token', 'submit', 'id']:
            ciudad_data.pop(field, None)
            

        try:
            ciudad.update(**ciudad_data)
            return jsonify(success=True, mensaje='Ciudad actualizada exitosamente.')

        except Exception as e:
            current_app.logger.debug(f'Error al actualizar ciudad: {e}')
            return jsonify({
                'success': False,
                'mensaje': 'Error al actualizar la ciudad.',
                'error': str(e)
            }), 500
            
            
    if request.method == 'DELETE':
        try:
            data = request.get_json()
            if not data or 'id' not in data:
                return jsonify(success=False, mensaje='Se requiere un ID o lista de IDs de ciudad.'), 400

            ciudad_id = data['id']
            current_app.logger.debug(f'Recibido ID de ciudad para eliminar: {ciudad_id}')

            # Convert single ID to list for uniform handling
            ids_to_delete = [ciudad_id] if not isinstance(ciudad_id, list) else ciudad_id

            # Validate IDs are integers
            try:
                ids_to_delete = [int(id) for id in ids_to_delete]
            except (ValueError, TypeError):
                return jsonify(success=False, mensaje='IDs deben ser números enteros.'), 400

            # Get and delete cities in a single transaction
            ciudades = ciudadesModel.query.filter(ciudadesModel.id.in_(ids_to_delete)).all()
            
            if not ciudades:
                return jsonify(success=False, mensaje='No se encontraron ciudades con los IDs proporcionados.'), 404

            try:
                # Bulk delete operation
                delete_count = ciudadesModel.query.filter(ciudadesModel.id.in_(ids_to_delete)).delete()
                db.session.commit()
                
                return jsonify(
                    success=True,
                    mensaje=f'Se eliminaron {delete_count} ciudades exitosamente.',
                    eliminadas=ids_to_delete
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Error al eliminar ciudades: {str(e)}', exc_info=True)
                return jsonify(
                    success=False,
                    mensaje='Error al eliminar ciudades.',
                    errores=str(e)
                ), 500

        except Exception as error:
            current_app.logger.error(f'Error inesperado: {str(error)}', exc_info=True)
            return jsonify(
                success=False,
                mensaje='Error interno del servidor.'
            ), 500
            
    elif form.validate_on_submit():
        ciudad = {**form.data}
        # Eliminar campos no relacionados con el modelo antes de crear la ciudad
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id']:
            ciudad.pop(field, None)
        nueva_ciudad = ciudadesModel(**ciudad)
        try:
            nueva_ciudad.save()
            return jsonify(success=True, mensaje='Ciudad registrada exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al registrar ciudad: {e}')
            return jsonify(success=False, mensaje='Error al registrar la ciudad.', errores=str(e))

    elif form.errors:
 
        first_field, first_errors = next(iter(form.errors.items()))
        error_messages = f"{first_errors[0]}"
        # current_app.logger.debug(f'Errores en el formulario: {error_messages}')
        return jsonify(success=False, mensaje='Error al registrar la ciudad.', errores=error_messages)

    return render_template('ciudades.html', year=datetime.now().year, form=ciudadesForm(), User=current_user)

@ciudades_bp.route('/all', methods=['GET', 'POST'])
# @login_required
def all_ciudades():
    try:
        ciudades = ciudadesModel.query.all()

        ciudades_serialized = [ciudad.serialize() for ciudad in ciudades]


        
        response_data = {
            'success': True,
            'data': ciudades_serialized,
            'mensaje': 'Consulta exitosa'
        }
        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')
     
    except Exception as e:
        error = str(e)
        if 'not found' in error.lower():
            return jsonify(success=False, mensaje='No se encontraron ciudades.')
        elif 'database' in error.lower():
            return jsonify(success=False, mensaje='Error de base de datos.')
        elif 'connection' in error.lower():
            return jsonify(success=False, mensaje='Error de conexión a la base de datos.')
        elif 'timeout' in error.lower():
            return jsonify(success=False, mensaje='Tiempo de espera agotado al intentar acceder a la base de datos.')
        else:
            # current_app.logger.debug(f'Error desconocido: {error}')
            return jsonify(success=False, mensaje=error)

@ciudades_bp.route('/buscar', methods=['GET'])
def buscar_ciudad():
    termino = request.args.get('q', '', type=str)
    # current_app.logger.debug(f'Término de búsqueda recibido: {termino}')
    try:
        ciudades = ciudadesModel.query.filter(ciudadesModel.nombre.ilike(f'%{termino}%')).all()
        ciudades_serialized = [ciudad.data_selectize() for ciudad in ciudades]

        response_data = {
            'success': True,
            'data': ciudades_serialized,
            'mensaje': 'Consulta exitosa'
        }

        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')

    except Exception as e:
        error = str(e)
        current_app.logger.debug(f'Error al buscar ciudades: {error}')
        return jsonify(success=False, mensaje='Error al buscar ciudades.', errores=error), 500

@ciudades_bp.route('/origen', methods=['GET'])
def get_ciudad_origen():
    empresa_id = request.args.get('empresa', type=int)
    if not empresa_id:
        return jsonify(success=False, mensaje='ID de empresa inválido.')

    try:
        tarifas = tarifasModel.query.filter_by(empresa=empresa_id).all()

        if not tarifas:
            return jsonify(success=False, mensaje='No hay rutas para la empresa especificada.')

        ciudades = ciudadesModel.query.filter(ciudadesModel.id.in_([tarifa.origen for tarifa in tarifas if tarifa.origen])).all()


        data = [ciudad.serialize() for ciudad in ciudades]

        return jsonify(success=True, data=data, mensaje='Ciudad encontrada exitosamente.')
    
    except Exception as e:
        error = str(e)
        return jsonify(success=False, mensaje=f'Error al obtener la ciudad: {error}'), 500
    
@ciudades_bp.route('/destino', methods=['GET'])
def get_ciudad_destino():
    empresa_id = request.args.get('empresa', type=int)
    origen_id = request.args.get('origen', type=int)
    operador_id = request.args.get('operador', type=int)
    
    if not empresa_id or not origen_id:
        return jsonify(success=False, mensaje='ID de empresa o origen inválido.')

    try:
        tarifas = tarifasModel.query.filter_by(empresa=empresa_id, origen=origen_id).all()
        
        current_app.logger.debug(f'Tarifas encontradas: {tarifas}')

        ciudades = ciudadesModel.query.filter(ciudadesModel.id.in_([tarifa.destino for tarifa in tarifas if tarifa.destino])).all()

        data = [ciudad.serialize() for ciudad in ciudades]

        return jsonify(success=True, data=data, mensaje='Ciudad encontrada exitosamente.')
    
    except Exception as e:
        error = str(e)
        return jsonify(success=False, mensaje=f'Error al obtener la ciudad: {error}'), 500
    
#   VEHICULOS
@vehiculos_bp.route('/', methods=['GET', 'POST', 'DELETE', 'PUT'])
def vehiculos():
    form = vehiculosForm()
    if request.method == 'GET':
        
        vehiculos = vehiculosModel.query.filter_by(tipo='SEDAN').first()
        if not vehiculos:
            crear_sedan = vehiculosModel(tipo='SEDAN', codigo='SEDN')
            
            crear_sedan.save()
        
        return render_template('vehiculos.html', year=datetime.now().year, form=form, User=current_user, vehiculos=vehiculos)

    if request.method == 'PUT' and form.validate_on_submit():
        vehiculo_data = request.get_json()
        current_app.logger.debug(f'Recibido datos de vehiculo para actualizar: {vehiculo_data}')
       
        if not vehiculo_data or 'id' not in vehiculo_data:
            return jsonify(success=False, mensaje='Datos de vehiculo inválidos.')

        vehiculo_id = vehiculo_data.get('id')
        vehiculo = vehiculosModel.query.get(vehiculo_id)
        current_app.logger.debug(f'Vehiculo encontrado: {vehiculo.tipo}')

        if vehiculo.tipo == 'Sedan':
            return jsonify(success=False, errores='', mensaje="No se puede modificar vehiculo Sedan")

        if not vehiculo:
            return jsonify(success=False, mensaje='Vehiculo no encontrado.')
        # Eliminar campos no relacionados con el modelo antes de actualizar
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id']:
            vehiculo_data.pop(field, None)
            

        try:
            vehiculo.update(**vehiculo_data)
            return jsonify(success=True, mensaje='Vehiculo actualizado exitosamente.')

        except Exception as e:
            current_app.logger.debug(f'Error al actualizar vehiculo: {e}')
            return jsonify({
                'success': False,
                'mensaje': 'Error al actualizar la vehiculo.',
                'error': str(e)
            }), 500
            
            
    if request.method == 'DELETE':
            vehiculo_id = request.get_json().get('id')
            current_app.logger.debug(f'Recibido ID de vehiculo para eliminar: {vehiculo_id}')
            
            if not vehiculo_id:
                return jsonify(success=False, mensaje='ID de vehiculo inválido.')

            vehiculo = vehiculosModel.query.get(vehiculo_id)

            if vehiculo.tipo == 'Sedan':
                return jsonify(success=False, mensaje='No se puede eliminar vehiculo SEDAN')

            if not vehiculo:
                return jsonify(success=False, mensaje='Vehiculo no encontrado.')

            try:
                vehiculo.delete()
                return jsonify(success=True, mensaje='Vehiculo eliminada exitosamente.')

            except Exception as e:
                current_app.logger.debug(f'Error al eliminar vehiculo: {e}')
                return jsonify({
                    'success': False,
                    'mensaje': 'Error al eliminar la vehiculo.',
                    'errores': str(e)
                }), 500
            
    elif form.validate_on_submit():
        vehiculo = {**form.data}
        # Eliminar campos no relacionados con el modelo antes de crear la vehiculo
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id']:
            vehiculo.pop(field, None)
        nueva_ciudad = vehiculosModel(**vehiculo)
        try:
            nueva_ciudad.save()
            return jsonify(success=True, mensaje='Ciudad registrada exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al registrar vehiculo: {e}')
            return jsonify(success=False, mensaje='Error al registrar la vehiculo.', errores=str(e))

    elif form.errors:
 
        first_field, first_errors = next(iter(form.errors.items()))
        error_messages = f"{first_errors[0]}"
        # current_app.logger.debug(f'Errores en el formulario: {error_messages}')
        return jsonify(success=False, mensaje='Error al registrar la vehiculo.', errores=error_messages)

    
    

@vehiculos_bp.route('/all', methods=['GET', 'POST'])
# @login_required
def all_vehiculos():
    try:
        vehiculos = vehiculosModel.query.all()

        vehiculos_serialized = [vehiculo.serialize() for vehiculo in vehiculos]

        response_data = {
            'success': True,
            'data': vehiculos_serialized,
            'mensaje': 'Consulta exitosa'
        }

        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')

    except Exception as e:
        error = str(e)
        if 'not found' in error.lower():
            return jsonify(success=False, mensaje='No se encontraron vehículos.')
        elif 'database' in error.lower():
            return jsonify(success=False, mensaje='Error de base de datos.')
        elif 'connection' in error.lower():
            return jsonify(success=False, mensaje='Error de conexión a la base de datos.')
        elif 'timeout' in error.lower():
            return jsonify(success=False, mensaje='Tiempo de espera agotado al intentar acceder a la base de datos.')
        else:
            current_app.logger.debug(f'Error desconocido: {error}')
            return jsonify(success=False, mensaje=error)

# TASA DE CAMBIO

@tasa_bp.route('/', methods=['GET', 'PUT'])
def tasa():
    form = tasaForm()
    API_URL = "https://ve.dolarapi.com/v1/dolares"
    
    if request.method == 'GET':
        try:
            response = requests.get(API_URL)
            
            if response.status_code == 200:
                
                data = response.json()
                tasa_bcv = data[0]['promedio']
                fecha_bcv = data[0]['fechaActualizacion']
                fecha_bcv = fecha_bcv.split("T")[0]
                split_fecha = fecha_bcv.split("-")
                fecha_bcv = f"{split_fecha[2]}-{split_fecha[1]}-{split_fecha[0]}"
        
                form.tasa.data = tasa_bcv
               

            else:
                tasa_bcv = "Error al obtener datos"
                fecha_bcv = "Error al obtener datos"
        except Exception as e:
            current_app.logger.error(f'Error al consultar tarifas BCV: {e}')
            tasa_bcv = "Error al obtener datos"
            fecha_bcv = "Error de conexión"
        finally:
            current_app.logger.debug(f'Tasa BCV: {tasa_bcv}, Fecha BCV: {fecha_bcv}')
        
        data = tasaModel.query.order_by(tasaModel.id.desc()).first()
        
        if not data:
            set_tasa = tasaModel(
                    tasa=tasa_bcv,
                )
            set_tasa.save()
        else:
            tasa_actual = data.tasa
            fecha_actual = data.fecha.strftime('%d-%m-%Y %H:%M:%S')

    if request.method == 'PUT' and form.validate_on_submit():
        set_tasa = tasaModel(
            tasa=form.tasa.data
        )
        form.tasa.data = None
        set_tasa.save()
        return jsonify(success=True, mensaje='Tasa actualizada exitosamente.')

    return render_template(
        'tasa.html',
        year=datetime.now().year,
        form=form,
        User=current_user,
        tasa=tasa_actual,
        fecha=fecha_actual,
        tasa_bcv=tasa_bcv,
        fecha_bcv=fecha_bcv
    )



@tasa_bp.route('/all', methods=['GET'])
def all_tasa():
    try:
        tasas = tasaModel.query.all()
        tasa_data = [tasa.serialize() for tasa in tasas]
        
        response_data = {
            'success': True,
            'data': tasa_data,
            'mensaje': 'Consulta exitosa'
        }

        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')
    except Exception as e:
        current_app.logger.debug(f'Error al obtener tasas: {e}')
        return jsonify(success=False, mensaje='Error al obtener las tasas.', errores=str(e))
    
