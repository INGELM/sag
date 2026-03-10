from time import strftime
from flask import Response, json, redirect, request, url_for, render_template, jsonify, flash, current_app
from flask_login import current_user, login_required
from app.auxiliares.models import ciudadesModel, vehiculosModel
from app.clientes.models import clientesModel, pasajerosModel, tarifasModel
from app.empleados.models import empleadosModel, tarifasOperadoresModel
from app.facturacion.models import facturasClientesModel, pagosOperadoresModel
from app.facturacion.routes import crear_factura_cliente, crear_pago_operador
from app.helpers.logger_utils import format_error_simple, log_action, registrar_log
from app.programacion import programacion_bp
from app.programacion.form import programacionForm
from datetime import datetime
from app.extensions import db
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

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
    
    if not tarifa_base and form.status.data == 'Finalizado':
        raise ValueError('No existe una tarifa base para la combinación del servicio seleccionado')
    
    if not form.operador.data and form.status.data == 'Finalizado':
        raise ValueError('El operador es obligatorio para finalizar un viaje.')

    # if form.operador.data and form.status.data == 'Finalizado':
    #     tipo_operador = form.operador.data.tipo
    #     tarifa_operador = tarifasOperadoresModel.query.filter_by(
    #         codigo=tarifa_base.id,  # Relación con tarifa_base
    #         tipo=tipo_operador
    #     ).first()
    #     current_app.logger.debug("Tarifa operador encontrada:", tarifa_operador)
    #     if not tarifa_operador:
    #         raise ValueError(f'No hay tarifas definidas para el tipo de operador: {tipo_operador} en esta ruta.')

    # Validar que el operador tenga tarifas definidas
    if form.operador.data:
        current_app.logger.debug("Operador seleccionado:", form.operador.data, "Tipo:", form.operador.data.tipo)

        tipo_operador = form.operador.data.tipo

        tarifas_operadores_tipo = tarifasOperadoresModel.query.filter_by(tipo=tipo_operador).first()
        # current_app.logger.debug("Tarifas operadores para tipo:", tipo_operador)

        if not tarifas_operadores_tipo and form.status.data == 'Finalizado':
            raise ValueError(f'No hay tarifas definidas en la ruta seleccionada para el operador: {form.operador.data.nombres} ({tipo_operador}).')

    #guia repetida
    if form.guia.data:
        query = programacionModel.query.filter_by(guia=form.guia.data)
        
        if form.id.data:
            query = query.filter(programacionModel.id != form.id.data)
        
        guia_existente = query.first()
        registrar_log("VALIDAR GUIA", "PROGRAMACION",f'Validando guía repetida: {form.guia.data} ==> {guia_existente.guia if guia_existente else "No existe"}')
        if guia_existente:
            raise ValueError(f'La guía {form.guia.data} ya está registrada en otra programación.')
    
    # WorkFlow repetido
    if form.workflow.data:
        registrar_log("VALIDAR WORKFLOW", "PROGRAMACION",f'Validando workflow repetido: {form.workflow.data}')
        workflow_existente = programacionModel.query.filter_by(workflow=form.workflow.data).first()
        registrar_log("VALIDAR WORKFLOW", "PROGRAMACION",f'Workflow existente: {workflow_existente.workflow if workflow_existente else "No existe"}')
        if workflow_existente and (workflow_existente.id != form.id.data):
  
            raise ValueError('El WorkFlow ingresado ya está registrado en otra programación.')
    
    if form.retorno.data and not form.hora_retorno.data:
        raise ValueError('La hora de retorno es obligatoria cuando se selecciona retorno.')
    
    # Validar hora de retorno mayor a hora de salida
    if form.retorno.data:
        if form.hora_retorno.data  <= form.hora_salida.data:
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
    
    if not form.fecha_salida.data:
        raise ValueError('La fecha de salida es obligatoria.')
    
    # if form.status.data == 'Finalizado' and not tarifa_base:
    #     raise ValueError('No existe una tarifa para la combinación del servicio seleccionado ({}).'.format(codigo_tarifa))

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
    # Parámetros de DataTables para server-side processing
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')
    filtro = request.args.get('filtro', None)
    fecha_desde = request.args.get('fecha_desde')
    # fecha_desde = strftime('%d-%m-%Y', fecha_desde) if fecha_desde else None
    fecha_hasta = request.args.get('fecha_hasta')
    # fecha_hasta = strftime('%d-%m-%Y', fecha_hasta) if fecha_hasta else None
    
    # current_app.logger.debug(f"Parámetros recibidos - draw: {draw}, start: {start}, length: {length}, search_value: '{search_value}', filtro: '{filtro}', fecha_desde: '{fecha_desde}', fecha_hasta: '{fecha_hasta}'")

    origen_alias = aliased(ciudadesModel)
    destino_alias = aliased(ciudadesModel)

    # Construir la consulta base
    query = programacionModel.query

    # Aplicar filtro de status (case-insensitive) si existe
    if filtro:
        query = query.filter(programacionModel.status.ilike(filtro))

    # Filtro por rango de fechas (fecha_salida)
    def parse_fecha(valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor, '%d-%m-%Y').date()
        except ValueError:
            try:
                return datetime.strptime(valor, '%Y-%m-%d').date()
            except ValueError:
                return None

    desde = parse_fecha(fecha_desde)
    hasta = parse_fecha(fecha_hasta)

    if desde:
        query = query.filter(programacionModel.fecha_salida >= desde)
    if hasta:
        query = query.filter(programacionModel.fecha_salida <= hasta)

    # Obtener el total de registros sin filtros
    total_records = programacionModel.query.count()

    # Aplicar búsqueda global si hay un valor de búsqueda
    if search_value:
        query = (
            query
            .outerjoin(programacionModel.pasajeros)
            .outerjoin(clientesModel, pasajerosModel.empresa == clientesModel.id)
            .outerjoin(origen_alias, programacionModel.origen == origen_alias.id)
            .outerjoin(destino_alias, programacionModel.destino == destino_alias.id)
            .outerjoin(empleadosModel, programacionModel.operador == empleadosModel.id)
            .outerjoin(vehiculosModel, programacionModel.vehiculo == vehiculosModel.id)
        )
        
        search_terms = search_value.split()
        final_filters = []
        
        for term in search_terms:
            term_filter = f'%{term}%'
            # Para CADA palabra, buscamos en todas las columnas (OR)
            final_filters.append(or_(
                programacionModel.guia.ilike(term_filter),
                programacionModel.workflow.ilike(term_filter),
                programacionModel.status.ilike(term_filter),
                clientesModel.codigo.ilike(term_filter),
                clientesModel.empresa.ilike(term_filter),
                pasajerosModel.nombres.ilike(term_filter),
                origen_alias.nombre.ilike(term_filter),
                destino_alias.nombre.ilike(term_filter),
                empleadosModel.nombres.ilike(term_filter),
                vehiculosModel.tipo.ilike(term_filter)
            ))

        query = query.filter(and_(*final_filters)).distinct()
    # Obtener el total de registros filtrados
    total_filtered = query.count()

    # Aplicar ordenamiento si se especifica
    order_column = request.args.get('order[0][column]')
    order_dir = request.args.get('order[0][dir]', 'asc')

    if order_column:
        column_name = request.args.get(f'columns[{order_column}][data]')
        if column_name:
            # Solo ordenar por columnas directas del modelo para simplificar
            column_map = {
                'id': programacionModel.id,
                'fecha_salida': programacionModel.fecha_salida,
                'hora_salida': programacionModel.hora_salida,
                'status': programacionModel.status,
                'guia': programacionModel.guia,
                'workflow': programacionModel.workflow
            }

            if column_name in column_map:
                order_attr = column_map[column_name]
                if order_dir == 'desc':
                    query = query.order_by(order_attr.desc())
                else:
                    query = query.order_by(order_attr.asc())

    # Aplicar paginación
    query = query.offset(start).limit(length)

    # Ejecutar la consulta y serializar
    data = query.all()
    data_serializada = [d.serialize() for d in data]

    # Respuesta compatible con DataTables
    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_filtered,
        'data': data_serializada
    }
   
    try:
        preview_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_filtered,
            'data': response['data'][:1] if response.get('data') else []
        }
        # current_app.logger.debug(f"Respuesta DataTables (preview 1 registro): {preview_response}")
    except Exception as e:
        current_app.logger.debug(f"Error generando preview de respuesta: {e}")
    
    return jsonify(response)

@programacion_bp.route('/', methods=['GET'])
def programacion_get():
    if request.method == 'GET':
        form = programacionForm()
        return render_template('/programacion.html', User=current_user, form=form)

@programacion_bp.route('/', methods=['POST'])
@login_required
@log_action('CREAR', 'Programacion')
def programacion():
    form = programacionForm()
    dataForm = form.data
    programacion_data = {**form.data}
    
   

    if request.method == 'POST' and form.validate_on_submit():
        try:
            validar_coherencias(form)
        except ValueError as e:
            log = f"Error de validación para programación de cliente {form.empresa.data.empresa if form.empresa.data else '(sin empresa)'}: {str(e)}"
            return jsonify(success=False, mensaje='Error de validación.', errores=str(e), log=log)

        for field in ['csrf_token', 'submit', 'id', 'empresa', 'pasajeros']:
            programacion_data.pop(field, None)
        
        # CORREGIDO: Usar f-string para logging
        # current_app.logger.debug(f"Datos de la programación DIRECCION ORIGEN: {programacion_data['direccion_origen']}")
        
        fecha_string = form.fecha_salida.data
        
        lista_fechas = [fecha.strip() for fecha in fecha_string.split(',')]
        # current_app.logger.debug(f"LISTA DE FECHASSS: {lista_fechas}")

        for fecha_str in lista_fechas:
            
            # current_app.logger.debug(f"Cantidad de fechas: {len(lista_fechas)}")
            # current_app.logger.debug(f"Procesando fecha: {fecha_str}")
            fecha_obj = datetime.strptime(fecha_str, '%d-%m-%Y').date()
            nueva_programacion = programacionModel(**programacion_data)
            nueva_programacion.fecha_salida = fecha_obj
            nueva_programacion.pasajeros = form.pasajeros.data if form.pasajeros.data else []
            # Se asigna solo si el checkbox está marcado Y la hora no está vacía
            nueva_programacion.hora_retorno = form.hora_retorno.data if form.retorno.data  else None
        

            if form.status.data == 'Finalizado':
                nueva_factura = crear_factura_cliente(form)
                
                programacion = nueva_programacion.save()
                
                nueva_factura['programacion'] = programacion.id
            
                try:
                    crear_factura = facturasClientesModel(**nueva_factura)
                    db.session.add(crear_factura)
                    db.session.commit()
                    log = f"Factura creada con ID: {crear_factura.id} para programación ID: {programacion.id}"
                    
                    try:
                        crear_pago_operador(form)
                        log += f"; Pago operador creado para programación ID: {programacion.id}"
                    except Exception as e:
                        db.session.rollback()
                        error = format_error_simple(e)
                        log += f"; Error al crear el pago al operador para programación ID {programacion.id}: {error}"
                        return jsonify(success=False, mensaje='Error al crear el pago al operador.', error=str(e), log=log)
                    
                    
                    return jsonify(success=True, mensaje='Programación Finalizada y Factura Generada correctamente.', log=log)

                except Exception as e:
                    db.session.rollback()
                    error = format_error_simple(e)
                    log = f"Error al crear la factura para programación ID {nueva_programacion.id}: {error}"
                    return jsonify(success=False, mensaje='Error al crear la factura del cliente.', log=log)
            else:
                try:
                    nueva_programacion.save()
                    success=True
                    mensaje='Programación guardada correctamente.'
                    log = f"ID: {nueva_programacion.id}, guia {nueva_programacion.guia if nueva_programacion.guia else 'N/A'}, fecha: {fecha_str}, cliente: {form.empresa.data.empresa}"
                except Exception as e:
                    db.session.rollback()
                    success=False
                    mensaje='Error al guardar la programación.'
                    errores=str(e)
                    error = format_error_simple(e)
                    log = f"fecha {fecha_str}, cliente {form.empresa.data.empresa}, {error}"
        return jsonify(success=success, mensaje=mensaje, log=log)
    else:
        primer_error = next(iter(form.errors.values()))[0] if form.errors else 'Error desconocido.'
        return jsonify(success=False, mensaje='Error en el formulario.', errores=primer_error)   
   

@programacion_bp.route('/', methods=['DELETE'])
@login_required
@log_action('ELIMINAR', 'Programacion')
def delete_programacion():
    form = programacionForm()
    dataForm = form.data
    programacion_data = {**form.data}
    
    if request.method == 'DELETE':
        

        id_programacion = request.json.get('id')
        # current_app.logger.info(f"ID de programación a eliminar: {id_programacion}")

        if not id_programacion:
            return jsonify(success=False, mensaje='ID de programación no proporcionado.')

        programaciones = programacionModel.query.filter(programacionModel.id.in_(id_programacion)).all()
        if not programaciones:
            return jsonify(success=False, mensaje='Programación no encontrada.')
        
        try:
            # La eliminación en cascada se encargará de eliminar facturas y pagos asociados
            for programacion in programaciones:
                # current_app.logger.info(f"Eliminando programación ID: {programacion.id} por cuenta de {current_user.usuario}")
                db.session.delete(programacion)
            
            db.session.commit()
            empresas = [
                (prog.pasajeros[0].cliente.empresa if prog.pasajeros and prog.pasajeros[0].cliente else "(sin empresa)")
                for prog in programaciones
            ]
            log = f"IDs: {id_programacion}, clientes: {empresas}"
            return jsonify(success=True, mensaje='Programación y registros asociados eliminados correctamente.', log=log)

        except Exception as e:
            db.session.rollback()
            error = format_error_simple(e)
            empresas = [
                (prog.pasajeros[0].cliente.empresa if prog.pasajeros and prog.pasajeros[0].cliente else "(sin empresa)")
                for prog in programaciones
            ]
            log = f"ID: {id_programacion}, Clientes: {empresas}: {error}"
            return jsonify(success=False, mensaje='No se pudo eliminar la programación.', error=str(e), log=log)

#RUTINA EN USO ACTUALMENTE
@programacion_bp.route('/programacion/<int:id>/update', methods=['PUT'])
@login_required
@log_action('ACTUALIZAR', 'Programacion')
def update_programacion(id):
    programacion = programacionModel.query.get(id)
    form = programacionForm()
    # validar_coherencias(form)
    if not programacion:
        return jsonify(success=False, mensaje='Programación no encontrada.')
    
    if not current_user.is_admin and current_user.rol not in ['Programador', 'Finanzas']:
        log = f"Usuario sin permiso intentó actualizar programación ID {id} de {programacion.pasajeros[0].cliente.empresa if programacion.pasajeros and programacion.pasajeros[0].cliente else '(sin empresa)'} {current_user.usuario} (Rol: {current_user.rol})"
        return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.", log=log)
    
    
    try:
        validar_coherencias(form)
    except ValueError as e:
        return jsonify(success=False, mensaje=str(e), errores=str(e))
    
    # Obtener el status anterior
    status_anterior = programacion.status
    status_nuevo = request.form.get('status', 'Pendiente')
    
    factura_existing = facturasClientesModel.query.filter_by(programacion=id).first()
    recibo_operador_existing = pagosOperadoresModel.query.filter_by(programacion=id).first()
    
    # Si el status cambia de "Finalizado" a otro, eliminar facturas y pagos
    if status_anterior == 'Finalizado' and status_nuevo != 'Finalizado':
        try:
            if factura_existing:
                db.session.delete(factura_existing)
                # current_app.logger.info(f"Factura {factura_existing.id} eliminada por cambio de status")
            
            if recibo_operador_existing:
                db.session.delete(recibo_operador_existing)
                # current_app.logger.info(f"Pago operador {recibo_operador_existing.id} eliminado por cambio de status")
            
            db.session.commit()
            log = f"Id: {id}, cliente: {programacion.pasajeros[0].cliente.empresa if programacion.pasajeros and programacion.pasajeros[0].cliente else '(sin empresa)'}, guia: {programacion.guia if programacion.guia else 'N/A'} - Facturas y pagos eliminados por cambio de status"
            # current_app.logger.info(f"Facturas y pagos eliminados exitosamente para programación {id}")
        except Exception as e:
            db.session.rollback()
            error = format_error_simple(e)
            log = f"Error al eliminar facturas/pagos: {error} - Id: {id}, cliente: {programacion.pasajeros[0].cliente.empresa if programacion.pasajeros and programacion.pasajeros[0].cliente else '(sin empresa)'}, guia: {programacion.guia if programacion.guia else 'N/A'}"
            return jsonify(success=False, mensaje='Error al eliminar facturas y pagos asociados.', errores=str(e), log=log)
    
    # Si el status nuevo es Finalizado y ya existe factura, eliminar y regenerar
    elif status_nuevo == 'Finalizado' and factura_existing:
        try:
            # current_app.logger.info(f"Regenerando facturas para programación {id}")
            
            if factura_existing:
                db.session.delete(factura_existing)
                # current_app.logger.info(f"Factura {factura_existing.id} eliminada para regeneración")
            
            if recibo_operador_existing:
                db.session.delete(recibo_operador_existing)
                # current_app.logger.info(f"Pago operador {recibo_operador_existing.id} eliminado para regeneración")
            
            db.session.commit()
            # current_app.logger.info(f"Facturas y pagos eliminados exitosamente, se regenerarán después de actualizar")
            log = f"Id: {id}, cliente: {programacion.pasajeros[0].cliente.empresa if programacion.pasajeros and programacion.pasajeros[0].cliente else '(sin empresa)'}, guia: {programacion.guia if programacion.guia else 'N/A'} - Facturas y pagos eliminados para regeneración"
            
            # Limpiar las variables para que se creen nuevas facturas más adelante
            factura_existing = None
            recibo_operador_existing = None
            
        except Exception as e:
            db.session.rollback()
            error = format_error_simple(e)
            log = f"Error al eliminar facturas/pagos para regeneración: {error} - Id: {id}, cliente: {programacion.pasajeros[0].cliente.empresa if programacion.pasajeros and programacion.pasajeros[0].cliente else '(sin empresa)'}, guia: {programacion.guia if programacion.guia else 'N/A'}"
            # current_app.logger.error(log)
            return jsonify(success=False, mensaje='Error al regenerar facturas y pagos.', errores=str(e), log=log)

    
    try:
        # Procesar los campos del FormData manualmente
        
        if 'fecha_salida' in request.form:
            # programacion.fecha_salida = datetime.strptime(request.form['fecha_salida'], '%Y-%m-%d').date()
            
            lista_fechas = [fecha.strip() for fecha in request.form['fecha_salida'].split(',')]
            if len(lista_fechas) > 1:
                return jsonify(success=False, mensaje='Para actualización solo se permite una fecha a la vez.')
            try:
                fecha_obj = datetime.strptime(request.form['fecha_salida'], '%d-%m-%Y').date()
                programacion.fecha_salida = fecha_obj
            except ValueError:
                return jsonify(success=False, mensaje='Formato de fecha inválido. Use Día-Mes-Año.')
            
            
        
        if 'hora_salida' in request.form:
            programacion.hora_salida = datetime.strptime(request.form['hora_salida'], '%H:%M').time()
        
        if 'hora_retorno' in request.form and request.form['hora_retorno']:
            programacion.hora_retorno = datetime.strptime(request.form['hora_retorno'], '%H:%M').time()
        else:
            programacion.hora_retorno = None
        
        # Manejar campos booleanos
        programacion.retorno = 'retorno' in request.form
        
        # Campos de texto
        programacion.workflow = request.form.get('workflow', '')
        programacion.guia = request.form.get('guia', '')
        programacion.observaciones = request.form.get('observaciones', '')
        programacion.status = request.form.get('status', 'Pendiente')
        
        # Campos numéricos
        programacion.distancia = float(request.form.get('distancia', 0.0))
        programacion.tiempo_espera = int(request.form.get('tiempo_espera', 0))
        programacion.desvios = int(request.form.get('desvios', 0))
        
        # **CORRECCIÓN CLAVE: Asignar IDs en lugar de objetos para Foreign Keys**
        if 'empresa' in request.form and request.form['empresa']:
            empresa_id = int(request.form['empresa'])
            programacion.empresa = empresa_id  # ← ASIGNAR ID, no objeto
        
        if 'operador' in request.form and request.form['operador']:
            operador_id = int(request.form['operador'])
            programacion.operador = operador_id  # ← ASIGNAR ID, no objeto
        
        if 'origen' in request.form and request.form['origen']:
            origen_id = int(request.form['origen'])
            programacion.origen = origen_id  # ← ASIGNAR ID, no objeto
        
        if 'destino' in request.form and request.form['destino']:
            destino_id = int(request.form['destino'])
            programacion.destino = destino_id  # ← ASIGNAR ID, no objeto
        
        if 'vehiculo' in request.form and request.form['vehiculo']:
            vehiculo_id = int(request.form['vehiculo'])
            programacion.vehiculo = vehiculo_id  # ← ASIGNAR ID, no objeto
        
        # **MANEJO CRÍTICO: Pasajeros (relación many-to-many)**
        if 'pasajeros' in request.form:
            pasajeros_ids = request.form.getlist('pasajeros')
            # current_app.logger.debug(f"IDs de pasajeros recibidos: {pasajeros_ids}")
            
            pasajeros_objects = []
            for pasajero_id in pasajeros_ids:
                if pasajero_id:
                    pasajero = pasajerosModel.query.get(int(pasajero_id))
                    if pasajero:
                        pasajeros_objects.append(pasajero)
            
            programacion.pasajeros = pasajeros_objects
            # current_app.logger.debug(f"Pasajeros asignados: {[p.id for p in pasajeros_objects]}")
        
        # **MANEJO CRÍTICO: Direcciones (arrays)**
        if 'direccion_origen' in request.form:
            direcciones_origen = request.form.getlist('direccion_origen')
            programacion.direccion_origen = [d.strip() for d in direcciones_origen if d.strip()]
        
        if 'direccion_destino' in request.form:
            direcciones_destino = request.form.getlist('direccion_destino')
            programacion.direccion_destino = [d.strip() for d in direcciones_destino if d.strip()]
        
        # Manejar desplazamiento basado en retorno
        if programacion.retorno:
            programacion.desplazamiento = "idav"
        else:
            programacion.desplazamiento = "ida"
            programacion.hora_retorno = None

        programacion.turno = "D" if 6 <= programacion.hora_salida.hour < 18 else "E"
        
        programacion.wa_status = ""
        programacion.wa_msg_id = ""
        programacion.wa_callback_button = ""
        
        current_app.logger.debug(f"Datos a actualizar para programación ID {id}: desplazamiento: {programacion.desplazamiento}, turno: {programacion.turno}, retorno: {programacion.retorno}, hora_retorno: {programacion.hora_retorno}")
        
        # Debug antes del commit
        # current_app.logger.info(f"Valor de origen antes de commit: {programacion.origen} (tipo: {type(programacion.origen)})")
        # current_app.logger.info(f"Valor de destino antes de commit: {programacion.destino} (tipo: {type(programacion.destino)})")

        db.session.commit()
        
        mensaje = 'Programación actualizada correctamente.'
        empresa_nombre = (
            programacion.pasajeros[0].cliente.empresa
            if programacion.pasajeros and programacion.pasajeros[0].cliente
            else "(sin empresa)"
        )
        log = f"ID: {id}, cliente: {empresa_nombre}, status: {programacion.status}, guia: {programacion.guia if programacion.guia else 'N/A'}"
        
        # Solo crear factura si el status es Finalizado y no existe una factura previa
        if programacion.status == 'Finalizado' and not factura_existing:
            # current_app.logger.info(f"Programación finalizada, creando factura y pago operador.")
            # current_app.logger.info(f"Programación ID: {programacion.id}")
            
            try:
                # Crear un objeto form-like para pasar a las funciones de creación
                from types import SimpleNamespace
                
                form_data = SimpleNamespace()
                form_data.guia = SimpleNamespace(data=programacion.guia)
                form_data.empresa = SimpleNamespace(data=programacion.pasajeros[0].cliente if programacion.pasajeros else None)
                form_data.origen = SimpleNamespace(data=programacion.origen_rel)
                form_data.destino = SimpleNamespace(data=programacion.destino_rel)
                form_data.vehiculo = SimpleNamespace(data=programacion.vehiculo_rel)
                form_data.hora_salida = SimpleNamespace(data=programacion.hora_salida)
                form_data.retorno = SimpleNamespace(data=programacion.retorno)
                form_data.desvios = SimpleNamespace(data=programacion.desvios if programacion.desvios else 0)
                form_data.tiempo_espera = SimpleNamespace(data=programacion.tiempo_espera if programacion.tiempo_espera else 0)
                form_data.distancia = SimpleNamespace(data=programacion.distancia if programacion.distancia else 0)
                
                # Crear factura del cliente
                nueva_factura = crear_factura_cliente(form_data)
                nueva_factura['programacion'] = programacion.id
                
                factura_cliente = facturasClientesModel(**nueva_factura)
                db.session.add(factura_cliente)
                db.session.commit()
                
                log = mensaje + f" Factura creada para programacion: ID {programacion.id}, cliente {form_data.empresa.data.empresa}, guia {form_data.guia.data if form_data.guia.data else 'N/A'}"
                
                # Crear pago al operador
                crear_pago_operador(form_data)
                
                mensaje = 'Programación Finalizada, Factura de Cliente y Pago Operador Generados correctamente.'
                log = mensaje + " - " + f" Programación ID {programacion.id}, cliente {form_data.empresa.data.empresa}, guia {form_data.guia.data if form_data.guia.data else 'N/A'}"
                
            except Exception as e:
                db.session.rollback()
                error = format_error_simple(e)
                log += f" .Error al crear factura/pago: {error}"
                current_app.logger.error(log)
                return jsonify(success=False, mensaje=f'Error al crear la factura del cliente o pago operador.  {str(e)}', error=str(e), log=log)
        
        return jsonify(success=True, mensaje=mensaje, log=log)

    except Exception as e:
        db.session.rollback()
        error = format_error_simple(e)
        log = f"Error al actualizar programación ID {id}: {error}"
        return jsonify(success=False, mensaje='Error al actualizar la programación.', error=str(e), log=log)


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
    # print("Pasajeros seleccionados:", pasajeros_seleccionados)
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