/**
 * Funcionalidad de doble click para DataTables
 * Agregar este archivo después de app.js
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
                    table.rows().deselect();
                    table.row($this).select();
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
                console.log('Doble click en fila:', data);
                editar(data.id);
            }
        }
    });
}

// Función para agregar doble click con acción de editar
function agregarDobleClickEditar(tablaId) {
    agregarDobleClick(tablaId, function(data, fila) {
        console.log('Editando registro:', data.id);
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
    // Categorizar los campos por secciones
    const secciones = {
        'Información General': ['id', 'fecha_salida', 'hora_salida', 'hora_retorno', 'guia', 'workflow', 'status'],
        'Cliente y Pasajeros': ['empresa', 'pasajeros', 'operador'],
        'Ubicación': ['origen', 'destino', 'direccion_origen', 'direccion_destino', 'distancia'],
        'Vehículo': ['vehiculo', 'desvios', 'tiempo_espera'],
        'Financiero': ['total_', 'costo_total', 'factura', 'numero_factura'],
        'Observaciones': ['observaciones', 'notas', 'comentarios']
    };

    const iconos = {
        'Información General': 'bx bx-info-circle',
        'Cliente y Pasajeros': 'bx bx-user-circle',
        'Ubicación': 'bx bx-map',
        'Vehículo': 'bx bx-car',
        'Financiero': 'bx bx-dollar-circle',
        'Observaciones': 'bx bx-note'
    };

    const colores = {
        'Información General': 'primary',
        'Cliente y Pasajeros': 'success',
        'Ubicación': 'warning',
        'Vehículo': 'info',
        'Financiero': 'danger',
        'Observaciones': 'secondary'
    };

    let contenido = '<div class="container-fluid p-0">';
    
    // Crear secciones organizadas
    Object.keys(secciones).forEach(seccion => {
        const camposSeccion = secciones[seccion];
        const camposExistentes = camposSeccion.filter(campo =>
            data.hasOwnProperty(campo) && data[campo] !== null && data[campo] !== undefined && data[campo] !== ''
        );
        
        if (camposExistentes.length > 0) {
            const color = colores[seccion];
            const icono = iconos[seccion];
            
            contenido += `
                <div class="card mb-3 border-${color}">
                    <div class="card-header bg-${color} text-white d-flex align-items-center">
                        <i class="${icono} me-2"></i>
                        <h6 class="mb-0 fw-bold">${seccion}</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
            `;
            
            camposExistentes.forEach(campo => {
                let valor = data[campo];
                let etiqueta = campo.charAt(0).toUpperCase() + campo.slice(1).replace('_', ' ');
                
                // Formatear valores especiales
                if (campo.includes('fecha')) {
                    valor = new Date(valor).toLocaleDateString('es-ES');
                } else if (campo.includes('total') || campo.includes('costo')) {
                    valor = typeof valor === 'number' ? `$${valor.toFixed(2)}` : valor;
                } else if (Array.isArray(valor)) {
                    valor = valor.join(', ');
                } else if (typeof valor === 'object' && valor !== null) {
                    valor = JSON.stringify(valor);
                }
                
                // Determinar el tamaño de columna basado en el contenido
                const colSize = valor && valor.toString().length > 50 ? 'col-12' : 'col-md-6';
                
                contenido += `
                    <div class="${colSize} mb-2">
                        <div class="d-flex align-items-start">
                            <span class="badge bg-light text-dark me-2 text-wrap" style="min-width: 120px;">
                                ${etiqueta}
                            </span>
                            <span class="text-muted flex-grow-1">${valor || 'N/A'}</span>
                        </div>
                    </div>
                `;
            });
            
            contenido += `
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    contenido += '</div>';
    
    // Determinar el título basado en el tipo de registro
    let titulo = 'Detalle del Registro';
    if (data.guia) titulo = `Programación - Guía: ${data.guia}`;
    else if (data.factura) titulo = `Factura: ${data.factura}`;
    else if (data.numero_factura) titulo = `Factura: ${data.numero_factura}`;
    
    Swal.fire({
        title: titulo,
        html: contenido,
        width: '900px',
        showCancelButton: true,
        showDenyButton: true,
        confirmButtonText: '<i class="bx bx-edit me-1"></i>Editar',
        denyButtonText: '<i class="bx bx-trash me-1"></i>Eliminar',
        cancelButtonText: '<i class="bx bx-x me-1"></i>Cerrar',
        confirmButtonColor: '#007bff',
        denyButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        customClass: {
            popup: 'swal-wide',
            htmlContainer: 'text-start'
        },
        didOpen: () => {
            // Agregar estilos personalizados
            const style = document.createElement('style');
            style.textContent = `
                .swal-wide .swal2-html-container {
                    max-height: 70vh;
                    overflow-y: auto;
                }
                .swal-wide .card {
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .swal-wide .badge {
                    font-size: 0.75rem;
                    font-weight: 600;
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
                    eliminar(data.id, window.modelo);
                }
            });
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