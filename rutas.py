from conocimiento import CONEXIONES, ESTACIONES


def grafo():
    g = {e: [] for e in ESTACIONES}
    for a, b, medio, tiempo, costo in CONEXIONES:
        g[a].append((b, medio, tiempo, costo))
        g[b].append((a, medio, tiempo, costo))
    return g


def buscar(origen, destino, max_tramos=25):
    g, rutas = grafo(), []

    def dfs(actual, camino, tramos):
        if len(tramos) > max_tramos:
            return
        if actual == destino:
            rutas.append((camino, tramos))
            return
        for siguiente, medio, tiempo, costo in g.get(actual, []):
            if siguiente not in camino:
                dfs(siguiente, camino + [siguiente], tramos + [(medio, tiempo, costo)])

    dfs(origen, [origen], [])
    return rutas


def datos(ruta):
    nodos, tramos = ruta
    transbordos = sum(
        1
        for a, b in zip(tramos, tramos[1:])
        if a[0] != b[0] and a[0] != "Transbordo" and b[0] != "Transbordo"
    )
    transbordos += sum(1 for t in tramos if t[0] == "Transbordo")
    return {
        "nodos": nodos,
        "tramos": tramos,
        "tiempo": sum(t[1] for t in tramos),
        "costo": sum(t[2] for t in tramos),
        "transbordos": transbordos,
    }