from fastapi import APIRouter, Depends  # noqa: F401 - pista para S10.3d

from wine_api.dependencies import RequestIdDep, SettingsDep  # noqa: F401
from wine_api.rate_limit import RateLimiterDep  # noqa: F401 - pista para S10.3d
from wine_api.schemas import ClientUsage, UsageResponse  # noqa: F401
from wine_api.security import AUTH_RESPONSES, require_scope

# TODO S10.3d: protege este router con el scope `admin` (a nivel de
# `APIRouter`, como en predicciones) y crea `GET /v1/admin/usage`:
# - devuelve `UsageResponse` (tipo de retorno, no `dict`) con un `ClientUsage`
#   por cliente configurado, ordenados por nombre: nombre, peticiones en la
#   ventana actual (`limiter.usage(...)`) y límite por minuto;
# - nunca incluyas la clave: ¿qué campo de `ClientConfig` NO debe salir?
# - añade `summary`, `response_description` y un docstring para /docs (los
#   tests de S9.3 lo exigen a toda operación).
# Comprobación: uv run pytest -q tests/test_s10_3_authorization.py
# TODO S10.6a: documenta también aquí los 401 y 403 con `ErrorResponse`.
router = APIRouter(
    prefix="/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_scope("admin"))],
    responses=AUTH_RESPONSES,
)


@router.get(
    "/usage",
    summary="Consultar el consumo de cada cliente",
    response_description="Peticiones de cada cliente en la ventana actual.",
)
def read_usage(
    settings: SettingsDep, limiter: RateLimiterDep, request_id: RequestIdDep
) -> UsageResponse:
    """Devuelve, por cliente, cuántas predicciones lleva en la ventana actual.

    - Requiere la cabecera `X-API-Key` de un cliente con scope `admin`.
    - Identifica a los clientes por su nombre; las claves nunca se devuelven.
    - El contador es del proceso que responde: con varias réplicas, cada una
      informa de lo suyo.
    """

    clients = [
        ClientUsage(
            client=name,
            requests_in_window=limiter.usage(name),
            limit=config.rate_limit_per_minute,
        )
        for name, config in sorted(settings.clients.items())
    ]
    return UsageResponse(clients=clients, request_id=request_id)
