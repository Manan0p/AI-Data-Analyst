"""Grounded, domain-aware automatic analysis.

The deterministic pass is the source of truth. Optional LLM providers may be
used later for wording, but they never choose business measures or invent the
facts shown to the user. This keeps chat and auto-insights useful when Redis,
Vector, Gemini, or Groq are unavailable.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.analytics.understanding import DataUnderstandingEngine, public_understanding
from app.schemas.contracts import AutoAnalysisResponse, DataQualityReport, InsightCard

logger = logging.getLogger(__name__)


def _safe(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return value


def _top_n(series: pd.Series, n: int = 10) -> list[dict[str, Any]]:
    counts = series.value_counts(dropna=True).head(n)
    return [{"label": str(k), "value": int(v)} for k, v in counts.items()]


def _fmt_number(value: Any, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return str(value)


def _fmt_money(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return str(value)


def _fmt_pct(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return str(value)


def _chart(title: str, chart_type: str, x: list[Any], y: list[Any], name: str) -> dict[str, Any]:
    trace: dict[str, Any] = {"type": chart_type, "x": [_safe(v) for v in x], "name": name}
    if chart_type not in {"pie", "histogram"}:
        trace["y"] = [_safe(v) for v in y]
    elif chart_type == "pie":
        trace = {"type": "pie", "labels": [_safe(v) for v in x], "values": [_safe(v) for v in y], "name": name}
    else:
        trace = {"type": "histogram", "x": [_safe(v) for v in y], "name": name}
    return {
        "title": title,
        "data": [trace],
        "layout": {
            "title": title,
            "paper_bgcolor": "transparent",
            "plot_bgcolor": "transparent",
        },
    }


def _metric(frame: pd.DataFrame, column: str | None, operation: str = "sum") -> float | None:
    if not column or column not in frame.columns:
        return None
    series = pd.to_numeric(frame[column], errors="coerce").dropna()
    if series.empty:
        return None
    if operation == "mean":
        return float(series.mean())
    if operation == "min":
        return float(series.min())
    if operation == "max":
        return float(series.max())
    return float(series.sum())


def _aggregate(frame: pd.DataFrame, dimension: str | None, measure: str | None) -> pd.DataFrame:
    if not dimension or not measure or dimension not in frame.columns or measure not in frame.columns:
        return pd.DataFrame()
    working = frame[[dimension, measure]].copy()
    working[measure] = pd.to_numeric(working[measure], errors="coerce")
    working = working.dropna(subset=[dimension, measure])
    if working.empty:
        return pd.DataFrame()
    return working.groupby(dimension, dropna=False)[measure].agg(["sum", "mean", "count"]).sort_values("sum", ascending=False)


def _period_aggregate(frame: pd.DataFrame, date_col: str | None, measure: str | None) -> pd.DataFrame:
    if not date_col or not measure or date_col not in frame.columns or measure not in frame.columns:
        return pd.DataFrame()
    working = frame[[date_col, measure]].copy()
    working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
    working[measure] = pd.to_numeric(working[measure], errors="coerce")
    working = working.dropna()
    if working.empty:
        return pd.DataFrame()
    working["period"] = working[date_col].dt.to_period("M").astype(str)
    return working.groupby("period")[measure].agg(["sum", "mean", "count"]).sort_index()


class StatisticalPass:
    """Derive semantic schema, quality, key metrics, and useful charts."""

    def run(self, dataset_id: str, frame: pd.DataFrame) -> dict[str, Any]:
        understanding = DataUnderstandingEngine().run(frame)
        working = understanding["frame"]
        measures = understanding["measures"]
        dimensions = understanding["dimensions"]
        metric_columns = understanding["metric_columns"]
        primary_measure = metric_columns.get("revenue") or metric_columns.get("primary")
        date_col = understanding.get("date_column")

        stats: dict[str, dict[str, Any]] = {}
        if measures:
            desc = working[measures].describe()
            stats = {
                col: {key: _safe(value) for key, value in desc[col].to_dict().items()}
                for col in measures
            }

        top_n: dict[str, list[dict[str, Any]]] = {}
        for col in dimensions[:8]:
            if working[col].nunique(dropna=True) <= 100:
                top_n[col] = _top_n(working[col], 10)

        charts: list[dict[str, Any]] = []
        primary_dimension = dimensions[0] if dimensions else None
        grouped = _aggregate(working, primary_dimension, primary_measure)
        if not grouped.empty:
            charts.append(_chart(
                f"{primary_measure} by {primary_dimension}",
                "bar",
                grouped.head(12).index.tolist(),
                grouped.head(12)["sum"].tolist(),
                primary_measure,
            ))

        periods = _period_aggregate(working, date_col, primary_measure)
        if not periods.empty:
            charts.append(_chart(
                f"Monthly {primary_measure} trend",
                "scatter",
                periods.index.tolist(),
                periods["sum"].tolist(),
                primary_measure,
            ))

        if primary_measure and primary_measure in working.columns:
            charts.append(_chart(
                f"Distribution of {primary_measure}",
                "histogram",
                [],
                pd.to_numeric(working[primary_measure], errors="coerce").dropna().head(2000).tolist(),
                primary_measure,
            ))

        meaningful_numeric = [col for col in measures if col in working.columns]
        if len(meaningful_numeric) >= 2:
            corr = working[meaningful_numeric].corr().round(3)
            charts.append({
                "title": "Meaningful numeric correlations",
                "data": [{
                    "type": "heatmap",
                    "z": corr.values.tolist(),
                    "x": corr.columns.tolist(),
                    "y": corr.index.tolist(),
                    "colorscale": "RdBu",
                }],
                "layout": {"title": "Meaningful numeric correlations", "paper_bgcolor": "transparent", "plot_bgcolor": "transparent"},
            })

        null_columns = [
            {"name": str(col), "null_pct": round(float(working[col].isna().mean() * 100), 2)}
            for col in working.columns
        ]
        null_columns.sort(key=lambda item: item["null_pct"], reverse=True)
        duplicate_rows = int(working.duplicated().sum())
        warnings: list[str] = []
        if duplicate_rows:
            warnings.append(f"{duplicate_rows:,} duplicate rows detected.")
        for item in null_columns:
            if item["null_pct"] >= 5:
                warnings.append(f"{item['name']} is {item['null_pct']:.1f}% null.")
        if not date_col and understanding["domain"] in {"sales", "marketing", "finance", "operations"}:
            warnings.append("No reliable date column was detected, so period trends are unavailable.")

        total_cols = len(working.columns)
        null_penalty = sum(item["null_pct"] for item in null_columns) / max(total_cols, 1)
        duplicate_penalty = min(20.0, duplicate_rows / max(len(working), 1) * 100)
        health_score = max(0.0, round(100.0 - null_penalty - duplicate_penalty, 1))
        quality = DataQualityReport(
            total_rows=len(working),
            total_columns=total_cols,
            duplicate_rows=duplicate_rows,
            null_columns=null_columns,
            healthy_columns=sum(1 for item in null_columns if item["null_pct"] < 5),
            health_score=health_score,
            warnings=warnings,
            domain=understanding["domain"],
            domain_confidence=understanding["domain_confidence"],
            grain=understanding["grain"],
            date_column=date_col,
        )

        key_metrics: dict[str, Any] = {
            "rows": len(working),
            "columns": len(working.columns),
            "domain": understanding["domain"],
            "grain": understanding["grain"],
        }
        if metric_columns.get("revenue"):
            key_metrics["revenue"] = _metric(working, metric_columns["revenue"])
        if metric_columns.get("profit"):
            key_metrics["profit"] = _metric(working, metric_columns["profit"])
        if metric_columns.get("quantity"):
            key_metrics["quantity"] = _metric(working, metric_columns["quantity"])
        if metric_columns.get("spend"):
            key_metrics["spend"] = _metric(working, metric_columns["spend"])
        if metric_columns.get("conversions"):
            key_metrics["conversions"] = _metric(working, metric_columns["conversions"])

        return {
            "understanding": understanding,
            "public_understanding": public_understanding(understanding),
            "stats": stats,
            "top_n": top_n,
            "charts": charts,
            "quality": quality,
            "key_metrics": key_metrics,
            "periods": periods,
        }


class DeterministicFallback:
    """Produce business findings without external services."""

    def build(
        self,
        frame: pd.DataFrame,
        stats: dict[str, dict[str, Any]],
        top_n: dict[str, list[dict[str, Any]]],
        quality: DataQualityReport,
        understanding: dict[str, Any] | None = None,
        periods: pd.DataFrame | None = None,
        charts: list[dict[str, Any]] | None = None,
        key_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        understanding = understanding or DataUnderstandingEngine().run(frame)
        metric_columns = understanding["metric_columns"]
        domain = understanding["domain"]
        dimensions = understanding["dimensions"]
        revenue_col = metric_columns.get("revenue")
        profit_col = metric_columns.get("profit")
        primary_dimension = dimensions[0] if dimensions else None
        cards: list[dict[str, Any]] = []
        recommendations: list[str] = []
        actions: list[dict[str, Any]] = []
        summary_parts = [
            f"This is a {domain} dataset with {quality.total_rows:,} {understanding['grain']} records and {quality.total_columns} columns.",
        ]

        if domain == "sales" and revenue_col:
            total_revenue = _metric(frame, revenue_col)
            summary_parts.append(f"Total {revenue_col} is {_fmt_money(total_revenue)}.")
            if profit_col:
                total_profit = _metric(frame, profit_col)
                margin = total_profit / total_revenue if total_profit is not None and total_revenue else None
                summary_parts.append(f"Total {profit_col} is {_fmt_money(total_profit)} ({_fmt_pct(margin)} margin).")

            grouped = _aggregate(frame, primary_dimension, revenue_col)
            if not grouped.empty:
                leader = grouped.iloc[0]
                label = str(grouped.index[0])
                cards.append({
                    "title": f"Top {primary_dimension} by {revenue_col}",
                    "body": f"{label} leads {revenue_col} with {_fmt_money(leader['sum'])} across {int(leader['count']):,} records.",
                    "metric": _fmt_money(leader["sum"]), "type": "stat", "importance": 0.95,
                    "severity": "positive", "evidence": {"dimension": primary_dimension, "label": label, "value": leader["sum"]},
                })
                recommendations.append(f"Protect and expand the {label} segment while checking whether its profit margin is also above average.")

            category_dimension = next((col for col in dimensions if col.lower().strip() == "category"), None)
            if category_dimension and category_dimension != primary_dimension:
                category_grouped = _aggregate(frame, category_dimension, revenue_col)
                if not category_grouped.empty:
                    category_leader = str(category_grouped.index[0])
                    cards.append({
                        "title": f"Top category by {revenue_col}",
                        "body": f"{category_leader} generated {_fmt_money(category_grouped.iloc[0]['sum'])} in {revenue_col}, the strongest category-level result.",
                        "metric": _fmt_money(category_grouped.iloc[0]["sum"]), "type": "stat", "importance": 0.94,
                        "severity": "positive", "evidence": {"dimension": category_dimension, "label": category_leader, "value": category_grouped.iloc[0]["sum"]},
                    })

            product_dimension = next((col for col in dimensions if "product" in col.lower()), None)
            if product_dimension:
                product_sales = _aggregate(frame, product_dimension, revenue_col)
                if not product_sales.empty:
                    top_product = str(product_sales.index[0])
                    cards.append({
                        "title": "Top product by sales",
                        "body": f"{top_product} is the leading product by {revenue_col} at {_fmt_money(product_sales.iloc[0]['sum'])}.",
                        "metric": _fmt_money(product_sales.iloc[0]["sum"]), "type": "distribution", "importance": 0.91,
                        "severity": "positive", "evidence": {"product": top_product, "sales": product_sales.iloc[0]["sum"]},
                    })

            if profit_col and primary_dimension:
                profit_grouped = _aggregate(frame, primary_dimension, profit_col)
                if not profit_grouped.empty:
                    worst = profit_grouped.sort_values("sum").iloc[0]
                    best = profit_grouped.sort_values("sum", ascending=False).iloc[0]
                    worst_label = str(profit_grouped.sort_values("sum").index[0])
                    best_label = str(profit_grouped.sort_values("sum", ascending=False).index[0])
                    cards.append({
                        "title": f"Profitability risk in {worst_label}",
                        "body": f"{worst_label} has the lowest total {profit_col} at {_fmt_money(worst['sum'])}; {best_label} leads at {_fmt_money(best['sum'])}.",
                        "metric": _fmt_money(worst["sum"]), "type": "anomaly", "importance": 0.93,
                        "severity": "critical" if float(worst["sum"]) < 0 else "warning",
                        "evidence": {"worst_segment": worst_label, "worst_profit": worst["sum"], "best_segment": best_label, "best_profit": best["sum"]},
                        "recommendation": f"Review pricing, discounting, and product mix in {worst_label}.",
                    })
                    if float(worst["sum"]) < 0:
                        recommendations.append(f"Review pricing and discounting in {worst_label}, which is loss-making on aggregate.")

            if profit_col and product_dimension:
                product_profit = _aggregate(frame, product_dimension, profit_col)
                if not product_profit.empty:
                    worst_product = str(product_profit.sort_values("sum").index[0])
                    worst_value = product_profit.sort_values("sum").iloc[0]["sum"]
                    cards.append({
                        "title": "Worst product by profit",
                        "body": f"{worst_product} lost {_fmt_money(worst_value)} in aggregate profit and should be reviewed before further promotion.",
                        "metric": _fmt_money(worst_value), "type": "anomaly", "importance": 0.96,
                        "severity": "critical" if float(worst_value) < 0 else "warning",
                        "evidence": {"product": worst_product, "profit": worst_value},
                        "recommendation": f"Inspect price, discount, and return patterns for {worst_product}.",
                    })
                    recommendations.append(f"Inspect price, discount, and return patterns for {worst_product} before promoting it further.")

            if periods is not None and not periods.empty:
                peak_period = periods["sum"].idxmax()
                worst_period = periods["sum"].idxmin()
                peak_value = periods.loc[peak_period, "sum"]
                worst_value = periods.loc[worst_period, "sum"]
                cards.append({
                    "title": "Peak and weakest sales periods",
                    "body": f"Peak {revenue_col} was {_fmt_money(peak_value)} in {peak_period}; the weakest period was {worst_period} at {_fmt_money(worst_value)}.",
                    "metric": str(peak_period), "type": "trend", "importance": 0.9,
                    "severity": "positive", "evidence": {"peak_period": peak_period, "peak_value": peak_value, "worst_period": worst_period, "worst_value": worst_value},
                })
                recommendations.append(f"Compare product mix and discounting between {peak_period} and {worst_period} before planning promotions.")

            discount_col = metric_columns.get("discount")
            if discount_col and profit_col:
                pair = frame[[discount_col, profit_col]].apply(pd.to_numeric, errors="coerce").dropna()
                if len(pair) >= 3:
                    corr = float(pair[discount_col].corr(pair[profit_col]))
                    if corr < -0.1:
                        cards.append({
                            "title": "Discount and profit move in opposite directions",
                            "body": f"The observed correlation between {discount_col} and {profit_col} is {corr:.2f}. This is an association, not proof of causation.",
                            "metric": f"r={corr:.2f}", "type": "correlation", "importance": 0.84,
                            "severity": "warning", "evidence": {"correlation": corr, "rows": len(pair)},
                            "recommendation": "Review high-discount transactions by product and region before increasing discount levels.",
                        })
                        recommendations.append("Review high-discount transactions by product and region; the negative association with profit warrants investigation.")

        elif domain == "marketing":
            spend_col = metric_columns.get("spend")
            impressions_col = metric_columns.get("impressions")
            clicks_col = metric_columns.get("clicks")
            conversions_col = metric_columns.get("conversions")
            if spend_col and clicks_col:
                total_spend = _metric(frame, spend_col)
                total_clicks = _metric(frame, clicks_col)
                cpc = total_spend / total_clicks if total_spend is not None and total_clicks else None
                summary_parts.append(f"Total spend is {_fmt_money(_metric(frame, spend_col))} with blended CPC {_fmt_money(cpc)}.")
            if impressions_col and clicks_col:
                total_clicks = _metric(frame, clicks_col)
                total_impressions = _metric(frame, impressions_col)
                ctr = total_clicks / total_impressions if total_clicks is not None and total_impressions else None
                cards.append({"title": "Click-through rate", "body": f"Blended CTR is {_fmt_pct(ctr)} based on clicks divided by impressions.", "metric": _fmt_pct(ctr), "type": "stat", "importance": 0.9, "severity": "info", "evidence": {"ctr": ctr}})
            if clicks_col and conversions_col:
                total_conversions = _metric(frame, conversions_col)
                total_clicks = _metric(frame, clicks_col)
                cvr = total_conversions / total_clicks if total_conversions is not None and total_clicks else None
                cards.append({"title": "Conversion efficiency", "body": f"Blended conversion rate is {_fmt_pct(cvr)} based on conversions divided by clicks.", "metric": _fmt_pct(cvr), "type": "trend", "importance": 0.88, "severity": "info", "evidence": {"conversion_rate": cvr}})
            channel = next((col for col in dimensions if "channel" in col.lower() or "campaign" in col.lower()), primary_dimension)
            if channel and spend_col and conversions_col:
                grouped = frame.copy()
                grouped[spend_col] = pd.to_numeric(grouped[spend_col], errors="coerce")
                grouped[conversions_col] = pd.to_numeric(grouped[conversions_col], errors="coerce")
                grouped = grouped.dropna(subset=[channel, spend_col, conversions_col])
                if not grouped.empty:
                    by_channel = grouped.groupby(channel).agg(spend=(spend_col, "sum"), conversions=(conversions_col, "sum"))
                    by_channel["cpa"] = by_channel["spend"] / by_channel["conversions"].replace(0, pd.NA)
                    by_channel = by_channel.dropna(subset=["cpa"]).sort_values("cpa")
                    if not by_channel.empty:
                        best = str(by_channel.index[0])
                        worst = str(by_channel.index[-1])
                        cards.append({"title": f"Best and weakest {channel}", "body": f"{best} has the lowest CPA at {_fmt_money(by_channel.iloc[0]['cpa'])}; {worst} has the highest at {_fmt_money(by_channel.iloc[-1]['cpa'])}.", "metric": best, "type": "distribution", "importance": 0.92, "severity": "positive", "evidence": {"best": best, "worst": worst}})
                        recommendations.append(f"Protect the {best} allocation and review the conversion economics of {worst} before adding budget.")
        else:
            if primary_dimension and understanding["metric_columns"].get("primary"):
                measure = understanding["metric_columns"]["primary"]
                grouped = _aggregate(frame, primary_dimension, measure)
                if not grouped.empty:
                    label = str(grouped.index[0])
                    cards.append({"title": f"Largest {measure} segment", "body": f"{label} has the largest aggregate {measure} at {_fmt_number(grouped.iloc[0]['sum'])}.", "metric": _fmt_number(grouped.iloc[0]['sum']), "type": "stat", "importance": 0.8, "severity": "info", "evidence": {"dimension": primary_dimension, "label": label}})
            recommendations.extend([
                "Validate the detected dataset grain before making business decisions.",
                "Investigate the highest-impact dimensions and compare their distributions over time if a date column is available.",
            ])

        if quality.warnings:
            cards.append({
                "title": "Data quality limitations",
                "body": " ".join(quality.warnings[:3]),
                "metric": f"{len(quality.warnings)} warning(s)",
                "type": "anomaly", "importance": 0.86, "severity": "warning",
                "evidence": {"warnings": quality.warnings},
            })

        if not cards:
            cards.append({
                "title": "Dataset overview",
                "body": f"No domain-specific findings were strong enough to report. The dataset contains {quality.total_rows:,} records.",
                "metric": f"{quality.total_rows:,}", "type": "stat", "importance": 0.5, "severity": "info",
            })

        return {
            "executive_summary": " ".join(summary_parts),
            "trend_story": cards[2]["body"] if len(cards) > 2 else None,
            "insight_cards": cards[:8],
            "recommendations": list(dict.fromkeys(recommendations))[:6],
            "actions": [{"priority": "high" if card.get("severity") == "critical" else "medium", "action": card.get("recommendation") or rec} for card, rec in zip(cards, list(dict.fromkeys(recommendations)))] if recommendations else [],
            "anomaly_note": next((card["body"] for card in cards if card.get("severity") in {"warning", "critical"}), None),
        }


# Backwards-compatible name used by earlier tests and callers.
DeterministicNarrative = DeterministicFallback


class AutoAnalysisEngine:
    def __init__(self):
        self._stat = StatisticalPass()
        self._fallback = DeterministicFallback()

    def run(self, dataset_id: str, frame: pd.DataFrame, owner_id: str | None = None) -> AutoAnalysisResponse:
        stat_result = self._stat.run(dataset_id, frame)
        understanding = stat_result["understanding"]
        fallback = self._fallback.build(
            understanding["frame"],
            stat_result["stats"],
            stat_result["top_n"],
            stat_result["quality"],
            understanding=understanding,
            periods=stat_result["periods"],
            charts=stat_result["charts"],
            key_metrics=stat_result["key_metrics"],
        )
        cards = [InsightCard(**card) for card in fallback["insight_cards"]]
        return AutoAnalysisResponse(
            dataset_id=dataset_id,
            executive_summary=fallback["executive_summary"],
            trend_story=fallback.get("trend_story"),
            insights=cards,
            charts=stat_result["charts"],
            recommendations=fallback["recommendations"],
            actions=fallback.get("actions", []),
            key_metrics=stat_result["key_metrics"],
            domain=understanding["domain"],
            domain_confidence=understanding["domain_confidence"],
            grain=understanding["grain"],
            data_quality=stat_result["quality"],
            anomaly_note=fallback.get("anomaly_note"),
            generated_at=datetime.now(timezone.utc).isoformat(),
            gemini_used=False,
            groq_used=False,
            status="completed",
        )

    def run_and_persist(self, dataset_id: str, frame: pd.DataFrame, owner_id: str | None = None) -> AutoAnalysisResponse:
        from app.database.connection import SessionLocal
        from app.database.models import AutoAnalysisReportModel

        report = self.run(dataset_id, frame, owner_id)
        db = SessionLocal()
        try:
            existing = db.query(AutoAnalysisReportModel).filter(
                AutoAnalysisReportModel.dataset_id == dataset_id,
                AutoAnalysisReportModel.owner_id == owner_id,
            ).first()
            if existing:
                existing.report_json = report.model_dump()
                existing.gemini_used = "false"
                existing.groq_used = "false"
                existing.updated_at = datetime.now(timezone.utc)
            else:
                db.add(AutoAnalysisReportModel(
                    dataset_id=dataset_id,
                    owner_id=owner_id,
                    report_json=report.model_dump(),
                    gemini_used="false",
                    groq_used="false",
                ))
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to persist auto-analysis report for %s", dataset_id)
        finally:
            db.close()
        return report
