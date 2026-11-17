# Ejercicio 01 — Microejercicios de la clase 1

Cuatro microejercicios de 5 minutos, uno al final de cada bloque de teoría. Se
hacen sobre las demos de [`examples/`](../../../examples/README.md) y no
requieren escribir una API nueva.

Prepara el entorno una vez, desde `semana9/modules/09-api-professional`:

```bash
uv sync --locked
```

## M1 — Serialización (bloque 1)

Arranca `uv run fastapi dev examples/serialization_demo.py` y compara
`/v1/scores/leaky` con `/v1/scores/public`.

1. Anota qué campos aparecen en la primera respuesta y no en la segunda.
leaky: {"band":"acceptable","confidence":0.8312377,"raw_score":6.137,"threshold_config":"/srv/models/thresholds.yaml"}
public: {"band":"acceptable","confidence":0.83,"served_at":"2026-11-17T10:56:59.095867Z","note":null,"is_reliable":true}
Los campos que aparecen en leaky pero no en public son: raw_score y threshold_config.

2. Explica en una frase por qué `/v1/scores/filtered` tampoco los devuelve,
   aunque la función devuelve un `dict` con todos ellos.
La función devuelve un dict con todo, pero el decorador declara response_model=PublicScore. Con eso, FastAPI valida lo que devuelve la función contra PublicScore y serializa solo los campos que el modelo declara. Todo lo demás lo descarta.

3. En `/docs`, abre el esquema `PublicScore`: ¿aparece `is_reliable`?
Si aparece.

**Comprobación:** tu respuesta a la pregunta 2 menciona `response_model` y
qué hace con los campos que no declara.

## M2 — Errores (bloque 2)

Arranca `uv run fastapi dev examples/errors_demo.py` y envía, desde `/docs` o
con `curl`, tres peticiones a `POST /v1/scores`:

- `{"age": 30, "income": 1000}`
- `{"age": "treinta", "income": 1000}`
- `{"age": 30}`

Después llama a `GET /v1/nada` y a `GET /v1/boom`.

1. Rellena una tabla con status, `error.code` y `error.fields` de cada caso.

| # | Petición | Status | `error.code` | `error.fields` |
|---|---|---|---|---|
| 1 | `POST /v1/scores` `{"age": 30, "income": 1000}` | 200 OK | - | - |
| 2 | `POST /v1/scores` `{"age": "treinta", "income": 1000}` | 422 Unprocessable Entity | validation_error| "field": "age", "message": "Input should be a valid integer, unable to parse string as an integer" |
| 3 | `POST /v1/scores` `{"age": 30}` | 422 Unprocessable Entity | validation_error | "field": "income", "message": "Field required" |
| 4 | `GET /v1/nada` | 404 | not_found | - |
| 5 | `GET /v1/boom` | 500 Internal Server Error | internal_error | - |

2. ¿Qué devolvería FastAPI en el segundo caso si borraras `handle_validation`?
   Pruébalo comentando el decorador y restáuralo después.

Sin handle_validation, FastAPI usa su handler por defecto para RequestValidationError. La respuesta sigue siendo un 422, pero cambia el formato del cuerpo:
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": [
        "body",
        "age"
      ],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "treinta"
    }
  ]
}
```

Ya no existe la clave error en la raíz, ni code, ni fields. Se rompe el contrato de errores: un cliente que espera error.code falla, y los errores de validación tienen una forma distinta del resto (404, 500, 503). Además, devuelve el input del usuario y el loc interno ("body"), que el handler propio limpiaba.

**Comprobación:** las cinco respuestas de error tienen la clave `error` en la
raíz y ninguna contiene el texto `TU_SECRETO`.

## M3 — OpenAPI (bloque 3)

Arranca `uv run fastapi dev examples/openapi_demo.py`.

1. Localiza en `/openapi.json` dónde terminan `summary`, el docstring y
   `responses` de `create_score`.

- `summary` → `paths./v1/scores.post.summary`: "Calcular el score de riesgo".
- Docstring → `paths./v1/scores.post.description`: "Calcula la probabilidad de impago de un cliente. ...".
- `responses` → `paths./v1/scores.post.responses`:
  - `200`: "Score y versión del modelo." (viene de `response_description`), esquema `ScoringResponse`.
  - `422`: "Entrada fuera de contrato.", esquema `ErrorResponse`.
  - `503`: "Modelo no disponible.", esquema `ErrorResponse`.

Los `responses` 422 y 503 se declaran en el `APIRouter`, pero aparecen dentro de cada operación del router.

2. Ejecuta el ejemplo `minor` desde Swagger con «Try it out».
```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": [
        "body",
        "age"
      ],
      "msg": "Input should be greater than or equal to 18",
      "input": 16,
      "ctx": {
        "ge": 18
      }
    }
  ]
}
```

Devuelve 422, pero con el formato por defecto de FastAPI (`detail`) y no con `ErrorResponse`, que es lo que promete la documentación. Esta demo no tiene handlers propios, así que la documentación no coincide con la respuesta real.

3. Añade un tercer ejemplo `no_income` sin el campo `income` y comprueba que
   aparece en el desplegable.

Añadí a `openapi_examples` de `create_score`:

```python
"no_income": {
    "summary": "Sin ingresos: 422",
    "value": {"age": 42},
},
```

Apareció como tercera opción del desplegable *Examples* en `/docs`. Al ejecutarlo devuelve 422:
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "income"
      ],
      "msg": "Field required",
      "input": {
        "age": 42
      }
    }
  ]
}
```

Con el cambio, `test_openapi_documents_errors_and_examples` falla porque espera solo `{"valid", "minor"}`. Deshice el cambio y `uv run pytest -q` vuelve a estar en verde.

**Comprobación:** `uv run pytest -q` sigue en verde y el desplegable muestra
tres ejemplos. Deshaz el cambio al terminar o adapta el test que cuenta los
ejemplos.   

## M4 — Tests (bloque 4)

Abre [`tests/test_examples.py`](../../../tests/test_examples.py).

1. Ejecuta `uv run pytest -q` y localiza el test que usa `dependency_overrides`.

El test que usa `dependency_overrides` es
   `test_dependency_override_simulates_unavailable_model`. Sustituye la
   dependencia `get_model` por un `Model` con `ready = False`, lo que simula
   un modelo no disponible sin tocar el código de la API. Comprueba que la
   respuesta es `503` con `error.code == "model_unavailable"`. El fixture
   `errors_client` limpia los overrides al terminar para no afectar a otros
   tests.

2. Elimina temporalmente `raise_server_exceptions=False` del fixture
   `errors_client` y vuelve a ejecutar. Explica qué cambia.
Sin `raise_server_exceptions=False` falla `test_unexpected_error_hides_secrets`
   con `RuntimeError: password=TU_SECRETO in /etc/app.conf`. El handler
   genérico sí genera el `500`, pero Starlette vuelve a lanzar la excepción
   para que el servidor la registre. Por defecto, `TestClient` la propaga
   al test, así que el test nunca recibe la respuesta. Con
   `raise_server_exceptions=False`, el test ve lo mismo que un cliente real:
   un `500` con `internal_error` y sin el secreto, que solo queda en la traza
   del servidor.

3. Escribe un test nuevo que compruebe que `income: 0` devuelve `422` con
   `fields[0].field == "income"`.
He añadido `test_zero_income_is_rejected` en `tests/test_examples.py`.
   Envía `{"age": 30, "income": 0}` y comprueba que devuelve `422` con
   `error.fields[0].field == "income"`, porque `income` tiene `Field(gt=0)`.
   `uv run pytest -q` → 10 passed.

**Comprobación:** la suite vuelve a estar en verde con tu test incluido.

La [solución comentada](../solution/README.md) se comparte al final de la clase.
