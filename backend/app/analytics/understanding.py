"""Deterministic dataset understanding used by insights and chat.

The LLM is optional.  This module deliberately derives the analytical
contract from the dataframe first so identifiers such as postal codes and
row IDs are not accidentally treated as business measures.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    "sales": (
        "sale", "sales", "revenue", "profit", "margin", "order", "product",
        "category", "quantity", "discount", "ship", "region", "customer",
    ),
    "marketing": (
        "campaign", "channel", "impression", "click", "spend", "conversion",
        "lead", "ctr", "cpc", "cpa", "roas", "creative", "audience",
    ),
    "finance": (
        "account", "debit", "credit", "balance", "expense", "invoice", "budget",
        "cash", "asset", "liability", "transaction",
    ),
    "support": (
        "ticket", "issue", "resolution", "sla", "sentiment", "priority", "agent",
        "response", "csat",
    ),
    "inventory": (
        "inventory", "stock", "sku", "warehouse", "reorder", "on hand", "supply",
        "stockout",
    ),
    "operations": (
        "delivery", "fulfillment", "lead time", "return", "shipment", "vendor",
        "production", "downtime",
    ),
}

MEASURE_TERMS: tuple[str, ...] = (
    "sales", "revenue", "profit", "margin", "cost", "price", "amount", "value",
    "quantity", "units", "discount", "spend", "impression", "click", "conversion",
    "revenue", "expense", "balance", "duration", "score", "rate", "count",
)

DIMENSION_TERMS: tuple[str, ...] = (
    "product", "category", "sub-category", "subcategory", "region", "state", "city",
    "country", "segment", "customer", "campaign", "channel", "source", "medium",
    "gender", "age group", "status", "type", "class", "department", "team",
)

ID_TERMS: tuple[str, ...] = (
    "id", "code", "zip", "postal", "phone", "row", "number", "number",
)


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower().replace("_", " ")))


def _name_score(name: str, terms: tuple[str, ...]) -> int:
    lowered = name.lower().replace("_", " ")
    tokens = _tokens(name)
    score = 0
    for term in terms:
        if " " in term and term in lowered:
            score += 2
        elif term in tokens or term in lowered:
            score += 1
    return score


def is_identifier_column(name: str, series: pd.Series) -> bool:
    """Return True for identifier-like numeric or categorical columns."""
    score = _name_score(name, ID_TERMS)
    uniqueness = float(series.nunique(dropna=True) / max(len(series), 1))
    return score > 0 and (uniqueness > 0.35 or score >= 2)


def _find_column(columns: list[str], terms: tuple[str, ...]) -> str | None:
    ranked = sorted(
        ((col, _name_score(col, terms)) for col in columns),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[0][0] if ranked and ranked[0][1] > 0 else None


def _detect_date_column(frame: pd.DataFrame) -> tuple[str | None, pd.DataFrame]:
    working = frame.copy()
    for col in working.columns:
        if pd.api.types.is_datetime64_any_dtype(working[col]):
            return str(col), working

    candidates: list[tuple[int, str, pd.Series]] = []
    for col in working.columns:
        name = str(col)
        lowered = name.lower()
        if not any(term in lowered for term in ("date", "time", "timestamp")):
            continue
        if pd.api.types.is_numeric_dtype(working[col]):
            continue
        parsed = pd.to_datetime(working[col], errors="coerce", format="mixed")
        ratio = float(parsed.notna().mean()) if len(parsed) else 0.0
        if ratio >= 0.7:
            candidates.append((int(ratio * 100), name, parsed))

    if not candidates:
        return None, working

    _, name, parsed = max(candidates, key=lambda item: item[0])
    working[name] = parsed
    return name, working


def _detect_grain(frame: pd.DataFrame, identifiers: list[str], domain: str) -> str:
    columns = [str(c).lower() for c in frame.columns]
    if domain == "sales":
        if any("order line" in c or "line number" in c for c in columns):
            return "order line"
        if any("order id" in c or c == "orderid" for c in columns):
            order_col = next((c for c in frame.columns if "order" in str(c).lower() and "id" in str(c).lower()), None)
            if order_col and frame[order_col].nunique(dropna=True) < len(frame):
                return "order line"
            return "order"
        if any("transaction" in c for c in columns):
            return "transaction"
    if domain == "marketing":
        if any("campaign" in c for c in columns) and any("date" in c or "time" in c for c in columns):
            return "campaign-period"
        return "campaign/event"
    if domain == "support":
        return "support ticket"
    if domain == "inventory":
        return "inventory snapshot"
    if identifiers:
        return "entity record"
    return "row"


class DataUnderstandingEngine:
    """Build a compact, deterministic semantic model for a dataframe."""

    def run(self, frame: pd.DataFrame) -> dict[str, Any]:
        date_column, working = _detect_date_column(frame)
        columns = [str(c) for c in working.columns]
        scores = {
            domain: sum(_name_score(col, terms) for col in columns)
            for domain, terms in DOMAIN_TERMS.items()
        }
        domain, best_score = max(scores.items(), key=lambda item: item[1], default=("generic", 0))
        total_score = sum(scores.values())
        confidence = min(0.99, best_score / max(total_score, 1)) if best_score else 0.0
        if best_score < 2 or confidence < 0.22:
            domain = "generic"
            confidence = min(confidence, 0.4)

        numeric = [
            str(col) for col in working.select_dtypes(include="number").columns
            if not is_identifier_column(str(col), working[col])
        ]
        identifiers = [
            str(col) for col in working.columns
            if is_identifier_column(str(col), working[col])
        ]
        dimensions = [
            str(col) for col in working.select_dtypes(exclude="number").columns
            if str(col) not in identifiers and working[col].nunique(dropna=True) <= max(100, len(working) * 0.5)
        ]
        dimensions.sort(
            key=lambda col: (_name_score(col, DIMENSION_TERMS), -working[col].nunique(dropna=True)),
            reverse=True,
        )

        measure_candidates = sorted(
            numeric,
            key=lambda col: (_name_score(col, MEASURE_TERMS), -working[col].nunique(dropna=True)),
            reverse=True,
        )

        measures: dict[str, str | None] = {
            "revenue": _find_column(measure_candidates, ("sales", "revenue", "amount", "value")),
            "profit": _find_column(measure_candidates, ("profit", "margin")),
            "cost": _find_column(measure_candidates, ("cost", "expense")),
            "quantity": _find_column(measure_candidates, ("quantity", "units", "volume")),
            "discount": _find_column(measure_candidates, ("discount",)),
            "spend": _find_column(measure_candidates, ("spend", "budget", "cost")),
            "impressions": _find_column(measure_candidates, ("impression", "reach")),
            "clicks": _find_column(measure_candidates, ("click",)),
            "conversions": _find_column(measure_candidates, ("conversion", "lead", "purchase")),
        }
        measures["primary"] = next(iter(measure_candidates), None)

        derived: list[str] = []
        if measures["profit"] and measures["revenue"]:
            derived.append("profit_margin")
        if measures["clicks"] and measures["impressions"]:
            derived.append("ctr")
        if measures["conversions"] and measures["clicks"]:
            derived.append("conversion_rate")
        if measures["spend"] and measures["clicks"]:
            derived.append("cpc")
        if measures["spend"] and measures["conversions"]:
            derived.append("cpa")
        if measures["revenue"] and measures["spend"]:
            derived.append("roas")

        return {
            "domain": domain,
            "domain_confidence": round(confidence, 3),
            "grain": _detect_grain(working, identifiers, domain),
            "date_column": date_column,
            "date_range": (
                {
                    "start": working[date_column].min().isoformat(),
                    "end": working[date_column].max().isoformat(),
                }
                if date_column and working[date_column].notna().any()
                else None
            ),
            "dimensions": dimensions[:10],
            "measures": measure_candidates[:15],
            "identifiers": identifiers[:15],
            "metric_columns": measures,
            "derived_metrics": derived,
            "rows": len(working),
            "columns": len(working.columns),
            "frame": working,
        }


def public_understanding(model: dict[str, Any]) -> dict[str, Any]:
    """Remove the dataframe before returning the model to API/UI code."""
    return {key: value for key, value in model.items() if key not in {"frame"}}
