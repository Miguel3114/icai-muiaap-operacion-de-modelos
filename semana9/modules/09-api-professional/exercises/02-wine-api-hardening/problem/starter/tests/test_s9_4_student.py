"""S9.4 — Tests que escribe el alumnado.

Cada test empezaba en rojo con `pytest.fail`; aquí cada `pytest.fail` se ha
sustituido por el test real. La entrega se considera completa cuando toda la
suite está en verde.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wine_api.dependencies import get_predictor
from wine_api.export_openapi import DEFAULT_PATH, render_openapi
from wine_api.predictor import UnavailablePredictor

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_prediction_returns_503_when_model_is_unavailable(
    client: TestClient, valid_payload: dict
) -> None:
    # TODO S9.4a: sin tocar el código de la API, haz que `get_predictor`
    # devuelva un UnavailablePredictor con `app.dependency_overrides` (llega
    # desde `client.app`). Comprueba status 503 y `error.code`. Limpia el
    # override al terminar para no contaminar otros tests.
    client.app.dependency_overrides[get_predictor] = UnavailablePredictor
    try:
        response = client.post("/v1/predictions", json=valid_payload)
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


# TODO S9.4b: convierte este test en `@pytest.mark.parametrize` con al
# menos cinco casos (justo por debajo y por encima de un rango, None, un
# texto...). Para cada uno comprueba 422 y que `fields` señala exactamente
# `features.<campo>`.
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("alcohol", 4.99),
        ("alcohol", 20.01),
        ("ph", 2.49),
        ("density", 1.02),
        ("chlorides", None),
        ("sulphates", "alto"),
        ("citric_acid", True),
    ],
)
def test_out_of_contract_values_are_rejected(
    client: TestClient, valid_payload: dict, field: str, value: object
) -> None:
    valid_payload["features"][field] = value

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 422
    fields = [f["field"] for f in response.json()["error"]["fields"]]
    assert fields == [f"features.{field}"]


# TODO S9.4c: los límites del contrato son inclusivos. Demuéstralo con los
# dos extremos de `alcohol` (5 y 20): ambos deben devolver 200.
@pytest.mark.parametrize("alcohol", [5.0, 20.0])
def test_range_limits_are_inclusive(
    client: TestClient, valid_payload: dict, alcohol: float
) -> None:
    valid_payload["features"]["alcohol"] = alcohol

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 200


def test_openapi_matches_versioned_contract() -> None:
    # TODO S9.4d: genera `contracts/openapi.json` con
    # `uv run python -m wine_api.export_openapi` y versiónalo en Git. Después
    # compara el JSON de `render_openapi()` con el archivo: si alguien cambia el
    # contrato sin querer, este test lo detecta en la revisión.
    versioned = (PROJECT_ROOT / DEFAULT_PATH).read_text(encoding="utf-8")

    assert render_openapi() == versioned
