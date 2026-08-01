import pandas as pd
from sklearn.ensemble import IsolationForest

class AnomalyService:
    def detect(self, frame: pd.DataFrame, max_anomalies: int = 15) -> list[dict[str, object]]:
        numeric = frame.select_dtypes(include='number').dropna()
        if len(numeric) < 10 or numeric.shape[1] == 0:
            return []
            
        model = IsolationForest(contamination=0.01, random_state=42)
        model.fit(numeric)
        
        # Get decision function scores (lower score = more anomalous)
        decision_scores = model.decision_function(numeric)
        numeric_with_scores = numeric.copy()
        numeric_with_scores['_score'] = decision_scores
        
        # Filter negative decision scores (outliers) and sort by severity
        outliers = numeric_with_scores[numeric_with_scores['_score'] < 0].sort_values('_score').head(max_anomalies)
        
        # If no severe outliers found with 0.01 contamination, pick top 5 lowest decision scores
        if outliers.empty:
            outliers = numeric_with_scores.sort_values('_score').head(5)

        output = []
        for idx, row in outliers.iterrows():
            row_data = row.drop('_score')
            # Identify the 2 columns with highest standard deviation deviation for this row
            std_dev = numeric.std().replace(0, 1)
            prominent = ((row_data - numeric.median()).abs() / std_dev).nlargest(2).index.tolist()
            
            output.append({
                'row_index': int(idx),
                'values': row_data.to_dict(),
                'reason': f"Unusual values in {', '.join(prominent)} relative to the dataset distribution."
            })
            
        return output
