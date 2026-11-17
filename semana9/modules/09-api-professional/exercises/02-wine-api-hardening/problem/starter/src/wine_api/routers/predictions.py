from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.schemas import (
    VALID_FEATURES_EXAMPLE,
    ErrorResponse,
    Prediction,
    PredictionRequest,
    PredictionResponse,
)

# TODO S9.3a: mueve aquí `prefix="/v1/predictions"` y `tags=["predictions"]`.
# TODO S9.3c: declara a nivel de router `responses=` para 400, 422 y 503 con
# `{"model": ErrorResponse, "description": ...}`. Así el 422 deja de
# documentarse como `HTTPValidationError`, que ya no es lo que devolvemos.
router = APIRouter(
    prefix="/v1/predictions",
    tags=["predictions"],
    responses={
        400: {"model": ErrorResponse, "description": "El cuerpo no es JSON válido."},
        422: {
            "model": ErrorResponse,
            "description": "JSON válido que incumple el contrato de entrada; "
            "`error.fields` indica qué campos.",
        },
        503: {"model": ErrorResponse, "description": "El modelo no está disponible."},
    },
)

PREDICTION_EXAMPLES = {
    "valid": {
        "summary": "Vino válido",
        "description": "Las once variables dentro de rango.",
        "value": {"features": VALID_FEATURES_EXAMPLE},
    },
    "out_of_range": {
        "summary": "Alcohol fuera de rango (422)",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": 25.0}},
    },
    "wrong_type": {
        "summary": "Texto en un campo numérico (422)",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "ph": "ácido"}},
    },
}


@router.post(
    "",
    summary="Predecir la calidad de un vino tinto",
    response_description="Banda de calidad, confianza y versiones del modelo.",
)
def create_prediction(
    payload: Annotated[PredictionRequest, Body(openapi_examples=PREDICTION_EXAMPLES)],
    predictor: PredictorDep,
    request_id: RequestIdDep,
) -> PredictionResponse:
    """Clasifica un vino tinto en una banda de calidad.
    Envía las once variables fisicoquímicas en `features`; todos los rangos son
    inclusivos y no se admiten campos extra. La respuesta incluye
    `quality_band`, `confidence` redondeada a dos decimales, las versiones del
    modelo y del preprocesado y `served_at` en UTC (ISO 8601 con `Z`).
    """
    # TODO S9.3e: añade summary, response_description y un docstring útil para
    # quien consume la API (campos, rangos, decimales de confidence).
    # TODO S9.3f: ofrece en Swagger al menos tres ejemplos de cuerpo (uno válido
    # y dos inválidos). Investiga `Annotated[PredictionRequest, Body(...)]` con
    # `openapi_examples=`; usa VALID_FEATURES_EXAMPLE como base.
    output = predictor.predict(payload.features)
    # TODO S9.1e: este dict expone `raw_score` y la confianza sin redondear.
    # Declara `-> PredictionResponse` y construye el modelo; para pasar de la
    # dataclass ModelOutput a Prediction investiga `from_attributes=True`.
    return PredictionResponse(
        prediction=Prediction.model_validate(output),
        request_id=request_id,
        served_at=datetime.now(UTC),
    )
