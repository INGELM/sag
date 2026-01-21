$(document).ready(function () {
    //console.log("clientes  initialized");

    var urlSegments = window.location.pathname.split('/').filter(Boolean);
    var lastSegment = urlSegments[urlSegments.length - 1];
    //console.log("Último segmento de la URL:", lastSegment);

    // Tabla principal se inicializa aparte en clientesTable.js cuando lastSegment === 'clientes'
    if (lastSegment && lastSegment !== 'clientes' && lastSegment !== 'tarifas') {
        cargarTabla1(lastSegment, 'clientes');
    }

    const formulario = $(`#${lastSegment}Form`);

    window.ruta = `clientes/${lastSegment}/`;

     $(`#telefono-${lastSegment}`).on('input', function () {
        const phoneInput = document.querySelector(`#telefono-${lastSegment}`);
        const maskOptions = {
            mask: '0000-000-0000'
        };
        IMask(phoneInput, maskOptions);

    });

    formulario.submit(function (e) {
        e.preventDefault();

        guardarRegistro(lastSegment);

        //console.log("Formulario enviado para:", lastSegment);

    });

    var origenSelect = $(`#origenTarSelectize`).selectize({
        create: false,
        sortField: 'text',
        loadThrottle: 500,
        // preload: true,
        load: function(query, callback) {
            if (!query.length) return callback();
            $.ajax({
                url: '/ciudades/buscar',
                type: 'GET',
                dataType: 'json',
                data: {
                    q: query
                },
                success: function(results) {
                    callback(results.data);
                },
                error: function() {
                    callback();
                }
            });
        }
    });


    




});