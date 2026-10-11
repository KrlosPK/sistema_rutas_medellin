# Agrupamiento exploratorio de conexiones con K-Means

## Propósito

Explorar si las conexiones descritas por el grafo académico del repositorio pueden agruparse por semejanza en su medio, tiempo simplificado y costo simplificado. El modelo complementa el sistema basado en reglas; no lo reemplaza y no decide cuál ruta debe tomar un pasajero.

## Ejecución

Desde la raíz del repositorio:

```bash
python -m pip install -r ia_no_supervisado/requirements.txt
python ia_no_supervisado/generar_dataset.py  # opcional: reconstruye el CSV desde conocimiento.py
python ia_no_supervisado/agrupamiento.py
python -m unittest discover -s ia_no_supervisado/tests -v
```

Para seleccionar otra cantidad de grupos: `python ia_no_supervisado/agrupamiento.py --grupos 3`. Para usar otra ruta de archivo: `python ia_no_supervisado/agrupamiento.py --csv ruta/al.csv --salida ruta/resultados`.

## Variables usadas

- `tiempo_min`: tiempo por conexión dentro del modelo académico del proyecto.
- `costo_simplificado`: número que representa el costo simplificado registrado por el proyecto; no se interpreta automáticamente como pesos colombianos ni como tarifa actual.
- `medio`: categoría de conexión (Metro, Tranvía, Metrocable, Metroplús o Transbordo). Se transforma en columnas 0/1.

El origen, destino e identificador se conservan para entender la asignación, pero no son características del entrenamiento. No se usa una etiqueta objetivo ni hay predicción supervisada.

## Qué produce

- `resultados/conexiones_agrupadas.csv`: cada conexión más su número de grupo.
- `resultados/resumen_grupos.csv`: cantidad de conexiones, promedios y medios frecuentes por grupo.
- `resultados/grafica_agrupamiento.png`: visualización basada en tiempo y costo.

El número de grupo es un identificador, no un juicio de calidad. Sus números pueden cambiar cuando cambien los datos o el número de grupos.

## Alcance y limitaciones

La muestra tiene 29 conexiones y procede del grafo académico existente. El dataset mezcla nombres de estaciones conocidos con conexiones y valores de tiempo/costo simplificados. No se han incorporado geometrías oficiales, aforos, horarios actualizados ni registros operativos. No se infieren congestión, demanda ni tiempos reales de viaje. Para una ampliación futura, consultar las rutas de transporte público de la Alcaldía de Medellín y validar licencia, vigencia y diccionario antes de mezclar campos.
