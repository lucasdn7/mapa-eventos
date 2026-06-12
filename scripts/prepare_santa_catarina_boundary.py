#!/usr/bin/env python3
"""Filtra uma malha geográfica para manter somente Santa Catarina.

Uso:
    python scripts/prepare_santa_catarina_boundary.py caminho/entrada.geojson data/santa_catarina_boundary.geojson

A entrada pode ser uma malha do Brasil em GeoJSON, Shapefile, GeoPackage etc.
O filtro procura códigos/nome/UF comuns usados em bases do IBGE e salva apenas SC.
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "santa_catarina_boundary.geojson"
SC_CODES = {"42", "4200000"}
SC_NAMES = {"santa catarina", "sc"}


def normalize(value: object) -> str:
    return str(value).strip().lower()


def is_santa_catarina(row) -> bool:
    for column, value in row.items():
        normalized = normalize(value)
        if normalized in SC_NAMES or normalized in SC_CODES:
            return True
        if column.upper() in {"CD_UF", "CD_GEOCUF", "GEOCODIGO", "SIGLA_UF", "UF", "NM_UF", "NOME"}:
            if normalized in SC_NAMES or normalized in SC_CODES:
                return True
    return False


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Informe a malha de entrada. Ex.: python scripts/prepare_santa_catarina_boundary.py brasil.geojson")

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    gdf = gpd.read_file(input_path)
    sc = gdf[gdf.apply(is_santa_catarina, axis=1)].to_crs("EPSG:4326")

    if sc.empty:
        raise SystemExit("Nenhuma feição de Santa Catarina foi encontrada na malha informada.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sc.to_file(output_path, driver="GeoJSON")
    print(f"Mapa de Santa Catarina salvo em {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
