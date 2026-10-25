CREATE TABLE IF NOT EXISTS produccion_mensual (
    pozo                     TEXT    NOT NULL,
    mes                      TEXT    NOT NULL,  -- formato 'YYYY-MM'
    dias_produccion          INTEGER NOT NULL,
    petroleo_total           REAL    NOT NULL,
    petroleo_promedio_diario REAL    NOT NULL,
    PRIMARY KEY (pozo, mes)
);