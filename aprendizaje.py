"""
Aprendizaje supervisado sobre el sistema de rutas del Valle de Aburrá.

Idea: el sistema basado en conocimiento (DFS + reglas) actúa como "etiquetador".
Con él se genera un dataset (origen, destino, criterio -> ruta óptima) y se
entrenan modelos que APRENDEN a aproximar esa respuesta sin recorrer el grafo.

Tareas:
  - Clasificación: predecir la categoría de transbordos de la ruta (0, 1, 2+).
  - Regresión:     predecir el tiempo (min) y el costo ($) de la ruta.

Ejecución:  python aprendizaje.py
Requiere:   pandas, numpy, scikit-learn
"""
from collections import deque
from itertools import permutations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from conocimiento import ESTACIONES
from inferencia import seleccionar
from rutas import buscar, datos, grafo

SEMILLA = 42
CRITERIOS = ["1", "2", "3", "4"]
CAT = ["origen", "destino", "criterio", "medio_origen", "medio_destino"]
NUM = ["transb_origen", "transb_destino", "saltos_min"]


# ---------------------------------------------------------------- 1. DATASET
def saltos_minimos(origen):
    """BFS: número mínimo de estaciones a recorrer desde `origen` a cada nodo."""
    g, dist, cola = grafo(), {origen: 0}, deque([origen])
    while cola:
        x = cola.popleft()
        for y, *_ in g[x]:
            if y not in dist:
                dist[y] = dist[x] + 1
                cola.append(y)
    return dist


def generar_dataset():
    filas, omitidos = [], []
    for origen in ESTACIONES:
        dist = saltos_minimos(origen)
        for destino in ESTACIONES:
            if origen == destino:
                continue
            rutas = [datos(x) for x in buscar(origen, destino)]
            for c in CRITERIOS:
                try:
                    mejor = seleccionar([dict(r) for r in rutas], c)
                except ZeroDivisionError:
                    # inferencia.py divide por el costo; hay rutas de costo $0
                    # (solo tramos "Transbordo") que rompen el criterio 3.
                    omitidos.append((origen, destino, c))
                    continue
                if mejor is None:
                    continue
                filas.append(
                    {
                        "origen": origen,
                        "destino": destino,
                        "criterio": c,
                        "medio_origen": ESTACIONES[origen]["medio"],
                        "medio_destino": ESTACIONES[destino]["medio"],
                        "transb_origen": int(ESTACIONES[origen]["transbordo"]),
                        "transb_destino": int(ESTACIONES[destino]["transbordo"]),
                        "saltos_min": dist.get(destino, -1),
                        # etiquetas (lo que el sistema de reglas decidió)
                        "tiempo": mejor["tiempo"],
                        "costo": mejor["costo"],
                        "transbordos": mejor["transbordos"],
                        "clase_transb": min(mejor["transbordos"], 2),
                        # grupo: par NO ordenado, evita fuga de datos A->B vs B->A
                        "par": "|".join(sorted([origen, destino])),
                    }
                )
    return pd.DataFrame(filas), omitidos


# ------------------------------------------------------------ 2. UTILIDADES
def preprocesador(escalar=False):
    num = StandardScaler() if escalar else "passthrough"
    return ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
            ("num", num, NUM),
        ]
    )


def dividir(df):
    """70/30 manteniendo todos los criterios de un mismo par en el mismo lado."""
    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=SEMILLA)
    i_tr, i_te = next(gss.split(df, groups=df["par"]))
    return df.iloc[i_tr], df.iloc[i_te]


# ------------------------------------------------------------ 3. CLASIFICACIÓN
def clasificacion(tr, te):
    modelos = {
        "Regresión logística": (LogisticRegression(max_iter=2000), True),
        "KNN (k=5)": (KNeighborsClassifier(n_neighbors=5), True),
        "Árbol de decisión": (DecisionTreeClassifier(max_depth=8, random_state=SEMILLA), False),
        "Random Forest": (RandomForestClassifier(n_estimators=200, random_state=SEMILLA), False),
    }
    X_tr, X_te = tr[CAT + NUM], te[CAT + NUM]
    y_tr, y_te = tr["clase_transb"], te["clase_transb"]
    resultados, mejor = [], None
    for nombre, (m, esc) in modelos.items():
        pipe = Pipeline([("pre", preprocesador(esc)), ("m", m)]).fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        acc, f1 = accuracy_score(y_te, pred), f1_score(y_te, pred, average="macro")
        resultados.append({"modelo": nombre, "accuracy": acc, "f1_macro": f1})
        if mejor is None or f1 > mejor[1]:
            mejor = (nombre, f1, confusion_matrix(y_te, pred, labels=[0, 1, 2]))
    # línea base: predecir siempre la clase más frecuente
    base = (y_te == y_tr.mode()[0]).mean()
    resultados.append({"modelo": "Línea base (clase mayoritaria)", "accuracy": base, "f1_macro": np.nan})
    return pd.DataFrame(resultados), mejor


# ------------------------------------------------------------ 4. REGRESIÓN
def regresion(tr, te, objetivo):
    modelos = {
        "Regresión lineal": (LinearRegression(), True),
        "Ridge": (Ridge(alpha=1.0), True),
        "KNN (k=5)": (KNeighborsRegressor(n_neighbors=5), True),
        "Árbol de decisión": (DecisionTreeRegressor(max_depth=10, random_state=SEMILLA), False),
        "Random Forest": (RandomForestRegressor(n_estimators=200, random_state=SEMILLA), False),
    }
    X_tr, X_te = tr[CAT + NUM], te[CAT + NUM]
    y_tr, y_te = tr[objetivo], te[objetivo]
    filas = []
    for nombre, (m, esc) in modelos.items():
        pipe = Pipeline([("pre", preprocesador(esc)), ("m", m)]).fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        filas.append(
            {
                "modelo": nombre,
                "MAE": mean_absolute_error(y_te, pred),
                "RMSE": root_mean_squared_error(y_te, pred),
                "R2": r2_score(y_te, pred),
            }
        )
    base = np.full(len(y_te), y_tr.mean())
    filas.append(
        {
            "modelo": "Línea base (promedio)",
            "MAE": mean_absolute_error(y_te, base),
            "RMSE": root_mean_squared_error(y_te, base),
            "R2": r2_score(y_te, base),
        }
    )
    return pd.DataFrame(filas)


# ------------------------------------------- 5. USO DESDE OTROS ARCHIVOS
_MODELOS = {}  # caché: se entrena una sola vez por ejecución


def entrenar_modelos():
    """Entrena con TODO el dataset los modelos que usará main.py."""
    if _MODELOS:
        return _MODELOS
    df, _ = generar_dataset()
    X = df[CAT + NUM]
    for nombre, modelo, esc in [
        ("transbordos", KNeighborsClassifier(n_neighbors=5), True),
        ("tiempo", LinearRegression(), True),
        ("costo", LinearRegression(), True),
    ]:
        y = df["clase_transb"] if nombre == "transbordos" else df[nombre]
        _MODELOS[nombre] = Pipeline([("pre", preprocesador(esc)), ("m", modelo)]).fit(X, y)
    return _MODELOS


def predecir(origen, destino, criterio):
    """Predice tiempo, costo y transbordos SIN recorrer el grafo con DFS."""
    modelos = entrenar_modelos()
    fila = pd.DataFrame(
        [
            {
                "origen": origen,
                "destino": destino,
                "criterio": criterio,
                "medio_origen": ESTACIONES[origen]["medio"],
                "medio_destino": ESTACIONES[destino]["medio"],
                "transb_origen": int(ESTACIONES[origen]["transbordo"]),
                "transb_destino": int(ESTACIONES[destino]["transbordo"]),
                "saltos_min": saltos_minimos(origen).get(destino, -1),
            }
        ]
    )
    return {
        "tiempo": round(float(modelos["tiempo"].predict(fila)[0]), 1),
        "costo": round(float(modelos["costo"].predict(fila)[0])),
        "transbordos": int(modelos["transbordos"].predict(fila)[0]),
    }


# ----------------------------------------------------------------- 6. MAIN
def main():
    pd.set_option("display.width", 120)
    df, omitidos = generar_dataset()
    df.to_csv("dataset_rutas.csv", index=False)
    tr, te = dividir(df)

    print("=" * 62)
    print(f"DATASET: {len(df)} ejemplos | entrenamiento: {len(tr)} | prueba: {len(te)}")
    if omitidos:
        print(f"Casos omitidos por división por cero en inferencia.py: {len(omitidos)}")
        for o in omitidos:
            print("  -", o)
    print("Distribución de transbordos:")
    print(df["clase_transb"].value_counts().sort_index().to_string())

    print("\n" + "=" * 62 + "\nCLASIFICACIÓN: categoría de transbordos (0, 1, 2+)\n" + "=" * 62)
    res, (nombre, f1, cm) = clasificacion(tr, te)
    print(res.round(3).to_string(index=False))
    print(f"\nMatriz de confusión del mejor modelo ({nombre}) [filas=real, cols=predicho]:")
    print(pd.DataFrame(cm, index=["0", "1", "2+"], columns=["0", "1", "2+"]))

    for obj, unidad in [("tiempo", "min"), ("costo", "$")]:
        print("\n" + "=" * 62 + f"\nREGRESIÓN: {obj} ({unidad})\n" + "=" * 62)
        print(regresion(tr, te, obj).round(3).to_string(index=False))


if __name__ == "__main__":
    main()