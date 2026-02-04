// Inicialización específica de DataTable para Tarifas con procesamiento en servidor
$(document).ready(function () {
	// Contexto global para reutilizar acciones definidas en app.js
	window.modulo = 'clientes';
	window.modelo = 'tarifas';
	window.tablaId = '#tarifasTable';

	const columnas = [
		{ data: 'id', title: 'ID', visible: false, searchable: false, className: 'no-report' },
		{ data: 'codigo', title: 'Código' },
		{ data: 'empresa', title: 'Empresa' },
		{ data: 'origen', title: 'Origen' },
		{ data: 'destino', title: 'Destino' },
		{ data: 'vehiculo', title: 'Vehículo' },
		{ data: 'desplazamiento', title: 'Desplazamiento' },
		{ data: 'horario', title: 'Horario' },
		{ data: 'espera', title: 'Espera' },
		{ data: 'desvios', title: 'Desvíos' },
		{ data: 'base', title: 'Base' },
		{ data: 'tarifa_km', title: 'Tarifa/Km' },
		// Campos auxiliares para ocultar pero permitir ordenamiento/consistencia
		{ data: 'empresa_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'origen_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'destino_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'vehiculo_rel', visible: false, searchable: false, className: 'no-report' },
		{ data: 'color_rel', visible: false, searchable: false, className: 'no-report' },
		// Acciones
		{
			data: null,
			title: '',
			orderable: false,
			className: 'no-report',
			searchable: false,
			render: function (_data, _type, row) {
				const color = row.color_rel || 'gray';
				return `<a href="/empleados/tarifasOperadores" title="Ver tarifas del operador">
							<i class="bx bxs-car" style="cursor:pointer;color:${color};"></i>
						</a>`;
			}
		}
	];

	// Crear/Destruir si existe
	const tablaSel = $(window.tablaId);
	if (tablaSel.hasClass('dataTable')) {
		tablaSel.DataTable().clear().destroy();
	}

	const dt = tablaSel.DataTable({
		processing: true,
		serverSide: true,
		ajax: {
			url: '/clientes/tarifas/get_data',
			type: 'GET',
			data: function (d) {
				// Permite filtrar por empresa si se setea en la vista: window.empresaId
				if (window.empresaId) {
					d.cliente = window.empresaId;
				}
			}
		},
		columns: columnas,
		responsive: true,
		pageLength: 50,
		pagingType: 'numbers',
		order: [[1, 'asc']], // Por código
		select: {
			style: 'multi',
			blurable: true,
			items: 'row',
			className: 'selected'
		},
		language: {
			processing: '',
			search: '',
			select: {
				rows: {
					_: 'Has seleccionado %d filas',
					// 0: 'Haz clic en una fila para seleccionarla',
					1: '1 fila seleccionada'
				}
			}
		},
		layout: {
			topStart: {
				// Exportación e impresión (usa configuración similar a app.js)
				buttons: typeof botonesEspeciales === 'function' ? botonesEspeciales() : []
			},
			topEnd: {
				// Botones auxiliares (Seleccionar todos, etc.) y Acciones
				buttons: typeof botonesAuxiliares === 'function'
					? botonesAuxiliares()
					: [],
				search: true
			}
		}
	});

	// Exponer instancia si se requiere invalidar/redibujar
	window.tablaInstancia = dt;
});
