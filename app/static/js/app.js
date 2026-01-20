$(document).ready(function () {
    // ✅ SOLUCIÓN: Configurar jQuery para enviar el token CSRF en todas las peticiones AJAX
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            // Solo agregar el token para métodos que lo requieren
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                const csrfToken = $('input[name="csrf_token"]').val();
                if (csrfToken) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    // //console.log("🔍 DEBUG CSRF - Token agregado al header:", csrfToken);
                }
            }
        }
    });

    $('#agregarFacturaModal').on('click', function (e) {
        e.stopPropagation(); // Evita que el clic se propague y afecte la selección
    });

    $('#guardarNoFacturaBtn').click(function (e) {
        e.preventDefault();
        const form = $('#agregarFacturaForm');
        const dt = $('#facturasClientesTable').DataTable();
        const selectedRows = dt.rows({ selected: true });
        const selectedIds = selectedRows.data().toArray().map(row => row.id);
        //console.log("IDs seleccionados:", selectedIds);
        //console.log("Datos del formulario:", form.serializeArray());
        //console.log("Numero de factura", $('#numero-factura').val());

        const data = {
            factura: $('#numero-factura').val(),
            ids: selectedIds
        };

        //console.log("Datos a enviar:", data);
        
        $.ajax({
            url: '/facturacion/facturasClientes/agregar-factura',
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function (response) {
                if (response.success) {
                    Swal.fire({
                        title: 'Éxito',
                        text: response.mensaje,
                        icon: 'success',
                        timer: 2000,
                        timerProgressBar: true,
                        confirmButtonText: 'Aceptar'
                    }).then(() => {
                        $('#agregarFacturaModal').modal('hide');
                        // Limpiar el campo de número de factura
                        $('#numero-factura').val('');
                        // Deseleccionar las filas
                        dt.rows({ selected: true }).deselect();
                        // Recargar solo la tabla
                        cargarTabla2(window.modelo, window.modulo, "", []);
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: response.mensaje,
                        icon: 'error',
                        // confirmButtonText: 'Aceptar',
                        timer: 2000,
                        timerProgressBar: true
                    });
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                let mensaje = jqXHR.responseJSON?.mensaje || jqXHR.statusText || "Error al agregar el número de factura";
                Swal.fire({
                    title: 'Falló la operación',
                    text: mensaje,
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            }
        });
        
        
    });
});




const selectizeConfig = {
    plugins: ['remove_button'],
    allowEmptyOption: false,
    placeholder: 'Seleccione',
    valueField: 'id',
    labelField: 'text',
    sortField: 'text',
    searchField: ['text', 'nombres'],
    render: {
        option: function (item, escape) {
            return `<div>${escape(item.text)}</div>`;
        }
    }
};

function cargarSelectize(url, empresaId, selectize) {
    if (empresaId && empresaId !== "__None" && empresaId !== null && empresaId !== undefined) {
        //console.log("Consultando para la empresa:", empresaId);
        fetch(url)
            .then(response => response.json())
            .then(response => {
                //console.log("Datos consultados:", response);
                selectize.clear();
                selectize.clearOptions();
                if (response.success) {
                    response.data.forEach(function (item) {
                        item.nombres = item.nombres.title || item.nombre || item.tipo || item.codigo;
                       // console.log(`Agregando opción: ${item.nombres}`);
                        selectize.addOption({
                            id: item.id,
                            text: item.nombres,
                        });
                    });
                } else {
                    selectize.addOption({
                        id: 0,
                        text: response.mensaje || 'No se encontraron resultados'
                    });
                }
                selectize.refreshOptions(false);
            })
    } else {
        //console.log("No se ha seleccionado una empresa válida.");
        selectize.clear();
        selectize.clearOptions();
        // selectize.addOption({
        //     id: 0,
        //     text: 'Seleccione una empresa'
        // });
    }
}

// Función de ordenamiento personalizada para fechas en formato DD-MM-YYYY
$.fn.dataTable.ext.type.order['date-dd-mm-yyyy-pre'] = function (data) {
    if (!data || data === '') {
        return 0;
    }
    var dateParts = data.split('-');
    if (dateParts.length === 3) {
        // Convertir DD-MM-YYYY a timestamp para ordenamiento correcto
        var day = parseInt(dateParts[0], 10);
        var month = parseInt(dateParts[1], 10) - 1; // Los meses en JS van de 0-11
        var year = parseInt(dateParts[2], 10);
        return new Date(year, month, day).getTime();
    }
    return 0;
};

$.extend(true, $.fn.DataTable.defaults, {
    language: {

        url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-MX.json ',
        search: "",
        searchPlaceholder: "Buscar...",
        info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
        infoEmpty: "No hay registros disponibles",
        emptyTable: "No hay datos disponibles en la tabla",
        zeroRecords: "No se encontraron registros coincidentes"
        
    },
    lengthChange: false,
    ordering: true,
    responsive: true,
    // scrollX: true,
    columnDefs: [
        {
            targets: [0],
            visible: false,
            searchable: false
        }
    ],
});

// Filtro por rango de fechas
$.fn.dataTable.ext.search.push(
    function (_settings, data, _dataIndex) {
        var min = $('#f-desde').val();
        var max = $('#f-hasta').val();
        var fecha = data[1];

        if (!fecha) return true;

        // Si la celda no luce como fecha (ej: códigos de tarifas), no aplicar este filtro
        var fechaParts = fecha.split('-');
        if (fechaParts.length < 3) {
            return true;
        }

        // Función auxiliar para parsear fechas en formatos DD-MM-YYYY o YYYY-MM-DD y establecer inicio/fin del día
        function parseDateInput(value, endOfDay) {
            if (!value) return null;
            var parts = value.split('-');
            var d;
            if (parts.length === 3) {
                if (parts[0].length === 4) {
                    // YYYY-MM-DD
                    var y = parseInt(parts[0], 10);
                    var m = parseInt(parts[1], 10) - 1;
                    var day = parseInt(parts[2], 10);
                    d = new Date(y, m, day);
                } else {
                    // DD-MM-YYYY
                    var day2 = parseInt(parts[0], 10);
                    var m2 = parseInt(parts[1], 10) - 1;
                    var y2 = parseInt(parts[2], 10);
                    d = new Date(y2, m2, day2);
                }
            } else {
                d = new Date(value);
                if (isNaN(d)) return null;
            }
            if (endOfDay) {
                d.setHours(23, 59, 59, 999);
            } else {
                d.setHours(0, 0, 0, 0);
            }
            return d;
        }

        var fechaData = new Date(fechaParts[2], fechaParts[1] - 1, fechaParts[0]);
        if (isNaN(fechaData.getTime())) {
            return true;
        }
        fechaData.setHours(12, 0, 0, 0); // Evitar problemas por zona horaria usando hora intermedia

        var minDate = parseDateInput(min, false);
        var maxDate = parseDateInput(max, true);

        if (
            (!minDate || fechaData >= minDate) &&
            (!maxDate || fechaData <= maxDate)
        ) {
            return true;
        }
        return false;
    }
);

$('#f-filtrar').on('click', function () {
    $(window.tablaId).DataTable().draw();
    //console.log("Tabla filtrada: ", window.tablaId);
    //console.log("Filtro aplicado: desde", $('#f-desde').val(), "hasta", $('#f-hasta').val());
});

$('#f-limpiar').on('click', function () {
    $('#f-desde').val('');
    $('#f-hasta').val('');
    $(window.tablaId).DataTable().draw();
});

let tablaInstancia = null;
let tasaGlobal = 1;
window.filtroActual = null; // Variable global para mantener el filtro actual

async function baseTablas(modelo, modulo = "", empresa_id = "") {
    //console.log("Cargando tabla para el modelo:", modelo);
    //console.log("Módulo:", modulo);
    //console.log("Empresa ID:", empresa_id);

    const basePath = (modulo && modulo !== modelo) ? `/${modulo}/${modelo}` : `/${modelo}`;
    var url = `${basePath}/all`;
    if (empresa_id) {
        url = `${modelo}?cliente=${empresa_id}`;
    }

    //console.log("URL de la tabla:", url);

    window.modulo = modulo;
    window.modelo = modelo;

    var tabla = `#${modelo}Table`;

    if ($(tabla).hasClass('dataTable')) {
        $(tabla).DataTable().clear().destroy();
    }

    Swal.fire({
        title: 'Actualizando...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    if (modelo === 'facturasClientes' || modelo === 'pagosOperadores') {

        try {
            const responseTasa = await fetch("/tasa/all");
            const jsonTasa = await responseTasa.json();

            if (jsonTasa.success && jsonTasa.data.length > 0) {
                tasaGlobal = jsonTasa.data.at(-1)?.tasa || 1;
            } else {
                Swal.fire({
                    icon: 'warning',
                    title: 'Sin Tasa',
                    text: 'No se encontró una tasa válida para convertir montos.',
                    timer: 2000,
                    showConfirmButton: false
                });
            }
        } catch (error) {
            console.error("Error al obtener la tasa:", error);
        }
    }

    const response = await fetch(url);
    Swal.close();

    if (!response.ok) throw new Error("Error en la respuesta del servidor");

    const json = await response.json();

    if (!json.success) {
        Swal.fire({
            title: 'Error',
            text: json.mensaje || "Ocurrió un error al cargar los datos",
            icon: 'error',
            confirmButtonText: 'Aceptar',
            timer: 5000,
            timerProgressBar: true,
        });
        return Promise.reject("Datos no cargados");
    }

    // Validar si hay datos antes de procesar columnas
    if (!json.data || json.data.length === 0) {
        //console.log("No hay datos disponibles para mostrar en la tabla");
        
        // Crear tabla vacía con mensaje
        if ($(tabla).hasClass('dataTable')) {
            $(tabla).DataTable().clear().destroy();
        }
        
        $(tabla).DataTable({
            data: [],
            columns: [{ data: null, defaultContent: '', title: 'Sin datos' }],
            language: {
                emptyTable: "No hay datos disponibles en la tabla"
            }
        });
        
        return Promise.resolve({
            tabla,
            columnas: [],
            columnDefs: [],
            jsonData: []
        });
    }

    const keys = Object.keys(json.data[0]);
    const columnas = keys.map((campo, index) => {
        const columna = {
            data: campo,
            title: campo.charAt(0).toUpperCase() + campo.slice(1).replace('_', ' '),
            render: function(data) {
                // Debug opcional (solo si necesitas)
                // //console.log(`Columna: ${campo}, Datos:`, data);
                
                // Manejo específico para pasajeros
                if (campo === 'pasajeros') {
                    if (Array.isArray(data)) {
                        const separador = modelo === 'programacion' ? ' /<br>' : '<br>';
                        return data.map(p => p.nombre).join(separador);
                    }
                    return data;
                }
                
                return data;
            }
        };
                
        // Aplicar tipo de ordenamiento personalizado para la columna de fecha (índice 1)
        if (index === 1) {
            columna.type = 'date-dd-mm-yyyy';
        }
        
        return columna;
    });

    if (modelo === 'facturasClientes' || modelo === 'pagosOperadores') {

        columnas.forEach(columna => {
            if (columna.data.startsWith('total') || columna.data.startsWith('costo')) {
                columna.render = function (data_3) {
                    const usarBs = localStorage.getItem('Bs') === 'true';
                    if (typeof data_3 === 'number' && usarBs) {
                        return (data_3 * tasaGlobal).toFixed(2);
                    }
                    return typeof data_3 === 'number' ? data_3.toFixed(2) : data_3;
                };
            }
        });

    }


    if (modelo === 'tarifas') {
        columnas.push({
            data: null,
            title: "",
            orderable: false,
            className: 'no-export',
            searchable: false,
            render: function (data_4, type, row) {
                var acciones = `<a href="/empleados/tarifasOperadores" title="Ver tarifas del operador">
                    <i id="oper" class="bx bxs-car" style="cursor: pointer; color:${row.color_rel};"></i>
                </a>`;
            return acciones;
            
            }
        });
    }
    const relColumnIndexes = keys
        .map((campo_1, idx) => campo_1.endsWith('_rel') ? idx : -1)
        .filter(idx_1 => idx_1 !== -1);
    relColumnIndexes.push(0);

    const columnDefs = [];
    if (relColumnIndexes.length > 0) {
        columnDefs.push({
            targets: relColumnIndexes,
            visible: false,
            searchable: false
        });
    }
    //console.log("JsonData:", json.data);
    return {
        tabla,
        columnas,
        columnDefs,
        jsonData: json.data
    };
}

function cargarTabla1(modelo, modulo = "", VisibleColumns = []) {
    // console.log("Cargando tabla con modelo:", modelo, "módulo:", modulo, "columnas visibles:", VisibleColumns);
    baseTablas(modelo, modulo).then(({ tabla, columnas, columnDefs, jsonData }) => {

    
        // Si se especifican columnas visibles, actualiza columnDefs
        let mobileColumnDefs = Array.isArray(columnDefs) ? [...columnDefs] : [];
        if (Array.isArray(VisibleColumns) && VisibleColumns.length > 0) {
            //console.log("Columnas visibles:", VisibleColumns);
            // Si columnDefs está vacío, agregamos un objeto por cada índice a ocultar
            if (mobileColumnDefs.length === 0) {
            mobileColumnDefs = [{
                targets: VisibleColumns,
                responsivePriority: 1,
            }];
            } else {
            // Si ya hay reglas, agregamos/ajustamos la visibilidad
            mobileColumnDefs.push({
                targets: VisibleColumns,
                responsivePriority: 1,
            });
            }
        }

        let AllColumnDefs = [columnDefs, ...mobileColumnDefs];

        $(tabla).DataTable({
            data: jsonData,
            columns: columnas,
            responsive: true,
            columnDefs: AllColumnDefs,
            paging: true,
            pageLength: 50,
            pagingType: "numbers",
            select: {
                style: 'multi',
                blurable: true,
                items: 'row',
                className: 'selected'
            },
            
            language: {
                search: "",
                // info: "",
                select: {
                    rows: {
                        _: "Has seleccionado %d filas",
                        0: "Haz clic en una fila para seleccionarla",
                        1: "1 fila seleccionada"
                    },
                    cells: {
                        _: "",
                        0: "",
                        1: ""
                    },
                    columns: {
                        _: "",
                        0: "",
                        1: ""
                    }
                }
            },
            layout: {

                topStart: {
                    buttons: modelo == 'tarifas' ? botonesEspeciales() : []
                },
           
                topEnd: {
                    buttons: [botonesAuxiliares()[1], botonesAuxiliares()[2]],
                    search: {
                        
                        // Aquí puedes personalizar la búsqueda
                    }
                }
            }
        });
    }).catch(err => {
        console.error("Error al cargar la tabla:", err);
    });
}



function cargarTabla2(modelo, modulo = "", empresa_id = "", VisibleColumns = []) {
    console.log("Cargando tabla con modelo:", modelo, "módulo:", modulo, "empresa_id:", empresa_id, "columnas visibles:", VisibleColumns);
    baseTablas(modelo, modulo, empresa_id).then(({ tabla, columnas, columnDefs, jsonData }) => {
        // Configuración base de DataTable

         // Si se especifican columnas visibles, actualiza columnDefs
        let mobileColumnDefs = Array.isArray(columnDefs) ? [...columnDefs] : [];
        if (Array.isArray(VisibleColumns) && VisibleColumns.length > 0) {
            //console.log("Columnas visibles:", VisibleColumns);
            // Si columnDefs está vacío, agregamos un objeto por cada índice a ocultar
            if (mobileColumnDefs.length === 0) {
            mobileColumnDefs = [{
                targets: VisibleColumns,
                responsivePriority: 1,
            }];
            } else {
            // Si ya hay reglas, agregamos/ajustamos la visibilidad
            mobileColumnDefs.push({
                targets: VisibleColumns,
                responsivePriority: 1,
            });
            }
        }

        let AllColumnDefs = [columnDefs, ...mobileColumnDefs];

        let config = {};

        // Configuración diferente para programacion (server-side processing)
        if (modelo === 'programacion') {
            config = {
                serverSide: true,
                ajax: {
                    url: '/programacion/get_data',
                    type: 'GET',
                    data: function(d) {
                        // Agregar filtro adicional si existe
                        if (window.filtroActual) {
                            d.filtro = window.filtroActual;
                        }
                        // Enviar rango de fechas al servidor para habilitar el filtrado server-side
                        d.fecha_desde = $('#f-desde').val();
                        d.fecha_hasta = $('#f-hasta').val();
                    }
                },
                columns: columnas,
                responsive: true,
                columnDefs: AllColumnDefs,
                paging: true,
                pageLength: 50,
                select: {
                    style: 'multi',
                    blurable: true,
                    items: 'row',
                    className: 'selected'
                },
                language: {
                    search: "",
                    select: {
                        rows: {
                            _: "Has seleccionado %d filas",
                            0: "Haz clic en una fila para seleccionarla",
                            1: "1 fila seleccionada"
                        },
                        cells: {
                            _: "",
                            0: "",
                            1: ""
                        },
                        columns: {
                            _: "",
                            0: "",
                            1: ""
                        }
                    }
                },
                order: [[1, 'desc']], // Ordenar por fecha de forma descendente
                pagingType: "numbers",
                layout: {
                    topStart: {
                        buttons: modelo === 'programacion' ? [getTablaBotones(), ...botonesEspeciales()] : [botonesEspeciales()]
                    },
                    topEnd: {
                        buttons: botonesAuxiliares(),
                        search: true
                    }
                },
                createdRow: function (row, data, dataIndex) {
                    // Validación temprana y normalización del status
                    if (!data || typeof data.status !== 'string' || !data.status.trim()) {
                        return; // Salida temprana si no hay status válido
                    }

                    const status = data.status.toLowerCase().trim();

                    // Mapeo de estados a clases CSS para mejor mantenibilidad
                    const statusClassMap = {
                        'finalizado': 'table-success text-success',
                        'facturado': 'table-success',
                        'pendiente': 'table-danger',
                        'por facturar': 'table-danger',
                        'programado': 'table-warning'
                    };

                    // Aplicar clase CSS si existe mapeo para el status
                    const cssClass = statusClassMap[status];
                    if (cssClass) {
                        $(row).addClass(cssClass);
                    }
                }
            };
        } else {
            // Configuración original para otras tablas
            config = {
                data: jsonData,
                columns: columnas,
                responsive: true,
                columnDefs: AllColumnDefs,
                paging: true,
                pageLength: 50,
                select: {
                    style: 'multi',
                    blurable: true,
                    items: 'row',
                    className: 'selected'
                },
                language: {
                    search: "",
                    select: {
                        rows: {
                            _: "Has seleccionado %d filas",
                            0: "Haz clic en una fila para seleccionarla",
                            1: "1 fila seleccionada"
                        },
                        cells: {
                            _: "",
                            0: "",
                            1: ""
                        },
                        columns: {
                            _: "",
                            0: "",
                            1: ""
                        }
                    }
                },
                order: [[1, 'desc']],
                pagingType: "numbers",
                layout: {
                    topStart: {
                        buttons: modelo === 'programacion' ? [getTablaBotones(), ...botonesEspeciales()] : [botonesEspeciales()]
                    },
                    topEnd: {
                        buttons: botonesAuxiliares(),
                        search: true
                    }
                },
                createdRow: function (row, data, dataIndex) {
                    // Validación temprana y normalización del status
                    if (!data || typeof data.status !== 'string' || !data.status.trim()) {
                        return; // Salida temprana si no hay status válido
                    }

                    const status = data.status.toLowerCase().trim();

                    // Mapeo de estados a clases CSS para mejor mantenibilidad
                    const statusClassMap = {
                        'finalizado': 'table-success text-success',
                        'facturado': 'table-success',
                        'pendiente': 'table-danger',
                        'por facturar': 'table-danger',
                        'programado': 'table-warning'
                    };

                    // Aplicar clase CSS si existe mapeo para el status
                    const cssClass = statusClassMap[status];
                    if (cssClass) {
                        $(row).addClass(cssClass);
                    }
                }
            };
        }


        // Agregar footerCallback solo para facturasClientes y pagosOperadores
        if (modelo === 'facturasClientes' || modelo === 'pagosOperadores') {
            // Encontrar la columna que contiene el total
            const totalColumnIndex = columnas.findIndex(col => col.data === 'total_');
            //console.log("Total Column Index:", totalColumnIndex);

            if (totalColumnIndex !== -1) {
                config.footerCallback = function (row, data, start, end, display) {
                    var api = this.api();
                    var total = 0;

                    // Sumar solo las filas visibles (filtradas/paginadas)
                    api.rows({ page: 'current', search: 'applied' }).data().each(function (row) {
                        const usarBs = localStorage.getItem('Bs') === 'true';
                        const value = parseFloat(usarBs ? row.total_ * tasaGlobal : row.total_) || 0;
                        total += value;
                    });

                    // Actualizar el footer

                    $(api.column(totalColumnIndex).footer()).html(
                        `<strong>${total.toFixed(2)}</strong>`
                    );
                    $(api.column(totalColumnIndex - 1).footer()).html(
                        `<strong>TOTAL:</strong>`
                    );
                };
            }
        }

        // Destruir tabla existente si ya está creada
        if ($(tabla).hasClass('dataTable')) {
            $(tabla).DataTable().clear().destroy();
            //console.log("Tabla destruida y reiniciada");
        }

        // Crear tabla DataTable
        tablaInstancia = $(tabla).DataTable(config);
    }).catch(err => {
        console.error("Error al cargar la tabla:", err);
    });
}

function botonBs() {
    return [
            {
                init: function (dt, node, config) {
                    const clase = localStorage.getItem('Bs') === 'true' ? 'btn btn-success btn-sm mb-1' : 'btn btn-outline-secondary btn-sm mb-1';
                    $(node).attr('class', clase);
                },
                text: 'Bolivares',
                action: function (e, dt, node, config) {
                    const current = localStorage.getItem('Bs') === 'true';
                    localStorage.setItem('Bs', !current);
                    $(node)
                        .toggleClass('btn-success', !current)
                        .toggleClass('btn-outline-secondary', current);
                    if (tablaInstancia) {
                        tablaInstancia.rows().invalidate().draw(false);
                    }
                }
            }
        ];
}

function crearTabla(url, tablaId, columnas) {
    //console.log("Creando tabla en:", tablaId, "y URL:", url);

    if ($(tablaId).hasClass('dataTable')) {
        $(tablaId).DataTable().clear().destroy();
    }
        $(tablaId).DataTable({
            ajax: {
                url: url,
                dataSrc: 'data'
            },
            columns: columnas,
            responsive: true,
            paging: true,
            searching: true,
            // VisibleColumns: [1,2,3,4,11,12,13,14],
            // targets: [1,2,3,4,11,12,13,14],
            // responsivePriority: 1,
            columnDefs: [
                {
                    // columns: columnas,
                    targets: [1,2,3,4,11,12,13,14,15],
                    visible: true,
                    responsivePriority: 1,
                },
            ],
            select: {
                layout: {
                    topStart: {
                        buttons: botonesEspeciales() 
                    },
                    topEnd: {
                        // buttons: botonBs(),
                        search: true
                    }

            
                }
            },
        });
}

function botonesAcciones(){
    return [
        {
            text: 'Eliminar',
            className: 'btn btn-danger btn-sm mb-1',
            action: function (e, dt, node, config) {
                eliminarSeleccionados(window.modelo);
            }
        },
        {
            text: 'Editar',
            className: 'btn  btn-sm mb-1',
            action: function (e, dt, node, config) {
                const selectedRows = dt.rows({ selected: true });
                if (selectedRows.count() === 1) {
                    const rowData = selectedRows.data().toArray()[0];
                    // const url = window.modulo !== "" ? `/${window.modulo}/${window.modelo}` : `/${window.modelo}`;
                    editar(rowData.id);
                } else {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Aviso',
                        text: 'Debe seleccionar un único registro para editar.',
                        timer: 2000
                    });
                }
            }
        },
        {
            text: "Cambiar a Por Facturar",
            className: 'btn btn-success btn-sm mb-1',
            action: function (e, dt, node, config) {
                const selectedRows = dt.rows({ selected: true });
                const selectedIds = selectedRows.data().toArray().map(row => row.id);
                //console.log("Filas seleccionadas:", selectedIds);
                if (selectedRows.count() === 0) {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Aviso',
                        text: 'Debe seleccionar al menos un registro para cambiar el estado.',
                        timer: 2000
                    });
                } else {
                    // //console.log(`Cambiar el estado de la fila con ID: ${selectedIds.join(", ")} a "Por Facturar"`);
                    const url = '/facturacion/facturasClientes/cambio-status';
                    $.ajax({
                        url: url,
                        type: 'PUT',
                        contentType: 'application/json',
                        data: JSON.stringify({ ids: selectedIds, nuevo_status: 'Por Facturar' }),
                        success: function (data) {
                            if (data.success) {
                                Swal.fire({
                                    title: 'Éxito',
                                    text: data.mensaje,
                                    icon: 'success',
                                    timer: 2000,
                                    timerProgressBar: true,
                                    confirmButtonText: 'Aceptar'
                                }).then(() => {
                                    dt.rows({ selected: true }).deselect();
                                    // Recargar solo la tabla
                                    cargarTabla2(window.modelo, window.modulo, "", [1, 2, 4, 5, 6, 7, 9, 10, 11, 19]);
                                });
                            } else {
                                Swal.fire({
                                    title: data.mensaje,
                                    text: data.errores,
                                    icon: 'error',
                                    timer: 2500,
                                    timerProgressBar: true,
                                    confirmButtonText: 'Aceptar'
                                });
                            }
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            let mensaje = jqXHR.responseJSON?.mensaje || jqXHR.statusText || "Error al cambiar el estado";
                            Swal.fire({
                                title: 'Falló el cambio de estado',
                                text: mensaje,
                                icon: 'error',
                                confirmButtonText: 'Aceptar'
                            });
                        }
                    });  
                }
            }
        },
        {
            text: "Agregar Nº Factura",
            className: 'btn btn-info btn-sm mb-1',
            action: function (e, dt, node, config) {
                const selectedRows = dt.rows({ selected: true });
                if (selectedRows.count() === 0) {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Aviso',
                        text: 'Debe seleccionar al menos un registro para agregar el número de factura.',
                        timer: 2000,
                        confirmButtonText: 'Aceptar',
                        timerProgressBar: true

                    });
                } else {
                    $('#agregarFacturaModal').modal('show');
                }
            }
        }
    ];
}





function getTablaBotones() {
    return [
        {
            init: function (dt, node, config) {
                $(node).attr('class', 'btn btn-primary btn-sm mb-1');
            },
            text: 'Todas',
            action: function (e, dt, node, config) {
                aplicarFiltro(dt, node, '', 'VIAJES');
            }
        },
        
        {
            init: function (dt, node, config) {
                $(node).attr('class', 'btn btn-outline-primary btn-sm mb-1');
            },
            text: 'Pendientes',
            action: function (e, dt, node, config) {
                aplicarFiltro(dt, node, 'pendiente', 'VIAJES PENDIENTES');
            }
        },
        {
            init: function (dt, node, config) {
                $(node).attr('class', 'btn btn-outline-primary btn-sm mb-1');
            },
            text: 'Programadas',
            action: function (e, dt, node, config) {
                aplicarFiltro(dt, node, 'programado', 'VIAJES PROGRAMADOS');
            }
        },
        {
            init: function (dt, node, config) {
                $(node).attr('class', 'btn btn-outline-primary btn-sm mb-1 me-3');
            },
            text: 'Finalizadas',
            action: function (e, dt, node, config) {
                aplicarFiltro(dt, node, 'Finalizado', 'VIAJES FINALIZADOS');
            }
        }
    ];






}

function botonesEspeciales() {
    return [
        {
            init: function (dt, node, config) {
                $(node).attr('class', 'btn btn-outline-primary btn-sm mb-1');
            },
            extend: 'excelHtml5',
            text: 'Excel',
            titleAttr: 'Exportar a Excel',
            exportOptions: {
                columns: ':visible:not(.no-export)',
                format: {
                    body: function (data) {
                        if (typeof data === 'string') {
                            return data.replace(/<[^>]+>/g, '');
                        }
                        if (Array.isArray(data)) {
                            return data.join(', ');
                        }
                        if (typeof data === 'object' && data !== null) {
                            return Object.values(data).join(', ');
                        }
                        return data;
                    }
                }
            }
        },
        {
            init: function (dt, node, config) {
                $(node).attr('class', 'btn btn-outline-primary btn-sm mb-1');
            },
            extend: 'print',
            text: 'Imprimir',
            titleAttr: 'Imprimir',
            className: 'btn btn-danger btn-sm mb-1',
            exportOptions: {
                rows: { search: 'applied' },
                columns: ':visible:not(.no-export)',
                format: {
                    body: function (data) {
                        if (typeof data === 'string') {
                            return data.replace(/<[^>]+>/g, '');
                        }
                        if (Array.isArray(data)) {
                            return data.join(', ');
                        }
                        if (typeof data === 'object' && data !== null) {
                            return Object.values(data).join(', ');
                        }
                        return data;
                    }
                }
            }
        }
    ];
}

function botonesAuxiliares() {
    return [
            {
                init: function (dt, node, config) {
                    const clase = localStorage.getItem('Bs') === 'true' ? 'btn btn-success btn-sm mb-1' : 'btn btn-outline-secondary btn-sm mb-1';
                    $(node).attr('class', clase);
                },
                text: 'Bolivares',
                action: function (e, dt, node, config) {
                    const current = localStorage.getItem('Bs') === 'true';
                    localStorage.setItem('Bs', !current);
                    $(node)
                        .toggleClass('btn-success', !current)
                        .toggleClass('btn-outline-secondary', current);
                    if (tablaInstancia) {
                        tablaInstancia.rows().invalidate().draw(false);
                    }
                }
            },
            {
                init: function (dt, node, config) {
                    $(node).attr('class', 'btn btn-outline-primary btn-sm mb-1');
                    $(node).removeClass('btn-primary').addClass('btn-outline-primary');
                    $(node).text('Seleccionar todos');
                },
                text: 'Seleccionar todos',
                action: function(e, dt, node, config) {
                    if (dt.rows({ search: 'applied' }).count() > 0) {
                        if ($(node).text() === 'Seleccionar todos') {
                            dt.rows({ search: 'applied' }).select();
                            $(node).removeClass('btn-outline-primary').addClass('btn-primary');
                            $(node).text('Deseleccionar todos');
                        } else {
                            dt.rows({ search: 'applied' }).deselect();
                            $(node).removeClass('btn-primary').addClass('btn-outline-primary');
                            $(node).text('Seleccionar todos');
                        }
                    } else {
                        Swal.fire({
                            icon: 'warning',
                            title: 'Aviso',
                            text: 'No hay filas disponibles para seleccionar.',
                            timer: 2000
                        });
                    }
                }
            },
            {
                init: function (dt, node, config) {
                    $(node).attr('class', 'btn btn-outline-primary btn-sm mb-1');
                },
                extend: 'collection',
                text: 'Acciones',
                // className: 'btn btn-outline-primary btn-sm mb-1 dropdown-toggle',
                autoClose: true,
                buttons: modelo === 'facturasClientes' ? botonesAcciones() : [botonesAcciones()[0], botonesAcciones()[1]],
            }
            ]
        }
function aplicarFiltro(dt, node, filtro, textoTabla) {
    // Para server-side processing, actualizar la URL base y recargar
    window.filtroActual = filtro; // Actualizar el filtro global
    dt.ajax.url(`/programacion/get_data?filtro=${filtro}`);
    dt.ajax.reload();
    $("#nombre-tabla").text(textoTabla);
    $(node).parent().find('button').removeClass('btn-primary').addClass('btn-outline-primary');
    $(node).removeClass('btn-outline-primary').addClass('btn-primary');
}

$(".agregar").click(function (e, modelo = window.modelo) {
    e.preventDefault();
    $(".formulario").removeClass("visually-hidden");
    // $(".tituloForm").text(`Registrar ${modelo.charAt(0).toUpperCase() + modelo.slice(1)}`);
    $(".tituloForm").text(`Registrar`);
    $(".botonForm").text('Registrar');
    $(`#${modelo}Form`).attr('method', 'POST');
    $(`#${modelo}Form`)[0].reset();
    $(`#${modelo}Form .selectized`).each(function () {
        if (this.selectize) {
            this.selectize.clear();
            // this.selectize.clearOptions();
        }
    });
});

$(".cerrar-form").click(function (e) {
    e.preventDefault();
    $(".formulario").addClass("visually-hidden");
});

// app.js
async function guardarRegistro(modelo, varModulo = "", reintentar = false) {
    const FORMULARIO = $(`#${modelo}Form`);
    const metodo = FORMULARIO.attr('method');

    let formData;
    let isFormData = false;

    // 🔍 LOG: Verificar método HTTP
    // //console.log("🔍 DEBUG CSRF - Método HTTP:", metodo);

    if (metodo === 'POST') {
        formData = new FormData(FORMULARIO[0]);
        isFormData = true;
        // 🔍 LOG: Verificar si el token CSRF está en FormData
        //console.log("🔍 DEBUG CSRF - Token en FormData POST:", formData.get('csrf_token'));
    } else if (metodo === 'PUT') {
        //console.log("PETICION PUT");
        formData = new FormData(FORMULARIO[0]);
        isFormData = false;
        //console.log("Formdata: " + formData);
        // 🔍 LOG: Verificar si el token CSRF está en FormData PUT
        //console.log("🔍 DEBUG CSRF - Token en FormData PUT:", formData.get('csrf_token'));

        if (!formData.get('costo_total')) {
            formData.delete('costo_total');
        }
    } else {
        formData = FORMULARIO.serialize();
    }

    const modulo = varModulo || window.modulo;
    const url = modulo !== "" ? `/${modulo}/${modelo}` : `/${modelo}`;

    // Obtener el token CSRF del formulario
    const csrfToken = FORMULARIO.find('input[name="csrf_token"]').val();

    const fetchOptions = {
        method: metodo,
        headers: {
            'X-CSRFToken': csrfToken  // ✅ SOLUCIÓN: Agregar token en headers
        },
    };

    if (isFormData) {
        //console.log("es formData");
        fetchOptions.body = formData;
        // 🔍 LOG: Verificar headers cuando se usa FormData
        //console.log("🔍 DEBUG CSRF - Headers con FormData:", fetchOptions.headers);
    } else {
        fetchOptions.headers['Content-Type'] = 'application/json';
        const params = new URLSearchParams(formData);
        const formDataObject = Object.fromEntries(params);
        for (let [key, value] of params) {
            if (key.endsWith('[]')) {
                const cleanKey = key.slice(0, -2);
                const values = params.getAll(key);
                formDataObject[cleanKey] = values;
            }
        }
        // 🔍 LOG: Verificar si csrf_token está en el objeto JSON
        //console.log("🔍 DEBUG CSRF - Token en JSON:", formDataObject.csrf_token);
        //console.log("🔍 DEBUG CSRF - Objeto completo a enviar:", formDataObject);
        //console.log("🔍 DEBUG CSRF - Token en Header X-CSRFToken:", csrfToken);
        fetchOptions.body = JSON.stringify(formDataObject);
    }

    // 🔍 LOG: Verificar configuración final de fetch
    //console.log("🔍 DEBUG CSRF - URL:", url);
    //console.log("🔍 DEBUG CSRF - Fetch Options:", fetchOptions);

    try {
        const response = await fetch(url, fetchOptions);
        const data = await response.json();

        if (data.success) {
            Swal.fire({
                title: 'Éxito',
                text: data.mensaje || "Registro guardado correctamente",
                icon: 'success',
                timer: 3000,
                timerProgressBar: true,
            }).then(() => {
                $(`#${modelo}Form`)[0].reset();
                $(`#${modelo}Form .selectized`).each(function () {
                    if (this.selectize) {
                        this.selectize.clear();
                    }
                });
                
                if (metodo === 'PUT') {
                    $(".formulario").addClass("visually-hidden");
                    window.registroIdEditar = null;
                    $(".tituloForm").text(`Registrar ${modelo.charAt(0).toUpperCase() + modelo.slice(1)}`);
                    $(".botonForm").text('Registrar');
                    // $(`#${modelo}Form`).attr('method', 'POST');
                }
                
                // Recargar solo la tabla sin refrescar la página
                const columnasVisibles = {
                    programacion: [1, 3, 9, 10, 12, 15, 27]
                };
                
                if (modelo === 'programacion') {
                    //cargarTabla2(modelo, varModulo, "", columnasVisibles[modelo] || []);
                    console.log("Recargando tabla de programación después de guardar...");
                    window.location.reload();
                } else {
                    window.location.reload();
                }
            });
        } else if (data.mensaje === "Factura existente." && !reintentar) {
            // Si es factura existente y no estamos en modo reintento
            Swal.fire({
                title: 'Confirmación',
                text: 'Esta acción eliminará las facturas, ¿está seguro desea continuar? Esta acción no se puede deshacer',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar y actualizar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#d33'
            }).then((result) => {
                if (result.isConfirmed) {
                    eliminarFacturasRecibos(data.factura_id, data.recibo_id, modelo, varModulo);
                }
            });
        } else {
            Swal.fire({
                title: data.mensaje || "Error al guardar",
                text: data.errores || "Ocurrió un error",
                icon: 'error',
                timer: 10000,
                timerProgressBar: true,
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            title: 'Error',
            text: "Ocurrió un error inesperado",
            icon: 'error',
        });
    }
}

function eliminarFacturasRecibos(factura_id, recibo_id, modelo, varModulo) {
    const url_facturas = `/facturacion/facturasClientes`;
    const url_recibos = `/facturacion/pagosOperadores`;
    
    $.ajax({
        url: url_facturas,
        type: 'DELETE',
        contentType: 'application/json',
        data: JSON.stringify({ id: factura_id }),
        success: function (data) {
            if (data.success) {
                $.ajax({
                    url: url_recibos,
                    type: 'DELETE',
                    contentType: 'application/json',
                    data: JSON.stringify({ id: recibo_id }),
                    success: function (data) {
                        if (data.success) {
                            Swal.fire({
                                title: 'Facturas eliminadas',
                                text: 'Facturas eliminadas correctamente, reintentando actualización...',
                                icon: 'success',
                                timer: 2000,
                                timerProgressBar: true,
                                showConfirmButton: false
                            }).then(() => {
                                // Reintentar la actualización después de eliminar
                                guardarRegistro(modelo, varModulo, true);
                            });
                        } else {
                            Swal.fire({
                                title: 'Error',
                                text: data.errores || 'Error al eliminar recibos',
                                icon: 'error',
                                timer: 2500,
                                timerProgressBar: true,
                                confirmButtonText: 'Aceptar'
                            });
                        }
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        let mensaje = jqXHR.responseJSON?.mensaje || jqXHR.statusText || "Error al eliminar el registro";
                        console.error("Error al eliminar recibos:", mensaje);
                        Swal.fire({
                            title: 'Error',
                            text: mensaje,
                            icon: 'error',
                            confirmButtonText: 'Aceptar'
                        });
                    }
                });
            } else {
                Swal.fire({
                    title: 'Error',
                    text: data.errores || 'Error al eliminar facturas',
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            let mensaje = jqXHR.responseJSON?.mensaje || jqXHR.statusText || "Error al eliminar facturas";
            console.error("Error al eliminar facturas:", mensaje);
            Swal.fire({
                title: 'Error',
                text: mensaje,
                icon: 'error',
                confirmButtonText: 'Aceptar'
            });
        }
    });
}



function eliminarSeleccionados(modelo) {
    const tabla = `#${modelo}Table`;
    const dt = $(tabla).DataTable();
    
    if (dt.rows({ selected: true }).count() === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Aviso',
            text: 'Debe seleccionar al menos un registro para eliminar.',
            timer: 2000
        });
        return;
    }

    // Extraer los IDs correctamente
    const registroIds = [];
    dt.rows({ selected: true }).every(function() {
        const data = this.data();
        registroIds.push(data.id);
    });

    //console.log("IDs de registros seleccionados para eliminar:", registroIds);

    // Mensaje especial para programaciones
    const mensajeTexto = modelo === 'programacion'
        ? "Esta acción eliminará la programación y todos sus registros asociados (facturas y pagos de operador). No podrás recuperar los registros eliminados."
        : "No podrás recuperar los registros eliminados";

    Swal.fire({
        title: '¿Estás seguro?',
        text: mensajeTexto,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminarlos'
    }).then((result) => {
        if (result.isConfirmed) {
            const basePath = (window.modulo && window.modulo !== modelo) ? `/${window.modulo}/${modelo}` : `/${modelo}`;
            const url = basePath;
            
            $.ajax({
                url: url,
                type: 'DELETE',
                contentType: 'application/json',
                data: JSON.stringify({ id: registroIds }),
                success: function (data) {
                    if (data.success) {
                        Swal.fire({
                            title: 'Éxito',
                            text: data.mensaje,
                            icon: 'success',
                            timer: 2000,
                            timerProgressBar: true,
                            confirmButtonText: 'Aceptar'
                        }).then(() => {
                            // Recargar solo la tabla
                            const columnasVisibles = {
                                programacion: [1, 3, 9, 10, 12, 15, 27]
                            };
                            // cargarTabla2(modelo, "", "", columnasVisibles[modelo] || []);
                            //console.log(" 🔍Modelo:", window.modelo, "Modulo:", window.modulo);
                            // cargarTabla2(window.modelo, window.modulo, "", columnasVisibles[window.modelo] || []);
                            window.location.reload();
                        });
                    } else {
                        Swal.fire({
                            title: "Error al eliminar",
                            text: data.mensaje || "Ocurrió un error",
                            icon: 'error',
                            timer: 5500,
                            timerProgressBar: true,
                            confirmButtonText: 'Aceptar'
                        });
                    }
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    let mensaje = jqXHR.responseJSON?.mensaje || jqXHR.statusText || "Error al eliminar el registro";
                    Swal.fire({
                        title: 'Falló la eliminación',
                        text: mensaje,
                        icon: 'error',
                        confirmButtonText: 'Aceptar'
                    });
                }
            });
        }
    });
}

function editar(id) {
 

    llenarFormulario(id);


    $(".formulario").removeClass("visually-hidden");
    $(".tituloForm").text(`Editar ${modelo.charAt(0).toUpperCase() + modelo.slice(1)}`);
    $(".botonForm").text('Actualizar');
    $(`#${window.modelo}Form`).attr('method', 'PUT');
}



function llenarFormulario(id) {
    const basePath = (window.modulo && window.modulo !== window.modelo) ? `/${window.modulo}/${window.modelo}` : `/${window.modelo}`;
    const URL = `${basePath}/get_data/${id}`;

    //console.log(`Llenando formulario para el modelo: ${modelo}, ID: ${id}, URL: ${URL}`);

    $.ajax({
        type: "GET",
        url: URL,
        data: {},
        dataType: "json",
        success: function (response) {
            if (response.success) {
                //console.log("Datos obtenidos:", response.data);
                const data = response.data;
                
                // Guardar el status original en el formulario para detectar cambios
                if (data.status) {
                    $(`#${modelo}Form`).data('status-original', data.status);
                    //console.log(`Status original guardado: ${data.status}`);
                }
                
                Object.keys(data).forEach(key => {
                    const $campo = $(`#${modelo}Form [name="${key}"]`);
                    //console.log(`Procesando campo: ${key}, valor: ${data[key]}`);
                    
                    if ($campo.length) {
                        // CASO ESPECIAL PARA CHECKBOX
                        if ($campo.attr('type') === 'Checkbox') {
                            //console.log(`🔘 Checkbox detectado: ${key}, valor: ${data[key]}`);
                            
                            // Convertir el valor a booleano
                            const isChecked = Boolean(data[key]);
                            $campo.prop('checked', isChecked);
                            //console.log(`✓ Checkbox ${key} ${isChecked ? 'marcado' : 'desmarcado'}`);
                        }
                        // CASO PARA SELECTIZE
                        else if ($campo[0].selectize) {
                            if (key === "pasajeros") {
                                $campo[0].selectize.setValue(data[key], true);
                                $campo[0].selectize.trigger('change');
                            }
                            else {
                                $campo[0].selectize.setValue(data[key], true);
                            }

                            if (key.includes('direccion_destino') || key.includes('direccion_origen')) {
                                setTimeout(() => {
                                    $campo[0].selectize.setValue(data[key], true);
                                    //console.log(`Selectize timeout actualizado para: ${key} con valor: ${data[key]}`);
                                }, 600);
                            }
                        }
                        // CASO PARA INPUTS NORMALES
                        else {
                            $campo.val(data[key]);
                            //console.log(`Llenando campo: ${key} con valor: ${data[key]}`);
                        }
                    }
                });
            } else {
                console.error(response.mensaje);
            }

            if ($("#retorno-form").is(':checked')) {
                $("#h-retorno").removeClass("visually-hidden");
                //console.log("Hora de retorno visible");
            } else {
                $("#h-retorno").addClass("visually-hidden");
            }

        }
        
    }).fail(function (jqXHR, textStatus, errorThrown) {
        console.error("Error al obtener los datos:", textStatus, errorThrown);
        Swal.fire({
            title: 'Error',
            text: "Ocurrió un error al cargar los datos del registro",
            icon: 'error',
            confirmButtonText: 'Aceptar'
        });
    });
}

