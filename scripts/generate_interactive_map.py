#!/usr/bin/env python3
"""Gera um mapa interativo em SVG/HTML para os eventos de Santa Catarina.

O repositório declara GeoPandas em requirements.txt para permitir substituir o
contorno simplificado por uma malha oficial filtrada para SC quando a rede e as
rodas nativas estiverem disponíveis. Este gerador usa apenas a biblioteca padrão
para manter o build reproduzível no ambiente atual.
"""

from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_CSV = ROOT / "data" / "events_sc_2026.csv"
BOUNDARY_GEOJSON = ROOT / "data" / "santa_catarina_boundary.geojson"
OUTPUT_HTML = ROOT / "santa_catarina_eventos_2026.html"
PUBLIC_OUTPUT_HTML = ROOT / "public" / "santa_catarina_eventos_2026.html"
WIDTH = 1100
HEIGHT = 760
PADDING = 58


def read_events() -> list[dict[str, str]]:
    with EVENTS_CSV.open(encoding="utf-8", newline="") as file:
        events = list(csv.DictReader(file))
    for event in events:
        event["latitude"] = float(event["latitude"])
        event["longitude"] = float(event["longitude"])
    return events


def read_boundary() -> list[tuple[float, float]]:
    data = json.loads(BOUNDARY_GEOJSON.read_text(encoding="utf-8"))
    return [(lat, lon) for lon, lat in data["features"][0]["geometry"]["coordinates"][0]]


def haversine_km(a: dict[str, str], b: dict[str, str]) -> float:
    radius = 6371.0
    lat1 = math.radians(float(a["latitude"]))
    lat2 = math.radians(float(b["latitude"]))
    dlat = lat2 - lat1
    dlon = math.radians(float(b["longitude"]) - float(a["longitude"]))
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def nearest_neighbor_route(events: list[dict[str, str]]) -> list[dict[str, str]]:
    remaining = events.copy()
    route = [remaining.pop(0)]
    while remaining:
        current = route[-1]
        nearest = min(remaining, key=lambda event: haversine_km(current, event))
        remaining.remove(nearest)
        route.append(nearest)
    total = 0.0
    for index, event in enumerate(route):
        if index == 0:
            event["route_leg_km"] = 0.0
            event["route_total_km"] = 0.0
        else:
            leg = haversine_km(route[index - 1], event)
            total += leg
            event["route_leg_km"] = round(leg, 1)
            event["route_total_km"] = round(total, 1)
        event["route_order"] = index + 1
    return route


def projection(boundary: list[tuple[float, float]], events: list[dict[str, str]]):
    lats = [lat for lat, _ in boundary] + [float(event["latitude"]) for event in events]
    lons = [lon for _, lon in boundary] + [float(event["longitude"]) for event in events]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    def project(lat: float, lon: float) -> tuple[float, float]:
        x = PADDING + (lon - min_lon) / (max_lon - min_lon) * (WIDTH - PADDING * 2)
        y = PADDING + (max_lat - lat) / (max_lat - min_lat) * (HEIGHT - PADDING * 2)
        return round(x, 2), round(y, 2)

    return project


def make_html(events: list[dict[str, str]], boundary: list[tuple[float, float]]) -> str:
    route = nearest_neighbor_route(events)
    project = projection(boundary, events)
    boundary_points = " ".join(f"{x},{y}" for x, y in (project(lat, lon) for lat, lon in boundary))
    route_points = " ".join(f"{project(float(event['latitude']), float(event['longitude']))[0]},{project(float(event['latitude']), float(event['longitude']))[1]}" for event in route)

    markers = []
    for event in route:
        x, y = project(float(event["latitude"]), float(event["longitude"]))
        tooltip = (
            f"{event['route_order']}. {event['evento']}\n"
            f"Cidade: {event['cidade']}\n"
            f"Data: {event['data']}\n"
            f"Contato: {event['contato']}\n"
            f"Coordenadas: {event['latitude']}, {event['longitude']}\n"
            f"Trecho anterior: {event['route_leg_km']} km | Acumulado: {event['route_total_km']} km"
        )
        markers.append(
            f'<g class="marker" tabindex="0" data-title="{html.escape(event["evento"])}" '
            f'data-city="{html.escape(event["cidade"])}" data-date="{html.escape(event["data"])}" '
            f'data-contact="{html.escape(event["contato"])}" data-lat="{event["latitude"]}" '
            f'data-lon="{event["longitude"]}" data-leg="{event["route_leg_km"]}" '
            f'data-total="{event["route_total_km"]}">'
            f'<circle cx="{x}" cy="{y}" r="12"/><text x="{x}" y="{y + 4}" text-anchor="middle">{event["route_order"]}</text>'
            f'<title>{html.escape(tooltip)}</title></g>'
        )

    rows = []
    for event in route:
        rows.append(
            "<tr>"
            f"<td>{event['route_order']}</td>"
            f"<td>{html.escape(event['evento'])}</td>"
            f"<td>{html.escape(event['cidade'])}</td>"
            f"<td>{html.escape(event['data'])}</td>"
            f"<td>{event['route_leg_km']}</td>"
            f"<td>{event['route_total_km']}</td>"
            "</tr>"
        )

    html_text = (ROOT / "scripts" / "map_template.html").read_text(encoding="utf-8")
    replacements = {
        "{{boundary_points}}": boundary_points,
        "{{route_points}}": route_points,
        "{{markers}}": "\n".join(markers),
        "{{rows}}": "\n".join(rows),
        "{{total_km}}": str(route[-1]["route_total_km"]),
        "{{event_count}}": str(len(events)),
    }
    for key, value in replacements.items():
        html_text = html_text.replace(key, value)
    return html_text


def main() -> None:
    events = read_events()
    boundary = read_boundary()
    html_text = make_html(events, boundary)
    OUTPUT_HTML.write_text(html_text, encoding="utf-8")
    PUBLIC_OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_OUTPUT_HTML.write_text(html_text, encoding="utf-8")
    print(f"Mapa gerado em {OUTPUT_HTML.relative_to(ROOT)} e {PUBLIC_OUTPUT_HTML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
