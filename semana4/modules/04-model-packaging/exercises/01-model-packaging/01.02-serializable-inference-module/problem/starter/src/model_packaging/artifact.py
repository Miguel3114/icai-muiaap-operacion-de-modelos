"""Puntos de extensión del taller de serialización."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

import joblib
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from model_packaging.contracts import (
    QualityBand,
    WineQualityPrediction,
    WineQualityRequest,
)
from model_packaging.preprocess import (
    FEATURE_NAMES,
    PREPROCESSING_VERSION,
    preprocess_wine_request,
)

ARTIFACT_SCHEMA_VERSION = "wine-quality-bundle-v1"
DEFAULT_BUNDLE_PATH = Path("models/wine_quality_bundle")
MANIFEST_FILENAME = "manifest.json"
MODEL_FILENAME = "model.joblib"
OUTPUT_LABELS: tuple[QualityBand, ...] = (
    "needs_review",
    "acceptable",
    "excellent",
)


class WineQualityEstimator(Protocol):
    """Interfaz mínima que debe cumplir el estimador cargado."""

    def predict(self, features: list[list[float]]) -> Sequence[str]:
        """Devuelve una etiqueta por fila."""

    def predict_proba(self, features: list[list[float]]) -> Sequence[Sequence[float]]:
        """Devuelve probabilidades por fila."""


class ArtifactManifest(BaseModel):
    """TODO: declara y valida los metadatos del bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    model_version: str = Field(min_length=1)
    preprocessing_version: str
    feature_names: tuple[str, ...]
    output_labels: tuple[QualityBand, ...]
    estimator_type: str = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value):
        if value != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version debe ser {ARTIFACT_SCHEMA_VERSION},"
                f"pero se recibió {value}"
            )
        return value

    @field_validator("preprocessing_version")
    @classmethod
    def validate_preprocessing_version(cls, value):
        if value != PREPROCESSING_VERSION:
            raise ValueError(
                f"preprocessing_version debe ser {PREPROCESSING_VERSION},"
                f"pero se recibió {value}"
            )
        return value

    @field_validator("feature_names")
    @classmethod
    def validate_feature_names(cls, value):
        if tuple(value) != FEATURE_NAMES:
            raise ValueError(
                f"feature_names debe ser {FEATURE_NAMES}, pero se recibió {value}"
            )
        return value

    @field_validator("output_labels")
    @classmethod
    def validate_output_labels(cls, value):
        if tuple(value) != OUTPUT_LABELS:
            raise ValueError(
                f"output_labels debe ser {OUTPUT_LABELS}, pero se recibió {value}"
            )
        return value

    @field_validator("model_version")
    @classmethod
    def validate_model_version(cls, value):
        if not value.strip():
            raise ValueError("model_version no puede estar vacío.")
        return value


@dataclass(frozen=True)
class LoadedModelBundle:
    """Bundle cargado; no modificar esta interfaz pública."""

    estimator: WineQualityEstimator
    manifest: ArtifactManifest


def _require_estimator(estimator):

    if not callable(getattr(estimator, "predict", None)):
        raise ValueError("El estimador debe implementar predict.")

    if not callable(getattr(estimator, "predict_proba", None)):
        raise ValueError("El estimador debe implementar predict_proba.")

    return cast(WineQualityEstimator, estimator)


def create_manifest(
    estimator: WineQualityEstimator, model_version: str
) -> ArtifactManifest:
    """TODO: devuelve un manifiesto compatible con el contrato."""

    _require_estimator(estimator)

    return ArtifactManifest(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        model_version=model_version,
        preprocessing_version=PREPROCESSING_VERSION,
        feature_names=FEATURE_NAMES,
        output_labels=OUTPUT_LABELS,
        estimator_type=type(estimator).__name__,
    )


def save_model_bundle(
    bundle_path: Path,
    estimator: WineQualityEstimator,
    manifest: ArtifactManifest | None = None,
) -> ArtifactManifest:
    """TODO: escribe manifest.json y model.joblib de forma segura."""

    estimator = _require_estimator(estimator)

    if manifest is None:
        manifest = create_manifest(
            estimator,
            model_version="unknown",
        )

    bundle_path.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {"estimator": estimator},
        bundle_path / MODEL_FILENAME,
        compress=3,
    )

    (bundle_path / MANIFEST_FILENAME).write_text(
        manifest.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )

    return manifest


def load_model_bundle(bundle_path: Path) -> LoadedModelBundle:
    """TODO: valida el manifiesto antes de cargar el estimador."""

    manifest_path = bundle_path / MANIFEST_FILENAME
    model_path = bundle_path / MODEL_FILENAME

    if not manifest_path.is_file() or not model_path.is_file():
        raise FileNotFoundError("El bundle debe contener manifest.json y model.joblib.")

    try:
        manifest = ArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except ValidationError as error:
        raise ValueError("manifest.json inválido") from error

    payload = joblib.load(model_path)

    if not isinstance(payload, Mapping):
        raise ValueError("model.joblib no tiene el formato esperado.")

    estimator = _require_estimator(payload.get("estimator"))

    return LoadedModelBundle(
        estimator=estimator,
        manifest=manifest,
    )


def infer_wine_quality(
    bundle: LoadedModelBundle,
    request: WineQualityRequest,
) -> WineQualityPrediction:
    """TODO: preprocesa, invoca el estimador y valida la respuesta."""

    features = preprocess_wine_request(request)
    matrix = [features.as_vector()]

    labels = bundle.estimator.predict(matrix)
    probabilities = bundle.estimator.predict_proba(matrix)

    if len(labels) != 1 or len(probabilities) != 1:
        raise ValueError("El modelo debe devolver una salida por fila.")

    if len(probabilities[0]) == 0:
        raise ValueError("El modelo no devolvió probabilidades.")

    try:
        return WineQualityPrediction(
            quality_band=str(labels[0]),
            confidence=max(float(value) for value in probabilities[0]),
            model_version=bundle.manifest.model_version,
            preprocessing_version=bundle.manifest.preprocessing_version,
        )
    except ValidationError as error:
        raise ValueError("La salida del modelo no cumple el contrato.") from error
