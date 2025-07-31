$(document).ready(function () {
    console.log("Programacion  initialized");



    var urlSegments = window.location.pathname.split('/').filter(Boolean);
    var lastSegment = urlSegments[urlSegments.length - 1];
    const formulario = $(`#${lastSegment}Form`);
    window.ruta = `${lastSegment}/`;
    const PASAJEROS_SELECT = $('#pasajeros-select');
    const EMPRESA_SELECT = $('#empresa-select');
    const CIUDAD_ORIGEN = $('#programacionForm .origen-select');
    const CIUDAD_DESTINO = $('#programacionForm .destino-select');
    const VEHICULO_SELECT = $('#programacionForm .vehiculo-select');
    const DIRECCION_ORIGEN = $('#direccion-origen')
    const DIRECCION_DESTINO = $('#direccion-destino')

    window.tablaId = `#${lastSegment}Table`;

    cargarTabla2(lastSegment, "", "", [1, 3, 5, 15]);
    console.log("Tabla cargada para:", formulario);
    
    // Agregar funcionalidad de doble click para editar registros
    setTimeout(() => {
        agregarDobleClickPersonalizado(`#${lastSegment}Table`, 'abrir_modal');
    }, 1000); // Esperar a que la tabla se cargue completamente

    $(formulario).submit(function (e) {
        e.preventDefault();
        console.log("Formulario enviado:", this);
        var formData = new FormData(this);
        console.log("Datos del formulario:", formData);


        guardarRegistro(lastSegment);
    });




    // EMPRESA_SELECT.selectize(selectizeConfig);
    EMPRESA_SELECT.selectize(selectizeConfig);
    PASAJEROS_SELECT.selectize(selectizeConfig);
    CIUDAD_ORIGEN.selectize(selectizeConfig);
    CIUDAD_DESTINO.selectize(selectizeConfig);
    VEHICULO_SELECT.selectize(selectizeConfig);

    const config_direccion = {
        create: true,
        sortField: 'text',
        plugins: ['remove_button'],
        render: {
            option_create: function (data, escape) {
                return `<div class="create">Crear dirección <strong>${escape(data.input)}</strong>&hellip;</div>`;
            }
        }
    };

    DIRECCION_ORIGEN.selectize(config_direccion);

    DIRECCION_DESTINO.selectize(config_direccion);
        
 

    PASAJEROS_SELECT.on('change', function () {
        var pasajerosSeleccionados = $(this).val();
        console.log("Pasajeros seleccionados:", pasajerosSeleccionados);
        if (pasajerosSeleccionados && pasajerosSeleccionados.length > 0) {

            cargarDirecciones(pasajerosSeleccionados, DIRECCION_ORIGEN[0].selectize);
            cargarDirecciones(pasajerosSeleccionados, DIRECCION_DESTINO[0].selectize);
        }
    });

   
    function cargarDirecciones(pasajeros, selectize) {
        if (!pasajeros || pasajeros.length === 0) {
            selectize.clearOptions();
            return;
        }

        var URL_CONSULTA_DIRECCIONES = '/programacion/get/direcciones';
        
        $.ajax({
            type: "GET",
            url: URL_CONSULTA_DIRECCIONES,
            data: { 'pasajeros[]': pasajeros },
            dataType: "json",
            success: function (response) {
                if (response.success) {
                    console.log("Direcciones cargadas:", response.data);
                    selectize.clearOptions();
                    selectize.addOption(response.data);
                    selectize.refreshOptions(false);
                } else {
                    console.error("Error al cargar direcciones:", response.mensaje);
                }
            },
            error: function (xhr, status, error) {
                console.error("Error en la solicitud AJAX:", error);
            }
        });
    }

    // const EMPRESA_SELECTIZE = EMPRESA_SELECT[0].selectize;
    // EMPRESA_SELECTIZE.clearOptions();

    EMPRESA_SELECT.on('change', function () {
        var empresaId = $(this).val();
        console.log("Empresa ID cac:", empresaId);
        var URL_CONSULTA_ORIGEN = `/ciudades/origen?empresa=${empresaId}`;
        var origen_selectize = CIUDAD_ORIGEN[0].selectize;
        var URL_CONSULTA_VEHICULO = `/clientes/vehiculos?empresa=${empresaId}`;
        var vehiculo_selectize = VEHICULO_SELECT[0].selectize;

        var URL_CONSULTA_PASAJEROS = `/clientes/empresas/pasajeros?empresa=${empresaId}`;
        var PASAJEROS_selectize = PASAJEROS_SELECT[0].selectize;

        Promise.all([
            cargarSelectize(URL_CONSULTA_PASAJEROS, empresaId, PASAJEROS_selectize),
            cargarSelectize(URL_CONSULTA_ORIGEN, empresaId, origen_selectize),
            cargarSelectize(URL_CONSULTA_VEHICULO, empresaId, vehiculo_selectize)
        ]).then(() => {
            console.log("Todos los selectize dependientes han sido cargados");
        });
    });

    CIUDAD_ORIGEN.on('change', function () {
        var empresaId = EMPRESA_SELECT.val();
        var origenId = CIUDAD_ORIGEN[0].selectize.getValue();
        console.log("Empresa ID:", empresaId);
        console.log("Ciudad Origen ID:", origenId);
        var URL_CONSULTA_DESTINO = `/ciudades/destino?origen=${origenId}&empresa=${empresaId}`;
        var destino_selectize = CIUDAD_DESTINO[0].selectize;

        cargarSelectize(URL_CONSULTA_DESTINO, empresaId, destino_selectize);
    });


    $("#retorno-form").change(function (e) {
        e.preventDefault();
        if ($("#retorno-form").is(':checked')) {
            $("#h-retorno").removeClass("visually-hidden");
            console.log("Hora de retorno visible");
        }
        else {
            $("#h-retorno").addClass("visually-hidden");
        }

    });

    // $("#status").change(function (e) {
    //     e.preventDefault();
    //     if ($(this).val() === "Finalizado") {
    //         $("#desvios, #t-espera").removeClass("visually-hidden");
    //         console.log($(this).val());
    //     } else {
    //         $("#desvios, #t-espera").addClass("visually-hidden");
    //         console.log($(this).val());
    //     }

    // });

});




