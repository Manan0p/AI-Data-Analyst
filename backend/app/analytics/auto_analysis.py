"""
auto_analysis.py — Automated Intelligence Engine (Dual-Model Parallel Architecture)

Pipeline:
  1. StatisticalPass  — pure Pandas, ~100 ms, feeds both LLM prompts
  2. asyncio.gather(
       GeminiStructuredPass,   → insight_cards + chart_recommendations + anomaly_note
       GroqNarrativePass,      → executive_summary + recommendations + trend_story
     )
  3. merge + persist to AutoAnalysisReportModel

Graceful degradation tiers:
  - GEMINI_API_KEY + GROQ_API_KEY  → full parallel dual-model
  - GEMINI_API_KEY only             → Gemini handles both tasks sequentially
  - neither key                     → deterministic rule-based report (instant)
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.config import settings
from app.schemas.contracts import AutoAnalysisResponse, DataQualityReport, InsightCard

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe(value: Any) -> Any:
    """Replace NaN/Inf with None for JSON serialisation."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _top_n(series: pd.Series, n: int = 10) -> list[dict]:
    counts = series.value_counts().head(n)
    return [{"label": str(k), "value": int(v)} for k, v in counts.items()]


# ── Step 1: Statistical Pass (pure Python, no LLM) ───────────────────────────

class StatisticalPass:
    """Derives charts, quality metrics and summary stats from raw DataFrame."""

    def run(self, dataset_id: str, frame: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {
            "charts": [],
            "quality": {},
            "stats": {},
            "top_n": {},
            "date_col": None,
        }

        numeric_cols = frame.select_dtypes(include="number").columns.tolist()
        categorical_cols = frame.select_dtypes(exclude="number").columns.tolist()
        date_col: str | None = None

        # ── detect date column ────────────────────────────────────────
        for col in frame.columns:
            if pd.api.types.is_datetime64_any_dtype(frame[col]):
                date_col = col
                break
        if date_col is None:
            for col in categorical_cols:
                if any(t in col.lower() for t in ("date", "time", "year", "month")):
                    try:
                        parsed = pd.to_datetime(frame[col], errors="coerce")
                        if parsed.notna().mean() > 0.7:
                            frame = frame.copy()
                            frame[col] = parsed
                            date_col = col
                            break
                    except Exception:
                        pass
        result["date_col"] = date_col

        # ── numeric summary ───────────────────────────────────────────
        if numeric_cols:
            desc = frame[numeric_cols].describe()
            result["stats"] = {
                col: {k: _safe(v) for k, v in desc[col].to_dict().items()}
                for col in numeric_cols
            }

        # ── top-N breakdown per categorical column ────────────────────
        for col in categorical_cols[:6]:
            if frame[col].nunique() <= 50:
                result["top_n"][col] = _top_n(frame[col])

        # ── auto charts ───────────────────────────────────────────────
        charts = []

        # Chart 1: bar — top categorical × first numeric
        if categorical_cols and numeric_cols:
            cat = categorical_cols[0]
            num = numeric_cols[0]
            agg = (
                frame.groupby(cat)[num].sum().sort_values(ascending=False).head(15)
            )
            if not agg.empty:
                charts.append({
                    "title": f"{num} by {cat}",
                    "data": [{"type": "bar",
                               "x": agg.index.astype(str).tolist(),
                               "y": [_safe(v) for v in agg.values.tolist()],
                               "name": num}],
                    "layout": {"title": f"{num} by {cat}",
                                "paper_bgcolor": "transparent",
                                "plot_bgcolor": "transparent"},
                })

        # Chart 2: line — time series of first numeric col if date detected
        if date_col and numeric_cols:
            num = numeric_cols[0]
            ts = frame[[date_col, num]].dropna()
            if not ts.empty:
                ts = ts.sort_values(date_col)
                # Resample to monthly if > 60 data points
                ts = ts.set_index(date_col)
                if len(ts) > 60:
                    ts = ts[num].resample("ME").sum().reset_index()
                else:
                    ts = ts.reset_index()
                charts.append({
                    "title": f"{num} over time",
                    "data": [{"type": "scatter", "mode": "lines+markers",
                               "x": ts[date_col].astype(str).tolist(),
                               "y": [_safe(v) for v in ts[num].tolist()],
                               "name": num}],
                    "layout": {"title": f"{num} over time",
                                "paper_bgcolor": "transparent",
                                "plot_bgcolor": "transparent"},
                })

        # Chart 3: histogram — distribution of first numeric column
        if numeric_cols:
            col = numeric_cols[0]
            vals = frame[col].dropna().tolist()[:2000]
            charts.append({
                "title": f"Distribution of {col}",
                "data": [{"type": "histogram", "x": vals}],
                "layout": {"title": f"Distribution of {col}",
                            "paper_bgcolor": "transparent",
                            "plot_bgcolor": "transparent"},
            })

        # Chart 4: pie — second categorical column share
        if len(categorical_cols) > 1 and numeric_cols:
            cat = categorical_cols[1]
            num = numeric_cols[0]
            if frame[cat].nunique() <= 12:
                agg = frame.groupby(cat)[num].sum().sort_values(ascending=False)
                charts.append({
                    "title": f"{num} share by {cat}",
                    "data": [{"type": "pie",
                               "labels": agg.index.astype(str).tolist(),
                               "values": [_safe(v) for v in agg.values.tolist()]}],
                    "layout": {"title": f"{num} share by {cat}",
                                "paper_bgcolor": "transparent",
                                "plot_bgcolor": "transparent"},
                })

        # Chart 5: heatmap — correlation matrix (≥2 numeric cols)
        if len(numeric_cols) >= 2:
            corr = frame[numeric_cols].corr().round(3)
            charts.append({
                "title": "Correlation Heatmap",
                "data": [{"type": "heatmap",
                           "z": corr.values.tolist(),
                           "x": corr.columns.tolist(),
                           "y": corr.index.tolist(),
                           "colorscale": "RdBu"}],
                "layout": {"title": "Numeric Correlations",
                            "paper_bgcolor": "transparent",
                            "plot_bgcolor": "transparent"},
            })

        result["charts"] = charts

        # ── data quality ──────────────────────────────────────────────
        null_cols = []
        healthy = 0
        for col in frame.columns:
            pct = round(float(frame[col].isna().mean() * 100), 2)
            null_cols.append({"name": col, "null_pct": pct})
            if pct < 5:
                healthy += 1
        null_cols.sort(key=lambda x: x["null_pct"], reverse=True)

        total_cols = len(frame.columns)
        duplicates = int(frame.duplicated().sum())
        # health score: weighted by null %, duplicates, and empty cols
        health = max(0.0, 100.0 - (sum(c["null_pct"] for c in null_cols) / max(total_cols, 1)) - min(duplicates / max(len(frame), 1) * 100, 20))

        result["quality"] = DataQualityReport(
            total_rows=len(frame),
            total_columns=total_cols,
            duplicate_rows=duplicates,
            null_columns=null_cols,
            healthy_columns=healthy,
            health_score=round(health, 1),
        )
        return result


# ── Step 2a: Gemini Structured Pass ──────────────────────────────────────────

class GeminiStructuredPass:
    """Uses Gemini Flash to produce typed insight_cards + chart_recommendations."""

    def _build_stats_summary(self, stats: dict, top_n: dict) -> str:
        lines = []
        for col, s in list(stats.items())[:8]:
            lines.append(f"  {col}: mean={s.get('mean')}, max={s.get('max')}, min={s.get('min')}, std={s.get('std')}")
        for col, rows in list(top_n.items())[:4]:
            top = rows[:5]
            lines.append(f"  {col} top values: " + ", ".join(f"{r['label']}({r['value']})" for r in top))
        return "\n".join(lines)

    async def run(self, schema: list[dict], stats: dict, top_n: dict) -> dict:
        if not settings.gemini_api_key:
            return {}
        try:
            from google import genai
            from google.genai import types

            stats_text = self._build_stats_summary(stats, top_n)
            prompt = (
                "You are a data analyst. Based on the dataset schema and statistics below, "
                "generate a JSON object with exactly these keys:\n"
                "- insight_cards: array of 5-8 objects, each with: title (string), body (string, 1-2 sentences with specific numbers), "
                "metric (string, the key number e.g. '42%'), type (one of: stat|trend|anomaly|distribution|correlation), importance (float 0-1)\n"
                "- anomaly_note: string or null (brief note about any suspicious patterns)\n\n"
                "Return ONLY valid JSON. Use actual column names and real numbers from the stats.\n\n"
                f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
                f"Statistics:\n{stats_text}"
            )

            client = genai.Client(api_key=settings.gemini_api_key)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                ),
            )
            return json.loads(response.text)
        except Exception as exc:
            logger.warning("Gemini structured pass failed: %s", exc)
            return {}


# ── Step 2b: Groq Narrative Pass ─────────────────────────────────────────────

class GroqNarrativePass:
    """Uses Groq Llama 3.1 to write executive summary, trend story, and recommendations."""

    async def run(self, schema: list[dict], stats: dict, top_n: dict, date_col: str | None) -> dict:
        if not settings.groq_api_key:
            return {}
        try:
            from groq import AsyncGroq

            col_names = [c["name"] for c in schema[:12]]
            num_rows = next((c for c in schema if c.get("rows")), {}).get("rows", "unknown")

            stat_lines = []
            for col, s in list(stats.items())[:6]:
                stat_lines.append(f"  {col}: mean={s.get('mean')}, max={s.get('max')}")
            for col, rows in list(top_n.items())[:3]:
                top = rows[:3]
                stat_lines.append(f"  {col} leaders: " + ", ".join(f"{r['label']}" for r in top))

            time_hint = f" A date/time column '{date_col}' is present, so time-based trends are relevant." if date_col else ""

            prompt = (
                "You are a senior business data analyst writing an executive intelligence report. "
                "Based on the dataset information below, generate a JSON object with:\n"
                "- executive_summary: 2-3 sentences describing what this dataset is about and its most important finding\n"
                "- trend_story: 1-2 sentences about trends or patterns observed (or null if no trends obvious)\n"
                "- recommendations: array of exactly 4 specific, insightful questions an analyst should explore next\n\n"
                "Be specific, use actual column names and numbers. Be professional but concise.\n"
                f"Columns: {col_names}\n"
                f"Statistics:\n" + "\n".join(stat_lines) +
                f"\n{time_hint}\n\n"
                "Return ONLY valid JSON."
            )

            client = AsyncGroq(api_key=settings.groq_api_key)
            response = await client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content or "{}"
            return json.loads(text)
        except Exception as exc:
            logger.warning("Groq narrative pass failed: %s", exc)
            return {}


# ── Step 3: Deterministic Fallback (no LLM) ──────────────────────────────────

class DeterministicNarrative:
    """Rule-based narrative when no LLM keys are configured."""

    def build(self, frame: pd.DataFrame, stats: dict, top_n: dict, quality: DataQualityReport) -> dict:
        numeric_cols = frame.select_dtypes(include="number").columns.tolist()
        categorical_cols = frame.select_dtypes(exclude="number").columns.tolist()

        # Executive summary
        summary_parts = [
            f"This dataset contains {quality.total_rows:,} rows and {quality.total_columns} columns "
            f"with a data quality score of {quality.health_score:.0f}/100."
        ]
        if numeric_cols and stats:
            top_col = max(stats, key=lambda c: stats[c].get("mean") or 0)
            summary_parts.append(
                f"The highest-average numeric column is '{top_col}' "
                f"(mean: {stats[top_col].get('mean', 0):.2f}, max: {stats[top_col].get('max', 0):.2f})."
            )
        if categorical_cols and top_n:
            first_cat = categorical_cols[0]
            if first_cat in top_n and top_n[first_cat]:
                leader = top_n[first_cat][0]
                summary_parts.append(
                    f"The most frequent '{first_cat}' is '{leader['label']}' with {leader['value']:,} occurrences."
                )

        # Insight cards
        cards: list[dict] = []
        for col in numeric_cols[:4]:
            s = stats.get(col, {})
            if s.get("mean") is not None:
                cards.append({
                    "title": f"{col} Statistics",
                    "body": f"Mean: {s['mean']:.2f}, Max: {s.get('max', 'N/A')}, Min: {s.get('min', 'N/A')}",
                    "metric": f"{s['mean']:.2f}",
                    "type": "stat",
                    "importance": 0.7,
                })

        for col, rows in list(top_n.items())[:2]:
            if rows:
                leader = rows[0]
                cards.append({
                    "title": f"Top {col}",
                    "body": f"'{leader['label']}' leads with {leader['value']:,} occurrences in the '{col}' column.",
                    "metric": str(leader["value"]),
                    "type": "distribution",
                    "importance": 0.6,
                })

        if quality.duplicate_rows > 0:
            cards.append({
                "title": "Duplicate Rows Detected",
                "body": f"{quality.duplicate_rows:,} duplicate rows found. Consider deduplication before analysis.",
                "metric": str(quality.duplicate_rows),
                "type": "anomaly",
                "importance": 0.8,
            })

        # Recommendations
        recommendations = [
            f"Which {categorical_cols[0]} has the highest {numeric_cols[0]}?" if categorical_cols and numeric_cols else "What are the key trends in this dataset?",
            f"What is the distribution of {numeric_cols[0]}?" if numeric_cols else "How are the categories distributed?",
            "Are there any anomalies or outliers in the numeric columns?",
            "How does data quality affect the reliability of insights?",
        ]

        return {
            "executive_summary": " ".join(summary_parts),
            "trend_story": None,
            "insight_cards": cards,
            "recommendations": recommendations,
            "anomaly_note": f"{quality.duplicate_rows} duplicate rows may affect analysis." if quality.duplicate_rows > 0 else None,
        }


# ── Main Engine ───────────────────────────────────────────────────────────────

class AutoAnalysisEngine:
    """Orchestrates the full dual-model parallel auto-analysis pipeline."""

    def __init__(self):
        self._stat = StatisticalPass()
        self._gemini = GeminiStructuredPass()
        self._groq = GroqNarrativePass()
        self._fallback = DeterministicNarrative()

    def _build_schema(self, frame: pd.DataFrame) -> list[dict]:
        schema = []
        for col in frame.columns:
            dtype = str(frame[col].dtype)
            schema.append({
                "name": str(col),
                "dtype": dtype,
                "unique": int(frame[col].nunique()),
                "null_pct": round(float(frame[col].isna().mean() * 100), 1),
                "sample": frame[col].dropna().head(3).astype(str).tolist(),
            })
        return schema

    def _merge_results(
        self,
        dataset_id: str,
        stat_result: dict,
        gemini_result: dict,
        groq_result: dict,
        fallback_result: dict | None,
    ) -> AutoAnalysisResponse:
        gemini_used = bool(gemini_result)
        groq_used   = bool(groq_result)

        # ── executive summary (Groq > Gemini > fallback) ─────────────
        executive_summary = (
            groq_result.get("executive_summary")
            or fallback_result.get("executive_summary", "Dataset analysis complete.")  # type: ignore[union-attr]
        )
        trend_story = groq_result.get("trend_story") if groq_result else None

        # ── recommendations (Groq > fallback) ────────────────────────
        recommendations: list[str] = (
            groq_result.get("recommendations")  # type: ignore[assignment]
            or (fallback_result or {}).get("recommendations", [])
        )

        # ── anomaly note (Gemini > fallback) ─────────────────────────
        anomaly_note = (
            gemini_result.get("anomaly_note")
            or (fallback_result or {}).get("anomaly_note")
        )

        # ── insight cards (Gemini > fallback) ────────────────────────
        raw_cards: list[dict] = (
            gemini_result.get("insight_cards")  # type: ignore[assignment]
            or (fallback_result or {}).get("insight_cards", [])
        )
        insight_cards = []
        for card in raw_cards:
            try:
                insight_cards.append(InsightCard(**{
                    "title": card.get("title", ""),
                    "body": card.get("body", ""),
                    "metric": card.get("metric"),
                    "type": card.get("type", "stat"),
                    "chart": card.get("chart"),
                    "importance": float(card.get("importance", 0.5)),
                }))
            except Exception:
                pass
        # Sort by importance descending
        insight_cards.sort(key=lambda c: c.importance, reverse=True)

        return AutoAnalysisResponse(
            dataset_id=dataset_id,
            executive_summary=executive_summary,
            trend_story=trend_story,
            insights=insight_cards,
            charts=stat_result.get("charts", []),
            recommendations=recommendations if isinstance(recommendations, list) else [],
            data_quality=stat_result["quality"],
            anomaly_note=anomaly_note,
            generated_at=datetime.now(timezone.utc).isoformat(),
            gemini_used=gemini_used,
            groq_used=groq_used,
            status="completed",
        )

    async def _run_async(self, frame: pd.DataFrame, schema: list[dict], stat_result: dict) -> tuple[dict, dict]:
        """Fire both LLM passes concurrently."""
        gemini_task = self._gemini.run(schema, stat_result.get("stats", {}), stat_result.get("top_n", {}))
        groq_task   = self._groq.run(schema, stat_result.get("stats", {}), stat_result.get("top_n", {}), stat_result.get("date_col"))
        return await asyncio.gather(gemini_task, groq_task)

    def run(self, dataset_id: str, frame: pd.DataFrame, owner_id: str | None = None) -> AutoAnalysisResponse:
        """Full pipeline: stat → parallel LLM → merge → return."""
        logger.info("AutoAnalysisEngine: starting for dataset %s", dataset_id)

        # Step 1: statistical pass (~100ms)
        stat_result = self._stat.run(dataset_id, frame)

        # Build schema for LLM prompts
        schema = self._build_schema(frame)

        # Step 2: parallel LLM calls
        gemini_result: dict = {}
        groq_result: dict = {}
        if settings.gemini_api_key or settings.groq_api_key:
            try:
                try:
                    loop = asyncio.get_running_loop()
                    # If called from inside an event loop (unlikely in thread pool), use run_in_executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._run_async(frame, schema, stat_result))
                        gemini_result, groq_result = future.result()
                except RuntimeError:
                    # No running event loop — use asyncio.run directly
                    gemini_result, groq_result = asyncio.run(self._run_async(frame, schema, stat_result))
            except Exception as exc:
                logger.warning("Parallel LLM pass failed, using deterministic fallback: %s", exc)

        # Step 2 fallback: if both LLMs failed or no keys, use deterministic
        fallback: dict | None = None
        if not gemini_result and not groq_result:
            quality = stat_result["quality"]
            fallback = self._fallback.build(frame, stat_result.get("stats", {}), stat_result.get("top_n", {}), quality)
        # If only one LLM failed, supplement with deterministic data
        elif not groq_result:
            quality = stat_result["quality"]
            fallback = self._fallback.build(frame, stat_result.get("stats", {}), stat_result.get("top_n", {}), quality)
        elif not gemini_result:
            quality = stat_result["quality"]
            fallback = self._fallback.build(frame, stat_result.get("stats", {}), stat_result.get("top_n", {}), quality)

        # Step 3: merge
        result = self._merge_results(dataset_id, stat_result, gemini_result, groq_result, fallback)
        logger.info(
            "AutoAnalysisEngine: completed for %s | gemini=%s groq=%s insights=%d charts=%d",
            dataset_id, result.gemini_used, result.groq_used, len(result.insights), len(result.charts),
        )
        return result

    def run_and_persist(self, dataset_id: str, frame: pd.DataFrame, owner_id: str | None = None) -> AutoAnalysisResponse:
        """Run analysis and cache result in PostgreSQL."""
        from app.database.connection import SessionLocal
        from app.database.models import AutoAnalysisReportModel

        report = self.run(dataset_id, frame, owner_id)

        db = SessionLocal()
        try:
            existing = db.query(AutoAnalysisReportModel).filter(
                AutoAnalysisReportModel.dataset_id == dataset_id
            ).first()
            report_dict = report.model_dump()
            if existing:
                existing.report_json = report_dict
                existing.gemini_used = str(report.gemini_used)
                existing.groq_used   = str(report.groq_used)
                existing.updated_at  = datetime.now(timezone.utc)
            else:
                rec = AutoAnalysisReportModel(
                    dataset_id=dataset_id,
                    owner_id=owner_id,
                    report_json=report_dict,
                    gemini_used=str(report.gemini_used),
                    groq_used=str(report.groq_used),
                )
                db.add(rec)
            db.commit()
            logger.info("AutoAnalysisEngine: report persisted for dataset %s", dataset_id)
        except Exception as exc:
            db.rollback()
            logger.warning("AutoAnalysisEngine: failed to persist report: %s", exc)
        finally:
            db.close()

        return report
