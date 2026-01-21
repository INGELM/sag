// Inicialización independiente de la tabla de clientes
$(document).ready(function () {
  try {
    const lastSegment = window.location.pathname.split('/').filter(Boolean).pop();
    if (lastSegment !== 'clientes') return; // Solo en la vista clientes

    window.modulo = 'clientes';
    window.modelo = 'clientes';
    window.tablaId = '#clientesTable';

    const columnasPrioritarias = [1];
    cargarTabla1('clientes', 'clientes', columnasPrioritarias);
  } catch (e) {
    console.error('Error inicializando clientesTable:', e);
  }
});
