# INEGI BIE/BISE API — Referencia de uso y catálogo de indicadores

> 331 series mapeadas. Actualizado: mayo 2025.


## 1. Autenticación

Obtén un token UUID en:
https://www.inegi.org.mx/app/desarrolladores/generatoken/

El token va en la URL, no en headers. Guárdalo como variable de entorno:

```bash
export INEGI_TOKEN="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

---

## 2. Endpoint principal

```
GET https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml
    /INDICATOR/{indicator_id}/{lang}/{geo}/{recent}/{fuente}/2.0/{token}?type=json
```

### Parámetros

| Parámetro | Valores | Descripción |
|---|---|---|
| `indicator_id` | número | Clave del indicador (ver catálogo abajo) |
| `lang` | `es` / `en` | Idioma de las etiquetas |
| `geo` | `00` / `01`-`32` | `00` = nacional. `01`-`32` = entidad federativa |
| `recent` | `true` / `false` | `true` = solo el dato más reciente |
| `fuente` | `BIE-BISE` / `BISE` | `BIE-BISE` para económicos. `BISE` para socioeconómicos. |
| `token` | UUID | Token personal del desarrollador |

### Notas críticas

- Las series marcadas `[solo estatal]` solo aceptan `geo=01`-`32`. `geo=00` retorna HTTP 400.
- Las series marcadas `[BISE]` requieren `fuente=BISE`. Con `BIE-BISE` regresan vacías o 404.
- La respuesta trae las observaciones en orden **cronológico inverso** (más reciente primero).

---

## 3. Endpoint de catálogos de metadatos

```
GET .../CL_INDICATOR/{id_o_null}/{lang}/BIE-BISE/2.0/{token}?type=json
```

Catálogos disponibles:

| Catálogo | Descripción |
|---|---|
| `CL_INDICATOR` | Nombres de indicadores (90,757 registros) |
| `CL_UNIT` | Unidades de medida |
| `CL_FREQ` | Frecuencias (mensual, trimestral, anual, quincenal) |
| `CL_GEO_AREA` | Áreas geográficas disponibles |
| `CL_SOURCE` | Fuentes estadísticas |
| `CL_TOPIC` | Temas |
| `CL_NOTE` | Notas metodológicas |
| `CL_STATUS` | Estatus de la observación |

---

## 4. Códigos geográficos

| Código | Entidad |
|---|---|
| 00 | Nacional |
| 01 | Aguascalientes |
| 02 | Baja California |
| 03 | Baja California Sur |
| 04 | Campeche |
| 05 | Coahuila |
| 06 | Colima |
| 07 | Chiapas |
| 08 | Chihuahua |
| 09 | Ciudad de México |
| 10 | Durango |
| 11 | Guanajuato |
| 12 | Guerrero |
| 13 | Hidalgo |
| 14 | Jalisco |
| 15 | Estado de México |
| 16 | Michoacán |
| 17 | Morelos |
| 18 | Nayarit |
| 19 | Nuevo León |
| 20 | Oaxaca |
| 21 | Puebla |
| 22 | Querétaro |
| 23 | Quintana Roo |
| 24 | San Luis Potosí |
| 25 | Sinaloa |
| 26 | Sonora |
| 27 | Tabasco |
| 28 | Tamaulipas |
| 29 | Tlaxcala |
| 30 | Veracruz |
| 31 | Yucatán |
| 32 | Zacatecas |

---

## 5. Script Python autocontenido

```python
import os
import requests

TOKEN = os.environ["INEGI_TOKEN"]
BASE = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"


def get_indicator(
    indicator_id: str,
    geo: str = "00",
    recent_only: bool = False,
    fuente: str = "BIE-BISE",
    lang: str = "es",
) -> list[dict]:
    """
    Consulta un indicador del BIE/BISE del INEGI.

    Retorna lista de observaciones en orden cronológico ascendente.
    Cada elemento: {indicator_id, freq, unit, time_period, obs_value, geo, last_update}

    Args:
        indicator_id: Clave numérica del indicador.
        geo: '00' = nacional. '01'-'32' = entidad federativa.
             ITAEE (741927, 741929) y exportaciones por entidad (629659, 630459)
             solo aceptan '01'-'32'.
        recent_only: True para solo el dato más reciente.
        fuente: 'BIE-BISE' para económicos (default).
                'BISE' para indicadores sociodemográficos.
        lang: 'es' (default) o 'en'.
    """
    recent = "true" if recent_only else "false"
    url = f"{BASE}/INDICATOR/{indicator_id}/{lang}/{geo}/{recent}/{fuente}/2.0/{TOKEN}?type=json"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for series in data.get("Series", []):
        for obs in series.get("OBSERVATIONS", []):
            rows.append({
                "indicator_id": series.get("INDICADOR"),
                "freq":         series.get("FREQ"),
                "unit":         series.get("UNIT"),
                "last_update":  series.get("LASTUPDATE"),
                "time_period":  obs.get("TIME_PERIOD"),
                "obs_value":    obs.get("OBS_VALUE"),
                "geo":          obs.get("COBER_GEO"),
            })
    rows.reverse()   # cronológico ascendente
    return rows


def get_catalog(catalog: str, catalog_id: str = None, fuente: str = "BIE-BISE") -> list:
    """
    Consulta un catálogo de metadatos.
    catalog: CL_INDICATOR | CL_UNIT | CL_FREQ | CL_GEO_AREA | CL_SOURCE |
             CL_TOPIC | CL_NOTE | CL_STATUS
    """
    id_str = catalog_id or "null"
    url = f"{BASE}/{catalog}/{id_str}/es/{fuente}/2.0/{TOKEN}?type=json"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json().get("CODE", [])


# ---------------------------------------------------------------------------
# Ejemplos de uso
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # 1. IGAE total — último dato
    obs = get_indicator("737121", recent_only=True)
    print(obs[0])
    # {'indicator_id': '737121', 'freq': 'M', 'unit': '...',
    #  'time_period': '2025/03', 'obs_value': '107.2', 'geo': '00', ...}

    # 2. Inflación anual — serie completa
    obs = get_indicator("910406")
    for o in obs[-6:]:   # últimas 6 observaciones
        print(o["time_period"], o["obs_value"])

    # 3. ITAEE Jalisco (estado 14) — desestacionalizado
    obs = get_indicator("741927", geo="14")
    print(obs[-1])   # dato más reciente disponible

    # 4. Tasa de desocupación desestacionalizada
    obs = get_indicator("444884")
    print(obs[-1])

    # 5. Exportaciones de Nuevo León (trimestral)
    obs = get_indicator("629659", geo="19")
    print(obs[-4:])   # últimos 4 trimestres

    # 6. PIB estatal CDMX a precios constantes
    obs = get_indicator("746097", geo="09")
    print(obs[-3:])

    # 7. Indicador BISE: % afiliado a servicios de salud
    obs = get_indicator("6207019018", fuente="BISE")
    print(obs[-1])

    # 8. Indicador BISE: promedio de escolaridad
    obs = get_indicator("1005000038", fuente="BISE")
    for o in obs:
        print(o["time_period"], o["obs_value"])

    # 9. Catálogo de frecuencias disponibles
    freqs = get_catalog("CL_FREQ")
    for f in freqs:
        print(f)

    # 10. Consultar metadatos de un indicador específico
    meta = get_catalog("CL_INDICATOR", "910406")
    print(meta)
```

---

## 6. Estructura de la respuesta

La API retorna un JSON con dos claves principales:

```json
{
  "Header": { ... },
  "Series": [
    {
      "INDICADOR": "910406",
      "FREQ": "M",
      "UNIT": "Tasa",
      "LASTUPDATE": "2025-04-24",
      "OBSERVATIONS": [
        {
          "TIME_PERIOD": "2025/03",
          "OBS_VALUE": "3.80",
          "COBER_GEO": "00"
        }
      ]
    }
  ]
}
```

Campos clave:

| Campo | Descripción |
|---|---|
| `FREQ` | `M`=mensual, `T`=trimestral, `A`=anual, `Q`=quincenal |
| `UNIT` | Código de unidad (ver `CL_UNIT` para descripción) |
| `TIME_PERIOD` | Formato: `YYYY/MM` (mensual), `YYYY/T` (trimestral), `YYYY` (anual) |
| `OBS_VALUE` | Valor de la observación como string. Convertir con `float()`. |
| `COBER_GEO` | Código geográfico de la observación |

---

## 7. Catálogo de indicadores mapeados (331 series)

Sufijos de convención:
- `_orig` = serie original, no desestacionalizada
- `_desest` = serie desestacionalizada, nivel/índice
- `_var_mens` / `_var_mensual` = variación mensual desestacionalizada
- `_var_anual` = variación anual desestacionalizada
- (sin sufijo) = serie principal para ese indicador

`[solo estatal]` = geo='00' retorna HTTP 400; usar geo='01'-'32'.
`[BISE]` = pasar fuente='BISE' en la llamada.



### IGAE — Indicador Global de la Actividad Económica (mensual, base 2018)

| Clave | ID |
|---|---|
| `igae_total` | `737121` |
| `igae_total_variacion` | `737145` |
| `igae_total_desest` | `737219` |
| `igae_actividades_primarias` | `737096` |
| `igae_actividades_secundarias` | `737104` |
| `igae_actividades_terciarias` | `737115` |
| `igae_desest_var_mensual` | `737220` |
| `igae_desest_var_anual` | `737221` |
| `igae_primarias_var_mensual` | `737227` |
| `igae_primarias_var_anual` | `737228` |
| `igae_secundarias_var_mensual` | `737234` |
| `igae_secundarias_var_anual` | `737235` |
| `igae_terciarias_var_mensual` | `737269` |
| `igae_terciarias_var_anual` | `737270` |
| `igae_mineria_var_anual` | `737242` |
| `igae_energia_var_anual` | `737249` |
| `igae_construccion_var_anual` | `737256` |
| `igae_manufacturas_var_anual` | `737263` |
| `igae_comercio_mayoreo_var_anual` | `737277` |
| `igae_comercio_menudeo_var_anual` | `737284` |
| `igae_transportes_var_anual` | `737291` |
| `igae_serv_financieros_var_anual` | `737305` |
| `igae_serv_inmobiliarios_var_anual` | `737312` |
| `igae_serv_profesionales_var_anual` | `737319` |
| `igae_gobierno_var_anual` | `737368` |

### PIB trimestral nacional (base 2018)

| Clave | ID |
|---|---|
| `pib_vol_2018_trimestral` | `735879` |
| `pib_variacion_anual` | `735904` |
| `pib_desest_trimestral` | `736181` |
| `pib_precios_corrientes` | `735979` |
| `pib_precios_corrientes_valor` | `734407` |
| `pib_anual_vol_2018` | `782389` |
| `pib_desest_eo` | `736183` |
| `pib_desest_trim` | `736182` |
| `pib_primarias_var_trim` | `736196` |
| `pib_primarias_var_anual` | `736197` |
| `pib_secundarias_var_trim` | `736203` |
| `pib_secundarias_var_anual` | `736204` |
| `pib_terciarias_var_trim` | `736238` |
| `pib_terciarias_var_anual` | `736239` |
| `pib_mineria_var_anual` | `736211` |
| `pib_energia_var_anual` | `736218` |
| `pib_construccion_var_anual` | `736225` |
| `pib_manufacturas_var_anual` | `736232` |
| `pib_comercio_mayoreo_var_anual` | `736246` |
| `pib_comercio_menudeo_var_anual` | `736253` |
| `pib_transportes_var_anual` | `736260` |
| `pib_serv_financieros_var_anual` | `736274` |
| `pib_serv_inmobiliarios_var_anual` | `736281` |
| `pib_serv_profesionales_var_anual` | `736288` |
| `pib_gobierno_var_anual` | `736344` |
| `pib_consumo_privado_var_trim` | `737474` |
| `pib_consumo_privado_var_anual` | `737475` |
| `pib_consumo_gobierno_var_trim` | `737481` |
| `pib_consumo_gobierno_var_anual` | `737482` |
| `pib_fbcf_var_trim` | `737488` |
| `pib_fbcf_var_anual` | `737489` |
| `pib_fbcf_privada_var_anual` | `737503` |
| `pib_fbcf_publica_var_anual` | `737496` |
| `pib_exportaciones_var_trim` | `737516` |
| `pib_exportaciones_var_anual` | `737517` |
| `pib_importaciones_var_trim` | `737460` |
| `pib_importaciones_var_anual` | `737461` |

### PIB por entidad federativa (anual, geo=00 o 01-32)

| Clave | ID |
|---|---|
| `pib_estatal_constante` | `746097` |
| `pib_estatal_corriente` | `750453` |
| `pib_estatal_ivf` | `749001` |
| `pib_estatal_participacion` | `747549` |

### INPC — Inflación (mensual y quincenal)

| Clave | ID |
|---|---|
| `inpc_inflacion_mensual` | `910399` |
| `inpc_inflacion_anual` | `910406` |
| `inpc_inflacion_acumulada` | `910413` |
| `inpc_inflacion_mensual_sub` | `910400` |
| `inpc_inflacion_anual_sub` | `910407` |
| `inpc_inflacion_acumul_sub` | `910414` |
| `inpc_subyacente_mercancias_mens` | `910401` |
| `inpc_subyacente_mercancias_anual` | `910408` |
| `inpc_subyacente_servicios_mens` | `910402` |
| `inpc_subyacente_servicios_anual` | `910409` |
| `inpc_no_subyacente_mensual` | `910403` |
| `inpc_no_subyacente_anual` | `910410` |
| `inpc_no_subyacente_agrop_mens` | `910404` |
| `inpc_no_subyacente_agrop_anual` | `910411` |
| `inpc_no_subyacente_energ_mens` | `910405` |
| `inpc_no_subyacente_energ_anual` | `910412` |
| `inpc_quincenal` | `910427` |
| `inpc_quincenal_sub` | `910428` |
| `inpc_quincenal_interanual` | `910438` |
| `inpc_quincenal_interanual_sub` | `910439` |

### INPP — Índice Nacional de Precios al Productor (mensual)

| Clave | ID |
|---|---|
| `inpp_indice_total` | `1700001` |
| `inpp_indice_con_petroleo` | `1700002` |
| `inpp_manufactureras` | `1700244` |
| `inpp_variacion_sin_petroleo` | `1800001` |
| `inpp_variacion_con_petroleo` | `1800002` |
| `inpp_variacion_sin_pet_anual` | `1801001` |
| `inpp_variacion_con_pet_anual` | `1801002` |

### Actividad industrial (mensual, base 2018)

| Clave | ID |
|---|---|
| `actind_total` | `736407` |
| `actind_variacion` | `736526` |
| `actind_desest` | `736885` |
| `manufactureras_variacion_anual` | `736537` |
| `actind_var_mensual` | `736886` |
| `actind_mineria_var` | `736893` |
| `actind_energia_var` | `736921` |
| `actind_construccion_var` | `736942` |
| `actind_manufactureras_var` | `736970` |
| `actind_alimentos_var_anual` | `736978` |
| `actind_bebidas_var_anual` | `736985` |
| `actind_textil_var_anual` | `737006` |
| `actind_cuero_var_anual` | `737013` |
| `actind_madera_var_anual` | `737020` |
| `actind_papel_var_anual` | `737027` |
| `actind_quimica_var_anual` | `737048` |
| `actind_plastico_var_anual` | `737055` |
| `actind_metales_var_anual` | `737069` |
| `actind_metalicos_var_anual` | `737076` |
| `actind_maquinaria_var_anual` | `737083` |
| `actind_computacion_var_anual` | `737090` |
| `actind_electrico_var_anual` | `737097` |
| `actind_transporte_var_anual` | `737104` |

### Sector externo — Balanza comercial (mensual, desest.)

| Clave | ID |
|---|---|
| `balanza_comercial_saldo` | `897` |
| `balanza_comercial_desest` | `87537` |
| `balanza_saldo_petrolero` | `206780` |
| `balanza_saldo_no_petrolero` | `206782` |
| `balanza_exportaciones_mensual` | `451979` |
| `balanza_exportaciones_anual` | `451980` |
| `balanza_export_petroleras_mens` | `451983` |
| `balanza_export_petroleras_anual` | `451984` |
| `balanza_export_no_pet_mensual` | `451995` |
| `balanza_export_no_pet_anual` | `451996` |
| `balanza_export_agropecuarias` | `452000` |
| `balanza_export_extractivas` | `452004` |
| `balanza_export_manufacturas` | `452008` |
| `balanza_export_automotriz_mens` | `452011` |
| `balanza_export_automotriz_anual` | `452012` |
| `balanza_export_resto_manuf` | `452016` |
| `balanza_import_consumo_mensual` | `452031` |
| `balanza_import_consumo_anual` | `452032` |
| `balanza_import_intermedios_mens` | `452043` |
| `balanza_import_intermedios_anual` | `452044` |
| `balanza_import_capital_mensual` | `452055` |
| `balanza_import_capital_anual` | `452056` |

### Exportaciones por entidad federativa [solo geo=01-32]

| Clave | ID |
|---|---|
| `export_entidad_trimestral` | `629659` `[solo estatal]` |
| `export_entidad_anual` | `630459` `[solo estatal]` |

### Mercado laboral — ENOE mensual (tasas nacionales, desest.)

| Clave | ID |
|---|---|
| `tasa_desocupacion` | `444883` |
| `tasa_desocupacion_desest` | `444884` |
| `tasa_desocupacion_hombres` | `444887` |
| `tasa_desocupacion_mujeres` | `444890` |
| `tasa_participacion` | `444875` |
| `tasa_participacion_hombres` | `444878` |
| `tasa_participacion_mujeres` | `444881` |
| `tasa_subocupacion` | `444899` |
| `tasa_informalidad` | `444893` |
| `tasa_ocupacion` | `454853` |
| `tasa_ocupacion_parcial` | `444604` |
| `tasa_participacion_urbana` | `444902` |
| `tasa_desocupacion_urbana` | `444911` |
| `tasa_subocupacion_urbana` | `668897` |
| `tasa_informalidad_urbana` | `444920` |

### ENOE trimestral — población 15 años y más (absolutos)

| Clave | ID |
|---|---|
| `enoe_pob_total` | `289242` |
| `enoe_pea_total` | `289244` |
| `enoe_pea_ocupada` | `289245` |
| `enoe_pea_desocupada` | `289246` |
| `enoe_pnea_total` | `289247` |
| `enoe_pnea_disponible` | `289248` |
| `enoe_pnea_no_disponible` | `289249` |
| `enoe_desocupada_total` | `289289` |
| `enoe_pob_hombres` | `289292` |
| `enoe_pea_hombres` | `289294` |
| `enoe_pea_ocupada_hombres` | `289295` |
| `enoe_pea_desocupada_hombres` | `289296` |
| `enoe_pnea_hombres` | `289297` |
| `enoe_pnea_disponible_hombres` | `289298` |
| `enoe_pnea_no_disponible_hombres` | `289299` |
| `enoe_pob_mujeres` | `289342` |
| `enoe_pea_mujeres` | `289344` |
| `enoe_pea_ocupada_mujeres` | `289345` |
| `enoe_pea_desocupada_mujeres` | `289346` |
| `enoe_pnea_mujeres` | `289347` |
| `enoe_pnea_disponible_mujeres` | `289348` |
| `enoe_pnea_no_disponible_mujeres` | `289349` |

### Consumo privado (IMCPMI, mensual, desest.)

| Clave | ID |
|---|---|
| `consumo_privado_var_anual` | `740946` |
| `consumo_privado_mensual` | `740988` |
| `consumo_privado_var_anual_desest` | `740989` |
| `consumo_privado_nacional_mens` | `740995` |
| `consumo_privado_nacional_anual` | `740996` |
| `consumo_privado_importado_mens` | `741016` |
| `consumo_privado_importado_anual` | `741017` |
| `consumo_privado_duraderos_nac` | `740949` |
| `consumo_privado_semi_nac` | `740950` |
| `consumo_privado_no_dur_nac` | `740951` |
| `consumo_privado_servicios_nac` | `740952` |
| `consumo_privado_duraderos_imp` | `740955` |
| `consumo_privado_semi_imp` | `740956` |
| `consumo_privado_no_dur_imp` | `740957` |

### Ventas al menudeo (mensual)

| Clave | ID |
|---|---|
| `ventas_menudeo` | `718506` |
| `ventas_menudeo_var` | `718507` |
| `ventas_menudeo_desest` | `718942` |

### Confianza del consumidor — ICC (mensual, desest.)

| Clave | ID |
|---|---|
| `confianza_consumidor` | `454168` |
| `confianza_consumidor_desest` | `454186` |
| `icc_var_mensual` | `454187` |
| `icc_var_anual` | `454188` |
| `icc_hogar_actual_var` | `454195` |
| `icc_hogar_futuro_var` | `454202` |
| `icc_pais_actual_var` | `454209` |
| `icc_pais_futuro_var` | `454216` |
| `icc_compra_durables_var` | `454223` |

### FBCF — Formación bruta de capital fijo (mensual, desest.)

| Clave | ID |
|---|---|
| `fbcf_total` | `741020` |
| `fbcf_variacion` | `741040` |
| `fbcf_desest` | `741100` |
| `fbcf_total_mensual` | `741103` |
| `fbcf_total_var_anual` | `741104` |
| `fbcf_maquinaria_mensual` | `741110` |
| `fbcf_maquinaria_var_anual` | `741111` |
| `fbcf_construccion_mensual` | `741159` |
| `fbcf_construccion_var_anual` | `741160` |
| `fbcf_construccion_residencial` | `741167` |
| `fbcf_construccion_no_residencial` | `741174` |
| `fbcf_maquinaria_nacional` | `741118` |
| `fbcf_maquinaria_importada` | `741139` |

### Oferta y demanda global (trimestral)

| Clave | ID |
|---|---|
| `odgbs_total` | `737371` |
| `odgbs_variacion` | `737374` |
| `odgbs_desest` | `737445` |

### EMOE — Encuesta Mensual de Opinión Empresarial (mensual)

| Clave | ID |
|---|---|
| `emoe_iat_manufacturero` | `701490` |
| `emoe_iat_mensual` | `910455` |
| `emoe_iat_anual` | `910456` |
| `emoe_iat_construccion_var` | `701417` |
| `emoe_iat_comercio_var` | `701860` |
| `emoe_ice_manufacturero` | `701570` |
| `emoe_ice_mensual` | `910462` |
| `emoe_ice_anual` | `910463` |
| `emoe_ice_manufacturas_var` | `701740` |
| `emoe_ice_construccion_var` | `701452` |
| `emoe_ice_comercio_var` | `701902` |
| `emoe_ice_servicios_var` | `702056` |
| `emoe_ipm_manufacturero` | `701618` |
| `emoe_ipm_mensual` | `701781` |
| `emoe_ipm_anual` | `701782` |
| `emoe_ipm_pedidos_var` | `701789` |
| `emoe_ipm_produccion_var` | `701796` |
| `emoe_ipm_personal_var` | `701803` |
| `emoe_ipm_entrega_var` | `701810` |
| `emoe_ipm_inventarios_var` | `701817` |

### EMIM — Encuesta Mensual Industria Manufacturera (mensual)

| Clave | ID |
|---|---|
| `emim_personal_orig` | `702139` |
| `emim_ivf_desest` | `910466` |
| `emim_ivf_variacion_desest` | `910467` |
| `emim_volumen_var` | `910469` |
| `emim_personal_var` | `702336` |
| `emim_horas_trabajadas` | `702504` |
| `emim_remuneraciones_reales` | `702672` |

### ENEC — Encuesta Nacional Empresas Constructoras (mensual)

| Clave | ID |
|---|---|
| `enec_valor_prod_orig` | `720322` |
| `enec_valor_prod_desest` | `720346` |
| `enec_valor_prod_var` | `720349` |
| `enec_personal_ocupado` | `720398` |
| `enec_remuneraciones` | `720440` |
| `enec_horas_trabajadas` | `720461` |
| `enec_edificacion_var` | `720357` |
| `enec_agua_saneamiento_var` | `720364` |
| `enec_electricidad_telecom_var` | `720371` |
| `enec_transporte_var` | `720378` |
| `enec_petroleo_var` | `720385` |
| `enec_otras_construcciones_var` | `720392` |

### EMS — Encuesta Mensual de Servicios (mensual)

| Clave | ID |
|---|---|
| `ems_ingresos_orig` | `715722` |
| `ems_ingresos_desest` | `715854` |
| `ems_ingresos_var` | `715857` |
| `ems_personal` | `715927` |
| `ems_remuneraciones` | `716004` |
| `ems_gastos` | `715997` |
| `ems_transporte_var` | `715865` |
| `ems_info_medios_var` | `715872` |
| `ems_inmobiliarios_var` | `715879` |
| `ems_profesionales_var` | `715886` |
| `ems_apoyo_negocios_var` | `715893` |
| `ems_educativos_var` | `715900` |
| `ems_salud_var` | `715907` |
| `ems_esparcimiento_var` | `715914` |
| `ems_alojamiento_var` | `715921` |
| `ems_otros_servicios_var` | `720276` |

### EMEC — Encuesta Mensual Empresas Comerciales (mensual)

| Clave | ID |
|---|---|
| `emec_mayoreo_orig` | `718480` |
| `emec_mayoreo_desest` | `718520` |
| `emec_mayoreo_personal` | `718523` |
| `emec_mayoreo_remuneracion` | `718530` |
| `emec_mayoreo_ingresos` | `718537` |
| `emec_mayoreo_mercancias` | `718922` |
| `emec_mayoreo_farma_var` | `718797` |
| `emec_mayoreo_intermediacion_var` | `718909` |
| `emec_menudeo_personal` | `718929` |
| `emec_menudeo_remuneracion` | `718936` |
| `emec_menudeo_mercancias` | `719370` |
| `emec_menudeo_vehiculos_var` | `719329` |
| `emec_menudeo_textiles_var` | `719217` |
| `emec_menudeo_papeleria_var` | `719252` |
| `emec_menudeo_ferreteria_var` | `719322` |
| `emec_menudeo_internet_var` | `719364` |

### IMMEX (mensual)

| Clave | ID |
|---|---|
| `immex_personal_ocupado` | `203933` |

### ITAEE — Actividad Económica Estatal (trimestral) [solo geo=01-32]

| Clave | ID |
|---|---|
| `itaee_indice` | `741177` `[solo estatal]` |
| `itaee_con_petroleo` | `741180` `[solo estatal]` |
| `itaee_sin_petroleo` | `741181` `[solo estatal]` |
| `itaee_indice_desest` | `741927` `[solo estatal]` |
| `itaee_var_anual` | `741929` `[solo estatal]` |

### IMAI — Actividad Industrial Estatal (mensual)

| Clave | ID |
|---|---|
| `imai_total_nacional` | `738182` |
| `imai_manufacturera_total` | `736418` |
| `imai_manufacturera_var` | `739277` |

### Subsector automotriz — IVF (mensual, base 2018)

| Clave | ID |
|---|---|
| `actind_automotriz_total` | `736511` |
| `actind_automoviles_camiones` | `736512` |

### Minería y metalurgia (mensual)

| Clave | ID |
|---|---|
| `mineria_total` | `656` |
| `mineria_variacion` | `657` |
| `mineria_desest` | `661524` |
| `cobre_produccion` | `666` |
| `oro_produccion` | `659` |
| `plata_produccion` | `660` |

### Indicadores cíclicos (mensual)

| Clave | ID |
|---|---|
| `indicador_coincidente` | `214294` |
| `indicador_adelantado` | `214308` |

### Gobierno (anual)

| Clave | ID |
|---|---|
| `consumo_gobierno_total` | `728658` |

### BISE — Población

| Clave | ID |
|---|---|
| `poblacion_total` | `1002000001` `[BISE]` |

### BISE — Educación [fuente=BISE]

| Clave | ID |
|---|---|
| `bise_alfabetismo_15mas` | `1002000041` `[BISE]` |
| `bise_tasa_alfab_15_24` | `1002000050` `[BISE]` |
| `bise_escolaridad_promedio` | `1005000038` `[BISE]` |
| `bise_asistencia_primaria` | `6207019026` `[BISE]` |
| `bise_asistencia_secundaria` | `6207019028` `[BISE]` |
| `bise_asistencia_superior` | `6207019029` `[BISE]` |
| `bise_pct_sin_instruccion` | `6200240447` `[BISE]` |
| `bise_pct_instruccion_superior` | `6200240365` `[BISE]` |
| `bise_pct_rezago_educativo` | `6200240391` `[BISE]` |
| `bise_matriculacion_primaria` | `6000000001` `[BISE]` |
| `bise_matriculacion_preescolar` | `6000000004` `[BISE]` |

### BISE — Salud y derechohabiencia [fuente=BISE]

| Clave | ID |
|---|---|
| `bise_derechohabiente_total` | `1004000001` `[BISE]` |
| `bise_pct_afiliado_salud` | `6207019018` `[BISE]` |
| `bise_pct_imss` | `6200240471` `[BISE]` |
| `bise_pct_issste` | `6200240421` `[BISE]` |
| `bise_pct_no_afiliado` | `6207049072` `[BISE]` |

### BISE — Vivienda y servicios [fuente=BISE]

| Clave | ID |
|---|---|
| `bise_viviendas_habitadas` | `1003000011` `[BISE]` |
| `bise_ocupantes_promedio` | `1003000015` `[BISE]` |
| `bise_viviendas_electricidad` | `1003000017` `[BISE]` |
| `bise_viviendas_agua_red` | `1003000018` `[BISE]` |