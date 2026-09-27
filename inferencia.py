from conocimiento import ESTACIONES


def validar_transbordos(r):
    for i, (a, b) in enumerate(zip(r["tramos"], r["tramos"][1:])):
        if a[0] != b[0] and a[0] != "Transbordo" and b[0] != "Transbordo":
            if not ESTACIONES.get(r["nodos"][i + 1], {}).get("transbordo", False):
                return False
    return True


def seleccionar(rutas, criterio):
    candidatas = []
    for r in rutas:
        if not validar_transbordos(r):
            continue
        r["reglas"] = ["R5: transbordos válidos."]
        if len(r["tramos"]) == 1:
            r["reglas"].append("R1: ruta directa.")
        if criterio == "1":
            r["puntaje"] = 100 / r["tiempo"]
            r["reglas"].append("R3: se prioriza menor tiempo.")
        elif criterio == "2":
            r["puntaje"] = 100 / (1 + r["transbordos"])
            r["reglas"].append("R2: se priorizan menos transbordos.")
        elif criterio == "3":
            r["puntaje"] = 100000 / r["costo"]
            r["reglas"].append("R4: se prioriza menor costo.")
        else:
            r["puntaje"] = (
                50 / r["tiempo"] + 30 / (1 + r["transbordos"]) + 20000 / r["costo"]
            )
            r["reglas"].append("R2 + R3 + R4: criterio equilibrado.")
        candidatas.append(r)
    if not candidatas:
        return None
    return sorted(
        candidatas,
        key=lambda r: (-r["puntaje"], r["tiempo"], r["transbordos"], r["costo"]),
    )[0]