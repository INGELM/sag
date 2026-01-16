$(document).ready(function () {

    var lastSegment = window.location.pathname.split('/').pop();
    var FORMULARIO = $(`#${lastSegment}Form`);
    var EMPRESA_SELECT = $('#empresa-tarifa');
    var CODIGO_SELECT = $('#codigo-tarifa');
    var URL_TARIFAS = `/clientes/get/tarifas?empresa=`;

    cargarTabla1(lastSegment, 'empleados', [1]);

    EMPRESA_SELECT.selectize(selectizeConfig);
    CODIGO_SELECT.selectize(selectizeConfig);

    EMPRESA_SELECT.on('change', function () {
        var empresaId = $(this).val();
        console.log(empresaId)

        cargarSelectize(URL_TARIFAS + empresaId, empresaId, CODIGO_SELECT[0].selectize);
    });

    CODIGO_SELECT.on('change', function(){
        var codigoTo =  CODIGO_SELECT.val();
        console.log(codigoTo)
        $.ajax({
            type: "GET",
            url: `/clientes/tarifas/get_data/${codigoTo}`,
            // data: "data",
            dataType: "json",
            success: function (response) {
                if (response.success){
                    console.log(response.data)
                    $('#origen-to').val(response.data.origen_nombre);
                    $('#destino-to').val(response.data.destino_nombre);
                    $('#desplazamiento-to').val(response.data.desplazamiento);
                }
                else{
                    console.log("error en consulta:", response.error)
                }
            },
            error: function (error) {
                console.log("error en la llamada ajax")
            }
       
        });
    });




 

    $('.telefono').on('input', function () {
        const phoneInput = document.getElementById('telefono');
        const maskOptions = {
            mask: '(0000)-000-0000'
        };
        IMask(phoneInput, maskOptions);

    });

    $(FORMULARIO).submit(function (e) {
        e.preventDefault();
        guardarRegistro(lastSegment);
    });



    $('#empleadosTable tbody').on('click', 'tr', function () {
        var table = $('#empleadosTable').DataTable();
        var data = table.row(this).data();
        if (data) {
            // Aquí puedes manejar los datos de la fila seleccionada
            //console.log('Datos de la fila seleccionada:', data);
            // Por ejemplo, llenar un formulario con los datos:
    
        }
    });

    


});
