import pandas as pd
from sklearn.ensemble import IsolationForest
class AnomalyService:
    def detect(self, frame: pd.DataFrame) -> list[dict[str, object]]:
        numeric=frame.select_dtypes(include='number').dropna()
        if len(numeric)<10 or numeric.shape[1]==0:return []
        scores=IsolationForest(contamination='auto',random_state=42).fit_predict(numeric); output=[]
        for idx,row in numeric.loc[scores==-1].head(100).iterrows():
            prominent=((row-numeric.median()).abs()/numeric.std().replace(0,1)).nlargest(2).index.tolist(); output.append({'row_index':int(idx),'values':row.to_dict(),'reason':f"Unusual values in {', '.join(prominent)} relative to the dataset distribution."})
        return output
