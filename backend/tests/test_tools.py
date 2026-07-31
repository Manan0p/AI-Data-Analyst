import pandas as pd,pytest
from app.tools.sql_tool import SqlTool
from app.tools.pandas_tool import PandasTool
def test_sql_rejects_mutations():
    with pytest.raises(ValueError):SqlTool().run({'data':pd.DataFrame({'x':[1]})},'delete from data')
def test_sql_joins_datasets():assert SqlTool().run({'a':pd.DataFrame({'id':[1]}),'b':pd.DataFrame({'id':[1],'v':['ok']})},'select v from a join b using(id)')[1]==[{'v':'ok'}]
def test_pandas_returns_records():assert PandasTool().run(pd.DataFrame({'x':[1,2]}),'df[df.x > 1]')==[{'x':2}]
