"""
ML Engine: Train and load Logistic Regression models for
Stroke, Epilepsy, Meningitis, and Encephalitis.
Uses synthetic/representative data where Kaggle data is unavailable.
"""
import os
import time
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
DATA_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# ─── Synthetic dataset builders ──────────────────────────────────────────────

def _make_stroke_data():
    np.random.seed(0)
    n = 5000
    age = np.random.randint(10, 85, n)
    hypertension = np.random.choice([0,1], n, p=[0.7,0.3])
    heart_disease = np.random.choice([0,1], n, p=[0.8,0.2])
    avg_glucose = np.random.uniform(60, 280, n)
    bmi = np.random.uniform(16, 45, n)
    ever_married = np.random.choice([0,1], n, p=[0.4,0.6])
    smoking = np.random.choice([0,1,2], n)          # 0=never,1=former,2=smokes
    slurred_speech = np.random.choice([0,1], n, p=[0.75,0.25])
    weakness = np.random.choice([0,1], n, p=[0.7,0.3])
    vision_issues = np.random.choice([0,1], n, p=[0.8,0.2])
    gender = np.random.choice([0,1], n)             # 0=F,1=M

    score = (
        (age > 55) * 2 + hypertension * 2 + heart_disease * 2 +
        (avg_glucose > 140) * 1 + (bmi > 30) * 1 + ever_married * 0.5 +
        slurred_speech * 3 + weakness * 2.5 + vision_issues * 1.5
    )
    label = (score + np.random.normal(0, 1.5, n) > 7).astype(int)

    df = pd.DataFrame({
        'age': age, 'gender': gender, 'hypertension': hypertension,
        'heart_disease': heart_disease, 'ever_married': ever_married,
        'avg_glucose_level': avg_glucose, 'bmi': bmi, 'smoking_status': smoking,
        'slurred_speech': slurred_speech, 'weakness': weakness,
        'vision_issues': vision_issues, 'stroke': label
    })
    return df, 'stroke'


def _make_epilepsy_data():
    np.random.seed(1)
    n = 5000
    age = np.random.randint(5, 70, n)
    seizure_history = np.random.choice([0,1], n, p=[0.4,0.6])
    loss_of_consciousness = np.random.choice([0,1], n, p=[0.5,0.5])
    jerking_movements = np.random.choice([0,1], n, p=[0.45,0.55])
    aura = np.random.choice([0,1], n, p=[0.6,0.4])
    postictal_confusion = np.random.choice([0,1], n, p=[0.55,0.45])
    family_history = np.random.choice([0,1], n, p=[0.7,0.3])
    eeg_abnormal = np.random.choice([0,1], n, p=[0.5,0.5])
    duration_minutes = np.random.randint(1, 30, n)
    gender = np.random.choice([0,1], n)

    score = (
        seizure_history * 3 + loss_of_consciousness * 2 +
        jerking_movements * 2.5 + aura * 1.5 + postictal_confusion * 2 +
        family_history * 1 + eeg_abnormal * 3 + (duration_minutes > 5) * 1
    )
    label = (score + np.random.normal(0, 1.5, n) > 9).astype(int)

    df = pd.DataFrame({
        'age': age, 'gender': gender, 'seizure_history': seizure_history,
        'loss_of_consciousness': loss_of_consciousness,
        'jerking_movements': jerking_movements, 'aura': aura,
        'postictal_confusion': postictal_confusion, 'family_history': family_history,
        'eeg_abnormal': eeg_abnormal, 'duration_minutes': duration_minutes,
        'epilepsy': label
    })
    return df, 'epilepsy'


def _make_meningitis_data():
    np.random.seed(2)
    n = 5000
    age = np.random.randint(1, 80, n)
    fever = np.random.choice([0,1], n, p=[0.2,0.8])
    headache = np.random.choice([0,1], n, p=[0.25,0.75])
    neck_stiffness = np.random.choice([0,1], n, p=[0.4,0.6])
    photophobia = np.random.choice([0,1], n, p=[0.5,0.5])
    vomiting = np.random.choice([0,1], n, p=[0.4,0.6])
    rash = np.random.choice([0,1], n, p=[0.7,0.3])
    altered_consciousness = np.random.choice([0,1], n, p=[0.6,0.4])
    kernig_sign = np.random.choice([0,1], n, p=[0.65,0.35])
    temperature = np.random.uniform(36.5, 41.5, n)
    gender = np.random.choice([0,1], n)

    score = (
        fever * 3 + headache * 2 + neck_stiffness * 3 +
        photophobia * 2 + vomiting * 1.5 + rash * 2.5 +
        altered_consciousness * 2 + kernig_sign * 2.5 +
        (temperature > 39) * 2
    )
    label = (score + np.random.normal(0, 2, n) > 11).astype(int)

    df = pd.DataFrame({
        'age': age, 'gender': gender, 'fever': fever,
        'headache': headache, 'neck_stiffness': neck_stiffness,
        'photophobia': photophobia, 'vomiting': vomiting,
        'rash': rash, 'altered_consciousness': altered_consciousness,
        'kernig_sign': kernig_sign, 'temperature': temperature,
        'meningitis': label
    })
    return df, 'meningitis'


def _make_encephalitis_data():
    """Load static CSV if exists, else generate."""
    csv_path = os.path.join(DATA_DIR, 'encephalitis.csv')
    if not os.path.exists(csv_path):
        from app.data.encephalitis_data import generate_encephalitis_csv
        df = generate_encephalitis_csv()
    else:
        df = pd.read_csv(csv_path)

    df['gender'] = (df['gender'] == 'Male').astype(int)
    return df, 'encephalitis'


# ─── Feature configs ──────────────────────────────────────────────────────────

DISEASE_CONFIGS = {
    'stroke': {
        'features': ['age','gender','hypertension','heart_disease','ever_married',
                     'avg_glucose_level','bmi','smoking_status',
                     'slurred_speech','weakness','vision_issues'],
        'target': 'stroke',
        'data_fn': _make_stroke_data
    },
    'epilepsy': {
        'features': ['age','gender','seizure_history','loss_of_consciousness',
                     'jerking_movements','aura','postictal_confusion',
                     'family_history','eeg_abnormal','duration_minutes'],
        'target': 'epilepsy',
        'data_fn': _make_epilepsy_data
    },
    'meningitis': {
        'features': ['age','gender','fever','headache','neck_stiffness',
                     'photophobia','vomiting','rash','altered_consciousness',
                     'kernig_sign','temperature'],
        'target': 'meningitis',
        'data_fn': _make_meningitis_data
    },
    'encephalitis': {
        'features': ['age','gender','fever','headache','seizures',
                     'altered_consciousness','neck_stiffness','vomiting',
                     'photophobia','confusion','duration_days','temperature'],
        'target': 'encephalitis',
        'data_fn': _make_encephalitis_data
    }
}


# ─── Train & Save ─────────────────────────────────────────────────────────────

def train_all_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    metrics_all = {}

    for disease, cfg in DISEASE_CONFIGS.items():
        print(f"[ML] Training model for: {disease}")
        df, _ = cfg['data_fn']()
        features = cfg['features']
        target   = cfg['target']

        # Align columns
        available = [f for f in features if f in df.columns]
        X = df[available].fillna(df[available].mean(numeric_only=True))
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)
        X_test_sc  = scaler.transform(X_test)

        model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
        model.fit(X_train_sc, y_train)

        y_pred = model.predict(X_test_sc)
        acc  = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec  = recall_score(y_test, y_pred, zero_division=0)
        f1   = f1_score(y_test, y_pred, zero_division=0)
        cm   = confusion_matrix(y_test, y_pred).tolist()

        metrics_all[disease] = {
            'accuracy': round(acc, 4),
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1': round(f1, 4),
            'confusion_matrix': cm,
            'features': available
        }

        joblib.dump(model,  os.path.join(MODELS_DIR, f'{disease}_model.pkl'))
        joblib.dump(scaler, os.path.join(MODELS_DIR, f'{disease}_scaler.pkl'))
        print(f"  [ML] {disease}: acc={acc:.3f}  f1={f1:.3f}")

    with open(os.path.join(MODELS_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics_all, f, indent=2)

    print("[ML] All models trained and saved.")
    return metrics_all


# ─── Load & Predict ───────────────────────────────────────────────────────────

_model_cache  = {}
_scaler_cache = {}

def _load(disease):
    if disease not in _model_cache:
        mp = os.path.join(MODELS_DIR, f'{disease}_model.pkl')
        sp = os.path.join(MODELS_DIR, f'{disease}_scaler.pkl')
        if not os.path.exists(mp):
            train_all_models()
        _model_cache[disease]  = joblib.load(mp)
        _scaler_cache[disease] = joblib.load(sp)
    return _model_cache[disease], _scaler_cache[disease]


def predict(disease: str, input_dict: dict) -> dict:
    """
    Run inference for a given disease.
    Returns probability, risk_level, recommendation, latency_ms.
    """
    model, scaler = _load(disease)
    cfg      = DISEASE_CONFIGS[disease]
    features = cfg['features']

    t0 = time.perf_counter()

    row = []
    for f in features:
        val = input_dict.get(f, 0)
        try:
            row.append(float(val))
        except (TypeError, ValueError):
            row.append(0.0)

    X = np.array(row).reshape(1, -1)
    X_sc = scaler.transform(X)
    prob = float(model.predict_proba(X_sc)[0][1])

    latency_ms = (time.perf_counter() - t0) * 1000

    # Risk level
    if prob < 0.35:
        risk_level     = 'Low'
        recommendation = 'Stay home. Monitor symptoms. Rest and hydrate.'
    elif prob < 0.65:
        risk_level     = 'Medium'
        recommendation = 'Visit the nearest PHC within 24 hours for evaluation.'
    else:
        risk_level     = 'High'
        recommendation = 'Seek emergency referral immediately. Call 108 ambulance.'

    return {
        'disease': disease,
        'probability': round(prob, 4),
        'risk_level': risk_level,
        'recommendation': recommendation,
        'latency_ms': round(latency_ms, 2)
    }


def rule_based_predict(symptoms: dict) -> dict:
    """
    Fallback rule-based prediction when model is unavailable.
    Returns most likely disease and risk.
    """
    scores = {'stroke': 0, 'epilepsy': 0, 'meningitis': 0, 'encephalitis': 0}

    if symptoms.get('slurred_speech'): scores['stroke'] += 4
    if symptoms.get('weakness'):        scores['stroke'] += 3
    if symptoms.get('vision_issues'):   scores['stroke'] += 2
    if symptoms.get('hypertension'):    scores['stroke'] += 2

    if symptoms.get('seizures') or symptoms.get('jerking_movements'):
        scores['epilepsy'] += 4
        scores['encephalitis'] += 2
    if symptoms.get('loss_of_consciousness'): scores['epilepsy'] += 3
    if symptoms.get('aura'):                   scores['epilepsy'] += 2

    if symptoms.get('neck_stiffness'): scores['meningitis'] += 4
    if symptoms.get('fever'):          scores['meningitis'] += 2; scores['encephalitis'] += 2
    if symptoms.get('photophobia'):    scores['meningitis'] += 3
    if symptoms.get('rash'):           scores['meningitis'] += 3

    if symptoms.get('altered_consciousness'): scores['encephalitis'] += 4
    if symptoms.get('confusion'):             scores['encephalitis'] += 3
    if symptoms.get('headache'):              scores['encephalitis'] += 1; scores['meningitis'] += 1

    best_disease = max(scores, key=scores.get)
    best_score   = scores[best_disease]
    max_possible = 13

    prob = min(best_score / max_possible, 0.95)
    if prob < 0.35:
        risk_level     = 'Low'
        recommendation = 'Stay home. Monitor symptoms.'
    elif prob < 0.65:
        risk_level     = 'Medium'
        recommendation = 'Visit the nearest PHC within 24 hours.'
    else:
        risk_level     = 'High'
        recommendation = 'Seek emergency referral immediately. Call 108.'

    return {
        'disease': best_disease,
        'probability': round(prob, 4),
        'risk_level': risk_level,
        'recommendation': recommendation,
        'latency_ms': 0.5,
        'method': 'rule-based'
    }


def get_metrics():
    path = os.path.join(MODELS_DIR, 'metrics.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


if __name__ == '__main__':
    train_all_models()
