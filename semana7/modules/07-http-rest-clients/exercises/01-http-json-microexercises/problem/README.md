# Microejercicios — HTTP, JSON y diseño de recursos

Trabajad por parejas. No hace falta levantar ningún servicio. En el ejercicio 3
sí haréis una comprobación breve con `json.loads()` o un validador local.
Conservad las decisiones: se reutilizarán en el laboratorio de clientes.

## 1. Tres formas de pedir una predicción

Comparad estos tres casos:

A. `infer_measurements(payload)` dentro del mismo programa Python.
B. Un cliente envía `POST /runPumpModel` a otro proceso mediante HTTP.
C. Un cliente envía `POST /v1/predictions` a otro proceso mediante HTTP.

Completad la tabla:

Un proceso es un programa en ejecución. En A todo ocurre en el mismo proceso;
en B y C, el cliente se comunica con el proceso servidor.

| Caso | ¿Sale del proceso Python? | ¿Usa HTTP? | ¿La ruta nombra una acción o un recurso? |
| --- | --- | --- | --- |
| A | No | No | No hay ruta |
| B | Si | Si | La acción runPumpModel |
| C | Si | Si | El recurso predictions |



## 2. URL, path y query

```text
http://127.0.0.1:8000/v1/predictions/pred-42?include=explanation&limit=1
```

**TODO:** marcad scheme, host, port, path y cada parámetro de query. Después
decidid dónde pondríais:

scheme: http

host: 127.0.0.1

port: 8000

path: /v1/predictions/pred-42

query: include=explanation y limit=1

- el identificador de una predicción concreta: path
- un límite de resultados: query
- cuatro medidas de una bomba: body JSON

**Comprobación:** las medidas estructuradas no deberían acabar en la URL.

## 3. JSON y Python

```python
{"machine_id": "pump-017", "ready": True, "comment": None, "axes": (1, 2)}
```

**TODO:** convertid esta expresión Python a JSON interoperable. Investigad las
formas JSON de booleano, nulo y colección. Comprobad el resultado con un
validador local o `json.loads()`.

```JSON
{"machine_id": "pump-017", "ready": true, "comment": null, "axes": [1, 2]}
```

## 4. Cuatro estados HTTP esenciales

Para cada caso, elegid solo entre `200`, `400`, `422` y `503`. Escribid el
código y una razón de una frase.

1. Predicción correcta y devuelta: código 200; razón: la predicción se ha realizado correctamente y se ha devuelto un resultado.
2. Texto truncado o que no es JSON: código 400; razón: no se puede interpretar el texto.
3. JSON válido, pero `vibration_mm_s` es la cadena `"alta"`: código 422;
   razón: el JSON se entiende pero un feature no cunmple el contrato.
4. Petición correcta, pero el modelo no está disponible temporalmente: código
   503; razón: la solicitud esválida pero el modelo no está disponible.

## 5. Crear y consultar una predicción

Completad estas plantillas:

```text
Crear una predicción:    POST /v1/predictions
Consultar la predicción: GET /v1/predictions/pred-42
```

¿Dónde van las mediciones: en el path, en la query o en el body JSON? ¿Dónde va
`pred-42`? ¿Qué podría pasar si se repite dos veces la creación? ¿Consultar dos
veces debería cambiar el estado del servidor?

Las mediciones van en el body JSON del POST y pred-42 va en el path del GET. El POST no es seguro porque solicita una creación. El POST no es idempotente por defecto porque repetirlo puede crear otra predicción. El GET es seguro porque solo lee. El GET es idempotente porque repetirlo conserva el mismo efecto esperado.

- **segura:** está pensada solo para leer, sin cambiar el estado del servidor;
- **idempotente:** repetirla tiene el mismo efecto esperado que ejecutarla una
  sola vez.

Aplicad ambos términos a crear y consultar una predicción.
