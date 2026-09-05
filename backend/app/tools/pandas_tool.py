import ast
import concurrent.futures
from typing import Any
import pandas as pd


# Node types the expression is allowed to contain. Anything else -> reject.
ALLOWED_NODES = (
    ast.Expression, ast.Module, ast.Load,
    ast.Name, ast.Attribute, ast.Constant,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv,
    ast.And, ast.Or, ast.Not, ast.Invert, ast.USub, ast.UAdd,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
    ast.Call, ast.keyword,
    ast.Subscript, ast.Slice, getattr(ast, "Index", ast.AST),
    ast.List, ast.Tuple, ast.Dict,
    ast.Assign, ast.Store,  # only for the single top-level "result = ..." pattern
)

# Method/function names allowed to be *called*. Everything else is rejected
# even if the node type is otherwise fine — this stops df.to_csv, df.eval,
# df.query with injected code, etc.
ALLOWED_CALL_NAMES = {
    "head", "tail", "sort_values", "groupby", "agg", "sum", "mean", "median",
    "std", "min", "max", "count", "nunique", "value_counts", "describe",
    "reset_index", "rename", "astype", "round", "sort_index", "drop_duplicates",
    "isna", "notna", "fillna", "dropna", "corr", "pivot_table", "merge",
    "to_frame", "unique", "size", "cumsum", "abs", "quantile",
    "to_datetime", "qcut", "cut", "concat", "isin", "nlargest", "nsmallest",
    "clip", "diff", "pct_change", "rank", "copy", "filter", "select_dtypes"
}

ALLOWED_BUILTIN_CALLS = {"len", "round", "abs", "sum", "min", "max", "int", "float", "str", "bool"}

# Permitted identifiers in loaded variable expressions
ALLOWED_NAME_IDS = {
    "df", "pd", "result", "res", "out", "frame", "data", "output",
    "len", "round", "abs", "sum", "min", "max", "int", "float", "str", "bool",
    "True", "False", "None"
}

ALLOWED_ASSIGN_TARGETS = {"result", "res", "out", "frame", "data", "output", "df"}

FORBIDDEN_NAME_PREFIXES = ("__",)


class UnsafeExpression(ValueError):
    """Raised when an expression violates safety restrictions."""
    pass


def validate_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise UnsafeExpression(f"Disallowed syntax: {type(node).__name__}")
        if isinstance(node, ast.Attribute) and node.attr.startswith(FORBIDDEN_NAME_PREFIXES):
            raise UnsafeExpression(f"Disallowed attribute: {node.attr}")
        if isinstance(node, ast.Name) and node.id.startswith(FORBIDDEN_NAME_PREFIXES):
            raise UnsafeExpression(f"Disallowed name: {node.id}")
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id not in ALLOWED_ASSIGN_TARGETS:
                    raise UnsafeExpression(f"Disallowed assignment target: {target.id}")
        if isinstance(node, ast.Name):
            if isinstance(getattr(node, "ctx", None), ast.Load):
                if node.id not in ALLOWED_NAME_IDS:
                    raise UnsafeExpression(f"Disallowed variable: {node.id}")
        if isinstance(node, ast.Call):
            func = node.func
            # Only allow df.method(...) calls or bare pd.<fn>(...) — never a bare
            # dynamic call like getattr(...)(...) or a call on a Name that isn't pd/df.
            if isinstance(func, ast.Attribute):
                if func.attr not in ALLOWED_CALL_NAMES:
                    raise UnsafeExpression(f"Disallowed method call: {func.attr}")
            elif isinstance(func, ast.Name):
                if func.id not in ALLOWED_BUILTIN_CALLS:
                    raise UnsafeExpression(f"Disallowed function call: {func.id}")
            else:
                raise UnsafeExpression("Disallowed call target")


class PandasTool:
    DEFAULT_TIMEOUT: float = 5.0  # seconds

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

    def _execute_with_timeout(self, func: Any, timeout: float = 5.0) -> Any:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Pandas expression execution timed out after {timeout}s")

    def run(self, frame: pd.DataFrame, code: str) -> list[dict[str, object]]:
        code = self._clean(code)
        if not code:
            raise ValueError("Empty code expression")

        try:
            tree = ast.parse(code, mode="eval")
            is_eval = True
        except SyntaxError:
            try:
                tree = ast.parse(code, mode="exec")
                is_eval = False
            except SyntaxError as e:
                raise ValueError(f"Invalid Python syntax: {e}")

        validate_ast(tree)

        safe_builtins = {
            "len": len,
            "round": round,
            "abs": abs,
            "sum": sum,
            "min": min,
            "max": max,
            "range": range,
            "bool": bool,
            "int": int,
            "float": float,
            "str": str,
        }
        env = {"pd": pd, "__builtins__": safe_builtins}
        local = {"df": frame.copy()}

        def _execute():
            if is_eval:
                return eval(compile(tree, "<pandas>", "eval"), env, local)
            else:
                exec(compile(tree, "<pandas>", "exec"), env, local)
                return local.get("result") or local.get("df")

        result = self._execute_with_timeout(_execute, timeout=self.DEFAULT_TIMEOUT)

        if result is None:
            raise ValueError("Expression did not return a value. Assign your result to 'result'.")
        if isinstance(result, pd.Series):
            result = result.reset_index().rename(columns={0: "value"}) if result.name is None else result.to_frame()
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Expression must return a DataFrame or Series, got {type(result).__name__}")

        return result.head(500).where(pd.notna, None).to_dict(orient="records")

