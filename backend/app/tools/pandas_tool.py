import ast
import pandas as pd


class PandasTool:
    FORBIDDEN = ("__", "import", "open", "exec", "eval", "os.", "sys.", "builtins", "subprocess")

    @staticmethod
    def _strip_fences(code: str) -> str:
        """Remove markdown code fences."""
        code = code.strip()
        if code.startswith("```"):
            lines = code.splitlines()
            start = 1 if lines[0].startswith("```") else 0
            end = -1 if len(lines) > 1 and lines[-1].strip() == "```" else len(lines)
            code = "\n".join(lines[start:end]).strip()
        return code

    @staticmethod
    def _strip_assignment(code: str) -> str:
        """Strip leading variable assignment (e.g. 'result = df[...]' → 'df[...]')."""
        LVALUE_NAMES = {"df", "result", "res", "out", "frame", "data", "output"}
        if "=" not in code:
            return code
        lhs, _, rhs = code.partition("=")
        lhs = lhs.strip()
        # Only strip simple name assignments, not ==, >=, <=, !=
        if lhs in LVALUE_NAMES and not lhs.endswith(("!", "<", ">", "=")):
            return rhs.strip()
        return code

    def _clean(self, code: str) -> str:
        code = self._strip_fences(code)
        code = self._strip_assignment(code)
        return code

    def _check_safety(self, code: str) -> None:
        lowered = code.lower()
        for token in self.FORBIDDEN:
            if token in lowered:
                raise ValueError(f"Unsafe expression: forbidden token '{token}'")

    def run(self, frame: pd.DataFrame, code: str) -> list[dict[str, object]]:
        code = self._clean(code)
        self._check_safety(code)

        env = {"pd": pd, "__builtins__": {}}
        local = {"df": frame.copy()}

        # Try single-expression eval first (most common from LLM)
        try:
            tree = ast.parse(code, mode="eval")
            result = eval(compile(tree, "<pandas>", "eval"), env, local)
        except SyntaxError:
            # Fall back to exec for multi-line code
            tree = ast.parse(code, mode="exec")
            exec(compile(tree, "<pandas>", "exec"), env, local)
            # Prefer explicit 'result' variable; then look for a modified 'df'
            result = local.get("result") or local.get("df")

        if result is None:
            raise ValueError("Expression did not return a value. Assign your result to 'result'.")
        if isinstance(result, pd.Series):
            result = result.reset_index().rename(columns={0: "value"}) if result.name is None else result.to_frame()
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Expression must return a DataFrame or Series, got {type(result).__name__}")

        return result.head(500).where(pd.notna, None).to_dict(orient="records")
