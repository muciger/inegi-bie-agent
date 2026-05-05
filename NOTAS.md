# Agente INEGI BIE — Notas de desarrollo

## Qué se construyó

Agente conversacional en Python que consulta el Banco de Información Económica (BIE) y el Banco de Indicadores Sociodemográficos (BISE) del INEGI. El usuario hace preguntas en lenguaje natural y el agente jala datos reales de la API usando el SDK de Anthropic con tool use.

Archivos en la carpeta:

| Archivo | Descripción |
|---|---|
| `inegi_bie_client.py` | Wrapper de la API BIE/BISE v2.0. 331 indicadores mapeados. |
| `agent.py` | Loop agentico con 3 tools: get_indicator, search_indicators, get_catalog |
| `scrape_bfs.py` | Scraper BFS del árbol interno con checkpoint (para exploración local) |
| `catalogo_ids.md` | Catálogo de los 331 IDs en 30 grupos. Referencia rápida. |
| `feeds_map.json` | Mapeo crudo de la página de feeds del INEGI (34 indicadores) |
| `indicadores_coyuntura.json` | Mapa parcial del árbol BIE, tema coyuntura (160 indicadores) |
| `requirements.txt` | Dependencias: anthropic, requests |

---

## Cómo ejecutar

```bash
export ANTHROPIC_API_KEY="sk-..."
export INEGI_TOKEN="tu-uuid-de-inegi"
pip install -r requirements.txt
python agent.py
```

Token INEGI: https://www.inegi.org.mx/app/desarrolladores/generatoken/

---

## API del BIE/BISE — estructura

### Endpoint principal (datos)

```
https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml
/INDICATOR/{id}/{lang}/{geo}/{recent}/{fuente}/2.0/{token}?type=json
```

Parámetros clave:

- `fuente`: `BIE-BISE` para indicadores económicos, `BISE` para sociodemografía
- `geo`: `00` = nacional, `01`-`32` = entidades federativas
- `recent`: `true` solo el dato más reciente, `false` serie completa
- Token va en la URL, no en headers

La API devuelve observaciones en orden cronológico inverso (más reciente primero). El cliente invierte con `rows.reverse()` en `parse_series()`.

### Endpoint de catálogos

```
/CL_INDICATOR/null/es/BIE-BISE/2.0/{token}?type=json
```

Retorna 90,757 IDs con nombres. Los nombres son genéricos ("Variación anual", "Total") sin contexto de la serie padre. Útil para CL_GEO_AREA, CL_FREQ, CL_UNIT, no para búsqueda por keyword.

### Endpoint interno del árbol (solo para scraping)

```
https://www.inegi.org.mx/app/api/indicadores/interna_v1_3/API.svc/NodosTemas
/null/es/{nodeId}/null/null/null/3/true/405/json/{token}?callback=?
```

Responde JSONP con formato `?([...]);`. Nodos de tipo `TEMA` (rama) o `INDICADOR` (hoja).

Requiere headers `Referer` y `Origin` apuntando a `inegi.org.mx`. Sin ellos, devuelve status 200 con cuerpo vacío.

Parámetros por árbol:
- BIE: `tematica=3`, `geo=null`, `tipo=true`
- BISE: `tematica=6`, `geo=null`, `tipo=false`

---

## Temas raíz del BIE

| Clave | Nombre | Indicadores |
|---|---|---|
| 1 | Indicadores económicos de coyuntura | 5,856 |
| 3817 | Ocupación, empleo y remuneraciones | 1,063 |
| 671866 | Indicadores de productividad. Base 2018 | 4,730 |
| 8061 | Cuentas nacionales | 27,331 |
| 18339 | Minería | 119 |
| 19027 | Manufacturas | 37,001 |
| 568856 | ENEC. Serie 2018 | 410 |
| 748431 | EAEC. Serie 2018 | 365 |
| 564496 | EMEC. Base 2018 | 566 |
| 565434 | EMS. Base 2018 | 1,500 |
| 36576 | Comunicaciones y transportes | 319 |
| 36694 | Sector externo | 8,782 |
| 776856 | Finanzas públicas | 48 |
| 682367 | Proyectos especiales | 214 |

Total: ~88,000 indicadores en el BIE completo.

---

## Catálogo de indicadores mapeados (331 series)

Ver `catalogo_ids.md` para la lista completa con IDs. Resumen por grupo:

| Grupo | Series | Descripción |
|---|---|---|
| IGAE | 21 | Total + subsectores, originales y variaciones desest. |
| PIB nacional | 28 | Por sectores + componentes de demanda, desest. |
| PIB estatal | 4 | Constantes, corrientes, IVF, participación. geo=00-32 |
| INPC | 20 | General, subyacente (mercancías/servicios), no subyacente, quincenal |
| INPP | 7 | Con/sin petróleo, variaciones mensual/anual |
| Actividad industrial | 19 | Total + 17 subsectores SCIAN, variaciones desest. |
| Balanza comercial | 22 | Saldos, exportaciones por tipo, importaciones por bien |
| Exportaciones estatales | 2 | Trimestral y anual. Solo geo=01-32. |
| ENOE mensual | 15 | Desocupación, informalidad, subocupación, participación (desest.) |
| ENOE trimestral | 21 | PEA, PNEA, ocupación, por sexo (absolutos) |
| Consumo privado | 13 | IMCPMI total + por tipo de bien y origen |
| Ventas menudeo | 3 | Nivel, variación, desest. |
| Confianza consumidor | 9 | ICC + 5 componentes, variaciones |
| FBCF | 13 | Total + maquinaria (nac/imp) + construcción (res/no-res) |
| Oferta y demanda global | 3 | Total, variación, desest. |
| EMOE | 16 | IAT, ICE (4 sectores), IPM (5 componentes) |
| EMIM | 7 | Personal, IVF, vol. producción, horas, remuneraciones |
| ENEC | 12 | Valor producción + 6 subsectores + personal/remun/horas |
| EMS | 16 | Ingresos + 10 subsectores + personal/gastos/remun |
| EMEC | 16 | Mayoreo (8) + menudeo (8), ingresos/personal/remun |
| IMMEX | 1 | Personal ocupado |
| ITAEE | 5 | Índice, con/sin petróleo, desest. Solo geo=01-32. |
| IMAI | 3 | Total, manufacturera, var. mensual |
| Automotriz | 2 | Subsector 336 + 3361 (IVF, BIE) |
| Minería | 6 | Total + variación + cobre/oro/plata |
| Indicadores cíclicos | 2 | Coincidente, adelantado |
| Gobierno | 1 | Consumo de gobierno anual |
| BISE Población | 1 | Población total |
| BISE Educación | 11 | Alfabetismo, escolaridad, asistencia, matriculación |
| BISE Salud | 5 | Derechohabiencia, IMSS, ISSSTE, sin cobertura |
| BISE Vivienda | 4 | Viviendas habitadas, electricidad, agua de red |

---

## Restricciones geográficas

Indicadores state-only (geo='00' retorna HTTP 400):

- ITAEE: `741177`, `741180`, `741181`, `741927`, `741929`
- Exportaciones por entidad: `629659`, `630459`

Declarados en `GEO_SOLO_ESTATAL` dentro de `inegi_bie_client.py`. El agente pasa geo por defecto '00'; para estos indicadores hay que especificar la entidad.

Indicadores que funcionan tanto con geo='00' como geo='01'-'32':

- PIB estatal: `746097`, `750453`, `749001`, `747549`
- La mayoría de series de coyuntura solo tienen nivel nacional (geo='00')

---

## Indicadores BISE (sociodemográficos)

Requieren `fuente="BISE"` en la llamada. El agente tiene este parámetro en la tool `get_indicator`.

Características:
- Frecuencia censal o quinquenal, no mensual
- Cubre educación, salud/derechohabiencia, vivienda
- Claves en el dict con prefijo `bise_` o `poblacion_total`
- El set `FUENTE_BISE` en `inegi_bie_client.py` identifica estos indicadores automáticamente

Ejemplo de uso:
```python
client.get_indicator("1002000041", fuente="BISE")  # % alfabetas 15+
```

---

## Indicadores pendientes (composites, no requieren ID nuevo)

| Nombre | Estrategia |
|---|---|
| igae_ioae_resumen | Combinar igae_total + igae_actividades_* |
| inflacion_resumen | Combinar inpc_inflacion_anual + subyacentes |
| pib_por_actividad | Combinar pib_desest_trimestral + variaciones sectoriales |
| pib_participacion | Usar pib_estatal_participacion (747549) por estado |

---

## Errores y soluciones

### 1. Fuente incorrecta (BISE vs BIE-BISE)

El cliente inicializaba con `fuente="BISE"`. Los indicadores económicos del BIE requieren `fuente="BIE-BISE"`. Con `BISE` la API regresaba 404 o series vacías. Corregido en `__init__` y en el dict `FUENTES`.

### 2. Orden cronológico invertido

La API devuelve el dato más reciente primero. `parse_series()` termina con `rows.reverse()`.

### 3. JSONP en la API interna del árbol

El endpoint `NodosTemas` responde con `?([...]);`. `json.loads()` falla directo. Solución:
```python
re.search(r"\?\((.*)\)", text, re.DOTALL)
```

Caso adicional: error `?({ErrorCode: "100", ...},202);` — el número `202` rompe el JSON. Se maneja con segundo regex que descarta el sufijo.

### 4. Headers requeridos en la API interna

Sin `Referer: https://www.inegi.org.mx/app/querybuilder2/default.html` y `Origin: https://www.inegi.org.mx`, el endpoint regresa status 200 sin resultados.

### 5. Parámetros distintos para árbol BIE vs BISE

BIE: `tematica=3`, `geo=null`, `tipo=true`. BISE: `tematica=6`, `geo=null`, `tipo=false`. Confundirlos devuelve cero nodos.

### 6. API interna lenta (~2.5s por request)

Con ~800 nodos en el árbol de coyuntura, el scraping completo toma ~500s secuencial. `ThreadPoolExecutor` con 4 workers lo reduce a ~130s pero el sandbox tiene límite de 45s. `scrape_bfs.py` usa checkpoint para correrlo localmente sin límite.

### 7. autos_ligeros/pesados en unidades (635031-635071)

El documento de referencia lista estas series como fallbacks BIE. Verificado: retornan HTTP 400 en el endpoint estándar. Removidos del dict. La fuente primaria es el parser AMIA (sitio externo).

### 8. CL_INDICATOR no sirve para búsqueda por keyword

90,757 entradas con nombres genéricos sin contexto de la serie padre. La búsqueda del agente usa el dict curado `INDICADORES_BIE`, no el catálogo completo.

---

## Cómo extender el mapeo

**Opción 1 — Constructor de Consultas:**
1. Ir a https://www.inegi.org.mx/app/querybuilder2/default.html?2.0
2. Navegar al tema de interés
3. Seleccionar el indicador y copiar la clave de la URL o el panel de vista previa
4. Agregar al dict con nombre descriptivo y sufijo de convención

**Opción 2 — Scraper BFS (para temas enteros):**
```bash
python scrape_bfs.py \
  --token 7656dc82-... \
  --start 8061 \
  --start-name "Cuentas nacionales" \
  --output indicadores_cuentas_nacionales.json
```

Completa en ~5-10 minutos por tema corriendo localmente.

**Convención de sufijos:**

| Sufijo | Significado |
|---|---|
| (sin sufijo) | Serie más frecuentemente consultada para ese indicador |
| `_orig` | Serie original, no desestacionalizada |
| `_desest` | Serie desestacionalizada, nivel/índice |
| `_var_mens` o `_var_mensual` | Variación mensual desest. |
| `_var_anual` | Variación anual desest. |

Para desglose sectorial de exportaciones por entidad, navegar desde nodo 38035 (trimestral) o 38068 (anual): cada uno tiene 28 series por sector SCIAN, todas state-only.
