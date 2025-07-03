$(document).ready(function () {
    console.log("auxiliares  initialized");

    var urlSegments = window.location.pathname.split('/').filter(Boolean);
    var lastSegment = urlSegments[urlSegments.length - 1];
    console.log("Último segmento de la URL:", lastSegment);

    if (lastSegment !== 'tasa') {
        cargarTabla1(lastSegment);
    }

    $("#ciudadesForm").submit(function (e) {
        e.preventDefault();
        guardarRegistro('ciudades');
    });

    $('#ciudadesTable tbody').on('click', 'tr', function () {
        var table = $('#ciudadesTable').DataTable();
        var data = table.row(this).data();
        if (data) {
            // Aquí puedes manejar los datos de la fila seleccionada
            console.log('Datos de la fila seleccionada:', data);
            // Por ejemplo, llenar un formulario con los datos:

        }
    });

    //  VEHICULOS


    $("#vehiculosForm").submit(function (e) {
        e.preventDefault();
        guardarRegistro('vehiculos');
    });

    $('#vehiculosTable tbody').on('click', 'tr', function () {
        var table = $('#vehiculosTable').DataTable();
        var data = table.row(this).data();
        if (data) {
            // Aquí puedes manejar los datos de la fila seleccionada
            console.log('Datos de la fila seleccionada:', data);
            // Por ejemplo, llenar un formulario con los datos:

        }
    });

    $('#tasaForm').submit(function (e) {
        e.preventDefault();

        const form = this;
        const isValid = form.checkValidity();
        var form_data = new FormData(this);

        Swal.fire({
            title: 'Actualizando...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });




        $.ajax({
            type: "PUT",
            url: "/tasa",
            data: form_data,
            processData: false,
            contentType: false,
            success: function (response) {
                Swal.close(); 
                if (response.success) {
                    
                    Swal.fire(
                        {
                            title: 'Tasa Actualizada',
                            icon: 'success',
                            timer: 1500,
                            showConfirmButton: false,
                            timerProgressBar: true
                        }).then(function () {
                            window.location.reload(); // Redirigir a la página de tasas
                        });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: response.mensaje || 'Error al actualizar la tasa',
                        text: response.errores || 'Ocurrió un error al actualizar la tasa.',
                        timer: 2000,
                        timerProgressBar: true,
                        showConfirmButton: true
                    });
                }
            }, error: function (xhr, status, error) {
                Swal.close();
                console.error('Error al actualizar la tasa:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error al actualizar la tasa',
                    text: 'Ocurrió un error al procesar la solicitud.',
                    timer: 2000,
                    timerProgressBar: true,
                    showConfirmButton: true
                });
            }
        });
    });


});
