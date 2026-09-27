# Sistema inteligente de rutas - Valle de Aburrá

Proyecto académico de Inteligencia Artificial basado en conocimiento.

## Archivos

- `conocimiento.py`: hechos, conexiones y reglas.
- `rutas.py`: grafo y búsqueda DFS.
- `inferencia.py`: motor de inferencia y selección.
- `main.py`: interfaz de consola.
- `pruebas.py`: pruebas reproducibles.

## Ejecución

```bash
python main.py
python pruebas.py
```

No requiere paquetes externos.

## Criterios

1. Más rápida: menor tiempo.
2. Menos transbordos: menor cantidad de cambios.
3. Más económica: menor costo.
4. Equilibrada: combina tiempo, transbordos y costo.

## Enfoque de IA

Es un sistema basado en conocimiento: hechos + reglas lógicas + motor de inferencia + búsqueda DFS. No utiliza machine learning.

Los nombres de estaciones se basan en información pública del Metro de Medellín. Los tiempos y costos son valores académicos simplificados y no representan tarifas ni tiempos en tiempo real.
