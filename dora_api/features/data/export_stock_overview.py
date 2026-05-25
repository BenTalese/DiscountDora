"""Stock-overview exports — install-wide CSV + a stocktake-friendly print view.

  GET /api/stock-items/export?format=csv
  GET /api/stock-items/print-view

Designed for "take it to the pantry" use — print-view groups by location,
shows level + expiry, leaves a checkbox column to tick off as the user
counts.
"""
import csv
import io
import logging
from datetime import datetime, timezone

from flask import Response, render_template_string, request

from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.data.export_shared import PRINT_CSS, PRINT_TOOLBAR
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import bad_request
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def _location_name(item: StockItem) -> str:
    return item.stock_location.name if item.stock_location else "(no location)"


def _group_by_location(items):
    buckets: dict[str, list[StockItem]] = {}
    for item in items:
        buckets.setdefault(_location_name(item), []).append(item)
    for v in buckets.values():
        v.sort(key=lambda i: i.name.lower())

    def _sort_key(name: str) -> tuple[int, str]:
        return (1, "") if name == "(no location)" else (0, name.lower())

    return sorted(buckets.items(), key=lambda kv: _sort_key(kv[0]))


def _build_csv(items) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "location", "name", "level", "expiry", "is_flagged", "is_open",
        "auto_add_when_low", "barcode", "notes",
    ])
    for location, group in _group_by_location(items):
        for item in group:
            writer.writerow([
                location,
                item.name,
                item.stock_level.name if item.stock_level else "",
                item.expiry_date.isoformat() if item.expiry_date else "",
                "true" if item.is_flagged else "false",
                "true" if item.is_open else "false",
                "true" if item.auto_add_when_low else "false",
                item.barcode or "",
                item.notes or "",
            ])
    return buffer.getvalue()


_PRINT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Stock overview</title>
  {{ css | safe }}
</head>
<body>
  {{ toolbar | safe }}
  <div class="page">
    <h1>Stock overview</h1>
    <div class="meta">
      Generated {{ generated_at }} · {{ total }} item(s) across
      {{ groups | length }} location(s)
    </div>
    {% if total == 0 %}
      <p><em>No stock items yet.</em></p>
    {% else %}
      {% for location, items in groups %}
        <h2>{{ location }} <span class="meta">({{ items | length }})</span></h2>
        <table>
          <thead>
            <tr>
              <th class="box"></th>
              <th>Item</th>
              <th>Level</th>
              <th>Expiry</th>
            </tr>
          </thead>
          <tbody>
            {% for item in items %}
              <tr>
                <td class="box"><span class="checkbox"></span></td>
                <td>
                  <span class="item-name">{{ item.name }}</span>
                  {% if item.notes %}
                    <div class="item-notes">{{ item.notes }}</div>
                  {% endif %}
                </td>
                <td>{{ item.stock_level.name if item.stock_level else '—' }}</td>
                <td>{{ item.expiry_date.isoformat() if item.expiry_date else '—' }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% endfor %}
    {% endif %}
  </div>
</body>
</html>
"""


def _all_items():
    repo = SqlAlchemyRepository()
    return (
        repo.get(StockItem)
        .include("stock_level")
        .include("stock_location")
        .all()
    )


@STOCK_ITEM_ROUTER.route("/export", methods=["GET"])
def export_stock_overview():
    fmt = (request.args.get("format") or "csv").lower()
    if fmt not in ("csv",):
        return bad_request(
            f"Unsupported export format '{fmt}'. Supported: csv. "
            "For PDF, open the print-view and 'Save as PDF' from your browser."
        )
    items = _all_items()
    body = _build_csv(items)
    today = datetime.now(timezone.utc).date().isoformat()
    filename = f"stock-overview-{today}.csv"
    logging.getLogger(__name__).info(
        "Exported stock overview as %s (%d items)", fmt, len(items),
    )
    response = Response(body, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@STOCK_ITEM_ROUTER.route("/print-view", methods=["GET"])
def print_view_stock_overview():
    items = _all_items()
    generated_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    html = render_template_string(
        _PRINT_TEMPLATE,
        groups=_group_by_location(items),
        total=len(items),
        generated_at=generated_at,
        css=PRINT_CSS,
        toolbar=PRINT_TOOLBAR,
    )
    return Response(html, mimetype="text/html; charset=utf-8")
