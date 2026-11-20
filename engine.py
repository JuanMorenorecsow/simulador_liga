"""Motor de simulación: goles ~ Poisson, con fuerza derivada de ratings Elo."""
import numpy as np
import pandas as pd

BASE_LOCAL, BASE_VISITA, K = 1.40, 1.00, 0.09  # goles base y sensibilidad al rating


def goles(rng, elo_l, elo_v):
    d = (np.asarray(elo_l, float) - np.asarray(elo_v, float)) / 100
    return rng.poisson(BASE_LOCAL * np.exp(K * d)), rng.poisson(BASE_VISITA * np.exp(-K * d))


# ---------- Fase regular (todos contra todos, 19 fechas), vectorizada ----------
def simular_liga(rng, elo_arr, n_sims):
    T = len(elo_arr)
    i, j = np.triu_indices(T, 1)
    flip = rng.random((n_sims, len(i))) < 0.5
    h, a = np.where(flip, j, i), np.where(flip, i, j)
    gh, ga = goles(rng, elo_arr[h], elo_arr[a])
    hp = 3 * (gh > ga) + (gh == ga)
    ap = 3 * (ga > gh) + (gh == ga)
    pts, gf, gc = (np.zeros((n_sims, T)) for _ in range(3))
    for t in range(T):
        mh, ma = h == t, a == t
        pts[:, t] = (hp * mh).sum(1) + (ap * ma).sum(1)
        gf[:, t] = (gh * mh).sum(1) + (ga * ma).sum(1)
        gc[:, t] = (ga * mh).sum(1) + (gh * ma).sum(1)
    return pts, gf, gc


def ordenar_liga(rng, pts, gf, gc):
    clave = pts * 1e6 + (gf - gc + 500) * 1e3 + gf + rng.random(pts.shape) * 0.5
    return np.argsort(-clave, axis=1)


# ---------- Grupos / cuadrangulares ----------
def doble_ida_vuelta(equipos):
    return [(h, a, None, None) for h in equipos for a in equipos if h != a]


def _vacia():
    return {"PJ": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "PTS": 0}


def tabla(partidos):
    """partidos: lista de (local, visita, gl, gv); ignora los no jugados (None)."""
    tab = {}
    for h, a, gl, gv in partidos:
        for t in (h, a):
            tab.setdefault(t, _vacia())
        if gl is None or gv is None:
            continue
        gl, gv = int(gl), int(gv)
        for t, f, c in ((h, gl, gv), (a, gv, gl)):
            r = tab[t]
            r["PJ"] += 1
            r["GF"] += f
            r["GC"] += c
            r["G"] += f > c
            r["E"] += f == c
            r["P"] += f < c
            r["PTS"] += 3 * (f > c) + (f == c)
    return tab


def ordenar(rng, tab, semillas=()):
    """Orden de un grupo. Las cabezas de serie (`semillas`) tienen el 'punto invisible':
    ganan el desempate si igualan en puntos (se modela como +0.5 puntos solo para ordenar)."""
    return sorted(
        tab,
        key=lambda t: (tab[t]["PTS"] + (0.5 if t in semillas else 0), tab[t]["GF"] - tab[t]["GC"], tab[t]["GF"], rng.random()),
        reverse=True,
    )


def a_df(tab, orden):
    filas = [{"Pos": k + 1, "Equipo": t, **tab[t], "DG": tab[t]["GF"] - tab[t]["GC"]} for k, t in enumerate(orden)]
    cols = ["Pos", "Equipo", "PJ", "PTS", "G", "E", "P", "GF", "GC", "DG"]
    return pd.DataFrame(filas)[cols]


def completar(rng, elo, partidos):
    """Simula los partidos sin resultado y devuelve la lista completa."""
    out = []
    for h, a, gl, gv in partidos:
        if gl is None or gv is None:
            gl, gv = (int(x) for x in goles(rng, elo[h], elo[a]))
        out.append((h, a, gl, gv))
    return out


def final_ida_vuelta(rng, elo, t1, t2):
    """t1 = mejor ubicado (cierra de local). Empate global -> penales 50/50."""
    g2, g1 = (int(x) for x in goles(rng, elo[t2], elo[t1]))   # ida en casa de t2
    g1b, g2b = (int(x) for x in goles(rng, elo[t1], elo[t2]))  # vuelta en casa de t1
    a1, a2 = g1 + g1b, g2 + g2b
    pen = None
    if a1 == a2:
        pen = t1 if rng.random() < 0.5 else t2
        campeon = pen
    else:
        campeon = t1 if a1 > a2 else t2
    return {"ida": (t2, g2, g1, t1), "vuelta": (t1, g1b, g2b, t2), "global": (a1, a2), "penales": pen, "campeon": campeon}


def fase_final(rng, elo, grupos_partidos, semillas=(), pts_previos=None):
    """grupos_partidos: {'A': [(h,a,gl|None,gv|None)...], 'B': ...} -> dict con todo."""
    tablas, ganadores, completos = {}, {}, {}
    for g, partidos in grupos_partidos.items():
        completos[g] = completar(rng, elo, partidos)
        tab = tabla(completos[g])
        orden = ordenar(rng, tab, semillas)
        tablas[g] = (tab, orden)
        ganadores[g] = orden[0]
    wa, wb = ganadores["A"], ganadores["B"]
    ta, tb = tablas["A"][0][wa], tablas["B"][0][wb]
    pp = pts_previos or {}  # puntos de la fase regular: la localía de la vuelta sale de la tabla del semestre
    ka = (pp.get(wa, 0) + ta["PTS"], ta["GF"] - ta["GC"], ta["GF"])
    kb = (pp.get(wb, 0) + tb["PTS"], tb["GF"] - tb["GC"], tb["GF"])
    t1, t2 = (wa, wb) if ka >= kb else (wb, wa)
    final = final_ida_vuelta(rng, elo, t1, t2)
    return {"tablas": tablas, "ganadores": ganadores, "final": final, "campeon": final["campeon"], "partidos": completos}


# ---------- Campeonato desde cero ----------
def sortear(rng, ocho):
    """`ocho` viene ordenado de mejor a peor: los 2 primeros son cabezas de serie y van en grupos distintos."""
    semillas = list(ocho[:2])
    resto = list(ocho[2:])
    rng.shuffle(resto)
    if rng.random() < 0.5:
        semillas.reverse()
    return {"A": [semillas[0]] + resto[:3], "B": [semillas[1]] + resto[3:]}, set(ocho[:2])


def _clasificar(rng, elo_dict):
    """Devuelve (ocho clasificados ordenados, tabla regular o None, puntos previos o None)."""
    equipos = list(elo_dict)
    if len(equipos) == 8:  # solo cuadrangulares: sin fase regular, ordenados por rating
        return sorted(equipos, key=lambda t: -elo_dict[t]), None, None
    elo_arr = np.array([elo_dict[t] for t in equipos], float)
    pts, gf, gc = simular_liga(rng, elo_arr, 1)
    orden = ordenar_liga(rng, pts, gf, gc)[0]
    tab = {equipos[k]: {"PJ": 19, "G": 0, "E": 0, "P": 0, "GF": int(gf[0, k]), "GC": int(gc[0, k]), "PTS": int(pts[0, k])} for k in range(len(equipos))}
    reg = a_df(tab, [equipos[k] for k in orden]).drop(columns=["G", "E", "P"])
    return [equipos[k] for k in orden[:8]], reg, {t: tab[t]["PTS"] for t in tab}


def temporada(rng, elo_dict):
    ocho, reg, pp = _clasificar(rng, elo_dict)
    grupos, semillas = sortear(rng, ocho)
    res = fase_final(rng, elo_dict, {g: doble_ida_vuelta(e) for g, e in grupos.items()}, semillas, pp)
    res["regular"], res["grupos"], res["semillas"] = reg, grupos, semillas
    return res


def montecarlo_temporada(rng, elo_dict, n):
    equipos = list(elo_dict)
    solo8 = len(equipos) == 8
    cont = {t: dict(Top8=0, Final=0, Campeón=0) for t in equipos}
    if not solo8:
        elo_arr = np.array([elo_dict[t] for t in equipos], float)
        pts, gf, gc = simular_liga(rng, elo_arr, n)
        orden = ordenar_liga(rng, pts, gf, gc)
    for s in range(n):
        if solo8:
            ocho, pp = sorted(equipos, key=lambda t: -elo_dict[t]), None
        else:
            ocho = [equipos[k] for k in orden[s, :8]]
            pp = {equipos[k]: pts[s, k] for k in range(len(equipos))}
        g, semillas = sortear(rng, ocho)
        r = fase_final(rng, elo_dict, {k: doble_ida_vuelta(v) for k, v in g.items()}, semillas, pp)
        for t in ocho:
            cont[t]["Top8"] += 1
        for t in r["ganadores"].values():
            cont[t]["Final"] += 1
        cont[r["campeon"]]["Campeón"] += 1
    df = pd.DataFrame(cont).T
    for c in ("Top8", "Final", "Campeón"):
        df[c] = df[c] / n * 100
    if solo8:
        df = df.drop(columns="Top8")
    return df.sort_values(["Campeón", "Final"], ascending=False).round(1)


# ---------- Modo actualidad ----------
def montecarlo_cuadrangulares(rng, elo, grupos_partidos, n, semillas=(), pts_previos=None):
    equipos = [t for p in grupos_partidos.values() for m in p for t in m[:2]]
    cont = {t: dict(Gana_grupo=0, Campeón=0, PTS_prom=0.0) for t in dict.fromkeys(equipos)}
    for _ in range(n):
        r = fase_final(rng, elo, grupos_partidos, semillas, pts_previos)
        for g, (tab, _o) in r["tablas"].items():
            for t, v in tab.items():
                cont[t]["PTS_prom"] += v["PTS"]
        for t in r["ganadores"].values():
            cont[t]["Gana_grupo"] += 1
        cont[r["campeon"]]["Campeón"] += 1
    df = pd.DataFrame(cont).T
    df["PTS_prom"] = df["PTS_prom"] / n
    df["Gana_grupo"] = df["Gana_grupo"] / n * 100
    df["Campeón"] = df["Campeón"] / n * 100
    return df.sort_values("Campeón", ascending=False).round(1)
