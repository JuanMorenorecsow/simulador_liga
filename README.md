# ⚽ Simulador de Cuadrangulares 2026-II

Simulador de los cuadrangulares semifinales de la Liga BetPlay 2026-II, hecho con Streamlit.

- Fixture oficial de las 6 fechas, con marcadores editables.
- Simulación de lo que falta (goles con distribución de Poisson y ratings tipo Elo).
- Probabilidades de título por Monte Carlo, con punto invisible para las cabezas de serie.

## Ejecutar en local

```
pip install -r requirements.txt
streamlit run app.py
```

Los datos (equipos, ratings, fixture) están en `data.py` y el motor de simulación en `engine.py`.
