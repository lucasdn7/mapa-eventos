#!/usr/bin/env python3
"""Gera um mapa cartográfico interativo em HTML para eventos em Santa Catarina.

O HTML gerado é estático e contém os dados dos eventos e o contorno de Santa
Catarina embutidos. A rota e a tabela seguem a ordem cronológica dos eventos.
"""

from __future__ import annotations

import csv
import html
import json
import math
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_CSV = ROOT / "data" / "events_sc_2026.csv"
BOUNDARY_GEOJSON = ROOT / "data" / "santa_catarina_boundary.geojson"
OUTPUT_HTML = ROOT / "santa_catarina_eventos_2026.html"
PUBLIC_OUTPUT_HTML = ROOT / "public" / "santa_catarina_eventos_2026.html"
TEMPLATE_HTML = ROOT / "scripts" / "map_template.html"

MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def parse_start_date(value: str) -> date:
    """Extrai a primeira data informada em textos como '3, 4 e 5 de julho de 2026'."""
    normalized = value.strip().lower().replace("º", "")
    match = re.search(r"(\d{1,2})(?:\s*a\s*\d{1,2}|(?:\s*,\s*\d{1,2})*(?:\s*e\s*\d{1,2})?)?\s+de\s+([a-zç]+)\s+de\s+(\d{4})", normalized)
    if not match:
        raise ValueError(f"Não foi possível interpretar a data do evento: {value}")
    day, month_name, year = match.groups()
    return date(int(year), MONTHS[month_name], int(day))


def read_events() -> list[dict[str, object]]:
    with EVENTS_CSV.open(encoding="utf-8", newline="") as file:
        events = list(csv.DictReader(file))

    for event in events:
        event["latitude"] = float(event["latitude"])
        event["longitude"] = float(event["longitude"])
        event["start_date"] = parse_start_date(str(event["data"]))

    return sorted(events, key=lambda event: (event["start_date"], int(str(event["ordem_original"]))))


def read_boundary() -> dict[str, object]:
    return json.loads(BOUNDARY_GEOJSON.read_text(encoding="utf-8"))


def haversine_km(a: dict[str, object], b: dict[str, object]) -> float:
    radius = 6371.0
    lat1 = math.radians(float(a["latitude"]))
    lat2 = math.radians(float(b["latitude"]))
    dlat = lat2 - lat1
    dlon = math.radians(float(b["longitude"]) - float(a["longitude"]))
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def add_chronological_route(events: list[dict[str, object]]) -> list[dict[str, object]]:
    total = 0.0
    for index, event in enumerate(events):
        if index == 0:
            event["route_leg_km"] = 0.0
            event["route_total_km"] = 0.0
        else:
            leg = haversine_km(events[index - 1], event)
            total += leg
            event["route_leg_km"] = round(leg, 1)
            event["route_total_km"] = round(total, 1)
        event["route_order"] = index + 1
        event["start_date_iso"] = event["start_date"].isoformat()
    return events


def make_rows(events: list[dict[str, object]]) -> str:
    rows = []
    for event in events:
        rows.append(
            "<tr>"
            f"<td>{event['route_order']}</td>"
            f"<td>{html.escape(str(event['evento']))}</td>"
            f"<td>{html.escape(str(event['cidade']))}</td>"
            f"<td>{html.escape(str(event['data']))}</td>"
            f"<td>{event['route_leg_km']}</td>"
            f"<td>{event['route_total_km']}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def make_events_json(events: list[dict[str, object]]) -> str:
    serializable = []
    for event in events:
        serializable.append(
            {
                "route_order": event["route_order"],
                "evento": event["evento"],
                "cidade": event["cidade"],
                "data": event["data"],
                "contato": event["contato"],
                "latitude": event["latitude"],
                "longitude": event["longitude"],
                "route_leg_km": event["route_leg_km"],
                "route_total_km": event["route_total_km"],
                "start_date_iso": event["start_date_iso"],
            }
        )
    return json.dumps(serializable, ensure_ascii=False)


def make_html(events: list[dict[str, object]], boundary: dict[str, object]) -> str:
    routed_events = add_chronological_route(events)
    html_text = TEMPLATE_HTML.read_text(encoding="utf-8")
    replacements = {
        "{{events_json}}": make_events_json(routed_events),
        "{{boundary_json}}": json.dumps(boundary, ensure_ascii=False),
        "{{rows}}": make_rows(routed_events),
        "{{total_km}}": str(routed_events[-1]["route_total_km"]),
        "{{event_count}}": str(len(routed_events)),
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
