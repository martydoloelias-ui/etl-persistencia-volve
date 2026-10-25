"""
etl.py

ETL de produccion de petroleo (campo Volve):
CSV con produccion diaria por pozo -> agregacion mensual -> tabla
produccion_mensual en SQLite.
"""

import csv
import sqlite3
from collections import defaultdict

RUTA_CSV = "data/produccion_volve.csv"
RUTA_DB = "volve.db"
RUTA_SCHEMA = "schema.sql"


def extraer(ruta):
    """Lee el CSV y devuelve una lista de diccionarios, uno por fila."""
    try:
        with open(ruta, newline="", encoding="utf-8") as archivo:
            return list(csv.DictReader(archivo))
    except FileNotFoundError:
        print(
            f"[ERROR] No se encontro el archivo '{ruta}'. "
            "Verifica que exista la carpeta data/ con el CSV."
        )
        return []


def transformar(filas):
    """
    Agrega la produccion diaria por (pozo, mes).

    Devuelve (registros, descartadas): una lista de tuplas
    (pozo, mes, dias_produccion, petroleo_total, petroleo_promedio_diario)
    y la cantidad de filas descartadas por datos invalidos.
    """
    acumulado = defaultdict(lambda: [0, 0.0])
    descartadas = 0

    for fila in filas:
        try:
            volumen = float(fila["oil_vol"])
            mes = fila["fecha"][:7]  # 'YYYY-MM'
            if volumen <= 0 or len(mes) != 7:
                raise ValueError("fila invalida")
        except (ValueError, KeyError):
            descartadas += 1
            continue

        parcial = acumulado[(fila["pozo"], mes)]
        parcial[0] += 1
        parcial[1] += volumen

    registros = [
        (pozo, mes, dias, round(total, 2), round(total / dias, 2))
        for (pozo, mes), (dias, total) in sorted(acumulado.items())
    ]
    return registros, descartadas


def cargar(conexion, registros):
    """
    Crea la tabla destino (DDL en schema.sql) y carga los registros.

    Evita duplicados: la clave primaria (pozo, mes) junto con
    ON CONFLICT ... DO UPDATE hace que volver a correr el script
    actualice las filas existentes en vez de insertarlas de nuevo.
    """
    with open(RUTA_SCHEMA, encoding="utf-8") as archivo:
        conexion.executescript(archivo.read())

    with conexion:  # commit automatico, o rollback si hay un error
        conexion.executemany(
            """
            INSERT INTO produccion_mensual
                (pozo, mes, dias_produccion, petroleo_total, petroleo_promedio_diario)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (pozo, mes) DO UPDATE SET
                dias_produccion          = excluded.dias_produccion,
                petroleo_total           = excluded.petroleo_total,
                petroleo_promedio_diario = excluded.petroleo_promedio_diario
            """,
            registros,
        )


def main():
    print("1/3 Extrayendo datos...")
    filas = extraer(RUTA_CSV)
    if not filas:
        print("No hay datos para procesar. Se cancela el proceso.")
        return
    print(f"    Filas leidas: {len(filas)}")

    print("2/3 Transformando (agregacion mensual por pozo)...")
    registros, descartadas = transformar(filas)
    print(f"    Registros mensuales: {len(registros)} | filas descartadas: {descartadas}")

    print("3/3 Cargando en SQLite...")
    try:
        conexion = sqlite3.connect(RUTA_DB)
        try:
            cargar(conexion, registros)
            total = conexion.execute(
                "SELECT COUNT(*) FROM produccion_mensual"
            ).fetchone()[0]
        finally:
            conexion.close()
    except (sqlite3.Error, FileNotFoundError) as error:
        print(f"[ERROR] No se pudo cargar en la base de datos: {error}")
        return
    print(f"    Filas en produccion_mensual: {total}")
    print("Proceso completado.")


if __name__ == "__main__":
    main()