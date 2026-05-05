# Agente INEGI BIE

Agente conversacional en Python para consultar el [Banco de Información Económica (BIE)](https://www.inegi.org.mx/servicios/api_indicadores.html) y el Banco de Indicadores Sociodemográficos (BISE) del INEGI. El usuario hace preguntas en lenguaje natural y el agente obtiene datos reales de la API usando el SDK de Anthropic con tool use.

**331 series mapeadas:** IGAE, PIB nacional y estatal, INPC, INPP, actividad industrial, balanza comercial, exportaciones por entidad, ENOE, encuestas sectoriales (EMOE, EMIM, ENEC, EMS, EMEC), ITAEE, indicadores cíclicos, y sociodemográficos BISE (educación, salud, vivienda).

---

## Requisitos

- Python 3.10+
- Clave de API de Anthropic: https://console.anthropic.com
- Token de INEGI: https://www.inegi.org.mx/app/desarrolladores/generatoken/

## Instalación

```bash
git clone https://github.com/tu-usuario/inegi-bie-agent.git
cd inegi-bie-agent
pip install -r requirements.txt
```

## Configuración

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export INEGI_TOKEN="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

## Uso

### Agente conversacional

```bash
python agent.py
```

```
Agente INEGI BIE activo. Escribe 'salir' para terminar.

Tú: ¿Cuál fue el IGAE de marzo 2025?
Agente: El IGAE total de marzo de 2025 registró una variación anual de...

Tú: Dame la tasa de desocupación desestacionalizada
Tú: ¿Cómo van las exportaciones de Nuevo León este año?
```

### Cliente directo (sin agente)

```python
from inegi_bie_client import INEGIBIEClient
import os

client = INEGIBIEClient(token=os.environ["INEGI_TOKEN"])

# Inflación anual — últimos 6 datos
obs = client.get_indicator("910406")
rows = client.parse_series(obs)
for r in rows[-6:]:
    print(r["time_period"], r["obs_value"])

# ITAEE Jalisco (requiere geo estatal)
obs = client.get_indicator("741927", geo="14")
rows = client.parse_series(obs)
print(rows[-1])

# Indicador BISE (educación, salud, vivienda)
obs = client.get_indicator("1005000038", fuente="BISE")
rows = client.parse_series(obs)
print(rows[-1])
```

Ver [`INEGI_BIE_referencia.md`](INEGI_BIE_referencia.md) para el catálogo completo de IDs y ejemplos adicionales.

---

## Archivos

| Archivo | Descripción |
|---|---|
| `inegi_bie_client.py` | Wrapper de la API BIE/BISE v2.0. 331 indicadores mapeados. |
| `agent.py` | Loop agentico con 3 tools: `get_indicator`, `search_indicators`, `get_catalog` |
| `scrape_bfs.py` | Scraper BFS del árbol interno para explorar y agregar nuevos indicadores |
| `INEGI_BIE_referencia.md` | Referencia completa: endpoint, parámetros, script Python y catálogo de IDs |
| `catalogo_ids.md` | Catálogo de 331 IDs agrupados por tema |

## Scraper (para explorar nuevos indicadores)

```bash
python scrape_bfs.py \
  --token $INEGI_TOKEN \
  --start 8061 \
  --start-name "Cuentas nacionales" \
  --output cuentas_nacionales.json
# Si no termina en una ejecución, vuelve a correr — retoma desde el checkpoint
```

---

## Notas sobre la API

- `fuente=BIE-BISE` para indicadores económicos. `fuente=BISE` para sociodemográficos.
- `geo=00` = nacional. `geo=01`-`32` = entidad federativa.
- ITAEE (`741927`, `741929`) y exportaciones por entidad (`629659`, `630459`) solo aceptan `geo=01`-`32`.
- La API devuelve observaciones en orden cronológico inverso. `parse_series()` invierte el orden.

## Licencia

MIT
