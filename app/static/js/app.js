const selectizeConfig = {
    create: false,
    allowEmptyOption: false,
    placeholder: 'Seleccione',
    valueField: 'id',
    labelField: 'text',
    searchField: ['text', 'nombres'],
    render: {
        option: function (item, escape) {
            return `<div>${escape(item.text)}</div>`;
        }
    }
};

function cargarSelectize(url, empresaId, selectize) {
    if (empresaId && empresaId !== "__None" && empresaId !== null && empresaId !== undefined) {
        console.log("Consultando para la empresa:", empresaId);
        fetch(url)
            .then(response => response.json())
            .then(response => {
                console.log("Datos consultados:", response);
                selectize.clear();
                selectize.clearOptions();
                if (response.success) {
                    response.data.forEach(function (item) {
                        item.nombres = item.nombres || item.nombre || item.tipo || item.codigo;
                        console.log(`Agregando opción: ${item.nombres}`);
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
        console.log("No se ha seleccionado una empresa válida.");
        selectize.clear();
        selectize.clearOptions();
        selectize.addOption({
            id: 0,
            text: 'Seleccione una empresa'
        });
    }
}

$.extend(true, $.fn.DataTable.defaults, {
    language: {

        url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-MX.json ',
        search: "",
        searchPlaceholder: "Buscar...",
        
       
        
    },
    lengthChange: false,
    ordering: false,
    responsive: true,
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
    function (settings, data, dataIndex) {
        var min = $('#f-desde').val();
        var max = $('#f-hasta').val();
        var fecha = data[1]; // Ajusta este índice según la posición real de tu columna de fecha

        if (!fecha) return true;

        var fechaParts = fecha.split('-'); // Formato esperado: dd-mm-yyyy
        var fechaData = new Date(fechaParts[2], fechaParts[1] - 1, fechaParts[0]); // YYYY, MM-1, DD
        var minDate = min ? new Date(min) : null;
        var maxDate = max ? new Date(max) : null;

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
});

$('#f-limpiar').on('click', function () {
    $('#f-desde').val('');
    $('#f-hasta').val('');
    $(window.tablaId).DataTable().draw();
});

let tablaInstancia = null;
let tasaGlobal = 1;

async function baseTablas(modelo, modulo = "", empresa_id = "") {
    console.log("Cargando tabla para el modelo:", modelo);
    console.log("Módulo:", modulo);
    console.log("Empresa ID:", empresa_id);

    var url = modulo !== "" ? `/${modulo}/${modelo}/all` : `/${modelo}/all`;
    if (empresa_id) {
        url = `${modelo}?cliente=${empresa_id}`;
    }

    console.log("URL de la tabla:", url);

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
                tasaGlobal = jsonTasa.data[0].tasa || 1;
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

    const keys = json.data.length > 0 ? Object.keys(json.data[0]) : [];
    const columnas = keys.map(campo => ({
        data: campo,
        title: campo.charAt(0).toUpperCase() + campo.slice(1).replace('_', " "),
       
        render: function (data_2) {
            // console.log(`Columna creada: ${campo} (índice: ${keys.indexOf(campo)})`);
            if (campo === 'pasajeros' && modelo === 'programacion') {
                if (Array.isArray(data_2)) {
                    return data_2.map(p => `${p.nombre} (${p.telefono})`).join('<br>');
                }
                return data_2;
            }
            else if (campo === 'pasajeros') {
                if (Array.isArray(data_2)) {
                    return data_2.map(p => `${p.nombre}`).join('<br>');
                }
                return data_2;
            }

            return data_2;
        }
    }));

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



    columnas.push({
        data: null,
        title: "Acciones",
        orderable: false,
        className: 'no-export',
        searchable: false,
        render: function (data_4, type, row) {
            let acciones = `
                <i class="bx bx-edit text-primary" style="cursor: pointer;" onClick="editar(${row.id}, '${modelo}')"></i>
                <i class="bx bx-trash text-danger" style="cursor: pointer;" onClick="eliminar(${row.id}, '${modelo}')"></i>
            `;
            if (modelo === 'tarifas') {
                acciones += `<a href="/empleados/tarifasOperadores" title="Ver tarifas del operador">
                    <i id="oper" class="bx bxs-car" style="cursor: pointer; color:${row.color_rel};"></i>
                </a>`;
            }
            return acciones;
        }
    });

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
    console.log("JsonData:", json.data);
    return {
        tabla,
        columnas,
        columnDefs,
        jsonData: json.data
    };
}

function cargarTabla1(modelo, modulo = "", VisibleColumns = []) {
    baseTablas(modelo, modulo).then(({ tabla, columnas, columnDefs, jsonData }) => {

    
        // Si se especifican columnas visibles, actualiza columnDefs
        let mobileColumnDefs = Array.isArray(columnDefs) ? [...columnDefs] : [];
        if (Array.isArray(VisibleColumns) && VisibleColumns.length > 0) {
            console.log("Columnas visibles:", VisibleColumns);
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
            pageLength: 10,
            pagingType: "numbers"
        });
    }).catch(err => {
        console.error("Error al cargar la tabla:", err);
    });
}

function cargarTabla2(modelo, modulo = "", empresa_id = "", VisibleColumns = []) {
    baseTablas(modelo, modulo, empresa_id).then(({ tabla, columnas, columnDefs, jsonData }) => {
        // Configuración base de DataTable

         // Si se especifican columnas visibles, actualiza columnDefs
        let mobileColumnDefs = Array.isArray(columnDefs) ? [...columnDefs] : [];
        if (Array.isArray(VisibleColumns) && VisibleColumns.length > 0) {
            console.log("Columnas visibles:", VisibleColumns);
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

        let config = {
            data: jsonData,
            columns: columnas,
            responsive: true,
            columnDefs: AllColumnDefs,
            paging: true,
            pageLength: 20,
            select: 'row',
            language: {
                search: "",
                info: "",
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
            // orderable: true,
            // order: [[0, 'desc']], // Ordenar por la primera columna (id) de forma descendente

            pagingType: "numbers",
            
            layout: {
                topStart: {
                    buttons: modulo !== 'facturacion' ? getTablaBotones() : botonesEspeciales(),
                },
                topEnd: {
                    buttons: [
                        {
                            init: function (dt, node, config) {
                                const clase = localStorage.getItem('Bs') === 'true' ? 'btn btn-success btn-sm mb-1' : 'btn btn-outline-secondary btn-sm mb-1';
                                $(node).attr('class', clase);
                            },
                            text: 'Bs',
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
                            buttons: [
                                {
                                    text: 'Editar',
                                    className: 'dropdown-item',
                                    action: function (e, dt, node, config) {
                                        if (dt.rows({ selected: true }).count() === 0) {
                                            Swal.fire({
                                                icon: 'warning',
                                                title: 'Aviso',
                                                text: 'Debe seleccionar al menos un registro para editar.',
                                                timer: 2000
                                            });
                                            return;
                                        }
                                        if (dt.rows({ selected: true }).count() > 1) {
                                            Swal.fire({
                                                icon: 'warning',
                                                title: 'Aviso',
                                                text: 'Solo se puede editar un registro a la vez.',
                                                timer: 2000
                                            });
                                            return;
                                        }
                        
                                            const registroId = dt.rows({ selected: true }).data()[0].id;
                                            editar(registroId, modelo);
                                 
                                    }
                                },
                                {
                                    text: 'Eliminar',
                                    className: 'dropdown-item',
                                    action: function (e, dt, node, config) {
                                        if (dt.rows({ selected: true }).count() === 0) {
                                            Swal.fire({
                                                icon: 'warning',
                                                title: 'Aviso',
                                                text: 'Debe seleccionar al menos un registro para eliminar.',
                                                timer: 2000
                                            });
                                            return;
                                        }
                                        else  {
                                            eliminarSeleccionados(modelo);
                                        }
                                        
                                        
                                    }
                                }
                            ]
                          }
                    ],
                    search: true
                }
            },
            createdRow: function (row, data, dataIndex) {
                    if (data.status && (data.status.toLowerCase() === 'finalizado' || data.status.toLowerCase() === 'facturado')) {
                        $(row).addClass('table-success');
                    }
                    if (data.status && (data.status.toLowerCase() === 'pendiente' || data.status.toLowerCase() === 'por facturar')) {
                        $(row).addClass('table-danger');
                    }
                    if (data.status && (data.status.toLowerCase() === 'programado' )) {
                        $(row).addClass('table-warning');
                    }
            },
        };


        // Agregar footerCallback solo para facturasClientes y pagosOperadores
        if (modelo === 'facturasClientes' || modelo === 'pagosOperadores') {
            // Encontrar la columna que contiene el total
            const totalColumnIndex = columnas.findIndex(col => col.data === 'total_');
            console.log("Total Column Index:", totalColumnIndex);

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
            console.log("Tabla destruida y reiniciada");
        }

        // Crear tabla DataTable
        tablaInstancia = $(tabla).DataTable(config);
    }).catch(err => {
        console.error("Error al cargar la tabla:", err);
    });
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
                $(node).attr('class', 'btn btn-primary btn-sm mb-1');
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
                $(node).attr('class', 'btn btn-primary btn-sm mb-1');
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

function aplicarFiltro(dt, node, filtro, textoTabla) {
    dt.ajax.url(`/programacion/get_data?filtro=${filtro}`).load();
    $("#nombre-tabla").text(textoTabla);
    $(node).parent().find('button').removeClass('btn-primary').addClass('btn-outline-primary');
    $(node).removeClass('btn-outline-primary').addClass('btn-primary');
}

$(".agregar").click(function (e, modelo = window.modelo) {
    e.preventDefault();
    $(".formulario").removeClass("visually-hidden");
    $(".tituloForm").text(`Registrar ${modelo.charAt(0).toUpperCase() + modelo.slice(1)}`);
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

async function guardarRegistro(modelo, varModulo = "") {
    const FORMULARIO = $(`#${modelo}Form`);
    const metodo = FORMULARIO.attr('method');

    let formData = metodo === 'POST' ? new FormData(FORMULARIO[0]) : FORMULARIO.serialize();

    if (modelo === 'programacion' && metodo === 'POST') {
        const operador = formData.get('operador');
        const status = formData.get('status');
        if (operador !== "__None" && status === 'Pendiente') {
            await Swal.fire({
                icon: 'warning',
                title: 'Aviso',
                text: 'Ha asignado un operador, pero el estado es "Pendiente". ¿Desea cambiar a "Programado"?',
                showCancelButton: true,
                confirmButtonText: 'Sí, cambiar a Programado',
                cancelButtonText: 'No, mantener Pendiente'
            }).then((result) => {
                if (result.isConfirmed) {
                    formData.set('status', 'Programado');
                }
            });
        }
    }

    if (metodo === 'PUT') {
        // Convertimos la cadena serializada en un objeto URLSearchParams
        let params = new URLSearchParams(formData);

        // Verificamos si costo_total no está presente o es undefined
        if (params.get('costo_total') === "" || params.get('costo_total') === null || params.get('costo_total') === undefined) {
            console.log("costo_total no está presente, eliminando...");
            params.delete('costo_total'); // Lo eliminamos si existe (opcional, por seguridad)
        }

        // Convertimos a objeto plano y luego a JSON
        const formDataObject = Object.fromEntries(params);
        formData = JSON.stringify(formDataObject);

        console.log("Datos del formulario:", formData, "para:", metodo, "en el modelo:", modelo);
    }

    const modulo = varModulo || window.modulo;
    const url = modulo !== "" ? `/${modulo}/${modelo}` : `/${modelo}`;

    fetch(url, {
        method: metodo,
        headers: {
            ...(!(formData instanceof FormData) && { 'Content-Type': 'application/json' })
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    title: 'Éxito',
                    text: data.mensaje || "Registro guardado correctamente",
                    icon: 'success',
                    confirmButtonText: 'Aceptar',
                    timer: 7000,
                    timerProgressBar: true,
                }).then(() => {
                    $(`#${modelo}Form`)[0].reset();
                    $(`#${modelo}Form .selectized`).each(function () {
                        if (this.selectize) {
                            this.selectize.clear();
                            // this.selectize(selectizeConfig)

                            // this.selectize.clearOptions();
                        }
                    });
                    if (modelo === 'programacion' || modelo === 'facturasClientes') {
                        // cargarTabla2(modelo, modulo);
                        location.reload();
                    } else {
                        cargarTabla1(modelo, modulo);
                    }
                    if (metodo === 'PUT') {
                        $(".formulario").addClass("visually-hidden");
                        window.registroIdEditar = null;
                        $(".tituloForm").text(`Registrar ${modelo.charAt(0).toUpperCase() + modelo.slice(1)}`);
                        $(".botonForm").text('Registrar');
                        $(`#${modelo}Form`).attr('method', 'POST');
                    }
                });
            } else {
                Swal.fire({
                    title: data.mensaje || "Ocurrió un error al guardar el registro",
                    text: data.errores || "Ocurrió un error al guardar el registro",
                    icon: 'error',
                    timer: 10000,
                    timerProgressBar: true,
                    confirmButtonText: 'Aceptar',
                });
            }
        })
        .catch(error => {
            console.warn('Error:', error);
            Swal.fire({
                title: 'Error',
                text: "Ocurrió un error inesperado al guardar el registro",
                icon: 'error',
                confirmButtonText: 'Aceptar',
            });
        });
}

function eliminar(id, modelo) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "No podrás recuperar este registro",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminarlo'
    }).then((result) => {
        if (result.isConfirmed) {
            const url = window.modulo !== "" ? `/${window.modulo}/${modelo}` : `/${modelo}`;
            $.ajax({
                url: url,
                type: 'DELETE',
                contentType: 'application/json',
                data: JSON.stringify({ id: id }),
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
                            const dataTable = $(`#${modelo}Table`).DataTable();
                            if (dataTable.rows().count() === 1) {
                                location.reload();
                            } else {
                                dataTable.clear().destroy();
                                if (modelo === 'programacion' || modelo === 'facturasClientes') {
                                    cargarTabla2(modelo, window.modulo);
                                } else {
                                    cargarTabla1(modelo, window.modulo);
                                }
                            }
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
                    let mensaje = jqXHR.responseJSON?.mensaje || jqXHR.statusText || "Error al eliminar el registro";
                    console.error("Error al eliminar:", mensaje);
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

    console.log("IDs de registros seleccionados para eliminar:", registroIds);

    Swal.fire({
        title: '¿Estás seguro?',
        text: "No podrás recuperar estos registros",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminarlos'
    }).then((result) => {
        if (result.isConfirmed) {
            const url = window.modulo !== "" ? `/${window.modulo}/${modelo}` : `/${modelo}`;
            
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
                            const dataTable = $(`#${modelo}Table`).DataTable();
                            if (dataTable.rows().count() === 1) {
                                location.reload();
                            } else {
                                dataTable.clear().destroy();
                                if (modelo === 'programacion' || modelo === 'facturasClientes') {
                                    cargarTabla2(modelo, window.modulo);
                                } else {
                                    cargarTabla1(modelo, window.modulo);
                                }
                            }
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

function editar(id, modelo) {
    window.registroIdEditar = id;
    const tabla = `#${modelo}Table`;
    const table = $(tabla).DataTable();
    const rowData = table.rows().data().toArray().find(row => row.id === id);
    if (!rowData) {
        Swal.fire({
            title: 'Error',
            text: 'No se encontraron los datos del registro.',
            icon: 'error',
            confirmButtonText: 'Aceptar'
        });
        return;
    }

    llenarFormulario(modelo, rowData);


    $(".formulario").removeClass("visually-hidden");
    $(".tituloForm").text(`Editar ${modelo.charAt(0).toUpperCase() + modelo.slice(1)}`);
    $(".botonForm").text('Actualizar');
    $(`#${modelo}Form`).attr('method', 'PUT');
}

function llenarFormulario(modelo, rowData) {
    Object.keys(rowData).forEach(key => {
        const $campo = $(`#${modelo}Form [name="${key}"]`);
        if ($campo.length) {
            $campo.val(rowData[key]);
            console.log(`Llenando campo: ${key} con valor: ${rowData[key]}`);
        }
        if (key.includes('_rel')) {
            const baseKey = key.replace('_rel', '');
            const valorRelacionado = rowData[key];
            const $campoBase = $(`#${modelo}Form [name="${baseKey}"]`);

            if ($campoBase.length) {
                $campoBase.val(valorRelacionado);

                // console.log(`Llenando campo relacionado: ${baseKey} con valor: ${valorRelacionado}`);
                if ($campoBase[0] && $campoBase[0].selectize) {

                    if (baseKey === 'empresa' || baseKey === 'origen') {
                        $campoBase[0].selectize.setValue(valorRelacionado, false);
                        console.log(`Selectize actualizado para: ${baseKey} con valor: ${valorRelacionado}`);
                        setTimeout(() => {
                            $campoBase[0].selectize.setValue(valorRelacionado, false);
                        }, 600);
                    }

                    else {
                        setTimeout(() => {
                            $campoBase[0].selectize.setValue(valorRelacionado, true);
                        }, 600);
                        console.log(`Selectize timeout actualizado para: ${baseKey} con valor: ${valorRelacionado}`);

                    }

                    // console.log(`Selectize actualizado para: ${baseKey} con valor: ${valorRelacionado}`);
                }

            }
        }
    });

}

