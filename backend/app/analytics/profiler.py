import math, pandas as pd
from app.schemas.contracts import ProfileResponse
def clean(value): return None if value is None or (isinstance(value,float) and math.isnan(value)) else float(value)
class ProfileService:
    def profile(self, dataset_id: str, frame: pd.DataFrame) -> ProfileResponse:
        columns=[{'name':str(c),'dtype':str(frame[c].dtype),'null_percentage':round(float(frame[c].isna().mean()*100),2),'unique_values':int(frame[c].nunique(dropna=True))} for c in frame.columns]
        numeric=frame.select_dtypes(include='number'); stats={n:{k:clean(v) for k,v in values.items()} for n,values in numeric.describe().to_dict().items()}
        return ProfileResponse(dataset_id=dataset_id,rows=len(frame),columns=len(frame.columns),duplicate_rows=int(frame.duplicated().sum()),columns_profile=columns,numeric_summary=stats)
