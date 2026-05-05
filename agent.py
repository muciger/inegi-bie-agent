"""
Agente INEGI BIE con Claude tool use
Permite consultar indicadores económicos y demográficos del BIE del INEGI
en lenguaje natural, usando el SDK de Anthropic.

Uso:
    export ANTHROPIC_API_KEY="sk-..."
    export INEGI_TOKEN="tu-uuid-de-inegi"
    python agent.py
"""

import json
import os
import anthropic
from inegi_bie_client import INEGIBIEClient, INDICADORES_BIE


# ---------------------------------------------------------------------------
# Definición de tools para Claude
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_indicator",
        "description": (
            "Obtiene la serie de tiempo de un indicador del BIE/BISE del INEGI. "
            "Cubre 330+ series económicas y ~20 socioeconómicas. "
            "Retorna valores históricos o el dato más reciente, filtrado por "
            "área geográfica. Usa search_indicators para encontrar el ID correcto."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "indicator_id": {
                    "type": "string",
                    "description": (
                        "Clave numérica del indicador. IDs principales:\n"
                        "--- IGAE mensual ---\n"
                        "Total orig: '737121' | Desest var mensual: '737220' | Desest var anual: '737221'\n"
                        "Secundarias var: '737234'/'737235' | Terciarias: '737269'/'737270'\n"
                        "Manufacturas var anual: '737263' | Construcción: '737256'\n"
                        "--- PIB trimestral ---\n"
                        "Total desest nivel: '736181' | Total var trim: '736182' | Var anual desest: '736183'\n"
                        "Manufacturas var anual: '736232' | Construcción: '736225'\n"
                        "Consumo privado var trim/anual: '737474'/'737475' | FBCF: '737488'/'737489'\n"
                        "Exportaciones var trim/anual: '737516'/'737517' | Importaciones: '737460'/'737461'\n"
                        "--- PIB por entidad (anual, geo 00 o 01-32) ---\n"
                        "Constantes 2018: '746097' | Corrientes: '750453' | Participación: '747549'\n"
                        "--- Inflación INPC mensual ---\n"
                        "Anual: '910406' | Mensual: '910399' | Subyacente anual: '910407'\n"
                        "No subyacente anual: '910410' | Energéticos anual: '910412'\n"
                        "INPP sin petróleo var mensual: '1800001' | Anual: '1801001'\n"
                        "--- Actividad industrial mensual ---\n"
                        "Total desest nivel: '736885' | Var mensual: '736886'\n"
                        "Manufacturas var: '736970' | Construcción: '736942'\n"
                        "--- Balanza comercial (desest) ---\n"
                        "Saldo: '87537' | Export totales var mensual: '451979'\n"
                        "Export automotriz: '452011'/'452012' | Export manufacturas anual: '452008'\n"
                        "Import intermedios: '452043'/'452044' | Import capital: '452055'/'452056'\n"
                        "Export por entidad (state-only geo 01-32): '629659' trim / '630459' anual\n"
                        "--- Mercado laboral ENOE mensual ---\n"
                        "Desocupación: '444883'/'444884' | Informalidad: '444893' | Subocupación: '444899'\n"
                        "Participación: '444875' | Informalidad urbana: '444920'\n"
                        "--- ENOE trimestral (personas) ---\n"
                        "PEA total/ocupada/desocupada: '289244','289245','289246'\n"
                        "PNEA total: '289247' | PEA hombres/mujeres: '289294'/'289344'\n"
                        "--- Demanda interna ---\n"
                        "Consumo privado var anual desest: '740989' | Ventas menudeo: '718506'\n"
                        "ICC nivel: '454168' | ICC var mensual: '454187'\n"
                        "FBCF total mensual: '741103' | Maquinaria mensual: '741110'\n"
                        "--- Encuestas sectoriales (mensual) ---\n"
                        "EMOE IAT: '910455'/'910456' | EMOE ICE: '910462'/'910463' | IPM: '701781'/'701782'\n"
                        "EMIM vol prod var: '910469' | Remuneraciones reales: '702672'\n"
                        "ENEC valor prod var: '720349' | EMS ingresos var: '715857'\n"
                        "EMEC mayoreo ingresos: '718537' | Menudeo remuneración: '718936'\n"
                        "--- Regional ---\n"
                        "ITAEE desest (state-only geo 01-32): '741927'/'741929'\n"
                        "IMAI manufacturera var: '739277'\n"
                        "--- Socioeconómicos BISE (usar fuente='BISE') ---\n"
                        "Alfabetismo 15+: '1002000041' | Escolaridad promedio: '1005000038'\n"
                        "% afiliado salud: '6207019018' | % sin cobertura: '6207049072'\n"
                        "Ocupantes por vivienda: '1003000015' | Viviendas con agua: '1003000018'\n"
                        "Usa search_indicators para encontrar cualquier otro ID."
                    ),
                },
                "geo": {
                    "type": "string",
                    "description": (
                        "Clave geográfica. '00' = nacional (default). "
                        "'01'-'32' = entidades federativas (01=Aguascalientes, "
                        "09=CDMX, 14=Jalisco, 15=Edomex, 19=Nuevo León, etc.). "
                        "ITAEE (741927, 741929) y exportaciones por entidad "
                        "(629659, 630459) solo aceptan '01'-'32'."
                    ),
                    "default": "00",
                },
                "recent_only": {
                    "type": "boolean",
                    "description": (
                        "True para solo el dato más reciente. "
                        "False (default) para la serie histórica completa."
                    ),
                    "default": False,
                },
                "fuente": {
                    "type": "string",
                    "enum": ["BIE-BISE", "BISE"],
                    "description": (
                        "Fuente de datos. 'BIE-BISE' (default) para indicadores "
                        "económicos. 'BISE' para indicadores socioeconómicos "
                        "(claves bise_*, población, educación, salud, vivienda)."
                    ),
                    "default": "BIE-BISE",
                },
            },
            "required": ["indicator_id"],
        },
    },
    {
        "name": "search_indicators",
        "description": (
            "Busca indicadores del BIE/BISE del INEGI por nombre o tema. "
            "Catálogo curado de 330+ series: IGAE, PIB (nacional y estatal), "
            "INPC, INPP, actividad industrial por subsector, balanza comercial "
            "desagregada (exportaciones/importaciones por tipo), exportaciones "
            "por entidad, mercado laboral (ENOE mensual y trimestral: "
            "desocupación, informalidad, subocupación, PEA por sexo), consumo "
            "privado por tipo de bien y origen, FBCF, confianza consumidor, "
            "EMOE/EMIM/ENEC/EMS/EMEC completos, ITAEE, IMAI, automotriz, "
            "minería, y socioeconómicos BISE (educación, salud, vivienda)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Término de búsqueda. Ejemplos: 'informalidad', "
                        "'exportaciones automotriz', 'consumo privado', "
                        "'PIB secundarias', 'balanza import capital', "
                        "'EMIM remuneraciones', 'alfabetismo', 'vivienda agua', "
                        "'ITAEE', 'derechohabiencia', 'bise'."
                    ),
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_catalog",
        "description": (
            "Consulta los catálogos de metadatos del BIE del INEGI. "
            "Útil para descubrir qué indicadores existen (CL_INDICATOR), "
            "sus unidades de medida (CL_UNIT), frecuencias (CL_FREQ), "
            "áreas geográficas disponibles (CL_GEO_AREA), "
            "fuentes (CL_SOURCE), temas (CL_TOPIC), "
            "notas metodológicas (CL_NOTE) y estatus (CL_STATUS)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "catalog": {
                    "type": "string",
                    "enum": [
                        "CL_INDICATOR",
                        "CL_UNIT",
                        "CL_NOTE",
                        "CL_SOURCE",
                        "CL_TOPIC",
                        "CL_FREQ",
                        "CL_GEO_AREA",
                        "CL_STATUS",
                    ],
                    "description": "Tipo de catálogo a consultar.",
                },
                "catalog_id": {
                    "type": "string",
                    "description": (
                        "ID del registro. Puede ser un número, una lista "
                        "separada por comas (ej. '2,3,343'), o dejar vacío "
                        "para obtener todos los registros del catálogo."
                    ),
                },
            },
            "required": ["catalog"],
        },
    },
]


# ---------------------------------------------------------------------------
# Ejecución de tools
# ---------------------------------------------------------------------------

def execute_tool(tool_name: str, tool_input: dict, client: INEGIBIEClient) -> str:
    """Despacha la llamada de herramienta y retorna el resultado como string JSON."""
    try:
        if tool_name == "search_indicators":
            query = tool_input.get("query", "").lower()
            # Buscar en el mapeo curado INDICADORES_BIE
            matches = []
            seen_ids = set()
            for key, indicator_id in INDICADORES_BIE.items():
                if query in key.lower() or query in indicator_id:
                    if indicator_id not in seen_ids:
                        seen_ids.add(indicator_id)
                        matches.append({
                            "key": key,
                            "indicator_id": indicator_id,
                        })
            return json.dumps({
                "query": query,
                "matches": matches,
                "total": len(matches),
                "hint": (
                    "Usa el indicator_id con get_indicator para obtener los datos. "
                    "Las claves con '_desest' son series desestacionalizadas, "
                    "con '_variacion' son variaciones porcentuales. "
                    "ITAEE (itaee_*) y exportaciones por entidad (export_entidad_*) "
                    "requieren geo='01'-'32', no funcionan con geo='00'."
                ),
            }, ensure_ascii=False)

        elif tool_name == "get_indicator":
            raw = client.get_indicator(
                indicator_id=tool_input["indicator_id"],
                geo=tool_input.get("geo", "00"),
                recent_only=tool_input.get("recent_only", False),
                fuente=tool_input.get("fuente"),
            )
            # Parsear a formato limpio para no saturar el contexto
            rows = client.parse_series(raw)
            # Limitar a 50 observaciones si la serie es muy larga
            if len(rows) > 50:
                rows = rows[-50:]  # las más recientes
                truncated = True
            else:
                truncated = False
            result = {
                "observations": rows,
                "count": len(rows),
                "truncated_to_last_50": truncated,
            }
            return json.dumps(result, ensure_ascii=False)

        elif tool_name == "get_catalog":
            raw = client.get_catalog(
                catalog=tool_input["catalog"],
                catalog_id=tool_input.get("catalog_id"),
            )
            # Limitar a 100 entradas para no saturar el contexto
            codes = raw.get("CODE", [])
            truncated = len(codes) > 100
            result = {
                "codes": codes[:100],
                "total_returned": len(codes[:100]),
                "truncated": truncated,
            }
            return json.dumps(result, ensure_ascii=False)

        else:
            return json.dumps({"error": f"Tool desconocida: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------

def run_agent(user_message: str, inegi_client: INEGIBIEClient, verbose: bool = True):
    """
    Ejecuta el agente con un mensaje del usuario.
    Maneja el loop de tool use hasta obtener la respuesta final.
    """
    anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [{"role": "user", "content": user_message}]

    system_prompt = (
        "Eres un analista de datos especializado en estadísticas de México. "
        "Tienes acceso a la API del BIE y BISE del INEGI con un catálogo de "
        "330+ series económicas y 20+ socioeconómicas. "
        "Cuando el usuario pregunte sobre indicadores económicos, laborales, "
        "sociales o demográficos de México, usa las tools para obtener datos reales. "
        "Presenta resultados con período, valor y unidad de medida. "
        "Para tendencias usa series desest. (_var_mensual, _var_anual). "
        "Para niveles usa series originales o de índice. "
        "ITAEE (741927/741929) y exportaciones por entidad (629659/630459) "
        "requieren geo='01'-'32', no '00'. "
        "Para indicadores BISE (educación, salud, vivienda: claves bise_*), "
        "pasa fuente='BISE'. Estos son censales: frecuencia anual o quinquenal. "
        "Responde siempre en español."
    )

    if verbose:
        print(f"\nUsuario: {user_message}\n")

    while True:
        response = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Agregar respuesta del asistente al historial
        messages.append({"role": "assistant", "content": response.content})

        # Si Claude terminó (no hay más tool calls), retornar respuesta
        if response.stop_reason == "end_turn":
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "",
            )
            if verbose:
                print(f"Agente: {final_text}")
            return final_text

        # Procesar tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if verbose:
                    print(f"  [tool] {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                result = execute_tool(block.name, block.input, inegi_client)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        # Agregar resultados de tools al historial
        if tool_results:
            messages.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# CLI interactivo
# ---------------------------------------------------------------------------

def main():
    token = os.environ.get("INEGI_TOKEN")
    if not token:
        raise ValueError(
            "Define la variable de entorno INEGI_TOKEN con tu UUID del INEGI."
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ValueError(
            "Define la variable de entorno ANTHROPIC_API_KEY."
        )

    inegi = INEGIBIEClient(token=token)

    print("Agente INEGI BIE activo. Escribe 'salir' para terminar.\n")
    while True:
        user_input = input("Tú: ").strip()
        if user_input.lower() in ("salir", "exit", "quit"):
            break
        if not user_input:
            continue
        run_agent(user_input, inegi)
        print()


if __name__ == "__main__":
    main()
