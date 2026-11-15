"""Investigate a synthetic monthly net sales variance after close."""

from decimal import Decimal, ROUND_HALF_UP

from .runtime import Call, Tool

INSTRUCTIONS = (
    "Investigate the requested GB net sales comparison using the read-only tools. "
    "Call get_close_status first. Continue to get_sales_variance only when both "
    "periods are closed and reconciled. Keep the requested period pair. Treat "
    "channel movements as arithmetic contributions and leave causal assessment "
    "and release to the finance analyst."
)

_PERIODS = {
    "normal": ("2026-10", "2026-09"),
    "blocked": ("2026-11", "2026-10"),
}
_CHANNEL_SALES_PENCE = {
    "2026-09": {"grocery": 120_000_000, "convenience": 50_000_000, "ecommerce": 30_000_000},
    "2026-10": {"grocery": 126_000_000, "convenience": 47_000_000, "ecommerce": 33_000_000},
}
_CLOSE_LEDGER_PENCE = {"2026-09": 200_000_000, "2026-10": 206_000_000}


def question(scenario: str) -> str:
    current, previous = _PERIODS[scenario]
    return (
        f"Explain the change in GB net sales from {previous} to {current} by channel. "
        "Check both closes and reconciliation before preparing anything for review."
    )


def _scope(current: str, previous: str) -> dict:
    return {"market": "GB", "current_period": current, "comparison_period": previous}


def _period_status(period: str) -> dict:
    if period not in _CLOSE_LEDGER_PENCE:
        return {"period": period, "close_status": "OPEN", "reconciliation_difference_pence": None}

    reported = sum(_CHANNEL_SALES_PENCE[period].values())
    return {
        "period": period,
        "close_status": "CLOSED",
        "reconciliation_difference_pence": reported - _CLOSE_LEDGER_PENCE[period],
    }


def _close_status(current: str, previous: str) -> dict:
    periods = [_period_status(current), _period_status(previous)]
    ready = all(
        item["close_status"] == "CLOSED" and item["reconciliation_difference_pence"] == 0
        for item in periods
    )
    return {
        "evidence_id": f"close-status:{current}:{previous}",
        "scope": _scope(current, previous),
        "periods": periods,
        "ready": ready,
    }


def _sales_variance(current: str, previous: str) -> dict:
    check = _close_status(current, previous)
    result = {
        "evidence_id": f"net-sales-variance:{current}:{previous}",
        "scope": check["scope"],
        "ready": check["ready"],
    }
    if not check["ready"]:
        return result

    current_sales = _CHANNEL_SALES_PENCE[current]
    previous_sales = _CHANNEL_SALES_PENCE[previous]
    channel_rows = []
    for channel in sorted(current_sales.keys() | previous_sales.keys()):
        current_pence = current_sales.get(channel, 0)
        comparison_pence = previous_sales.get(channel, 0)
        channel_rows.append({
            "channel": channel,
            "current_pence": current_pence,
            "comparison_pence": comparison_pence,
            "delta_pence": current_pence - comparison_pence,
        })
    return {
        **result,
        "current_pence": sum(row["current_pence"] for row in channel_rows),
        "comparison_pence": sum(row["comparison_pence"] for row in channel_rows),
        "delta_pence": sum(row["delta_pence"] for row in channel_rows),
        "channels": channel_rows,
    }


def tools(scenario: str) -> tuple[Tool, ...]:
    current, previous = _PERIODS[scenario]
    expected = {"current_period": current, "comparison_period": previous}
    parameters = {
        "type": "object",
        "properties": {key: {"type": "string", "enum": [value]} for key, value in expected.items()},
        "required": list(expected),
        "additionalProperties": False,
    }

    def scoped(operation):
        def execute(arguments: dict) -> dict:
            if arguments != expected:
                raise ValueError("Use the exact periods authorised for this comparison.")
            return operation(current, previous)

        return execute

    return (
        Tool(
            "get_close_status",
            "Check the close and reconciliation for both periods in the requested GB comparison.",
            parameters,
            scoped(_close_status),
        ),
        Tool(
            "get_sales_variance",
            "Get net sales totals and channel contributions when both periods are ready.",
            parameters,
            scoped(_sales_variance),
        ),
    )


def script(scenario: str) -> tuple[Call, ...]:
    current, previous = _PERIODS[scenario]
    arguments = {"current_period": current, "comparison_period": previous}
    check = Call("get_close_status", arguments)
    if scenario == "blocked":
        return (check,)
    return (check, Call("get_sales_variance", arguments.copy()))


def _additive(variance: dict) -> bool:
    rows = variance["channels"]
    return (
        all(row["current_pence"] - row["comparison_pence"] == row["delta_pence"] for row in rows)
        and all(
            sum(row[field] for row in rows) == variance[field]
            for field in ("current_pence", "comparison_pence", "delta_pence")
        )
        and variance["current_pence"] - variance["comparison_pence"] == variance["delta_pence"]
    )


def render(evidence: dict[str, dict]) -> dict:
    close = evidence.get("get_close_status")
    if close is None:
        return {"status": "INSUFFICIENT_EVIDENCE", "reason": "Close evidence is missing."}

    if not close["ready"]:
        return {
            "status": "WITHHELD",
            "reason": "Finance needs to close and reconcile both periods first.",
            "scope": close["scope"],
            "periods": close["periods"],
            "evidence_ids": [close["evidence_id"]],
        }

    variance = evidence.get("get_sales_variance")
    if not variance or not variance["ready"] or variance["scope"] != close["scope"]:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "reason": "Matching variance evidence is missing.",
            "evidence_ids": [close["evidence_id"]],
        }
    if not _additive(variance):
        return {
            "status": "WITHHELD",
            "reason": "Channel contributions do not reconcile to the headline.",
            "evidence_ids": [close["evidence_id"], variance["evidence_id"]],
        }

    prior = variance["comparison_pence"]
    delta = variance["delta_pence"]
    percent = None
    if prior > 0:
        percent = str((Decimal(delta) * 100 / prior).quantize(Decimal("0.01"), ROUND_HALF_UP))
    return {
        "status": "DRAFT_FOR_REVIEW",
        "scope": close["scope"],
        "metric": "Net sales",
        "currency": "GBP",
        "current_pence": variance["current_pence"],
        "comparison_pence": prior,
        "delta_pence": delta,
        "delta_percent": percent,
        "channel_contributions": variance["channels"],
        "evidence_ids": [close["evidence_id"], variance["evidence_id"]],
        "next_action": "Finance analyst reviews the contributors and approves any release.",
    }
