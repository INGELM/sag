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
		{ data: 'id', visible: false, className: 'no-report' },
		{ data: 'wa_msg_id', visible: false, className: 'no-report' },
		{ data: 'wa_status', title: 'Wa', orderable: false, searchable: false, className: 'no-report',
			render: function (valor) {
				console.log('Renderizando WhatsApp:', valor);
				if (valor === null || valor === undefined) {
					return '';
				}
				else if (valor === 'sent') {
					return '<i class="bx bx-check" />';
				}
				else if (valor === 'delivered') {
					return '<i class="bx bx-checks bx-sm" />';
				}
				else if (valor === 'read') {
					return '<i class="bx bx-checks bx-remove-padding bx-sm" style="color:#1100ff;" />';
				}
				else if (valor === 'failed') {
					return `<i class="bx bx-x" style="color: red;" />`;
				}
			}
		},
		{ data: 'fecha_salida', title: 'Fecha', type: 'date-dd-mm-yyyy', className: 'exportable' },
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
		{ data: 'operador', title: 'Operador',
			render: function (data) {
				console.log('Renderizando operador:', data);
        		if (data[0] && data[0].nombre) {
            		return `${data[0].nombre}`;
					//  <span class="badge bg-danger">1</span>`
        }
        return '<span class="text-muted">Sin asignar</span>';
    }
		},
		{ data: 'vehiculo', title: 'Vehículo' },//13
		{ data: 'horario', title: 'Horario' },
		{ data: 'desplazamiento', title: 'Desplaz.', visible: false, searchable: false },
		// { data: 'distancia', title: 'Km' },
		{ data: 'tiempo_espera', title: 'Tiempo Espera' },
		{ data: 'desvios', title: 'Desvíos' },
		{ data: 'status', title: 'Status', visible: false, searchable: false },
		{ data: 'observaciones', title: 'Observaciones' },
		// Ocultas para mantener datos base
		{ data: 'empresa_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'origen_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'destino_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'operador_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'vehiculo_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'fecha_salida_rel', visible: false, searchable: false, className: 'no-report' },
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
			const priority_col = ['fecha_salida', 'empresa', 'guia', 'hora_salida', 'hora_retorno', 'Ciudad_Origen', 'Ciudad_Destino', 'operador', 'observaciones'];
			const col_indices = columnas.reduce((indices, col, idx) => {
				if (priority_col.includes(col.data)) {
					indices.push(idx);
				}
				return indices;
			}, []);
			console.log('Índices de columnas visibles:', col_indices);
			const visibleColumns = col_indices; // Índices de columnas importantes
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

	const socket = io(); // Conexión Socket.IO para actualizaciones en tiempo real
	socket.on('message_status_update', function (data) {
		const msgId = data.msg_id;
		const newStatus = data.status;
		// console.log(`Socket.IO - Actualización de estado recibida para msg_id ${msgId}: ${newStatus}`);

		// Encuentra la fila correspondiente al mensaje actualizado
		dt.rows().every(function () {
			const rowData = this.data();
			// console.log('Verificando fila con datos:', rowData);
			// console.log('Verificando fila con msg_id:', rowData.wa_msg_id);
			// console.log(`Recibida actualización de estado para msg_id ${msgId}: ${newStatus}`);
			if (rowData.wa_msg_id === msgId) {
				rowData.wa_status = newStatus;
				this.data(rowData).draw(false); // Actualiza la fila sin reiniciar la paginación

				// console.log(`Fila actualizada para msg_id ${msgId} con nuevo estado: ${newStatus}`);
			}
		});
	});
}
