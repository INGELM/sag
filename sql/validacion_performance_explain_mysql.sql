-- SAG - Validacion de performance con EXPLAIN
-- Fecha: 2026-05-23
-- Uso recomendado:
-- 1) Ejecutar este archivo antes de aplicar indices y guardar salida.
-- 2) Ejecutar sql/indexes_performance_mysql.sql.
-- 3) Ejecutar de nuevo este archivo y comparar.
--
-- Nota: usa valores de fechas y filtros similares a los de produccion.

-- ============================================================
-- 0) Contexto de version y base
-- ============================================================
SELECT DATABASE() AS db_actual, VERSION() AS mysql_version;

-- ============================================================
-- 1) Programacion - filtro por rango de fecha + status + orden
-- Ruta relacionada: app/programacion/routes.py get_data
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT p.id, p.fecha_salida, p.status, p.guia, p.workflow
FROM programacion p
WHERE p.fecha_salida >= '2026-01-01'
  AND p.fecha_salida <= '2026-12-31'
  AND p.status LIKE 'Por%'
ORDER BY p.fecha_salida DESC
LIMIT 50 OFFSET 0;

-- ============================================================
-- 2) Facturas clientes - join con programacion + filtro de fecha
-- Ruta relacionada: app/facturacion/routes.py facturas_clientes_data
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT fc.id, fc.factura, fc.status, p.fecha_salida, p.guia
FROM facturas_clientes fc
JOIN programacion p ON p.id = fc.programacion
WHERE p.fecha_salida >= '2026-01-01'
  AND p.fecha_salida <= '2026-12-31'
ORDER BY p.fecha_salida DESC
LIMIT 50 OFFSET 0;

-- ============================================================
-- 3) Pagos operadores - join con programacion + filtro de fecha
-- Ruta relacionada: app/facturacion/routes.py pagos_operadores_data
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT fo.id, fo.costo_total, p.fecha_salida, p.guia, p.operador
FROM facturas_operadores fo
JOIN programacion p ON p.id = fo.programacion
WHERE p.fecha_salida >= '2026-01-01'
  AND p.fecha_salida <= '2026-12-31'
ORDER BY p.fecha_salida DESC
LIMIT 50 OFFSET 0;

-- ============================================================
-- 4) Tarifas por empresa + orden por codigo (caso de tabla clientes)
-- Ruta relacionada: app/clientes/routes.py get_tarifas_server_data
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT t.id, t.empresa, t.codigo, t.codigo_desc
FROM tarifas t
WHERE t.empresa = 1
ORDER BY t.codigo DESC
LIMIT 50 OFFSET 0;

-- ============================================================
-- 5) Tarifas operadores por codigo y tipo (lookup puntual)
-- Ruta relacionada: app/facturacion/routes.py crear_pago_operador
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT toper.id, toper.codigo, toper.tipo
FROM tarifas_operadores toper
WHERE toper.codigo = 100
  AND toper.tipo = 'Fijo'
LIMIT 1;

-- ============================================================
-- 6) Pasajeros por empresa + orden por nombres
-- Ruta relacionada: app/clientes/routes.py pasajero_get
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT pa.id, pa.empresa, pa.nombres
FROM pasajeros pa
WHERE pa.empresa = 1
ORDER BY pa.nombres ASC
LIMIT 100;

-- ============================================================
-- 7) Tabla pivote M:N programacion_pasajeros
-- Ruta relacionada: joins sobre programacionModel.pasajeros
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT pp.programacion, pp.pasajero
FROM programacion_pasajeros pp
WHERE pp.programacion = 1000;

EXPLAIN FORMAT=TRADITIONAL
SELECT pp.programacion, pp.pasajero
FROM programacion_pasajeros pp
WHERE pp.pasajero = 2000;

-- ============================================================
-- 8) Consulta realista con joins (sin busqueda textual)
-- Aproxima base de DataTables en facturacion clientes
-- ============================================================
EXPLAIN FORMAT=TRADITIONAL
SELECT DISTINCT fc.id
FROM facturas_clientes fc
JOIN programacion p ON p.id = fc.programacion
LEFT JOIN programacion_pasajeros pp ON pp.programacion = p.id
LEFT JOIN pasajeros pa ON pa.id = pp.pasajero
LEFT JOIN clientes c ON c.id = pa.empresa
WHERE p.fecha_salida >= '2026-01-01'
  AND p.fecha_salida <= '2026-12-31'
ORDER BY p.fecha_salida DESC
LIMIT 50 OFFSET 0;

-- ============================================================
-- 9) Inventario de indices actual (para comparar antes/despues)
-- ============================================================
SELECT
  s.table_name,
  s.index_name,
  GROUP_CONCAT(s.column_name ORDER BY s.seq_in_index SEPARATOR ',') AS columnas,
  s.non_unique,
  s.index_type
FROM information_schema.statistics s
WHERE s.table_schema = DATABASE()
  AND s.table_name IN (
    'programacion',
    'tarifas',
    'tarifas_operadores',
    'pasajeros',
    'facturas_clientes',
    'facturas_operadores',
    'programacion_pasajeros'
  )
GROUP BY s.table_name, s.index_name, s.non_unique, s.index_type
ORDER BY s.table_name, s.index_name;
