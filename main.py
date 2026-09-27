from conocimiento import ESTACIONES
from rutas import buscar, datos
from inferencia import seleccionar


def elegir(texto):
    opciones = sorted(ESTACIONES)
    print("\n" + texto)
    for i, x in enumerate(opciones, 1):
        print(f"{i}. {x}")
    while True:
        try:
            n = int(input("Seleccione: "))
            if 1 <= n <= len(opciones):
                return opciones[n - 1]
        except ValueError:
            pass
        print("Opción inválida.")


def mostrar(r, criterio):
    print("\n" + "=" * 55 + "\nRUTA RECOMENDADA\n" + "=" * 55)
    print("Origen:", r["nodos"][0])
    print("Destino:", r["nodos"][-1])
    print("Criterio:", criterio)
    print("\nRecorrido:")
    for i, nodo in enumerate(r["nodos"]):
        print(nodo)
        if i < len(r["tramos"]):
            print("   ↓", r["tramos"][i][0], "|", r["tramos"][i][1], "min")
    print("\nTiempo:", r["tiempo"], "minutos")
    print("Costo académico: $" + str(r["costo"]))
    print("Transbordos:", r["transbordos"])
    print("\nReglas activadas:")
    [print("-", x) for x in r["reglas"]]


def main():
    print("=" * 55 + "\nSISTEMA INTELIGENTE DE RUTAS - VALLE DE ABURRÁ\n" + "=" * 55)
    origen = elegir("Origen:")
    destino = elegir("Destino:")
    if origen == destino:
        print("Deben ser diferentes.")
        return
    print(
        "\n1. Ruta más rápida\n2. Menos transbordos\n3. Más económica\n4. Equilibrada"
    )
    criterio = input("Seleccione: ")
    nombres = {
        "1": "Ruta más rápida",
        "2": "Menos transbordos",
        "3": "Más económica",
        "4": "Equilibrada",
    }
    if criterio not in nombres:
        print("Criterio inválido.")
        return
    rutas = [datos(x) for x in buscar(origen, destino)]
    resultado = seleccionar(rutas, criterio)
    if resultado:
        mostrar(resultado, nombres[criterio])
    else:
        print("No se encontró una ruta válida.")


if __name__ == "__main__":
    main()
