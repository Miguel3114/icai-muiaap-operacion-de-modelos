"""TODOs de la vista UX: copy de salida y traducción de errores."""

from __future__ import annotations

from model_ui.contracts import PredictionPayload, PredictionView, UserFacingError
from model_ui.errors import (
    ArtifactUnavailableError,
    InferenceTimeoutError,
    InputContractError,
)
from model_ui.policies import (
    DEFAULT_CONFIDENCE_POLICY,
    DEFAULT_LATENCY_POLICY,
    ConfidencePolicy,
    LatencyPolicy,
    classify_confidence,
    classify_latency,
)

QUALITY_LABELS = {
    "needs_review": "Requiere revisión",
    "acceptable": "Resultado aceptable",
    "excellent": "Resultado excelente",
}

CONFIDENCE_COPY = {
    "low": (
        "Confianza baja",
        "El resultado es orientativo y requiere revisión; "
        "la confianza no es una garantía.",
    ),
    "medium": (
        "Confianza intermedia",
        "Usa el resultado como señal orientativa y revisa su contexto antes de actuar.",
    ),
    "high": (
        "Confianza alta",
        "La confianza es alta para este modelo, pero no garantiza "
        "que la decisión sea correcta.",
    ),
}

LATENCY_COPY = {
    "within_target": (
        "Dentro del objetivo",
        "La respuesta quedó dentro del objetivo de la demo.",
    ),
    "above_target": (
        "Por encima del objetivo",
        "La respuesta llegó, pero la latencia supera el objetivo técnico de la demo.",
    ),
}


def build_prediction_view(
    prediction: PredictionPayload,
    latency_ms: float,
    *,
    confidence_policy: ConfidencePolicy = DEFAULT_CONFIDENCE_POLICY,
    latency_policy: LatencyPolicy = DEFAULT_LATENCY_POLICY,
) -> PredictionView:
    """TODO: construye la vista con etiquetas, confianza, latencia y versiones."""

    confidence_level = classify_confidence(prediction.confidence, confidence_policy)

    latency_status = classify_latency(latency_ms, latency_policy)

    confidence_label, confidence_message = CONFIDENCE_COPY[confidence_level]
    latency_label, latency_message = LATENCY_COPY[latency_status]

    return PredictionView(
        quality_band=prediction.quality_band,
        quality_label=QUALITY_LABELS[prediction.quality_band],
        confidence=prediction.confidence,
        confidence_level=confidence_level,
        confidence_label=confidence_label,
        confidence_message=confidence_message,
        latency_ms=round(latency_ms, 3),
        latency_status=latency_status,
        latency_label=latency_label,
        latency_message=latency_message,
        model_version=prediction.model_version,
        preprocessing_version=prediction.preprocessing_version,
    )


def to_user_facing_error(error: Exception, request_id: str) -> UserFacingError:
    """TODO: asigna código estable, mensaje accionable y recuperación."""

    if isinstance(error, InputContractError):
        return UserFacingError(
            code="invalid_input",
            title="Entrada no válida",
            message="Los datos proporcionados no son válidos.",
            recovery="Revisa los valores e inténtalo de nuevo.",
            request_id=request_id,
        )

    if isinstance(error, ArtifactUnavailableError):
        return UserFacingError(
            code="artifact_unavailable",
            title="Modelo no disponible",
            message="El modelo no está disponible actualmente.",
            recovery="Comprueba la configuración del bundle y reintenta.",
            request_id=request_id,
        )

    if isinstance(error, InferenceTimeoutError):
        return UserFacingError(
            code="timeout",
            title="Tiempo de espera agotado",
            message="La inferencia superó el tiempo permitido.",
            recovery="Vuelve a intentarlo.",
            request_id=request_id,
        )

    return UserFacingError(
        code="prediction_error",
        title="Error de inferencia",
        message="No se pudo completar la predicción.",
        recovery="Vuelve a intentarlo o revisa el servicio.",
        request_id=request_id,
    )
