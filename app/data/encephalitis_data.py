"""
Encephalitis static dataset — representative synthetic clinical data.
Features align with symptom-checker inputs.
"""
import pandas as pd
import numpy as np
import os

def generate_encephalitis_csv():
    """Generate and save a static encephalitis dataset."""
    np.random.seed(42)
    n = 500

    data = {
        'age': np.random.randint(1, 80, n),
        'gender': np.random.choice(['Male', 'Female'], n),
        'fever': np.random.choice([0, 1], n, p=[0.15, 0.85]),
        'headache': np.random.choice([0, 1], n, p=[0.2, 0.8]),
        'seizures': np.random.choice([0, 1], n, p=[0.5, 0.5]),
        'altered_consciousness': np.random.choice([0, 1], n, p=[0.4, 0.6]),
        'neck_stiffness': np.random.choice([0, 1], n, p=[0.6, 0.4]),
        'vomiting': np.random.choice([0, 1], n, p=[0.45, 0.55]),
        'photophobia': np.random.choice([0, 1], n, p=[0.55, 0.45]),
        'confusion': np.random.choice([0, 1], n, p=[0.35, 0.65]),
        'duration_days': np.random.randint(1, 14, n),
        'temperature': np.random.uniform(37.0, 41.5, n).round(1),
        'encephalitis': np.zeros(n, dtype=int)
    }

    # Rule-based labeling (clinical heuristic)
    df = pd.DataFrame(data)
    df['score'] = (
        df['fever'] * 3 +
        df['altered_consciousness'] * 3 +
        df['seizures'] * 2 +
        df['headache'] * 1 +
        df['confusion'] * 2 +
        df['neck_stiffness'] * 1 +
        (df['temperature'] > 39.0).astype(int) * 2
    )
    df['encephalitis'] = (df['score'] >= 7).astype(int)
    df.drop(columns=['score'], inplace=True)

    out_path = os.path.join(os.path.dirname(__file__), 'encephalitis.csv')
    df.to_csv(out_path, index=False)
    print(f"[Data] Encephalitis dataset saved: {out_path} ({len(df)} rows)")
    return df

if __name__ == '__main__':
    generate_encephalitis_csv()
