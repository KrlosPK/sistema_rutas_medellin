"""Genera el CSV a partir de las conexiones que ya existen en conocimiento.py.

Ejecutar desde la raíz del repositorio:
    python ia_no_supervisado/generar_dataset.py

Este módulo no modifica conocimiento.py ni el sistema de rutas original.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]
if str(RAIZ_REPOSITORIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_REPOSITORIO))

try:
    from conocimiento import CONEXIONES
except ImportError as exc:
    raise SystemExit(
        "No se encontró conocimiento.py. Ejecuta este archivo desde la carpeta "
        "ia_no_supervisado dentro del repositorio sistema_rutas_medellin."
    ) from exc

SALIDA = Path(__file__).resolve().parent / "data" / "conexiones_transporte.csv"
CAMPOS = ["id_conexion", "origen", "destino", "medio", "tiempo_min", "costo_simplificado"]


def generar_csv() -> Path:
    """Convierte CONEXIONES en una tabla CSV estable y reproducible."""
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS)
        escritor.writeheader()
        for numero, (origen, destino, medio, tiempo, costo) in enumerate(CONEXIONES, start=1):
            escritor.writerow({
                "id_conexion": f"C{numero:03d}",
                "origen": origen,
                "destino": destino,
                "medio": medio,
                "tiempo_min": tiempo,
                "costo_simplificado": costo,
            })
    print(f"Dataset generado: {SALIDA}")
    print(f"Registros escritos: {len(CONEXIONES)}")
    print("Nota: los tiempos y costos conservan el carácter académico/simplificado del proyecto.")
    return SALIDA


if __name__ == "__main__":
    generar_csv()
