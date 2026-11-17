"""Punto de extensión del CLI de inferencia sobre un bundle."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pydantic import ValidationError

from model_packaging.artifact import (
    DEFAULT_BUNDLE_PATH,
    infer_wine_quality,
    load_model_bundle,
)
from model_packaging.contracts import WineQualityRequest
from model_packaging.preprocess import FEATURE_NAMES

OUTPUT_FIELDS = (
    "sample_id",
    "quality_band",
    "confidence",
    "model_version",
    "preprocessing_version",
)

INPUT_FIELDS = ("sample_id", *FEATURE_NAMES)


def predict_file(
    input_path: Path,
    output_path: Path,
    bundle_path: Path,
) -> int:
    """TODO: valida todas las filas y escribe el CSV solo al final."""
    bundle = load_model_bundle(bundle_path)
    predictions: list[dict[str, str | float]] = []

    with input_path.open(
        newline="",
        encoding="utf-8",
    ) as source:
        rows = csv.DictReader(source)

        if (
            rows.fieldnames is None
            or len(rows.fieldnames) != len(INPUT_FIELDS)
            or set(rows.fieldnames) != set(INPUT_FIELDS)
        ):
            raise ValueError("El CSV no contiene las columnas esperadas.")

        for row_number, row in enumerate(rows, start=2):
            sample_id = (row.pop("sample_id") or "").strip()

            if not sample_id:
                raise ValueError(f"Fila {row_number} tiene un sample_id vacío.")

            try:
                request = WineQualityRequest.model_validate(row)

            except ValidationError as error:
                raise ValueError(
                    f"Fila {row_number} inválida para sample_id={sample_id}."
                ) from error

            prediction = infer_wine_quality(
                bundle,
                request,
            )

            predictions.append(
                {
                    "sample_id": sample_id,
                    **prediction.model_dump(),
                }
            )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as target:
        writer = csv.DictWriter(
            target,
            fieldnames=OUTPUT_FIELDS,
        )

        writer.writeheader()
        writer.writerows(predictions)

    return len(predictions)


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE_PATH, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(
        predict_file(
            input_path=arguments.input,
            output_path=arguments.output,
            bundle_path=arguments.bundle,
        )
    )
