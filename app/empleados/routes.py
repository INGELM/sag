def _normalize_decimal(value):
    """Permite ingresar 8,5 o 8.5 y lo convierte a float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(',', '.').strip()
    return float(cleaned) if cleaned else None


from flask import Response, current_app, flash, json, jsonify, redirect, render_template, request, session, url_for
from flask_login import login_required, current_user
from app.empleados.models import empleadosModel, tarifasOperadoresModel
from app.clientes.models import tarifasModel, clientesModel
from app.auxiliares.models import ciudadesModel, vehiculosModel
from . import empleados_bp
from .form import *
from app.login.form import LoginForm
from datetime import datetime
from app.extensions import db
from functools import wraps
from sqlalchemy.orm import aliased



@empleados_bp.before_request
def before_request():
    if not current_user.is_authenticated:
        flash('Por favor, inicie sesión para acceder a esa página.', 'warning')
        return redirect(url_for('login.login'))

@empleados_bp.route('/', methods=['GET', 'POST', 'DELETE', 'PUT'])
@login_required
def empleados():
    form = empleadosForm()
    empleado_data = {**form.data}

    if request.method == 'PUT' and form.validate_on_submit():
        if not current_user.is_admin:
            # current_app.logger.debug("Solicitud PUT recibida.")
            return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.")
        # empleado_data = request.get_json()
        current_app.logger.debug(f'Recibido datos de empleado para actualizar: {empleado_data}')
        if not empleado_data or 'id' not in empleado_data:
            return jsonify(success=False, mensaje='Datos de empleado inválidos.')

        empleado_id = empleado_data.get('id')
        empleado = empleadosModel.query.get(empleado_id)

        if not empleado:
            return jsonify(success=False, mensaje='Empleado no encontrado.')
        # Eliminar campos no relacionados con el modelo antes de actualizar
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id']:
            empleado_data.pop(field, None)

        if not form.contrasena.data:
            # Mantener la contraseña actual si no se proporciona una nueva
            empleado_data['contrasena'] = empleado.contrasena
            
         # Convertir campos tipo <empleadosModel ...> a su id
        for key, value in empleado_data.items():
            if hasattr(value, 'id'):
                empleado_data[key] = value.id

        try:
            empleado.update(**empleado_data)
            return jsonify(success=True, mensaje='Empleado actualizado exitosamente.')

        except Exception as e:
            current_app.logger.debug(f'Error al actualizar empleado: {e}')
            return jsonify({
                'success': False,
                'mensaje': "No se pudo actualizar el empleado.",
                'errores': str(e)
            }), 500

    if request.method == 'DELETE':
        if not current_user.is_admin:
            # current_app.logger.debug("Solicitud PUT recibida.")
            return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.")

        empleado_id = request.get_json().get('id')
        current_app.logger.debug(f'Recibido ID de empleado para eliminar: {empleado_id}')
        if not empleado_id:
            return jsonify(success=False, mensaje='ID de empleado inválido.')

        empleado = empleadosModel.query.get(empleado_id)

        if not empleado:
            return jsonify(success=False, mensaje='Empleado no encontrado.')

        try:
            empleado.delete()
            return jsonify(success=True, mensaje='Empleado eliminado exitosamente.')

        except Exception as e:
            if '1452' in str(e).lower() or 'foreign key constraint fails' in str(e).lower():
                mensaje = 'No se puede eliminar el empleado porque tiene registros relacionados.'
            else:
                mensaje = 'Error al eliminar el empleado.'

            return jsonify({
                'success': False,
                'mensaje': mensaje,
                'error': str(e)
            }), 500

    elif form.validate_on_submit():
        empleado = {**form.data}
        # Eliminar campos no relacionados con el modelo antes de crear el empleado
        for field in ['csrf_token', 'validar_contrasena', 'submit', 'id', 'origen', 'destino', 'desplazamiento']:
            empleado.pop(field, None)
        nuevo_empleado = empleadosModel(**empleado)
        try:
            nuevo_empleado.save()
            return jsonify(success=True, mensaje='Empleado registrado exitosamente.')
        except Exception as e:
            # current_app.logger.debug(f'Error al registrar empleado: {e}')
            return jsonify(success=False, mensaje='Error al registrar el empleado.', errores=str(e))

    elif form.errors:

        first_field, first_errors = next(iter(form.errors.items()))
        error_messages = f"{first_errors[0]}"
        # current_app.logger.debug(f'Errores en el formulario: {error_messages}')
        return jsonify(success=False, mensaje='Error al registrar el empleado.', errores=error_messages)

    return render_template('empleados.html', year=datetime.now().year, form=empleadosForm(), User=current_user)

@empleados_bp.route('/get_data/<int:id>', methods=['GET'])
@login_required
def get_empleado_data(id):
    try:
        empleado = empleadosModel.query.get(id)
        if not empleado:
            return jsonify(success=False, mensaje='Empleado no encontrado.')

        empleado_data = empleado.serialize_form()
        return jsonify(success=True, data=empleado_data, mensaje='Datos del empleado obtenidos exitosamente.')

    except Exception as e:
        current_app.logger.error(f'Error al obtener datos del empleado: {str(e)}', exc_info=True)
        return jsonify(success=False, mensaje='Error al obtener datos del empleado.', error=str(e))



@empleados_bp.route('/all', methods=['GET'])
@login_required
# @login_required
def all_empleados():
    try:
        if current_user.is_admin:
            empleados = empleadosModel.query.all()
            current_app.logger.debug("todos los empleados")
        else:
            empleados = empleadosModel.query.filter_by(
                usuario=current_user.usuario).all()

            current_app.logger.debug("empleados del usuario", empleados)

        empleados_serialized = [e.serialize() for e in empleados]

        if not empleados_serialized:
            raise ValueError("No se encontraron empleados.")

        response_data = {
            'success': True,
            'data': empleados_serialized,
            'mensaje': 'Consulta exitosa'
        }
        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')

    except Exception as e:
        error = str(e)
        if 'not found' in error.lower():
            return jsonify(success=False, mensaje='No se encontraron empleados.')
        elif 'database' in error.lower():
            return jsonify(success=False, mensaje='Error de base de datos.')
        elif 'connection' in error.lower():
            return jsonify(success=False, mensaje='Error de conexión a la base de datos.')
        elif 'timeout' in error.lower():
            return jsonify(success=False, mensaje='Tiempo de espera agotado al intentar acceder a la base de datos.')
        else:
            current_app.logger.error(f'Error desconocido: {error}', exc_info=True)
            return jsonify(success=False, mensaje=error)


@empleados_bp.route('/tarifasOperadores/get_data/<int:id>', methods=['GET'])
@login_required
def get_tarifa_operador_data(id):
    try:
        tarifa = tarifasOperadoresModel.query.get(id)
        if not tarifa:
            return jsonify(success=False, mensaje='Tarifa no encontrada.')

        tarifa_data = tarifa.serialize_form()
        return jsonify(success=True, data=tarifa_data, mensaje='Datos de la tarifa obtenidos exitosamente.')

    except Exception as e:
        current_app.logger.error(f'Error al obtener datos de la tarifa: {str(e)}', exc_info=True)
        return jsonify(success=False, mensaje='Error al obtener datos de la tarifa.', error=str(e))

    

@empleados_bp.route('/tarifasOperadores/get_data', methods=['GET'])
@login_required
def get_tarifas_operador_server_data():
    """Endpoint server-side para DataTables de tarifas de operadores."""
    try:
        draw = int(request.args.get('draw', 1))
        start = int(request.args.get('start', 0))
        length = int(request.args.get('length', 10))
        search_value = request.args.get('search[value]', '')
        empresa_id = request.args.get('empresa', type=int)

        origen_alias = aliased(ciudadesModel)
        destino_alias = aliased(ciudadesModel)

        base_query = (
            tarifasOperadoresModel.query
            .join(tarifasOperadoresModel.codigo_rel)
            .join(clientesModel, tarifasModel.empresa == clientesModel.id)
            .join(origen_alias, tarifasModel.origen_rel.of_type(origen_alias))
            .join(destino_alias, tarifasModel.destino_rel.of_type(destino_alias))
            .join(vehiculosModel, tarifasModel.vehiculo == vehiculosModel.id, isouter=True)
        )

        query = base_query
        if empresa_id:
            query = query.filter(tarifasModel.empresa == empresa_id)

        total_base_query = base_query
        if empresa_id:
            total_base_query = total_base_query.filter(tarifasModel.empresa == empresa_id)
        records_total = total_base_query.count()

        if search_value:
            words = [w.strip() for w in search_value.split() if w.strip()]
            for word in words:
                like = f"%{word}%"
                query = query.filter(
                    (tarifasModel.codigo.ilike(like)) |
                    (clientesModel.empresa.ilike(like)) |
                    (origen_alias.nombre.ilike(like)) |
                    (destino_alias.nombre.ilike(like)) |
                    (vehiculosModel.tipo.ilike(like)) |
                    (tarifasModel.desplazamiento.ilike(like)) |
                    (tarifasOperadoresModel.tipo.ilike(like))
                )

        records_filtered = query.count()

        order_column = request.args.get('order[0][column]')
        order_dir = request.args.get('order[0][dir]', 'asc')
        if order_column is not None:
            col_name = request.args.get(f'columns[{order_column}][data]')
            column_map = {
                'id': tarifasOperadoresModel.id,
                'codigo': tarifasModel.codigo,
                'empresa': clientesModel.empresa,
                'origen': origen_alias.nombre,
                'destino': destino_alias.nombre,
                'vehiculo': vehiculosModel.tipo,
                'desplazamiento': tarifasModel.desplazamiento,
                'tipo': tarifasOperadoresModel.tipo,
                'espera': tarifasOperadoresModel.espera,
                'desvios': tarifasOperadoresModel.desvios,
                'base': tarifasOperadoresModel.base,
            }
            if col_name in column_map:
                sort_attr = column_map[col_name]
                query = query.order_by(sort_attr.desc() if order_dir == 'desc' else sort_attr.asc())

        data_page = query.offset(start).limit(length).all()
        data_serialized = [t.serialize() for t in data_page]

        return jsonify({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data_serialized
        })

    except Exception as e:
        current_app.logger.error(f'Error en server-side tarifas operadores: {e}')
        return jsonify(success=False, mensaje='Error al obtener tarifas de operadores.', errores=str(e))



@empleados_bp.route('/tarifasOperadores/all', methods=['GET'])
@empleados_bp.route('/get/tarifasOperadores', methods=['GET'])
@login_required
def get_tarifas_operador():
    id = request.args.get('empresa', type=int)
    codigo = request.args.get('codigo', type=int)

    try:
        if not id and not codigo:
            tarifas = tarifasOperadoresModel.query.all()
            tarifas_serialized = [t.serialize() for t in tarifas]
        elif codigo:
            tarifas = tarifasOperadoresModel.query.filter(tarifasOperadoresModel.codigo==codigo).first()
            if not tarifas:
                raise ValueError("No se encontraron tarifas para el código proporcionado.")
            tarifas_serialized = [tarifas.serialize()] if tarifas else []
        else:
            tarifas = tarifasOperadoresModel.query.filter_by(id=id).all()
            tarifas_serialized = [t.serialize() for t in tarifas]

        # if codigo:
        #     tarifas = tarifasOperadoresModel.query.filter_by(codigo=codigo).all()

        # current_app.logger.debug(f'Tarifas obtenidas: {tarifas}')

        # tarifas_serialized = [t.serialize() for t in tarifas]
        
        response_data = {
            'success': True,
            'data': tarifas_serialized,
            'mensaje': 'Consulta exitosa'
        }
        return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')

    except Exception as e:
        return jsonify(success=False, mensaje='Error al obtener tarifas de operadores.', error=str(e))


@empleados_bp.route('/tarifasOperadores', methods=['GET'])
@login_required
def tarifas_operador():
    form = tarifasOperadoresForm()

    return render_template('tarifas-operadores.html', year=datetime.now().year, form=form, User=current_user)


@empleados_bp.route('/tarifasOperadores', methods=['POST', 'DELETE', 'PUT'])
@login_required
def tarifas_operadores():
    form = tarifasOperadoresForm()

    current_app.logger.debug(f'Datos recibidos para registrar tarifa: {form.data}')

    if request.method == 'POST' and form.validate_on_submit():
        # Procesar los datos del formulario
        tarifa_data = {**form.data}
        # Eliminar campos no relacionados con el modelo antes de crear la tarifa
        for field in ['csrf_token', 'submit', 'id', 'empresa', 'origen', 'destino', 'desplazamiento']:
            tarifa_data.pop(field, None)

        # Normalizar decimales para que acepten coma o punto
        for field in ['desvios', 'espera', 'base']:
            tarifa_data[field] = _normalize_decimal(tarifa_data.get(field))

        nueva_tarifa = tarifasOperadoresModel(**tarifa_data)
        try:
            nueva_tarifa.save()
            return jsonify(success=True, mensaje='Tarifa registrada exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al registrar tarifa: {e}')
            return jsonify(success=False, mensaje='Error al registrar la tarifa.', errores=str(e))

    elif request.method == 'DELETE':
        tarifa_id = request.get_json().get('id')
        current_app.logger.debug(f'Recibido ID de tarifa para eliminar: {tarifa_id}')
        if not tarifa_id:
            return jsonify(success=False, mensaje='ID de tarifa inválido.')

        tarifa = tarifasOperadoresModel.query.get(tarifa_id)

        if not tarifa:
            return jsonify(success=False, mensaje='Tarifa no encontrada.')

        try:
            tarifa.delete()
            return jsonify(success=True, mensaje='Tarifa eliminada exitosamente.')

        except Exception as e:
            
            if '1452' in str(e).lower():
                mensaje = 'No se puede eliminar la tarifa porque tiene registros relacionados.'

            return jsonify(success=False, mensaje="Operación Invalida", errores=mensaje)

    elif request.method == 'PUT' and form.validate_on_submit():
        request_data = request.get_json()
        current_app.logger.debug(f'Recibido datos de tarifa para actualizar: {request_data}')

        tarifa_id = request_data.get('id')
        if not tarifa_id:
            return jsonify(success=False, mensaje='ID de tarifa inválido.')

        tarifa = tarifasOperadoresModel.query.get(tarifa_id)
        if not tarifa:
            return jsonify(success=False, mensaje='Tarifa no encontrada.')
        
        # Eliminar campos no relacionados con el modelo antes de actualizar
        for field in ['csrf_token', 'submit', 'id']:
            request_data.pop(field, None)

        # Normalizar decimales para que acepten coma o punto
        for field in ['desvios', 'espera', 'base']:
            if field in request_data:
                request_data[field] = _normalize_decimal(request_data.get(field))

        # Actualizar los campos de la tarifa con los nuevos datos
        for key, value in request_data.items():
            setattr(tarifa, key, value)

        try:
            tarifa.update()
            return jsonify(success=True, mensaje='Tarifa actualizada exitosamente.')
        except Exception as e:
            current_app.logger.debug(f'Error al actualizar tarifa: {e}')
            return jsonify(success=False, mensaje='Error al actualizar la tarifa.', errores=str(e))

    elif form.errors:
        first_field, first_errors = next(iter(form.errors.items()))
        current_app.logger.debug(f'Errores en el formulario: {first_field} : {first_errors}')
        return jsonify(success=False, mensaje='Error de validación.', errores=f'{first_field} : {first_errors}')

