// Inicialización de DataTable server-side para Tarifas de Operadores
$(document).ready(function () {
	const tablaId = '#tarifasOperadoresTable';
	const tablaSel = $(tablaId);

	// Limpiar instancia previa
	if (tablaSel.hasClass('dataTable')) {
		tablaSel.DataTable().clear().destroy();
	}

	const wrapperId = '#tarifasOperadoresTable_wrapper';

	const columnas = [
		{ data: 'id', visible: false },
		{ data: 'codigo', title: 'Código' },
		{ data: 'empresa', title: 'Empresa' },
		{ data: 'origen', title: 'Origen' },
		{ data: 'destino', title: 'Destino' },
		{ data: 'vehiculo', title: 'Vehículo' },
		{ data: 'desplazamiento', title: 'Desplazamiento' },
		{ data: 'tipo', title: 'Tipo' },
		{ data: 'espera', title: 'Espera' },
		{ data: 'desvios', title: 'Desvíos' },
		{ data: 'base', title: 'Base' }
	];

	const dt = tablaSel.DataTable({
		processing: true,
		serverSide: true,
		ajax: {
			url: '/empleados/tarifasOperadores/get_data',
			type: 'GET',
			data: function (d) {
				if (window.empresaId) {
					d.empresa = window.empresaId;
				}
			}
		},
		columns: columnas,
		autoWidth: false,
		scrollX: true,
		responsive: true,
		pageLength: 50,
		pagingType: 'numbers',
		order: [[1, 'asc']],
		language: {
			processing: '',
			search: '',
			info: '_START_ a _END_ de _TOTAL_ entradas',
			infoEmpty: '0 entradas',
			infoFiltered: '(filtrado de _MAX_ entradas totales)'
		},
		// initComplete: function () {
		// 	this.api().columns.adjust().responsive.recalc();
		// }
	});

	window.tarifasOperadoresDT = dt;
});
