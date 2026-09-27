from rutas import buscar, datos
from inferencia import seleccionar

CASOS = [
    ("PRUEBA 1", "Niquía", "Hospital", "1"),
    ("PRUEBA 2", "Niquía", "Santo Domingo", "2"),
    ("PRUEBA 3", "Niquía", "Villa Sierra", "4"),
]
for nombre, origen, destino, criterio in CASOS:
    rutas = [datos(x) for x in buscar(origen, destino)]
    r = seleccionar(rutas, criterio)
    print("\n" + "=" * 55)
    print(nombre)
    print(origen, "->", destino, "| criterio:", criterio)
    print(" -> ".join(r["nodos"]))
    print(
        "Tiempo:",
        r["tiempo"],
        "min | Costo:",
        r["costo"],
        "| Transbordos:",
        r["transbordos"],
    )
    print("Reglas:", "; ".join(r["reglas"]))
 