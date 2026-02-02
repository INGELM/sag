from flask import Response, current_app, json, jsonify, render_template, flash, redirect, url_for, request
from sqlalchemy import or_, and_
from sqlalchemy.orm import aliased
from app.clientes.models import clientesModel, pasajerosModel, tarifasModel, recargoVehiculosModel
from app.auxiliares.models import ciudadesModel
from app.empleados.models import empleadosModel, tarifasOperadoresModel
from app.facturacion import facturacion_bp
from app.extensions import db
from flask_login import login_required, current_user
from app.facturacion.form import facturasClientesForm, pagosOperadoresForm
from app.facturacion.models import pagosOperadoresModel, facturasClientesModel
from app.programacion.models import programacionModel
from datetime import datetime

@facturacion_bp.before_request
def before_request():
    if not current_user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json':
            return jsonify(success=False, mensaje='No autenticado', redirect=url_for('login.login')), 401

        flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
        return redirect(url_for('login.login'))

@staticmethod
def create_codigo_desc(form):
    desplazamiento = "ida" if not form.retorno.data else "idav"
    if 6 <= form.hora_salida.data.hour < 18:
        horario = "D"
    else:
        horario = "E"

    codigo_desc = f"{form.empresa.data.codigo}{form.origen.data.codigo}{form.destino.data.codigo}-{form.vehiculo.data.codigo}-{desplazamiento}-{horario}".upper()
    current_app.logger.debug(f"Código de descripción generado: {codigo_desc}")
    return codigo_desc

@staticmethod
def crear_factura_cliente(form):

    codigo_desc = create_codigo_desc(form)

    current_app.logger.debug(f"Código de descripción generado: {codigo_desc}")

    tarifas = tarifasModel.query.filter_by(codigo_desc=codigo_desc).first()
    current_app.logger.debug(f"Tarifas para factura encontradas: {tarifas}")
   
    factura_existente = facturasClientesModel.query.join(
        facturasClientesModel.programacion_rel
    ).filter(
        programacionModel.guia == form.guia.data
    ).first()
    
    if factura_existente:
        current_app.logger.debug(f"Ya existe una factura para la Guia: {form.guia.data}")
        raise ValueError(f"Ya existe una factura para la Guia: {form.guia.data}, elimínela para modificar la programación.")

    if not tarifas:
        raise ValueError("No se encontraron tarifas con el código proporcionado.")

   
    costo_desvios = tarifas.desvios if tarifas.desvios else 0
    costo_espera = tarifas.espera if tarifas.espera else 0
    costo_base = tarifas.base if tarifas.base else 0
    
    # calcular recargo por vehiculo

    # recargo = recargoVehiculosModel.query.filter_by(vehiculo=form.vehiculo.data.id).first()
    # if recargo:
    #     costo_base += costo_base * recargo.recargo
    #     current_app.logger.debug(f"Recargo por vehículo aplicado: {recargo.recargo}")


    costo_distancia = tarifas.tarifa_km if tarifas.tarifa_km else 0
  

    total_desvios = form.desvios.data * costo_desvios
    total_espera = form.tiempo_espera.data * costo_espera
    total_distancia = form.distancia.data * costo_distancia if form.distancia.data else 0
    total_base = costo_base


    costo_total = total_base + total_desvios + total_espera + total_distancia

    nueva_factura = {

        "tarifas_cliente": tarifas.id,
        "factura": "--",
        "costo_desvios": costo_desvios,
        "costo_espera": costo_espera,
        "costo_distancia": costo_distancia,
        "costo_base": costo_base,
        "total_desvios": total_desvios,
        "total_espera": total_espera,
        "costo_total": costo_total,
        "total_distancia": total_distancia,
        "status": "Por facturar",
    }
    
    current_app.logger.debug("Datos de la nueva factura:", nueva_factura)
    
    return nueva_factura
    
@facturacion_bp.route('/facturasClientes', methods=['GET'])
def facturacion():
    form = facturasClientesForm()
    user = current_user
    clientes = clientesModel.query.all()

    return render_template('facturacion.html', User=user, form=form, clientes=clientes)



@facturacion_bp.route('/facturasClientes/cambio-status', methods=['PUT'])
@login_required
def facturasClientes_cambio_status():
    ids = request.json.get('ids', [])
    nuevo_status = request.json.get('nuevo_status', 'Por facturar')

    if not ids:
        return jsonify(success=False, mensaje='No se proporcionaron IDs de facturas.')

    facturas = facturasClientesModel.query.filter(facturasClientesModel.id.in_(ids)).all()

    if not facturas:
        return jsonify(success=False, mensaje='No se encontraron facturas.')

    for factura in facturas:
        factura.status = nuevo_status

    try:
        db.session.commit()
        return jsonify(success=True, mensaje='Estado de las facturas actualizado correctamente.')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error al actualizar el estado de las facturas:", e)
        return jsonify(success=False, mensaje='Error al actualizar el estado de las facturas.', error=str(e))

@facturacion_bp.route('/facturasClientes/agregar-factura', methods=['PUT'])
@login_required
def facturasClientes_agregar_factura():
    numero_factura = request.json.get('factura')
    id_facturas = request.json.get('ids', [])
    
    current_app.logger.debug("Número de factura recibido:", numero_factura)
    current_app.logger.debug("ID de facturas recibido:", id_facturas)
    
    if not numero_factura or not id_facturas:
        return jsonify(success=False, mensaje='Número de factura o ID no proporcionado.')
    
    if not isinstance(id_facturas, list):
        id_facturas = [id_facturas]
        
    for id_factura in id_facturas:
        factura = facturasClientesModel.query.filter_by(id=id_factura).first()
        
        if not factura:
            return jsonify(success=False, mensaje=f'Factura con ID {id_factura} no encontrada.')
        
        # if factura.factura and factura.factura != "--":
        #     return jsonify(success=False, mensaje=f'La factura con ID {id_factura} ya tiene un número de factura asignado.')
        
        try:
            factura.factura = numero_factura
            factura.status = 'Facturado'
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al agregar la factura {numero_factura} a la factura con ID {id_factura}: {str(e)}")
            return jsonify(success=False, mensaje=f'Error al agregar la factura: {str(e)}')
    
    return jsonify(success=True, mensaje='Numero(s) de Factura(s) agregada(s) correctamente.')

@facturacion_bp.route('/facturasClientes', methods=['PUT'])
def facturasClientes_update():
    if not current_user.is_admin:
        # current_app.logger.debug("Solicitud PUT recibida.")
        return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.")
   
    form = facturasClientesForm()
    user = current_user
        
    if form.validate_on_submit():
        form_data = form.data
       
        factura = facturasClientesModel.query.filter_by(id=form_data['id']).first()

        if not factura:
            raise ValueError("Factura no encontrada.")

        # Actualizar los campos de la factura
        try:
            factura.total_espera = "--"
            factura.total_desvios = "--"
            factura.total_distancia = "--"
            factura.costo_base = "--"
            factura.costo_total = form_data['costo_total'] if form_data['costo_total'] else factura.costo_total
            factura.factura = form_data['factura'] if form_data['factura'] else factura.factura
            factura.status = form_data['status']
            
            db.session.commit()
            
            mensaje = "Factura actualizada exitosamente."
            
            # Si el status es Finalizado, crear el pago al operador si no existe
            if form_data['status'] == 'Finalizado':
                programacion = factura.programacion_rel
                
                if programacion:
                    # Verificar si ya existe un pago para esta programación
                    pago_existente = pagosOperadoresModel.query.filter_by(programacion=programacion.id).first()
                    
                    if not pago_existente:
                        try:
                            # Crear un objeto form-like para pasar a la función de creación
                            from types import SimpleNamespace
                            
                            form_data_pago = SimpleNamespace()
                            form_data_pago.guia = SimpleNamespace(data=programacion.guia)
                            form_data_pago.empresa = SimpleNamespace(data=programacion.pasajeros[0].cliente if programacion.pasajeros else None)
                            form_data_pago.origen = SimpleNamespace(data=programacion.origen_rel)
                            form_data_pago.destino = SimpleNamespace(data=programacion.destino_rel)
                            form_data_pago.vehiculo = SimpleNamespace(data=programacion.vehiculo_rel)
                            form_data_pago.hora_salida = SimpleNamespace(data=programacion.hora_salida)
                            form_data_pago.retorno = SimpleNamespace(data=programacion.retorno)
                            form_data_pago.desvios = SimpleNamespace(data=programacion.desvios if programacion.desvios else 0)
                            form_data_pago.tiempo_espera = SimpleNamespace(data=programacion.tiempo_espera if programacion.tiempo_espera else 0)
                            
                            # Crear pago al operador
                            crear_pago_operador(form_data_pago)
                            
                            mensaje = "Factura actualizada y Pago Operador generado exitosamente."
                            current_app.logger.debug(f"Pago al operador creado para programación: {programacion.id}")
                            
                        except Exception as e:
                            current_app.logger.error(f"Error al crear pago operador: {str(e)}")
                            # No fallar la actualización de la factura si falla el pago
                            mensaje = f"Factura actualizada, pero error al crear pago operador: {str(e)}"
                    else:
                        current_app.logger.debug(f"Ya existe un pago para esta programación: {pago_existente.id}")
            
            return jsonify(success=True, mensaje=mensaje, icon='success')
        except Exception as e:
            db.session.rollback()
            return jsonify(success=False, mensaje=f"Error al actualizar la factura: {str(e)}", icon='danger')
    
    return render_template('facturacion.html', User=user, form=form)

@facturacion_bp.route('/facturasClientes', methods=['DELETE'])
def facturasClientes_delete():
    if not current_user.is_admin:
            current_app.logger.debug("Solicitud DELETE recibida.")
            return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.")

    form = facturasClientesForm()
    user = current_user
    current_app.logger.debug("Solicitud DELETE recibida por:", user, "rol:", user.is_admin)
    
    if not current_user.is_admin:
        current_app.logger.debug("Solicitud DELETE recibida.")
        raise PermissionError('No tienes permiso para realizar esta acción.')

    id_facturacion = request.json.get('id')
    if not isinstance(id_facturacion, list):
        id_facturacion = [id_facturacion]
    
    current_app.logger.debug("ID de facturación a eliminar:", id_facturacion)

    if not id_facturacion:
        return jsonify(success=False, mensaje='ID de facturación no proporcionado.')

    facturas = facturasClientesModel.query.filter(facturasClientesModel.id.in_(id_facturacion)).all()

    if not facturas:
        return jsonify(success=False, mensaje='Factura no encontrada.')

    try:
        for factura in facturas:
            db.session.delete(factura)
        db.session.commit()
        return jsonify(success=True, mensaje='Facturas eliminadas correctamente.')

    except Exception as e:
        db.session.rollback()
        current_app.logger.debug("Error al eliminar la factura:", e)
        return jsonify(success=False, mensaje='No se pudo eliminar la factura.', error=str(e))
    
    
    
@facturacion_bp.route('/facturasClientes/data', methods=['GET'])
def facturas_clientes_data():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '').strip()
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    def parse_fecha(valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(valor, '%d-%m-%Y').date()
            except ValueError:
                return None

    desde = parse_fecha(fecha_desde)
    hasta = parse_fecha(fecha_hasta)

    origen_alias = aliased(ciudadesModel)
    destino_alias = aliased(ciudadesModel)

    base_query = facturasClientesModel.query.join(programacionModel)
    base_query = (base_query
                  .outerjoin(programacionModel.pasajeros)
                  .outerjoin(clientesModel, pasajerosModel.empresa == clientesModel.id)
                  .outerjoin(origen_alias, programacionModel.origen == origen_alias.id)
                  .outerjoin(destino_alias, programacionModel.destino == destino_alias.id))

    total_records = facturasClientesModel.query.count()

    if desde:
        base_query = base_query.filter(programacionModel.fecha_salida >= desde)
    if hasta:
        base_query = base_query.filter(programacionModel.fecha_salida <= hasta)

    if search_value:
        terms = search_value.split()
        term_filters = []
        for t in terms:
            like_term = f"%{t}%"
            term_filters.append(or_(
                facturasClientesModel.factura.ilike(like_term),
                facturasClientesModel.status.ilike(like_term),
                programacionModel.guia.ilike(like_term),
                programacionModel.workflow.ilike(like_term),
                clientesModel.codigo.ilike(like_term),
                clientesModel.empresa.ilike(like_term),
                pasajerosModel.nombres.ilike(like_term),
                origen_alias.nombre.ilike(like_term),
                destino_alias.nombre.ilike(like_term)
            ))

        if term_filters:
            base_query = base_query.filter(and_(*term_filters))

    total_filtered = base_query.distinct().count()

    order_column = request.args.get('order[0][column]')
    order_dir = request.args.get('order[0][dir]', 'desc')
    column_name = request.args.get(f'columns[{order_column}][data]') if order_column else None

    column_map = {
        'fecha': programacionModel.fecha_salida,
        'cliente': clientesModel.codigo,
        'factura': facturasClientesModel.factura,
        'guia': programacionModel.guia,
        'status': facturasClientesModel.status,
    }

    if column_name in column_map:
        sort_col = column_map[column_name]
        base_query = base_query.order_by(sort_col.desc() if order_dir == 'desc' else sort_col.asc())
    else:
        base_query = base_query.order_by(programacionModel.fecha_salida.desc())

    data = base_query.distinct().offset(start).limit(length).all()

    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_filtered,
        'data': [factura.serialize() for factura in data]
    })



@facturacion_bp.route('/facturasClientes/all', methods=['GET'])
def facturas_clientes_all():
    facturas = facturasClientesModel.query.all()
    # facturas.sort(key=lambda x: x.programacion, reverse=True)
    
    # if not facturas:
    #     return jsonify(success=False, mensaje="No se encontraron facturas.", icon='warning', data=[])
    
    
    
    response_data = {
        'success': True,
        'mensaje': 'Programaciones obtenidas exitosamente.',
        'data': [factura.serialize() for factura in facturas]
    }
    return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')
 
@facturacion_bp.route('/facturasClientes/get_data/<int:id>', methods=['GET'])
def get_factura_cliente(id):
    factura = facturasClientesModel.query.get(id)
    
    if not factura:
        return jsonify(success=False, mensaje='Factura no encontrada.')

    factura_data = factura.serialize_form()

    return jsonify(success=True, mensaje='Factura obtenida exitosamente.', data=factura_data)

@facturacion_bp.route('/facturasClientes', methods=['GET'])
def facturas_clientes():
    current_app.logger.debug("Obteniendo facturas de clientes...")
        
    cliente = request.args.get('cliente')
    
    current_app.logger.debug("Cliente recibido:", cliente)

    if cliente:
        facturas = facturasClientesModel.query.join(
            facturasClientesModel.programacion_rel
        ).join(
            programacionModel.pasajeros
        ).filter(
            programacionModel.pasajeros.any(empresa=cliente)
        ).all()
    else:
        facturas = facturasClientesModel.query.all()
 
    response_data = {
        'success': True,
        'mensaje': 'Facturas obtenidas exitosamente.',
        'data': [factura.serialize(x) for x, factura in enumerate(facturas)]
    }

    current_app.logger.debug("Datos de respuesta:", response_data['data'])
    return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')


@facturacion_bp.route('/pagosOperadores', methods=['GET'])
def pagos_operadores():
    form = pagosOperadoresForm()
    user = current_user
    
    return render_template('pagosOperadores.html', User=user, form=form)

@facturacion_bp.route('/pagosOperadores/get_data/<int:id>', methods=['GET'])
def get_pago_operador(id):
    pago = pagosOperadoresModel.query.get(id)

    if not pago:
        return jsonify(success=False, mensaje='Pago no encontrado.')
    
    pago_data = pago.serialize_form()

    return jsonify(success=True, mensaje='Pago obtenido exitosamente.', data=pago_data)


@facturacion_bp.route('/pagosOperadores/data', methods=['GET'])
def pagos_operadores_data():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '').strip()
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    def parse_fecha(valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(valor, '%d-%m-%Y').date()
            except ValueError:
                return None

    desde = parse_fecha(fecha_desde)
    hasta = parse_fecha(fecha_hasta)

    origen_alias = aliased(ciudadesModel)
    destino_alias = aliased(ciudadesModel)

    base_query = pagosOperadoresModel.query.join(programacionModel)
    base_query = (base_query
                .outerjoin(programacionModel.pasajeros)
                .outerjoin(clientesModel, pasajerosModel.empresa == clientesModel.id)
                .outerjoin(origen_alias, programacionModel.origen == origen_alias.id)
                .outerjoin(destino_alias, programacionModel.destino == destino_alias.id)
                .outerjoin(empleadosModel, programacionModel.operador == empleadosModel.id))

    total_records = pagosOperadoresModel.query.count()

    if desde:
        base_query = base_query.filter(programacionModel.fecha_salida >= desde)
    if hasta:
        base_query = base_query.filter(programacionModel.fecha_salida <= hasta)

    if search_value:
        terms = search_value.split()
        term_filters = []
        for t in terms:
            like_term = f"%{t}%"
            term_filters.append(or_(
                programacionModel.guia.ilike(like_term),
                clientesModel.codigo.ilike(like_term),
                clientesModel.empresa.ilike(like_term),
                pasajerosModel.nombres.ilike(like_term),
                origen_alias.nombre.ilike(like_term),
                destino_alias.nombre.ilike(like_term),
                empleadosModel.nombres.ilike(like_term)
            ))

        if term_filters:
            base_query = base_query.filter(and_(*term_filters))

    total_filtered = base_query.distinct().count()

    order_column = request.args.get('order[0][column]')
    order_dir = request.args.get('order[0][dir]', 'desc')
    column_name = request.args.get(f'columns[{order_column}][data]') if order_column else None

    column_map = {
        'fecha': programacionModel.fecha_salida,
        'cliente': clientesModel.codigo,
        'guia': programacionModel.guia,
        'total_': pagosOperadoresModel.costo_total,
    }

    if column_name in column_map:
        sort_col = column_map[column_name]
        base_query = base_query.order_by(sort_col.desc() if order_dir == 'desc' else sort_col.asc())
    else:
        base_query = base_query.order_by(programacionModel.fecha_salida.desc())

    data = base_query.distinct().offset(start).limit(length).all()

    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_filtered,
        'data': [pago.serialize() for pago in data]
    })

@facturacion_bp.route('/pagosOperadores/all', methods=['GET'])
def pagos_operadores_all():
    pagos = pagosOperadoresModel.query.all()
    response_data = {
        'success': True,
        'mensaje': 'Pagos de operadores obtenidos exitosamente.',
        'data': [pago.serialize() for pago in pagos]
    }
    return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')


@staticmethod
def crear_pago_operador(form):
    
    codigo_desc = create_codigo_desc(form)
    current_app.logger.debug(f"Código de descripción generado: {codigo_desc}")
    programacion = programacionModel.query.filter_by(guia=form.guia.data).first()
    
    current_app.logger.debug(f"Programación encontrada: {programacion}")
    
    tipo_operador = programacion.operador_rel.tipo if programacion and programacion.operador_rel else None
    current_app.logger.debug(f"Tipo de operador: {tipo_operador}")
    
    tarifas_clientes = tarifasModel.query.filter_by(codigo_desc=codigo_desc).first()
    tarifa_cliente_id = tarifas_clientes.id if tarifas_clientes else None
    
    try:
        tarifas_operador = tarifasOperadoresModel.query.filter_by(codigo=tarifa_cliente_id, tipo=tipo_operador).first()
    except Exception as e:
        current_app.logger.debug(f"Error al obtener tarifas del operador: {str(e)}")
        raise ValueError("No se encontró tarifas del operador.")
    
    current_app.logger.debug(f"Tarifas Operador encontradas: {tarifas_operador}")

    if not tarifas_clientes:
        raise ValueError("No se encontraron tarifas para Clientes con el código proporcionado.")

    if not tarifas_operador:
        raise ValueError("No se encontraron tarifas para Operador con la ruta proporcionada.")

    if not programacion:
        raise ValueError("No se encontró una programación con la guía proporcionada.")
    

    costo_desvios = tarifas_operador.desvios if tarifas_operador.desvios else 0
    costo_espera = tarifas_operador.espera if tarifas_operador.espera else 0
    costo_base = tarifas_operador.base if tarifas_operador.base else 0
    costo_total = costo_base + costo_desvios*form.desvios.data + costo_espera*form.tiempo_espera.data
    # costo_distancia = tarifas_clientes.tarifa_km 

   
    # total_distancia = form.distancia.data * costo_distancia if form.distancia.data else 0

   
       
    
    nuevo_pago = {
        "programacion":  programacion.id,
        "tarifas_operador": tarifas_operador.id,
        "costo_desvios": costo_desvios,
        "costo_espera": costo_espera,
        "costo_base": costo_base,
        "costo_total":costo_total,  # Inicialmente 0, se calculará después
    }
    
 
    try:
        # from app.facturacion.models import pagosOperadoresModel
        pago = pagosOperadoresModel(**nuevo_pago)
        db.session.add(pago)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.debug(f"Error al crear el pago: {str(e)}")
        raise ValueError(f"Error al crear el pago")

@facturacion_bp.route('/pagosOperadores', methods=['DELETE'])
def pagosOperadores_delete():
    form = pagosOperadoresForm()
    user = current_user

    id_pago = request.json.get('id')
    current_app.logger.debug("ID de pago a eliminar:", id_pago)

    if not id_pago:
        return jsonify(success=False, mensaje='ID de pago no proporcionado.')

    pago = pagosOperadoresModel.query.get(id_pago)

    if not pago:
        return jsonify(success=False, mensaje='Pago no encontrado.')

    try:
        db.session.delete(pago)
        db.session.commit()
        return jsonify(success=True, mensaje='Pago eliminado correctamente.')

    except Exception as e:
        db.session.rollback()
        current_app.logger.debug("Error al eliminar el pago:", e)
        return jsonify(success=False, mensaje='No se pudo eliminar el pago.', error=str(e))

@facturacion_bp.route('/pagosOperadores', methods=['PUT'])
def pagosOperadores_update():
    form = pagosOperadoresForm()
    user = current_user
    
    current_app.logger.debug("Solicitud PUT recibida por:", user, "rol:", user.is_admin)
        
    if form.validate_on_submit():
        form_data = form.data

        pago = pagosOperadoresModel.query.filter_by(id=form_data['id']).first()

        if not pago:
            raise ValueError("Pago no encontrado.")

        # Actualizar los campos del pago
        try:
            pago.costo_espera = "--"
            pago.costo_desvios = "--"
            pago.costo_base = "--"
            pago.costo_total = form_data['costo_total']

            db.session.commit()
            return jsonify(success=True, mensaje="Pago actualizado exitosamente.", icon='success')
        except Exception as e:
            db.session.rollback()
            return jsonify(success=False, mensaje=f"Error al actualizar el pago: {str(e)}", icon='danger')

    return render_template('pagosOperadores.html', User=user, form=form)

@facturacion_bp.route('/cobro_detalle', methods=['GET'])
def cobro_detalle():
    user = current_user
    # current_app.logger.debug(f"Accediendo a la vista de cobro detalle por: {user} rol: {user.is_admin}")
    return render_template('cobro-detalle.html', User=user)

@facturacion_bp.route("/get/cobro_detalle", methods=['GET'])
def get_cobro_detalle():
    user = current_user
    # programaciones = programacionModel.query.all()
    facturas = facturasClientesModel.query.all()
    
    data = []
    for factura in facturas:
        total_pasajeros = len(factura.programacion_rel.pasajeros)
        for x, pasajero in enumerate(factura.programacion_rel.pasajeros):
            data.append(factura.serialize_detalle(x, total_pasajeros))

    response_data = {
        'success': True,
        'mensaje': 'Detalles de cobro obtenidos exitosamente.',
        'data': data
    }

    return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')


@facturacion_bp.route('/cobro_detalle/data', methods=['GET'])
def cobro_detalle_data():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '').strip()
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    def parse_fecha(valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(valor, '%d-%m-%Y').date()
            except ValueError:
                return None

    desde = parse_fecha(fecha_desde)
    hasta = parse_fecha(fecha_hasta)

    base_query = facturasClientesModel.query.join(programacionModel)
    base_query = (base_query
                  .outerjoin(programacionModel.pasajeros)
                  .outerjoin(clientesModel, pasajerosModel.empresa == clientesModel.id))

    if desde:
        base_query = base_query.filter(programacionModel.fecha_salida >= desde)
    if hasta:
        base_query = base_query.filter(programacionModel.fecha_salida <= hasta)

    facturas = base_query.all()

    rows = []
    for factura in facturas:
        pasajeros = factura.programacion_rel.pasajeros if factura.programacion_rel and factura.programacion_rel.pasajeros else []
        total_pasajeros = len(pasajeros)
        if total_pasajeros == 0:
            continue
        for idx, _ in enumerate(pasajeros):
            rows.append(factura.serialize_detalle(idx, total_pasajeros))

    records_total = len(rows)

    if search_value:
        terms = search_value.lower().split()

        def coincide(row):
            campos = ['cliente', 'pasajero', 'factura', 'guia', 'origen', 'destino', 'horario', '#_Pasajero']

            def match_term(term):
                for campo in campos:
                    valor = row.get(campo)
                    if valor and term in str(valor).lower():
                        return True
                return False

            return all(match_term(term) for term in terms)

        filtered_rows = list(filter(coincide, rows))
    else:
        filtered_rows = rows

    order_column = request.args.get('order[0][column]')
    order_dir = request.args.get('order[0][dir]', 'desc')
    column_name = request.args.get(f'columns[{order_column}][data]') if order_column else None

    def sort_value(valor):
        try:
            return float(valor)
        except (TypeError, ValueError):
            return str('' if valor is None else valor).lower()

    if column_name:
        filtered_rows.sort(key=lambda row: sort_value(row.get(column_name)), reverse=(order_dir == 'desc'))

    data = filtered_rows[start:start + length]

    response = {
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': len(filtered_rows),
        'data': data
    }

    return jsonify(response)

     