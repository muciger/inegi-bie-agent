"""
INEGI BIE / BISE API Client
Wrapper para la API de Indicadores del Banco de Información Económica (BIE)
y el Banco de Indicadores Sociodemográficos (BISE) v2.0.
Docs: https://www.inegi.org.mx/servicios/api_indicadores.html
"""

import requests
from typing import Optional


BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"

FUENTES = {
    "demografía": "BISE",
    "economía":   "BIE-BISE",
}

# ---------------------------------------------------------------------------
# Mapeo curado de indicadores.
# Fuentes: feeds.html, Constructor de Consultas, INEGI_BIE_API_reference.md,
#          y navegación directa del árbol BIE/BISE.
#
# Convención de sufijos:
#   _orig      = serie original (no desest.)
#   _desest    = serie desestacionalizada, nivel/índice
#   _var_mens  = variación mensual desest.
#   _var_anual = variación anual desest.
#   (sin sufijo) = serie más frecuentemente consultada para ese indicador
# ---------------------------------------------------------------------------
INDICADORES_BIE = {

    # =========================================================================
    # IGAE — Indicador Global de la Actividad Económica (mensual, base 2018)
    # Árbol BIE: 603587
    # =========================================================================

    # --- Índices nivel (series originales) ---
    "igae_total":                       "737121",  # Total, series originales
    "igae_total_variacion":             "737145",  # Var. mensual orig
    "igae_total_desest":                "737219",  # Total desest, nivel
    "igae_actividades_primarias":       "737096",  # Primarias, orig
    "igae_actividades_secundarias":     "737104",  # Secundarias, orig
    "igae_actividades_terciarias":      "737115",  # Terciarias, orig

    # --- Variaciones desest. (ref. doc) ---
    "igae_desest_var_mensual":          "737220",  # Total desest, var. mensual
    "igae_desest_var_anual":            "737221",  # Total desest, var. anual
    "igae_primarias_var_mensual":       "737227",
    "igae_primarias_var_anual":         "737228",
    "igae_secundarias_var_mensual":     "737234",
    "igae_secundarias_var_anual":       "737235",
    "igae_terciarias_var_mensual":      "737269",
    "igae_terciarias_var_anual":        "737270",
    "igae_mineria_var_anual":           "737242",
    "igae_energia_var_anual":           "737249",
    "igae_construccion_var_anual":      "737256",
    "igae_manufacturas_var_anual":      "737263",
    "igae_comercio_mayoreo_var_anual":  "737277",
    "igae_comercio_menudeo_var_anual":  "737284",
    "igae_transportes_var_anual":       "737291",
    "igae_serv_financieros_var_anual":  "737305",
    "igae_serv_inmobiliarios_var_anual":"737312",
    "igae_serv_profesionales_var_anual":"737319",
    "igae_gobierno_var_anual":          "737368",

    # =========================================================================
    # PIB trimestral — nacional (desest., base 2018)
    # Árbol BIE: 600253 (sectores) + 605590 (oferta y demanda global)
    # =========================================================================

    # --- Por sectores, nivel ---
    "pib_vol_2018_trimestral":          "735879",  # Total orig, vol. físico
    "pib_variacion_anual":              "735904",  # Var. anual orig
    "pib_desest_trimestral":            "736181",  # Total desest, nivel
    "pib_precios_corrientes":           "735979",  # Corrientes trim
    "pib_precios_corrientes_valor":     "734407",  # Valores abs. corrientes
    "pib_anual_vol_2018":               "782389",  # Anual vol. 2018
    "pib_desest_eo":                    "736183",  # Estimación oportuna desest
    "pib_desest_trim":                  "736182",  # Desest. trim

    # --- Por sectores, variaciones desest. ---
    "pib_primarias_var_trim":           "736196",
    "pib_primarias_var_anual":          "736197",
    "pib_secundarias_var_trim":         "736203",
    "pib_secundarias_var_anual":        "736204",
    "pib_terciarias_var_trim":          "736238",
    "pib_terciarias_var_anual":         "736239",
    "pib_mineria_var_anual":            "736211",
    "pib_energia_var_anual":            "736218",
    "pib_construccion_var_anual":       "736225",
    "pib_manufacturas_var_anual":       "736232",
    "pib_comercio_mayoreo_var_anual":   "736246",
    "pib_comercio_menudeo_var_anual":   "736253",
    "pib_transportes_var_anual":        "736260",
    "pib_serv_financieros_var_anual":   "736274",
    "pib_serv_inmobiliarios_var_anual": "736281",
    "pib_serv_profesionales_var_anual": "736288",
    "pib_gobierno_var_anual":           "736344",

    # --- Componentes de demanda (desest.) ---
    "pib_consumo_privado_var_trim":     "737474",
    "pib_consumo_privado_var_anual":    "737475",
    "pib_consumo_gobierno_var_trim":    "737481",
    "pib_consumo_gobierno_var_anual":   "737482",
    "pib_fbcf_var_trim":                "737488",
    "pib_fbcf_var_anual":               "737489",
    "pib_fbcf_privada_var_anual":       "737503",
    "pib_fbcf_publica_var_anual":       "737496",
    "pib_exportaciones_var_trim":       "737516",
    "pib_exportaciones_var_anual":      "737517",
    "pib_importaciones_var_trim":       "737460",
    "pib_importaciones_var_anual":      "737461",

    # =========================================================================
    # PIB por entidad federativa (anual, base 2018)
    # Árbol BIE: 8061 > 610708. geo='00' = nacional; '01'-'32' = estado.
    # =========================================================================
    "pib_estatal_constante":            "746097",  # A precios constantes 2018
    "pib_estatal_corriente":            "750453",  # A precios corrientes
    "pib_estatal_ivf":                  "749001",  # IVF 2018=100
    "pib_estatal_participacion":        "747549",  # Participación porcentual

    # =========================================================================
    # INPC — Índice Nacional de Precios al Consumidor (mensual y quincenal)
    # Árbol BIE: 3623
    # =========================================================================

    # --- Generales ---
    "inpc_inflacion_mensual":           "910399",
    "inpc_inflacion_anual":             "910406",
    "inpc_inflacion_acumulada":         "910413",

    # --- Subyacente ---
    "inpc_inflacion_mensual_sub":       "910400",
    "inpc_inflacion_anual_sub":         "910407",
    "inpc_inflacion_acumul_sub":        "910414",
    "inpc_subyacente_mercancias_mens":  "910401",
    "inpc_subyacente_mercancias_anual": "910408",
    "inpc_subyacente_servicios_mens":   "910402",
    "inpc_subyacente_servicios_anual":  "910409",

    # --- No subyacente ---
    "inpc_no_subyacente_mensual":       "910403",
    "inpc_no_subyacente_anual":         "910410",
    "inpc_no_subyacente_agrop_mens":    "910404",
    "inpc_no_subyacente_agrop_anual":   "910411",
    "inpc_no_subyacente_energ_mens":    "910405",
    "inpc_no_subyacente_energ_anual":   "910412",

    # --- Quincenal ---
    "inpc_quincenal":                   "910427",
    "inpc_quincenal_sub":               "910428",
    "inpc_quincenal_interanual":        "910438",
    "inpc_quincenal_interanual_sub":    "910439",

    # =========================================================================
    # INPP — Índice Nacional de Precios al Productor (mensual)
    # Árbol BIE: 3623 > 3790
    # =========================================================================
    "inpp_indice_total":                "1700001",
    "inpp_indice_con_petroleo":         "1700002",
    "inpp_manufactureras":              "1700244",
    "inpp_variacion_sin_petroleo":      "1800001",  # Var. mensual sin petróleo
    "inpp_variacion_con_petroleo":      "1800002",  # Var. mensual con petróleo
    "inpp_variacion_sin_pet_anual":     "1801001",  # Var. anual sin petróleo
    "inpp_variacion_con_pet_anual":     "1801002",  # Var. anual con petróleo

    # =========================================================================
    # Actividad industrial (mensual, base 2018)
    # Árbol BIE: 606034
    # =========================================================================

    # --- Nivel/índice (series originales) ---
    "actind_total":                     "736407",
    "actind_variacion":                 "736526",
    "actind_desest":                    "736885",
    "manufactureras_variacion_anual":   "736537",

    # --- Variaciones desest. (ref. doc) ---
    "actind_var_mensual":               "736886",
    "actind_mineria_var":               "736893",
    "actind_energia_var":               "736921",
    "actind_construccion_var":          "736942",
    "actind_manufactureras_var":        "736970",
    "actind_alimentos_var_anual":       "736978",
    "actind_bebidas_var_anual":         "736985",
    "actind_textil_var_anual":          "737006",
    "actind_cuero_var_anual":           "737013",
    "actind_madera_var_anual":          "737020",
    "actind_papel_var_anual":           "737027",
    "actind_quimica_var_anual":         "737048",
    "actind_plastico_var_anual":        "737055",
    "actind_metales_var_anual":         "737069",
    "actind_metalicos_var_anual":       "737076",
    "actind_maquinaria_var_anual":      "737083",
    "actind_computacion_var_anual":     "737090",
    "actind_electrico_var_anual":       "737097",
    # actind_transporte_var_anual: ID pendiente de verificar (737104 es igae_actividades_secundarias)

    # =========================================================================
    # Sector externo — Balanza comercial (mensual, desest.)
    # Árbol BIE: 3655
    # =========================================================================

    # --- Saldos ---
    "balanza_comercial_saldo":          "897",     # Saldo total (serie orig)
    "balanza_comercial_desest":         "87537",   # Saldo total desest
    "balanza_saldo_petrolero":          "206780",
    "balanza_saldo_no_petrolero":       "206782",

    # --- Exportaciones ---
    "balanza_exportaciones_mensual":    "451979",  # Totales, var. mensual
    "balanza_exportaciones_anual":      "451980",  # Totales, var. anual
    "balanza_export_petroleras_mens":   "451983",
    "balanza_export_petroleras_anual":  "451984",
    "balanza_export_no_pet_mensual":    "451995",
    "balanza_export_no_pet_anual":      "451996",
    "balanza_export_agropecuarias":     "452000",
    "balanza_export_extractivas":       "452004",
    "balanza_export_manufacturas":      "452008",
    "balanza_export_automotriz_mens":   "452011",
    "balanza_export_automotriz_anual":  "452012",
    "balanza_export_resto_manuf":       "452016",

    # --- Importaciones ---
    "balanza_import_consumo_mensual":   "452031",
    "balanza_import_consumo_anual":     "452032",
    "balanza_import_intermedios_mens":  "452043",
    "balanza_import_intermedios_anual": "452044",
    "balanza_import_capital_mensual":   "452055",
    "balanza_import_capital_anual":     "452056",

    # =========================================================================
    # Exportaciones por entidad federativa
    # Árbol BIE: 36694 > 38035 (trim) / 38068 (anual)
    # IMPORTANTE: solo geo='01'-'32'. geo='00' devuelve HTTP 400.
    # =========================================================================
    "export_entidad_trimestral":        "629659",
    "export_entidad_anual":             "630459",

    # =========================================================================
    # Mercado laboral — ENOE mensual (tasas nacionales, desest.)
    # Árbol BIE: 2
    # =========================================================================
    "tasa_desocupacion":                "444883",  # Total
    "tasa_desocupacion_desest":         "444884",
    "tasa_desocupacion_hombres":        "444887",
    "tasa_desocupacion_mujeres":        "444890",
    "tasa_participacion":               "444875",
    "tasa_participacion_hombres":       "444878",
    "tasa_participacion_mujeres":       "444881",
    "tasa_subocupacion":                "444899",
    "tasa_informalidad":                "444893",
    "tasa_ocupacion":                   "454853",
    "tasa_ocupacion_parcial":           "444604",
    "tasa_participacion_urbana":        "444902",
    "tasa_desocupacion_urbana":         "444911",
    "tasa_subocupacion_urbana":         "668897",
    "tasa_informalidad_urbana":         "444920",

    # =========================================================================
    # ENOE trimestral — población 15 años y más (absolutos)
    # Árbol BIE: 123
    # =========================================================================
    "enoe_pob_total":                   "289242",
    "enoe_pea_total":                   "289244",
    "enoe_pea_ocupada":                 "289245",
    "enoe_pea_desocupada":              "289246",
    "enoe_pnea_total":                  "289247",
    "enoe_pnea_disponible":             "289248",
    "enoe_pnea_no_disponible":          "289249",
    "enoe_desocupada_total":            "289289",
    # Por sexo
    "enoe_pob_hombres":                 "289292",
    "enoe_pea_hombres":                 "289294",
    "enoe_pea_ocupada_hombres":         "289295",
    "enoe_pea_desocupada_hombres":      "289296",
    "enoe_pnea_hombres":                "289297",
    "enoe_pnea_disponible_hombres":     "289298",
    "enoe_pnea_no_disponible_hombres":  "289299",
    "enoe_pob_mujeres":                 "289342",
    "enoe_pea_mujeres":                 "289344",
    "enoe_pea_ocupada_mujeres":         "289345",
    "enoe_pea_desocupada_mujeres":      "289346",
    "enoe_pnea_mujeres":                "289347",
    "enoe_pnea_disponible_mujeres":     "289348",
    "enoe_pnea_no_disponible_mujeres":  "289349",

    # =========================================================================
    # Demanda interna — Consumo privado (mensual, desest.)
    # Árbol BIE: 605903
    # =========================================================================
    "consumo_privado_var_anual":        "740946",  # IMCPMI var. anual (orig)
    "consumo_privado_mensual":          "740988",  # Total, var. mensual desest
    "consumo_privado_var_anual_desest": "740989",  # Total, var. anual desest
    "consumo_privado_nacional_mens":    "740995",
    "consumo_privado_nacional_anual":   "740996",
    "consumo_privado_importado_mens":   "741016",
    "consumo_privado_importado_anual":  "741017",
    "consumo_privado_duraderos_nac":    "740949",
    "consumo_privado_semi_nac":         "740950",
    "consumo_privado_no_dur_nac":       "740951",
    "consumo_privado_servicios_nac":    "740952",
    "consumo_privado_duraderos_imp":    "740955",
    "consumo_privado_semi_imp":         "740956",
    "consumo_privado_no_dur_imp":       "740957",

    # =========================================================================
    # Ventas al menudeo (mensual)
    # =========================================================================
    "ventas_menudeo":                   "718506",
    "ventas_menudeo_var":               "718507",
    "ventas_menudeo_desest":            "718942",

    # =========================================================================
    # Confianza del consumidor (mensual, desest.)
    # Árbol BIE: 3552
    # =========================================================================
    "confianza_consumidor":             "454168",  # ICC nivel
    "confianza_consumidor_desest":      "454186",
    "icc_var_mensual":                  "454187",  # ICC var. mensual
    "icc_var_anual":                    "454188",
    "icc_hogar_actual_var":             "454195",
    "icc_hogar_futuro_var":             "454202",
    "icc_pais_actual_var":              "454209",
    "icc_pais_futuro_var":              "454216",
    "icc_compra_durables_var":          "454223",

    # =========================================================================
    # FBCF — Formación bruta de capital fijo (mensual, desest.)
    # Árbol BIE: 606972
    # =========================================================================
    "fbcf_total":                       "741020",  # Orig, nivel
    "fbcf_variacion":                   "741040",
    "fbcf_desest":                      "741100",
    "fbcf_total_mensual":               "741103",  # Desest, var. mensual
    "fbcf_total_var_anual":             "741104",
    "fbcf_maquinaria_mensual":          "741110",
    "fbcf_maquinaria_var_anual":        "741111",
    "fbcf_construccion_mensual":        "741159",
    "fbcf_construccion_var_anual":      "741160",
    "fbcf_construccion_residencial":    "741167",
    "fbcf_construccion_no_residencial": "741174",
    "fbcf_maquinaria_nacional":         "741118",
    "fbcf_maquinaria_importada":        "741139",

    # =========================================================================
    # Oferta y demanda global (trimestral)
    # =========================================================================
    "odgbs_total":                      "737371",
    "odgbs_variacion":                  "737374",
    "odgbs_desest":                     "737445",

    # =========================================================================
    # EMOE — Encuesta Mensual de Opinión Empresarial (mensual, base 2018)
    # Árbol BIE: 138032
    # =========================================================================

    # IAT — Indicador de Tendencia del Empleo (total manufacturero)
    "emoe_iat_manufacturero":           "701490",
    "emoe_iat_mensual":                 "910455",  # IAT global, var. mensual
    "emoe_iat_anual":                   "910456",
    "emoe_iat_construccion_var":        "701417",
    "emoe_iat_comercio_var":            "701860",

    # ICE — Indicador de Confianza Empresarial
    "emoe_ice_manufacturero":           "701570",
    "emoe_ice_mensual":                 "910462",
    "emoe_ice_anual":                   "910463",
    "emoe_ice_manufacturas_var":        "701740",
    "emoe_ice_construccion_var":        "701452",
    "emoe_ice_comercio_var":            "701902",
    "emoe_ice_servicios_var":           "702056",

    # IPM — Indicador de Pedidos Manufactureros
    "emoe_ipm_manufacturero":           "701618",
    "emoe_ipm_mensual":                 "701781",
    "emoe_ipm_anual":                   "701782",
    "emoe_ipm_pedidos_var":             "701789",
    "emoe_ipm_produccion_var":          "701796",
    "emoe_ipm_personal_var":            "701803",
    "emoe_ipm_entrega_var":             "701810",
    "emoe_ipm_inventarios_var":         "701817",

    # =========================================================================
    # EMIM — Encuesta Mensual Industria Manufacturera (mensual, base 2018)
    # Árbol BIE: 542904
    # =========================================================================
    "emim_personal_orig":               "702139",  # Personal ocupado, nivel
    "emim_ivf_desest":                  "910466",  # IVF producción, nivel
    "emim_ivf_variacion_desest":        "910467",  # Var. anual IVF
    "emim_volumen_var":                 "910469",  # Var. mensual vol. prod.
    "emim_personal_var":                "702336",  # Var. personal ocupado
    "emim_horas_trabajadas":            "702504",
    "emim_remuneraciones_reales":       "702672",

    # =========================================================================
    # ENEC — Encuesta Nacional de Empresas Constructoras (mensual, base 2018)
    # Árbol BIE: 568505
    # =========================================================================
    "enec_valor_prod_orig":             "720322",  # Valor producción, nivel
    "enec_valor_prod_desest":           "720346",
    "enec_valor_prod_var":              "720349",  # Var. mensual
    "enec_personal_ocupado":            "720398",
    "enec_remuneraciones":              "720440",
    "enec_horas_trabajadas":            "720461",
    "enec_edificacion_var":             "720357",
    "enec_agua_saneamiento_var":        "720364",
    "enec_electricidad_telecom_var":    "720371",
    "enec_transporte_var":              "720378",
    "enec_petroleo_var":                "720385",
    "enec_otras_construcciones_var":    "720392",

    # =========================================================================
    # EMS — Encuesta Mensual de Servicios (mensual, base 2018)
    # Árbol BIE: 564077
    # =========================================================================
    "ems_ingresos_orig":                "715722",  # Ingresos totales, nivel
    "ems_ingresos_desest":              "715854",
    "ems_ingresos_var":                 "715857",  # Var. mensual
    "ems_personal":                     "715927",
    "ems_remuneraciones":               "716004",
    "ems_gastos":                       "715997",
    "ems_transporte_var":               "715865",
    "ems_info_medios_var":              "715872",
    "ems_inmobiliarios_var":            "715879",
    "ems_profesionales_var":            "715886",
    "ems_apoyo_negocios_var":           "715893",
    "ems_educativos_var":               "715900",
    "ems_salud_var":                    "715907",
    "ems_esparcimiento_var":            "715914",
    "ems_alojamiento_var":              "715921",
    "ems_otros_servicios_var":          "720276",

    # =========================================================================
    # EMEC — Encuesta Mensual sobre Empresas Comerciales (mensual, base 2018)
    # Árbol BIE: 562654
    # =========================================================================

    # Mayoreo
    "emec_mayoreo_orig":                "718480",
    "emec_mayoreo_desest":              "718520",
    "emec_mayoreo_personal":            "718523",
    "emec_mayoreo_remuneracion":        "718530",
    "emec_mayoreo_ingresos":            "718537",
    "emec_mayoreo_mercancias":          "718922",
    "emec_mayoreo_farma_var":           "718797",
    "emec_mayoreo_intermediacion_var":  "718909",

    # Menudeo
    "emec_menudeo_personal":            "718929",
    "emec_menudeo_remuneracion":        "718936",
    "emec_menudeo_mercancias":          "719370",
    "emec_menudeo_vehiculos_var":       "719329",
    "emec_menudeo_textiles_var":        "719217",
    "emec_menudeo_papeleria_var":       "719252",
    "emec_menudeo_ferreteria_var":      "719322",
    "emec_menudeo_internet_var":        "719364",

    # =========================================================================
    # IMMEX (mensual)
    # =========================================================================
    "immex_personal_ocupado":           "203933",

    # =========================================================================
    # ITAEE — Indicador Trimestral Actividad Económica Estatal (trim., base 2018)
    # Árbol BIE: 603944
    # IMPORTANTE: solo geo='01'-'32'. geo='00' devuelve HTTP 400.
    # =========================================================================
    "itaee_indice":                     "741177",  # Índice total (nivel)
    "itaee_con_petroleo":               "741180",
    "itaee_sin_petroleo":               "741181",
    "itaee_indice_desest":              "741927",  # Índice desest (ref. doc)
    "itaee_var_anual":                  "741929",

    # =========================================================================
    # IMAI — Indicador Mensual Actividad Industrial Estatal (mensual, base 2018)
    # Árbol BIE: 607220
    # =========================================================================
    "imai_total_nacional":              "738182",
    "imai_manufacturera_total":         "736418",
    "imai_manufacturera_var":           "739277",  # Var. mensual desest

    # =========================================================================
    # Subsector automotriz (IVF mensual, base 2018)
    # Nota: 636031/635070 son producción en unidades (AMIA es fuente primaria)
    # =========================================================================
    "actind_automotriz_total":          "736511",
    "actind_automoviles_camiones":      "736512",
    # autos_ligeros/pesados en unidades (635031-635071) no disponibles vía
    # endpoint estándar BIE. Fuente primaria: parser AMIA (fuente externa).

    # =========================================================================
    # Minería y metalurgia (mensual)
    # =========================================================================
    "mineria_total":                    "656",
    "mineria_variacion":                "657",
    "mineria_desest":                   "661524",
    "cobre_produccion":                 "666",
    "oro_produccion":                   "659",
    "plata_produccion":                 "660",

    # =========================================================================
    # Indicadores cíclicos (mensual)
    # Árbol BIE: 630
    # =========================================================================
    "indicador_coincidente":            "214294",  # Diferencia vs mes anterior
    "indicador_adelantado":             "214308",

    # =========================================================================
    # Gobierno (anual)
    # =========================================================================
    "consumo_gobierno_total":           "728658",

    # =========================================================================
    # INDICADORES SOCIODEMOGRÁFICOS — fuente BISE
    # Usar fuente="BISE" al llamar get_indicator().
    # La mayoría son censales (cada 5-10 años); verificar TIME_PERIOD.
    # =========================================================================

    # --- Población ---
    "poblacion_total":                  "1002000001",

    # --- Educación (BISE, árbol 15) ---
    "bise_alfabetismo_15mas":           "1002000041",   # % alfabetas 15+
    "bise_tasa_alfab_15_24":            "1002000050",   # Tasa alfab. 15-24 años
    "bise_escolaridad_promedio":        "1005000038",   # Grado promedio escolar
    "bise_asistencia_primaria":         "6207019026",   # % 6-11 años en escuela
    "bise_asistencia_secundaria":       "6207019028",   # % 12-14 años en escuela
    "bise_asistencia_superior":         "6207019029",   # % 15-24 años en escuela
    "bise_pct_sin_instruccion":         "6200240447",   # % sin instrucción 15+
    "bise_pct_instruccion_superior":    "6200240365",   # % con instrucción superior
    "bise_pct_rezago_educativo":        "6200240391",   # % con rezago educativo
    "bise_matriculacion_primaria":      "6000000001",   # Tasa neta matric. primaria
    "bise_matriculacion_preescolar":    "6000000004",   # Tasa neta matric. preescolar

    # --- Salud y derechohabiencia (BISE, árbol 143) ---
    "bise_derechohabiente_total":       "1004000001",   # Pob. derechohabiente (abs)
    "bise_pct_afiliado_salud":          "6207019018",   # % afiliado a servicios de salud
    "bise_pct_imss":                    "6200240471",   # % derechohabiente IMSS
    "bise_pct_issste":                  "6200240421",   # % derechohabiente ISSSTE
    "bise_pct_no_afiliado":             "6207049072",   # % sin cobertura de salud

    # --- Vivienda y servicios (BISE, árbol 56) ---
    "bise_viviendas_habitadas":         "1003000011",   # Viviendas part. habitadas
    "bise_ocupantes_promedio":          "1003000015",   # Promedio ocupantes/vivienda
    "bise_viviendas_electricidad":      "1003000017",   # Viviendas con electricidad
    "bise_viviendas_agua_red":          "1003000018",   # Viviendas con agua de red
}


CATALOGOS_VALIDOS = {
    "CL_INDICATOR",
    "CL_UNIT",
    "CL_NOTE",
    "CL_SOURCE",
    "CL_TOPIC",
    "CL_FREQ",
    "CL_GEO_AREA",
    "CL_STATUS",
}

GEO = {
    "nacional": "00",
    "aguascalientes": "01",
    "baja_california": "02",
    "baja_california_sur": "03",
    "campeche": "04",
    "coahuila": "05",
    "colima": "06",
    "chiapas": "07",
    "chihuahua": "08",
    "cdmx": "09",
    "durango": "10",
    "guanajuato": "11",
    "guerrero": "12",
    "hidalgo": "13",
    "jalisco": "14",
    "edomex": "15",
    "michoacan": "16",
    "morelos": "17",
    "nayarit": "18",
    "nuevo_leon": "19",
    "oaxaca": "20",
    "puebla": "21",
    "queretaro": "22",
    "quintana_roo": "23",
    "san_luis_potosi": "24",
    "sinaloa": "25",
    "sonora": "26",
    "tabasco": "27",
    "tamaulipas": "28",
    "tlaxcala": "29",
    "veracruz": "30",
    "yucatan": "31",
    "zacatecas": "32",
}

# Indicadores state-only (geo='00' devuelve error)
GEO_SOLO_ESTATAL = {
    "741177", "741180", "741181",  # ITAEE
    "741927", "741929",             # ITAEE ref
    "629659", "630459",             # Exportaciones por entidad
}

# Indicadores que requieren fuente="BISE"
FUENTE_BISE = {k for k, v in INDICADORES_BIE.items() if k.startswith("bise_") or k == "poblacion_total"}


class INEGIBIEClient:
    """
    Cliente para la API del BIE/BISE del INEGI.
    token: UUID obtenido en https://www.inegi.org.mx/app/desarrolladores/generatoken/
    """

    def __init__(self, token: str, lang: str = "es", fuente: str = "BIE-BISE"):
        self.token = token
        self.lang = lang
        self.fuente = fuente

    def get_indicator(
        self,
        indicator_id: str,
        geo: str = "00",
        recent_only: bool = False,
        fuente: Optional[str] = None,
    ) -> dict:
        """
        Obtiene la serie de tiempo de un indicador.

        Args:
            indicator_id: Clave numérica del indicador.
            geo: '00' = nacional (default). '01'-'32' = entidad federativa.
                 ITAEE y exportaciones por entidad solo aceptan '01'-'32'.
            recent_only: True para solo el dato más reciente.
            fuente: Overrides la fuente del cliente. Usar 'BISE' para
                    indicadores sociodemográficos (bise_*).

        Returns:
            Dict con Header y Series (incluyendo OBSERVATIONS).
        """
        src = fuente or self.fuente
        recent_str = "true" if recent_only else "false"
        url = (
            f"{BASE_URL}/INDICATOR/{indicator_id}/{self.lang}/{geo}"
            f"/{recent_str}/{src}/2.0/{self.token}?type=json"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_catalog(
        self,
        catalog: str,
        catalog_id: Optional[str] = None,
    ) -> dict:
        if catalog not in CATALOGOS_VALIDOS:
            raise ValueError(
                f"Catálogo inválido: {catalog}. "
                f"Opciones: {', '.join(sorted(CATALOGOS_VALIDOS))}"
            )
        id_str = catalog_id if catalog_id else "null"
        url = (
            f"{BASE_URL}/{catalog}/{id_str}/{self.lang}"
            f"/{self.fuente}/2.0/{self.token}?type=json"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def parse_series(self, response: dict) -> list[dict]:
        """
        Extrae las observaciones de una respuesta del endpoint INDICATOR.

        Returns:
            Lista de dicts con keys: indicator_id, freq, unit, time_period,
            obs_value, geo, last_update. Orden cronológico ascendente.
        """
        rows = []
        for series in response.get("Series", []):
            indicator_id = series.get("INDICADOR")
            freq = series.get("FREQ")
            unit = series.get("UNIT")
            last_update = series.get("LASTUPDATE")
            for obs in series.get("OBSERVATIONS", []):
                rows.append({
                    "indicator_id": indicator_id,
                    "freq": freq,
                    "unit": unit,
                    "last_update": last_update,
                    "time_period": obs.get("TIME_PERIOD"),
                    "obs_value": obs.get("OBS_VALUE"),
                    "geo": obs.get("COBER_GEO"),
                })
        rows.reverse()
        return rows
