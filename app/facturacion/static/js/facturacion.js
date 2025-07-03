$(document).ready(function () {

    const FORM_FACTURACION_CLIENTE = $('#facturasClientesForm');
    window.modulo = 'facturacion';

    const modelo = window.location.pathname.split('/').filter(Boolean).pop();





    console.log("Modelo actual:", modelo);

    cargarTabla2(modelo, 'facturacion');

    FORM_FACTURACION_CLIENTE.on('submit', function (e) {
        e.preventDefault();
        guardarRegistro(modelo, 'facturacion');
    });

    $('#btnfactCliente li a').on('click', function (e) {
        e.preventDefault();
        const cliente_id = $(this).data('cliente');
        const cliente_nombre = $(this).text();
        console.log(cliente_id);

        $('#titulo-fact').text(cliente_nombre);

        cargarTabla2('facturasClientes', 'facturacion', cliente_id);

    });



});
