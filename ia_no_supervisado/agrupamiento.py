"""Agrupa conexiones del grafo de transporte con K-Means.

El módulo es independiente del programa de rutas original. Lee un CSV local y
exporta una tabla asignada, un resumen y una gráfica para inspección académica.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Permite crear la gráfica sin abrir una ventana.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent
CSV_POR_DEFECTO = BASE_DIR / "data" / "conexiones_transporte.csv"
SALIDA_POR_DEFECTO = BASE_DIR / "resultados"
COLUMNAS_REQUERIDAS = [
    "id_conexion", "origen", "destino", "medio", "tiempo_min", "costo_simplificado"
]
COLUMNAS_TEXTO = ["id_conexion", "origen", "destino", "medio"]
COLUMNAS_NUMERICAS = ["tiempo_min", "costo_simplificado"]


def cargar_y_validar(ruta_csv: str | Path = CSV_POR_DEFECTO) -> pd.DataFrame:
    """Carga el CSV, valida su esquema y limpia filas incompletas o inválidas."""
    ruta = Path(ruta_csv)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {ruta}")

    try:
        datos = pd.read_csv(ruta, encoding="utf-8-sig")
    except (UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"No se pudo leer el CSV {ruta}: {exc}") from exc

    faltantes = sorted(set(COLUMNAS_REQUERIDAS) - set(datos.columns))
    if faltantes:
        raise ValueError("Faltan columnas obligatorias: " + ", ".join(faltantes))

    datos = datos[COLUMNAS_REQUERIDAS].copy()
    for columna in COLUMNAS_TEXTO:
        datos[columna] = datos[columna].astype("string").str.strip()
        datos[columna] = datos[columna].replace("", pd.NA)
    for columna in COLUMNAS_NUMERICAS:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    # Se eliminan únicamente filas que no pueden usarse de forma segura.
    datos = datos.dropna(subset=COLUMNAS_REQUERIDAS)
    datos = datos[(datos["tiempo_min"] >= 0) & (datos["costo_simplificado"] >= 0)]
    datos = datos.drop_duplicates(subset=[
        "origen", "destino", "medio", "tiempo_min", "costo_simplificado"
    ])
    datos = datos.reset_index(drop=True)

    if datos.empty:
        raise ValueError("El dataset quedó vacío después de la validación y limpieza.")
    if datos["medio"].nunique() < 1:
        raise ValueError("La columna 'medio' no tiene categorías útiles.")
    return datos


def preparar_variables(datos: pd.DataFrame) -> np.ndarray:
    """Escala tiempo/costo y convierte el medio en columnas indicadoras."""
    faltantes = sorted(set(COLUMNAS_REQUERIDAS) - set(datos.columns))
    if faltantes:
        raise ValueError("El DataFrame no contiene las columnas: " + ", ".join(faltantes))

    # Tiempo y costo se escalan para que sus magnitudes no dominen el cálculo.
    escalador = StandardScaler()
    numericas = escalador.fit_transform(datos[COLUMNAS_NUMERICAS].astype(float))

    # Los medios son categorías; get_dummies las expresa como 0/1, no como orden.
    categoricas = pd.get_dummies(datos["medio"].astype(str), prefix="medio", dtype=float)
    matriz = np.column_stack([numericas, categoricas.to_numpy(dtype=float)])
    return matriz


def construir_resumen(agrupados: pd.DataFrame) -> pd.DataFrame:
    """Resume el tamaño y las características de cada grupo."""
    resumen = agrupados.groupby("grupo", sort=True).agg(
        cantidad_conexiones=("id_conexion", "count"),
        tiempo_promedio_min=("tiempo_min", "mean"),
        costo_promedio_simplificado=("costo_simplificado", "mean"),
        medios_mas_frecuentes=(
            "medio",
            lambda serie: ", ".join(serie.value_counts().head(3).index.astype(str)),
        ),
    ).reset_index()
    resumen["tiempo_promedio_min"] = resumen["tiempo_promedio_min"].round(2)
    resumen["costo_promedio_simplificado"] = resumen["costo_promedio_simplificado"].round(2)
    return resumen


def entrenar_modelo(datos: pd.DataFrame, cantidad_grupos: int = 3) -> tuple[pd.DataFrame, pd.DataFrame, Optional[float]]:
    """Entrena K-Means y devuelve conexiones etiquetadas, resumen y silueta."""
    if cantidad_grupos < 2:
        raise ValueError("K-Means necesita al menos 2 grupos para este ejercicio.")
    if len(datos) <= cantidad_grupos:
        raise ValueError(
            f"Se necesitan más registros que grupos: hay {len(datos)} registros y "
            f"se solicitaron {cantidad_grupos} grupos."
        )

    matriz = preparar_variables(datos)
    modelo = KMeans(n_clusters=cantidad_grupos, random_state=42, n_init=10)
    etiquetas = modelo.fit_predict(matriz)

    agrupados = datos.copy()
    agrupados["grupo"] = etiquetas.astype(int)
    resumen = construir_resumen(agrupados)

    silueta: Optional[float] = None
    grupos_detectados = np.unique(etiquetas)
    if 2 <= len(grupos_detectados) <= len(datos) - 1:
        silueta = float(silhouette_score(matriz, etiquetas))
    return agrupados, resumen, silueta


def crear_grafica(agrupados: pd.DataFrame, destino: str | Path) -> Path:
    """Guarda la gráfica tiempo/costo coloreada por grupo."""
    archivo = Path(destino)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    generador = np.random.default_rng(42)

    fig, ax = plt.subplots(figsize=(9.4, 5.7), dpi=160)
    for grupo in sorted(agrupados["grupo"].unique()):
        segmento = agrupados[agrupados["grupo"] == grupo]
        # Pequeño desplazamiento solo visual para separar puntos superpuestos.
        x = segmento["tiempo_min"].to_numpy(float) + generador.normal(0, 0.055, len(segmento))
        y = segmento["costo_simplificado"].to_numpy(float) + generador.normal(0, 9, len(segmento))
        ax.scatter(x, y, s=72, alpha=0.82, label=f"Grupo {grupo}")
    ax.set_title("Agrupamiento de conexiones del sistema de rutas", fontsize=13, pad=12)
    ax.set_xlabel("Tiempo simplificado por conexión (minutos)")
    ax.set_ylabel("Costo simplificado del proyecto (sin unidad tarifaria confirmada)")
    ax.grid(True, alpha=0.25)
    ax.legend(title="K-Means")
    fig.text(
        0.01, 0.01,
        "El desplazamiento leve evita puntos superpuestos y solo afecta la visualización, no el modelo.",
        fontsize=7.5,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(archivo, bbox_inches="tight")
    plt.close(fig)
    return archivo


def ejecutar(
    ruta_csv: str | Path = CSV_POR_DEFECTO,
    carpeta_salida: str | Path = SALIDA_POR_DEFECTO,
    cantidad_grupos: int = 3,
) -> dict:
    """Ejecuta toda la cadena y guarda resultados reproducibles."""
    salida = Path(carpeta_salida)
    salida.mkdir(parents=True, exist_ok=True)
    datos = cargar_y_validar(ruta_csv)
    agrupados, resumen, silueta = entrenar_modelo(datos, cantidad_grupos)

    ruta_asignaciones = salida / "conexiones_agrupadas.csv"
    ruta_resumen = salida / "resumen_grupos.csv"
    ruta_grafica = salida / "grafica_agrupamiento.png"
    agrupados.to_csv(ruta_asignaciones, index=False, encoding="utf-8-sig")
    resumen.to_csv(ruta_resumen, index=False, encoding="utf-8-sig")
    crear_grafica(agrupados, ruta_grafica)

    print("\nAGRUPAMIENTO DE CONEXIONES - K-MEANS")
    print(f"Dataset validado: {len(datos)} conexiones")
    print(f"Grupos solicitados: {cantidad_grupos}")
    print("\nResumen por grupo:")
    print(resumen.to_string(index=False))
    if silueta is None:
        print("Coeficiente de silueta: no disponible para esta distribución de grupos.")
    else:
        print(f"Coeficiente de silueta: {silueta:.3f} (interpretar con cautela por el tamaño y tipo de datos)")
    print("\nArchivos creados:")
    print(f"- Asignaciones: {ruta_asignaciones}")
    print(f"- Resumen: {ruta_resumen}")
    print(f"- Gráfica: {ruta_grafica}")
    print("Advertencia: tiempos y costos provienen del modelo académico del repositorio, no de mediciones en tiempo real.")

    return {
        "datos": datos,
        "agrupados": agrupados,
        "resumen": resumen,
        "silueta": silueta,
        "asignaciones_csv": ruta_asignaciones,
        "resumen_csv": ruta_resumen,
        "grafica_png": ruta_grafica,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Agrupa conexiones del grafo de transporte de Medellín.")
    parser.add_argument("--csv", default=str(CSV_POR_DEFECTO), help="Ruta del dataset CSV")
    parser.add_argument("--salida", default=str(SALIDA_POR_DEFECTO), help="Carpeta para los resultados")
    parser.add_argument("--grupos", type=int, default=3, help="Cantidad de grupos para K-Means (predeterminado: 3)")
    args = parser.parse_args()
    try:
        ejecutar(args.csv, args.salida, args.grupos)
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
