$(document).ready(function () {

    const FORM_FACTURACION_CLIENTE = $('#facturasClientesForm');
    const FORM_PAGO_OPERADOR = $('#pagosOperadoresForm');
    window.modulo = 'facturacion';

    const modelo = window.location.pathname.split('/').filter(Boolean).pop();
    window.tablaId = `#${modelo}Table`;

    console.log("Modelo actual:", modelo);

    if (modelo === 'cobro_detalle') {
        $.ajax({
            type: "GET",
            url: "/facturacion/get/cobro_detalle",
            data: {},
            dataType: "json",
            success: function (response) {
                if (response.success) {
                    console.log("Datos de cobro detalle:", response.data);
                    const keys = Object.keys(response.data[0]);
                    // console.log("Keys:", keys);
                    var columnas = keys.map(campo => ({
                        data: campo,
                        title: campo.charAt(0).toUpperCase() + campo.slice(1).replace('_', " "),
                    }));
                    console.log("Columnas:", columnas);
                    crearTabla("/facturacion/get/cobro_detalle", "#facturasCobrosDetalle", columnas);
                }
            },
       });
    }
    else {
        cargarTabla2(modelo, 'facturacion', null, [1, 2, 4, 5, 6, 7, 9, 10, 11, 19]);
        
        // // Agregar funcionalidad de doble click con modal de detalle mejorado
        // setTimeout(() => {
        //     agregarDobleClickPersonalizado(`#${modelo}Table`, 'abrir_modal');
        // }, 1000); // Esperar a que la tabla se cargue completamente
    }

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
        console.log(cliente_id);

        $('#titulo-fact').text(cliente_nombre);

        cargarTabla2('facturasClientes', 'facturacion', cliente_id, [1, 2, 5, 6, 7, 8, 10, 11, 12, 23]);
        
        // Agregar funcionalidad de doble click con modal de detalle mejorado para facturas de clientes
        setTimeout(() => {
            agregarDobleClickPersonalizado('#facturasClientesTable', 'abrir_modal');
        }, 1000);

    });

  


   
});
