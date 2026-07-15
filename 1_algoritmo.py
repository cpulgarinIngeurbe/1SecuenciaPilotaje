# -*- coding: utf-8 -*-
"""
PASO 1 — Algoritmo de Secuenciacion de Pilotaje
================================================
Corre el algoritmo OR-Tools CP-SAT y guarda el resultado en:
    resultado_secuencia.json

Ejecutar este script cuando cambien los datos o los parametros.
El resultado queda guardado y puede regenerarse el HTML sin volver a correr.

Parametros configurables:
  EXCEL_PATH  : ruta al archivo Excel con los pilotes
  ID_COL      : columna del identificador del pilote
  X_COL       : columna de la coordenada X
  Y_COL       : columna de la coordenada Y
  D           : distancia critica minima entre huecos (metros)
  T           : tiempo de espera antes de poder abrir un hueco dentro del radio D (dias)
  R           : ritmo de la maquina (huecos por dia)
  TIME_LIMIT  : segundos maximos para el solver CP-SAT
  USE_SAMPLE  : True = datos de muestra; False = leer EXCEL_PATH
  START_ID    : ID del pilote (columna ITEM) por donde debe arrancar la secuencia.
                None = el algoritmo escoge el mejor punto de inicio automaticamente.
"""

import json
import math
import os
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# =============================================================================
# CONFIGURACION — ajustar segun el proyecto
# =============================================================================
EXCEL_PATH  = "pilotes.xlsx"
ID_COL      = "ITEM"
X_COL       = "X"
Y_COL       = "Y"
D           = 5
T           = 2
R           = 2
TIME_LIMIT  = 300
USE_SAMPLE  = False
START_ID    = "T1 P-1"          # Ej: START_ID = "P045"  o  START_ID = 12
STRATEGY    = "sweep_WE"         # "optimal" | "sweep_WE" | "sweep_EW" | "sweep_SN" | "sweep_NS"
RESULTADO   = "resultado_secuencia.json"   # archivo de salida
# =============================================================================


def generate_sample_data(n=30, seed=42):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 40, n)
    y = rng.uniform(0, 40, n)
    ids = [f"P{i+1:03d}" for i in range(n)]
    return pd.DataFrame({"id": ids, "x": x, "y": y})


def load_piles(excel_path, id_col, x_col, y_col):
    df = pd.read_excel(excel_path, engine="openpyxl")
    df = df[[id_col, x_col, y_col]].dropna().copy()
    df = df.rename(columns={id_col: "id", x_col: "x", y_col: "y"})
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    return df.dropna().reset_index(drop=True)


def _drill(idx, current_time, blocked_until, coords, D, T, time_per_hole):
    """
    Perfora el pilote idx y retorna el nuevo current_time (= dia de apertura).
    Usa la misma logica que simulate_times: open_time = max(current_time,
    blocked_until[idx]) + time_per_hole, luego bloquea vecinos desde open_time.
    Si blocked_until[idx] > current_time la maquina espera (idle inevitable).
    """
    open_time = max(current_time, blocked_until[idx]) + time_per_hole
    n = len(coords)
    for j in range(n):
        if np.linalg.norm(coords[idx] - coords[j]) < D:
            blocked_until[j] = max(blocked_until[j], open_time + T)
    return open_time


def greedy_sequence(coords, D, T, R, start_idx=0):
    """
    Vecino mas cercano con restriccion de distancia critica.
    Logica sincronizada con simulate_times: bloquea vecinos desde open_time
    (despues de perforar), no desde el inicio del slot.
    La maquina busca el pilote disponible mas cercano en TODA la obra; solo
    espera si absolutamente todos los pendientes estan bloqueados (caso raro).
    """
    n = len(coords)
    time_per_hole = 1.0 / R
    visited = [False] * n
    blocked_until = np.zeros(n)
    sequence = [start_idx]
    visited[start_idx] = True

    current_time = _drill(start_idx, 0.0, blocked_until, coords, D, T, time_per_hole)

    while len(sequence) < n:
        unvisited = [i for i in range(n) if not visited[i]]

        # Disponibles = no bloqueados en el momento actual (sin tiempo muerto)
        available = [i for i in unvisited if blocked_until[i] <= current_time]

        if not available:
            # Todos bloqueados: esperar el minimo indispensable (geometria muy densa)
            current_time = min(blocked_until[i] for i in unvisited)
            available = [i for i in unvisited if blocked_until[i] <= current_time + 1e-9]

        # Elegir el disponible mas cercano (puede estar lejos si la zona cercana esta bloqueada)
        last = sequence[-1]
        dists = [np.linalg.norm(coords[last] - coords[i]) for i in available]
        nearest = available[int(np.argmin(dists))]

        visited[nearest] = True
        sequence.append(nearest)
        current_time = _drill(nearest, current_time, blocked_until, coords, D, T, time_per_hole)

    total = sum(
        np.linalg.norm(coords[sequence[i]] - coords[sequence[i - 1]])
        for i in range(1, n)
    )
    return sequence, total


def sweep_sequence(coords, D, T, R, direction="WE", start_idx=None):
    """
    Genera la secuencia barriendo en una direccion fija.
      WE : Oeste a Este  (X ascendente)
      EW : Este a Oeste  (X descendente)
      SN : Sur a Norte   (Y ascendente)
      NS : Norte a Sur   (Y descendente)
    Respeta la restriccion de distancia critica: si un pilote esta bloqueado
    lo salta y sigue en el orden de barrido; vuelve a los pendientes cuando
    se desbloquean.
    """
    n = len(coords)
    time_per_hole = 1.0 / R
    blocked_until = np.zeros(n)
    sequence = []
    current_time = 0.0

    # Orden de barrido
    if direction == "WE":
        sorted_order = sorted(range(n), key=lambda i: ( coords[i][0],  coords[i][1]))
    elif direction == "EW":
        sorted_order = sorted(range(n), key=lambda i: (-coords[i][0],  coords[i][1]))
    elif direction == "SN":
        sorted_order = sorted(range(n), key=lambda i: ( coords[i][1],  coords[i][0]))
    else:  # NS
        sorted_order = sorted(range(n), key=lambda i: (-coords[i][1],  coords[i][0]))

    # Visitar el pilote de arranque fijo primero
    if start_idx is not None:
        sequence.append(start_idx)
        current_time = _drill(start_idx, 0.0, blocked_until, coords, D, T, time_per_hole)
        sorted_order = [i for i in sorted_order if i != start_idx]

    pending = list(sorted_order)

    while pending:
        # Disponibles en el orden de barrido sin tiempo muerto
        available = [i for i in pending if blocked_until[i] <= current_time]

        if not available:
            # Todos bloqueados: esperar minimo indispensable
            current_time = min(blocked_until[i] for i in pending)
            available = [i for i in pending if blocked_until[i] <= current_time + 1e-9]

        # Primer disponible en el orden de barrido
        next_pile = available[0]
        pending.remove(next_pile)
        sequence.append(next_pile)
        current_time = _drill(next_pile, current_time, blocked_until, coords, D, T, time_per_hole)

    total = sum(
        np.linalg.norm(coords[sequence[i]] - coords[sequence[i - 1]])
        for i in range(1, n)
    )
    return sequence, total


def best_greedy(coords, D, T, R):
    n = len(coords)
    best_seq, best_dist = None, np.inf
    for s in range(n):
        seq, dist = greedy_sequence(coords, D, T, R, start_idx=s)
        if dist < best_dist:
            best_seq, best_dist = seq, dist
    return best_seq, best_dist


def solve_cpsat(piles, D, T, R, time_limit_s=120, greedy_hint=None, fixed_start=None):
    """
    Modelo corregido: usa variables de tiempo reales en lugar del proxy de
    posicion. Esto permite que la maquina espere entre huecos sin violar la
    restriccion de distancia critica, lo cual es imposible de representar
    correctamente solo con gap de posicion.

    Variables de tiempo:
      t[p]       = tiempo (escalado) en que se abre la posicion p
      t_pile[i]  = tiempo en que se abre el pilote i = t[pos[i]]

    Restriccion real:
      Para par (i,j) con dist < D: |t_pile[i] - t_pile[j]| >= T_scaled
    """
    from ortools.sat.python import cp_model

    coords = piles[["x", "y"]].values
    n = len(coords)

    SCALE_D = 1000          # escala para distancias
    SCALE_T = 100           # escala para tiempos (evita fracciones con 1/R)
    tph = round(SCALE_T / R)           # tiempo por hueco escalado
    T_s = round(T * SCALE_T)           # tiempo de espera escalado
    MAX_T = n * (tph + T_s) + SCALE_T  # cota superior de tiempo total

    dist_float = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
    dist_int   = np.round(dist_float * SCALE_D).astype(int)

    critical_pairs = [
        (i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if dist_float[i, j] < D
    ]

    print(f"  Pares criticos encontrados: {len(critical_pairs)}")
    print(f"  Tiempo de espera escalado  : {T_s}  |  Por hueco: {tph}")

    model = cp_model.CpModel()

    # --- Variables de secuencia ---
    pile_at = [model.new_int_var(0, n - 1, f"pile_at_{p}") for p in range(n)]
    model.add_all_different(pile_at)

    pos = [model.new_int_var(0, n - 1, f"pos_{i}") for i in range(n)]
    model.add_inverse(pile_at, pos)

    # Restriccion de arranque fijo: el pilote fixed_start debe estar en la posicion 0
    if fixed_start is not None:
        model.add(pile_at[0] == fixed_start)

    # --- Variables de tiempo por posicion ---
    # t[p] puede ser mayor que t[p-1]+tph cuando la maquina espera
    t = [model.new_int_var(0, MAX_T, f"t_{p}") for p in range(n)]
    model.add(t[0] == tph)
    for p in range(1, n):
        model.add(t[p] >= t[p - 1] + tph)

    # t_pile[i] = t[pos[i]]  (tiempo real de apertura del pilote i)
    t_pile = [model.new_int_var(0, MAX_T, f"tp_{i}") for i in range(n)]
    for i in range(n):
        model.add_element(pos[i], t, t_pile[i])

    # --- Restriccion de distancia critica (en tiempo real, no en posicion) ---
    for i, j in critical_pairs:
        diff_t  = model.new_int_var(-MAX_T, MAX_T, f"dt_{i}_{j}")
        abs_dt  = model.new_int_var(0, MAX_T,      f"adt_{i}_{j}")
        model.add(diff_t == t_pile[i] - t_pile[j])
        model.add_abs_equality(abs_dt, diff_t)
        model.add(abs_dt >= T_s)

    # --- Objetivo: minimizar distancia total de recorrido ---
    dist_flat = dist_int.flatten().tolist()
    max_d = int(dist_int.max())
    step_dist = [model.new_int_var(0, max_d, f"step_{p}") for p in range(n - 1)]

    for p in range(n - 1):
        idx = model.new_int_var(0, n * n - 1, f"idx_{p}")
        model.add(idx == pile_at[p] * n + pile_at[p + 1])
        model.add_element(idx, dist_flat, step_dist[p])

    total_cost = model.new_int_var(0, max_d * n, "total_cost")
    model.add(total_cost == sum(step_dist))
    model.minimize(total_cost)

    # Warm-start desde solucion greedy (secuencia + tiempos aproximados)
    if greedy_hint is not None:
        coords_h = piles[["x", "y"]].values
        blocked_h = np.zeros(n)
        cur_t = 0.0
        hint_times = []
        for p, pile_idx in enumerate(greedy_hint):
            model.add_hint(pile_at[p], pile_idx)
            unvisited_blocked = [blocked_h[k] for k in range(n) if k not in greedy_hint[:p]]
            cur_t = max(cur_t, 0.0) + 1.0 / R
            hint_times.append(round(cur_t * SCALE_T))
            for k in range(n):
                if np.linalg.norm(coords_h[pile_idx] - coords_h[k]) < D:
                    blocked_h[k] = max(blocked_h[k], cur_t + T)
        for p, ht in enumerate(hint_times):
            model.add_hint(t[p], max(ht, (p + 1) * tph))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_workers = min(8, os.cpu_count() or 4)
    solver.parameters.log_search_progress = False

    print(f"  Ejecutando CP-SAT (limite: {time_limit_s}s, nucleos: {solver.parameters.num_workers})...")
    t0 = time.time()
    status = solver.solve(model)
    elapsed = time.time() - t0

    print(f"  Estado: {solver.status_name(status)}  |  Tiempo: {elapsed:.1f}s")

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        seq = [solver.value(pile_at[p]) for p in range(n)]
        total_d = solver.value(total_cost) / SCALE_D
        return seq, total_d, (status == cp_model.OPTIMAL)

    return None, None, False


def simulate_times(sequence, coords, D, T, R):
    """
    Simula los tiempos reales de apertura de cada pilote en la secuencia,
    respetando los bloqueos por distancia critica.
    Retorna lista de tiempos en dias (float) para cada posicion en la secuencia.
    """
    n_seq = len(sequence)
    time_per_hole = 1.0 / R
    blocked_until = np.zeros(len(coords))
    open_times = []
    current_time = 0.0

    for rank, idx in enumerate(sequence):
        # La maquina tarda 1/R dias en hacer el hueco; no puede empezar
        # antes de current_time ni antes de que el pilote se desbloquee
        start = max(current_time, blocked_until[idx]) + time_per_hole
        open_times.append(start)
        current_time = start

        # Bloquear vecinos dentro del radio critico
        for j in range(len(coords)):
            if np.linalg.norm(coords[idx] - coords[j]) < D:
                blocked_until[j] = max(blocked_until[j], current_time + T)

    return open_times


def save_result(piles, sequence, D, T, R, solver_label, output_path):
    coords = piles[["x", "y"]].values
    ids    = piles["id"].values

    # Tiempos reales de apertura (considera esperas por bloqueos)
    open_times = simulate_times(sequence, coords, D, T, R)

    rows = []
    total_dist = 0.0
    violations = 0

    for rank, idx in enumerate(sequence):
        x, y     = coords[idx]
        pid      = str(ids[idx])
        open_t   = open_times[rank]
        release_t = open_t + T

        if rank == 0:
            dist_step = None
            wait_days = None
            ok        = True
        else:
            prev      = sequence[rank - 1]
            dist_step = float(np.linalg.norm(coords[idx] - coords[prev]))
            total_dist += dist_step
            wait_days  = round(open_t - open_times[rank - 1], 4)
            # Verificar restriccion: si distancia < D, el tiempo entre ellos debe >= T
            if dist_step < D and (open_t - open_times[rank - 1]) < T - 1e-6:
                ok = False
                violations += 1
            else:
                ok = True

        rows.append({
            "rank":        rank + 1,
            "id":          pid,
            "x":           round(float(x), 4),
            "y":           round(float(y), 4),
            "dist":        round(dist_step, 4) if dist_step is not None else None,
            "open_day":    round(open_t, 2),
            "release_day": round(release_t, 2),
            "wait":        wait_days,
            "ok":          ok,
        })

    if violations == 0:
        print(f"  Validacion: OK — ninguna restriccion violada.")
    else:
        print(f"  ADVERTENCIA: {violations} restriccion(es) violada(s) en la secuencia.")

    result = {
        "params": {
            "D": D, "T": T, "R": R, "n": len(sequence),
            "solver": solver_label,
            "total_dist": round(total_dist, 4),
            "violations": violations,
        },
        "rows": rows,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Resultado guardado en: {output_path}")


# ---------------------------------------------------------------------------
# EJECUCION PRINCIPAL
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    SEP = "=" * 62
    print(SEP)
    print("  PASO 1 — Algoritmo de Secuenciacion de Pilotaje")
    print(SEP)

    if USE_SAMPLE:
        print(">> Datos de muestra (30 pilotes aleatorios)")
        piles = generate_sample_data(n=30)
    else:
        print(f">> Leyendo: {EXCEL_PATH}")
        piles = load_piles(EXCEL_PATH, ID_COL, X_COL, Y_COL)

    coords = piles[["x", "y"]].values
    n = len(piles)
    min_gap = max(1, math.ceil(T * R))

    # Resolver el indice del pilote de arranque si se especifico START_ID
    start_idx = None
    if START_ID is not None:
        matches = piles.index[piles["id"].astype(str) == str(START_ID)].tolist()
        if not matches:
            print(f"  ADVERTENCIA: START_ID='{START_ID}' no se encontro en los datos.")
            print(f"  IDs disponibles: {list(piles['id'].astype(str))[:10]} ...")
            print(f"  Se usara el inicio optimo automatico.")
        else:
            start_idx = matches[0]
            print(f"  Punto de arranque fijo: '{START_ID}' (indice {start_idx})")

    print(f"  Pilotes cargados  : {n}")
    print(f"  Distancia critica : D = {D} m")
    print(f"  Tiempo de espera  : T = {T} dia(s)")
    print(f"  Ritmo maquina     : R = {R} huecos/dia")
    print(f"  Separacion minima : {min_gap} posiciones en secuencia")
    print(f"  Limite de tiempo  : {TIME_LIMIT}s")
    strategy_labels = {
        "optimal": "Optimo (CP-SAT / Greedy)",
        "sweep_WE": "Barrido Oeste - Este",
        "sweep_EW": "Barrido Este - Oeste",
        "sweep_SN": "Barrido Sur - Norte",
        "sweep_NS": "Barrido Norte - Sur",
    }
    if start_idx is None:
        print(f"  Inicio            : automatico (el algoritmo decide)")
    else:
        print(f"  Inicio            : fijo en '{START_ID}'")
    print(f"  Estrategia        : {strategy_labels.get(STRATEGY, STRATEGY)}")
    print()

    if STRATEGY == "optimal":
        print("[1/2] Calculando solucion greedy inicial...")
        t0 = time.time()
        if start_idx is not None:
            greedy_seq, greedy_dist = greedy_sequence(coords, D, T, R, start_idx=start_idx)
        else:
            greedy_seq, greedy_dist = best_greedy(coords, D, T, R)
        print(f"      Distancia greedy: {greedy_dist:.2f} m  ({time.time()-t0:.1f}s)")
        print()

        try:
            import ortools
            print("[2/2] Ejecutando OR-Tools CP-SAT...")
            cpsat_seq, cpsat_dist, is_optimal = solve_cpsat(
                piles, D, T, R,
                time_limit_s=TIME_LIMIT,
                greedy_hint=greedy_seq,
                fixed_start=start_idx,
            )
            if cpsat_seq is not None:
                mejora = (greedy_dist - cpsat_dist) / greedy_dist * 100
                solver_label = "OR-Tools CP-SAT - OPTIMO" if is_optimal else "OR-Tools CP-SAT - Mejor hallado"
                print(f"      Distancia CP-SAT: {cpsat_dist:.2f} m")
                print(f"      Mejora vs greedy: {mejora:.1f}%")
                final_seq, final_dist = cpsat_seq, cpsat_dist
            else:
                print("      CP-SAT no encontro solucion factible. Usando greedy.")
                solver_label = "Greedy vecino mas cercano"
                final_seq, final_dist = greedy_seq, greedy_dist
        except ImportError:
            print("[2/2] OR-Tools no instalado. Usando greedy.")
            solver_label = "Greedy vecino mas cercano"
            final_seq, final_dist = greedy_seq, greedy_dist

    else:
        direction = STRATEGY.replace("sweep_", "")
        print(f"[1/1] Calculando barrido {strategy_labels[STRATEGY]}...")
        t0 = time.time()
        final_seq, final_dist = sweep_sequence(coords, D, T, R,
                                               direction=direction,
                                               start_idx=start_idx)
        solver_label = strategy_labels[STRATEGY]
        print(f"      Distancia total: {final_dist:.2f} m  ({time.time()-t0:.1f}s)")

    if start_idx is not None:
        solver_label += f"  |  Inicio: '{START_ID}'"

    print()
    print(SEP)
    print(f"  Distancia total: {final_dist:.2f} m  |  Solver: {solver_label}")
    print(SEP)

    save_result(piles, final_seq, D, T, R, solver_label, RESULTADO)
    print()
    print("Listo. Ahora ejecuta 2_html.py para generar la visualizacion.")
    input("\nPresiona Enter para cerrar...")
