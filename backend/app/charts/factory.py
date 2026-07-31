import pandas as pd


class ChartFactory:
    SUPPORTED = {"bar", "line", "scatter", "histogram", "pie", "box", "heatmap"}

    def _resolve_column(self, frame: pd.DataFrame, name: str) -> str | None:
        """Case-insensitive column lookup with strip."""
        if not name:
            return None
        name = name.strip()
        # Exact match
        if name in frame.columns:
            return name
        # Case-insensitive match
        lower = name.lower()
        for col in frame.columns:
            if str(col).lower() == lower:
                return col
        # Partial match (last resort)
        for col in frame.columns:
            if lower in str(col).lower() or str(col).lower() in lower:
                return col
        return None

    def create(self, frame: pd.DataFrame, chart_type: str, x: str, y: str | None) -> dict:
        if chart_type not in self.SUPPORTED:
            raise ValueError(f"Unsupported chart type '{chart_type}'. Choose from: {', '.join(sorted(self.SUPPORTED))}")

        # Histogram and heatmap don't require x/y column validation the same way
        if chart_type == "histogram":
            x_col = self._resolve_column(frame, x)
            if x_col is None:
                # Fallback: use first numeric column
                numeric_cols = frame.select_dtypes(include="number").columns
                if len(numeric_cols) == 0:
                    raise ValueError(f"Column '{x}' not found and no numeric columns available for histogram.")
                x_col = numeric_cols[0]
            return {
                "data": [{"type": "histogram", "x": frame[x_col].dropna().tolist()}],
                "layout": {
                    "title": f"Distribution of {x_col}",
                    "paper_bgcolor": "transparent",
                    "plot_bgcolor": "transparent",
                },
            }

        if chart_type == "heatmap":
            corr = frame.select_dtypes(include="number").corr().round(3)
            if corr.empty:
                raise ValueError("Heatmap requires at least two numeric columns.")
            return {
                "data": [{
                    "type": "heatmap",
                    "z": corr.values.tolist(),
                    "x": corr.columns.tolist(),
                    "y": corr.index.tolist(),
                    "colorscale": "Viridis",
                }],
                "layout": {
                    "title": "Numeric Correlations",
                    "paper_bgcolor": "transparent",
                    "plot_bgcolor": "transparent",
                },
            }

        # Resolve x column
        x_col = self._resolve_column(frame, x)
        if x_col is None:
            raise ValueError(
                f"Column '{x}' not found. Available columns: {list(frame.columns)}"
            )

        # Resolve y column (optional for some charts)
        y_col = self._resolve_column(frame, y) if y else None

        subset_cols = [x_col] + ([y_col] if y_col else [])
        grouped = frame[subset_cols].dropna().head(500)

        if chart_type == "pie":
            trace = {
                "type": "pie",
                "labels": grouped[x_col].astype(str).tolist(),
                "values": grouped[y_col].tolist() if y_col else [1] * len(grouped),
            }
        else:
            trace: dict = {
                "type": chart_type,
                "x": grouped[x_col].astype(str).tolist(),
                "name": y_col or x_col,
            }
            if y_col:
                trace["y"] = grouped[y_col].tolist()

        return {
            "data": [trace],
            "layout": {
                "title": f"{chart_type.title()}: {y_col or 'count'} by {x_col}",
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
            },
        }
