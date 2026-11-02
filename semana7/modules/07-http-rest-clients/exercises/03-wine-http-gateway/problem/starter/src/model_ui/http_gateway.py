"""Cliente HTTP que adapta la API Wine al contrato de inferencia de la UI."""

from __future__ import annotations

from collections.abc import Mapping
from threading import local
from typing import Any

import requests
from pydantic import ValidationError  # noqa: F401 - pista para el TODO S7.4

from model_ui.contracts import PredictionPayload
from model_ui.errors import (  # noqa: F401 - pistas para el TODO S7.2
    ArtifactUnavailableError,
    BackendInferenceError,
    InferenceTimeoutError,
    InputContractError,
)


class HttpInferenceGateway:
    """Implementa la frontera de inferencia mediante una llamada HTTP REST."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        session: Any | None = None,
    ) -> None:
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            raise ValueError("base_url no puede estar vacia")
        if timeout <= 0:
            raise ValueError("timeout debe ser positivo")

        self._prediction_url = f"{normalized}/v1/predictions"
        self._timeout = float(timeout)
        self._session = session if session is not None else requests.Session()
        self._request_context = local()
        self.last_request_id: str | None = None

    @property
    def last_request_id(self) -> str | None:
        """Devuelve el identificador de la ultima llamada en el contexto actual."""

        return getattr(self._request_context, "request_id", None)

    @last_request_id.setter
    def last_request_id(self, value: str | None) -> None:
        self._request_context.request_id = value

    def predict(self, values: Mapping[str, object]) -> PredictionPayload:
        """Envia la muestra por HTTP y devuelve el contrato interno de S6."""

        # TODO S7.1: envia POST a self._prediction_url con json={"features": ...},
        # Accept application/json y self._timeout. Compruebalo con el test de llamada.
        self.last_request_id = None

        try:
            response = self._session.post(
                self._prediction_url,
                json={"features": dict(values)},
                headers={"Accept": "application/json"},
                timeout=self._timeout,
            )
        # TODO S7.2: traduce Timeout, ConnectionError y RequestException a los
        # errores de dominio que ya entiende PredictionController.
        except requests.Timeout as error:
            raise InferenceTimeoutError(
                "Tiempo de espera agotado. Inténtalo de nuevo."
            ) from error

        except requests.ConnectionError as error:
            raise ArtifactUnavailableError(
                "No se ha podido conectar con la API"
            ) from error

        except requests.RequestException as error:
            raise BackendInferenceError("Fallo del ciente HTTP") from error
        # TODO S7.3: lee un objeto JSON, conserva request_id y diferencia 422/503
        # del resto de errores HTTP.

        self.last_request_id = self._header_request_id(response)
        if response.status_code == 422:
            raise InputContractError("El contrato de entrada ha sido rechazado")
        if response.status_code == 503:
            raise ArtifactUnavailableError("El modelo remoto no esta disponible.")
        if not 200 <= response.status_code < 300:
            raise BackendInferenceError(
                f"La API respondio con HTTP {response.status_code}."
            )
        # TODO S7.4: valida body["prediction"] como PredictionPayload; un dict sin
        # validar no satisface el contrato de salida.
        body = self._read_object(response)
        self.last_request_id = self._request_id(response, body)
        prediction = body.get("prediction")
        try:
            return PredictionPayload.model_validate(prediction)
        except ValidationError as error:
            raise BackendInferenceError(
                "La respuesta de la API no cumple el contrato."
            ) from error

    @staticmethod
    def _read_object(response: Any) -> dict[str, Any]:
        """Lee una respuesta JSON que debe representar un objeto."""

        # TODO S7.3: usa response.json(), traduce ValueError y rechaza listas u
        # otros valores que no sean un objeto JSON.
        try:
            body = response.json()
        except ValueError as error:
            raise BackendInferenceError(
                "La API no ha devuelto un JSON válido"
            ) from error
        if not isinstance(body, dict):
            raise BackendInferenceError("La respuesta no es un objeto JSON")
        return body

    @staticmethod
    def _request_id(response: Any, body: dict[str, Any]) -> str | None:
        """Obtiene request_id del cuerpo y usa la cabecera como alternativa."""

        # TODO S7.3: prioriza body["request_id"] y usa X-Request-Id como fallback.
        return body.get("request_id") or HttpInferenceGateway._header_request_id(
            response
        )

    @staticmethod
    def _header_request_id(response: Any) -> str | None:
        headers = getattr(response, "headers", {})
        return headers.get("X-Request-Id")
