import pandas as pd
import pytest
from app.tools.sql_tool import SqlTool
from app.tools.pandas_tool import PandasTool, UnsafeExpression


def test_sql_rejects_mutations():
    with pytest.raises(ValueError):
        SqlTool().run({'data': pd.DataFrame({'x': [1]})}, 'delete from data')


def test_sql_joins_datasets():
    assert SqlTool().run(
        {'a': pd.DataFrame({'id': [1]}), 'b': pd.DataFrame({'id': [1], 'v': ['ok']})},
        'select v from a join b using(id)'
    )[1] == [{'v': 'ok'}]


def test_sql_rejects_table_functions():
    tool = SqlTool()
    sample = {'data': pd.DataFrame({'x': [1]})}
    with pytest.raises(ValueError, match="forbidden"):
        tool.run(sample, "SELECT * FROM read_csv('/etc/passwd')")

    with pytest.raises(ValueError, match="forbidden"):
        tool.run(sample, "SELECT * FROM read_parquet('secret.parquet')")

    with pytest.raises(ValueError, match="forbidden"):
        tool.run(sample, "SELECT * FROM glob('../*')")


def test_pandas_returns_records():
    assert PandasTool().run(pd.DataFrame({'x': [1, 2]}), 'df[df.x > 1]') == [{'x': 2}]


def test_pandas_legitimate_queries():
    tool = PandasTool()
    df = pd.DataFrame({'dept': ['eng', 'eng', 'sales'], 'salary': [100, 200, 150]})

    # Groupby and agg
    grouped = tool.run(df, "df.groupby('dept').agg({'salary': 'mean'}).reset_index()")
    assert len(grouped) == 2

    # Sorting
    sorted_rows = tool.run(df, "df.sort_values('salary', ascending=False)")
    assert sorted_rows[0]['salary'] == 200

    # Top-level assignment
    assigned = tool.run(df, "result = df.head(1)")
    assert len(assigned) == 1

    # Safe builtins
    stats = tool.run(df, "df.describe()")
    assert len(stats) > 0


def test_pandas_rejects_import_and_exec():
    tool = PandasTool()
    df = pd.DataFrame({'x': [1, 2]})

    with pytest.raises(ValueError):
        tool.run(df, "__import__('os')")

    with pytest.raises(ValueError):
        tool.run(df, "import os")


def test_pandas_rejects_dangerous_methods():
    tool = PandasTool()
    df = pd.DataFrame({'x': [1, 2]})

    # File I/O
    with pytest.raises(UnsafeExpression):
        tool.run(df, "df.to_csv('hack.csv')")

    # Dynamic query/eval
    with pytest.raises(UnsafeExpression):
        tool.run(df, "df.eval('x + 1')")

    with pytest.raises(UnsafeExpression):
        tool.run(df, "df.query('x > 1')")


def test_pandas_rejects_introspection_and_dunder():
    tool = PandasTool()
    df = pd.DataFrame({'x': [1, 2]})

    with pytest.raises(ValueError):
        tool.run(df, "getattr(df, '__class__')")

    with pytest.raises(ValueError):
        tool.run(df, "().__class__.__bases__[0].__subclasses__()")

    with pytest.raises(ValueError):
        tool.run(df, "df.__dict__")


def test_pandas_rejects_unrelated_assignment_and_loops():
    tool = PandasTool()
    df = pd.DataFrame({'x': [1, 2]})

    # Unrelated assignment
    with pytest.raises(ValueError):
        tool.run(df, "evil = 42\nresult = evil")

    # Loops
    with pytest.raises(ValueError):
        tool.run(df, "while True: pass")

    with pytest.raises(ValueError):
        tool.run(df, "for i in range(10): pass")

