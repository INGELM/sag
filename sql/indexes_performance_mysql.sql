-- SAG - Indices de performance (MySQL)
-- Fecha: 2026-05-23
-- Objetivo:
-- 1) Crear indices de forma idempotente (solo si no existe un indice equivalente por columnas)
-- 2) Validar duplicados antes de crear unique sobre tarifas.codigo_desc
-- 3) No alterar logica de negocio

SET @OLD_SQL_SAFE_UPDATES = @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

-- ------------------------------------------------------------
-- Helpers
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS add_index_if_missing;
DELIMITER $$
CREATE PROCEDURE add_index_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64),
    IN p_cols_csv VARCHAR(255),
    IN p_cols_sql VARCHAR(255)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    SELECT COUNT(*) INTO v_exists
    FROM (
        SELECT index_name, GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ',') AS cols
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
        GROUP BY index_name
    ) s
    WHERE s.cols = p_cols_csv;

    IF v_exists = 0 THEN
        SET @sql_stmt = CONCAT(
            'ALTER TABLE `', p_table_name, '` ADD INDEX `', p_index_name, '` (', p_cols_sql, ')'
        );
        PREPARE stmt FROM @sql_stmt;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('OK: creado indice ', p_index_name, ' en ', p_table_name) AS resultado;
    ELSE
        SELECT CONCAT('SKIP: ya existe indice equivalente para (', p_cols_csv, ') en ', p_table_name) AS resultado;
    END IF;
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS add_unique_if_no_duplicates;
DELIMITER $$
CREATE PROCEDURE add_unique_if_no_duplicates(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64),
    IN p_col_name VARCHAR(64)
)
BEGIN
    DECLARE v_exists_equivalent INT DEFAULT 0;
    DECLARE v_duplicates INT DEFAULT 0;

    -- Si ya existe cualquier indice de una columna equivalente, no crear otro
    SELECT COUNT(*) INTO v_exists_equivalent
    FROM (
        SELECT index_name, GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ',') AS cols
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
        GROUP BY index_name
    ) s
    WHERE s.cols = p_col_name;

    IF v_exists_equivalent > 0 THEN
        SELECT CONCAT('SKIP: ya existe indice equivalente para (', p_col_name, ') en ', p_table_name) AS resultado;
    ELSE
        -- Validar duplicados no nulos antes de UNIQUE
        SET @dup_sql = CONCAT(
            'SELECT COUNT(*) FROM (',
            'SELECT `', p_col_name, '`, COUNT(*) c ',
            'FROM `', p_table_name, '` ',
            'WHERE `', p_col_name, '` IS NOT NULL ',
            'GROUP BY `', p_col_name, '` HAVING COUNT(*) > 1',
            ') d'
        );

        PREPARE dup_stmt FROM @dup_sql;
        EXECUTE dup_stmt;
        DEALLOCATE PREPARE dup_stmt;

        -- Repetimos la cuenta en variable para control de flujo
        SET @dup_sql_into = CONCAT(
            'SELECT COUNT(*) INTO @v_dup_count FROM (',
            'SELECT `', p_col_name, '`, COUNT(*) c ',
            'FROM `', p_table_name, '` ',
            'WHERE `', p_col_name, '` IS NOT NULL ',
            'GROUP BY `', p_col_name, '` HAVING COUNT(*) > 1',
            ') d'
        );

        PREPARE dup_stmt2 FROM @dup_sql_into;
        EXECUTE dup_stmt2;
        DEALLOCATE PREPARE dup_stmt2;

        SET v_duplicates = IFNULL(@v_dup_count, 0);

        IF v_duplicates = 0 THEN
            SET @sql_stmt = CONCAT(
                'ALTER TABLE `', p_table_name, '` ADD UNIQUE INDEX `', p_index_name, '` (`', p_col_name, '`)' 
            );
            PREPARE stmt FROM @sql_stmt;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            SELECT CONCAT('OK: creado unique ', p_index_name, ' en ', p_table_name, '(', p_col_name, ')') AS resultado;
        ELSE
            SELECT CONCAT('SKIP: no se crea unique ', p_index_name, ' porque hay ', v_duplicates, ' valores duplicados en ', p_table_name, '.', p_col_name) AS resultado;
            SET @show_dups = CONCAT(
                'SELECT `', p_col_name, '`, COUNT(*) repetidos ',
                'FROM `', p_table_name, '` ',
                'WHERE `', p_col_name, '` IS NOT NULL ',
                'GROUP BY `', p_col_name, '` HAVING COUNT(*) > 1 ',
                'ORDER BY repetidos DESC LIMIT 50'
            );
            PREPARE show_stmt FROM @show_dups;
            EXECUTE show_stmt;
            DEALLOCATE PREPARE show_stmt;
        END IF;
    END IF;
END$$
DELIMITER ;

-- ------------------------------------------------------------
-- Indices recomendados (prioridad alta)
-- ------------------------------------------------------------

-- programacion
CALL add_index_if_missing('programacion', 'idx_programacion_fecha_salida', 'fecha_salida', '`fecha_salida`');
CALL add_index_if_missing('programacion', 'idx_programacion_status', 'status', '`status`');
CALL add_index_if_missing('programacion', 'idx_programacion_guia', 'guia', '`guia`');
CALL add_index_if_missing('programacion', 'idx_programacion_operador', 'operador', '`operador`');
CALL add_index_if_missing('programacion', 'idx_programacion_fecha_status', 'fecha_salida,status', '`fecha_salida`,`status`');

-- tarifas
CALL add_index_if_missing('tarifas', 'idx_tarifas_empresa', 'empresa', '`empresa`');
CALL add_index_if_missing('tarifas', 'idx_tarifas_empresa_codigo', 'empresa,codigo', '`empresa`,`codigo`');
CALL add_index_if_missing('tarifas', 'idx_tarifas_codigo_desc', 'codigo_desc', '`codigo_desc`');

-- Opcional: unique para codigo_desc (solo si no hay duplicados)
CALL add_unique_if_no_duplicates('tarifas', 'uq_tarifas_codigo_desc', 'codigo_desc');

-- tarifas_operadores
CALL add_index_if_missing('tarifas_operadores', 'idx_tarifas_operadores_codigo_tipo', 'codigo,tipo', '`codigo`,`tipo`');

-- pasajeros
CALL add_index_if_missing('pasajeros', 'idx_pasajeros_empresa_nombres', 'empresa,nombres', '`empresa`,`nombres`');

-- facturas_clientes
CALL add_index_if_missing('facturas_clientes', 'idx_facturas_clientes_programacion', 'programacion', '`programacion`');
CALL add_index_if_missing('facturas_clientes', 'idx_facturas_clientes_tarifas_cliente', 'tarifas_cliente', '`tarifas_cliente`');
CALL add_index_if_missing('facturas_clientes', 'idx_facturas_clientes_status', 'status', '`status`');

-- facturas_operadores
CALL add_index_if_missing('facturas_operadores', 'idx_facturas_operadores_programacion', 'programacion', '`programacion`');
CALL add_index_if_missing('facturas_operadores', 'idx_facturas_operadores_tarifas_operador', 'tarifas_operador', '`tarifas_operador`');

-- tabla pivote programacion_pasajeros (M:N)
CALL add_index_if_missing('programacion_pasajeros', 'idx_prog_pasajero_programacion_pasajero', 'programacion,pasajero', '`programacion`,`pasajero`');
CALL add_index_if_missing('programacion_pasajeros', 'idx_prog_pasajero_pasajero_programacion', 'pasajero,programacion', '`pasajero`,`programacion`');

-- ------------------------------------------------------------
-- Verificacion final
-- ------------------------------------------------------------
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

-- Limpieza helpers
DROP PROCEDURE IF EXISTS add_index_if_missing;
DROP PROCEDURE IF EXISTS add_unique_if_no_duplicates;

SET SQL_SAFE_UPDATES = @OLD_SQL_SAFE_UPDATES;
