$(document).ready(function () {

    const FORM_FACTURACION_CLIENTE = $('#facturasClientesForm');
    const FORM_PAGO_OPERADOR = $('#pagosOperadoresForm');
    window.modulo = 'facturacion';

    const modelo = window.modelo || window.location.pathname.split('/').filter(Boolean).pop();
    window.tablaId = window.tablaId || `#${modelo}Table`;

    FORM_FACTURACION_CLIENTE.on('submit', function (e) {
        e.preventDefault();
        guardarRegistro(modelo, 'facturacion');
    });

    FORM_PAGO_OPERADOR.on('submit', function (e) {
        e.preventDefault();
        guardarRegistro('pagosOperadores', 'facturacion');
    });

    $('#btnfactCliente li a').on('click', function (e) {
        e.preventDefault();
        const cliente_id = $(this).data('cliente');
        const cliente_nombre = $(this).text();
        //console.log(cliente_id);

        $('#titulo-fact').text(cliente_nombre);

        // cargarTabla2('facturasClientes', 'facturacion', cliente_id, [1, 2, 5, 6, 7, 8, 10, 11, 12, 23]);
        
        // Agregar funcionalidad de doble click con modal de detalle mejorado para facturas de clientes
        // setTimeout(() => {
        //     agregarDobleClickPersonalizado('#facturasClientesTable', 'abrir_modal');
        // }, 1000);

    });

  


   
});
