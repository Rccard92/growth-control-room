from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.period import ResolvedPeriod

PROBE_QUERY = "FROM sales SHOW total_sales, orders SINCE -7d"


def period_to_shopifyql_range(period: ResolvedPeriod) -> str:
    start = period.start_date.isoformat()
    end = period.end_date.isoformat()
    return f"SINCE {start} UNTIL {end}"


def _column_names(columns: list[dict[str, Any]]) -> list[str]:
    return [str(col.get("name") or "") for col in columns]


def parse_table_response(result: dict[str, Any]) -> list[dict[str, Any]]:
    columns = _column_names(result.get("columns") or [])
    rows = result.get("rows") or []
    parsed: list[dict[str, Any]] = []

    for row in rows:
        if isinstance(row, dict):
            parsed.append(dict(row))
            continue
        if not isinstance(row, (list, tuple)):
            continue
        entry: dict[str, Any] = {}
        for index, name in enumerate(columns):
            if not name:
                continue
            entry[name] = row[index] if index < len(row) else None
        parsed.append(entry)

    return parsed


def _to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _to_int(value: Any) -> int | None:
    dec = _to_decimal(value)
    if dec is None:
        return None
    return int(dec)


def _to_float(value: Any) -> float | None:
    dec = _to_decimal(value)
    if dec is None:
        return None
    return float(dec)


def parse_scalar_row(rows: list[Any], column: str, parsed_rows: list[dict[str, Any]] | None = None) -> Any:
    data = parsed_rows if parsed_rows is not None else []
    if not data and rows:
        data = [{"value": rows[0][0] if isinstance(rows[0], (list, tuple)) and rows[0] else rows[0]}]
        column = "value"
    if not data:
        return None
    return data[0].get(column)


def classify_shopifyql_error(
    exc: Exception | None = None,
    *,
    response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message_blob = ""
    status_code: int | None = None

    if exc is not None:
        message_blob = str(getattr(exc, "message", exc)).lower()
        if isinstance(exc, ShopifyAPIError):
            status_code = exc.status_code

    if response:
        graphql_errors = response.get("graphql_errors") or []
        for err in graphql_errors:
            if isinstance(err, dict):
                message_blob += " " + str(err.get("message", "")).lower()
            else:
                message_blob += " " + str(err).lower()
        parse_errors = response.get("parse_errors") or []
        if parse_errors:
            messages = [
                err.get("message", str(err)) if isinstance(err, dict) else str(err)
                for err in parse_errors
            ]
            return {
                "available": False,
                "requires_reconnect": False,
                "error_code": "parse_error",
                "message": "Errore di sintassi ShopifyQL: " + "; ".join(messages[:2]),
            }

    if status_code in {401, 403} or "read_reports" in message_blob or "access denied" in message_blob:
        return {
            "available": False,
            "requires_reconnect": True,
            "error_code": "missing_read_reports",
            "message": (
                "ShopifyQL richiede lo scope read_reports. "
                "Riconnetti Shopify per autorizzare i report Analytics."
            ),
        }

    if "shopifyql" in message_blob and ("not authorized" in message_blob or "permission" in message_blob):
        return {
            "available": False,
            "requires_reconnect": True,
            "error_code": "shopifyql_not_authorized",
            "message": "ShopifyQL non autorizzato per questo store o app.",
        }

    if exc is not None:
        if isinstance(exc, ShopifyAPIError) and status_code and status_code >= 500:
            return {
                "available": False,
                "requires_reconnect": False,
                "error_code": "network_error",
                "message": "Shopify non disponibile al momento. Riprova più tardi.",
            }
        return {
            "available": False,
            "requires_reconnect": False,
            "error_code": "network_error",
            "message": str(getattr(exc, "message", exc)),
        }

    return {
        "available": False,
        "requires_reconnect": False,
        "error_code": "unknown_error",
        "message": "ShopifyQL non disponibile.",
    }


def build_unavailable_official_analytics(error: dict[str, Any]) -> dict[str, Any]:
    return {
        "available": False,
        "source": "shopifyql",
        "kpis": {
            "total_sales": None,
            "orders": None,
            "average_order_value": None,
            "sessions": None,
            "conversion_rate": None,
        },
        "timeseries": [],
        "sales_by_referring_channel": [],
        "sales_by_utm_campaign": [],
        "data_quality": {
            "status": "unavailable",
            "warnings": [error.get("message", "ShopifyQL non disponibile.")],
        },
        "_error": error,
    }


async def _run_shopifyql(client: ShopifyGraphQLClient, shopifyql: str) -> dict[str, Any]:
    return await client.execute_shopifyql(shopifyql)


async def probe_shopifyql(client: ShopifyGraphQLClient) -> dict[str, Any]:
    try:
        result = await _run_shopifyql(client, PROBE_QUERY)
        if result.get("graphql_errors"):
            error = classify_shopifyql_error(response=result)
            return {**error, "sample": None}

        parse_errors = result.get("parse_errors") or []
        if parse_errors:
            error = classify_shopifyql_error(response=result)
            return {**error, "sample": None}

        rows = result.get("rows") or []
        if not rows:
            return {
                "available": False,
                "requires_reconnect": False,
                "error_code": "empty_response",
                "message": "ShopifyQL ha risposto senza dati.",
                "sample": None,
            }

        return {
            "available": True,
            "requires_reconnect": False,
            "error_code": None,
            "message": "ShopifyQL disponibile.",
            "sample": {
                "columns": result.get("columns") or [],
                "rows": rows,
            },
        }
    except ShopifyAPIError as exc:
        error = classify_shopifyql_error(exc)
        return {**error, "sample": None}
    except Exception as exc:
        error = classify_shopifyql_error(exc)
        return {**error, "sample": None}


def _merge_timeseries(
    sales_rows: list[dict[str, Any]],
    sessions_rows: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    sessions_by_date: dict[str, dict[str, Any]] = {}
    for row in sessions_rows or []:
        day = str(row.get("day") or row.get("date") or "")
        if day:
            sessions_by_date[day] = row

    merged: list[dict[str, Any]] = []
    for row in sales_rows:
        day = str(row.get("day") or row.get("date") or "")
        session_row = sessions_by_date.get(day, {})
        merged.append(
            {
                "date": day,
                "total_sales": _to_decimal(row.get("total_sales")),
                "orders": _to_int(row.get("orders")),
                "sessions": _to_int(session_row.get("sessions")),
                "conversion_rate": _to_float(session_row.get("conversion_rate")),
            }
        )
    return merged


def _build_kpis(
    executive_rows: list[dict[str, Any]],
    sessions_rows: list[dict[str, Any]] | None,
) -> dict[str, Decimal | int | float | None]:
    executive = executive_rows[0] if executive_rows else {}
    total_sessions = 0
    conversion_rates: list[float] = []
    for row in sessions_rows or []:
        sessions_val = _to_int(row.get("sessions"))
        if sessions_val is not None:
            total_sessions += sessions_val
        rate = _to_float(row.get("conversion_rate"))
        if rate is not None:
            conversion_rates.append(rate)

    avg_conversion = (
        sum(conversion_rates) / len(conversion_rates) if conversion_rates else None
    )

    return {
        "total_sales": _to_decimal(executive.get("total_sales")),
        "orders": _to_int(executive.get("orders")),
        "average_order_value": _to_decimal(executive.get("average_order_value")),
        "sessions": total_sessions if sessions_rows else None,
        "conversion_rate": avg_conversion,
    }


async def fetch_official_analytics(
    client: ShopifyGraphQLClient,
    period: ResolvedPeriod,
) -> dict[str, Any]:
    date_range = period_to_shopifyql_range(period)
    warnings: list[str] = []
    data_quality_status = "ok"

    queries = {
        "executive": f"FROM sales SHOW total_sales, orders, average_order_value {date_range}",
        "sales_timeseries": f"FROM sales SHOW total_sales, orders TIMESERIES day {date_range}",
        "sessions_timeseries": f"FROM sessions SHOW sessions, conversion_rate TIMESERIES day {date_range}",
        "referring_channel": f"FROM sales SHOW total_sales, orders GROUP BY referring_channel {date_range}",
        "utm_campaign": (
            "FROM sales SHOW total_sales, orders "
            "GROUP BY utm_campaign_name, utm_campaign_source, utm_campaign_medium "
            f"{date_range}"
        ),
    }

    results: dict[str, dict[str, Any]] = {}
    for key, shopifyql in queries.items():
        try:
            response = await _run_shopifyql(client, shopifyql)
            if response.get("graphql_errors"):
                error = classify_shopifyql_error(response=response)
                return build_unavailable_official_analytics(error)
            if response.get("parse_errors"):
                if key in {"executive", "sales_timeseries"}:
                    error = classify_shopifyql_error(response=response)
                    return build_unavailable_official_analytics(error)
                warnings.append(
                    f"Query {key} non disponibile: "
                    + "; ".join(
                        err.get("message", str(err))
                        if isinstance(err, dict)
                        else str(err)
                        for err in response.get("parse_errors") or []
                    )[:200]
                )
                data_quality_status = "limited"
                results[key] = {"columns": [], "rows": [], "parse_errors": response.get("parse_errors")}
                continue
            results[key] = response
        except ShopifyAPIError as exc:
            if key in {"executive", "sales_timeseries"}:
                return build_unavailable_official_analytics(classify_shopifyql_error(exc))
            warnings.append(f"Query {key} fallita: {exc.message}")
            data_quality_status = "limited"
            results[key] = {"columns": [], "rows": [], "parse_errors": []}

    executive_rows = parse_table_response(results.get("executive", {}))
    sales_ts_rows = parse_table_response(results.get("sales_timeseries", {}))
    sessions_ts_rows = parse_table_response(results.get("sessions_timeseries", {}))
    channel_rows = parse_table_response(results.get("referring_channel", {}))
    utm_rows = parse_table_response(results.get("utm_campaign", {}))

    if not executive_rows and not sales_ts_rows:
        return build_unavailable_official_analytics(
            {
                "message": "ShopifyQL non ha restituito dati per il periodo selezionato.",
                "error_code": "empty_response",
            }
        )

    kpis = _build_kpis(executive_rows, sessions_ts_rows if results.get("sessions_timeseries", {}).get("rows") else None)
    if kpis.get("sessions") is None and "sessions_timeseries" in results:
        warnings.append("Sessions/conversion rate non disponibili per questo periodo.")
        data_quality_status = "limited"

    timeseries = _merge_timeseries(sales_ts_rows, sessions_ts_rows if sessions_ts_rows else None)

    sales_by_referring_channel = [
        {
            "channel": str(row.get("referring_channel") or "Unknown"),
            "total_sales": _to_decimal(row.get("total_sales")) or Decimal("0"),
            "orders": _to_int(row.get("orders")) or 0,
        }
        for row in channel_rows
    ]
    sales_by_referring_channel.sort(key=lambda item: item["total_sales"], reverse=True)

    sales_by_utm_campaign = [
        {
            "name": str(row.get("utm_campaign_name") or "(not set)"),
            "source": str(row.get("utm_campaign_source") or "(not set)"),
            "medium": str(row.get("utm_campaign_medium") or "(not set)"),
            "total_sales": _to_decimal(row.get("total_sales")) or Decimal("0"),
            "orders": _to_int(row.get("orders")) or 0,
        }
        for row in utm_rows
    ]
    sales_by_utm_campaign.sort(key=lambda item: item["total_sales"], reverse=True)

    return {
        "available": True,
        "source": "shopifyql",
        "kpis": kpis,
        "timeseries": timeseries,
        "sales_by_referring_channel": sales_by_referring_channel,
        "sales_by_utm_campaign": sales_by_utm_campaign,
        "data_quality": {
            "status": data_quality_status,
            "warnings": warnings,
        },
    }


def build_analytics_reconciliation(
    official_analytics: dict[str, Any],
    local_reconciliation: dict[str, Any],
) -> dict[str, Any]:
    local_total = Decimal(
        str(local_reconciliation.get("sales_breakdown", {}).get("total_sales", 0))
    )
    official_kpis = official_analytics.get("kpis") or {}
    official_total_raw = official_kpis.get("total_sales")
    official_total = (
        Decimal(str(official_total_raw)) if official_total_raw is not None else None
    )

    if not official_analytics.get("available") or official_total is None:
        return {
            "official_total_sales": None,
            "local_total_sales": local_total,
            "delta": None,
            "delta_percent": None,
            "message": (
                "Confronto ufficiale non disponibile. "
                "Usa i totali locali finché ShopifyQL non è autorizzato."
            ),
        }

    delta = official_total - local_total
    delta_percent: float | None
    if local_total == 0:
        delta_percent = None if official_total == 0 else 100.0
    else:
        delta_percent = round(float((delta / local_total) * 100), 1)

    if abs(delta) <= Decimal("0.01"):
        message = (
            "I total sales ShopifyQL e locali sono allineati per il periodo selezionato."
        )
    elif delta > 0:
        message = (
            "ShopifyQL riporta total sales superiori al calcolo locale. "
            "Possibili cause: reversal contabilizzati in giorni diversi, tax/shipping, "
            "o ordini fuori dallo storico sincronizzato."
        )
    else:
        message = (
            "Il calcolo locale supera i total sales ShopifyQL. "
            "Verifica refund non sincronizzati o differenze di periodo ordine vs reversal."
        )

    return {
        "official_total_sales": official_total,
        "local_total_sales": local_total,
        "delta": delta,
        "delta_percent": delta_percent,
        "message": message,
    }
