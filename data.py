"""Datos del simulador, temporada Liga BetPlay 2026-II. Edita aquí lo que cambie.

Este año el proyecto trabaja solo con los 8 clasificados a los cuadrangulares.
"""

# Puntos de la fase regular (19 fechas), tras la fecha 19 (14-nov-2026)
PTS_FASE_REGULAR = {
    "Atlético Nacional": 40,
    "América de Cali": 36,
    "Deportivo Cali": 35,
    "Independiente Santa Fe": 34,
    "Atlético Bucaramanga": 33,
    "Independiente Medellín": 32,
    "Millonarios": 30,
    "Once Caldas": 28,
}

# Rating tipo Elo derivado del rendimiento: 1500 + 15 * (puntos - promedio de los 8).
# Es una estimación sencilla; puedes sobrescribir cualquier valor a mano en la barra lateral.
_PROM = sum(PTS_FASE_REGULAR.values()) / len(PTS_FASE_REGULAR)
RATINGS_INICIALES = {t: round(1500 + 15 * (p - _PROM)) for t, p in PTS_FASE_REGULAR.items()}

# Cabezas de serie (los 2 mejores de la fase regular): tienen el "punto invisible",
# es decir, si empatan en puntos con otro en el 1.er lugar de su grupo, avanzan a la final.
CABEZAS_DE_SERIE = ["Atlético Nacional", "América de Cali"]

# Cuadrangulares semifinales (sorteo del 14-nov-2026). Días y horarios: pendientes de la Dimayor.
GRUPOS = {
    "A": ["Atlético Nacional", "Once Caldas", "Independiente Santa Fe", "Independiente Medellín"],
    "B": ["América de Cali", "Atlético Bucaramanga", "Millonarios", "Deportivo Cali"],
}

# (fecha, grupo, local, visitante)
FIXTURE_CUADRANGULARES = [
    (1, "A", "Independiente Medellín", "Independiente Santa Fe"),
    (1, "A", "Once Caldas", "Atlético Nacional"),
    (1, "B", "Deportivo Cali", "Millonarios"),
    (1, "B", "Atlético Bucaramanga", "América de Cali"),
    (2, "A", "Independiente Santa Fe", "Once Caldas"),
    (2, "A", "Atlético Nacional", "Independiente Medellín"),
    (2, "B", "Millonarios", "Atlético Bucaramanga"),
    (2, "B", "América de Cali", "Deportivo Cali"),
    (3, "A", "Independiente Santa Fe", "Atlético Nacional"),
    (3, "A", "Independiente Medellín", "Once Caldas"),
    (3, "B", "Millonarios", "América de Cali"),
    (3, "B", "Deportivo Cali", "Atlético Bucaramanga"),
    (4, "A", "Atlético Nacional", "Independiente Santa Fe"),
    (4, "A", "Once Caldas", "Independiente Medellín"),
    (4, "B", "América de Cali", "Millonarios"),
    (4, "B", "Atlético Bucaramanga", "Deportivo Cali"),
    (5, "A", "Once Caldas", "Independiente Santa Fe"),
    (5, "A", "Independiente Medellín", "Atlético Nacional"),
    (5, "B", "Atlético Bucaramanga", "Millonarios"),
    (5, "B", "Deportivo Cali", "América de Cali"),
    (6, "A", "Independiente Santa Fe", "Independiente Medellín"),
    (6, "A", "Atlético Nacional", "Once Caldas"),
    (6, "B", "Millonarios", "Deportivo Cali"),
    (6, "B", "América de Cali", "Atlético Bucaramanga"),
]

# Nombres de archivo alternativos para los escudos (carpeta "escudos", sin extensión).
# La app prueba primero el nombre automático (ej. "america_de_cali") y luego estos.
ARCHIVOS_ESCUDOS = {
    "Atlético Bucaramanga": ["bucaramanga"],
    "América de Cali": ["america"],
    "Independiente Santa Fe": ["independiente_santafe", "santa_fe"],
}
