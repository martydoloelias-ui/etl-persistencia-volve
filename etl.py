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