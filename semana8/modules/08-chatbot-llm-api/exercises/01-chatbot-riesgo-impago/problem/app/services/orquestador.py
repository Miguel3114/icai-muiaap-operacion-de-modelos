import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


# TODO: definir_tool() -> dict con la definicion de la tool, sacando "parameters" de PrestamoEntrada
def definir_tool():
    schema = PrestamoEntrada.model_json_schema()
    return {"type": "function",
            "function": {
                "name": NOMBRE_TOOL,
                "description": "Calcula la probabilidad de impago a partir de datos de entrada",
                "parameters": schema
                }
            }
            
# TODO: ejecutar_tool(nombre, argumentos_json) -> dict con "ok" True/False
#       (tool desconocida, JSON roto, datos invalidos o campos inventados -> ok False con el error)
def ejecutar_tool(nombre, argumentos_json):
    if nombre != NOMBRE_TOOL:
        return {"ok": False, "error": "La tool es desconocida"}

    try:
        entrada = PrestamoEntrada.model_validate_json(argumentos_json)
        prediccion = predecir(entrada)
    except Exception as error:
        return {"ok": False, "error": str(error)}

    return {"ok": True, **prediccion.model_dump()}


# TODO: responder(mensajes, llm) -> ChatSalida, con el bucle LLM -> tool -> LLM (maximo MAX_VUELTAS)
def responder(mensajes, llm):
    historial = [{"role": "system", "content": SISTEMA}]

    for mensaje in mensajes:
        if hasattr(mensaje, "model_dump"):
            historial.append(mensaje.model_dump())
        else:
            historial.append(mensaje)

    herramientas = [definir_tool()]
    herramienta_usada = None

    for _ in range(MAX_VUELTAS):
        respuesta = llm.completar(historial, herramientas)

        llamadas = respuesta.get("tool_calls")

        if not llamadas:
            return ChatSalida(
                respuesta=respuesta.get("content") or "",
                herramienta=herramienta_usada
            )

        historial.append(respuesta)

        for llamada in llamadas:
            nombre = llamada["function"]["name"]
            argumentos_json = llamada["function"]["arguments"]

            resultado = ejecutar_tool(nombre, argumentos_json)

            herramienta_usada = HerramientaUsada(
                nombre=nombre,
                argumentos=leer_argumentos(argumentos_json),
                resultado=resultado
            )

            historial.append({
                "role": "tool",
                "tool_call_id": llamada["id"],
                "content": json.dumps(resultado)
            })

    return ChatSalida(
        respuesta="No se ha podido completar la solicitud.",
        herramienta=herramienta_usada
    )
