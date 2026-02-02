// Configuración específica de DataTable para Programación con server-side
$(document).ready(function () {
	window.modulo = 'programacion';
	window.modelo = 'programacion';
	window.tablaId = '#programacionTable';
	window.filtroActual = null;

	initProgramacionTable();
});

function initProgramacionTable() {
	const tablaSel = $(window.tablaId);
	if (tablaSel.hasClass('dataTable')) {
		tablaSel.DataTable().clear().destroy();
	}

	// Oculta la tabla y su wrapper hasta que termine el primer render
	const wrapperId = '#programacionTable_wrapper';
	tablaSel.hide();
	$(wrapperId).hide();

	const columnas = [
		{
			data: null,
			title: '#',
			orderable: false,
			searchable: false,
			render: function (_, __, ___, meta) {
				return meta.row + 1 + meta.settings._iDisplayStart;
			}
		},
		{ data: 'id', visible: false },
		{ data: 'fecha_salida', title: 'Fecha', type: 'date-dd-mm-yyyy' },
		{ data: 'empresa', title: 'Empresa' },
		{ data: 'workflow', title: 'Workflow' },
		{ data: 'guia', title: 'Guía' },
		{
			data: 'pasajeros',
			title: 'Pasajeros',
			render: function (data) {
				if (Array.isArray(data)) {
					return data.map(p => p.nombre).join('|<br>');
				}
				return data || '';
			}
		},
		{ data: 'hora_salida', title: 'Hora salida' },
		{ data: 'hora_retorno', title: 'Hora retorno' },
		{ data: 'direccion_origen', title: 'Dir. Origen' },
		{ data: 'Ciudad_Origen', title: 'Origen' },
		{ data: 'direccion_destino', title: 'Dir. Destino' },
		{ data: 'Ciudad_Destino', title: 'Destino' },
		{ data: 'operador', title: 'Operador' },
		{ data: 'vehiculo', title: 'Vehículo' },//13
		{ data: 'horario', title: 'Horario' },
		{ data: 'desplazamiento', title: 'Desplaz.', visible: false, searchable: false },
		// { data: 'distancia', title: 'Km' },
		{ data: 'tiempo_espera', title: 'T. Espera' },
		{ data: 'desvios', title: 'Desvíos' },
		{ data: 'status', title: 'Status', visible: false, searchable: false },
		{ data: 'observaciones', title: 'Observaciones' },
		// Ocultas para mantener datos base
		{ data: 'empresa_rel', visible: false, searchable: false },
		{ data: 'origen_rel', visible: false, searchable: false },
		{ data: 'destino_rel', visible: false, searchable: false },
		{ data: 'operador_rel', visible: false, searchable: false },
		{ data: 'vehiculo_rel', visible: false, searchable: false },
		{ data: 'fecha_salida_rel', visible: false, searchable: false },
	];

	const dt = tablaSel.DataTable({
		processing: true,
		serverSide: true,
		ajax: {
			url: '/programacion/get_data',
			type: 'GET',
			data: function (d) {
				if (window.filtroActual) {
					d.filtro = window.filtroActual;
				}
				d.fecha_desde = $('#f-desde').val();
                d.fecha_hasta = $('#f-hasta').val();
				// console.log('Enviando datos AJAX:', d);
				// return d;
			}
		},
		columns: columnas,
		// Prioridad de visualización para columnas clave
		columnDefs: (function () {
			const visibleColumns = [3, 10,  12, 7, 8, 13, 20]; // Índices de columnas importantes
			const validTargets = visibleColumns.filter(idx => idx >= 0 && idx < columnas.length);
			return validTargets.length ? [{ targets: validTargets, responsivePriority: 1 }] : [];
		})(),
		responsive: true,
		pageLength: 40,
		pagingType: 'numbers',
		order: [[1, 'desc']],
		select: {
			style: 'multi',
			blurable: true,
			items: 'row',
			className: 'selected'
		},
		language: {
			processing: '',
			search: '',
			info: '_START_ a _END_ de _TOTAL_ entradas',
			infoEmpty: '0 entradas',
			infoFiltered: '(filtrado de _MAX_ entradas totales)',
			select: {
				rows: {
					_: '%d filas seleccionadas',
					// 0: 'Haz clic en una fila para seleccionarla',
					1: '1 fila seleccionada'
				},
				columns: {
					0: ""
				},
				cells: {
					0: ""
				}
			}
		},
		layout: {
			topStart: {
				buttons: [typeof getTablaBotones === 'function' ? getTablaBotones() : [],
				botonesEspeciales()
			]
			},
			topEnd: {
				buttons: typeof botonesAuxiliares === 'function' ? botonesAuxiliares() : [],
				search: true
			}
		},
		createdRow: function (row, data) {
			if (!data || typeof data.status !== 'string') return;
			const status = data.status.toLowerCase().trim();
			const statusClassMap = {
				'finalizado': 'table-success text-success',
				'facturado': 'table-success',
				'pendiente': 'table-danger',
				'por facturar': 'table-danger',
				'programado': 'table-warning'
			};
			const cssClass = statusClassMap[status];
			if (cssClass) $(row).addClass(cssClass);
		},
		initComplete: function () {
			// Ajusta anchos y muestra la tabla una vez cargados los datos iniciales
			this.api().columns.adjust().responsive.recalc();
			tablaSel.show();
			$(wrapperId).show();
		}
	});

	window.tablaInstancia = dt;
}
