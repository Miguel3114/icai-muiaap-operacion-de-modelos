# S10.7 — Informe de carga

> **TODO S10.7c:** ejecuta Locust con `--csv reports/s10`, versiona los CSV
> generados y completa las tablas y el análisis de este archivo.

Plantilla del informe. Rellénala con **tus** resultados: dependen de la máquina,
del número de workers y de la configuración de `.env`. No copies cifras de otra
persona ni de la solución, que no incluye resultados.

## Cómo se ha medido

| Dato | Valor |
| --- | --- |
| Comando de la API | `uv run fastapi dev` (1 proceso) |
| Comando de Locust | `uv run --group load locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10` |
| Cliente usado | front |
| `rate_limit_per_minute` del cliente | 60 |
| Máquina | Intel Core i7-11800H @ 2.30GHz (8 núcleos / 16 hilos), 16 GB RAM, Windows 11 |

Archivos generados por Locust y versionados junto a este informe:
`s10_stats.csv`, `s10_failures.csv` y `s10_stats_history.csv`.

## Resultados

Copia los valores de la fila `POST /v1/predictions` y de `Aggregated` de
`s10_stats.csv`.

| Endpoint | Peticiones | RPS | p50 (ms) | p95 (ms) | Fallos | % 429 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `POST /v1/predictions` | 750 | 12.61 | 8 | 19 | 696 | 92.8 % |
| `/v1/predictions [422]` | 88 | 1.48 | 9 | 16 | 82 | — |
| `GET /health` | 95 | 1.60 | 7 | 12 | 0 | — |
| Aggregated | 933 | 15.69 | 8 | 18 | 778 | 83.4 % |


`% 429` = fallos `429` de `s10_failures.csv` / peticiones de
`POST /v1/predictions` × 100.

## Análisis (5–10 líneas)

- ¿Cuántas predicciones por minuto deja pasar el límite y cuántas ha pedido
  Locust? ¿Cuadra el `% 429` con esa cuenta?
  
  Pasaron 54 válidas + 6 inválidas = 60, justo el límite. Locust pidió 838 predicciones en un minuto, así que el 92.8 % de 429 cuadra.

- ¿Qué latencia (p50, p95) tiene `GET /health`, que no pasa por autenticación ni
  rate limit, frente a `POST /v1/predictions`?

/health tiene p50 de 7 ms y p95 de 12 ms; las predicciones, 8 y 19 ms. La autenticación y el rate limit apenas añaden coste.

- ¿Qué cambiaría con dos workers (`fastapi run --workers 2`) y un contador en
  memoria por proceso?

Cada uno cuenta por su lado y la cuota real pasa a ser de unas 120 por minuto. La solución es Redis o un API gateway.
  
- Si quisieras medir la capacidad del servicio y no la política de cuotas, ¿qué
  cliente y qué límite usarías?

Un cliente con rate_limit_per_minute enorme, para que los 429 no tapen la latencia real del modelo.