-- SAG - Rollback de indices de performance (MySQL)
-- Fecha: 2026-05-23
-- Este script elimina solo los indices creados por indexes_performance_mysql.sql si existen.

DROP PROCEDURE IF EXISTS drop_index_if_exists;
DELIMITER $$
CREATE PROCEDURE drop_index_if_exists(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    SELECT COUNT(*) INTO v_exists
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = p_table_name
      AND index_name = p_index_name;

    IF v_exists > 0 THEN
        SET @sql_stmt = CONCAT(
            'ALTER TABLE `', p_table_name, '` DROP INDEX `', p_index_name, '`'
        );
        PREPARE stmt FROM @sql_stmt;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('OK: eliminado indice ', p_index_name, ' en ', p_table_name) AS resultado;
    ELSE
        SELECT CONCAT('SKIP: no existe indice ', p_index_name, ' en ', p_table_name) AS resultado;
    END IF;
END$$
DELIMITER ;

CALL drop_index_if_exists('programacion', 'idx_programacion_fecha_salida');
CALL drop_index_if_exists('programacion', 'idx_programacion_status');
CALL drop_index_if_exists('programacion', 'idx_programacion_guia');
CALL drop_index_if_exists('programacion', 'idx_programacion_operador');
CALL drop_index_if_exists('programacion', 'idx_programacion_fecha_status');

CALL drop_index_if_exists('tarifas', 'idx_tarifas_empresa');
CALL drop_index_if_exists('tarifas', 'idx_tarifas_empresa_codigo');
CALL drop_index_if_exists('tarifas', 'idx_tarifas_codigo_desc');
CALL drop_index_if_exists('tarifas', 'uq_tarifas_codigo_desc');

CALL drop_index_if_exists('tarifas_operadores', 'idx_tarifas_operadores_codigo_tipo');

CALL drop_index_if_exists('pasajeros', 'idx_pasajeros_empresa_nombres');

CALL drop_index_if_exists('facturas_clientes', 'idx_facturas_clientes_programacion');
CALL drop_index_if_exists('facturas_clientes', 'idx_facturas_clientes_tarifas_cliente');
CALL drop_index_if_exists('facturas_clientes', 'idx_facturas_clientes_status');

CALL drop_index_if_exists('facturas_operadores', 'idx_facturas_operadores_programacion');
CALL drop_index_if_exists('facturas_operadores', 'idx_facturas_operadores_tarifas_operador');

CALL drop_index_if_exists('programacion_pasajeros', 'idx_prog_pasajero_programacion_pasajero');
CALL drop_index_if_exists('programacion_pasajeros', 'idx_prog_pasajero_pasajero_programacion');

SELECT
    table_name,
    index_name,
    GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ',') AS columnas,
    non_unique
FROM information_schema.statistics
WHERE table_schema = DATABASE()
  AND table_name IN (
      'programacion',
      'tarifas',
      'tarifas_operadores',
      'pasajeros',
      'facturas_clientes',
      'facturas_operadores',
      'programacion_pasajeros'
  )
GROUP BY table_name, index_name, non_unique
ORDER BY table_name, index_name;

DROP PROCEDURE IF EXISTS drop_index_if_exists;
