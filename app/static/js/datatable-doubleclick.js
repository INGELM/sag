/**
 * Funcionalidad de doble click para DataTables
 */

function agregarDobleClick(tablaId, callback) {
    let clickTimer = null;
    
    $(`${tablaId} tbody`).on('click', 'tr', function (e) {
        // Evitar que se ejecute si se hace click en botones o enlaces
        if ($(e.target).is('button, a, i, .btn, .bx')) {
            return;
        }
        
        var $this = $(this);
        var table = $(tablaId).DataTable();
        var data = table.row(this).data();
        
        if (!data) return;
        
        if (clickTimer === null) {
            clickTimer = setTimeout(function() {
                // Click simple - mantener funcionalidad de selección existente
                if (table.select && !$this.hasClass('selected')) {
                    // table.rows().deselect();
                    table.row($this).deselect();
                }
                clickTimer = null;
            }, 250);
        } else {
            // Doble click detectado
            clearTimeout(clickTimer);
            clickTimer = null;
            
            // Ejecutar callback personalizado
            if (typeof callback === 'function') {
                callback(data, $this);
            } else {
                // Acción por defecto: abrir formulario de edición
                //console.log('Doble click en fila:', data);
                editar(data.id);
            }
        }
    });
}

// Función para agregar doble click con acción de editar
function agregarDobleClickEditar(tablaId) {
    agregarDobleClick(tablaId, function(data, fila) {
        //console.log('Editando registro:', data.id);
        editar(data.id);
    });
}

// Función para agregar doble click con acción personalizada
function agregarDobleClickPersonalizado(tablaId, accion) {
    agregarDobleClick(tablaId, function(data, fila) {
        switch(accion) {
            case 'ver_detalle':
                // Redirigir a página de detalle
                const modulo = window.modulo || '';
                const modelo = window.modelo || '';
                const url = modulo ? `/${modulo}/${modelo}/detalle/${data.id}` : `/${modelo}/detalle/${data.id}`;
                window.location.href = url;
                break;
                
            case 'abrir_modal':
                // Abrir modal con información
                mostrarModalDetalle(data);
                break;
                
            case 'copiar_registro':
                // Copiar registro para crear uno nuevo
                copiarRegistro(data);
                break;
                
            default:
                editar(data.id);
        }
    });
}

// Función auxiliar para mostrar modal de detalle
function mostrarModalDetalle(data) {
    // Formatear fecha y hora
    // const formatearFecha = (fecha) => {
    //     if (!fecha) return '';
    //     return new Date(fecha).toLocaleDateString('es-ES', {
    //         weekday: 'long',
    //         year: 'numeric',
    //         month: 'long',
    //         day: 'numeric'
    //     });
    // };

    //console.log(data.Ciudad_Origen)

    const formatearHora = (hora) => {
        if (!hora) return '';
        return hora.substring(0, 5); // HH:MM
    };
    let iconoViaje = data.hora_retorno ? ' ⇄ ' : ' → ';
    // Construir el contenido del modal
    let contenido = `
        <div class="card border-0 shadow-sm">
            <div class="card-body p-4">
                <!-- Encabezado Principal -->
                <div class="text-center mb-4">
                    <h4 class="fw-bold text-primary mb-2">${data.empresa || 'Empresa'}</h4>
                    <div class="d-flex justify-content-center align-items-center">
                        <span class="badge bg-light text-dark fs-6 px-3 py-2">
                            ${data.Ciudad_Origen || 'Origen'}
                            ${iconoViaje}
                            ${data.Ciudad_Destino || 'Destino'}
                        </span>
                    </div>
                </div>

                <!-- Información de Fecha y Hora -->
                <div class="row mb-4 text-center">
                    <div class="col-md-4">
                        <div class="p-1 bg-light rounded">
                            <i class="bx bx-calendar text-primary bx-sm"></i>
                            <div class="mt-2">
                                <small class="text-muted">Fecha</small>
                                <div class="fw-semibold">${data.fecha_salida}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-1 bg-light rounded">
                            <i class='bx  bx-clock-7 text-primary bx-sm'></i>
                            <div class="mt-2">
                                <small class="text-muted">Salida</small>
                                <div class="fw-semibold">${formatearHora(data.hora_salida)}</div>
                            </div>
                        </div>
                    </div>
                    ${data.hora_retorno ? `
                    <div class="col-md-4">
                        <div class="p-1 bg-light rounded">
                            <i class='bx bx-clock-4 text-primary bx-sm'></i>
                            <div class="mt-2">
                                <small class="text-muted">Retorno</small>
                                <div class="fw-semibold">${formatearHora(data.hora_retorno)}</div>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>

                <hr class="my-4">
    `;

    // Sección de Pasajeros
    if (data.pasajeros && Array.isArray(data.pasajeros) && data.pasajeros.length > 0) {
        contenido += `
                <!-- Pasajeros -->
                <div class="mb-4">
                    <h6 class="text-primary fw-bold mb-3">
                        <i class="bx bx-user me-2"></i>Pasajeros
                    </h6>
        `;
        
        data.pasajeros.forEach((pasajero, index) => {
            const direccionOrigen = Array.isArray(data.direccion_origen) ? data.direccion_origen[index] || '' : data.direccion_origen || '';
            //console.log(direccionOrigen)
            //console.log(data.direccion_origen)
            
            const direccionDestino = Array.isArray(data.direccion_destino) ? data.direccion_destino[index] || '' : data.direccion_destino || '';
            //console.log(direccionDestino)
            //console.log(data.direccion_destino)

            contenido += `
                    <div class="border rounded p-3 mb-3 bg-light">
                        <div class="row align-items-center">
                            <div class="col-md-6">
                                <div class="fw-semibold">${pasajero.nombre || pasajero}</div>
                                <small class="text-muted">${pasajero.telefono || ''}</small>
                            </div>
                            <div class="col-md-6">
                                <div class="d-flex align-items-center justify-content-end">
                                    <div class="text-end">
                                        <div class="small text-muted">Origen → Destino</div>
                                        <div class="small">${direccionOrigen} → ${direccionDestino}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
            `;
        });
        
        contenido += `</div>`;
    }

    // Sección de Detalles del Servicio
    contenido += `
                <!-- Detalles del Servicio -->
                <div class="mb-4">
                    <h6 class="text-primary fw-bold mb-3">
                        <i class='bx  bx-info-circle text-primary'></i> Detalles del Servicio
                    </h6>
                    <div class="row">
                        ${data.operador ? `
                        <div class="col-md-4 mb-2">
                            <div class="d-flex align-items-center">
                                <i class="bx bx-user-circle text-muted me-2"></i>
                                <div>
                                    <small class="text-muted">Operador</small>
                                    <div class="fw-semibold">${data.operador[0].nombre} </div>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                        ${data.vehiculo ? `
                        <div class="col-md-4 mb-2">
                            <div class="d-flex align-items-center">
                                <i class="bx bx-car text-muted me-2"></i>
                                <div>
                                    <small class="text-muted">Vehículo</small>
                                    <div class="fw-semibold">${data.vehiculo}</div>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                        ${data.status ? `
                        <div class="col-md-4 mb-2">
                            <div class="d-flex align-items-center">
                                <i class="bx bx-info-circle text-muted me-2"></i>
                                <div>
                                    <small class="text-muted">Estado</small>
                                    <div class="fw-semibold">
                                        <span class="badge ${
                                            data.status.toLowerCase() === 'finalizado' ? 'bg-success' :
                                            data.status.toLowerCase() === 'programado' ? 'bg-warning' :
                                            data.status.toLowerCase() === 'pendiente' ? 'bg-danger' : 'bg-secondary'
                                        }">${data.status}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
    `;

    // Información adicional (Guía, Workflow, etc.)
    // if (data.guia || data.workflow || data.distancia) {
    //     contenido += `
    //             <div class="row mb-4">
    //                 ${data.guia ? `
    //                 <div class="col-md-4 mb-2">
    //                     <div class="text-center p-2 bg-primary bg-opacity-10 rounded">
    //                         <small class="text-muted">Guía</small>
    //                         <div class="fw-bold text-primary">${data.guia}</div>
    //                     </div>
    //                 </div>
    //                 ` : ''}
    //                 ${data.workflow ? `
    //                 <div class="col-md-4 mb-2">
    //                     <div class="text-center p-2 bg-info bg-opacity-10 rounded">
    //                         <small class="text-muted">Workflow</small>
    //                         <div class="fw-bold text-info">${data.workflow}</div>
    //                     </div>
    //                 </div>
    //                 ` : ''}
    //                 ${data.distancia ? `
    //                 <div class="col-md-4 mb-2">
    //                     <div class="text-center p-2 bg-warning bg-opacity-10 rounded">
    //                         <small class="text-muted">Distancia</small>
    //                         <div class="fw-bold text-warning">${data.distancia} km</div>
    //                     </div>
    //                 </div>
    //                 ` : ''}
    //             </div>
    //     `;
    // }

    // Sección de Observaciones
    if (data.observaciones) {
        contenido += `
                <!-- Observaciones -->
                <div class="mb-3">
                    <h6 class="text-primary fw-bold mb-3">
                        <i class="bx bx-note me-2"></i>Observaciones
                    </h6>
                    <div class="p-3 bg-light rounded">
                        <p class="mb-0 text-muted">${data.observaciones}</p>
                    </div>
                </div>
        `;
    }

    contenido += `
            </div>
        </div>
    `;

    // Determinar el título del modal
    let titulo = 'Detalle del Viaje <hr class="mt-4 mb-0">';
    // if (data.guia) titulo = `Programación - Guía: ${data.guia}`;
    // else if (data.factura) titulo = `Factura: ${data.factura}`;
    // else if (data.numero_factura) titulo = `Factura: ${data.numero_factura}`;
    
    Swal.fire({
        title: titulo,
        html: contenido,
        width: '800px',
        showCancelButton: true,
        // showDenyButton: true,
        showCloseButton: true,
        confirmButtonText: '<i class="bx bx-edit me-1"></i>Editar',
        // denyButtonText: '<i class="bx bx-trash me-1"></i>Eliminar',
        cancelButtonText: '<i class="bx bx-paper-plane me-1"></i>Enviar',
        closeButtonAriaLabel: 'Cerrar',
        confirmButtonColor: '#007bff',
        denyButtonColor: '#dc3545',
        cancelButtonColor: '#28a745',
        customClass: {
            popup: 'swal-compact-modal',
            htmlContainer: 'text-start p-0',
            closeButton: 'swal-close-button-custom'
        },
        didOpen: () => {
            // Agregar estilos personalizados
            const style = document.createElement('style');
            style.textContent = `
                .swal-compact-modal .swal2-html-container {
                    max-height: 75vh;
                    overflow-y: auto;
                    padding: 0 !important;
                }
                .swal-compact-modal .card {
                    border: none !important;
                }
                .swal-compact-modal .bg-light {
                    background-color: #f8f9fa !important;
                }
                .swal-compact-modal .text-primary {
                    color: #0d6efd !important;
                }
                .swal-compact-modal .border {
                    border: 1px solid #dee2e6 !important;
                }
                .swal-compact-modal .shadow-sm {
                    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
                }
            `;
            document.head.appendChild(style);
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // Editar registro
            editar(data.id);
        } else if (result.isDenied) {
            // Confirmar eliminación
            Swal.fire({
                title: '¿Estás seguro?',
                text: "Esta acción no se puede deshacer",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: '<i class="bx bx-trash me-1"></i>Sí, eliminar',
                cancelButtonText: '<i class="bx bx-x me-1"></i>Cancelar'
            }).then((deleteResult) => {
                if (deleteResult.isConfirmed) {
                    //console.log(`🆔 Registro ID: ${data.id} | Modelo: ${window.modelo}`);
                    eliminarSeleccionados(data.id, window.modelo);
                }
            });
        } else if (result.isDismissed && result.dismiss === Swal.DismissReason.cancel) {
            // Botón "Enviar" presionado
            // enviarRegistro(data);
            enviarWA(data)
            // alert("Funcion enviar registro no implementada aún")
        }
        // Si se presiona el botón X (cerrar) o se hace clic fuera del modal, no se ejecuta ninguna acción
    });
}

function enviarWA(data){
    let jsonData = JSON.stringify(data)
    console.log(jsonData)
    console.log(data)
    let URL = "/wa/send-programacion"
    //console.log(URL)

    $.ajax({
        type: "POST",
        url: URL,
        data: jsonData,
        contentType: "application/json",
        success: function (response) {
            if (response.success){
                Swal.fire({
                    icon: 'success',
                    title: "Operación Exitosa",
                    text: response.mensaje,
                    timer: 3500,
                    timerProgressBar: true

                })
            }
            else {
                Swal.fire({
                    icon: 'error',
                    title: "Mensaje no enviado",
                    text: response.mensaje,
                    timer: 3500,
                    timerProgressBar: true
                })
            }

        }
    });

}




// Función auxiliar para copiar registro
function copiarRegistro(data) {
    // Llenar formulario con los datos existentes (excluyendo ID)
    Object.keys(data).forEach(key => {
        if (key !== 'id' && !key.endsWith('_rel')) {
            const $campo = $(`#${window.modelo}Form [name="${key}"]`);
            if ($campo.length) {
                if ($campo[0].selectize) {
                    $campo[0].selectize.setValue(data[key], true);
                } else {
                    $campo.val(data[key]);
                }
                
                // Función para manejar el envío de registros
                // function enviarRegistro(data) {
                //     Swal.fire({
                //         title: '¿Enviar registro?',
                //         text: `¿Estás seguro de que deseas enviar el registro con ID: ${data.id}?`,
                //         icon: 'question',
                //         showCancelButton: true,
                //         confirmButtonColor: '#28a745',
                //         cancelButtonColor: '#6c757d',
                //         confirmButtonText: '<i class="bx bx-paper-plane me-1"></i>Sí, enviar',
                //         cancelButtonText: '<i class="bx bx-x me-1"></i>Cancelar',
                //         showLoaderOnConfirm: true,
                //         preConfirm: () => {
                //             // Aquí puedes personalizar la URL y los datos según tu aplicación
                //             const url = window.modulo !== "" ? `/${window.modulo}/${window.modelo}/enviar` : `/${window.modelo}/enviar`;
                            
                //             return fetch(url, {
                //                 method: 'POST',
                //                 headers: {
                //                     'Content-Type': 'application/json',
                //                 },
                //                 body: JSON.stringify({
                //                     id: data.id,
                //                     // Agregar otros datos necesarios para el envío
                //                     ...data
                //                 })
                //             })
                //             .then(response => {
                //                 if (!response.ok) {
                //                     throw new Error('Error en la respuesta del servidor');
                //                 }
                //                 return response.json();
                //             })
                //             .then(result => {
                //                 if (!result.success) {
                //                     throw new Error(result.mensaje || 'Error al enviar el registro');
                //                 }
                //                 return result;
                //             })
                //             .catch(error => {
                //                 Swal.showValidationMessage(`Error: ${error.message}`);
                //             });
                //         },
                //         allowOutsideClick: () => !Swal.isLoading()
                //     }).then((result) => {
                //         if (result.isConfirmed && result.value) {
                //             Swal.fire({
                //                 title: '¡Enviado!',
                //                 text: result.value.mensaje || 'El registro ha sido enviado correctamente',
                //                 icon: 'success',
                //                 timer: 3000,
                //                 timerProgressBar: true,
                //                 confirmButtonText: 'Aceptar'
                //             }).then(() => {
                //                 // Opcional: recargar la tabla o actualizar el estado
                //                 if (typeof location !== 'undefined') {
                //                     location.reload();
                //                 }
                //             });
                //         }
                //     });
                // }
            }
        }
    });
    
    // Mostrar formulario en modo crear
    $(".formulario").removeClass("visually-hidden");
    $(".tituloForm").text(`Copiar ${window.modelo.charAt(0).toUpperCase() + window.modelo.slice(1)}`);
    $(".botonForm").text('Registrar Copia');
    $(`#${window.modelo}Form`).attr('method', 'POST');
    
    Swal.fire({
        title: 'Registro Copiado',
        text: 'Los datos han sido copiados al formulario. Modifica lo que necesites y guarda.',
        icon: 'info',
        timer: 3000,
        timerProgressBar: true
    });
}