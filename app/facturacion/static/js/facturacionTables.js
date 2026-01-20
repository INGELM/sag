$(document).ready(function () {
	const modelo = window.location.pathname.split('/').filter(Boolean).pop();

	window.modulo = 'facturacion';
	window.modelo = modelo;
	window.tablaId = `#${modelo}Table`;

	if (modelo === 'cobro_detalle') {
		$.getJSON('/facturacion/get/cobro_detalle', function (response) {
			if (!response || !response.success || !response.data || response.data.length === 0) {
				return;
			}

			const keys = Object.keys(response.data[0]);
			const columnas = keys.map(campo => ({
				data: campo,
				title: campo.charAt(0).toUpperCase() + campo.slice(1).replace('_', ' '),
			}));

			crearTabla('/facturacion/get/cobro_detalle', '#facturasCobrosDetalle', columnas);
		});

		return;
	}

	const columnasVisibles = {
		facturasClientes: [1, 2, 4, 5, 6, 7, 9, 10, 11, 19],
		pagosOperadores: [1, 2, 3, 4, 5, 8, 9, 10, 11, 14, 16, 18],
	};

	const visibles = columnasVisibles[modelo] || [];
	cargarTabla2(modelo, 'facturacion', null, visibles);
});
