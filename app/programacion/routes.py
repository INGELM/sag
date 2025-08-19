from flask import Response, json, redirect, request, url_for, render_template, jsonify, flash, current_app
from flask_login import current_user, login_required
from app.clientes.models import tarifasModel
from app.empleados.models import empleadosModel, tarifasOperadoresModel
from app.facturacion.models import facturasClientesModel
from app.facturacion.routes import crear_factura_cliente, crear_pago_operador
from app.programacion import programacion_bp
from app.programacion.form import programacionForm
from datetime import datetime
from app.extensions import db

from app.programacion.models import programacionModel

@programacion_bp.before_request
def before_request():
    # current_app.logger.debug("Usuario autenticado: %s", current_user.is_authenticated)
    if not current_user.is_authenticated:
        flash('Por favor, inicie sesión para acceder a esa página.', 'warning')
        return redirect(url_for('login.login'))
    
    # if request.method == 'DELETE':
    #     if not current_user.is_admin:
    #         # flash('No tienes permiso para realizar esta acción.', 'danger')
    #         raise PermissionError('No tienes permiso para realizar esta acción.')

@staticmethod
def validar_coherencias(form):
    if form.vehiculo.data is None:
        raise ValueError('El vehículo es obligatorio.')
    
    desplazamiento = "ida" if not form.retorno.data else "idav"
    if 6 <= form.hora_salida.data.hour < 18:
       horario =  "D"
    else:
       horario =  "E"

    codigo_tarifa = f"{form.empresa.data.codigo}{form.origen.data.codigo}{form.destino.data.codigo}-{form.vehiculo.data.codigo}-{desplazamiento}-{horario}".upper()
    # current_app.logger.debug("Código de tarifa generado:", codigo_tarifa)
    
    tarifa_base = tarifasModel.query.filter_by(codigo_desc=codigo_tarifa).first()
    
    if not tarifa_base:
        raise ValueError('No existe una tarifa base para la combinación del servicio seleccionado ({}).'.format(codigo_tarifa))

    if form.operador.data:
        tipo_operador = form.operador.data.tipo
        tarifa_operador = tarifasOperadoresModel.query.filter_by(
            codigo=tarifa_base.id,  # Relación con tarifa_base
            tipo=tipo_operador
        ).first()
        
        if not tarifa_operador:
            raise ValueError(f'No hay tarifas definidas para el tipo de operador: {tipo_operador} en esta ruta.')

    # Validar que el operador tenga tarifas definidas
    if form.operador.data:
        # current_app.logger.debug("Operador seleccionado:", form.operador.data, "Tipo:", form.operador.data.tipo)

        tipo_operador = form.operador.data.tipo

        tarifas_operadores_tipo = tarifasOperadoresModel.query.filter_by(tipo=tipo_operador).first()

        if not tarifas_operadores_tipo:
            raise ValueError(f'No hay tarifas definidas para el tipo de operador: {tipo_operador}.')

    #guia repetida
    if form.guia.data and form.id.data is None:
        guia_existente = programacionModel.query.filter_by(guia=form.guia.data).first()
        if guia_existente:
            raise ValueError('La guía ya está registrada en otra programación.')
    
    # Validar hora de retorno mayor a hora de salida
    if form.hora_retorno.data and form.hora_retorno.data <= form.hora_salida.data:
        raise ValueError(
            'La hora de retorno debe ser mayor a la hora de salida.')

    if form.retorno.data:
        if not form.hora_retorno.data:
            raise ValueError(
                'La hora de retorno es obligatoria cuando se selecciona retorno.')

    # Validar que la distancia sea un número positivo
    if form.distancia.data is not None and form.distancia.data < 0:
        raise ValueError('La distancia debe ser un número positivo.')

    # Validar que el tiempo de espera sea un número positivo
    if form.tiempo_espera.data is not None and form.tiempo_espera.data < 0:
        raise ValueError('El tiempo de espera debe ser un número positivo.')

    if form.desvios.data is not None and form.desvios.data < 0:
        raise ValueError('Los desvíos deben ser un número positivo.')

    if form.status.data == 'Programado' and (not form.operador.data or not form.vehiculo.data):
        raise ValueError(
            'El operador y el vehículo son obligatorios cuando el estado es Programado.')

    # fecha_salida = form.fecha_salida.data
    # hoy = datetime.now().date()
    # if form.status.data in ['Programado', 'Pendiente']:
    #     if fecha_salida and fecha_salida < hoy:
    #         raise ValueError(
    #             'La fecha de salida no puede ser menor que la fecha actual, para un viaje programado o pendiente.')

    # if form.status.data == 'Finalizado':
    #     if fecha_salida and fecha_salida > hoy:
    #         raise ValueError(
    #             'La fecha de salida no puede ser mayor que la fecha actual cuando el estado es "Finalizado".')

    # hora_salida = form.hora_salida.data
    # ahora = datetime.now()
    # if hora_salida and fecha_salida == hoy and form.status.data != 'Finalizado':
    #     if hora_salida < ahora.time():
    #         raise ValueError(
    #             'La hora de salida no puede ser menor que la hora actual, cuando el estado no es "Finalizado".')

    # if form.status.data == 'Finalizado':
    #     if hora_salida and hora_salida > ahora.time() and fecha_salida == hoy:
    #         raise ValueError(
    #             'La hora de salida no puede ser mayor que la hora actual cuando el estado es "Finalizado".')
    
    if form.status.data == 'Finalizado' and not form.guia.data:
        raise ValueError('La guía es obligatoria para finalizar un viaje.')


@programacion_bp.route('/get_data/<int:id>', methods=['GET'])
@login_required
def get_data_by_id(id):
    data = programacionModel.query.get(id)
    
    if not data:
        return jsonify(success=False, mensaje='No se encontró la programación.'), 404
    

    
    response = data.serialize_form() if data else None



    return jsonify(success=True, data=response, mensaje='Programación obtenida exitosamente.')

@programacion_bp.route('/get_data', methods=['GET'])
@login_required
def get_data():
    filtro = request.args.get('filtro', None)
    if not filtro:
        data = programacionModel.query.all()
    else:
        data = programacionModel.query.filter_by(status=filtro).all()
    data_serializada = [d.serialize() for d in data]
    # current_app.logger.debug("Datos serializados:", data_serializada)
    return jsonify(data=data_serializada)

@programacion_bp.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def programacion():
    form = programacionForm()
    dataForm = form.data
    programacion_data = {**form.data}
    print("Datos de la programación:---------------------------", programacion_data)
    if request.method == 'GET':
        return render_template('/programacion.html', User=current_user, form=form)

    elif request.method == 'POST' and form.validate_on_submit():
        
        
        print("Datos del formulario:", programacion_data)

        try:
            # Validar coherencias antes de guardar
            validar_coherencias(form)
        except ValueError as e:
            # current_app.logger.debug("Error de validación:", str(e))
            return jsonify(success=False, mensaje='Error de validación.', errores=str(e))

        # Eliminar campos que no son necesarios para el procesamiento
        for field in ['csrf_token', 'submit', 'id', 'empresa', 'pasajeros']:
            programacion_data.pop(field, None)
        
        # programacion_data['direccion_origen'] = json.dumps(form.direccion_origen.data) if form.direccion_origen.data else None
        current_app.logger.debug("Datos de la programación DIRECCION ORIGEN", programacion_data['direccion_origen'])

        nueva_programacion = programacionModel(**programacion_data)
        
        nueva_programacion.pasajeros = form.pasajeros.data if form.pasajeros.data else []


        # current_app.logger.debug("Datos de la nueva programación:", {nueva_programacion})
        
        if form.status.data == 'Finalizado':
            nueva_factura = crear_factura_cliente(form)
            
            
            
            programacion = nueva_programacion.save()
            # current_app.logger.debug("Programación guardada:", programacion)
            
            nueva_factura['programacion'] = programacion.id
            
        
            try:
                crear_factura = facturasClientesModel(**nueva_factura)
                db.session.add(crear_factura)
                db.session.commit()
                # current_app.logger.debug("Factura del cliente creada:", crear_factura)
                crear_pago_operador(form)
                return jsonify(success=True, mensaje='Programación Finalizada y Factura Generada correctamente.')

            except Exception as e:
                db.session.rollback()
                # current_app.logger.error(f"Error al crear la factura del cliente: {str(e)}")
                return jsonify(success=False, mensaje='Error al crear la factura del cliente.')
        else:
            try:
                # current_app.logger.debug("Guardando nueva programación:", nueva_programacion)
                nueva_programacion.save()
                # current_app.logger.debug("Programación guardada:", nueva_programacion)
                return jsonify(success=True, mensaje='Programación guardada correctamente.')
            except Exception as e:
                db.session.rollback()
                # current_app.logger.error(f"Error al guardar la programación: {str(e)}")
                return jsonify(success=False, mensaje='Error al guardar la programación.', errores=str(e))
        
        
        
    elif request.method == 'PUT' and form.validate_on_submit():
        if not current_user.is_admin:
            return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.")
        
        factura_existing = facturasClientesModel.query.filter_by(programacion=form.id.data).first()
        if factura_existing:
            # current_app.logger.debug("Factura existente encontrada para la programación:", factura_existing)
            return jsonify(success=False, errores='No se puede actualizar la programación. Elimine primero las facturas asociadas.', mensaje='Factura existente.')

        # programacion_data = {**form.data}
        print("Datos del formulario para actualizar:", programacion_data)

        
        id_programacion = programacion_data.get('id')

        if not id_programacion:
            return jsonify(success=False, mensaje='ID de programación no proporcionado.')

        try:
            # Validar coherencias antes de actualizar
            validar_coherencias(form)
        except ValueError as e:
            # current_app.logger.debug("Error de validación:", e)
            return jsonify(success=False, mensaje='Error de validación.', errores=str(e))
        
        programacion = programacionModel.query.get(id_programacion)
        
        if not programacion:
            return jsonify(success=False, mensaje='Programación no encontrada.')
        
        # Eliminar campos que no son necesarios para el procesamiento
        for field in ['csrf_token', 'submit', 'empresa', 'pasajeros']:
            programacion_data.pop(field, None)
            
        # Convertir campos tipo <empleadosModel ...> a su id
        for key, value in programacion_data.items():
            if hasattr(value, 'id'):
                programacion_data[key] = value.id
                
        # programacion_data['direccion_origen'] = json.dumps(form.direccion_origen.data) if form.direccion_origen.data else None
        
        try:
            db.session.query(programacionModel).filter_by(id=id_programacion).update(programacion_data)
            # Limpiar la relación de pasajeros antes de asignar los nuevos
            programacion.pasajeros = []
            db.session.commit()
            # Asignar los nuevos pasajeros si existen
            if form.pasajeros.data:

                programacion.pasajeros = form.pasajeros.data
            
            db.session.add(programacion)
            db.session.commit()
            mensaje = 'Programación actualizada correctamente.'
            if form.status.data == 'Finalizado':
                nueva_factura = crear_factura_cliente(form)
                nueva_factura['programacion'] = programacion.id
                
                try:
                    crear_factura = facturasClientesModel(**nueva_factura)
                    db.session.add(crear_factura)
                    db.session.commit()
                    mensaje = 'Programación Finalizada y Factura Generada correctamente.'
                    crear_pago_operador(form)
                    mensaje = 'Programación Finalizada, Factura de Cliente y Pago Operador Generados correctamente.'
                    # current_app.logger.debug("Factura del cliente creada:", crear_factura)
                except Exception as e:
                    db.session.rollback()
                    print("----------------error: ------------------", e)
                    # current_app.logger.error(f"Error al crear la factura del cliente: {str(e)}")
                    raise ValueError('Error al crear la factura del cliente.')

            return jsonify(success=True, mensaje=mensaje)

        except Exception as e:
            db.session.rollback()
            # current_app.logger.error(f"Error al actualizar la programación: {str(e)}")
            return jsonify(success=False, errores=str(e), mensaje='Error al actualizar la programación.')

    elif request.method == 'DELETE':
        if not current_user.is_admin:
            # current_app.logger.debug("Solicitud DELETE recibida.")
            return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.')

        id_programacion = request.json.get('id')
        # current_app.logger.debug("ID de programación a eliminar:", id_programacion)

        if not id_programacion:
            return jsonify(success=False, mensaje='ID de programación no proporcionado.')

        programacion = programacionModel.query.filter(programacionModel.id.in_(id_programacion)).all()
        if not programacion:
            return jsonify(success=False, mensaje='Programación no encontrada.')

        try:
            for item in programacion:
                db.session.delete(item)
            db.session.commit()
            return jsonify(success=True, mensaje='Programación eliminada correctamente.')

        except Exception as e:
            db.session.rollback()
            # current_app.logger.debug("Error al eliminar la programación:", e)
            return jsonify(success=False, mensaje='No se puede eliminar la programación. Elimine primero las facturas asociadas.', error=str(e))

    elif form.errors:
        # current_app.logger.debug("Errores de validación:", form.errors)
        primer_error = next(iter(form.errors.values()))[0] if form.errors else 'Error desconocido.'
        return jsonify(success=False, mensaje='Error en el formulario.', errores=primer_error)

    
@programacion_bp.route('/all', methods=['GET'])
def get_all_programaciones():
    programaciones = programacionModel.query.all()
    response_data = {
        'success': True,
        'mensaje': 'Programaciones obtenidas exitosamente.',
        'data': [programacion.serialize() for programacion in programaciones]
    }
    return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')



@programacion_bp.route('/get/direcciones', methods=['GET'])
def get_direcciones():
    tipo = request.args.get('tipo', None)
    pasajeros_seleccionados = request.args.getlist('pasajeros[]')
    pasajeros_seleccionados = [int(p) for p in pasajeros_seleccionados if p.isdigit()]
    # pasajeros_seleccionados = [1]
    print("Pasajeros seleccionados:", pasajeros_seleccionados)
    # Filtrar direcciones para los pasajeros_seleccionados
    
    from app.clientes.models import pasajerosModel
    
    if tipo == 'origen':
        direcciones = programacionModel.query.\
            with_entities(programacionModel.direccion_origen).\
            join(programacionModel.pasajeros).\
            filter(pasajerosModel.id.in_(pasajeros_seleccionados)).\
            distinct().all()

    elif tipo == 'destino':
        direcciones = programacionModel.query.\
            with_entities(programacionModel.direccion_destino).\
            join(programacionModel.pasajeros).\
            filter(pasajerosModel.id.in_(pasajeros_seleccionados)).\
            distinct().all()

    data = [d[0] for d in direcciones if d[0]]
    
    # Separar direcciones múltiples en cada registro y aplanar la lista
    direcciones_separadas = []
    for direccion in data:
        if isinstance(direccion, str):
            partes = [d.strip() for d in direccion.split(',') if d.strip()]
            direcciones_separadas.extend(partes)
        elif isinstance(direccion, list):
            direcciones_separadas.extend([d.strip() for d in direccion if d.strip()])
        else:
            continue
    # Eliminar duplicados y mantener el orden
    data = list(dict.fromkeys(direcciones_separadas))

    opciones_selectize = [{'value': d, 'text': d} for d in data]

    if not data:
        return jsonify(success=False, mensaje='No se encontraron direcciones.', data=[])
    # current_app.logger.debug("Direcciones obtenidas:", direcciones)

    return jsonify(success=True, data=opciones_selectize, mensaje='Direcciones obtenidas exitosamente.')