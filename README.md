# ETL de producción de petróleo (Volve) a SQLite

Script en Python que lee la producción diaria por pozo del campo Volve
(Equinor) desde un CSV, la agrega por mes y la carga en una base SQLite
local. El proceso es repetible: se puede ejecutar varias veces sin
duplicar datos.

## Requisitos

- Python 3.9 o superior.
- No necesita instalar librerías externas: usa solo `csv` y `sqlite3`,
  que vienen incluidas con Python.

## Pasos para ejecutar

1. Clonar el repositorio y entrar a la carpeta:

   ```bash
   git clone <url-del-repo>
   cd etl-persistencia-volve
   ```

2. Ejecutar el ETL:

   ```bash
   python etl.py
   ```

3. Se crea el archivo `volve.db` con la tabla `produccion_mensual`.
   Resultado esperado: 298 filas. Para consultarlas:

   ```bash
   python -c "import sqlite3; con = sqlite3.connect('volve.db'); print(con.execute('SELECT * FROM produccion_mensual LIMIT 5').fetchall())"
   ```

## Patrón de datos

- **Extract**: `data/produccion_volve.csv`, un registro por pozo y por
  día con producción de petróleo (8.007 registros, fuente transaccional).
- **Transform**: se agrupa por pozo y mes. Se calcula la cantidad de
  días con producción, el petróleo total y el promedio diario. Las
  filas con volumen inválido o menor o igual a 0 se descartan y se
  cuentan.
- **Load**: se cargan en SQLite en la tabla `produccion_mensual`
  (298 registros, destino analítico).

## Esquema de la base (DDL)

Definido en `schema.sql`:

| Columna                    | Tipo    | Descripción                          |
|----------------------------|---------|--------------------------------------|
| pozo                       | TEXT    | Nombre del pozo                      |
| mes                        | TEXT    | Mes en formato `YYYY-MM`             |
| dias_produccion            | INTEGER | Días del mes con producción          |
| petroleo_total             | REAL    | Petróleo producido en el mes         |
| petroleo_promedio_diario   | REAL    | `petroleo_total / dias_produccion`   |

Clave primaria: `(pozo, mes)`.

## Cómo evita duplicados

La tabla se crea con `CREATE TABLE IF NOT EXISTS` y la carga usa
`INSERT ... ON CONFLICT (pozo, mes) DO UPDATE`. Si el script se corre
de nuevo, las filas existentes se actualizan en lugar de insertarse otra
vez, y la tabla se mantiene en 298 filas.

## Manejo de errores

- Si falta el CSV o el `schema.sql`, el script muestra un mensaje claro
  y termina sin romperse.
- Si hay un error de base de datos, la carga se revierte (rollback) y se
  informa el motivo.