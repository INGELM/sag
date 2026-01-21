// Inicialización independiente de la tabla de usuarios (empleados)
$(document).ready(function () {
  try {
    // Asegurar que estamos en la vista de empleados
    var lastSegment = window.location.pathname.split('/').filter(Boolean).pop();
    if (lastSegment !== 'empleados') return;

    window.modulo = 'empleados';
    window.modelo = 'empleados';
    window.tablaId = '#empleadosTable';

    // Columnas visibles con mayor prioridad en móvil (ajusta si necesitas)
    const columnasPrioritarias = [1];

    // Cargar tabla usando el helper genérico
    cargarTabla1('empleados', 'empleados', columnasPrioritarias);
  } catch (e) {
    console.error('Error inicializando usuariosTable:', e);
  }
});
