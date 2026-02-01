$(document).ready(async function () {
	const modelo = window.location.pathname.split('/').filter(Boolean).pop();
	window.modulo = 'facturacion';
	window.modelo = modelo;
	window.mostrarBolivares = true;
	window.tablaId = `#${modelo}Table`;

	await cargarTasaGlobal();
	inicializarTablaPagosOperadores(modelo);
	agregarFiltrosPagosOperadores();
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
	return convertido.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function columnasPagosOperadores() {
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
		{ data: 'id', visible: false },
		{ data: 'fecha', title: 'Fecha' },
		{ data: 'Operador', title: 'Operador' },
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
		{ data: 'guia', title: 'Guía' },
		{ data: 'hora_salida', title: 'Hora salida' },
		{ data: 'hora_retorno', title: 'Hora retorno' },
		{ data: 'horario', title: 'Horario' },
		{ data: 'desplazamiento', title: 'Desplaz.' },
		{ data: 'origen', title: 'Origen' },
		{ data: 'destino', title: 'Destino' },
		{ data: 'distancia', title: 'Distancia' },
		{ data: 'desvíos', title: 'Desvíos' },
		{ data: 'total_desvios', title: 'Total desvíos', render: formatearMonto },
		{ data: 'tiempo_espera', title: 'T. espera' },
		{ data: 'total_espera', title: 'Total espera', render: formatearMonto },
		{ data: 'costo_base', title: 'Costo base', render: formatearMonto },
		{ data: 'total_', title: 'Total', render: formatearMonto },
	];
}

function inicializarTablaPagosOperadores(modelo) {
	const columnas = columnasPagosOperadores();
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
		pageLength: 50,
		lengthMenu: [50, 100, 150, 200],
		lengthChange: true,
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
			const priorityKeys = ['fecha', 'Operador', 'cliente', 'guia', 'desplazamiento', 'origen', 'destino', 'costo_base', 'total_'];
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
			},
			bottomStart: {
				pageLength: true,
				info: true
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
	// if (typeof agregarDobleClickPersonalizado === 'function') {
	// 	agregarDobleClickPersonalizado(window.tablaId, 'abrir_modal');
	// }
}

function agregarFiltrosPagosOperadores() {
	$('#f-filtrar').on('click', function () {
		$(window.tablaId).DataTable().ajax.reload();
	});

	$('#f-limpiar').on('click', function () {
		$('#f-desde').val('');
		$('#f-hasta').val('');
		$(window.tablaId).DataTable().ajax.reload();
	});
}
