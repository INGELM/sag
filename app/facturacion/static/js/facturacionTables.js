$(document).ready(async function () {
	const modelo = window.location.pathname.split('/').filter(Boolean).pop();
	window.modulo = 'facturacion';
	window.modelo = modelo;
	// Habilitar botón Bolívares en vistas de facturación
	window.mostrarBolivares = true;

	if (modelo === 'cobro_detalle') {
		window.tablaId = '#facturasCobrosDetalle';
		await cargarTasaGlobal();
		inicializarTablaCobroDetalle();
		agregarFiltros(modelo);
		return;
	}

	if (modelo === 'pagosOperadores') {
		return;
	}

	window.tablaId = `#${modelo}Table`;

	await cargarTasaGlobal();
	inicializarTablaServerSide(modelo);
	agregarFiltros(modelo);
});

async function cargarTasaGlobal() {
	try {
		const resp = await fetch('/tasa/all');
		if (!resp.ok) {
			return;
		}
		const data = await resp.json();
		if (data.success && Array.isArray(data.data) && data.data.length > 0) {
			tasaGlobal = data.data.at(-1)?.tasa || tasaGlobal;
		}
	} catch (err) {
		console.error('No se pudo obtener la tasa:', err);
	}
}

function formatearMonto(valor) {
	const numero = parseFloat(valor) || 0;
	const usarBs = localStorage.getItem('Bs') === 'true';
	const tasa = typeof tasaGlobal !== 'undefined' && tasaGlobal ? tasaGlobal : 1;
	const convertido = usarBs ? numero * tasa : numero;
	// console.log('Formateando monto:', valor, '->', convertido, usarBs ? '(Bs)' : '(USD)');
	return convertido.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

}

function columnasFacturasClientes() {
	return [
			{
			data: null,
			title: '#',
			orderable: false,
			searchable: false,
			render: function (_, __, ___, meta) {
				return meta.row + 1 + meta.settings._iDisplayStart;
			}
		},
		{ data: 'id', visible: false, searchable: false, className: 'no-report' },
		{ data: 'fecha', title: 'Fecha' },
		{ data: 'cliente', title: 'Cliente' },
		{
			data: 'pasajeros',
			title: 'Pasajeros',
			render: function (data) {
				if (Array.isArray(data)) {
					return data.map(p => p.nombre).join('|<br>');
				}
				return '';
			}
		},
		{ data: 'factura', title: 'Factura' },
		{ data: 'guia', title: 'Guía' },
		{ data: 'hora_salida', title: 'Hora salida' },
		{ data: 'hora_retorno', title: 'Hora retorno' },
		{ data: 'horario', title: 'Horario' },
		{ data: 'desplazamiento', title: 'Desplaz.' },
		{ data: 'origen', title: 'Origen' },
		{ data: 'destino', title: 'Destino' },
		{ data: 'distancia', title: 'Distancia' },
		{ data: 'total_distancia', title: 'Total distancia', render: formatearMonto },
		{ data: 'tiempo_espera', title: 'Tiempo espera' },
		{ data: 'total_espera', title: 'Total espera', render: formatearMonto },
		{ data: 'desvíos', title: 'Desvíos' },
		{ data: 'total_desvios', title: 'Total desvíos', render: formatearMonto },
		{ data: 'costo_base', title: 'Costo base', render: formatearMonto },
		{ data: 'total_', title: 'Total', render: formatearMonto },
		{ data: 'status', title: 'Status' },
	];
}

function columnasCobroDetalle() {
	return [
	
		{ data: 'id', visible: false, searchable: false, className: 'no-report' },
		{ data: 'fecha', title: 'Fecha' },
		{ data: 'cliente', title: 'Cliente' },
		{ data: '#_Pasajero', title: '# Pasajero' },
		{ data: 'pasajero', title: 'Pasajero' },
		{ data: 'factura', title: 'Factura' },
		{ data: 'guia', title: 'Guía' },
		{ data: 'hora_salida', title: 'Hora salida' },
		{ data: 'hora_retorno', title: 'Hora retorno' },
		{ data: 'horario', title: 'Horario' },
		{ data: 'desplazamiento', title: 'Desplaz.' },
		{ data: 'origen', title: 'Origen' },
		{ data: 'destino', title: 'Destino' },
		{ data: 'total_espera', title: 'Total espera', render: formatearMonto },
		{ data: 'total_desvios', title: 'Total desvíos', render: formatearMonto },
		{ data: 'total_', title: 'Total', render: formatearMonto },
	];
}

function inicializarTablaServerSide(modelo) {
	const columnas = columnasFacturasClientes();
	const fechaIndex = columnas.findIndex(col => col.data === 'fecha');
	const orderBy = fechaIndex !== -1 ? [[fechaIndex, 'desc']] : [[1, 'desc']];
	const tablaSel = $(window.tablaId);
	if (tablaSel.hasClass('dataTable')) {
		tablaSel.DataTable().clear().destroy();
	}

	const dt = tablaSel.DataTable({
		serverSide: true,
		processing: true,
		ajax: {
			url: `/facturacion/${modelo}/data`,
			type: 'GET',
			data: function (d) {
				d.fecha_desde = $('#f-desde').val();
				d.fecha_hasta = $('#f-hasta').val();
			}
		},
		columns: columnas,
		order: orderBy,
		pageLength: 40,
		pagingType: 'numbers',
		responsive: true,
		select: {
			style: 'multi',
			blurable: true,
			items: 'row',
			className: 'selected'
		},
		language: {
			search: '',
			processing: "",
			select: {
				rows: {
					_: '%d filas seleccionadas',
					// 0: 'Haz clic en una fila para seleccionarla',
					1: '1 fila seleccionada'
				},
				cells: {
					0: ""
				},				
				columns: {
					0: ""
				}
			}
		},
		columnDefs: (function () {
			const priorityKeys = ['fecha', 'cliente', 'guia', 'desplazamiento', 'origen', 'destino', 'costo_base', 'total_'];
			const priorityTargets = priorityKeys
				.map(key => columnas.findIndex(col => col.data === key))
				.filter(idx => idx >= 0);
			const idIndex = columnas.findIndex(col => col.data === 'id');
			const defs = idIndex !== -1 ? [{ targets: [idIndex], visible: false, searchable: false }] : [];
			if (priorityTargets.length) {
				defs.push({ targets: priorityTargets, responsivePriority: 1 });
			}
			return defs;
		})(),
		layout: {
			topStart: {
				buttons: botonesEspeciales()
			},
			topEnd: {
				buttons: botonesAuxiliares(),
				search: true
			}
		},
		createdRow: function (row, data) {
			if (data && data.status) {
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
			}
		},
		footerCallback: function (row, data) {
			if (!Array.isArray(data) || data.length === 0) return;
			const total = data.reduce((acc, row) => {
				const usarBs = localStorage.getItem('Bs') === 'true';
				const value = parseFloat(usarBs ? row.total_ * tasaGlobal : row.total_) || 0;
				return acc + value;
			}, 0);
			const api = this.api();
			const totalColumnIndex = columnas.findIndex(col => col.data === 'total_');
			if (totalColumnIndex !== -1) {
				$(api.column(totalColumnIndex).footer()).html(`<strong>${total.toFixed(2)}</strong>`);
			}
		}
	});

	window.tablaInstancia = dt;

	// Redibujar en vivo al alternar Bs sin recargar página
	$(document).off('bolivares:toggled').on('bolivares:toggled', function () {
		dt.rows().invalidate().draw(false);
		// Si tiene footer de totales, recalcula al redibujar
		dt.columns.adjust();
	});
	// agregarDobleClickPersonalizado(window.tablaId, 'abrir_modal');
}

function inicializarTablaCobroDetalle() {
	const columnas = columnasCobroDetalle();
	const tablaSel = $(window.tablaId);
	if (tablaSel.hasClass('dataTable')) {
		tablaSel.DataTable().clear().destroy();
	}

	const dt = tablaSel.DataTable({
		serverSide: true,
		processing: true,
		ajax: {
			url: '/facturacion/cobro_detalle/data',
			type: 'GET',
			data: function (d) {
				d.fecha_desde = $('#f-desde').val();
				d.fecha_hasta = $('#f-hasta').val();
			}
		},
		columns: columnas,
		order: [[1, 'desc']],
		pageLength: 40,
		pagingType: 'numbers',
		responsive: true,
		select: {
			style: 'multi',
			blurable: true,
			items: 'row',
			className: 'selected'
		},
		language: {
			search: '',
			select: {
				rows: {
					_: 'Seleccionada %d filas',
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
		columnDefs: (function () {
			const priorityTargets = [1, 2, 3, 4, 6, 11, 12, 15].filter(idx => idx < columnas.length);
			const defs = [{ targets: [0], visible: false, searchable: false }];
			if (priorityTargets.length) {
				defs.push({ targets: priorityTargets, responsivePriority: 1 });
			}
			return defs;
		})(),
		layout: {
			topStart: {
				buttons: botonesEspeciales()
			},
			topEnd: {
				buttons: botonesAuxiliares(),
				search: true
			}
		},
		footerCallback: function (row, data) {
			if (!Array.isArray(data) || data.length === 0) return;
			const total = data.reduce((acc, row) => {
				const usarBs = localStorage.getItem('Bs') === 'true';
				const value = parseFloat(usarBs ? row.total_ * tasaGlobal : row.total_) || 0;
				return acc + value;
			}, 0);
			const api = this.api();
			const totalColumnIndex = columnas.findIndex(col => col.data === 'total_');
			if (totalColumnIndex !== -1) {
				$(api.column(totalColumnIndex).footer()).html(`<strong>${total.toFixed(2)}</strong>`);
			}
		}
	});

	window.tablaInstancia = dt;

	$(document).off('bolivares:toggled').on('bolivares:toggled', function () {
		dt.rows().invalidate().draw(false);
		dt.columns.adjust();
	});
}

function agregarFiltros(modelo) {
	$('#f-filtrar').on('click', function () {
		$(window.tablaId).DataTable().ajax.reload();
	});

	$('#f-limpiar').on('click', function () {
		$('#f-desde').val('');
		$('#f-hasta').val('');
		$(window.tablaId).DataTable().ajax.reload();
	});
}
