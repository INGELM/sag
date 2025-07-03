from flask import Response, current_app, json, jsonify, render_template, flash, redirect, url_for, request
from app.clientes.models import clientesModel, tarifasModel, recargoVehiculosModel
from app.empleados.models import tarifasOperadoresModel
from app.facturacion import facturacion_bp
from app.extensions import db
from flask_login import login_required, current_user
from app.facturacion.form import facturasClientesForm, pagosOperadoresForm
from app.facturacion.models import pagosOperadoresModel, facturasClientesModel
from app.programacion.models import programacionModel

@facturacion_bp.before_request
@login_required
def before_request():
    if not current_user.is_authenticated:
        flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
        return redirect(url_for('login.login'))


@staticmethod
def crear_factura_cliente(form):
    
    
    programacion = programacionModel.query.filter_by(guia=form.guia.data).first()
    current_app.debug(f"Programación encontrada: {programacion}")
    
    tarifas = tarifasModel.query.filter_by(codigo=programacion.codigo_tarifa).first()
    current_app.debug(f"Tarifas encontradas: {tarifas}")
    recargo_vehiculo = recargoVehiculosModel.query.filter_by(cliente=form.empresa.data.id, vehiculo=form.vehiculo.data.id).first()
    current_app.debug(f"Recargo de vehículo encontrado: {recargo_vehiculo}")

    factura_existente = facturasClientesModel.query.join(
        facturasClientesModel.programacion_rel
    ).filter(
        programacionModel.guia == form.guia.data
    ).first()
    
    if factura_existente:
        current_app.debug(f"Ya existe una factura para la Guia: {programacion.guia}")
        raise ValueError(f"Ya existe una factura para la Guia: {programacion.guia}")


    if not tarifas:
        raise ValueError("No se encontraron tarifas con el código proporcionado.")

    if not recargo_vehiculo:
        raise ValueError("No se encontró un recargo de vehículo para el cliente proporcionado.")
    
    if not programacion:
        raise ValueError("No se encontró una programación con la guía proporcionada.")

    # if factura_existente:
    #     current_app.debug(f"Ya existe una factura para la Guia: {programacion.guia}")
    #     raise ValueError("Ya existe una factura para la Guia: {}".format(programacion.guia))
    
    costo_vehiculo = recargo_vehiculo.recargo/100 if recargo_vehiculo.recargo else 0
    costo_desvios = tarifas.desvios if tarifas.desvios else 0
    costo_espera = tarifas.espera if tarifas.espera else 0
    costo_base = tarifas.base if tarifas.base else 0
    costo_especial = tarifas.especial if programacion.turno == 'especial' else 0
    costo_distancia = tarifas.tarifa_km if tarifas.tarifa_km else 0
    current_app.debug("Costo distancia: ",costo_distancia)
    current_app.debug("distancia: ", form.distancia.data)

    total_desvios = form.desvios.data * costo_desvios
    total_espera = form.tiempo_espera.data * costo_espera
    total_distancia = form.distancia.data * costo_distancia if form.distancia.data else 0
    total_distancia = total_distancia*2 if programacion.retorno else total_distancia
    total_base = costo_base*2 if programacion.retorno else costo_base


    costo_total = total_base + total_desvios + total_espera + total_distancia
    costo_total += costo_total*costo_vehiculo
    costo_total += costo_total*costo_especial/100

    current_app.debug(f"Costos calculados: Base: {total_base}, Desvios: {total_desvios}, Espera: {total_espera}, Recargo Vehiculo: {costo_total*costo_vehiculo}, Especial: {costo_total*costo_especial/100}, Costo Total: {costo_total}")
    
    current_app.debug(f"Creando factura con los siguientes datos: \n"
          f"Programación ID: {programacion.id}, "
          f"Tarifas ID: {tarifas.id}, "
          f"Recargo Vehículo ID: {recargo_vehiculo.id}, "
          f"Total Desvíos: {total_desvios}, "
          f"Total Espera: {total_espera}, "
          f"Costo Total: {costo_total}")
    

    nueva_factura = {
        "programacion":  programacion.id,
        "tarifas_cliente": tarifas.id,
        "recargo_vehiculo": recargo_vehiculo.id,
        "total_desvios": total_desvios,
        "total_espera": total_espera,
        "costo_total": costo_total
    }
    
    try:

        factura = facturasClientesModel(**nueva_factura)
        db.session.add(factura)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.debug(f"Error al crear la factura: {str(e)}")
        raise ValueError(f"Error al crear la factura")


@facturacion_bp.route('/facturasClientes', methods=['GET'])
def facturacion():
    form = facturasClientesForm()
    user = current_user
    clientes = clientesModel.query.all()

    return render_template('facturacion.html', User=user, form=form, clientes=clientes)

@facturacion_bp.route('/facturasClientes', methods=['PUT'])
def facturasClientes_update():
    if not current_user.is_admin:
        # current_app.debug("Solicitud PUT recibida.")
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
            factura.costo_total = form_data['costo_total']
            
            db.session.commit()
            return jsonify(success=True, mensaje="Factura actualizada exitosamente.", icon='success')
        except Exception as e:
            db.session.rollback()
            return jsonify(success=False, mensaje=f"Error al actualizar la factura: {str(e)}", icon='danger')
    
    return render_template('facturacion.html', User=user, form=form)

@facturacion_bp.route('/facturasClientes', methods=['DELETE'])
def facturasClientes_delete():
    if not current_user.is_admin:
            current_app.debug("Solicitud DELETE recibida.")
            return jsonify(success=False, mensaje='No tienes permiso para realizar esta acción.', errores="Consulte a un administrador.")

    form = facturasClientesForm()
    user = current_user
    current_app.debug("Solicitud DELETE recibida por:", user, "rol:", user.is_admin)
    
    if not current_user.is_admin:
        current_app.debug("Solicitud DELETE recibida.")
        raise PermissionError('No tienes permiso para realizar esta acción.')

    id_facturacion = request.json.get('id')
    current_app.debug("ID de facturación a eliminar:", id_facturacion)

    if not id_facturacion:
        return jsonify(success=False, mensaje='ID de facturación no proporcionado.')

    factura = facturasClientesModel.query.get(id_facturacion)

    if not factura:
        return jsonify(success=False, mensaje='Factura no encontrada.')

    try:
        db.session.delete(factura)
        db.session.commit()
        return jsonify(success=True, mensaje='Factura eliminada correctamente.')

    except Exception as e:
        db.session.rollback()
        current_app.debug("Error al eliminar la factura:", e)
        return jsonify(success=False, mensaje='No se pudo eliminar la factura.', error=str(e))
    
    
    

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
 
@facturacion_bp.route('/facturasClientes', methods=['GET'])
def facturas_clientes():
    current_app.debug("Obteniendo facturas de clientes...")
        
    cliente = request.args.get('cliente')
    
    current_app.debug("Cliente recibido:", cliente)

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
        'data': [factura.serialize() for factura in facturas]
    }

    current_app.debug("Datos de respuesta:", response_data['data'])
    return Response(json.dumps(response_data, sort_keys=False, ensure_ascii=False), mimetype='application/json')


@facturacion_bp.route('/pagosOperadores', methods=['GET'])
def pagos_operadores():
    form = pagosOperadoresForm()
    user = current_user
    
    return render_template('pagosOperadores.html', User=user, form=form)


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
    programacion = programacionModel.query.filter_by(guia=form.guia.data).first()
    current_app.debug(f"Programación encontrada: {programacion}")
    tipo_operador = programacion.operador_rel.tipo if programacion and programacion.operador_rel else None
    current_app.debug(f"Tipo de operador: {tipo_operador}")
    tarifas_clientes = tarifasModel.query.filter_by(codigo=programacion.codigo_tarifa).first()
    tarifa_cliente_id = tarifas_clientes.id if tarifas_clientes else None
    tarifas_operador = tarifasOperadoresModel.query.filter_by(codigo=tarifa_cliente_id, tipo=tipo_operador).first()
    current_app.debug(f"Tarifas Operador encontradas: {tarifas_operador}")
    recargo_vehiculo = recargoVehiculosModel.query.filter_by(cliente=form.empresa.data.id, vehiculo=form.vehiculo.data.id).first()
    current_app.debug(f"Recargo de vehículo encontrado: {recargo_vehiculo}")
    

    if not tarifas_clientes:
        raise ValueError("No se encontraron tarifas para Clientes con el código proporcionado.")

    if not tarifas_operador:
        raise ValueError("No se encontraron tarifas para Operador con la ruta proporcionada.")

    if not recargo_vehiculo:
        raise ValueError("No se encontró un recargo de vehículo para el cliente proporcionado.")
    
    if not programacion:
        raise ValueError("No se encontró una programación con la guía proporcionada.")
    
    costo_vehiculo = recargo_vehiculo.recargo/100 if recargo_vehiculo.recargo else 0
    costo_desvios = tarifas_operador.desvios if tarifas_operador.desvios else 0
    costo_espera = tarifas_operador.espera if tarifas_operador.espera else 0
    costo_base = tarifas_operador.base if tarifas_operador.base else 0
    costo_especial = tarifas_clientes.especial if tarifas_clientes.especial else 0
    costo_distancia = tarifas_clientes.tarifa_km 

    total_desvios = form.desvios.data * costo_desvios
    total_espera = form.tiempo_espera.data * costo_espera
    total_distancia = form.distancia.data * costo_distancia if form.distancia.data else 0

    costo_total = costo_base + total_desvios + total_espera + total_distancia
    costo_total += costo_total*costo_vehiculo
    costo_total += costo_total*costo_especial/100
    
    current_app.debug("programacion:", programacion.id)
    current_app.debug("tarifas_operador:", tarifas_operador.id)
    current_app.debug("recargo_vehiculo:", recargo_vehiculo.id)
    
    nuevo_pago = {
        "programacion":  programacion.id,
        "tarifas_operador": tarifas_operador.id,
        "recargo_vehiculo": recargo_vehiculo.id,
        "total_desvios": total_desvios,
        "total_espera": total_espera,
        "costo_total": costo_total
    }
    
 
    try:
        # from app.facturacion.models import pagosOperadoresModel
        pago = pagosOperadoresModel(**nuevo_pago)
        db.session.add(pago)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.debug(f"Error al crear el pago: {str(e)}")
        raise ValueError(f"Error al crear el pago")

@facturacion_bp.route('/pagosOperadores', methods=['DELETE'])
def pagosOperadores_delete():
    form = pagosOperadoresForm()
    user = current_user

    id_pago = request.json.get('id')
    current_app.debug("ID de pago a eliminar:", id_pago)

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
        current_app.debug("Error al eliminar el pago:", e)
        return jsonify(success=False, mensaje='No se pudo eliminar el pago.', error=str(e))

@facturacion_bp.route('/pagosOperadores', methods=['PUT'])
def pagosOperadores_update():
    form = pagosOperadoresForm()
    user = current_user
        
    if form.validate_on_submit():
        form_data = form.data

        pago = pagosOperadoresModel.query.filter_by(id=form_data['id']).first()

        if not pago:
            raise ValueError("Pago no encontrado.")

        # Actualizar los campos del pago
        try:
            pago.total_espera = "--"
            pago.total_desvios = "--"
            pago.costo_total = form_data['costo_total']

            db.session.commit()
            return jsonify(success=True, mensaje="Pago actualizado exitosamente.", icon='success')
        except Exception as e:
            db.session.rollback()
            return jsonify(success=False, mensaje=f"Error al actualizar el pago: {str(e)}", icon='danger')

    return render_template('pagosOperadores.html', User=user, form=form)