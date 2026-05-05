"""
Smoke test del cliente INEGI BIE/BISE.

Verifica que los casos críticos funcionen antes de subir a GitHub.
No requiere pytest — corre directamente con Python.

Uso:
    export INEGI_TOKEN="tu-uuid"
    python test_smoke.py
"""

import os
import sys
import traceback

token = os.environ.get("INEGI_TOKEN")
if not token:
    print("ERROR: define INEGI_TOKEN antes de correr.")
    sys.exit(1)

from inegi_bie_client import INEGIBIEClient, INDICADORES_BIE, GEO_SOLO_ESTATAL, FUENTE_BISE

client = INEGIBIEClient(token=token)

passed = 0
failed = 0
errors = []


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  OK   {name}")
        passed += 1
    else:
        print(f"  FAIL {name}" + (f" — {detail}" if detail else ""))
        failed += 1


def run(label, fn):
    """Ejecuta fn y retorna su resultado, o None si lanza excepción."""
    try:
        result = fn()
        return result
    except Exception as e:
        errors.append((label, str(e)))
        print(f"  ERR  {label} — {e}")
        return None


print("\n=== 1. Catálogo de indicadores ===")
n = len(INDICADORES_BIE)
check(f"{n} indicadores en el dict", n >= 330, f"actual: {n}")

from collections import Counter
dups = {iid: cnt for iid, cnt in Counter(INDICADORES_BIE.values()).items() if cnt > 1}
check("IDs únicos (sin duplicados)", len(dups) == 0,
      f"duplicados: { {iid: [k for k,v in INDICADORES_BIE.items() if v==iid] for iid in dups} }")
check("GEO_SOLO_ESTATAL contiene ITAEE y exports",
      {"741927", "741929", "629659", "630459"}.issubset(GEO_SOLO_ESTATAL))
check("FUENTE_BISE incluye bise_* y poblacion_total",
      "bise_alfabetismo_15mas" in FUENTE_BISE and "poblacion_total" in FUENTE_BISE)


print("\n=== 2. Indicador económico nacional — IGAE total ===")
raw = run("get_indicator IGAE", lambda: client.get_indicator("737121", recent_only=False))
if raw:
    rows = client.parse_series(raw)
    check("retorna observaciones", len(rows) > 0, f"rows={len(rows)}")
    check("orden cronológico ascendente",
          rows[0]["time_period"] < rows[-1]["time_period"],
          f"{rows[0]['time_period']} vs {rows[-1]['time_period']}")
    last = rows[-1]
    check("obs_value es string numérico", last["obs_value"] not in (None, ""),
          f"value={last['obs_value']}")
    check("time_period tiene formato YYYY/MM",
          "/" in last["time_period"],
          f"got={last['time_period']}")
    check("geo es nacional (0 o 00)", last["geo"] in ("00", "0"), f"got={last['geo']}")
    print(f"       Último dato: {last['time_period']}  valor={last['obs_value']}")


print("\n=== 3. recent_only=True ===")
raw_r = run("get_indicator recent_only", lambda: client.get_indicator("910406", recent_only=True))
if raw_r:
    rows_r = client.parse_series(raw_r)
    check("retorna exactamente 1 observación", len(rows_r) == 1, f"got {len(rows_r)}")
    print(f"       Inflación anual reciente: {rows_r[0]['time_period']}  {rows_r[0]['obs_value']}%")


print("\n=== 4. Indicador estatal — ITAEE Jalisco (geo=14) ===")
raw_e = run("ITAEE geo=14", lambda: client.get_indicator("741927", geo="14"))
if raw_e:
    rows_e = client.parse_series(raw_e)
    check("retorna observaciones para geo=14", len(rows_e) > 0)
    check("geo de la observación es '14'", rows_e[-1]["geo"] == "14",
          f"got={rows_e[-1]['geo']}")
    print(f"       ITAEE Jalisco último: {rows_e[-1]['time_period']}  {rows_e[-1]['obs_value']}")


print("\n=== 5. geo='00' en indicador state-only debe fallar ===")
try:
    client.get_indicator("741927", geo="00")
    # Si no lanza, es un problema
    print("  FAIL ITAEE geo=00 no retornó error (debería retornar HTTP 400)")
    failed += 1
except Exception as e:
    check("ITAEE geo=00 lanza excepción correctamente", True)
    print(f"       Error esperado: {type(e).__name__}")


print("\n=== 6. Indicador BISE — educación (fuente=BISE) ===")
raw_b = run("BISE escolaridad promedio",
            lambda: client.get_indicator("1005000038", fuente="BISE"))
if raw_b:
    rows_b = client.parse_series(raw_b)
    check("retorna observaciones BISE", len(rows_b) > 0)
    print(f"       Escolaridad promedio (último): {rows_b[-1]['time_period']}  {rows_b[-1]['obs_value']} grados")


print("\n=== 7. Indicador BISE — salud (fuente=BISE) ===")
raw_s = run("BISE % afiliado salud",
            lambda: client.get_indicator("6207019018", fuente="BISE"))
if raw_s:
    rows_s = client.parse_series(raw_s)
    check("retorna observaciones salud BISE", len(rows_s) > 0)
    print(f"       % afiliado salud (último): {rows_s[-1]['time_period']}  {rows_s[-1]['obs_value']}%")


print("\n=== 8. search_indicators — búsqueda en el catálogo ===")
hits_igae = [(k, v) for k, v in INDICADORES_BIE.items() if "igae" in k]
check("búsqueda 'igae' retorna resultados", len(hits_igae) >= 6,
      f"got {len(hits_igae)}")

hits_bise = [(k, v) for k, v in INDICADORES_BIE.items() if k.startswith("bise_")]
check("prefijo 'bise_' retorna indicadores sociodemográficos",
      len(hits_bise) >= 19, f"got {len(hits_bise)}")


print("\n=== 9. PIB estatal geo=00 (debe funcionar a nivel nacional) ===")
raw_p = run("PIB estatal geo=00",
            lambda: client.get_indicator("746097", geo="00", recent_only=True))
if raw_p:
    rows_p = client.parse_series(raw_p)
    check("PIB estatal geo=00 retorna datos", len(rows_p) > 0)
    print(f"       PIB estatal nacional (último): {rows_p[-1]['time_period']}  {rows_p[-1]['obs_value']}")


print("\n=== 10. Balanza comercial ===")
raw_bc = run("Balanza saldo desest",
             lambda: client.get_indicator("87537", recent_only=True))
if raw_bc:
    rows_bc = client.parse_series(raw_bc)
    check("balanza comercial retorna dato", len(rows_bc) > 0)
    print(f"       Saldo balanza desest (último): {rows_bc[-1]['time_period']}  {rows_bc[-1]['obs_value']}")


# ---------------------------------------------------------------------------
print(f"\n{'='*45}")
print(f"  Resultado: {passed} OK   {failed} FAIL   {len(errors)} ERR")
if errors:
    print("\n  Errores de conexión:")
    for label, msg in errors:
        print(f"    {label}: {msg}")
print(f"{'='*45}\n")

sys.exit(0 if failed == 0 and len(errors) == 0 else 1)
