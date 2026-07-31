import re
import duckdb
import pandas as pd


class SqlTool:
    """Executes read-only DuckDB SQL over registered DataFrames."""

    _ALLOWED_PATTERN = re.compile(r"^\s*select\b", re.IGNORECASE)
    _FORBIDDEN_KEYWORDS = re.compile(
        r"\b(insert|update|delete|drop|create|alter|truncate|copy|attach|detach|load|install|call|pragma)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _clean(query: str) -> str:
        """Strip markdown code fences and trailing semicolons."""
        query = query.strip()
        if query.startswith("```"):
            lines = query.splitlines()
            start = 1 if lines[0].startswith("```") else 0
            end = -1 if len(lines) > 1 and lines[-1].strip() == "```" else len(lines)
            query = "\n".join(lines[start:end]).strip()
        # Remove all semicolons (DuckDB doesn't need them and they enable statement chaining)
        query = query.replace(";", " ").strip()
        return query

    def _validate(self, query: str) -> None:
        if not self._ALLOWED_PATTERN.match(query):
            raise ValueError("Only SELECT queries are allowed.")
        if self._FORBIDDEN_KEYWORDS.search(query):
            raise ValueError("Query contains forbidden keyword.")

    def run(self, datasets: dict[str, pd.DataFrame], query: str) -> tuple[str, list[dict[str, object]]]:
        query = self._clean(query)
        self._validate(query)

        # Use a fresh per-request connection to avoid stale table registrations
        con = duckdb.connect(":memory:")
        try:
            for table_name, frame in datasets.items():
                con.register(table_name, frame)
            result_df = con.execute(query).df()
        finally:
            con.close()

        result_df = result_df.where(pd.notna, None).head(500)
        return query, result_df.to_dict(orient="records")


sql_tool = SqlTool()
